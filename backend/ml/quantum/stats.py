"""Significance tests on pooled out-of-fold predictions (docs/OPTIMIZATION_PLAN.md, shared protocol).

Primary: paired stratified bootstrap of a metric difference on the same OOF rows (95% CI, two-sided p).
Secondary: Wilcoxon signed-rank on per-fold values (minimum attainable p is 0.0625 with 5 folds).
Holm correction across the comparisons made within one dataset.
"""

import numpy as np
from scipy.stats import wilcoxon
from sklearn.metrics import roc_auc_score

from backend.ml.quantum import SEED

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


def compare_to_reference(y, oof_scores: dict, fold_auc: dict, reference: str, seed=SEED) -> dict:
    """AUC of every model vs the reference model on pooled OOF rows; Holm across the models compared."""
    others = [m for m in oof_scores if m != reference]
    if reference not in oof_scores or not others:
        return {}
    out = {m: {"vs": reference, **paired_bootstrap(y, oof_scores[m], oof_scores[reference], seed=seed),
               "p_wilcoxon": wilcoxon_p(fold_auc[m], fold_auc[reference])} for m in others}
    for m, p_adj, w_adj in zip(others, holm([out[m]["p"] for m in others]),
                               holm([out[m]["p_wilcoxon"] for m in others])):
        out[m].update(p_holm=p_adj, p_wilcoxon_holm=w_adj, significant=bool(p_adj < ALPHA))
    return out
