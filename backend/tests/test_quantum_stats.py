import numpy as np
import pytest

from backend.ml.quantum.data import load_dataset, stratified_subsample
from backend.ml.quantum.evaluate import calibration_summary, cross_validate, reliability, sensitivity_at_specificity
from backend.ml.quantum.stats import compare_to_reference, holm, paired_bootstrap, wilcoxon_p

rng = np.random.default_rng(0)
Y = np.array([0] * 40 + [1] * 40)
GOOD = Y + rng.normal(0, 0.3, len(Y))
NOISE = rng.normal(0, 1, len(Y))


def test_bootstrap_identical_scores_is_null():
    r = paired_bootstrap(Y, GOOD, GOOD, n_boot=200)
    assert r["delta"] == 0 and r["ci95"] == [0.0, 0.0] and r["p"] == 1.0


def test_bootstrap_detects_a_real_difference():
    r = paired_bootstrap(Y, GOOD, NOISE, n_boot=300)
    assert r["delta"] > 0.3 and r["ci95"][0] > 0 and r["p"] < 0.01
    flipped = paired_bootstrap(Y, NOISE, GOOD, n_boot=300)
    assert flipped["delta"] == pytest.approx(-r["delta"]) and flipped["ci95"][1] < 0


def test_bootstrap_is_reproducible():
    assert paired_bootstrap(Y, GOOD, NOISE, n_boot=100) == paired_bootstrap(Y, GOOD, NOISE, n_boot=100)


def test_holm_hand_computed():
    # sorted p: 0.01*3=0.03, 0.02*2=0.04, 0.04*1=0.04 (monotone); original order restored
    assert holm([0.04, 0.01, 0.02]) == pytest.approx([0.04, 0.03, 0.04])
    assert holm([0.5, 0.9]) == pytest.approx([1.0, 1.0])


def test_wilcoxon_zero_and_nonzero():
    assert wilcoxon_p([0.9] * 5, [0.9] * 5) == 1.0
    p = wilcoxon_p([0.91, 0.92, 0.93, 0.94, 0.95], [0.81, 0.82, 0.83, 0.84, 0.85])
    assert p == pytest.approx(0.0625)  # smallest attainable two-sided p with 5 folds


def test_compare_to_reference_holm_and_flags():
    sig = lambda s: 1 / (1 + np.exp(-s))  # noqa: E731 - probabilities, as the models produce
    out = compare_to_reference(Y, {"ref": sig(GOOD), "a": sig(NOISE), "b": sig(GOOD + 0.001)},
                               {"ref": [0.9] * 5, "a": [0.5] * 5, "b": [0.9] * 5}, "ref")
    assert set(out) == {"a", "b"}
    assert out["a"]["significant"] and not out["b"]["significant"]
    assert out["a"]["p_holm"] >= out["a"]["p"] and out["a"]["vs"] == "ref"
    assert compare_to_reference(Y, {"a": NOISE}, {"a": [0.5]}, "ref") == {}


def test_reliability_and_ece_hand_computed():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.05, 0.15, 0.85, 0.95])  # bins 0, 1, 8, 9: |0.05-0|,|0.15-0|,|0.85-1|,|0.95-1| each weight 1/4
    ece, pts = reliability(y, p)
    assert ece == pytest.approx((0.05 + 0.15 + 0.15 + 0.05) / 4)
    assert [pt["bin"] for pt in pts] == [0, 1, 8, 9] and sum(pt["n"] for pt in pts) == 4
    assert reliability(np.array([1]), np.array([1.0]))[1][0]["bin"] == 9  # p = 1.0 lands in the last bin


def test_sensitivity_at_specificity():
    y = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1])
    s = np.array([.1, .2, .3, .4, .5, .6, .7, .8, .9, .95, .85, .92, .97, .99])
    # spec >= 0.9 allows at most 1 FP: threshold 0.92 keeps 3 of 4 positives
    assert sensitivity_at_specificity(y, s, 0.90) == pytest.approx(0.75)
    assert sensitivity_at_specificity(y, s, 1.0) == pytest.approx(0.5)  # above 0.95: 0.97, 0.99


