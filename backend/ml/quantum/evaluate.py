"""Stratified k-fold evaluation, efficiency, generalisation gap and learning curves."""

import time

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import (
    GridSearchCV,
    ParameterGrid,
    StratifiedGroupKFold,
    StratifiedKFold,
    train_test_split,
)
from sklearn.pipeline import Pipeline

from backend.ml.quantum import SEED
from backend.ml.quantum.baselines import CLASSICAL_GRIDS, CLASSICAL_MODELS, build_baseline, count_params
from backend.ml.quantum.data import stratified_subsample
from backend.ml.quantum.hybrid_qnn import HybridQNNClassifier, ResidualQNNClassifier
from backend.ml.quantum.preprocess import make_preprocessor, select_features
from backend.ml.quantum.qkernel import QuantumKernelSVM
from backend.ml.quantum.vqc import TrigTwinClassifier, VQCClassifier

QUANTUM_MODELS = ["qsvm", "vqc", "hybrid_qnn"]
ALL_MODELS = CLASSICAL_MODELS + QUANTUM_MODELS
METRIC_KEYS = ["accuracy", "sensitivity", "specificity", "auc", "f1", "brier"]
SPECIFICITY_TARGETS = (0.90, 0.95)
INNER_FOLDS = 3
TUNING_GRIDS = {
    **CLASSICAL_GRIDS,
    # E3: bandwidth s of the ZZ map at C = 1 (main QSVM) vs the C-only control at s = 1 (qsvm_c)
    "qsvm": {"model__bandwidth": [0.1, 0.2, 0.35, 0.5, 0.75, 1.0]},
    "qsvm_c": {"model__C": [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]},
    "vqc": {"model__lr": [0.01, 0.05, 0.1], "model__epochs": [20, 40]},
    "hybrid_qnn": {"model__lr": [0.01, 0.05, 0.1], "model__epochs": [20, 40]},
}
# Experiment-only variants (docs/OPTIMIZATION_PLAN.md E4/E6), each trained exactly like its parent; not part of
# the main comparison table. Parameter counts at 6 qubits: vqc 26; vqc_3layer, vqc_scale, vqc_reupload_scale 38.
VQC_VARIANTS = {
    "vqc_3layer": {"n_layers": 3},                    # parameter-matched capacity control
    "vqc_scale": {"input_scaling": "affine"},         # trainable a_i x_i + b_i, encoded once
    "vqc_reupload_scale": {"input_scaling": "reupload"},
    "vqc_allz": {"readout": "allz"},                  # every qubit reaches the output, so the next is a fair ablation
    "vqc_allz_noent": {"readout": "allz", "entangle": False},
}
TUNING_GRIDS.update({m: TUNING_GRIDS["vqc"] for m in VQC_VARIANTS})
TUNING_GRIDS["hybrid_classical"] = TUNING_GRIDS["hybrid_qnn"]
FS_SUFFIX = "_fs"


def feature_selection_grid(name: str, seed: int = SEED) -> list[dict]:
    """E11: k in {4, 6, 8} x {mutual information, PCA} as the 6 inner configurations, model hyperparameters at
    their defaults. Quantum models need one qubit per feature, so n_qubits moves with k."""
    grid = []
    for k in (4, 6, 8):
        for method in ("mutual_info", "pca"):
            config = {"pre__select": [select_features(method, k, seed)]}
            if model_family(name) != "classical":
                config["model__n_qubits"] = [k]
            grid.append(config)
    return grid


# D4 controls (master prompt v2): classical twin of the re-uploading VQC, residual heads, and the untuned QSVM.
TUNING_GRIDS.update({"vqc_twin": TUNING_GRIDS["vqc"], "residual_qnn": TUNING_GRIDS["vqc"],
                     "residual_classical": TUNING_GRIDS["vqc"],
                     "qsvm_fixed": {"model__C": [1.0]}})  # untuned control (s = 1, C = 1): one configuration
UNTUNED_CONTROLS = ["qsvm_fixed"]
CONTROL_MODELS = ["mlp_matched", "vqc_twin", "residual_qnn", "residual_classical", "qsvm_fixed"]
EXPERIMENT_MODELS = ["qsvm_c", *VQC_VARIANTS, "hybrid_classical", *CONTROL_MODELS,
                     *(m + FS_SUFFIX for m in ALL_MODELS)]
