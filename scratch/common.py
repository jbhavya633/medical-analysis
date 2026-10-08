"""Shared helpers for exploratory sandbox checks. Exploratory, n too small for conclusions.

Reproduces the benchmark's fold/subsample logic (evaluate.cross_validate) without modifying backend/.
"""

import sys
import time
from pathlib import Path

import numpy as np
from sklearn.metrics import brier_score_loss, roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedKFold

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.ml.quantum import SEED  # noqa: E402
from backend.ml.quantum.data import load_dataset, stratified_subsample  # noqa: E402
from backend.ml.quantum.preprocess import make_preprocessor, selected_feature_names  # noqa: E402

LABEL = "exploratory, n too small for conclusions"


def folds(name, n_folds_used=2, n_qubits=6, max_train=200, seed=SEED):
    """Yield (fold_idx, A_train, y_train, A_val, y_val, selected) for the first n_folds_used benchmark folds."""
    X, y, feature_names = load_dataset(name)
    skf = StratifiedKFold(5, shuffle=True, random_state=seed)
    for k, (tr, va) in enumerate(skf.split(X, y)):
        if k >= n_folds_used:
            break
        X_tr, y_tr = stratified_subsample(X[tr], y[tr], max_train, seed)
        pre = make_preprocessor(n_qubits, "mutual_info", seed).fit(X_tr, y_tr)
        yield k, pre.transform(X_tr), y_tr, pre.transform(X[va]), y[va], selected_feature_names(pre, feature_names)


def ece(y, p, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    return float(sum(abs(p[idx == b].mean() - y[idx == b].mean()) * (idx == b).mean()
                     for b in range(bins) if (idx == b).any()))


def sens_at_spec(y, p, spec=0.90):
    fpr, tpr, _ = roc_curve(y, p)
    ok = fpr <= 1 - spec
    return float(tpr[ok].max()) if ok.any() else 0.0


def score(y, p):
    return {"auc": round(float(roc_auc_score(y, p)), 4), "acc": round(float(((p >= 0.5) == y).mean()), 4),
            "brier": round(float(brier_score_loss(y, p)), 4), "ece": round(ece(np.asarray(y), np.asarray(p)), 4),
            "sens@spec90": round(sens_at_spec(y, p), 4)}


class Timer:
    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *a):
        self.s = time.perf_counter() - self.t0
