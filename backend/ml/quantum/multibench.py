"""Multi-dataset benchmark runner (master prompt v2 P4; protocol in docs/PREREGISTRATION.md).

Unit of work = (dataset, model, repeat, fold). Each unit runs the nested-CV fit of evaluate.fit_and_score on the outer
training fold (stratified-subsampled to 200 rows, seed 42 + repeat), scores the outer validation fold, and writes one
JSON checkpoint. Relaunching skips finished checkpoints, so sleep/restart loses at most the units in flight.
Workers run in separate processes with one torch/BLAS thread each.

Leakage controls: folds keep subject groups (registry.group_column) and identical feature rows together
(StratifiedGroupKFold); tuning, imputation, scaling, feature selection and encoding-to-angles all happen inside the
per-fold Pipeline on training rows only; outer validation rows are only scored.

python -m backend.ml.quantum.multibench run --split development --models logreg,qsvm --repeats 3 --workers 6
python -m backend.ml.quantum.multibench aggregate
"""

import argparse
import json
import logging
import os
import time
import traceback
import zlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold

from backend.ml.quantum import SEED
from backend.ml.quantum.benchmark import MODEL_LABELS, RESULTS_DIR
from backend.ml.quantum.data import dataset_info, load_dataset, stratified_subsample
from backend.ml.quantum.evaluate import calibration_summary, fit_and_score, model_family
from backend.ml.quantum.stats import (
    corrected_resampled_ttest,
    friedman_nemenyi,
    holm,
    wilcoxon_holm_pairs,
    win_tie_loss,
)

MULTI_DIR = Path(os.getenv("QML_MULTI_DIR", RESULTS_DIR / "multi"))
N_FOLDS, MAX_TRAIN, N_QUBITS = 5, 200, 6
logger = logging.getLogger("qml.multibench")

# Main comparison and pre-specified pairs (docs/PREREGISTRATION.md section 6). "best VQC variant" is resolved from
# the development results before the confirmation run and recorded in the run config.
MAIN_CLASSICAL = ["logreg", "svm_rbf", "random_forest", "mlp", "hgb"]
PAIRS = [
    ("qsvm", "logreg"),               # P-H1
    ("qsvm", "qsvm_fixed"),           # P-H3
    ("vqc_scale", "vqc_3layer"),      # P-H4 (input scaling vs parameter-matched depth)
    ("vqc_reupload_scale", "vqc_3layer"),
    ("vqc_3layer", "mlp_matched"),    # P-H4 (quantum vs parameter-matched classical)
    ("vqc_allz_noent", "vqc_allz"),   # P-H5
    ("hybrid_qnn", "hybrid_classical"),  # P-H6
    ("residual_qnn", "residual_classical"),  # P-H7
    ("vqc_reupload_scale", "vqc_twin"),  # P-H8
    ("vqc", "logreg"), ("hybrid_qnn", "logreg"), ("qsvm", "hgb"),
]


# --------------------------------------------------------------------------------------------------------------
# folds

def duplicate_groups(X: np.ndarray) -> np.ndarray:
    """Group id per row: identical feature vectors (NaN-aware) share a group, so copies never straddle folds."""
    key = np.where(np.isnan(X), np.inf, X)
    _, inverse = np.unique(key, axis=0, return_inverse=True)
    return inverse.reshape(-1)


@lru_cache(maxsize=32)
def dataset_arrays(name: str):
    from backend.ml.quantum import registry
    X, y, names = load_dataset(name)
    g = registry.groups(registry.REGISTRY[name]) if name in registry.REGISTRY else None
    if g is not None:  # subject groups; identical rows within a subject are already together
        _, g = np.unique(g, return_inverse=True)
    else:
        g = duplicate_groups(X)
    grouped = len(np.unique(g)) < len(g)
    return X, y, names, (g if grouped else None)


def outer_folds(name: str, repeat: int) -> list[tuple[np.ndarray, np.ndarray]]:
    X, y, _, g = dataset_arrays(name)
    seed = SEED + repeat
    if g is not None:
        return list(StratifiedGroupKFold(N_FOLDS, shuffle=True, random_state=seed).split(X, y, g))
    return list(StratifiedKFold(N_FOLDS, shuffle=True, random_state=seed).split(X, y))