QUANTUM_NAMES = {"qsvm", "qsvm_c", "qsvm_fixed", "vqc", *VQC_VARIANTS}
HYBRID_NAMES = {"hybrid_qnn", "residual_qnn"}


def build_model(name: str, n_qubits: int, seed: int = SEED, epochs: int = 40, n_layers: int = 2):
    name = name.removesuffix(FS_SUFFIX)
    if name in ("qsvm", "qsvm_c", "qsvm_fixed"):
        return QuantumKernelSVM(n_qubits=n_qubits, seed=seed)
    if name == "vqc" or name in VQC_VARIANTS:
        options = {"n_layers": n_layers, **VQC_VARIANTS.get(name, {})}
        return VQCClassifier(n_qubits=n_qubits, epochs=epochs, seed=seed, **options)
    if name in ("hybrid_qnn", "hybrid_classical"):
        return HybridQNNClassifier(n_qubits=n_qubits, n_layers=n_layers, epochs=epochs, seed=seed,
                                   quantum=name == "hybrid_qnn")
    if name == "vqc_twin":
        return TrigTwinClassifier(n_qubits=n_qubits, n_layers=n_layers, epochs=epochs, seed=seed)
    if name in ("residual_qnn", "residual_classical"):
        return ResidualQNNClassifier(n_qubits=n_qubits, n_layers=n_layers, epochs=epochs, seed=seed,
                                     quantum=name == "residual_qnn")
    return build_baseline(name, seed)


def model_family(name: str) -> str:
    name = name.removesuffix(FS_SUFFIX)
    if name in QUANTUM_NAMES:
        return "quantum"
    if name in HYBRID_NAMES:
        return "hybrid"
    return "classical"


TUNING_GRIDS.update({m + FS_SUFFIX: feature_selection_grid(m) for m in ALL_MODELS})


def describe(value):
    """JSON-friendly description of a grid value (selector objects become e.g. "mutual_info(k=6)")."""
    if hasattr(value, "n_components"):
        return f"pca(k={value.n_components})"
    if hasattr(value, "k") and hasattr(value, "score_func"):
        return f"mutual_info(k={value.k})"
    return value


def describe_grid(grid):
    grids = grid if isinstance(grid, list) else [grid]
    out = [{k: [describe(v) for v in vs] for k, vs in g.items()} for g in grids]
    return out if isinstance(grid, list) else out[0]


def binary_metrics(y_true, y_pred, y_score) -> dict:
    """Positive class = 1 (disease). sensitivity = TP/(TP+FN); specificity = TN/(TN+FP)."""
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "sensitivity": float(tp / (tp + fn)) if tp + fn else float("nan"),
        "specificity": float(tn / (tn + fp)) if tn + fp else float("nan"),
        "auc": float(roc_auc_score(y_true, y_score)) if len(set(y_true)) == 2 else float("nan"),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "brier": float(brier_score_loss(y_true, y_score)),
    }


def sensitivity_at_specificity(y_true, y_score, specificity: float) -> float:
    """Highest sensitivity among ROC thresholds whose specificity is >= the target."""
    fpr, tpr, _ = roc_curve(y_true, y_score)
    ok = fpr <= 1 - specificity + 1e-12
    return float(tpr[ok].max())


def reliability(y_true, y_score, n_bins: int = 10) -> tuple[float, list[dict]]:
    """Expected calibration error (equal-width bins, weighted by bin size) and the per-bin points."""
    y_true, y_score = np.asarray(y_true, dtype=float), np.asarray(y_score, dtype=float)
    bins = np.clip((y_score * n_bins).astype(int), 0, n_bins - 1)
    points, ece = [], 0.0
    for b in range(n_bins):
        mask = bins == b
        if mask.any():
            mean_pred, frac_pos = float(y_score[mask].mean()), float(y_true[mask].mean())
            ece += abs(mean_pred - frac_pos) * mask.mean()
            points.append({"bin": b, "mean_pred": round(mean_pred, 4), "frac_pos": round(frac_pos, 4),
                           "n": int(mask.sum())})
    return float(ece), points


