"""MedFusion FastAPI gateway (port 8000). Endpoints only delegate to backend/models."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile

from backend.models import InvalidInputError, ModelUnavailableError
from backend.models.ct_model import CTModel
from backend.models.ecg_model import ECGModel
from backend.models.xray_model import XRayModel

logging.basicConfig(level=logging.INFO)

MODELS = {"ecg": ECGModel(), "xray": XRayModel(), "ct": CTModel()}


@asynccontextmanager
async def lifespan(_: FastAPI):
    for model in MODELS.values():
        model.load()
    yield


app = FastAPI(title="MedFusion API", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "models": {name: m.status() for name, m in MODELS.items()}}


def _analyze(name: str, file: UploadFile) -> dict:
    try:
        return MODELS[name].predict_file(file.file, file.filename)
    except ModelUnavailableError as exc:
        raise HTTPException(status_code=503, detail=f"{exc}; this modality is unavailable") from exc
    except InvalidInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/analyze/ecg")
def analyze_ecg(file: UploadFile = File(...)):
    return _analyze("ecg", file)


@app.post("/api/analyze/xray")
def analyze_xray(file: UploadFile = File(...)):
    return _analyze("xray", file)


@app.post("/api/analyze/ct")
def analyze_ct(file: UploadFile = File(...)):
    return _analyze("ct", file)
