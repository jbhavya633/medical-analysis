import pickle

import numpy as np
import pytest
import torch

from backend.ml.quantum import data as data_mod
from backend.ml.quantum.baselines import CLASSICAL_MODELS, build_baseline, count_params
from backend.ml.quantum.data import holdout_split, load_dataset, stratified_subsample
from backend.ml.quantum.evaluate import binary_metrics, build_model, cross_validate, learning_curve, model_family
from backend.ml.quantum.explain import feature_map_sensitivity, kernel_alignment, permutation_scores, shap_scores
from backend.ml.quantum.hybrid_qnn import HybridQNNClassifier
from backend.ml.quantum.preprocess import make_preprocessor, selected_feature_names, to_angles
from backend.ml.quantum.qkernel import QuantumKernelSVM, kernel_matrix, kernel_spectrum
from backend.ml.quantum.vqc import VQCClassifier

NQ = 4


@pytest.fixture(scope="module")
def small():
    X, y, names = load_dataset("breast_cancer")
    X, y = stratified_subsample(X, y, 80, seed=42)
    pre = make_preprocessor(NQ).fit(X, y)
    return X, y, names, pre, pre.transform(X)


def test_breast_cancer_positive_class_is_malignant():
    X, y, names = load_dataset("breast_cancer")
    assert X.shape == (569, 30) and len(names) == 30
    assert y.sum() == 212  # 212 malignant in the UCI dataset


def test_unknown_dataset():
    with pytest.raises(KeyError):
        load_dataset("nope")


def test_heart_offline_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(data_mod, "CACHE_DIR", tmp_path)

    def boom(*_, **__):
        raise OSError("offline")

    monkeypatch.setattr(data_mod.urllib.request, "urlopen", boom)
    with pytest.raises(data_mod.DatasetUnavailableError):
        load_dataset("heart")


def test_heart_from_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(data_mod, "CACHE_DIR", tmp_path)
    (tmp_path / "processed.cleveland.data").write_text(
        "63.0,1.0,1.0,145.0,233.0,1.0,2.0,150.0,0.0,2.3,3.0,0.0,6.0,0\n"
        "67.0,1.0,4.0,160.0,286.0,0.0,2.0,108.0,1.0,1.5,2.0,3.0,?,2\n")
    X, y, names = load_dataset("heart")
    assert X.shape == (2, 13) and y.tolist() == [0, 1] and np.isnan(X[1, 12])


def test_splits_are_stratified():
    X, y, _ = load_dataset("breast_cancer")
    X_tr, X_te, y_tr, y_te = holdout_split(X, y)
    assert len(y_te) == 114 and abs(y_tr.mean() - y_te.mean()) < 0.02
    Xs, ys = stratified_subsample(X, y, 100)
    assert len(ys) == 100 and abs(ys.mean() - y.mean()) < 0.02
    assert stratified_subsample(X[:10], y[:10], 50)[0].shape[0] == 10


@pytest.mark.parametrize("method", ["mutual_info", "pca"])
def test_preprocess_shape_and_range(small, method):
    X, y, names, _, _ = small
    pre = make_preprocessor(NQ, method).fit(X, y)
    A = pre.transform(X)
    assert A.shape == (len(X), NQ)
    assert A.min() >= 0 and A.max() <= np.pi + 1e-9
    assert len(selected_feature_names(pre, names)) == NQ
    assert pre.transform(X * 100).max() <= np.pi + 1e-9  # clipped for out-of-range data


def test_preprocess_bad_method():
    with pytest.raises(ValueError):
        make_preprocessor(4, "nope")


def test_to_angles():
    A = to_angles(np.array([[0.0, 5.0], [10.0, 5.0]]))
    assert np.allclose(A, [[0, 0], [np.pi, 0]])


@pytest.mark.parametrize("name", CLASSICAL_MODELS)
def test_baselines_fit_predict(small, name):
    _, y, _, _, A = small
    m = build_baseline(name).fit(A, y)
    assert m.predict(A).shape == y.shape
    assert m.predict_proba(A).shape == (len(y), 2)
    assert count_params(m) > 0


def test_unknown_baseline():
    with pytest.raises(KeyError):
        build_baseline("nope")


def test_kernel_matrix_properties(small):
    A = small[4][:20]
    K = kernel_matrix(A, A, NQ)
    assert np.allclose(K, K.T)
    assert np.allclose(np.diag(K), 1.0)
    assert np.linalg.eigvalsh(K).min() > -1e-8
    assert K.min() >= 0 and K.max() <= 1 + 1e-9