def calibration_slope_intercept(y_true, y_score, eps=1e-6) -> dict:
    """Logistic recalibration (Van Calster et al. 2019): slope from logit(y) ~ a + b * logit(p); calibration-in-the-
    large intercept from logit(y) ~ a + offset(logit(p)). Ideal: slope 1, intercept 0. Newton-Raphson, no penalty."""
    y = np.asarray(y_true, dtype=float)
    lp = np.log(np.clip(y_score, eps, 1 - eps) / (1 - np.clip(y_score, eps, 1 - eps)))

    def newton(X, offset):
        beta = np.zeros(X.shape[1])
        for _ in range(50):
            p = 1 / (1 + np.exp(-(X @ beta + offset)))
            W = p * (1 - p) + 1e-12
            step = np.linalg.solve(X.T @ (X * W[:, None]) + 1e-9 * np.eye(X.shape[1]), X.T @ (y - p))
            beta += step
            if np.max(np.abs(step)) < 1e-8:
                break
        return beta

    slope = newton(np.column_stack([np.ones_like(lp), lp]), 0.0)[1]
    intercept = newton(np.ones((len(lp), 1)), lp)[0]
    return {"slope": float(slope), "intercept": float(intercept)}


DCA_THRESHOLDS = tuple(round(t, 2) for t in np.arange(0.05, 0.51, 0.05))


def decision_curve(y_true, y_score, thresholds=DCA_THRESHOLDS) -> list[dict]:
    """Net benefit = TP/n - FP/n * t/(1-t) for the model, treat-all and treat-none (= 0) at each threshold t."""
    y = np.asarray(y_true)
    n, prev = len(y), float(np.mean(y))
    out = []
    for t in thresholds:
        pred = np.asarray(y_score) >= t
        tp, fp = float(np.sum(pred & (y == 1))), float(np.sum(pred & (y == 0)))
        out.append({"threshold": t, "model": tp / n - fp / n * t / (1 - t),
                    "treat_all": prev - (1 - prev) * t / (1 - t)})
    return out


def calibration_summary(y_true, y_score) -> dict:
    """Pooled out-of-fold calibration and decision metrics (per-fold ECE at ~60 rows is too noisy)."""
    ece, points = reliability(y_true, y_score)
    return {"brier": float(brier_score_loss(y_true, y_score)), "ece": ece, "reliability": points,
            **calibration_slope_intercept(y_true, y_score),
            "sens_at_spec": {f"{s:.2f}": sensitivity_at_specificity(y_true, y_score, s) for s in SPECIFICITY_TARGETS},
            "decision_curve": decision_curve(y_true, y_score)}


def tune(name, X_train, y_train, n_qubits, seed=SEED, method="mutual_info", epochs=40, groups=None):
    """Nested-CV inner loop on the training part only: preprocessor + model in one Pipeline, so supervised
    feature selection is refitted inside every inner fold. Returns the refitted best pipeline and the search.
    groups (same subject / identical rows) keeps each group inside one inner fold."""
    pipe = Pipeline([("pre", make_preprocessor(n_qubits, method, seed)), ("model", build_model(name, n_qubits, seed, epochs))])
    inner = (StratifiedGroupKFold(INNER_FOLDS, shuffle=True, random_state=seed) if groups is not None
             else StratifiedKFold(INNER_FOLDS, shuffle=True, random_state=seed))
    search = GridSearchCV(pipe, TUNING_GRIDS[name], scoring="roc_auc", refit=True, n_jobs=1, error_score="raise",
                          cv=inner)
    search.fit(X_train, y_train, groups=groups)
    return search.best_estimator_, search


def fit_and_score(name, X_train, y_train, X_val, y_val, n_qubits, seed=SEED, method="mutual_info", epochs=40,
                  tuned=False, groups=None):
    """Fit preprocessor + model on the training part only; return metrics, timings and the fitted pair.

    tuned=True runs the nested inner search (tune) first; train_time_s then covers the whole search.
    """
    t0 = time.perf_counter()
    tuning = {}
    if tuned:
        best, search = tune(name, X_train, y_train, n_qubits, seed, method, epochs, groups)
        pre, model = best.named_steps["pre"], best.named_steps["model"]
        tuning = {"best_params": {k.split("__")[-1]: describe(v) for k, v in search.best_params_.items()},
                  "inner_auc": float(search.best_score_), "n_configs": len(ParameterGrid(TUNING_GRIDS[name]))}
        A_train = pre.transform(X_train)
    else:
        pre = make_preprocessor(n_qubits, method, seed).fit(X_train, y_train)
        A_train = pre.transform(X_train)
        model = build_model(name, n_qubits, seed, epochs)
        t0 = time.perf_counter()
        model.fit(A_train, y_train)
    train_time = time.perf_counter() - t0
    A_val = pre.transform(X_val)
    t0 = time.perf_counter()
    score = model.predict_proba(A_val)[:, 1]
    infer_ms = (time.perf_counter() - t0) * 1000 / len(A_val)
    pred = (score >= 0.5).astype(int)
    train_pred = (model.predict_proba(A_train)[:, 1] >= 0.5).astype(int)  # same rule as validation
    train_acc = float(accuracy_score(y_train, train_pred))
    out = binary_metrics(y_val, pred, score)
    out.update(balanced_accuracy=float(balanced_accuracy_score(y_val, pred)),
               mcc=float(matthews_corrcoef(y_val, pred)))
    out.update(train_time_s=train_time, infer_ms_per_sample=infer_ms, train_accuracy=train_acc,
               gen_gap=train_acc - out["accuracy"], **tuning)
    if hasattr(model, "kernel_spectrum_"):
        out["kernel_spectrum"] = model.kernel_spectrum_
    selector = pre.named_steps["select"]
    if hasattr(selector, "get_support"):  # mutual-information selection: which raw features were kept
        out["selected_idx"] = selector.get_support(indices=True).tolist()
    return out, score, pre, model


