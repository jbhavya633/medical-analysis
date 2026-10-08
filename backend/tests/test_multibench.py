import concurrent.futures
import json

import numpy as np
import pytest

from backend.ml.quantum import multibench
from backend.ml.quantum.data import load_dataset, stratified_subsample
from backend.ml.quantum.evaluate import fit_and_score


@pytest.fixture()
def multi_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(multibench, "MULTI_DIR", tmp_path)
    # threads instead of processes keep the test fast and in-process (the unit logic is identical)
    monkeypatch.setattr(multibench, "ProcessPoolExecutor", concurrent.futures.ThreadPoolExecutor)
    return tmp_path


def test_duplicate_groups_keep_identical_rows_together():
    X = np.array([[1.0, np.nan], [1.0, np.nan], [2.0, 3.0], [1.0, 0.0]])
    g = multibench.duplicate_groups(X)
    assert g[0] == g[1] and len({g[0], g[2], g[3]}) == 3


def test_grouped_outer_folds_never_split_a_group(monkeypatch):
    rng = np.random.default_rng(0)
    X = np.repeat(rng.normal(size=(40, 3)), 3, axis=0)  # every row appears 3 times
    y = np.repeat(np.arange(40) % 2, 3)
    monkeypatch.setattr(multibench, "load_dataset", lambda name: (X, y, ["a", "b", "c"]))
    multibench.dataset_arrays.cache_clear()
    try:
        _, _, _, g = multibench.dataset_arrays("toy_grouped")
        assert g is not None
        for tr, va in multibench.outer_folds("toy_grouped", 0):
            assert not set(g[tr]) & set(g[va])
    finally:
        multibench.dataset_arrays.cache_clear()


def test_leakage_audit_outer_labels_never_reach_the_fit():
    """Pre-registered audit (docs/PREREGISTRATION.md section 7): permuting the outer-validation labels must leave
    every prediction unchanged, because tuning, imputation, scaling and selection see training rows only."""
    X, y, _ = load_dataset("heart")
    tr, va = np.arange(0, 200), np.arange(200, len(y))
    rng = np.random.default_rng(1)
    _, s1, _, _ = fit_and_score("logreg", X[tr], y[tr], X[va], y[va], 6, tuned=True)
    _, s2, _, _ = fit_and_score("logreg", X[tr], y[tr], X[va], rng.permutation(y[va]), 6, tuned=True)
    assert np.array_equal(s1, s2)


def test_run_resume_and_aggregate(multi_dir):
    datasets, models = ["breast_cancer"], ["logreg", "qsvm_fixed", "hgb"]
    r1 = multibench.run(datasets, models, repeats=1, workers=2)
    assert r1["done"] == 15 and not r1["failed"]
    assert multibench.pending_units(datasets, models, 1) == []  # resumable: nothing left
    assert multibench.run(datasets, models, repeats=1, workers=2)["done"] == 0
    ck = json.loads(multibench.ckpt_path("breast_cancer", "logreg", 0, 0).read_text(encoding="utf-8"))
    assert ck["n_train"] == 200 and ck["best_params"] and len(ck["val_idx"]) == len(ck["score"])
    multibench.main(["aggregate", "--datasets", "breast_cancer", "--repeats", "1", "--models", ",".join(models)])
    s = json.loads((multi_dir / "summary_custom.json").read_text(encoding="utf-8"))
    auc = s["datasets"]["breast_cancer"]["auc"]
    assert set(auc) == set(models) and all(0.5 < v["mean"] <= 1 for v in auc.values())
    per = json.loads((multi_dir / "breast_cancer.json").read_text(encoding="utf-8"))
    assert per["models"]["logreg"]["calibration"]["decision_curve_r0"]
    assert per["complexity"]["n"] == 569 and per["complexity"]["cov_effective_dim"] > 1


def test_failed_unit_is_logged_and_retried(multi_dir, monkeypatch):
    def boom(*a):
        raise RuntimeError("simulated crash")
    monkeypatch.setattr(multibench, "run_unit", boom)
    r = multibench.run(["breast_cancer"], ["logreg"], repeats=1, workers=1)
    assert r["done"] == 0 and len(r["failed"]) == 5
    assert len(multibench.pending_units(["breast_cancer"], ["logreg"], 1)) == 5


def test_cross_dataset_statistics_and_cd_plot(tmp_path):
    ds = [f"d{i}" for i in range(6)]
    scores = {"logreg": {d: 0.85 + 0.01 * i for i, d in enumerate(ds)},
              "hgb": {d: 0.84 + 0.01 * i for i, d in enumerate(ds)},
              "qsvm": {d: 0.80 + 0.012 * i for i, d in enumerate(ds)}}
    per = {d: {"tests": {"qsvm|logreg": {"delta": -0.05, "significant": i % 2 == 0},
                         "qsvm|hgb": {"delta": -0.04, "significant": False}},
               "complexity": {"n": 100 + 50 * i, "d": 5 + i, "grouped_folds": False},
               "models": {"qsvm": {"kernel_spectrum_mean": {"mean_offdiag": 0.3, "eff_rank_ratio": 0.1 * i}}}}
           for i, d in enumerate(ds)}
    briers = {m: {d: 0.2 - v for d, v in s.items()} for m, s in scores.items()}
    cross = multibench.cross_dataset(per, scores, briers, ["logreg", "hgb", "qsvm"])
    assert cross["friedman"]["mean_rank"]["logreg"] == 1.0
    assert cross["win_tie_loss"]["qsvm|logreg"] == {"win": 0, "tie": 3, "loss": 3}
    assert set(cross["complexity_vs_gap"]) >= {"n", "d", "qsvm_eff_rank_ratio"}
    assert cross["complexity_vs_gap"]["n"]["rho"] == pytest.approx(1.0)
    assert cross["complexity_vs_gap"]["qsvm_mean_offdiag"]["rho"] is None  # constant diagnostic
    multibench.plot_cd(cross["friedman"], tmp_path / "cd.png")
    assert (tmp_path / "cd.png").is_file()