def test_bandwidth_one_is_the_original_map_and_smaller_widens_the_kernel(small):
    A = small[4][:15]
    assert np.allclose(kernel_matrix(A, A, NQ, bandwidth=1.0), kernel_matrix(A, A, NQ))
    wide, narrow = kernel_spectrum(kernel_matrix(A, A, NQ, bandwidth=0.1)), kernel_spectrum(kernel_matrix(A, A, NQ))
    assert wide["mean_offdiag"] > narrow["mean_offdiag"]
    assert 0 < narrow["eff_rank_ratio"] <= 1 and 0 < wide["top1_var"] <= 1


def test_qsvm_unpickled_without_bandwidth_still_predicts(small):
    _, y, _, _, A = small
    m = QuantumKernelSVM(n_qubits=NQ).fit(A, y)
    del m.__dict__["bandwidth"]  # artifacts saved before the parameter existed
    clone = pickle.loads(pickle.dumps(m))
    assert clone.bandwidth == 1.0 and clone.predict_proba(A[:3]).shape == (3, 2)


def test_qsvm_fit_predict(small):
    _, y, _, _, A = small
    m = QuantumKernelSVM(n_qubits=NQ).fit(A, y)
    assert m.predict(A).shape == y.shape
    assert m.predict_proba(A).shape == (len(y), 2)
    assert m.decision_function(A).shape == y.shape
    assert m.circuit_depth_ > 0 and m.n_qubits_ == NQ
    assert (m.predict(A) == y).mean() > 0.7


def test_quantum_models_reject_wrong_width(small):
    _, y, _, _, A = small
    for m in (QuantumKernelSVM(n_qubits=NQ + 1), VQCClassifier(n_qubits=NQ + 1)):
        with pytest.raises(ValueError):
            m.fit(A, y)


def test_vqc_loss_decreases_and_pickles(small):
    _, y, _, _, A = small
    m = VQCClassifier(n_qubits=NQ, n_layers=1, epochs=6, lr=0.1).fit(A, y)
    assert m.loss_history_[-1] < m.loss_history_[0]
    assert m.predict_proba(A).shape == (len(y), 2)
    clone = pickle.loads(pickle.dumps(m))
    assert np.allclose(clone.predict_proba(A), m.predict_proba(A))


@pytest.mark.parametrize("name,n_params", [("vqc", 2 * NQ * 2 + 2), ("vqc_3layer", 3 * NQ * 2 + 2),
                                           ("vqc_scale", 2 * NQ * 2 + 2 + 2 * NQ),
                                           ("vqc_reupload_scale", 2 * NQ * 2 + 2 + 2 * NQ),
                                           ("vqc_allz", 2 * NQ * 2 + 2), ("vqc_allz_noent", 2 * NQ * 2 + 2)])
def test_vqc_variants_fit_and_count_params(small, name, n_params):
    _, y, _, _, A = small
    m = build_model(name, NQ, epochs=2).fit(A, y)
    assert m.n_params_ == n_params and m.predict_proba(A).shape == (len(y), 2) and m.circuit_depth_ > 0
    clone = pickle.loads(pickle.dumps(m))
    assert np.allclose(clone.predict_proba(A[:4]), m.predict_proba(A[:4]))


def test_variants_start_from_the_base_circuit(small):
    _, _, _, _, A = small
    x = torch.tensor(A[:5])
    torch.manual_seed(0)
    base = VQCClassifier(n_qubits=NQ)._build().double()
    for opts in ({"input_scaling": "affine"}, {"input_scaling": "reupload", "n_layers": 1}):
        torch.manual_seed(0)
        v = VQCClassifier(n_qubits=NQ, **opts)._build().double()
        if opts.get("n_layers") == 1:  # one layer: re-uploading once == encoding once
            torch.manual_seed(0)
            base1 = VQCClassifier(n_qubits=NQ, n_layers=1)._build().double()
            assert torch.allclose(v(x), base1(x))
        else:
            assert torch.allclose(v(x), base(x))
    with pytest.raises(ValueError):
        VQCClassifier(n_qubits=NQ, readout="nope")._build()


def test_entanglement_ablation_removes_cnots():
    import pennylane as qml
    from backend.ml.quantum.vqc import make_qnode
    args = (torch.zeros(NQ, dtype=torch.float64), torch.zeros(2, NQ, 2, dtype=torch.float64))
    gates = lambda q: qml.specs(q)(*args)["resources"].gate_types  # noqa: E731
    assert gates(make_qnode(NQ, 2, True))["CNOT"] == 2 * NQ
    assert "CNOT" not in gates(make_qnode(NQ, 2, True, entangle=False))


@pytest.mark.parametrize("name,params,family", [("vqc_twin", 2 * NQ + 4 * NQ + 1, "classical"),
                                                ("residual_qnn", 2 * NQ * 2 + 2 * NQ + 1, "hybrid"),
                                                ("residual_classical", NQ * 4 + 4 + NQ + 4 + 1, "classical")])
