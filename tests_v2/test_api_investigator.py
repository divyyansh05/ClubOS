from __future__ import annotations
import sys
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

sys.path.insert(0, "BACKEND/api")
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def test_investigator_endpoints_registered(client):
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    assert "/api/ai/investigator/run/{alert_id}" in paths
    assert "/api/ai/investigator" in paths
    assert "/api/ai/investigator/{investigation_id}" in paths


def test_run_investigation_404_on_unknown_alert(client):
    with patch("clubos2.watchdog.alerts_repo.AlertsRepository.get_by_id", new_callable=AsyncMock) as mock:
        mock.return_value = None
        response = client.post("/api/ai/investigator/run/alrt_nonexistent", json={})
    assert response.status_code == 404


def test_list_investigations_returns_200(client):
    with patch("clubos2.investigator.repo.InvestigationRepository.list_recent", new_callable=AsyncMock) as mock:
        mock.return_value = []
        response = client.get("/api/ai/investigator")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["investigations"] == []


def test_get_investigation_404_on_unknown(client):
    with patch("clubos2.investigator.repo.InvestigationRepository.get_by_id", new_callable=AsyncMock) as mock:
        mock.return_value = None
        response = client.get("/api/ai/investigator/inv_nonexistent")
    assert response.status_code == 404


def test_list_investigations_invalid_status_422(client):
    response = client.get("/api/ai/investigator?status=invalid_status_xyz")
    assert response.status_code == 422
