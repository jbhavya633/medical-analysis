"""Explainability: permutation importance, SHAP (KernelExplainer), kernel alignment, feature-map sensitivity."""

import logging

import numpy as np
from sklearn.inspection import permutation_importance

from backend.ml.quantum import SEED
from backend.ml.quantum.qkernel import kernel_from_states, statevectors

logger = logging.getLogger(__name__)

try:
    import shap
except ImportError:  # pragma: no cover - fallback documented in DECISIONS.md
    shap = None


def permutation_scores(model, X, y, feature_names, seed=SEED, n_repeats=5) -> dict:
    result = permutation_importance(model, X, y, scoring="roc_auc", n_repeats=n_repeats, random_state=seed)
    return {name: round(float(v), 5) for name, v in zip(feature_names, result.importances_mean)}


def shap_scores(model, X_background, X_explain, feature_names, nsamples=100, seed=SEED) -> dict | None:
    """Mean |SHAP| per feature for P(disease); model-agnostic so it covers classical and quantum models."""
    values = shap_values(model, X_background, X_explain, nsamples, seed)
    if values is None:
        return None
    return {name: round(float(v), 5) for name, v in zip(feature_names, np.abs(values).mean(axis=0))}


def shap_values(model, X_background, X_explain, nsamples=100, seed=SEED):
    if shap is None:
        return None
    np.random.seed(seed)
    explainer = shap.KernelExplainer(lambda Z: model.predict_proba(Z)[:, 1], X_background)
    return np.asarray(explainer.shap_values(X_explain, nsamples=nsamples, silent=True)).reshape(len(X_explain), -1)


def kernel_alignment(K: np.ndarray, y: np.ndarray) -> float:
    """Kernel-target alignment <K, yy^T>_F / (||K||_F ||yy^T||_F) with labels mapped to +/-1."""
    t = np.where(np.asarray(y) == 1, 1.0, -1.0)
    Y = np.outer(t, t)
    return float(np.sum(K * Y) / (np.linalg.norm(K) * np.linalg.norm(Y)))


def feature_map_sensitivity(X: np.ndarray, n_qubits: int, feature_names, eps=0.1, reps=2, bandwidth=1.0) -> dict:
    """Mean infidelity 1 - |<psi(x)|psi(x + eps e_i)>|^2 per input feature (how strongly the map reacts)."""
    base = statevectors(X, n_qubits, reps, bandwidth)
    out = {}
    for i, name in enumerate(feature_names):
        Xp = X.copy()
        Xp[:, i] = np.clip(Xp[:, i] + eps, 0, np.pi)
        fid = np.diag(kernel_from_states(base, statevectors(Xp, n_qubits, reps, bandwidth)))
        out[name] = round(float(np.mean(1 - fid)), 6)
    return out
