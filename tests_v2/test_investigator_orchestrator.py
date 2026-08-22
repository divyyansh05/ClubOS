from __future__ import annotations
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


def _make_finding_json(alert_id="alrt_test", metric="streaming_daily_users"):
    return json.dumps({
        "alert_id": alert_id,
        "metric_name": metric,
        "cause_hypothesis": "Test hypothesis for the metric.",
        "confidence": "medium",
        "evidence_summary": "- Evidence point one\n- Evidence point two",
        "citations": [],
        "reasoning_trace": [],
        "tools_called": ["get_metric_definition"],
        "total_steps": 2,
        "is_seasonal_or_expected": False,
        "data_gaps": [],
    })


def _make_alert_mock(alert_id="alrt_test", metric="streaming_daily_users"):
    from clubos2.watchdog.alerts_schema import WatchdogAlertRead, AlertType, AlertSeverity
    return WatchdogAlertRead(
        alert_id=alert_id,
        metric_name=metric,
        alert_type=AlertType.SCORE_JUMP,
        severity=AlertSeverity.WARNING,
        current_rank=2,
        previous_rank=5,
        rank_delta=-3,
        score_current=0.8,
        score_previous=0.5,
        triggered_by_rule="large_score_jump",
        context_snapshot="{}",
        source="test",
        run_id="run_test",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )


@pytest.mark.asyncio
async def test_happy_path_completed():
    """Mock graph returns valid finding JSON → status='completed'."""
    from clubos2.investigator.orchestrator import run_investigation
    from clubos2.investigator.agent_schemas import InvestigatorInput
    from langchain_core.messages import AIMessage

    finding_json = _make_finding_json()
    final_msg = AIMessage(content=finding_json, tool_calls=[])
    final_state = {
        "messages": [final_msg],
        "step_count": 2,
        "tools_called": ["get_metric_definition"],
        "reasoning_trace": [],
    }

    with (
        patch("clubos2.investigator.orchestrator.AlertsRepository") as MockAlerts,
        patch("clubos2.investigator.orchestrator.InvestigationRepository") as MockInvRepo,
        patch("clubos2.investigator.orchestrator.AgentMemoryRepository") as MockMemRepo,
        patch("clubos2.investigator.orchestrator.build_graph") as MockGraph,
        patch("clubos2.investigator.orchestrator.get_checkpointer") as MockCP,
        patch("clubos2.investigator.orchestrator.get_current_langsmith_trace_url", return_value=None),
    ):
        MockAlerts.return_value.get_by_id = AsyncMock(return_value=_make_alert_mock())
        mock_inv_repo = MagicMock()
        mock_inv_repo.start = AsyncMock(return_value=MagicMock(investigation_id="inv_test123"))
        mock_inv_repo.complete = AsyncMock()
        MockInvRepo.return_value = mock_inv_repo
        MockMemRepo.return_value.remember = AsyncMock()
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value=final_state)
        MockGraph.return_value = mock_graph
        MockCP.return_value = MagicMock()

        result = await run_investigation(InvestigatorInput(
            alert_id="alrt_test",
            metric_name="streaming_daily_users",
        ))

    assert result.status == "completed"
    assert result.finding is not None
    assert result.finding.cause_hypothesis == "Test hypothesis for the metric."
    mock_inv_repo.complete.assert_called_once()


@pytest.mark.asyncio
async def test_parse_failure_returns_failed():
    """Graph returns invalid JSON → status='failed'."""
    from clubos2.investigator.orchestrator import run_investigation
    from clubos2.investigator.agent_schemas import InvestigatorInput
    from langchain_core.messages import AIMessage

    final_msg = AIMessage(content="not json at all", tool_calls=[])
    final_state = {"messages": [final_msg], "step_count": 1, "tools_called": [], "reasoning_trace": []}

    with (
        patch("clubos2.investigator.orchestrator.AlertsRepository") as MockAlerts,
        patch("clubos2.investigator.orchestrator.InvestigationRepository") as MockInvRepo,
        patch("clubos2.investigator.orchestrator.AgentMemoryRepository"),
        patch("clubos2.investigator.orchestrator.build_graph") as MockGraph,
        patch("clubos2.investigator.orchestrator.get_checkpointer"),
        patch("clubos2.investigator.orchestrator.get_current_langsmith_trace_url", return_value=None),
    ):
        MockAlerts.return_value.get_by_id = AsyncMock(return_value=_make_alert_mock())
        mock_inv = MagicMock()
        mock_inv.start = AsyncMock(return_value=MagicMock(investigation_id="inv_fail1"))
        mock_inv.fail = AsyncMock()
        MockInvRepo.return_value = mock_inv
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value=final_state)
        MockGraph.return_value = mock_graph

        result = await run_investigation(InvestigatorInput(alert_id="alrt_test", metric_name="streaming_daily_users"))

    assert result.status == "failed"
    assert result.finding is None
    mock_inv.fail.assert_called_once()


