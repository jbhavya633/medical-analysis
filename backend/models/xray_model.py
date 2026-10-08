"""U-Net chest X-ray segmentation (architecture must match backend/ml/train/xray_segmentation_train.py)."""

import base64
import io
import logging
import os
import pickle
from pathlib import Path
from typing import BinaryIO

import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image, UnidentifiedImageError

from backend.models import InvalidInputError, ModelUnavailableError
from backend.models.ecg_model import _state_dict_mismatch

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WEIGHTS = REPO_ROOT / "xray_unet_checkpoint.pth"
ALLOWED_FORMATS = {"PNG", "JPEG"}
MAX_PIXELS = 4096 * 4096
TRANSFORM = transforms.Compose([transforms.Resize((256, 256)), transforms.ToTensor()])


class UNetBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        return self.relu(self.bn2(self.conv2(self.relu(self.bn1(self.conv1(x))))))


class UNet(nn.Module):
    def __init__(self, in_channels=3, out_channels=1, features=(64, 128, 256, 512)):
        super().__init__()
        self.ups = nn.ModuleList()
        self.downs = nn.ModuleList()
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        for feature in features:
            self.downs.append(UNetBlock(in_channels, feature))
            in_channels = feature
        for feature in reversed(features):
            self.ups.append(nn.ConvTranspose2d(feature * 2, feature, kernel_size=2, stride=2))
            self.ups.append(UNetBlock(feature * 2, feature))
        self.bottleneck = UNetBlock(features[-1], features[-1] * 2)
        self.final_conv = nn.Conv2d(features[0], out_channels, kernel_size=1)

    def forward(self, x):
        skips = []
        for down in self.downs:
            x = down(x)
            skips.append(x)
            x = self.pool(x)
        x = self.bottleneck(x)
        skips = skips[::-1]
        for idx in range(0, len(self.ups), 2):
            x = self.ups[idx](x)
            skip = skips[idx // 2]
            if x.shape != skip.shape:
                x = nn.functional.interpolate(x, size=skip.shape[2:], mode="bilinear", align_corners=False)
            x = self.ups[idx + 1](torch.cat((skip, x), dim=1))
        return torch.sigmoid(self.final_conv(x))


class XRayModel:
    name = "xray"

    def __init__(self, weights_path: str | os.PathLike | None = None):
        self.weights_path = Path(weights_path or os.getenv("XRAY_WEIGHTS_PATH") or DEFAULT_WEIGHTS)
        self.max_upload_bytes = int(os.getenv("MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
        self.model: UNet | None = None
        self.error: str | None = None

    def load(self) -> bool:
        self.model, self.error = None, None
        if not self.weights_path.is_file():
            self.error = f"weights not found at {self.weights_path}"
            logger.error("X-ray model unavailable: %s", self.error)
            return False
        try:
            state = torch.load(self.weights_path, map_location="cpu", weights_only=True)["state_dict"]
            net = UNet(in_channels=3, out_channels=1)
            mismatch = _state_dict_mismatch(net.state_dict(), state)
            if mismatch:
                self.error = f"checkpoint does not match UNet: {mismatch}"
                logger.error("X-ray model unavailable: %s", self.error)
                return False
            net.load_state_dict(state, strict=True)
            net.eval()
        except (OSError, KeyError, RuntimeError, pickle.UnpicklingError) as exc:
            self.error = f"failed to load checkpoint ({type(exc).__name__})"
            logger.exception("X-ray model unavailable: %s", self.error)
            return False
        self.model = net
        logger.info("Loaded X-ray model from %s", self.weights_path)
        return True

    def is_loaded(self) -> bool:
        return self.model is not None

    def status(self) -> dict:
        return {"loaded": self.is_loaded(), "error": self.error}

    def predict_file(self, fileobj: BinaryIO, filename: str | None) -> dict:
        if not self.is_loaded():
            raise ModelUnavailableError("X-ray model is not loaded")
        raw = fileobj.read(self.max_upload_bytes + 1)
        if len(raw) > self.max_upload_bytes:
            raise InvalidInputError("Image upload exceeds the maximum size")
        try:
            img = Image.open(io.BytesIO(raw))
            if img.format not in ALLOWED_FORMATS:
                raise InvalidInputError("Image must be PNG or JPEG")
            if img.width * img.height > MAX_PIXELS:
                raise InvalidInputError("Image dimensions are too large")
            img = img.convert("RGB")
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            raise InvalidInputError("Upload is not a readable PNG or JPEG image") from exc
        return self.predict(img)

    def predict(self, img: Image.Image) -> dict:
        if not self.is_loaded():
            raise ModelUnavailableError("X-ray model is not loaded")
        with torch.no_grad():
            mask = (self.model(TRANSFORM(img).unsqueeze(0)) > 0.5).float()[0, 0].numpy()
        mask_img = Image.fromarray((mask * 255).astype(np.uint8))
        buf = io.BytesIO()
        mask_img.save(buf, format="PNG")
        return {
            "segmentation_mask": base64.b64encode(buf.getvalue()).decode("ascii"),
            "mask_format": "PNG base64",
            "mask_size": list(mask_img.size),
            "original_size": list(img.size),
        }
