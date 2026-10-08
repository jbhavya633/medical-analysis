import json

import numpy as np
import pytest

from backend.ml.quantum import noise
from backend.ml.quantum.data import load_dataset, stratified_subsample
from backend.ml.quantum.evaluate import (
    TUNING_GRIDS,
    build_model,
    cross_validate,
    describe_grid,
    jaccard_stability,
    model_family,
)
from backend.ml.quantum.noise import SimConfig, gate_counts, noise_model, simulated_scores
from backend.ml.quantum.preprocess import make_preprocessor

NQ = 4


@pytest.fixture(scope="module")
def trained():
    X, y, _ = load_dataset("heart")
    X, y = stratified_subsample(X, y, 60, seed=42)
    A = make_preprocessor(NQ).fit(X, y).transform(X)
    return A, y, build_model("vqc", NQ, epochs=2).fit(A, y)


def test_simconfig_validation():
    with pytest.raises(ValueError):
        SimConfig("nope")
    with pytest.raises(ValueError):
        SimConfig("default.qubit", p2=0.01)  # noise needs a density-matrix device
    with pytest.raises(ValueError):
        SimConfig("default.mixed", shots=0)
    assert "exact" in SimConfig().label


def test_noiseless_devices_agree_and_noise_changes_outputs(trained):
    A, _, m = trained
    exact = m.predict_proba(A)[:, 1]
    for device in ("default.qubit", "lightning.qubit", "default.mixed"):
        assert np.allclose(simulated_scores(m, A, SimConfig(device)), exact, atol=1e-8)
    noisy = simulated_scores(m, A, SimConfig("default.mixed", p1=0.002, p2=0.02))
    assert not np.allclose(noisy, exact) and np.all((noisy >= 0) & (noisy <= 1))
    # depolarising noise pulls <Z> towards 0, so scores move towards sigmoid(bias)
    centre = 1 / (1 + np.exp(-float(m.module_.bias)))
    assert np.mean(np.abs(noisy - centre)) < np.mean(np.abs(exact - centre))
    shots = simulated_scores(m, A, SimConfig("default.mixed", shots=200))
    assert np.allclose(shots, simulated_scores(m, A, SimConfig("default.mixed", shots=200)))  # seeded


def test_noise_model_rules():
    assert len(noise_model(0.01, 0.0).model_map) == 1 and len(noise_model(0.01, 0.02).model_map) == 2


def test_gate_counts_and_classical_ablation_rejected(trained):
    A, y, m = trained
    g = gate_counts(m, A[0])
    assert g["gates"]["CNOT"] == 2 * NQ and g["num_gates"] == 2 * NQ + 2 * NQ * 2 + NQ
    cls = build_model("hybrid_classical", NQ, epochs=1).fit(A, y)
    with pytest.raises(ValueError):
        simulated_scores(cls, A, SimConfig())


def test_noise_sweep_cli(tmp_path, monkeypatch):
    monkeypatch.setattr(noise, "NOISE_LEVELS", [(0.001, 0.01), (0.05, 0.0)])
    monkeypatch.setattr(noise, "SHOTS", (None,))
    monkeypatch.setattr(noise, "_fold_models", _two_small_folds)
    noise.main(["sweep", "--dataset", "heart", "--models", "vqc", "--out", str(tmp_path)])
    rows = json.loads((tmp_path / "noise.json").read_text(encoding="utf-8"))["results"][0]["rows"]
    assert len(rows) == 4 and rows[0]["delta_auc_vs_exact"]["delta"] == 0
    assert (tmp_path / "noise_heart_vqc.png").is_file()


def _two_small_folds(name, dataset, chosen, n_qubits, seed):
    X, y, _ = load_dataset(dataset)
    X, y = stratified_subsample(X, y, 60, seed)
    half = np.arange(len(y)) % 2 == 0
    for tr, va in ((half, ~half), (~half, half)):
        pre = make_preprocessor(NQ).fit(X[tr], y[tr])
        yield y, np.flatnonzero(va), build_model(name, NQ, epochs=2).fit(pre.transform(X[tr]), y[tr]), pre.transform(X[va])


def test_device_comparison_cli(tmp_path, monkeypatch):
    real = noise.device_comparison
    monkeypatch.setattr(noise, "device_comparison", lambda: real(n_qubits_list=(4,)))
    noise.main(["devices", "--out", str(tmp_path)])
    rows = json.loads((tmp_path / "devices.json").read_text(encoding="utf-8"))["rows"]
    assert rows[0]["n_qubits"] == 4 and rows[0]["max_abs_diff"] < 1e-6  # measured ~1e-8 (float rounding)


def test_feature_selection_sweep_grid_and_stability():
    grid = TUNING_GRIDS["vqc_fs"]
    assert len(grid) == 6 and all(g["model__n_qubits"][0] in (4, 6, 8) for g in grid)
    assert "model__n_qubits" not in TUNING_GRIDS["logreg_fs"][0] and model_family("qsvm_fs") == "quantum"
    assert describe_grid(grid)[0]["pre__select"] == ["mutual_info(k=4)"]
    assert describe_grid(grid)[1]["pre__select"] == ["pca(k=4)"]
    assert jaccard_stability([[1, 2], [1, 2], [2, 3]]) == pytest.approx((1 + 1 / 3 + 1 / 3) / 3)
    assert jaccard_stability([[1]]) is None


def test_feature_selection_sweep_runs_nested():
    X, y, _ = load_dataset("breast_cancer")
    X, y = stratified_subsample(X, y, 90, seed=42)
    r = cross_validate("logreg_fs", X, y, n_qubits=6, n_splits=3, max_train=60, tuned=True)
    assert all(set(c) == {"select"} for c in r["tuning"]["chosen"])
    q = cross_validate("qsvm_fs", X, y, n_qubits=6, n_splits=2, max_train=40, tuned=True)
    k = int(q["tuning"]["chosen"][-1]["select"].split("k=")[1].rstrip(")"))
    assert q["n_qubits"] == k == q["tuning"]["chosen"][-1]["n_qubits"]
    assert r["feature_stability_jaccard"] is None or 0 <= r["feature_stability_jaccard"] <= 1