def test_calibration_summary_keys():
    c = calibration_summary(Y, np.clip(0.5 + 0.4 * (Y - 0.5) + 0.05, 0, 1))
    assert set(c) == {"brier", "ece", "reliability", "sens_at_spec", "slope", "intercept", "decision_curve"}
    assert set(c["sens_at_spec"]) == {"0.90", "0.95"}


def test_calibration_slope_intercept_recovers_known_miscalibration():
    from backend.ml.quantum.evaluate import calibration_slope_intercept
    r = np.random.default_rng(1)
    lp = r.normal(0, 2, 4000)
    y = (r.random(4000) < 1 / (1 + np.exp(-lp))).astype(int)
    good = calibration_slope_intercept(y, 1 / (1 + np.exp(-lp)))
    assert good["slope"] == pytest.approx(1, abs=0.1) and good["intercept"] == pytest.approx(0, abs=0.1)
    over = calibration_slope_intercept(y, 1 / (1 + np.exp(-2 * lp)))  # over-confident -> slope ~0.5
    assert over["slope"] == pytest.approx(0.5, abs=0.07)


def test_decision_curve_hand_computed():
    from backend.ml.quantum.evaluate import decision_curve
    y = np.array([1, 1, 0, 0])
    dc = decision_curve(y, np.array([0.9, 0.2, 0.6, 0.1]), thresholds=(0.5,))[0]
    assert dc["model"] == pytest.approx(1 / 4 - 1 / 4 * 1.0)  # TP=1, FP=1, t/(1-t)=1
    assert dc["treat_all"] == pytest.approx(0.5 - 0.5)


def test_corrected_resampled_ttest():
    from backend.ml.quantum.stats import corrected_resampled_ttest
    a, b = np.array([0.9, 0.92, 0.91, 0.93, 0.9]), np.array([0.8, 0.81, 0.79, 0.82, 0.8])
    r = corrected_resampled_ttest(a, b, n_train=200, n_test=50)
    plain = corrected_resampled_ttest(a, b, n_train=10 ** 9, n_test=1)  # correction ~ 0: plain paired t
    assert r["p"] > plain["p"] and r["df"] == 4 and r["ci95"][0] < r["delta"] < r["ci95"][1]
    assert corrected_resampled_ttest(a, a, 200, 50)["p"] == 1.0


def test_friedman_nemenyi_and_wilcoxon_pairs():
    from backend.ml.quantum.stats import friedman_nemenyi, wilcoxon_holm_pairs, win_tie_loss
    ds = [f"d{i}" for i in range(8)]
    scores = {"good": {d: 0.9 + 0.01 * i for i, d in enumerate(ds)}, "mid": {d: 0.85 for d in ds},
              "bad": {d: 0.6 for d in ds}}
    f = friedman_nemenyi(scores)
    assert f["mean_rank"]["good"] == 1 and f["mean_rank"]["bad"] == 3 and f["friedman_p"] < 0.01 and f["cd"] > 0
    rows = wilcoxon_holm_pairs(scores, [("good", "bad"), ("mid", "mid")])
    assert rows[0]["wins_a"] == 8 and rows[0]["significant"] and rows[1]["p"] == 1.0
    assert win_tie_loss({"x": {"significant": True, "delta": 0.1}, "y": {"significant": False, "delta": -1},
                         "z": {"significant": True, "delta": -0.2}}) == {"win": 1, "tie": 1, "loss": 1}


def test_compare_includes_secondary_metrics():
    out = compare_to_reference(Y, {"ref": 1 / (1 + np.exp(-GOOD)), "a": 1 / (1 + np.exp(-NOISE))},
                               {"ref": [0.9] * 5, "a": [0.5] * 5}, "ref")
    assert out["a"]["brier"]["delta"] > 0 and out["a"]["brier"]["significant"]
    assert out["a"]["sens_at_spec90"]["delta"] < 0


