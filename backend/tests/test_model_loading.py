import io

import numpy as np
import pytest
import torch

from backend.models import InvalidInputError, ModelUnavailableError
from backend.models.ct_model import CTModel
from backend.models.ecg_model import ECGModel, ECGNet
from backend.models.xray_model import XRayModel


def _save_ecg_checkpoint(path, leads=12, classes=3, max_length=400, corrupt=False):
    state = ECGNet(input_channels=leads, num_classes=classes, max_length=max_length).state_dict()
    if corrupt:
        state["fc2.weight"] = torch.zeros(classes, 7)
    torch.save(
        {"state_dict": state, "label_map": {f"c{i}": i for i in range(classes)}, "max_length": max_length},
        path,
    )


def test_missing_weights_is_not_loaded(tmp_path):
    for model in (ECGModel(tmp_path / "none.pth"), XRayModel(tmp_path / "none.pth"), CTModel()):
        assert model.load() is False
        assert model.is_loaded() is False
        assert model.status()["error"]
        with pytest.raises(ModelUnavailableError):
            model.predict_file(io.BytesIO(b"x"), "x.csv")


def test_ecg_loads_matching_checkpoint_and_predicts(tmp_path):
    path = tmp_path / "ecg.pth"
    _save_ecg_checkpoint(path)
    model = ECGModel(path)
    assert model.load() is True and model.is_loaded() is True
    csv = "\n".join(",".join(str(v) for v in row) for row in np.random.default_rng(0).normal(size=(500, 12)))
    out = model.predict_file(io.BytesIO(csv.encode()), "sig.csv")
    assert out["predicted_label"] in {"c0", "c1", "c2"}
    assert abs(sum(out["probabilities"].values()) - 1) < 1e-5


def test_ecg_shape_mismatch_marks_unavailable(tmp_path):
    path = tmp_path / "ecg.pth"
    _save_ecg_checkpoint(path, corrupt=True)
    model = ECGModel(path)
    assert model.load() is False
    assert "does not match" in model.error
    assert model.is_loaded() is False


def test_garbage_checkpoint_marks_unavailable(tmp_path):
    path = tmp_path / "bad.pth"
    path.write_bytes(b"not a checkpoint")
    assert ECGModel(path).load() is False
    assert XRayModel(path).load() is False


def test_ecg_input_validation(tmp_path):
    path = tmp_path / "ecg.pth"
    _save_ecg_checkpoint(path)
    model = ECGModel(path)
    model.load()
    with pytest.raises(InvalidInputError):
        model.predict_file(io.BytesIO(b"1,2"), "sig.txt")
    with pytest.raises(InvalidInputError):
        model.predict(np.zeros((5, 500)))
    with pytest.raises(InvalidInputError):
        model.predict(np.zeros((12, 10)))