@pytest.mark.asyncio
async def test_alert_not_found_returns_failed():
    from clubos2.investigator.orchestrator import run_investigation
    from clubos2.investigator.agent_schemas import InvestigatorInput

    with patch("clubos2.investigator.orchestrator.AlertsRepository") as MockAlerts:
        MockAlerts.return_value.get_by_id = AsyncMock(return_value=None)
        result = await run_investigation(InvestigatorInput(
            alert_id="alrt_nonexistent",
            metric_name="streaming_daily_users",
        ))

    assert result.status == "failed"
    assert "not found" in (result.error or "").lower()


@pytest.mark.asyncio
async def test_graph_crash_returns_failed():
    from clubos2.investigator.orchestrator import run_investigation
    from clubos2.investigator.agent_schemas import InvestigatorInput

    with (
        patch("clubos2.investigator.orchestrator.AlertsRepository") as MockAlerts,
        patch("clubos2.investigator.orchestrator.InvestigationRepository") as MockInvRepo,
        patch("clubos2.investigator.orchestrator.AgentMemoryRepository"),
        patch("clubos2.investigator.orchestrator.build_graph") as MockGraph,
        patch("clubos2.investigator.orchestrator.get_checkpointer"),
        patch("clubos2.investigator.orchestrator.get_current_langsmith_trace_url", return_value=None),
    ):
        MockAlerts.return_value.get_by_id = AsyncMock(return_value=_make_alert_mock())
        mock_inv = MagicMock()
        mock_inv.start = AsyncMock(return_value=MagicMock(investigation_id="inv_crash1"))
        mock_inv.fail = AsyncMock()
        MockInvRepo.return_value = mock_inv
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(side_effect=RuntimeError("Simulated crash"))
        MockGraph.return_value = mock_graph

        result = await run_investigation(InvestigatorInput(alert_id="alrt_test", metric_name="streaming_daily_users"))

    assert result.status == "failed"
    assert "Simulated crash" in (result.error or "")


@pytest.mark.asyncio
async def test_timeout_detection():
    """Graph hits max_steps → status='timeout'."""
    from clubos2.investigator.orchestrator import run_investigation
    from clubos2.investigator.agent_schemas import InvestigatorInput
    from langchain_core.messages import AIMessage

    final_msg = AIMessage(content="not parseable json", tool_calls=[])
    # step_count == max_steps signals timeout
    final_state = {"messages": [final_msg], "step_count": 3, "tools_called": [], "reasoning_trace": []}

    with (
        patch("clubos2.investigator.orchestrator.AlertsRepository") as MockAlerts,
        patch("clubos2.investigator.orchestrator.InvestigationRepository") as MockInvRepo,
        patch("clubos2.investigator.orchestrator.AgentMemoryRepository"),
        patch("clubos2.investigator.orchestrator.build_graph") as MockGraph,
        patch("clubos2.investigator.orchestrator.get_checkpointer"),
        patch("clubos2.investigator.orchestrator.get_current_langsmith_trace_url", return_value=None),
    ):
        MockAlerts.return_value.get_by_id = AsyncMock(return_value=_make_alert_mock())
        mock_inv = MagicMock()
        mock_inv.start = AsyncMock(return_value=MagicMock(investigation_id="inv_timeout1"))
        mock_inv.fail = AsyncMock()
        MockInvRepo.return_value = mock_inv
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value=final_state)
        MockGraph.return_value = mock_graph

        result = await run_investigation(InvestigatorInput(
            alert_id="alrt_test",
            metric_name="streaming_daily_users",
            max_steps=3,
        ))

    assert result.status == "timeout"
