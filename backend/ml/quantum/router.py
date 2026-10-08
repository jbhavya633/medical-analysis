"""/api/qml router. Delegation only: every endpoint calls one service function."""

from typing import Literal

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, Field

from backend.ml.quantum import service

router = APIRouter(prefix="/api/qml", tags=["Hybrid QML (research prototype - not a diagnostic tool)"])

DatasetId = Literal["breast_cancer", "heart"]
ModelId = Literal["logreg", "svm_rbf", "random_forest", "mlp", "qsvm", "vqc", "hybrid_qnn"]


class TrainRequest(BaseModel):
    dataset: DatasetId
    model: ModelId
    n_qubits: int = Field(6, ge=4, le=8)


class PredictRequest(BaseModel):
    model_id: str = Field(..., pattern=r"^[a-z0-9_]{1,80}$")
    features: dict[str, float | None] | list[float | None] = Field(..., max_length=64)


@router.get("/health")
def health():
    return service.health()


@router.get("/datasets")
def datasets():
    return service.list_datasets()


@router.get("/models")
def models():
    return service.list_models()


@router.get("/models/{model_id}")
def model_info(model_id: str):
    return service.get_model_info(model_id)


@router.get("/benchmark")
def benchmark():
    return service.get_benchmark()


@router.post("/train", status_code=202)
def train(req: TrainRequest, background_tasks: BackgroundTasks):
    return service.start_training(req.dataset, req.model, req.n_qubits, background_tasks)


@router.get("/jobs/{job_id}")
def job(job_id: str):
    return service.get_job(job_id)


@router.post("/predict")
def predict(req: PredictRequest):
    return service.predict(req.model_id, req.features)
