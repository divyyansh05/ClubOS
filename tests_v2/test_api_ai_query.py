from __future__ import annotations

import sys
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

# Ensure BACKEND/api is in python path to import app.main
sys.path.insert(0, "BACKEND/api")
from app.main import app

client = TestClient(app)


def test_query_endpoint_registered():
    """/api/ai/query exists in OpenAPI schema."""
    schema = client.get("/openapi.json").json()
    assert "/api/ai/query" in schema["paths"]


def test_query_validates_input():
    """Empty question → 422."""
    response = client.post("/api/ai/query", json={"question": ""})
    assert response.status_code == 422


def test_query_too_long():
    """Question > 500 chars → 422."""
    response = client.post("/api/ai/query", json={"question": "x" * 501})
    assert response.status_code == 422


@patch("app.routers.ai_query.run_scout", new_callable=AsyncMock)
def test_query_happy_path(mock_run_scout):
    """Valid question → 200 with ScoutAnswer shape."""
    from clubos2.agents.scout_schemas import Confidence, ScoutAnswer

    mock_run_scout.return_value = ScoutAnswer(
        answer="Test answer",
        citations=[],
        confidence=Confidence.HIGH,
        assumptions_made=[],
        metrics_queried=["streaming_daily_users"],
        chunks_retrieved=3,
    )
    response = client.post(
        "/api/ai/query",
        json={"question": "what is streaming daily users this month?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert "trace_url" in body or body.get("trace_url") is None
    assert "latency_ms" in body
    assert body["confidence"] == "high"
