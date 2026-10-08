"""Benchmark CLI: classical baselines vs quantum / hybrid models on public biomedical datasets.

python -m backend.ml.quantum.benchmark --dataset all --seed 42 --n-qubits 6

Writes results/benchmark_<dataset>.json, results/summary.json, results/summary.md, results/*.png
(ROC, learning curve, calibration, importance),
results/models/<dataset>_<model>.joblib and results/benchmark.log. Research prototype; not a diagnostic tool.
"""

import argparse
import json
import logging
import os
import platform
import subprocess
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np

from backend.ml.quantum import SEED
from backend.ml.quantum.data import DATASETS, DatasetUnavailableError, holdout_split, load_dataset, stratified_subsample
from backend.ml.quantum.evaluate import (
    ALL_MODELS,
    INNER_FOLDS,
    QUANTUM_MODELS,
    TUNING_GRIDS,
    cross_validate,
    fit_and_score,
    learning_curve,
)
from backend.ml.quantum.explain import (
    feature_map_sensitivity,
    kernel_alignment,
    permutation_scores,
    shap_scores,
)
from backend.ml.quantum.preprocess import selected_feature_names
from backend.ml.quantum.qkernel import QuantumKernelSVM, kernel_from_states, statevectors
from backend.ml.quantum.stats import compare_to_reference

REFERENCE_MODEL = "logreg"
RESULTS_DIR = Path(os.getenv("QML_RESULTS_DIR", Path(__file__).resolve().parent / "results"))
logger = logging.getLogger("qml.benchmark")

# Reference categorical palette (dataviz skill), fixed slot per model: classical 1-4, quantum 5-7.
MODEL_COLORS = {
    "logreg": "#2a78d6", "svm_rbf": "#eb6834", "random_forest": "#1baf7a", "mlp": "#eda100",
    "qsvm": "#e87ba4", "vqc": "#008300", "hybrid_qnn": "#4a3aa7", "hgb": "#7d4f2a",
}
MODEL_LABELS = {
    "logreg": "Logistic regression", "svm_rbf": "SVM (RBF)", "random_forest": "Random forest", "mlp": "MLP",
    "qsvm": "Quantum-kernel SVM", "vqc": "VQC", "hybrid_qnn": "Hybrid QNN", "hgb": "Gradient boosting (HGB)",
    # controls and experiment-only variants (cv-only runs; no plots)
    "mlp_matched": "MLP, parameter-matched (41)", "vqc_twin": "Classical trig twin of re-uploading VQC",
    "residual_qnn": "Residual head [x, quantum block]", "residual_classical": "Residual head [x, tanh block]",
    "qsvm_fixed": "QSVM, untuned (s = 1, C = 1)",
    "qsvm_c": "QSVM, C-tuned control (s = 1)",
    "vqc_3layer": "VQC, 3 layers (parameter-matched control)", "vqc_scale": "VQC + trainable input scaling",
    "vqc_reupload_scale": "VQC + data re-uploading (scaled)", "vqc_allz": "VQC, all-qubit readout",
    "vqc_allz_noent": "VQC, all-qubit readout, no CNOTs", "hybrid_classical": "Hybrid, quantum layer -> Linear+tanh",
}
MODEL_LABELS.update({m + "_fs": f"{MODEL_LABELS[m]}, feature-selection sweep" for m in ALL_MODELS})