# --------------------------------------------------------------------------------------------------------------
# one unit of work

def ckpt_path(dataset, model, repeat, fold) -> Path:
    return MULTI_DIR / "checkpoints" / dataset / model / f"r{repeat}_f{fold}.json"


def _init_worker():
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    import torch
    torch.set_num_threads(1)
    import warnings
    warnings.filterwarnings("ignore")


def run_unit(dataset: str, model: str, repeat: int, fold: int) -> dict:
    X, y, _, g = dataset_arrays(dataset)
    tr, va = outer_folds(dataset, repeat)[fold]
    seed = SEED + repeat
    if len(tr) > MAX_TRAIN:
        keep, _ = stratified_subsample(tr.reshape(-1, 1), y[tr], MAX_TRAIN, seed)
        tr = keep.reshape(-1)
    g_tr = g[tr] if g is not None else None
    t0 = time.perf_counter()
    metrics, score, pre, est = fit_and_score(model, X[tr], y[tr], X[va], y[va], N_QUBITS, SEED, tuned=True,
                                             groups=g_tr)
    out = {"dataset": dataset, "model": model, "repeat": repeat, "fold": fold, "n_train": int(len(tr)),
           "n_test": int(len(va)), "val_idx": va.tolist(), "score": np.round(score, 6).tolist(),
           "metrics": {k: v for k, v in metrics.items() if not isinstance(v, (dict, list))},
           "best_params": metrics.get("best_params"), "inner_auc": metrics.get("inner_auc"),
           "kernel_spectrum": metrics.get("kernel_spectrum"),
           "n_params": int(getattr(est, "n_params_", 0)) or None,
           "n_qubits": int(getattr(est, "n_qubits_", 0)) or None,
           "circuit_depth": int(getattr(est, "circuit_depth_", 0)) or None,
           "wall_s": round(time.perf_counter() - t0, 2)}
    path = ckpt_path(dataset, model, repeat, fold)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, default=_json_default), encoding="utf-8")
    tmp.replace(path)  # atomic: a half-written checkpoint never counts as done
    return out


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, tuple):
        return list(o)
    return str(o)


def pending_units(datasets, models, repeats) -> list[tuple]:
    return [(d, m, r, k) for d in datasets for m in models for r in range(repeats) for k in range(N_FOLDS)
            if not ckpt_path(d, m, r, k).is_file()]


COST_ORDER = ["hybrid", "quantum"]  # heavy first so workers are never idle at the end


def run(datasets, models, repeats, workers) -> dict:
    units = pending_units(datasets, models, repeats)
    units.sort(key=lambda u: (model_family(u[1]) not in COST_ORDER, u[1] in ("qsvm", "qsvm_fixed", "qsvm_c")))
    logger.info("%d units pending (%d datasets x %d models x %d repeats x %d folds), %d workers",
                len(units), len(datasets), len(models), repeats, N_FOLDS, workers)
    done, failed, t0 = 0, [], time.perf_counter()
    os.environ["OMP_NUM_THREADS"] = "1"
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker) as pool:
        futures = {pool.submit(_safe_unit, *u): u for u in units}
        for fut in as_completed(futures):
            u = futures[fut]
            res = fut.result()
            if "error" in res:
                failed.append(u)
                logger.error("FAILED %s: %s", u, res["error"])
            else:
                done += 1
                logger.info("done %s auc %.3f wall %.1fs [%d/%d, %.0f min elapsed]", u, res["metrics"]["auc"],
                            res["wall_s"], done, len(units), (time.perf_counter() - t0) / 60)
    return {"done": done, "failed": failed}


def _safe_unit(*u):
    try:
        return run_unit(*u)
    except Exception:  # noqa: BLE001 - logged by the parent; the unit stays pending and is retried on relaunch
        return {"error": traceback.format_exc(limit=5)}


# --------------------------------------------------------------------------------------------------------------
# aggregation

def load_checkpoints(dataset, model, repeats) -> list[dict] | None:
    paths = [ckpt_path(dataset, model, r, k) for r in range(repeats) for k in range(N_FOLDS)]
    if not all(p.is_file() for p in paths):
        return None
    return [json.loads(p.read_text(encoding="utf-8")) for p in paths]