def test_every_model_gets_the_same_tuning_budget():
    from sklearn.model_selection import ParameterGrid
    from backend.ml.quantum.evaluate import ALL_MODELS, EXPERIMENT_MODELS, TUNING_GRIDS, UNTUNED_CONTROLS
    assert set(TUNING_GRIDS) == set(ALL_MODELS + EXPERIMENT_MODELS)
    assert {len(ParameterGrid(g)) for m, g in TUNING_GRIDS.items() if m not in UNTUNED_CONTROLS} == {6}
    assert all(len(ParameterGrid(TUNING_GRIDS[m])) == 1 for m in UNTUNED_CONTROLS)


def _summary(path, y, scores):
    import json
    models = {m: {"oof": {"score": list(s)}, "metrics": {"auc": {"mean": 0.5}},
                  "folds": [{"auc": a} for a in (0.5, 0.6, 0.7)]} for m, s in scores.items()}
    path.write_text(json.dumps({"datasets": {"d": {"y": list(map(int, y)), "models": models}}}), encoding="utf-8")
    return str(path)


def test_compare_runs_across_files(tmp_path, capsys):
    from backend.ml.quantum import stats
    sig = lambda s: (1 / (1 + np.exp(-s))).tolist()  # noqa: E731
    a = _summary(tmp_path / "a.json", Y, {"m": sig(GOOD)})
    b = _summary(tmp_path / "b.json", Y, {"m": sig(NOISE), "n": sig(GOOD)})
    out = tmp_path / "cmp.json"
    stats.main(["--pair", f"{a}:m={b}:m", "--pair", f"{a}:m={b}:n", "--out", str(out)])
    rows = __import__("json").loads(out.read_text(encoding="utf-8"))["d"]
    assert rows[0]["significant"] and not rows[1]["significant"] and rows[0]["p_holm"] >= rows[0]["p"]
    assert "dAUC" in capsys.readouterr().out
    bad = _summary(tmp_path / "bad.json", Y[::-1], {"m": sig(GOOD)})
    with pytest.raises(ValueError):
        stats.compare_runs([(f"{a}:m", f"{bad}:m")])


def test_nested_cv_tunes_inside_training_folds(monkeypatch):
    import backend.ml.quantum.evaluate as ev
    X, y, _ = load_dataset("breast_cancer")
    X, y = stratified_subsample(X, y, 90, seed=42)
    r = cross_validate("logreg", X, y, n_qubits=4, n_splits=3, max_train=50, tuned=True)
    t = r["tuning"]
    assert t["n_configs"] == 6 and len(t["chosen"]) == 3 and set(t["chosen"][0]) == {"C"}
    assert t["optimism"] == pytest.approx(t["inner_auc_mean"] - r["metrics"]["auc"]["mean"])
    assert cross_validate("logreg", X, y, n_qubits=4, n_splits=3, max_train=50)["tuning"] is None
    # quantum models go through the same harness (small grid here to keep the test fast)
    monkeypatch.setitem(ev.TUNING_GRIDS, "vqc", {"model__lr": [0.05, 0.1], "model__epochs": [2]})
    q = cross_validate("vqc", X, y, n_qubits=4, n_splits=2, max_train=40, tuned=True)
    assert q["tuning"]["n_configs"] == 2 and {"lr", "epochs"} == set(q["tuning"]["chosen"][0])


def test_cross_validate_scores_every_row_once():
    X, y, _ = load_dataset("breast_cancer")
    X, y = stratified_subsample(X, y, 90, seed=42)
    r = cross_validate("logreg", X, y, n_qubits=4, n_splits=3, max_train=50)
    score, fold = np.array(r["oof"]["score"]), np.array(r["oof"]["fold"])
    assert len(score) == len(y) and not np.isnan(score).any()
    assert sorted(set(fold.tolist())) == [0, 1, 2]
