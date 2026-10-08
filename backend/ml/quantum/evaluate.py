"""Stratified k-fold evaluation, efficiency, generalisation gap and learning curves."""

import time

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedKFold, train_test_split

from backend.ml.quantum import SEED
from backend.ml.quantum.baselines import CLASSICAL_MODELS, build_baseline, count_params
from backend.ml.quantum.data import stratified_subsample
from backend.ml.quantum.hybrid_qnn import HybridQNNClassifier
from backend.ml.quantum.preprocess import make_preprocessor
from backend.ml.quantum.qkernel import QuantumKernelSVM
from backend.ml.quantum.vqc import VQCClassifier

QUANTUM_MODELS = ["qsvm", "vqc", "hybrid_qnn"]
ALL_MODELS = CLASSICAL_MODELS + QUANTUM_MODELS
METRIC_KEYS = ["accuracy", "sensitivity", "specificity", "auc", "f1"]


def build_model(name: str, n_qubits: int, seed: int = SEED, epochs: int = 40, n_layers: int = 2):
    if name == "qsvm":
        return QuantumKernelSVM(n_qubits=n_qubits, seed=seed)
    if name == "vqc":
        return VQCClassifier(n_qubits=n_qubits, n_layers=n_layers, epochs=epochs, seed=seed)
    if name == "hybrid_qnn":
        return HybridQNNClassifier(n_qubits=n_qubits, n_layers=n_layers, epochs=epochs, seed=seed)
    return build_baseline(name, seed)


def model_family(name: str) -> str:
    return "quantum" if name in ("qsvm", "vqc") else "hybrid" if name == "hybrid_qnn" else "classical"


def binary_metrics(y_true, y_pred, y_score) -> dict:
    """Positive class = 1 (disease). sensitivity = TP/(TP+FN); specificity = TN/(TN+FP)."""
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "sensitivity": float(tp / (tp + fn)) if tp + fn else float("nan"),
        "specificity": float(tn / (tn + fp)) if tn + fp else float("nan"),
        "auc": float(roc_auc_score(y_true, y_score)) if len(set(y_true)) == 2 else float("nan"),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }


def fit_and_score(name, X_train, y_train, X_val, y_val, n_qubits, seed=SEED, method="mutual_info", epochs=40):
    """Fit preprocessor + model on the training part only; return metrics, timings and the fitted pair."""
    pre = make_preprocessor(n_qubits, method, seed).fit(X_train, y_train)
    A_train, A_val = pre.transform(X_train), pre.transform(X_val)
    model = build_model(name, n_qubits, seed, epochs)
    t0 = time.perf_counter()
    model.fit(A_train, y_train)
    train_time = time.perf_counter() - t0
    t0 = time.perf_counter()
    score = model.predict_proba(A_val)[:, 1]
    infer_ms = (time.perf_counter() - t0) * 1000 / len(A_val)
    pred = (score >= 0.5).astype(int)
    train_pred = (model.predict_proba(A_train)[:, 1] >= 0.5).astype(int)  # same rule as validation
    train_acc = float(accuracy_score(y_train, train_pred))
    out = binary_metrics(y_val, pred, score)
    out.update(train_time_s=train_time, infer_ms_per_sample=infer_ms, train_accuracy=train_acc,
               gen_gap=train_acc - out["accuracy"])
    return out, score, pre, model


def cross_validate(name, X, y, n_qubits=6, n_splits=5, seed=SEED, max_train=200, method="mutual_info", epochs=40):
    """Stratified k-fold. Each training fold is subsampled to max_train rows (same rows for every model)."""
    folds, oof_true, oof_score = [], [], []
    model = None
    for train_idx, val_idx in StratifiedKFold(n_splits, shuffle=True, random_state=seed).split(X, y):
        X_tr, y_tr = stratified_subsample(X[train_idx], y[train_idx], max_train, seed)
        metrics, score, _, model = fit_and_score(name, X_tr, y_tr, X[val_idx], y[val_idx], n_qubits, seed, method, epochs)
        folds.append(metrics)
        oof_true.append(y[val_idx])
        oof_score.append(score)
    keys = METRIC_KEYS + ["train_time_s", "infer_ms_per_sample", "train_accuracy", "gen_gap"]
    summary = {k: {"mean": float(np.mean([f[k] for f in folds])), "std": float(np.std([f[k] for f in folds]))}
               for k in keys}
    fpr, tpr, _ = roc_curve(np.concatenate(oof_true), np.concatenate(oof_score))
    keep = np.unique(np.linspace(0, len(fpr) - 1, min(len(fpr), 60)).astype(int))
    return {
        "model": name,
        "family": model_family(name),
        "metrics": summary,
        "folds": folds,
        "roc": {"fpr": fpr[keep].round(4).tolist(), "tpr": tpr[keep].round(4).tolist()},
        "n_qubits": int(getattr(model, "n_qubits_", 0)) or None,
        "circuit_depth": int(getattr(model, "circuit_depth_", 0)) or None,
        "n_params": count_params(model),
        "loss_history": [round(v, 5) for v in getattr(model, "loss_history_", [])],
    }


def learning_curve(name, X, y, n_qubits=6, seed=SEED, max_train=200,
                   fractions=(0.2, 0.4, 0.6, 0.8, 1.0), method="mutual_info", epochs=40):
    """Single stratified 80/20 split; train on growing stratified subsets; report train/val accuracy."""
    X_tr, X_val, y_tr, y_val = train_test_split(X, y, test_size=0.2, stratify=y, random_state=seed)
    X_tr, y_tr = stratified_subsample(X_tr, y_tr, max_train, seed)
    points = []
    for frac in fractions:
        n = max(int(round(frac * len(y_tr))), 20)
        X_n, y_n = stratified_subsample(X_tr, y_tr, n, seed)
        metrics, *_ = fit_and_score(name, X_n, y_n, X_val, y_val, n_qubits, seed, method, epochs)
        points.append({"n_train": int(len(y_n)), "train_accuracy": metrics["train_accuracy"],
                       "val_accuracy": metrics["accuracy"]})
    return points
