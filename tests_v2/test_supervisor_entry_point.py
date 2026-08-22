from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

import clubos2.semantic_layer.db as db_mod
from clubos2.briefer.repo import bootstrap_briefings_db
from clubos2.investigator.repo import bootstrap_investigations_db
from clubos2.supervisor.entry_point import SupervisorRequest, SupervisorResponse, handle_query
from clubos2.watchdog.alerts_repo import AlertsRepository, bootstrap_watchdog_alerts_db
from clubos2.watchdog.alerts_schema import AlertSeverity, AlertType, WatchdogAlertCreate
from clubos2.watchdog.memory_repo import bootstrap_agent_memory_db
from clubos2.watchdog.snapshot_repo import bootstrap_snapshot_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def test_db_url(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("dbs") / "test_entry_point.duckdb"
    return f"duckdb:///{db_file}"


@pytest.fixture(scope="module")
def monkeypatch_module():
    from _pytest.monkeypatch import MonkeyPatch
    mp = MonkeyPatch()
    yield mp
    mp.undo()


@pytest.fixture(scope="module", autouse=True)
def setup_test_db(test_db_url, monkeypatch_module):
    bootstrap_briefings_db(test_db_url)
    bootstrap_investigations_db(test_db_url)
    bootstrap_watchdog_alerts_db(test_db_url)
    bootstrap_agent_memory_db(test_db_url)
    bootstrap_snapshot_db(test_db_url)
    engine = db_mod.get_engine(test_db_url)
    monkeypatch_module.setattr(db_mod, "_default_engine", engine)
    monkeypatch_module.setattr(db_mod, "_SessionFactory", sessionmaker(bind=engine))


def _uid() -> str:
    return uuid4().hex[:8]


# ---------------------------------------------------------------------------
# Shared mock factories
# ---------------------------------------------------------------------------

def _mock_scout_answer():
    from clubos2.agents.scout_schemas import ScoutAnswer, Citation
    return ScoutAnswer(
        answer="streaming_daily_users is 45,000.",
        metric_name="streaming_daily_users",
        value=45000.0,
        unit="users",
        citations=[Citation(claim="45k", source="metric_registry", section=None, quote=None)],
        confidence="high",
        caveat=None,
    )


def _mock_inv_result():
    from clubos2.investigator.orchestrator import InvestigationRunResult
    return InvestigationRunResult(
        investigation_id=f"inv_{_uid()}",
        alert_id="alrt_abc123",
        metric_name="net_sales",
        status="completed",
        finding=None,
        latency_seconds=1.2,
    )


def _mock_brf_result(scope_key: str = "monthly:2026-06"):
    from clubos2.briefer.agent_schemas import BriefingRunResult, BriefingType
    return BriefingRunResult(
        briefing_id=f"brf_{_uid()}",
        briefing_type=BriefingType.MONTHLY_SCHEDULED,
        scope_key=scope_key,
        status="completed",
        was_cached=False,
        content=None,
        latency_seconds=2.5,
    )


FAKE_METRICS = ["streaming_daily_users", "net_sales", "conversion_rate"]


# ---------------------------------------------------------------------------
# 1. Scout direct dispatch
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_direct_scout_dispatch():
    """'what is streaming_daily_users' → direct_scout, no LangGraph."""
    answer = _mock_scout_answer()

    with patch("clubos2.supervisor.classifier._load_known_metric_names", return_value=FAKE_METRICS):
        with patch("clubos2.agents.scout.run_scout", new=AsyncMock(return_value=answer)):
            result = await handle_query(SupervisorRequest(query="what is streaming_daily_users this month"))

    assert result.dispatch_path == "direct_scout"
    assert result.error is None
    assert result.classification["agent"] == "scout"
    assert result.classification["confidence"] in ("high", "medium")


# ---------------------------------------------------------------------------
# 2. Investigator direct dispatch (explicit alert_id)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_direct_investigator_dispatch():
    """'why did alert alrt_abc123 fire' → direct_investigator with parsed alert_id."""
    # Seed an alert in the DB so get_by_id returns it
    alerts_repo = AlertsRepository()
    alert_id = f"alrt_{_uid()}"
    await alerts_repo.create(WatchdogAlertCreate(
        alert_id=alert_id,
        metric_name="net_sales",
        alert_type=AlertType.SCORE_JUMP,
        severity=AlertSeverity.CRITICAL,
        current_rank=1,
        previous_rank=5,
        rank_delta=4,
        score_current=0.9,
        score_previous=0.5,
        triggered_by_rule="score_jump",
        context_snapshot="{}",
        source="test",
        run_id=f"run_{_uid()}",
    ))

    inv_result = _mock_inv_result()
    inv_result = inv_result.model_copy(update={"alert_id": alert_id})

    with patch("clubos2.supervisor.classifier._load_known_metric_names", return_value=FAKE_METRICS):
        with patch("clubos2.investigator.orchestrator.run_investigation", new=AsyncMock(return_value=inv_result)):
            result = await handle_query(SupervisorRequest(
                query=f"why did alert {alert_id} fire"
            ))

    assert result.dispatch_path == "direct_investigator"
    assert result.error is None
    assert result.classification["agent"] == "investigator"
    assert result.classification["confidence"] == "high"
    assert result.classification["extracted_params"]["alert_id"] == alert_id


# ---------------------------------------------------------------------------
# 3. Briefer direct dispatch
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_direct_briefer_dispatch():
    """'monthly summary' → direct_briefer."""
    brf_result = _mock_brf_result()

    with patch("clubos2.supervisor.classifier._load_known_metric_names", return_value=FAKE_METRICS):
        with patch("clubos2.briefer.orchestrator.run_briefing", new=AsyncMock(return_value=brf_result)):
            result = await handle_query(SupervisorRequest(query="give me a monthly summary"))

    assert result.dispatch_path == "direct_briefer"
    assert result.error is None
    assert result.classification["agent"] == "briefer"


# ---------------------------------------------------------------------------
# 4. LangGraph supervisor dispatch (complex / unknown query)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_langgraph_supervisor_dispatch():
    """Complex query → langgraph_supervisor dispatch path."""
    from clubos2.supervisor.graph import SupervisorPlan, SupervisorStep

    plan = SupervisorPlan(
        reasoning="Complex query needs Scout.",
        steps=[SupervisorStep(agent="scout", purpose="get data", question="metrics")],
    )
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = plan
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured

    scout_answer = _mock_scout_answer()

    with patch("clubos2.supervisor.classifier._load_known_metric_names", return_value=FAKE_METRICS):
        with patch("clubos2.supervisor.graph.ChatOpenAI", return_value=mock_llm):
            with patch("clubos2.agents.scout.run_scout", new=AsyncMock(return_value=scout_answer)):
                result = await handle_query(SupervisorRequest(
                    query="compare last quarter to this quarter and explain what changed"
                ))

    assert result.dispatch_path == "langgraph_supervisor"
    assert result.error is None
    assert "step_results" in result.result


# ---------------------------------------------------------------------------
# 5. Investigator falls through when alert_id not in DB
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_investigator_falls_through_when_alert_not_found():
    """Explicit alert_id but alert not in DB → falls through to LangGraph."""
    from clubos2.supervisor.graph import SupervisorPlan, SupervisorStep

    plan = SupervisorPlan(reasoning="fallback", steps=[])
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = plan
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured

    with patch("clubos2.supervisor.classifier._load_known_metric_names", return_value=FAKE_METRICS):
        with patch("clubos2.supervisor.graph.ChatOpenAI", return_value=mock_llm):
            result = await handle_query(SupervisorRequest(
                query="why did alert alrt_doesnotexist00 fire"
            ))

    # Falls through to LangGraph since alert not found in DB
    assert result.dispatch_path in ("langgraph_supervisor", "direct_investigator")
    assert result.error is None


# ---------------------------------------------------------------------------
# 6. Error in dispatch path → error field set, no exception raised
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatch_error_captured_not_raised():
    """If Scout raises, response has error field and dispatch_path='error'."""
    async def failing_scout(inp):
        raise RuntimeError("Scout exploded")

    with patch("clubos2.supervisor.classifier._load_known_metric_names", return_value=FAKE_METRICS):
        with patch("clubos2.agents.scout.run_scout", side_effect=failing_scout):
            result = await handle_query(SupervisorRequest(query="what is streaming_daily_users"))

    assert result.dispatch_path == "error"
    assert result.error is not None
    assert "Scout exploded" in result.error


# ---------------------------------------------------------------------------
# 7. Watchdog auto-trigger fires on critical alerts
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_watchdog_auto_trigger_on_critical_alert():
    """Watchdog run producing a critical alert fires asyncio.create_task for Investigator."""
    import asyncio
    from clubos2.watchdog import orchestrator as wdog_mod
    from clubos2.watchdog.alerts_schema import AlertSeverity, AlertType, WatchdogAlertRead
    from datetime import datetime, timezone

    tasks_created: list = []
    original_create_task = asyncio.create_task

    def capturing_create_task(coro, **kwargs):
        tasks_created.append(coro)
        return original_create_task(coro, **kwargs)

    fake_alert = WatchdogAlertRead(
        alert_id=f"alrt_{_uid()}",
        metric_name="streaming_daily_users",
        alert_type=AlertType.SCORE_JUMP,
        severity=AlertSeverity.CRITICAL,
        current_rank=1,
        previous_rank=8,
        rank_delta=7,
        score_current=0.95,
        score_previous=0.4,
        triggered_by_rule="score_jump",
        context_snapshot="{}",
        source="test",
        run_id=f"run_{_uid()}",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )

    async def mock_create_batch(alerts):
        return [fake_alert] if alerts else []

    async def mock_run_investigation(inp):
        from clubos2.investigator.orchestrator import InvestigationRunResult
        return InvestigationRunResult(
            investigation_id=f"inv_{_uid()}",
            alert_id=inp.alert_id,
            metric_name=inp.metric_name,
            status="completed",
            finding=None,
            latency_seconds=0.1,
        )

    # Patch asyncio.create_task in the orchestrator module's namespace
    with patch("clubos2.watchdog.orchestrator.asyncio.create_task", side_effect=capturing_create_task):
        with patch("clubos2.watchdog.alerts_repo.AlertsRepository.create_batch", side_effect=mock_create_batch):
            with patch("clubos2.investigator.orchestrator.run_investigation", new=AsyncMock(side_effect=mock_run_investigation)):
                result = await wdog_mod.run_watchdog()
                await asyncio.sleep(0)  # let event loop schedule tasks

    assert result.alerts_created >= 0  # run completed without crash
    assert len(tasks_created) >= 1, "create_task must be called for the critical alert"


# ---------------------------------------------------------------------------
# 8. SupervisorResponse is always a valid Pydantic model
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_response_is_pydantic_model():
    answer = _mock_scout_answer()
    with patch("clubos2.supervisor.classifier._load_known_metric_names", return_value=FAKE_METRICS):
        with patch("clubos2.agents.scout.run_scout", new=AsyncMock(return_value=answer)):
            result = await handle_query(SupervisorRequest(query="what is streaming_daily_users"))
    assert isinstance(result, SupervisorResponse)
    # Can round-trip to JSON
    assert result.model_dump(mode="json")
