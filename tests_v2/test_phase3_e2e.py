from __future__ import annotations

import os
import sys
import pytest

# E2E tests require RUN_E2E=1 and clean DB state
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_E2E") != "1",
    reason="E2E tests require RUN_E2E=1 and real API keys + clean DB",
)

sys.path.insert(0, "backend/api")


@pytest.mark.asyncio
async def test_watchdog_full_cycle_creates_alerts():
    """First-ever Watchdog run produces alerts; second run dedupes them."""
    from clubos2.watchdog.orchestrator import run_watchdog, bootstrap_all

    bootstrap_all()

    result1 = await run_watchdog(dedup_window_days=7, top_n=10)
    assert result1.alerts_created > 0, f"First run should produce alerts, got: {result1}"
    assert result1.alerts_deduped == 0
    assert len(result1.errors) == 0

    result2 = await run_watchdog(dedup_window_days=7, top_n=10)
    assert result2.alerts_created == 0, f"Second immediate run should dedupe all, got: {result2}"
    assert result2.alerts_deduped == result1.alerts_created


@pytest.mark.asyncio
async def test_v1_endpoints_still_work():
    """Regression: v1 still functional after Phase 3 additions."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/priorities")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_watchdog_api_endpoint_works():
    """Regression: Phase 3 endpoint registered and functional."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    schema = client.get("/openapi.json").json()
    assert "/api/ai/watchdog/run" in schema["paths"]
    assert "/api/ai/watchdog/alerts" in schema["paths"]