def summarise_model(units: list[dict], y: np.ndarray, repeats: int) -> dict:
    keys = ["auc", "balanced_accuracy", "accuracy", "sensitivity", "specificity", "f1", "brier", "mcc",
            "train_time_s", "infer_ms_per_sample"]
    per_fold = {k: [u["metrics"][k] for u in units] for k in keys}
    pooled = []
    for r in range(repeats):
        s = np.full(len(y), np.nan)
        for u in units:
            if u["repeat"] == r:
                s[u["val_idx"]] = u["score"]
        pooled.append(s)
    cal = [calibration_summary(y, s) for s in pooled]
    from sklearn.metrics import roc_auc_score
    pooled_auc = [float(roc_auc_score(y, s)) for s in pooled]

    def mean_sd(v):
        return {"mean": float(np.mean(v)), "sd": float(np.std(v, ddof=1)) if len(v) > 1 else 0.0}

    return {
        "metrics": {k: mean_sd(v) for k, v in per_fold.items()},
        "fold_auc": per_fold["auc"],
        "pooled_auc": mean_sd(pooled_auc),
        "calibration": {"brier": mean_sd([c["brier"] for c in cal]), "ece": mean_sd([c["ece"] for c in cal]),
                        "slope": mean_sd([c["slope"] for c in cal]), "intercept": mean_sd([c["intercept"] for c in cal]),
                        "sens_at_spec_90": mean_sd([c["sens_at_spec"]["0.90"] for c in cal]),
                        "sens_at_spec_95": mean_sd([c["sens_at_spec"]["0.95"] for c in cal]),
                        "reliability_r0": cal[0]["reliability"], "decision_curve_r0": cal[0]["decision_curve"]},
        "oof_r0": np.round(pooled[0], 5).tolist(),
        "chosen": [u["best_params"] for u in units],
        "inner_auc_mean": float(np.mean([u["inner_auc"] for u in units if u["inner_auc"] is not None]))
        if any(u["inner_auc"] is not None for u in units) else None,
        "n_params": units[0]["n_params"], "n_qubits": units[0]["n_qubits"], "circuit_depth": units[0]["circuit_depth"],
        "kernel_spectrum_mean": {k: float(np.mean([u["kernel_spectrum"][k] for u in units]))
                                 for k in units[0]["kernel_spectrum"]} if units[0].get("kernel_spectrum") else None,
        "n_train_mean": float(np.mean([u["n_train"] for u in units])),
        "n_test_mean": float(np.mean([u["n_test"] for u in units])),
    }


def complexity(name: str) -> dict:
    """E19 diagnostics on the full feature matrix (descriptive only; never used for any model decision)."""
    X, y, names, g = dataset_arrays(name)
    Xi = np.where(np.isnan(X), np.nanmedian(X, axis=0), X)
    Xi = np.nan_to_num(Xi)
    sd = Xi.std(axis=0)
    Z = (Xi - Xi.mean(axis=0)) / np.where(sd > 0, sd, 1)
    lam = np.clip(np.linalg.eigvalsh(np.cov(Z, rowvar=False)), 0, None)[::-1]
    cum = np.cumsum(lam) / lam.sum()
    raw = np.round(Z, 2).astype(np.float32).tobytes()
    return {"n": int(len(y)), "d": int(X.shape[1]), "positive_rate": float(y.mean()),
            "minority_rate": float(min(y.mean(), 1 - y.mean())),
            "cov_effective_dim": float(lam.sum() ** 2 / (lam ** 2).sum()),
            "pca_dims_90": int(np.searchsorted(cum, 0.90) + 1),
            "compression_ratio": len(zlib.compress(raw, 9)) / len(raw),
            "missing_rate": float(np.isnan(X).mean()), "grouped_folds": g is not None}


