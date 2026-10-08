"""Significance tests on pooled out-of-fold predictions (docs/OPTIMIZATION_PLAN.md, shared protocol).

Primary: paired stratified bootstrap of a metric difference on the same OOF rows (95% CI, two-sided p).
Secondary: Wilcoxon signed-rank on per-fold values (minimum attainable p is 0.0625 with 5 folds).
Holm correction across the comparisons made within one dataset.
"""

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon
from sklearn.metrics import brier_score_loss, roc_auc_score

from backend.ml.quantum import SEED
from backend.ml.quantum.evaluate import sensitivity_at_specificity

N_BOOT = 2000
ALPHA = 0.05


def paired_bootstrap(y, score_a, score_b, metric=roc_auc_score, n_boot=N_BOOT, seed=SEED) -> dict:
    """metric(a) - metric(b) on identical rows, resampled within each class (stratified)."""
    y = np.asarray(y)
    score_a, score_b = np.asarray(score_a, dtype=float), np.asarray(score_b, dtype=float)
    rng = np.random.default_rng(seed)
    pos, neg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
    deltas = np.empty(n_boot)
    for b in range(n_boot):
        idx = np.concatenate([rng.choice(pos, len(pos)), rng.choice(neg, len(neg))])
        deltas[b] = metric(y[idx], score_a[idx]) - metric(y[idx], score_b[idx])
    point = float(metric(y, score_a) - metric(y, score_b))
    lo, hi = np.percentile(deltas, [2.5, 97.5])
    p = float(min(1.0, 2 * min((deltas <= 0).mean(), (deltas >= 0).mean())))
    return {"delta": point, "ci95": [float(lo), float(hi)], "p": p}


def wilcoxon_p(a, b) -> float:
    """Two-sided Wilcoxon signed-rank p on paired per-fold values (1.0 when all differences are zero)."""
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    if np.allclose(d, 0):
        return 1.0
    return float(wilcoxon(d, zero_method="zsplit").pvalue)


