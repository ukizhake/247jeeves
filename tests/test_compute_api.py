import json
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "tech_fire_couple.json"


def test_compute_simulate_stateless() -> None:
    profile = json.loads(FIXTURE.read_text())
    client = TestClient(app)
    res = client.post("/api/compute/simulate", json={"profile": profile})
    assert res.status_code == 200
    body = res.json()
    assert "profile_id" not in body
    assert body["result"]["years"]
    assert body["result"]["summary"]


def test_compute_rebalance_stateless() -> None:
    profile = json.loads(FIXTURE.read_text())
    client = TestClient(app)
    res = client.post("/api/compute/rebalance-report", json={"profile": profile})
    assert res.status_code == 200
    body = res.json()
    assert "profile_id" not in body
    assert "current" in body["result"]
    assert "target" in body["result"]