def run_dataset(name, n_qubits, seed, folds, max_train, epochs, models, tuned=False, cv_only=False):
    """tuned: nested-CV tuning with an equal 6-configuration grid per model (outer folds and hold-out alike).
    cv_only: experiment runs - skip the learning curve, the hold-out fit, explanations and saved models."""
    X, y, feature_names = load_dataset(name)
    logger.info("%s: %d samples, %d raw features, %.1f%% positive", name, len(y), X.shape[1], 100 * y.mean())
    results = {}
    for model in models:
        t0 = time.perf_counter()
        cv = cross_validate(model, X, y, n_qubits, folds, seed, max_train, epochs=epochs, tuned=tuned)
        if not cv_only:  # learning curve stays untuned (default hyperparameters) to bound its cost
            cv["learning_curve"] = learning_curve(model, X, y, n_qubits, seed, max_train, epochs=epochs)
        m = cv["metrics"]
        logger.info("%-14s acc %.3f±%.3f sens %.3f spec %.3f auc %.3f train %.2fs (%.0fs total)",
                    model, m["accuracy"]["mean"], m["accuracy"]["std"], m["sensitivity"]["mean"],
                    m["specificity"]["mean"], m["auc"]["mean"], m["train_time_s"]["mean"], time.perf_counter() - t0)
        results[model] = cv

    # Significance vs logistic regression on pooled OOF rows (stats.py); same rows for every model.
    comparisons = compare_to_reference(
        y, {m: r["oof"]["score"] for m, r in results.items()},
        {m: [f["auc"] for f in r["folds"]] for m, r in results.items()}, REFERENCE_MODEL, seed)
    for model, cmp in comparisons.items():
        results[model]["vs_reference"] = cmp
    dataset = {"dataset": name, "info": DATASETS[name], "n_samples": int(len(y)), "n_raw_features": int(X.shape[1]),
               "positive_rate": float(y.mean()), "feature_names": feature_names, "y": y.astype(int).tolist(),
               "reference_model": REFERENCE_MODEL, "models": results}
    if cv_only:
        return dataset

    # Held-out 20% split: fit once per model (tuned on the hold-out training rows only), save it, and explain it.
    X_tr, X_te, y_tr, y_te = holdout_split(X, y, seed=seed)
    X_tr, y_tr = stratified_subsample(X_tr, y_tr, max_train, seed)
    model_dir = RESULTS_DIR / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    background_raw = X_tr[rng.choice(len(X_tr), size=min(20, len(X_tr)), replace=False)]
    for model in models:
        holdout, _, pre, fitted = fit_and_score(model, X_tr, y_tr, X_te, y_te, n_qubits, seed, epochs=epochs,
                                                tuned=tuned)
        selected = selected_feature_names(pre, feature_names)
        A_te = pre.transform(X_te)
        A_bg = pre.transform(background_raw)[:10]
        explain = {
            "selected_features": selected,
            "permutation_importance": permutation_scores(fitted, A_te, y_te, selected, seed),
            "shap_mean_abs": shap_scores(fitted, A_bg, A_te[:8], selected, nsamples=100, seed=seed),
        }
        if isinstance(fitted, QuantumKernelSVM):
            states = statevectors(pre.transform(X_tr), n_qubits, fitted.reps, fitted.bandwidth)
            explain["kernel_alignment"] = round(kernel_alignment(kernel_from_states(states, states), y_tr), 5)
            explain["feature_map_sensitivity"] = feature_map_sensitivity(A_te, n_qubits, selected,
                                                                         reps=fitted.reps, bandwidth=fitted.bandwidth)
            explain["bandwidth"] = fitted.bandwidth
        results[model]["holdout"] = {k: v for k, v in holdout.items()}
        results[model]["explain"] = explain
        joblib.dump({
            "dataset": name, "model": model, "n_qubits": n_qubits, "seed": seed,
            "preprocessor": pre, "estimator": fitted, "feature_names": feature_names,
            "selected_features": selected, "background_raw": background_raw,
            "holdout_metrics": holdout,
        }, model_dir / f"{name}_{model}.joblib")
    return dataset


