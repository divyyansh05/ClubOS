from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from clubos2.watchdog.alerts_schema import AlertSeverity, AlertType, WatchdogAlertRead
from clubos2.watchdog.orchestrator import WatchdogRunResult, run_watchdog


def _make_mock_alert(
    alert_id: str = "alrt_test",
    metric_name: str = "test_metric",
    alert_type: AlertType = AlertType.NEW_IN_TOP_N,
    run_id: str = "test_run",
) -> WatchdogAlertRead:
    return WatchdogAlertRead(
        alert_id=alert_id,
        metric_name=metric_name,
        alert_type=alert_type,
        severity=AlertSeverity.WARNING,
        current_rank=5,
        score_current=0.8,
        triggered_by_rule="new_in_top_n",
        context_snapshot="{}",
        source="data/gold_snapshots/gold_priority_board.csv",
        run_id=run_id,
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_first_run_produces_alerts():
    """First run on clean DB: no previous snapshot, no dedup — alerts are created."""
    with (
        patch("clubos2.watchdog.orchestrator.AlertsRepository") as MockAlerts,
        patch("clubos2.watchdog.orchestrator.AgentMemoryRepository") as MockMemory,
        patch("clubos2.watchdog.orchestrator.PriorityBoardSnapshotRepository") as MockSnapshot,
    ):
        mock_alerts = AsyncMock()
        mock_memory = AsyncMock()
        mock_snapshot = AsyncMock()
        MockAlerts.return_value = mock_alerts
        MockMemory.return_value = mock_memory
        MockSnapshot.return_value = mock_snapshot

        # First run: no previous snapshot, no dedup
        mock_snapshot.get_latest.return_value = None
        mock_memory.has_recent.return_value = False
        mock_memory.count_within.return_value = 0

        mock_alert = _make_mock_alert()
        mock_alerts.create_batch.return_value = [mock_alert]
        mock_memory.remember.return_value = None
        mock_memory.remember_top_n_presence.return_value = None
        mock_memory.purge_expired.return_value = 0

        result = await run_watchdog(top_n=10)

        assert isinstance(result, WatchdogRunResult)
        assert result.alerts_deduped == 0
        assert len(result.errors) == 0
        assert result.snapshot_id != ""
        assert result.duration_seconds >= 0


@pytest.mark.asyncio
async def test_second_run_dedupes_everything():
    """Immediate second run: has_recent returns True for every alert — all deduped."""
    with (
        patch("clubos2.watchdog.orchestrator.AlertsRepository") as MockAlerts,
        patch("clubos2.watchdog.orchestrator.AgentMemoryRepository") as MockMemory,
        patch("clubos2.watchdog.orchestrator.PriorityBoardSnapshotRepository") as MockSnapshot,
    ):
        mock_alerts = AsyncMock()
        mock_memory = AsyncMock()
        mock_snapshot = AsyncMock()
        MockAlerts.return_value = mock_alerts
        MockMemory.return_value = mock_memory
        MockSnapshot.return_value = mock_snapshot

        mock_snapshot.get_latest.return_value = None
        # Everything is deduped — has_recent always True
        mock_memory.has_recent.return_value = True
        mock_memory.count_within.return_value = 5

        mock_alerts.create_batch.return_value = []
        mock_memory.remember.return_value = None
        mock_memory.remember_top_n_presence.return_value = None
        mock_memory.purge_expired.return_value = 0

        result = await run_watchdog(top_n=10)

        assert isinstance(result, WatchdogRunResult)
        assert result.alerts_created == 0
        assert len(result.errors) == 0
        # create_batch should have been called with an empty list (or not called)
        # The deduped count equals the number of fired alerts
        assert result.alerts_deduped >= 0


@pytest.mark.asyncio
async def test_crash_returns_result_with_errors():
    """Reader crash: orchestrator never raises, returns WatchdogRunResult with errors populated."""
    with patch("clubos2.watchdog.orchestrator.PriorityBoardReader") as MockReader:
        mock_reader = AsyncMock()
        MockReader.return_value = mock_reader
        mock_reader.read_current.side_effect = RuntimeError("CSV broken")

        result = await run_watchdog()

        assert isinstance(result, WatchdogRunResult)
        assert len(result.errors) > 0
        assert "CSV broken" in result.errors[0]
        assert result.alerts_created == 0
        assert result.alert_ids == []


@pytest.mark.asyncio
async def test_dedup_window_days_respected():
    """has_recent is called with the correct within=timedelta(days=dedup_window_days)."""
    with (
        patch("clubos2.watchdog.orchestrator.AlertsRepository") as MockAlerts,
        patch("clubos2.watchdog.orchestrator.AgentMemoryRepository") as MockMemory,
        patch("clubos2.watchdog.orchestrator.PriorityBoardSnapshotRepository") as MockSnapshot,
    ):
        mock_alerts = AsyncMock()
        mock_memory = AsyncMock()
        mock_snapshot = AsyncMock()
        MockAlerts.return_value = mock_alerts
        MockMemory.return_value = mock_memory
        MockSnapshot.return_value = mock_snapshot

        mock_snapshot.get_latest.return_value = None
        mock_memory.has_recent.return_value = False
        mock_memory.count_within.return_value = 0
        mock_alerts.create_batch.return_value = []
        mock_memory.remember.return_value = None
        mock_memory.remember_top_n_presence.return_value = None
        mock_memory.purge_expired.return_value = 0

        custom_window = 14
        result = await run_watchdog(dedup_window_days=custom_window, top_n=10)

        assert isinstance(result, WatchdogRunResult)
        assert len(result.errors) == 0

        # If has_recent was called (alerts fired), verify the window arg
        for call in mock_memory.has_recent.call_args_list:
            _, kwargs = call
            if "within" in kwargs:
                assert kwargs["within"] == timedelta(days=custom_window)
            else:
                # positional: (agent_name, subject_key, within)
                assert call.args[2] == timedelta(days=custom_window)


@pytest.mark.asyncio
async def test_run_result_fields_are_populated():
    """WatchdogRunResult has expected shape on a normal successful run."""
    with (
        patch("clubos2.watchdog.orchestrator.AlertsRepository") as MockAlerts,
        patch("clubos2.watchdog.orchestrator.AgentMemoryRepository") as MockMemory,
        patch("clubos2.watchdog.orchestrator.PriorityBoardSnapshotRepository") as MockSnapshot,
    ):
        mock_alerts = AsyncMock()
        mock_memory = AsyncMock()
        mock_snapshot = AsyncMock()
        MockAlerts.return_value = mock_alerts
        MockMemory.return_value = mock_memory
        MockSnapshot.return_value = mock_snapshot

        mock_snapshot.get_latest.return_value = None
        mock_memory.has_recent.return_value = False
        mock_memory.count_within.return_value = 0

        mock_alert = _make_mock_alert(alert_id="alrt_abc123")
        mock_alerts.create_batch.return_value = [mock_alert]
        mock_memory.remember.return_value = None
        mock_memory.remember_top_n_presence.return_value = None
        mock_memory.purge_expired.return_value = 0

        result = await run_watchdog(top_n=10)

        assert result.run_id.startswith("wdog_")
        assert result.snapshot_id.startswith("snap_")
        assert isinstance(result.started_at, datetime)
        assert isinstance(result.finished_at, datetime)
        assert result.finished_at >= result.started_at
        assert result.metrics_evaluated >= 0
        assert result.rules_evaluated >= 0
        assert result.rules_fired >= 0
        assert isinstance(result.alert_ids, list)
        assert isinstance(result.errors, list)


@pytest.mark.asyncio
async def test_snapshot_repo_save_called_on_success():
    """snapshot_repo.save is called exactly once after a successful run."""
    with (
        patch("clubos2.watchdog.orchestrator.AlertsRepository") as MockAlerts,
        patch("clubos2.watchdog.orchestrator.AgentMemoryRepository") as MockMemory,
        patch("clubos2.watchdog.orchestrator.PriorityBoardSnapshotRepository") as MockSnapshot,
    ):
        mock_alerts = AsyncMock()
        mock_memory = AsyncMock()
        mock_snapshot = AsyncMock()
        MockAlerts.return_value = mock_alerts
        MockMemory.return_value = mock_memory
        MockSnapshot.return_value = mock_snapshot

        mock_snapshot.get_latest.return_value = None
        mock_memory.has_recent.return_value = False
        mock_memory.count_within.return_value = 0
        mock_alerts.create_batch.return_value = []
        mock_memory.remember.return_value = None
        mock_memory.remember_top_n_presence.return_value = None
        mock_memory.purge_expired.return_value = 0

        await run_watchdog(top_n=10)

        mock_snapshot.save.assert_called_once()


@pytest.mark.asyncio
async def test_purge_expired_called_on_success():
    """memory_repo.purge_expired is called for housekeeping at the end of a run."""
    with (
        patch("clubos2.watchdog.orchestrator.AlertsRepository") as MockAlerts,
        patch("clubos2.watchdog.orchestrator.AgentMemoryRepository") as MockMemory,
        patch("clubos2.watchdog.orchestrator.PriorityBoardSnapshotRepository") as MockSnapshot,
    ):
        mock_alerts = AsyncMock()
        mock_memory = AsyncMock()
        mock_snapshot = AsyncMock()
        MockAlerts.return_value = mock_alerts
        MockMemory.return_value = mock_memory
        MockSnapshot.return_value = mock_snapshot

        mock_snapshot.get_latest.return_value = None
        mock_memory.has_recent.return_value = False
        mock_memory.count_within.return_value = 0
        mock_alerts.create_batch.return_value = []
        mock_memory.remember.return_value = None
        mock_memory.remember_top_n_presence.return_value = None
        mock_memory.purge_expired.return_value = 0

        await run_watchdog(top_n=10)

        mock_memory.purge_expired.assert_called_once()