def jaccard_stability(sets: list[list[int]]) -> float | None:
    """Mean pairwise Jaccard index of the feature sets selected in different folds (1 = always the same)."""
    pairs = [(set(a), set(b)) for i, a in enumerate(sets) for b in sets[i + 1:]]
    return float(np.mean([len(a & b) / len(a | b) for a, b in pairs])) if pairs else None


def cross_validate(name, X, y, n_qubits=6, n_splits=5, seed=SEED, max_train=200, method="mutual_info", epochs=40,
                   tuned=False):
    """Stratified k-fold. Each training fold is subsampled to max_train rows (same rows for every model).

    Every row is scored exactly once, by the model of the fold where it is a validation row (pooled OOF).
    tuned=True: nested CV, hyperparameters chosen inside each outer training fold (outer rows never seen).
    """
    folds = []
    oof_score, oof_fold = np.full(len(y), np.nan), np.full(len(y), -1)
    model = None
    for k, (train_idx, val_idx) in enumerate(StratifiedKFold(n_splits, shuffle=True, random_state=seed).split(X, y)):
        X_tr, y_tr = stratified_subsample(X[train_idx], y[train_idx], max_train, seed)
        metrics, score, _, model = fit_and_score(name, X_tr, y_tr, X[val_idx], y[val_idx], n_qubits, seed, method,
                                                 epochs, tuned)
        folds.append(metrics)
        oof_score[val_idx], oof_fold[val_idx] = score, k
    keys = METRIC_KEYS + ["train_time_s", "infer_ms_per_sample", "train_accuracy", "gen_gap"]
    summary = {k: {"mean": float(np.mean([f[k] for f in folds])), "std": float(np.std([f[k] for f in folds]))}
               for k in keys}
    fpr, tpr, _ = roc_curve(y, oof_score)
    keep = np.unique(np.linspace(0, len(fpr) - 1, min(len(fpr), 60)).astype(int))
    tuning = None
    if tuned:
        inner = float(np.mean([f["inner_auc"] for f in folds]))
        tuning = {"n_configs": folds[0]["n_configs"], "inner_folds": INNER_FOLDS,
                  "grid": describe_grid(TUNING_GRIDS[name]),
                  "chosen": [f["best_params"] for f in folds], "inner_auc_mean": inner,
                  # best inner-CV AUC overstates what the chosen setting achieves on unseen rows (Varma & Simon)
                  "optimism": inner - summary["auc"]["mean"]}
    mi_sets = [f["selected_idx"] for f in folds if "selected_idx" in f]
    feature_stability = jaccard_stability(mi_sets) if len(mi_sets) == len(folds) else None
    return {
        "tuning": tuning,
        "feature_stability_jaccard": feature_stability,
        "model": name,
        "family": model_family(name),
        "metrics": summary,
        "folds": folds,
        "roc": {"fpr": fpr[keep].round(4).tolist(), "tpr": tpr[keep].round(4).tolist()},
        "n_qubits": int(getattr(model, "n_qubits_", 0)) or None,
        "circuit_depth": int(getattr(model, "circuit_depth_", 0)) or None,
        "n_params": count_params(model),
        "loss_history": [round(v, 5) for v in getattr(model, "loss_history_", [])],
        "oof": {"score": oof_score.round(5).tolist(), "fold": oof_fold.tolist()},
        "calibration": calibration_summary(y, oof_score),
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
