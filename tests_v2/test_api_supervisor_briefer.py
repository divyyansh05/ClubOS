from __future__ import annotations

import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

sys.path.insert(0, "BACKEND/api")
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def _uid() -> str:
    return uuid4().hex[:8]


# ---------------------------------------------------------------------------
# Endpoint registration
# ---------------------------------------------------------------------------

def test_supervisor_endpoints_registered(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/ai/supervisor/query" in paths


def test_briefer_endpoints_registered(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/ai/briefer/run" in paths
    assert "/api/ai/briefer/run_monthly" in paths
    assert "/api/ai/briefer" in paths
    assert "/api/ai/briefer/{briefing_id}" in paths


# ---------------------------------------------------------------------------
# POST /api/ai/supervisor/query
# ---------------------------------------------------------------------------

def test_supervisor_query_direct_scout(client):
    """Scout query returns 200 with dispatch_path=direct_scout."""
    from clubos2.agents.scout_schemas import ScoutAnswer, Citation

    answer = ScoutAnswer(
        answer="streaming_daily_users is 50k.",
        metric_name="streaming_daily_users",
        value=50000.0,
        unit="users",
        citations=[Citation(claim="50k", source="metric_registry", section=None, quote=None)],
        confidence="high",
        caveat=None,
    )

    with patch("clubos2.supervisor.classifier._load_known_metric_names", return_value=["streaming_daily_users"]):
        with patch("clubos2.agents.scout.run_scout", new=AsyncMock(return_value=answer)):
            response = client.post(
                "/api/ai/supervisor/query",
                json={"query": "what is streaming_daily_users this month"},
            )

    assert response.status_code == 200
    body = response.json()
    assert body["dispatch_path"] == "direct_scout"
    assert body["error"] is None


def test_supervisor_query_too_short_422(client):
    """Query shorter than 3 chars → 422 from Pydantic validation."""
    response = client.post("/api/ai/supervisor/query", json={"query": "hi"})
    assert response.status_code == 422


def test_supervisor_query_too_long_422(client):
    """Query longer than 2000 chars → 422."""
    response = client.post("/api/ai/supervisor/query", json={"query": "x" * 2001})
    assert response.status_code == 422


def test_supervisor_query_briefer_dispatch(client):
    """Briefing query → direct_briefer dispatch."""
    from clubos2.briefer.agent_schemas import BriefingRunResult, BriefingType

    brf_result = BriefingRunResult(
        briefing_id=f"brf_{_uid()}",
        briefing_type=BriefingType.MONTHLY_SCHEDULED,
        scope_key="monthly:2026-06",
        status="completed",
        was_cached=False,
        content=None,
        latency_seconds=1.5,
    )

    with patch("clubos2.supervisor.classifier._load_known_metric_names", return_value=[]):
        with patch("clubos2.briefer.orchestrator.run_briefing", new=AsyncMock(return_value=brf_result)):
            response = client.post(
                "/api/ai/supervisor/query",
                json={"query": "give me a monthly summary"},
            )

    assert response.status_code == 200
    body = response.json()
    assert body["dispatch_path"] == "direct_briefer"


# ---------------------------------------------------------------------------
# POST /api/ai/briefer/run
# ---------------------------------------------------------------------------

def test_briefer_run_returns_200(client):
    """Happy-path briefer run returns 200."""
    from clubos2.briefer.agent_schemas import BriefingRunResult, BriefingType

    brf_result = BriefingRunResult(
        briefing_id=f"brf_{_uid()}",
        briefing_type=BriefingType.AD_HOC_SUMMARY,
        scope_key="adhoc:test",
        status="completed",
        was_cached=False,
        content=None,
        latency_seconds=2.1,
    )

    with patch("app.routers.briefer.run_briefing", new=AsyncMock(return_value=brf_result)):
        response = client.post(
            "/api/ai/briefer/run",
            json={
                "briefing_type": "ad_hoc_summary",
                "scope_key": "adhoc:test",
                "period_start": "2026-06-01T00:00:00",
                "period_end": "2026-06-30T23:59:59",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["briefing_id"].startswith("brf_")


def test_briefer_run_invalid_briefing_type_422(client):
    """Invalid briefing_type returns 422."""
    response = client.post(
        "/api/ai/briefer/run",
        json={
            "briefing_type": "not_a_valid_type",
            "scope_key": "adhoc:x",
            "period_start": "2026-06-01T00:00:00",
            "period_end": "2026-06-30T23:59:59",
        },
    )
    assert response.status_code == 422


def test_briefer_run_cached_result(client):
    """Cached briefing returns was_cached=True."""
    from clubos2.briefer.agent_schemas import BriefingRunResult, BriefingType

    brf_result = BriefingRunResult(
        briefing_id=f"brf_{_uid()}",
        briefing_type=BriefingType.MONTHLY_SCHEDULED,
        scope_key="monthly:2026-05",
        status="cached",
        was_cached=True,
        content=None,
        latency_seconds=0.01,
    )

    with patch("app.routers.briefer.run_briefing", new=AsyncMock(return_value=brf_result)):
        response = client.post(
            "/api/ai/briefer/run",
            json={
                "briefing_type": "monthly_scheduled",
                "scope_key": "monthly:2026-05",
                "period_start": "2026-05-01T00:00:00",
                "period_end": "2026-05-31T23:59:59",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["was_cached"] is True
    assert body["status"] == "cached"


# ---------------------------------------------------------------------------
# POST /api/ai/briefer/run_monthly
# ---------------------------------------------------------------------------

def test_run_monthly_explicit_year_month(client):
    """run_monthly with explicit year_month returns 200."""
    from clubos2.briefer.agent_schemas import BriefingRunResult, BriefingType

    brf_result = BriefingRunResult(
        briefing_id=f"brf_{_uid()}",
        briefing_type=BriefingType.MONTHLY_SCHEDULED,
        scope_key="monthly:2026-03",
        status="completed",
        was_cached=False,
        content=None,
        latency_seconds=3.0,
    )

    with patch("app.routers.briefer.run_briefing", new=AsyncMock(return_value=brf_result)):
        response = client.post("/api/ai/briefer/run_monthly?year_month=2026-03")

    assert response.status_code == 200
    body = response.json()
    assert body["scope_key"] == "monthly:2026-03"


def test_run_monthly_default_period(client):
    """run_monthly with no year_month defaults to last complete month."""
    from clubos2.briefer.agent_schemas import BriefingRunResult, BriefingType

    brf_result = BriefingRunResult(
        briefing_id=f"brf_{_uid()}",
        briefing_type=BriefingType.MONTHLY_SCHEDULED,
        scope_key="monthly:2026-06",
        status="completed",
        was_cached=False,
        content=None,
        latency_seconds=2.5,
    )

    with patch("app.routers.briefer.run_briefing", new=AsyncMock(return_value=brf_result)):
        response = client.post("/api/ai/briefer/run_monthly")

    assert response.status_code == 200


def test_run_monthly_invalid_format_422(client):
    """Malformed year_month → 422."""
    response = client.post("/api/ai/briefer/run_monthly?year_month=notadate")
    assert response.status_code == 422


def test_run_monthly_invalid_month_422(client):
    """Out-of-range month → 422."""
    response = client.post("/api/ai/briefer/run_monthly?year_month=2026-13")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/ai/briefer  (list)
# ---------------------------------------------------------------------------

def test_list_briefings_returns_200(client):
    with patch("clubos2.briefer.repo.BriefingRepository.list_recent", new=AsyncMock(return_value=[])):
        response = client.get("/api/ai/briefer")
    assert response.status_code == 200
    assert response.json() == []


def test_list_briefings_with_type_filter(client):
    with patch("clubos2.briefer.repo.BriefingRepository.list_recent", new=AsyncMock(return_value=[])):
        response = client.get("/api/ai/briefer?briefing_type=monthly_scheduled&limit=5")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/ai/briefer/{briefing_id}
# ---------------------------------------------------------------------------

def test_get_briefing_404_on_unknown(client):
    with patch("clubos2.briefer.repo.BriefingRepository.get_by_id", new=AsyncMock(return_value=None)):
        response = client.get("/api/ai/briefer/brf_doesnotexist")
    assert response.status_code == 404


def test_get_briefing_returns_200(client):
    from clubos2.briefer.schema import BriefingRead, BriefingStatus, BriefingType as ST
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    fake = BriefingRead(
        briefing_id=f"brf_{_uid()}",
        briefing_type=ST.MONTHLY_SCHEDULED,
        scope_key="monthly:2026-06",
        period_start=now,
        period_end=now,
        triggered_by="test",
        status=BriefingStatus.COMPLETED,
        citations=[],
        investigations_referenced=[],
        alerts_referenced=[],
        metrics_covered=[],
        freshness_days=7,
        started_at=now,
    )

    with patch("clubos2.briefer.repo.BriefingRepository.get_by_id", new=AsyncMock(return_value=fake)):
        response = client.get(f"/api/ai/briefer/{fake.briefing_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["briefing_id"] == fake.briefing_id


# ---------------------------------------------------------------------------
# Previous endpoints unaffected
# ---------------------------------------------------------------------------

def test_watchdog_endpoints_still_registered(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/ai/watchdog/run" in paths


def test_investigator_endpoints_still_registered(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/ai/investigator/run/{alert_id}" in paths


def test_ai_query_endpoint_still_registered(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/ai/query" in paths