def aggregate(datasets, models, repeats) -> dict:
    per_dataset, scores, briers = {}, {}, {}
    for d in datasets:
        X, y, _, g = dataset_arrays(d)
        res = {}
        for m in models:
            units = load_checkpoints(d, m, repeats)
            if units is not None:
                res[m] = summarise_model(units, y, repeats)
        if not res:
            continue
        tests = {}
        for a, b in PAIRS:
            if a in res and b in res:
                t = corrected_resampled_ttest(res[a]["fold_auc"], res[b]["fold_auc"],
                                              int(round(res[a]["n_train_mean"])), int(round(res[a]["n_test_mean"])))
                tests[f"{a}|{b}"] = t
        for (key, t), p_adj in zip(tests.items(), holm([t["p"] for t in tests.values()])):
            t.update(p_holm=p_adj, significant=bool(p_adj < 0.05))
        info = dataset_info(d)
        per_dataset[d] = {"dataset": d, "title": info["title"], "split": info.get("split", "development"),
                          "y": y.astype(int).tolist(), "grouped_folds": g is not None, "models": res, "tests": tests,
                          "complexity": complexity(d)}
        for m, r in res.items():
            scores.setdefault(m, {})[d] = r["pooled_auc"]["mean"]
            briers.setdefault(m, {})[d] = r["calibration"]["brier"]["mean"]
        (MULTI_DIR / f"{d}.json").write_text(json.dumps(per_dataset[d], indent=1, default=_json_default),
                                             encoding="utf-8")
    return per_dataset, scores, briers


def cross_dataset(per_dataset, scores, briers, main_models) -> dict:
    complete = {m: s for m, s in scores.items() if m in main_models and len(s) == len(per_dataset)}
    friedman = friedman_nemenyi(complete) if len(complete) >= 3 and len(per_dataset) >= 2 else None
    pairs = [(a, b) for a, b in PAIRS if a in scores and b in scores]
    wilcoxon = wilcoxon_holm_pairs(scores, pairs)
    wtl = {f"{a}|{b}": win_tie_loss({d: v["tests"][f"{a}|{b}"] for d, v in per_dataset.items()
                                      if f"{a}|{b}" in v["tests"]}) for a, b in pairs}
    brier_vs_lr = wilcoxon_holm_pairs(briers, [(m, "logreg") for m in briers if m != "logreg" and "logreg" in briers])
    classical = [m for m in MAIN_CLASSICAL if m in scores]
    quantum = [m for m in scores if model_family(m) != "classical" and m in main_models]
    gaps, diag = {}, {}
    for d, v in per_dataset.items():
        cl = [scores[m][d] for m in classical if d in scores[m]]
        qu = [scores[m][d] for m in quantum if d in scores[m]]
        if cl and qu:
            gaps[d] = max(qu) - max(cl)
            diag[d] = v["complexity"]
            ks = v["models"].get("qsvm", {}).get("kernel_spectrum_mean")
            if ks:
                diag[d] = {**diag[d], "qsvm_mean_offdiag": ks["mean_offdiag"], "qsvm_eff_rank_ratio": ks["eff_rank_ratio"]}
    correlations = {}
    ds = sorted(gaps)
    rng = np.random.default_rng(SEED)
    if len(ds) >= 5:
        for key in diag[ds[0]]:
            if isinstance(diag[ds[0]][key], bool):
                continue
            xs, ys = np.array([diag[d][key] for d in ds], float), np.array([gaps[d] for d in ds])
            if len(np.unique(xs)) < 2 or len(np.unique(ys)) < 2:  # constant: correlation undefined
                correlations[key] = {"rho": None, "ci95": None, "significant": False}
                continue
            rho = spearmanr(xs, ys).statistic
            boots = []
            for _ in range(2000):
                i = rng.integers(0, len(ds), len(ds))
                if len(np.unique(xs[i])) > 1 and len(np.unique(ys[i])) > 1:
                    boots.append(spearmanr(xs[i], ys[i]).statistic)
            lo, hi = np.percentile(boots, [2.5, 97.5])
            correlations[key] = {"rho": float(rho), "ci95": [float(lo), float(hi)], "significant": bool(lo > 0 or hi < 0)}
    return {"friedman": friedman, "wilcoxon_holm": wilcoxon, "win_tie_loss": wtl, "brier_vs_logreg": brier_vs_lr,
            "quantum_minus_best_classical_auc": gaps, "complexity": diag, "complexity_vs_gap": correlations}