def test_d4_controls(small, name, params, family):
    _, y, _, _, A = small
    m = build_model(name, NQ, epochs=2).fit(A, y)
    assert m.n_params_ == params and model_family(name) == family
    assert m.predict_proba(A).shape == (len(y), 2)
    assert (getattr(m, "circuit_depth_", None) is not None) == (family == "hybrid")


def test_hgb_and_matched_mlp(small):
    _, y, _, _, A = small
    for name in ("hgb", "mlp_matched"):
        m = build_model(name, NQ).fit(A, y)
        assert count_params(m) > 0
    assert count_params(build_model("mlp_matched", 6).fit(np.random.default_rng(0).random((30, 6)),
                                                         np.arange(30) % 2)) == 6 * 5 + 5 + 5 + 1


def test_hybrid_classical_ablation(small):
    _, y, _, _, A = small
    m = build_model("hybrid_classical", NQ, epochs=2).fit(A, y)
    assert not hasattr(m, "n_qubits_") and m.n_params_ == 2 * (NQ * NQ + NQ) + NQ + 1  # pre + mid + head
    assert model_family("hybrid_classical") == "classical"


def test_hybrid_qnn_forward_shape(small):
    _, y, _, _, A = small
    m = HybridQNNClassifier(n_qubits=NQ, n_layers=1, epochs=2).fit(A, y)
    out = m.module_(torch.tensor(A[:5]))
    assert tuple(out.shape) == (5, 1)
    assert m.predict(A).shape == y.shape and m.n_params_ > 0


def test_binary_metrics_hand_computed():
    # TP=2, FN=1, TN=3, FP=1
    y_true = np.array([1, 1, 1, 0, 0, 0, 0])
    y_pred = np.array([1, 1, 0, 0, 0, 0, 1])
    score = np.array([0.9, 0.8, 0.4, 0.1, 0.2, 0.3, 0.7])
    m = binary_metrics(y_true, y_pred, score)
    assert m["sensitivity"] == pytest.approx(2 / 3)
    assert m["specificity"] == pytest.approx(3 / 4)
    assert m["accuracy"] == pytest.approx(5 / 7)
    assert m["f1"] == pytest.approx(2 * 2 / (2 * 2 + 1 + 1))
    assert m["auc"] == pytest.approx(11 / 12)
    assert m["brier"] == pytest.approx(np.mean((score - y_true) ** 2))


def test_binary_metrics_single_class_auc_nan():
    m = binary_metrics(np.array([1, 1]), np.array([1, 0]), np.array([0.9, 0.1]))
    assert np.isnan(m["auc"]) and np.isnan(m["specificity"])


def test_build_model_and_family():
    assert isinstance(build_model("qsvm", 4), QuantumKernelSVM)
    assert isinstance(build_model("qsvm_c", 4), QuantumKernelSVM) and model_family("qsvm_c") == "quantum"
    assert isinstance(build_model("vqc", 4), VQCClassifier)
    assert isinstance(build_model("hybrid_qnn", 4), HybridQNNClassifier)
    assert [model_family(m) for m in ("logreg", "qsvm", "hybrid_qnn")] == ["classical", "quantum", "hybrid"]


def test_cross_validate_and_learning_curve(small):
    X, y, *_ = small
    r = cross_validate("logreg", X, y, n_qubits=NQ, n_splits=3, max_train=60)
    assert len(r["folds"]) == 3 and set(r["metrics"]) >= {"accuracy", "sensitivity", "specificity", "auc", "gen_gap"}
    assert r["roc"]["fpr"][0] == 0 and r["roc"]["tpr"][-1] == 1
    q = cross_validate("qsvm", X, y, n_qubits=NQ, n_splits=2, max_train=40)
    assert q["n_qubits"] == NQ and q["circuit_depth"] > 0
    lc = learning_curve("logreg", X, y, n_qubits=NQ, max_train=60, fractions=(0.5, 1.0))
    assert [p["n_train"] for p in lc] == sorted(p["n_train"] for p in lc)


def test_explainability(small):
    _, y, names, pre, A = small
    selected = selected_feature_names(pre, names)
    m = QuantumKernelSVM(n_qubits=NQ).fit(A, y)
    perm = permutation_scores(m, A, y, selected, n_repeats=2)
    assert set(perm) == set(selected)
    shap = shap_scores(m, A[:5], A[:2], selected, nsamples=20)
    assert shap is None or set(shap) == set(selected)
    K = kernel_matrix(A, A, NQ)
    assert -1 <= kernel_alignment(K, y) <= 1
    assert kernel_alignment(np.outer(2 * y - 1, 2 * y - 1).astype(float), y) == pytest.approx(1.0)
    sens = feature_map_sensitivity(A[:10], NQ, selected)
    assert all(v >= 0 for v in sens.values())
