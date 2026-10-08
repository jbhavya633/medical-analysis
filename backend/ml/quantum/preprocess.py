"""Classical front-end: impute -> standardise -> select k features -> scale to [0, pi] angles."""

from functools import partial

import numpy as np
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from backend.ml.quantum import SEED


def select_features(method: str, k: int, seed: int = SEED):
    if method == "mutual_info":
        return SelectKBest(score_func=partial(mutual_info_classif, random_state=seed), k=k)
    if method == "pca":
        return PCA(n_components=k, random_state=seed)
    raise ValueError(f"unknown feature selection method: {method}")


def make_preprocessor(k: int, method: str = "mutual_info", seed: int = SEED) -> Pipeline:
    """Fit on training data only; output has k columns in [0, pi] (clipped for unseen data)."""
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("select", select_features(method, k, seed)),
        ("angles", MinMaxScaler(feature_range=(0.0, np.pi), clip=True)),
    ])


def to_angles(X: np.ndarray) -> np.ndarray:
    """Min-max scale columns of X to [0, pi] (stand-alone helper)."""
    X = np.asarray(X, dtype=float)
    lo, hi = X.min(axis=0), X.max(axis=0)
    return np.pi * (X - lo) / np.where(hi > lo, hi - lo, 1.0)


def selected_feature_names(preprocessor: Pipeline, feature_names: list[str]) -> list[str]:
    selector = preprocessor.named_steps["select"]
    if isinstance(selector, SelectKBest):
        return [feature_names[i] for i in selector.get_support(indices=True)]
    return [f"PC{i + 1}" for i in range(selector.n_components_)]
