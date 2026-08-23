from __future__ import annotations

from datetime import datetime, timezone, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

import clubos2.semantic_layer.db as db_mod
from clubos2.agents.scout_schemas import Citation
from clubos2.investigator.repo import InvestigationRepository, bootstrap_investigations_db
from clubos2.investigator.schema import InvestigationStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def test_db_url(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("dbs") / "test_investigations.duckdb"
    return f"duckdb:///{db_file}"


@pytest.fixture(scope="module")
def monkeypatch_module():
    """A module-scoped monkeypatch fixture."""
    from _pytest.monkeypatch import MonkeyPatch
    mp = MonkeyPatch()
    yield mp
    mp.undo()


@pytest.fixture(scope="module", autouse=True)
def setup_test_db(test_db_url, monkeypatch_module):
    """Bootstrap the test DB and redirect the module-level session factory."""
    bootstrap_investigations_db(test_db_url)
    engine = db_mod.get_engine(test_db_url)
    monkeypatch_module.setattr(db_mod, "_default_engine", engine)
    monkeypatch_module.setattr(db_mod, "_SessionFactory", sessionmaker(bind=engine))


@pytest.fixture
def repo() -> InvestigationRepository:
    return InvestigationRepository()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_citations() -> list[Citation]:
    return [
        Citation(
            claim="Revenue dropped 15% MoM",
            source="DATA/gold_snapshots/gold_priority_board.csv",
            section="monthly_summary",
            quote="total_revenue: 850000 vs prior 1000000",
        )
    ]


def _make_reasoning_trace() -> list[dict]:
    return [
        {
            "step_number": 1,
            "thought": "Need to check metric definition first",
            "action": "get_metric_definition",
            "action_input": {"metric_name": "total_revenue"},
            "observation": "total_revenue is sum of all membership fees",
        }
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_start_creates_running_row(repo):
    """start() creates a row with status='running' and started_at populated."""
    alert_id = f"alert_{uuid4().hex[:16]}"

    result = await repo.start(
        alert_id=alert_id,
        metric_name="total_revenue",
        triggered_by="watchdog",
    )

    assert result.investigation_id.startswith("inv_")
    assert result.alert_id == alert_id
    assert result.metric_name == "total_revenue"
    assert result.triggered_by == "watchdog"
    assert result.status == InvestigationStatus.RUNNING
    assert isinstance(result.started_at, datetime)
    assert result.completed_at is None
    assert result.citations == []
    assert result.reasoning_trace == []
    assert result.tools_called == []


async def test_complete_updates_row(repo):
    """start() then complete() sets status='completed' and all result fields."""
    alert_id = f"alert_{uuid4().hex[:16]}"

    started = await repo.start(
        alert_id=alert_id,
        metric_name="churn_rate",
        triggered_by="watchdog",
    )

    citations = _make_citations()
    reasoning = _make_reasoning_trace()
    tools = ["get_metric_definition", "query_metrics"]

    completed = await repo.complete(
        investigation_id=started.investigation_id,
        cause_hypothesis="Churn spiked due to price increase in Q4.",
        confidence="high",
        evidence_summary="- Revenue down 15%\n- 3 alerts in last 7 days",
        citations=citations,
        reasoning_trace=reasoning,
        tools_called=tools,
        total_steps=2,
        total_tokens=1500,
        cost_usd=0.003,
        latency_seconds=4.2,
        trace_url="https://traces.example.com/inv_abc",
    )

    assert completed.investigation_id == started.investigation_id
    assert completed.status == InvestigationStatus.COMPLETED
    assert completed.cause_hypothesis == "Churn spiked due to price increase in Q4."
    assert completed.confidence.value == "high"
    assert completed.evidence_summary == "- Revenue down 15%\n- 3 alerts in last 7 days"
    assert len(completed.citations) == 1
    assert completed.citations[0].claim == "Revenue dropped 15% MoM"
    assert completed.reasoning_trace == reasoning
    assert completed.tools_called == tools
    assert completed.total_steps == 2
    assert completed.total_tokens == 1500
    assert completed.cost_usd == pytest.approx(0.003)
    assert completed.latency_seconds == pytest.approx(4.2)
    assert completed.trace_url == "https://traces.example.com/inv_abc"
    assert completed.completed_at is not None
    assert isinstance(completed.completed_at, datetime)


async def test_fail_marks_failed(repo):
    """start() then fail() sets status='failed' and error_message."""
    alert_id = f"alert_{uuid4().hex[:16]}"

    started = await repo.start(
        alert_id=alert_id,
        metric_name="membership_count",
        triggered_by="manual",
    )

    failed = await repo.fail(
        investigation_id=started.investigation_id,
        error_message="Tool query_metrics timed out after 30s",
        latency_seconds=30.1,
        partial_reasoning_trace=[{"step_number": 1, "thought": "started", "action": "query_metrics", "action_input": {}, "observation": "timeout"}],
    )

    assert failed.status == InvestigationStatus.FAILED
    assert failed.error_message == "Tool query_metrics timed out after 30s"
    assert failed.latency_seconds == pytest.approx(30.1)
    assert failed.completed_at is not None
    assert len(failed.reasoning_trace) == 1


async def test_get_by_alert_sorted(repo):
    """get_by_alert() returns both investigations for an alert, most recent first."""
    alert_id = f"alert_{uuid4().hex[:16]}"

    inv1 = await repo.start(alert_id=alert_id, metric_name="total_revenue", triggered_by="watchdog")
    inv2 = await repo.start(alert_id=alert_id, metric_name="total_revenue", triggered_by="manual")

    results = await repo.get_by_alert(alert_id)

    assert len(results) == 2
    # Most recent first (inv2 started after inv1)
    assert results[0].investigation_id == inv2.investigation_id
    assert results[1].investigation_id == inv1.investigation_id


async def test_list_recent_filters(repo):
    """list_recent() with status/metric_name/since filters returns correct subset."""
    unique_metric = f"metric_{uuid4().hex[:8]}"
    alert_id = f"alert_{uuid4().hex[:16]}"

    # Create 2 investigations for our unique metric
    inv_a = await repo.start(alert_id=alert_id, metric_name=unique_metric, triggered_by="watchdog")
    inv_b = await repo.start(alert_id=alert_id, metric_name=unique_metric, triggered_by="manual")

    # Complete one of them
    await repo.complete(
        investigation_id=inv_a.investigation_id,
        cause_hypothesis="Test hypothesis",
        confidence="low",
        evidence_summary="- test",
        citations=[],
        reasoning_trace=[],
        tools_called=[],
        total_steps=0,
        total_tokens=None,
        cost_usd=None,
        latency_seconds=1.0,
        trace_url=None,
    )

    # Filter by metric_name
    by_metric = await repo.list_recent(metric_name=unique_metric)
    assert len(by_metric) == 2
    assert all(r.metric_name == unique_metric for r in by_metric)

    # Filter by status=running (only inv_b should be running)
    by_status = await repo.list_recent(metric_name=unique_metric, status=InvestigationStatus.RUNNING)
    assert len(by_status) == 1
    assert by_status[0].investigation_id == inv_b.investigation_id

    # Filter by since (far future — should return nothing)
    future = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
    by_since = await repo.list_recent(metric_name=unique_metric, since=future)
    assert len(by_since) == 0


async def test_complete_already_completed_raises(repo):
    """Calling complete() on an already-completed investigation raises ValueError."""
    alert_id = f"alert_{uuid4().hex[:16]}"

    started = await repo.start(alert_id=alert_id, metric_name="churn_rate", triggered_by="watchdog")

    await repo.complete(
        investigation_id=started.investigation_id,
        cause_hypothesis="First completion",
        confidence="medium",
        evidence_summary="- evidence",
        citations=[],
        reasoning_trace=[],
        tools_called=[],
        total_steps=1,
        total_tokens=None,
        cost_usd=None,
        latency_seconds=2.0,
        trace_url=None,
    )

    with pytest.raises(ValueError, match="Cannot complete investigation in status"):
        await repo.complete(
            investigation_id=started.investigation_id,
            cause_hypothesis="Second completion attempt",
            confidence="high",
            evidence_summary="- more evidence",
            citations=[],
            reasoning_trace=[],
            tools_called=[],
            total_steps=2,
            total_tokens=None,
            cost_usd=None,
            latency_seconds=3.0,
            trace_url=None,
        )


async def test_citations_round_trip(repo):
    """Citations serialise to JSON and deserialise back to Citation objects correctly."""
    alert_id = f"alert_{uuid4().hex[:16]}"

    started = await repo.start(alert_id=alert_id, metric_name="total_revenue", triggered_by="watchdog")

    citations = [
        Citation(
            claim="Revenue fell 20%",
            source="DATA/gold_snapshots/gold_priority_board.csv",
            section="monthly",
            quote="total_revenue: 800000",
        ),
        Citation(
            claim="No peers saw similar drop",
            source="DATA/gold_snapshots/gold_peer_benchmark.csv",
            section=None,
            quote=None,
        ),
    ]

    await repo.complete(
        investigation_id=started.investigation_id,
        cause_hypothesis="Internal pricing issue, not industry-wide.",
        confidence="high",
        evidence_summary="- Revenue -20%\n- Peers stable",
        citations=citations,
        reasoning_trace=[],
        tools_called=["get_peer_benchmark"],
        total_steps=3,
        total_tokens=2000,
        cost_usd=0.005,
        latency_seconds=6.0,
        trace_url=None,
    )

    fetched = await repo.get_by_id(started.investigation_id)

    assert fetched is not None
    assert len(fetched.citations) == 2
    assert fetched.citations[0].claim == "Revenue fell 20%"
    assert fetched.citations[0].source == "DATA/gold_snapshots/gold_priority_board.csv"
    assert fetched.citations[0].section == "monthly"
    assert fetched.citations[0].quote == "total_revenue: 800000"
    assert fetched.citations[1].claim == "No peers saw similar drop"
    assert fetched.citations[1].section is None
    assert fetched.citations[1].quote is None