def write_summary_md(all_results, config, path):
    lines = [
        "# SIH26139 benchmark summary",
        "",
        "Research prototype - not a diagnostic tool. Generated by `python -m backend.ml.quantum.benchmark`.",
        "",
        f"Config: {json.dumps(config)}",
        "",
    ]
    for ds in all_results.values():
        lines += [f"## {ds['info']['title']} (`{ds['dataset']}`, n={ds['n_samples']}, "
                  f"positive = {ds['info']['positive_class']})", "",
                  "| Model | Family | Accuracy | Sensitivity | Specificity | AUC | F1 | ΔAUC vs LogReg [95% CI] | Train s | Infer ms/sample | Gen. gap | Qubits | Depth | Params |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for name, r in ds["models"].items():
            m = r["metrics"]
            f = lambda k: f"{m[k]['mean']:.3f} ± {m[k]['std']:.3f}"
            lines.append(f"| {MODEL_LABELS[name]} | {r['family']} | {f('accuracy')} | {f('sensitivity')} | "
                         f"{f('specificity')} | {f('auc')} | {f('f1')} | {format_delta(name, r.get('vs_reference'))} | "
                         f"{m['train_time_s']['mean']:.3f} | {m['infer_ms_per_sample']['mean']:.3f} | "
                         f"{m['gen_gap']['mean']:.3f} | {r['n_qubits'] or '-'} | {r['circuit_depth'] or '-'} | {r['n_params']} |")
        lines += ["", "ΔAUC: pooled out-of-fold AUC minus logistic regression's on the same rows; paired stratified "
                  "bootstrap (2,000 resamples) 95% CI. * = significant after Holm correction (alpha 0.05); "
                  "otherwise not significant.", "",
                  "Calibration and decision utility (pooled out-of-fold predictions):", "",
                  "| Model | Brier | ΔBrier vs LogReg [95% CI] | ECE (10 bins) | Sens @ 90% spec | Sens @ 95% spec |",
                  "|---|---|---|---|---|---|"]
        for name, r in ds["models"].items():
            c = r["calibration"]
            lines.append(f"| {MODEL_LABELS[name]} | {c['brier']:.3f} | "
                         f"{format_delta(name, (r.get('vs_reference') or {}).get('brier'))} | {c['ece']:.3f} | "
                         f"{c['sens_at_spec']['0.90']:.3f} | {c['sens_at_spec']['0.95']:.3f} |")
        lines += ["", "ΔBrier < 0 means better calibrated than logistic regression.", ""]
        tuned = {n: r["tuning"] for n, r in ds["models"].items() if r.get("tuning")}
        if tuned:
            lines += ["Nested tuning (inner 3-fold CV on each outer training fold; 6 configurations per model):", "",
                      "| Model | Chosen per outer fold | Mean inner AUC | Optimism (inner - outer AUC) |",
                      "|---|---|---|---|"]
            for n, t in tuned.items():
                chosen = "; ".join(", ".join(f"{k}={v}" for k, v in c.items()) for c in t["chosen"])
                lines.append(f"| {MODEL_LABELS[n]} | {chosen} | {t['inner_auc_mean']:.3f} | {t['optimism']:+.3f} |")
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def format_delta(model, cmp) -> str:
    if not cmp:
        return "reference" if model == REFERENCE_MODEL else "-"
    lo, hi = cmp["ci95"]
    return f"{cmp['delta']:+.3f} [{lo:+.3f}, {hi:+.3f}]{'*' if cmp['significant'] else ''}"


def plot_dataset(ds, out_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#c3c2b7", "axes.labelcolor": "#52514e",
                         "xtick.color": "#52514e", "ytick.color": "#52514e", "axes.grid": True,
                         "grid.color": "#ecebe7", "grid.linewidth": 0.8, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})
    groups = [("Classical baselines", [m for m in ds["models"] if m not in QUANTUM_MODELS]),
              ("Quantum / hybrid", [m for m in ds["models"] if m in QUANTUM_MODELS])]
    name = ds["dataset"]

    fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    for ax, (title, models) in zip(axes, groups):
        ax.plot([0, 1], [0, 1], color="#a8a79f", linewidth=1, linestyle="--")
        for m in models:
            roc = ds["models"][m]["roc"]
            auc = ds["models"][m]["metrics"]["auc"]["mean"]
            ax.plot(roc["fpr"], roc["tpr"], color=MODEL_COLORS[m], linewidth=2,
                    label=f"{MODEL_LABELS[m]} (AUC {auc:.3f})")
        ax.set_title(title, color="#0b0b0b", loc="left")
        ax.set_xlabel("False positive rate (1 - specificity)")
        ax.legend(frameon=False, loc="lower right")
    axes[0].set_ylabel("True positive rate (sensitivity)")
    fig.suptitle(f"ROC, pooled out-of-fold - {ds['info']['title']}", x=0.01, ha="left", color="#0b0b0b")
    fig.tight_layout()
    fig.savefig(out_dir / f"roc_{name}.png", dpi=120)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    for ax, (title, models) in zip(axes, groups):
        for m in models:
            pts = ds["models"][m]["learning_curve"]
            ax.plot([p["n_train"] for p in pts], [p["val_accuracy"] for p in pts], color=MODEL_COLORS[m],
                    linewidth=2, marker="o", markersize=5, label=MODEL_LABELS[m])
        ax.set_title(title, color="#0b0b0b", loc="left")
        ax.set_xlabel("Training samples")
        ax.legend(frameon=False, loc="lower right")
    axes[0].set_ylabel("Validation accuracy")
    fig.suptitle(f"Learning curves - {ds['info']['title']}", x=0.01, ha="left", color="#0b0b0b")
    fig.tight_layout()
    fig.savefig(out_dir / f"learning_curve_{name}.png", dpi=120)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    for ax, (title, models) in zip(axes, groups):
        ax.plot([0, 1], [0, 1], color="#a8a79f", linewidth=1, linestyle="--")
        for m in models:
            c = ds["models"][m]["calibration"]
            pts = c["reliability"]
            ax.plot([p["mean_pred"] for p in pts], [p["frac_pos"] for p in pts], color=MODEL_COLORS[m],
                    linewidth=2, marker="o", markersize=4, label=f"{MODEL_LABELS[m]} (Brier {c['brier']:.3f})")
        ax.set_title(title, color="#0b0b0b", loc="left")
        ax.set_xlabel("Mean predicted P(disease)")
        ax.legend(frameon=False, loc="upper left")
    axes[0].set_ylabel("Observed fraction with disease")
    fig.suptitle(f"Reliability, pooled out-of-fold - {ds['info']['title']}", x=0.01, ha="left", color="#0b0b0b")
    fig.tight_layout()
    fig.savefig(out_dir / f"calibration_{name}.png", dpi=120)
    plt.close(fig)

    picks = [m for m in ("logreg", "qsvm") if m in ds["models"]]
    fig, axes = plt.subplots(1, len(picks), figsize=(4.5 * len(picks), 3.6), squeeze=False)
    for ax, m in zip(axes[0], picks):
        imp = ds["models"][m]["explain"]["permutation_importance"]
        items = sorted(imp.items(), key=lambda kv: kv[1])
        ax.barh([k for k, _ in items], [v for _, v in items], color=MODEL_COLORS[m], height=0.6)
        ax.set_title(f"{MODEL_LABELS[m]}: permutation importance", color="#0b0b0b", loc="left")
        ax.set_xlabel("Drop in AUC when permuted (held-out 20%)")
    fig.tight_layout()
    fig.savefig(out_dir / f"importance_{name}.png", dpi=120)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", default="all", choices=["all", *DATASETS])
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--n-qubits", type=int, default=6, choices=range(4, 9))
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--max-train", type=int, default=200)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--models", default=",".join(ALL_MODELS))
    parser.add_argument("--tune", action="store_true", help="nested-CV tuning, equal 6-configuration grid per model")
    parser.add_argument("--cv-only", action="store_true",
                        help="experiment run: CV table only (no learning curve, hold-out models, plots)")
    parser.add_argument("--results-dir", type=Path, default=None,
                        help="write here instead of results/ (e.g. results/experiments/<name>)")
    args = parser.parse_args(argv)
    unknown = [m for m in args.models.split(",") if m and m not in TUNING_GRIDS]
    if unknown:
        parser.error(f"unknown models: {unknown}")

    global RESULTS_DIR
    if args.results_dir is not None:
        RESULTS_DIR = args.results_dir
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", force=True,
                        handlers=[logging.StreamHandler(), logging.FileHandler(RESULTS_DIR / "benchmark.log", mode="w", encoding="utf-8")])
    warnings.filterwarnings("ignore")
    logging.getLogger("shap").setLevel(logging.WARNING)
    models = [m for m in args.models.split(",") if m]
    config = {"seed": args.seed, "n_qubits": args.n_qubits, "folds": args.folds, "max_train": args.max_train,
              "epochs": args.epochs, "feature_selection": "mutual_info", "simulator": "default.qubit",
              "models": models, "tuned": args.tune, "cv_only": args.cv_only,
              "tuning": {"inner_folds": INNER_FOLDS, "configs_per_model": 6} if args.tune else None}
    started = time.perf_counter()
    all_results = {}
    for name in (DATASETS if args.dataset == "all" else [args.dataset]):
        try:
            ds = run_dataset(name, args.n_qubits, args.seed, args.folds, args.max_train, args.epochs, models,
                             tuned=args.tune, cv_only=args.cv_only)
        except DatasetUnavailableError as exc:
            logger.warning("%s: skipped (%s)", name, exc)
            continue
        all_results[name] = ds
        (RESULTS_DIR / f"benchmark_{name}.json").write_text(json.dumps(ds, indent=1), encoding="utf-8")
        if not args.cv_only:
            plot_dataset(ds, RESULTS_DIR)

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": _git_sha(), "python": platform.python_version(), "config": config,
        "runtime_s": round(time.perf_counter() - started, 1),
        "disclaimer": "Research prototype on public benchmark data. Not a diagnostic tool.",
        "datasets": {k: {"info": v["info"], "n_samples": v["n_samples"], "positive_rate": v["positive_rate"],
                         "y": v["y"], "reference_model": v["reference_model"],
                         "models": {m: {key: r[key] for key in ("family", "metrics", "roc", "learning_curve",
                                                                  "n_qubits", "circuit_depth", "n_params",
                                                                  "holdout", "explain", "oof", "vs_reference",
                                                                  "calibration", "tuning", "folds",
                                                                  "feature_stability_jaccard")
                                        if key in r}
                                    for m, r in v["models"].items()}}
                     for k, v in all_results.items()},
    }
    (RESULTS_DIR / "summary.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    write_summary_md(all_results, config, RESULTS_DIR / "summary.md")
    logger.info("done in %.1fs -> %s", time.perf_counter() - started, RESULTS_DIR)


def _git_sha():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              timeout=5).stdout.strip() or None
    except OSError:
        return None


if __name__ == "__main__":
    main()
