"""1D-CNN ECG classifier (architecture must match backend/ml/train/ecg_analysis_train.py)."""

import io
import logging
import os
import pickle
from pathlib import Path
from typing import BinaryIO

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from backend.models import InvalidInputError, ModelUnavailableError

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WEIGHTS = REPO_ROOT / "ecg_cnn_checkpoint.pth"
ALLOWED_EXTENSIONS = {".csv"}
ALLOWED_LEAD_COUNTS = {1, 2, 3, 6, 12, 15}
MIN_SAMPLES = 250
MAX_SAMPLES = 60_000


class ECGNet(nn.Module):
    def __init__(self, input_channels=12, num_classes=5, max_length=5000, dropout_rate=0.5):
        super().__init__()
        self.conv1 = nn.Conv1d(input_channels, 64, kernel_size=5, stride=1, padding=2)
        self.bn1 = nn.BatchNorm1d(64)
        self.pool1 = nn.MaxPool1d(kernel_size=2, stride=2)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=5, stride=1, padding=2)
        self.bn2 = nn.BatchNorm1d(128)
        self.pool2 = nn.MaxPool1d(kernel_size=2, stride=2)
        self.conv3 = nn.Conv1d(128, 256, kernel_size=5, stride=1, padding=2)
        self.bn3 = nn.BatchNorm1d(256)
        self.pool3 = nn.MaxPool1d(kernel_size=2, stride=2)
        self.fc1 = nn.Linear(256 * (max_length // 8), 128)
        self.bn4 = nn.BatchNorm1d(128)
        self.dropout = nn.Dropout(dropout_rate)
        self.fc2 = nn.Linear(128, num_classes)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        x = self.pool1(self.relu(self.bn1(self.conv1(x))))
        x = self.pool2(self.relu(self.bn2(self.conv2(x))))
        x = self.pool3(self.relu(self.bn3(self.conv3(x))))
        x = x.view(x.size(0), -1)
        x = self.dropout(self.relu(self.bn4(self.fc1(x))))
        return self.fc2(x)


class ECGModel:
    name = "ecg"

    def __init__(self, weights_path: str | os.PathLike | None = None):
        self.weights_path = Path(weights_path or os.getenv("ECG_WEIGHTS_PATH") or DEFAULT_WEIGHTS)
        self.max_upload_bytes = int(os.getenv("MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
        self.model: ECGNet | None = None
        self.labels: list[str] = []
        self.max_length = 5000
        self.error: str | None = None

    def load(self) -> bool:
        self.model, self.error = None, None
        if not self.weights_path.is_file():
            self.error = f"weights not found at {self.weights_path}"
            logger.error("ECG model unavailable: %s", self.error)
            return False
        try:
            ckpt = torch.load(self.weights_path, map_location="cpu", weights_only=True)
            state = ckpt["state_dict"]
            label_map = ckpt["label_map"]
            max_length = int(ckpt.get("max_length", 5000))
            net = ECGNet(
                input_channels=state["conv1.weight"].shape[1],
                num_classes=len(label_map),
                max_length=max_length,
            )
            mismatch = _state_dict_mismatch(net.state_dict(), state)
            if mismatch:
                self.error = f"checkpoint does not match ECGNet: {mismatch}"
                logger.error("ECG model unavailable: %s", self.error)
                return False
            net.load_state_dict(state, strict=True)
            net.eval()
        except (OSError, KeyError, RuntimeError, pickle.UnpicklingError) as exc:
            self.error = f"failed to load checkpoint ({type(exc).__name__})"
            logger.exception("ECG model unavailable: %s", self.error)
            return False
        self.labels = [str(k) for k, _ in sorted(label_map.items(), key=lambda kv: kv[1])]
        self.max_length = max_length
        self.model = net
        logger.info("Loaded ECG model from %s", self.weights_path)
        return True

    def is_loaded(self) -> bool:
        return self.model is not None

    def status(self) -> dict:
        return {"loaded": self.is_loaded(), "error": self.error}

    def predict_file(self, fileobj: BinaryIO, filename: str | None) -> dict:
        if not self.is_loaded():
            raise ModelUnavailableError("ECG model is not loaded")
        if Path(filename or "").suffix.lower() not in ALLOWED_EXTENSIONS:
            raise InvalidInputError("ECG upload must be a .csv file")
        raw = fileobj.read(self.max_upload_bytes + 1)
        if len(raw) > self.max_upload_bytes:
            raise InvalidInputError("ECG upload exceeds the maximum size")
        try:
            signal = pd.read_csv(io.BytesIO(raw), header=None).to_numpy(dtype=np.float32)
        except (ValueError, UnicodeDecodeError, pd.errors.ParserError) as exc:
            raise InvalidInputError("ECG CSV must contain only numeric values") from exc
        return self.predict(signal)

    def predict(self, signal: np.ndarray) -> dict:
        if not self.is_loaded():
            raise ModelUnavailableError("ECG model is not loaded")
        signal = self._validate(signal)
        if signal.shape[1] > self.max_length:
            signal = signal[:, : self.max_length]
        else:
            signal = np.pad(signal, ((0, 0), (0, self.max_length - signal.shape[1])))
        signal = (signal - signal.mean(axis=1, keepdims=True)) / (signal.std(axis=1, keepdims=True) + 1e-8)
        with torch.no_grad():
            probs = torch.softmax(self.model(torch.from_numpy(signal).float().unsqueeze(0)), dim=1)[0]
        idx = int(probs.argmax())
        return {
            "predicted_label": self.labels[idx],
            "confidence": float(probs[idx]),
            "probabilities": {label: float(p) for label, p in zip(self.labels, probs)},
        }

    def _validate(self, signal: np.ndarray) -> np.ndarray:
        signal = np.asarray(signal, dtype=np.float32)
        if signal.ndim != 2:
            raise InvalidInputError("ECG signal must be 2-D (leads x samples)")
        if signal.shape[0] not in ALLOWED_LEAD_COUNTS and signal.shape[1] in ALLOWED_LEAD_COUNTS:
            signal = signal.T
        expected_leads = self.model.conv1.in_channels
        if signal.shape[0] != expected_leads:
            raise InvalidInputError(f"ECG signal must have {expected_leads} leads")
        if not MIN_SAMPLES <= signal.shape[1] <= MAX_SAMPLES:
            raise InvalidInputError(f"ECG signal length must be {MIN_SAMPLES}-{MAX_SAMPLES} samples")
        if not np.isfinite(signal).all():
            raise InvalidInputError("ECG signal contains NaN or infinite values")
        return signal


def _state_dict_mismatch(expected: dict, actual: dict) -> str | None:
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    shapes = sorted(k for k in set(expected) & set(actual) if expected[k].shape != actual[k].shape)
    if not (missing or unexpected or shapes):
        return None
    return f"missing={missing[:5]} unexpected={unexpected[:5]} shape_mismatch={shapes[:5]}"
