from __future__ import annotations
import sys
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, "backend/api")


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


def test_watchdog_endpoint_registered(client):
    """Endpoint exists in OpenAPI schema."""
    schema = client.get("/openapi.json").json()
    assert "/api/ai/watchdog/run" in schema["paths"]


def test_watchdog_alerts_endpoint_registered(client):
    """Alerts endpoint exists in OpenAPI schema."""
    schema = client.get("/openapi.json").json()
    assert "/api/ai/watchdog/alerts" in schema["paths"]


@patch("app.routers.watchdog.run_watchdog", new_callable=AsyncMock)
def test_watchdog_run_happy_path(mock_run, client):
    from clubos2.watchdog.orchestrator import WatchdogRunResult
    mock_run.return_value = WatchdogRunResult(
        run_id="wdog_test123",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration_seconds=2.5,
        metrics_evaluated=20,
        rules_evaluated=120,
        rules_fired=5,
        alerts_created=3,
        alerts_deduped=2,
        snapshot_id="snap_test",
        alert_ids=["alrt_a", "alrt_b", "alrt_c"],
        errors=[],
    )
    response = client.post("/api/ai/watchdog/run", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == "wdog_test123"
    assert body["alerts_created"] == 3
    assert len(body["alert_ids"]) == 3


def test_watchdog_validates_top_n_too_large(client):
    response = client.post("/api/ai/watchdog/run", json={"top_n": 100})
    assert response.status_code == 422


def test_watchdog_validates_top_n_too_small(client):
    response = client.post("/api/ai/watchdog/run", json={"top_n": 1})
    assert response.status_code == 422


def test_alerts_endpoint_invalid_severity(client):
    response = client.get("/api/ai/watchdog/alerts?severity=extreme")
    assert response.status_code == 422


@patch("app.routers.watchdog.AlertsRepository")
def test_alerts_list_empty(MockRepo, client):
    mock_repo = AsyncMock()
    MockRepo.return_value = mock_repo
    mock_repo.list_recent.return_value = []
    response = client.get("/api/ai/watchdog/alerts")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["alerts"] == []


@patch("app.routers.watchdog.AlertsRepository")
def test_acknowledge_not_found(MockRepo, client):
    mock_repo = AsyncMock()
    MockRepo.return_value = mock_repo
    mock_repo.acknowledge.side_effect = KeyError("alert not found")
    response = client.post(
        "/api/ai/watchdog/alerts/nonexistent/acknowledge",
        json={"acknowledged_by": "divyansh"},
    )
    assert response.status_code == 404
