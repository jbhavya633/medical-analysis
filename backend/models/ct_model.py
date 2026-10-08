"""CT analysis placeholder.

The repository contains no CT architecture, training script or checkpoint, so this modality is
reported as unavailable. It never produces output. CT_WEIGHTS_PATH is reserved for a future model.
"""

import os
from typing import BinaryIO

from backend.models import ModelUnavailableError


class CTModel:
    name = "ct"

    def __init__(self, weights_path: str | os.PathLike | None = None):
        self.weights_path = weights_path or os.getenv("CT_WEIGHTS_PATH")
        self.error: str | None = None

    def load(self) -> bool:
        self.error = "not available: no CT model architecture or weights in this repository"
        return False

    def is_loaded(self) -> bool:
        return False

    def status(self) -> dict:
        return {"loaded": False, "error": self.error}

    def predict_file(self, fileobj: BinaryIO, filename: str | None) -> dict:
        raise ModelUnavailableError("CT model is not available")
