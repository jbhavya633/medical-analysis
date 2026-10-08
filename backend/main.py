"""MedFusion FastAPI gateway (port 8000). Endpoints only delegate to backend/models and backend/ml/quantum."""

import logging
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.ml.quantum import service as qml_service
from backend.ml.quantum.router import router as qml_router
from backend.models import InvalidInputError, ModelUnavailableError
from backend.models.ct_model import CTModel
from backend.models.ecg_model import ECGModel
from backend.models.xray_model import XRayModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("medfusion.api")

MODELS = {"ecg": ECGModel(), "xray": XRayModel(), "ct": CTModel()}
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
MAX_REQUEST_BYTES = int(os.getenv("MAX_REQUEST_BYTES", 10 * 1024 * 1024))


@asynccontextmanager
async def lifespan(_: FastAPI):
    for model in MODELS.values():
        model.load()
    yield


app = FastAPI(
    title="MedFusion API",
    description="SIH26139 hybrid quantum-classical ML research prototype. "
                "**Not a diagnostic tool** - outputs must not be used for clinical decisions.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in ALLOWED_ORIGINS if o != "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(qml_router)


@app.middleware("http")
async def request_guard(request: Request, call_next):
    request.state.request_id = uuid.uuid4().hex[:12]
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > MAX_REQUEST_BYTES:
        return JSONResponse({"detail": "Request body too large", "request_id": request.state.request_id}, 413)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


def _error(request: Request, status: int, detail: str) -> JSONResponse:
    return JSONResponse({"detail": detail, "request_id": getattr(request.state, "request_id", None)}, status)


@app.exception_handler(qml_service.NotFoundError)
async def _not_found(request: Request, exc: qml_service.NotFoundError):
    return _error(request, 404, str(exc))


@app.exception_handler(qml_service.InvalidRequestError)
async def _invalid(request: Request, exc: qml_service.InvalidRequestError):
    return _error(request, 422, str(exc))


@app.exception_handler(qml_service.BusyError)
async def _busy(request: Request, exc: qml_service.BusyError):
    return _error(request, 429, str(exc))


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):
    logger.exception("Unhandled error (request_id=%s)", getattr(request.state, "request_id", None))
    return _error(request, 500, "Internal server error")


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
