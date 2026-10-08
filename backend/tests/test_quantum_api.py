import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.ml.quantum import benchmark, service


@pytest.fixture(scope="module")
def results_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp("qml_results")
    mp = pytest.MonkeyPatch()
    mp.setattr(benchmark, "RESULTS_DIR", path)
    mp.setattr(service, "RESULTS_DIR", path)
    benchmark.main(["--dataset", "breast_cancer", "--folds", "2", "--epochs", "2", "--max-train", "40",
                    "--n-qubits", "4", "--models", "logreg,qsvm"])
    yield path
    mp.undo()


@pytest.fixture()
def client(results_dir, monkeypatch):
    monkeypatch.setattr(benchmark, "RESULTS_DIR", results_dir)
    monkeypatch.setattr(service, "RESULTS_DIR", results_dir)
    service._load_artifact.cache_clear()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_benchmark_files_written(results_dir):
    for name in ("summary.json", "summary.md", "benchmark_breast_cancer.json", "roc_breast_cancer.png",
                 "calibration_breast_cancer.png",
                 "learning_curve_breast_cancer.png", "importance_breast_cancer.png", "benchmark.log"):
        assert (results_dir / name).is_file(), name
    assert (results_dir / "models" / "breast_cancer_qsvm.joblib").is_file()


def test_tuned_cv_only_experiment_run(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark, "RESULTS_DIR", benchmark.RESULTS_DIR)  # --results-dir rebinds the global
    out = tmp_path / "exp"
    benchmark.main(["--dataset", "breast_cancer", "--folds", "2", "--max-train", "40", "--n-qubits", "4",
                    "--models", "logreg,qsvm", "--tune", "--cv-only", "--results-dir", str(out)])
    summary = (out / "summary.json").read_text(encoding="utf-8")
    assert '"tuned": true' in summary and '"chosen"' in summary
    assert not (out / "models").exists() and not list(out.glob("*.png"))
    assert "Nested tuning" in (out / "summary.md").read_text(encoding="utf-8")
    with pytest.raises(SystemExit):
        benchmark.main(["--models", "nope", "--results-dir", str(out)])


def test_benchmark_endpoint(client):
    r = client.get("/api/qml/benchmark")
    assert r.status_code == 200
    body = r.json()
    assert "breast_cancer" in body["datasets"]
    assert set(body["datasets"]["breast_cancer"]["models"]) == {"logreg", "qsvm"}
    assert "not a diagnostic tool" in body["disclaimer"].lower()
    assert "breast_cancer_qsvm" in body["trained_models"]
    ds = body["datasets"]["breast_cancer"]
    assert len(ds["y"]) == ds["n_samples"] == len(ds["models"]["qsvm"]["oof"]["score"])
    cmp = ds["models"]["qsvm"]["vs_reference"]
    assert cmp["vs"] == "logreg" and len(cmp["ci95"]) == 2 and isinstance(cmp["significant"], bool)
    assert "vs_reference" not in ds["models"]["logreg"]


def test_benchmark_missing_is_404(client, tmp_path, monkeypatch):
    monkeypatch.setattr(service, "RESULTS_DIR", tmp_path)
    r = client.get("/api/qml/benchmark")
    assert r.status_code == 404 and "request_id" in r.json()


def test_catalog_endpoints(client):
    assert {d["id"] for d in client.get("/api/qml/datasets").json()} == {"breast_cancer", "heart"}
    assert len(client.get("/api/qml/models").json()) == 8
    assert client.get("/api/qml/health").json()["benchmark_available"] is True


def test_train_validation_422(client):
    assert client.post("/api/qml/train", json={"dataset": "breast_cancer", "model": "nope"}).status_code == 422
    assert client.post("/api/qml/train", json={"dataset": "breast_cancer", "model": "qsvm", "n_qubits": 20}).status_code == 422


def test_train_job_completes(client):
    r = client.post("/api/qml/train", json={"dataset": "breast_cancer", "model": "logreg", "n_qubits": 4})
    assert r.status_code == 202
    job = client.get(f"/api/qml/jobs/{r.json()['job_id']}").json()
    assert job["status"] == "done" and job["model_id"].startswith("breast_cancer_logreg_4q_job_")
    assert 0 <= job["holdout_metrics"]["accuracy"] <= 1


def test_job_not_found(client):
    assert client.get("/api/qml/jobs/doesnotexist").status_code == 404


def test_train_busy_429(client, monkeypatch):
    monkeypatch.setattr(service, "MAX_RUNNING_JOBS", 0)
    assert client.post("/api/qml/train", json={"dataset": "breast_cancer", "model": "logreg"}).status_code == 429


def test_predict_contract(client):
    info = client.get("/api/qml/models/breast_cancer_qsvm").json()
    assert len(info["feature_names"]) == 30 and len(info["selected_features"]) == 4
    r = client.post("/api/qml/predict", json={"model_id": "breast_cancer_qsvm", "features": [None] * 30})
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["probability_disease"] <= 1 and body["predicted_label"] in (0, 1)
    assert body["explanation"] is None or len(body["explanation"]) == 4
    assert "not a diagnostic tool" in body["disclaimer"].lower()
    named = client.post("/api/qml/predict", json={"model_id": "breast_cancer_logreg", "features": {"mean radius": 20.0}})
    assert named.status_code == 200


@pytest.mark.parametrize("payload,status", [
    ({"model_id": "breast_cancer_qsvm", "features": [1.0, 2.0]}, 422),
    ({"model_id": "breast_cancer_qsvm", "features": {"bogus": 1.0}}, 422),
    ({"model_id": "missing_model", "features": [1.0]}, 404),
    ({"model_id": "../../etc/passwd", "features": [1.0]}, 422),
    ({"model_id": "breast_cancer_qsvm"}, 422),
])
def test_predict_errors(client, payload, status):
    assert client.post("/api/qml/predict", json=payload).status_code == status


def test_model_info_not_found(client):
    assert client.get("/api/qml/models/nope").status_code == 404


def test_no_raw_exception_text_leaks(client, monkeypatch):
    def boom():
        raise RuntimeError("secret-internal-detail")

    monkeypatch.setattr(service, "get_benchmark", boom)
    r = client.get("/api/qml/benchmark")
    assert r.status_code == 500
    assert "secret" not in r.text and r.json()["detail"] == "Internal server error"


def test_cors_allows_only_configured_origin(client):
    ok = client.get("/api/qml/health", headers={"Origin": "http://localhost:3000"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"
    bad = client.get("/api/qml/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in bad.headers


def test_request_size_limit(client):
    r = client.post("/api/qml/predict", content=b"{}", headers={"Content-Length": str(50 * 1024 * 1024),
                                                                "Content-Type": "application/json"})
    assert r.status_code == 413


def test_body_without_content_length_rejected(client):
    def chunks():
        yield b'{"model_id": "breast_cancer_qsvm", "features": []}'

    r = client.post("/api/qml/predict", content=chunks(), headers={"Content-Type": "application/json"})
    assert r.status_code == 411


def test_artifact_cache_reloads_after_overwrite(client, results_dir):
    import os
    first = client.get("/api/qml/models/breast_cancer_logreg").json()
    path = results_dir / "models" / "breast_cancer_logreg.joblib"
    art = service.joblib.load(path)
    art["holdout_metrics"] = {**art["holdout_metrics"], "accuracy": -1.0}
    service.joblib.dump(art, path)
    st = path.stat()
    os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 10_000_000))
    assert client.get("/api/qml/models/breast_cancer_logreg").json()["holdout_metrics"]["accuracy"] == -1.0
    assert first["holdout_metrics"]["accuracy"] != -1.0