def plot_cd(friedman: dict, path: Path):
    """Critical-difference diagram (Demsar 2006): mean ranks with the Nemenyi CD bar."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ranks = sorted(friedman["mean_rank"].items(), key=lambda kv: kv[1])
    k = len(ranks)
    fig, ax = plt.subplots(figsize=(9, 0.42 * k + 1.4))
    for i, (m, r) in enumerate(ranks):
        color = "#4a3aa7" if model_family(m) != "classical" else "#52514e"
        ax.plot([r, r], [0, -(i + 1)], color=color, linewidth=1)
        ax.plot([r, k + 0.6], [-(i + 1), -(i + 1)], color=color, linewidth=1)
        ax.text(k + 0.7, -(i + 1), f"{MODEL_LABELS.get(m, m)} ({r:.2f})", va="center", fontsize=8, color=color)
    best = ranks[0][1]
    ax.plot([best, best + friedman["cd"]], [0.6, 0.6], color="#c0392b", linewidth=3)
    ax.text(best, 0.9, f"CD = {friedman['cd']:.2f} (Nemenyi, alpha 0.05)", fontsize=8, color="#c0392b")
    ax.set_xlim(0.5, k + 6)
    ax.set_ylim(-(k + 1), 1.4)
    ax.set_yticks([])
    ax.set_xlabel("Mean rank across datasets (1 = best AUC)")
    ax.set_title(f"Friedman p = {friedman['friedman_p']:.2g}, {friedman['n_datasets']} datasets, {k} models",
                 loc="left", fontsize=9)
    for s in ("left", "right", "top"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main(argv=None):
    from backend.ml.quantum import registry
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cmd", choices=["run", "aggregate"])
    parser.add_argument("--split", default="development", choices=["development", "confirmation", "all", "sanity"])
    parser.add_argument("--datasets", default=None, help="comma-separated names (overrides --split)")
    parser.add_argument("--models", default=None)
    parser.add_argument("--main-models", default=None, help="models entering Friedman/CD (default: all complete)")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args(argv)
    MULTI_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", force=True,
                        handlers=[logging.StreamHandler(),
                                  logging.FileHandler(MULTI_DIR / "run.log", mode="a", encoding="utf-8")])
    if args.datasets:
        datasets = args.datasets.split(",")
    elif args.split == "all":
        datasets = registry.names("development") + registry.names("confirmation")
    else:
        datasets = registry.names(args.split)
    models = args.models.split(",") if args.models else None
    if args.cmd == "run":
        result = run(datasets, models, args.repeats, args.workers)
        logger.info("run finished: %d done, %d failed %s", result["done"], len(result["failed"]), result["failed"])
        return
    known = models or sorted({p.name for d in datasets for p in (MULTI_DIR / "checkpoints" / d).glob("*")
                              if (MULTI_DIR / "checkpoints" / d).is_dir()})
    per_dataset, scores, briers = aggregate(datasets, known, args.repeats)
    main_models = args.main_models.split(",") if args.main_models else known
    cross = cross_dataset(per_dataset, scores, briers, main_models)
    summary = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "git_commit": _git_sha(), "repeats": args.repeats,
               "folds": N_FOLDS, "max_train": MAX_TRAIN, "n_qubits": N_QUBITS, "seed": SEED,
               "datasets": {d: {"title": v["title"], "split": v["split"], "n": v["complexity"]["n"],
                                "grouped_folds": v["grouped_folds"],
                                "auc": {m: r["pooled_auc"] for m, r in v["models"].items()},
                                "tests": v["tests"]} for d, v in per_dataset.items()},
               "models": {m: {"label": MODEL_LABELS.get(m, m), "family": model_family(m)} for m in known},
               "main_models": main_models, **cross,
               "disclaimer": "Simulator-only research benchmark on public datasets. Not a diagnostic tool."}
    out = MULTI_DIR / f"summary_{args.split if not args.datasets else 'custom'}.json"
    out.write_text(json.dumps(summary, indent=1, default=_json_default), encoding="utf-8")
    if cross["friedman"]:
        plot_cd(cross["friedman"], MULTI_DIR / f"cd_{args.split if not args.datasets else 'custom'}.png")
    logger.info("aggregate written: %s", out)


def _git_sha():
    import subprocess
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              timeout=5).stdout.strip() or None
    except OSError:
        return None


if __name__ == "__main__":
    main()
