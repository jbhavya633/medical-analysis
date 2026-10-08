import numpy as np
import pytest

from backend.ml.quantum.data import load_dataset, stratified_subsample
from backend.ml.quantum.evaluate import cross_validate
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
    out = compare_to_reference(Y, {"ref": GOOD, "a": NOISE, "b": GOOD + 0.001},
                               {"ref": [0.9] * 5, "a": [0.5] * 5, "b": [0.9] * 5}, "ref")
    assert set(out) == {"a", "b"}
    assert out["a"]["significant"] and not out["b"]["significant"]
    assert out["a"]["p_holm"] >= out["a"]["p"] and out["a"]["vs"] == "ref"
    assert compare_to_reference(Y, {"a": NOISE}, {"a": [0.5]}, "ref") == {}


def test_cross_validate_scores_every_row_once():
    X, y, _ = load_dataset("breast_cancer")
    X, y = stratified_subsample(X, y, 90, seed=42)
    r = cross_validate("logreg", X, y, n_qubits=4, n_splits=3, max_train=50)
    score, fold = np.array(r["oof"]["score"]), np.array(r["oof"]["fold"])
    assert len(score) == len(y) and not np.isnan(score).any()
    assert sorted(set(fold.tolist())) == [0, 1, 2]
