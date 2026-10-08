"""Service layer behind /api/qml. All logic lives here; router.py only delegates."""

import json
import logging
import math
import re
import threading
import time
import uuid
from functools import lru_cache

import joblib
import numpy as np

from backend.ml.quantum import SEED
from backend.ml.quantum.benchmark import MODEL_LABELS, RESULTS_DIR
from backend.ml.quantum.data import DATASETS, DatasetUnavailableError, holdout_split, load_dataset, stratified_subsample
from backend.ml.quantum.evaluate import ALL_MODELS, fit_and_score, model_family
from backend.ml.quantum.explain import shap_values
from backend.ml.quantum.preprocess import selected_feature_names

logger = logging.getLogger(__name__)

DISCLAIMER = "Research prototype on public benchmark data. Not a diagnostic tool; do not use for clinical decisions."
MODEL_ID_RE = re.compile(r"^[a-z0-9_]{1,80}$")
MAX_RUNNING_JOBS = 2
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


class NotFoundError(LookupError):
    """Requested dataset, model, job or benchmark does not exist."""


class InvalidRequestError(ValueError):
    """Request is well-formed JSON but semantically invalid."""


class BusyError(RuntimeError):
    """Too many training jobs are already running."""


def health() -> dict:
    return {"status": "ok", "benchmark_available": (RESULTS_DIR / "summary.json").is_file(),
            "trained_models": len(list_trained_models()), "disclaimer": DISCLAIMER}


def list_datasets() -> list[dict]:
    return [{"id": k, **v} for k, v in DATASETS.items()]


def list_models() -> list[dict]:
    return [{"id": m, "label": MODEL_LABELS[m], "family": model_family(m)} for m in ALL_MODELS]


def list_trained_models() -> list[str]:
    return sorted(p.stem for p in (RESULTS_DIR / "models").glob("*.joblib"))


def get_benchmark() -> dict:
    path = RESULTS_DIR / "summary.json"
    if not path.is_file():
        raise NotFoundError("No benchmark results yet. Run: python -m backend.ml.quantum.benchmark --dataset all")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["trained_models"] = list_trained_models()
    return data


def start_training(dataset: str, model: str, n_qubits: int, background_tasks) -> dict:
    if dataset not in DATASETS:
        raise InvalidRequestError(f"Unknown dataset '{dataset}'")
    if model not in ALL_MODELS:
        raise InvalidRequestError(f"Unknown model '{model}'")
    with _jobs_lock:
        if sum(j["status"] in ("queued", "running") for j in _jobs.values()) >= MAX_RUNNING_JOBS:
            raise BusyError("Too many training jobs are running; try again shortly")
        job_id = uuid.uuid4().hex[:12]
        _jobs[job_id] = {"job_id": job_id, "status": "queued", "dataset": dataset, "model": model,
                         "n_qubits": n_qubits, "created_at": time.time()}
    background_tasks.add_task(run_training_job, job_id)
    return _jobs[job_id]


def run_training_job(job_id: str) -> None:
    job = _jobs[job_id]
    job["status"] = "running"
    try:
        X, y, feature_names = load_dataset(job["dataset"])
        X_tr, X_te, y_tr, y_te = holdout_split(X, y, seed=SEED)
        X_tr, y_tr = stratified_subsample(X_tr, y_tr, 200, SEED)
        metrics, _, pre, est = fit_and_score(job["model"], X_tr, y_tr, X_te, y_te, job["n_qubits"], SEED)
        model_id = f"{job['dataset']}_{job['model']}_{job['n_qubits']}q_job_{job_id}"
        rng = np.random.default_rng(SEED)
        joblib.dump({
            "dataset": job["dataset"], "model": job["model"], "n_qubits": job["n_qubits"], "seed": SEED,
            "preprocessor": pre, "estimator": est, "feature_names": feature_names,
            "selected_features": selected_feature_names(pre, feature_names),
            "background_raw": X_tr[rng.choice(len(X_tr), size=min(20, len(X_tr)), replace=False)],
            "holdout_metrics": metrics,
        }, RESULTS_DIR / "models" / f"{model_id}.joblib")
        job.update(status="done", model_id=model_id, holdout_metrics=metrics)
    except DatasetUnavailableError:
        job.update(status="failed", error="Dataset is unavailable (offline and not cached)")
    except Exception:  # noqa: BLE001 - job errors are logged; clients get a generic message
        logger.exception("training job %s failed", job_id)
        job.update(status="failed", error="Training failed; see server logs")
    finally:
        job["finished_at"] = time.time()


def get_job(job_id: str) -> dict:
    if job_id not in _jobs:
        raise NotFoundError(f"Unknown job '{job_id}'")
    return _jobs[job_id]


@lru_cache(maxsize=32)
def _load_artifact(model_id: str) -> dict:
    return joblib.load(RESULTS_DIR / "models" / f"{model_id}.joblib")


def get_model_info(model_id: str) -> dict:
    art = _artifact(model_id)
    return {"model_id": model_id, "dataset": art["dataset"], "model": art["model"], "n_qubits": art["n_qubits"],
            "feature_names": art["feature_names"], "selected_features": art["selected_features"],
            "holdout_metrics": art["holdout_metrics"]}


def predict(model_id: str, features: dict[str, float | None] | list[float | None]) -> dict:
    art = _artifact(model_id)
    names = art["feature_names"]
    if isinstance(features, dict):
        unknown = sorted(set(features) - set(names))
        if unknown:
            raise InvalidRequestError(f"Unknown features: {unknown[:5]}")
        row = [features.get(n) for n in names]
    else:
        if len(features) != len(names):
            raise InvalidRequestError(f"Expected {len(names)} feature values, got {len(features)}")
        row = list(features)
    if any(v is not None and not math.isfinite(v) for v in row):
        raise InvalidRequestError("Feature values must be finite numbers or null")
    x = np.array([[np.nan if v is None else float(v) for v in row]])
    pre, est = art["preprocessor"], art["estimator"]
    angles = pre.transform(x)
    proba = float(est.predict_proba(angles)[0, 1])
    contributions = None
    sv = shap_values(est, pre.transform(art["background_raw"])[:10], angles, nsamples=100, seed=SEED)
    if sv is not None:
        contributions = [{"feature": f, "encoded_value": round(float(a), 4), "shap": round(float(s), 5)}
                         for f, a, s in zip(art["selected_features"], angles[0], sv[0])]
    return {"model_id": model_id, "dataset": art["dataset"], "model": art["model"],
            "probability_disease": proba, "predicted_label": int(proba >= 0.5),
            "positive_class": DATASETS[art["dataset"]]["positive_class"],
            "explanation": contributions, "disclaimer": DISCLAIMER}


def _artifact(model_id: str) -> dict:
    if not MODEL_ID_RE.match(model_id) or not (RESULTS_DIR / "models" / f"{model_id}.joblib").is_file():
        raise NotFoundError(f"Unknown model_id '{model_id}'")
    return _load_artifact(model_id)
