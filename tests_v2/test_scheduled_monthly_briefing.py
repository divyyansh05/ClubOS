from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from scripts.scheduled_monthly_briefing import main


def _brf(status: str, error: str | None = None):
    from clubos2.briefer.agent_schemas import BriefingRunResult, BriefingType
    return BriefingRunResult(
        briefing_id="brf_test",
        briefing_type=BriefingType.MONTHLY_SCHEDULED,
        scope_key="monthly:2026-06",
        status=status,
        was_cached=(status == "cached"),
        content=None,
        latency_seconds=1.0,
        error=error,
    )


@pytest.mark.asyncio
async def test_exit_0_on_completed():
    with patch("clubos2.briefer.orchestrator.run_briefing", new=AsyncMock(return_value=_brf("completed"))):
        code = await main()
    assert code == 0


@pytest.mark.asyncio
async def test_exit_0_on_cached():
    with patch("clubos2.briefer.orchestrator.run_briefing", new=AsyncMock(return_value=_brf("cached"))):
        code = await main()
    assert code == 0


@pytest.mark.asyncio
async def test_exit_1_on_failed():
    with patch("clubos2.briefer.orchestrator.run_briefing", new=AsyncMock(return_value=_brf("failed", error="LLM timeout"))):
        code = await main()
    assert code == 1


@pytest.mark.asyncio
async def test_scope_key_is_previous_month():
    """Script always targets the previous complete calendar month, not the current one."""
    from datetime import datetime, timezone

    captured_inputs = []

    async def capture(inp):
        captured_inputs.append(inp)
        return _brf("completed")

    with patch("clubos2.briefer.orchestrator.run_briefing", new=AsyncMock(side_effect=capture)):
        await main()

    assert len(captured_inputs) == 1
    inp = captured_inputs[0]

    now = datetime.utcnow()
    # The briefing must NOT be for the current month
    current_ym = now.strftime("%Y-%m")
    assert inp.scope_key != f"monthly:{current_ym}", (
        f"Script should target the previous month, not the current month {current_ym}"
    )
    # scope_key must match the monthly: prefix
    assert inp.scope_key.startswith("monthly:")
    assert inp.triggered_by == "scheduled_cron"
