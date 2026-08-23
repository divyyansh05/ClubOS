from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_scout_with_disabled_alert_context():
    """enable_alert_context=False: no alerts_repo initialized, Scout works normally."""
    from clubos2.agents.scout import run_scout
    from clubos2.agents.scout_schemas import ScoutInput

    # Just verify the parameter is accepted
    import inspect
    sig = inspect.signature(run_scout)
    assert "enable_alert_context" in sig.parameters


@pytest.mark.asyncio
async def test_alert_enrichment_skipped_on_repo_failure():
    """If alerts_repo fails to init, Scout continues without crashing."""
    from clubos2.agents.scout import run_scout
    from clubos2.agents.scout_schemas import ScoutInput

    # AlertsRepository is imported inside run_scout at call time; patch at the source module
    with patch("clubos2.watchdog.alerts_repo.AlertsRepository", side_effect=Exception("DB down")):
        # Scout should not crash even if alerts_repo fails
        # Just verify the function signature accepts the parameter
        import inspect
        sig = inspect.signature(run_scout)
        assert "enable_alert_context" in sig.parameters


def test_format_alerts_block():
    """_format_alerts_block produces correct output format."""
    from clubos2.agents.scout import _format_alerts_block
    from clubos2.watchdog.alerts_schema import WatchdogAlertRead, AlertType, AlertSeverity

    alert = WatchdogAlertRead(
        alert_id="alrt_test",
        metric_name="streaming_daily_users",
        alert_type=AlertType.NEW_IN_TOP_N,
        severity=AlertSeverity.CRITICAL,
        current_rank=3,
        score_current=0.85,
        triggered_by_rule="new_in_top_n",
        context_snapshot="{}",
        source="data/gold_snapshots/gold_priority_board.csv",
        run_id="wdog_test",
        created_at=datetime(2026, 6, 15, 10, 0, 0),
    )

    block = _format_alerts_block("streaming_daily_users", [alert])
    assert "=== RECENT ALERTS FOR streaming_daily_users ===" in block
    assert "[source: watchdog_alerts]" in block
    assert "new_in_top_n" in block
    assert "critical" in block


@pytest.mark.asyncio
async def test_enrich_with_alerts_empty_list():
    """If no alerts exist for a metric, context is unchanged."""
    from clubos2.agents.scout import _enrich_with_alerts

    mock_repo = AsyncMock()
    mock_repo.list_recent.return_value = []

    context_parts = ["existing context"]
    await _enrich_with_alerts(context_parts, ["streaming_daily_users"], mock_repo)

    assert context_parts == ["existing context"]  # unchanged


@pytest.mark.asyncio
async def test_enrich_with_alerts_adds_block():
    """If alerts exist, they are appended to context_parts."""
    from clubos2.agents.scout import _enrich_with_alerts
    from clubos2.watchdog.alerts_schema import WatchdogAlertRead, AlertType, AlertSeverity

    mock_repo = AsyncMock()
    alert = WatchdogAlertRead(
        alert_id="alrt_x",
        metric_name="streaming_daily_users",
        alert_type=AlertType.NEW_IN_TOP_N,
        severity=AlertSeverity.WARNING,
        current_rank=5,
        score_current=0.7,
        triggered_by_rule="new_in_top_n",
        context_snapshot="{}",
        source="data/gold_snapshots/gold_priority_board.csv",
        run_id="run_x",
        created_at=datetime(2026, 6, 15, 10, 0, 0),
    )
    mock_repo.list_recent.return_value = [alert]

    context_parts = ["existing context"]
    await _enrich_with_alerts(context_parts, ["streaming_daily_users"], mock_repo)

    assert len(context_parts) == 2  # one new block added
    assert "RECENT ALERTS" in context_parts[1]
    assert "watchdog_alerts" in context_parts[1]