def holm(pvalues: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values (same order as the input)."""
    p = np.asarray(pvalues, dtype=float)
    order = np.argsort(p)
    adjusted = np.empty_like(p)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(p) - rank) * p[i])
        adjusted[i] = min(1.0, running)
    return adjusted.tolist()


def compare_runs(pairs: list[tuple[str, str]], seed=SEED) -> dict:
    """Experiment comparisons across benchmark runs: each pair is ("dirA/summary.json:model", "dirB/...:model").

    Both sides must hold pooled OOF scores on identical rows (same seed, folds and dataset). Per dataset, the
    AUC difference A - B gets a paired bootstrap CI; Holm across the pairs. Returns {dataset: [rows]}.
    """
    def load(spec):
        path, model = spec.rsplit(":", 1)
        return json.loads(Path(path).read_text(encoding="utf-8")), model

    loaded = [(load(a), load(b)) for a, b in pairs]
    datasets = sorted(set.intersection(*[set(sa["datasets"]) & set(sb["datasets"]) for (sa, _), (sb, _) in loaded]))
    out = {}
    for ds in datasets:
        rows = []
        for (a, b), ((sa, ma), (sb, mb)) in zip(pairs, loaded):
            da, db = sa["datasets"][ds], sb["datasets"][ds]
            if da["y"] != db["y"]:
                raise ValueError(f"{ds}: {a} and {b} were not scored on the same rows")
            ra, rb = da["models"][ma], db["models"][mb]
            res = paired_bootstrap(da["y"], ra["oof"]["score"], rb["oof"]["score"], seed=seed)
            rows.append({"a": f"{ma}", "b": f"{mb}", "a_run": a.rsplit(":", 1)[0], "b_run": b.rsplit(":", 1)[0],
                         "auc_a": ra["metrics"]["auc"]["mean"], "auc_b": rb["metrics"]["auc"]["mean"], **res,
                         "p_wilcoxon": wilcoxon_p([f["auc"] for f in ra["folds"]], [f["auc"] for f in rb["folds"]])
                         if "folds" in ra and "folds" in rb else None})
        for row, p_adj in zip(rows, holm([r["p"] for r in rows])):
            row.update(p_holm=p_adj, significant=bool(p_adj < ALPHA))
        out[ds] = rows
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description="Paired comparisons of models across benchmark runs (pooled OOF).")
    parser.add_argument("--pair", action="append", required=True, metavar="A_SUMMARY:MODEL=B_SUMMARY:MODEL")
    parser.add_argument("--out", type=Path, required=True, help="JSON file to write")
    args = parser.parse_args(argv)
    result = compare_runs([tuple(p.split("=", 1)) for p in args.pair])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=1), encoding="utf-8")
    for ds, rows in result.items():
        for r in rows:
            print(f"{ds:14s} {r['a']} vs {r['b']}: dAUC {r['delta']:+.3f} [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}] "
                  f"p_holm {r['p_holm']:.3f}{' *' if r['significant'] else ''}")


def corrected_resampled_ttest(a, b, n_train: int, n_test: int) -> dict:
    """Nadeau & Bengio corrected resampled t-test on paired per-fold scores from repeated k-fold CV.

    The variance of the mean difference is inflated by (1/J + n_test/n_train) instead of 1/J to account for the
    overlap between training sets (J = repeats x folds). Two-sided p from Student t with J - 1 df.
    """
    from scipy.stats import t as student_t
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    J = len(d)
    mean, var = float(d.mean()), float(d.var(ddof=1)) if J > 1 else 0.0
    if J < 2 or var == 0:
        return {"delta": mean, "t": 0.0 if mean == 0 else float("inf") * np.sign(mean),
                "p": 1.0 if mean == 0 else 0.0, "df": J - 1}
    se = np.sqrt((1 / J + n_test / n_train) * var)
    t = mean / se
    return {"delta": mean, "t": float(t), "p": float(2 * student_t.sf(abs(t), J - 1)), "df": J - 1,
            "ci95": [float(mean - student_t.ppf(0.975, J - 1) * se), float(mean + student_t.ppf(0.975, J - 1) * se)]}


def friedman_nemenyi(scores: dict[str, dict[str, float]], alpha: float = ALPHA) -> dict:
    """scores[model][dataset] (higher is better). Friedman test over datasets, mean ranks (1 = best) and the
    Nemenyi critical difference CD = q_alpha * sqrt(k (k + 1) / (6 N)) (Demsar 2006)."""
    from scipy.stats import friedmanchisquare, rankdata, studentized_range
    models = list(scores)
    datasets = sorted(set.intersection(*[set(scores[m]) for m in models]))
    M = np.array([[scores[m][d] for m in models] for d in datasets])  # N x k
    ranks = np.array([rankdata(-row) for row in M])
    k, N = len(models), len(datasets)
    stat, p = friedmanchisquare(*M.T) if k >= 3 and N >= 2 else (float("nan"), float("nan"))
    q = studentized_range.ppf(1 - alpha, k, np.inf) / np.sqrt(2)
    return {"models": models, "datasets": datasets, "mean_rank": dict(zip(models, ranks.mean(axis=0).tolist())),
            "friedman_stat": float(stat), "friedman_p": float(p), "cd": float(q * np.sqrt(k * (k + 1) / (6 * N))),
            "n_datasets": N, "k_models": k}


def wilcoxon_holm_pairs(scores: dict[str, dict[str, float]], pairs: list[tuple[str, str]], seed=SEED) -> list[dict]:
    """Pre-specified model pairs compared across datasets: Wilcoxon signed-rank (two-sided), Holm across the pairs,
    median difference with a bootstrap 95% CI over datasets."""
    rows = []
    rng = np.random.default_rng(seed)
    for a, b in pairs:
        ds = sorted(set(scores[a]) & set(scores[b]))
        d = np.array([scores[a][x] - scores[b][x] for x in ds])
        boots = [np.median(rng.choice(d, len(d))) for _ in range(N_BOOT)] if len(d) else [np.nan]
        rows.append({"a": a, "b": b, "n_datasets": len(ds), "median_delta": float(np.median(d)) if len(d) else None,
                     "median_ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
                     "p": wilcoxon_p(d, np.zeros_like(d)) if len(d) >= 2 else 1.0,
                     "wins_a": int((d > 0).sum()), "wins_b": int((d < 0).sum())})
    for r, p_adj in zip(rows, holm([r["p"] for r in rows])):
        r.update(p_holm=p_adj, significant=bool(p_adj < ALPHA))
    return rows


def win_tie_loss(per_dataset_tests: dict[str, dict]) -> dict:
    """Counts over datasets from per-dataset corrected tests: win/loss = significant after Holm, else tie."""
    out = {"win": 0, "tie": 0, "loss": 0}
    for t in per_dataset_tests.values():
        if t.get("significant"):
            out["win" if t["delta"] > 0 else "loss"] += 1
        else:
            out["tie"] += 1
    return out


def sens_at_spec90(y, score) -> float:
    return sensitivity_at_specificity(y, score, 0.90)


# Secondary metric families, each Holm-corrected on its own (AUC is the primary comparison).
SECONDARY_METRICS = {"brier": brier_score_loss, "sens_at_spec90": sens_at_spec90}


def compare_to_reference(y, oof_scores: dict, fold_auc: dict, reference: str, seed=SEED) -> dict:
    """AUC (plus Brier and sensitivity at 90% specificity) of every model vs the reference model on the same
    pooled OOF rows; Holm across the models compared, separately per metric."""
    others = [m for m in oof_scores if m != reference]
    if reference not in oof_scores or not others:
        return {}
    out = {m: {"vs": reference, **paired_bootstrap(y, oof_scores[m], oof_scores[reference], seed=seed),
               "p_wilcoxon": wilcoxon_p(fold_auc[m], fold_auc[reference])} for m in others}
    for m, p_adj, w_adj in zip(others, holm([out[m]["p"] for m in others]),
                               holm([out[m]["p_wilcoxon"] for m in others])):
        out[m].update(p_holm=p_adj, p_wilcoxon_holm=w_adj, significant=bool(p_adj < ALPHA))
    for key, metric in SECONDARY_METRICS.items():
        sec = {m: paired_bootstrap(y, oof_scores[m], oof_scores[reference], metric=metric, seed=seed) for m in others}
        for m, p_adj in zip(others, holm([sec[m]["p"] for m in others])):
            out[m][key] = {**sec[m], "p_holm": p_adj, "significant": bool(p_adj < ALPHA)}
    return out


if __name__ == "__main__":
    main()
