"""Public biomedical benchmark datasets with a local cache. Positive class (1) = disease present."""

import logging
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split

from backend.ml.quantum import SEED

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parent / "data_cache"
HEART_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data"
HEART_COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal",
]

DATASETS = {
    "breast_cancer": {
        "title": "Breast Cancer Wisconsin (Diagnostic)",
        "positive_class": "malignant",
        "source": "UCI ML Repository via scikit-learn load_breast_cancer",
        "url": "https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic",
        "licence": "CC BY 4.0",
    },
    "heart": {
        "title": "Heart Disease (Cleveland)",
        "positive_class": "heart disease present (num > 0)",
        "source": "UCI ML Repository, processed.cleveland.data",
        "url": "https://archive.ics.uci.edu/dataset/45/heart+disease",
        "licence": "CC BY 4.0",
    },
}


class DatasetUnavailableError(RuntimeError):
    """Raised when a dataset cannot be loaded (e.g. offline and not cached)."""


def load_dataset(name: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Built-in datasets load here; every other registered dataset loads through backend.ml.quantum.registry."""
    if name in DATASETS:
        return load_builtin(name)
    from backend.ml.quantum import registry
    if name in registry.REGISTRY:
        return registry.load(registry.REGISTRY[name])
    raise KeyError(f"unknown dataset: {name}")


def dataset_info(name: str) -> dict:
    """Title, source, licence and positive class for any registered dataset (built-in or registry)."""
    if name in DATASETS:
        return DATASETS[name]
    from backend.ml.quantum import registry
    e = registry.REGISTRY[name]
    return {"title": e.title, "positive_class": e.positive_class, "source": e.source, "url": e.url,
            "licence": e.licence, "split": e.split, "provenance": e.provenance}


def load_builtin(name: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    if name == "breast_cancer":
        data = load_breast_cancer()
        return data.data.astype(float), (data.target == 0).astype(int), list(data.feature_names)
    if name == "heart":
        df = _load_heart()
        y = (df["num"] > 0).astype(int).to_numpy()
        return df[HEART_COLUMNS].to_numpy(dtype=float), y, list(HEART_COLUMNS)
    raise KeyError(f"unknown dataset: {name}")


def _load_heart() -> pd.DataFrame:
    path = CACHE_DIR / "processed.cleveland.data"
    if not path.is_file():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with urllib.request.urlopen(HEART_URL, timeout=20) as resp:
                path.write_bytes(resp.read())
        except OSError as exc:
            raise DatasetUnavailableError("heart dataset not cached and download failed (offline?)") from exc
    return pd.read_csv(path, header=None, names=HEART_COLUMNS + ["num"], na_values="?")


def holdout_split(X, y, test_size=0.2, seed=SEED):
    """Stratified train/test split used for the prediction demo and saved models."""
    return train_test_split(X, y, test_size=test_size, stratify=y, random_state=seed)


def stratified_subsample(X, y, n, seed=SEED):
    """Stratified subsample of at most n rows (identical for every model, for fairness)."""
    if len(y) <= n:
        return X, y
    X_sub, _, y_sub, _ = train_test_split(X, y, train_size=n, stratify=y, random_state=seed)
    return X_sub, y_sub
