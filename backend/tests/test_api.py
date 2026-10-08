import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ECG_WEIGHTS_PATH", str(tmp_path / "missing_ecg.pth"))
    monkeypatch.setenv("XRAY_WEIGHTS_PATH", str(tmp_path / "missing_xray.pth"))
    import backend.main as main

    main.MODELS["ecg"].__init__()
    main.MODELS["xray"].__init__()
    with TestClient(app) as c:
        yield c


def test_health_reports_truthful_status(client):
    models = client.get("/health").json()["models"]
    assert set(models) == {"ecg", "xray", "ct"}
    assert all(m["loaded"] is False for m in models.values())


@pytest.mark.parametrize("modality", ["ecg", "xray", "ct"])
def test_unloaded_model_returns_503(client, modality):
    r = client.post(f"/api/analyze/{modality}", files={"file": ("a.csv", b"1,2,3", "text/csv")})
    assert r.status_code == 503
    assert "unavailable" in r.json()["detail"]
