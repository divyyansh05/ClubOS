from __future__ import annotations

from datetime import datetime, timezone, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

import clubos2.semantic_layer.db as db_mod
from clubos2.agents.scout_schemas import Citation
from clubos2.briefer.input_assembly import (
    BriefingSourceMaterial,
    assemble_source_material,
    _compute_aggregates,
    _parse_metric_scope_key,
    _parse_incident_scope_key,
)
from clubos2.briefer.schema import BriefingType
from clubos2.investigator.repo import InvestigationRepository, bootstrap_investigations_db
from clubos2.investigator.schema import InvestigationStatus, Confidence
from clubos2.watchdog.alerts_repo import AlertsRepository, bootstrap_watchdog_alerts_db
from clubos2.watchdog.alerts_schema import AlertSeverity, AlertType, WatchdogAlertCreate
from clubos2.watchdog.memory_repo import AgentMemoryRepository, bootstrap_agent_memory_db


# ---------------------------------------------------------------------------
# Fixtures — isolated DuckDB per module
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def test_db_url(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("dbs") / "test_assembly.duckdb"
    return f"duckdb:///{db_file}"


@pytest.fixture(scope="module")
def monkeypatch_module():
    from _pytest.monkeypatch import MonkeyPatch
    mp = MonkeyPatch()
    yield mp
    mp.undo()


@pytest.fixture(scope="module", autouse=True)
def setup_test_db(test_db_url, monkeypatch_module):
    bootstrap_investigations_db(test_db_url)
    bootstrap_watchdog_alerts_db(test_db_url)
    bootstrap_agent_memory_db(test_db_url)
    engine = db_mod.get_engine(test_db_url)
    monkeypatch_module.setattr(db_mod, "_default_engine", engine)
    monkeypatch_module.setattr(db_mod, "_SessionFactory", sessionmaker(bind=engine))


@pytest.fixture
def inv_repo() -> InvestigationRepository:
    return InvestigationRepository()


@pytest.fixture
def alerts_repo() -> AlertsRepository:
    return AlertsRepository()


@pytest.fixture
def memory_repo() -> AgentMemoryRepository:
    return AgentMemoryRepository()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _uid() -> str:
    return uuid4().hex[:8]


async def _seed_investigation(
    inv_repo: InvestigationRepository,
    metric_name: str,
    alert_id: str,
    confidence: str = "high",
) -> str:
    row = await inv_repo.start(
        alert_id=alert_id,
        metric_name=metric_name,
        triggered_by="test",
    )
    await inv_repo.complete(
        investigation_id=row.investigation_id,
        cause_hypothesis=f"Hypothesis for {metric_name}",
        confidence=confidence,
        evidence_summary="Evidence here.",
        citations=[Citation(claim="x", source="investigations", section=None, quote=None)],
        reasoning_trace=[],
        tools_called=[],
        total_steps=1,
        total_tokens=None,
        cost_usd=None,
        latency_seconds=1.0,
        trace_url=None,
    )
    return row.investigation_id


async def _seed_alert(
    alerts_repo: AlertsRepository,
    metric_name: str,
    severity: AlertSeverity = AlertSeverity.CRITICAL,
) -> str:
    alert_id = f"alrt_{_uid()}"
    await alerts_repo.create(WatchdogAlertCreate(
        alert_id=alert_id,
        metric_name=metric_name,
        alert_type=AlertType.SCORE_JUMP,
        severity=severity,
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
    return alert_id


# ---------------------------------------------------------------------------
# Unit tests — compute_aggregates (pure function)
# ---------------------------------------------------------------------------

async def test_compute_aggregates_counts_correctly(inv_repo):
    """5 investigations, 3 metrics (counts 3/1/1) → persistent=[metric_1]"""
    metric_a = "streaming_daily_users"
    metric_b = "net_sales"
    metric_c = "bounce_rate_web"

    invs = []
    for _ in range(3):
        row = await inv_repo.start(alert_id=f"alrt_{_uid()}", metric_name=metric_a, triggered_by="test")
        await inv_repo.complete(row.investigation_id, "h", "high", "e", [], [], [], 1, None, None, 1.0, None)
        invs.append(row)

    for m in (metric_b, metric_c):
        row = await inv_repo.start(alert_id=f"alrt_{_uid()}", metric_name=m, triggered_by="test")
        await inv_repo.complete(row.investigation_id, "h", "medium", "e", [], [], [], 1, None, None, 1.0, None)
        invs.append(row)

    fetched = await inv_repo.list_recent(limit=10, status=InvestigationStatus.COMPLETED)
    relevant = [i for i in fetched if i.investigation_id in {r.investigation_id for r in invs}]

    aggs = _compute_aggregates(relevant)
    assert aggs["total_investigations"] == 5
    assert aggs["high_confidence_count"] == 3
    assert aggs["medium_confidence_count"] == 2
    assert aggs["low_confidence_count"] == 0
    assert metric_a in aggs["persistent_metrics"]
    assert metric_b not in aggs["persistent_metrics"]
    assert metric_c not in aggs["persistent_metrics"]


# ---------------------------------------------------------------------------
# MONTHLY_SCHEDULED scope
# ---------------------------------------------------------------------------

async def test_monthly_scope_fetches_investigations_alerts_memories(
    inv_repo, alerts_repo, memory_repo
):
    period_start = _now() - timedelta(days=5)
    period_end = _now() + timedelta(hours=1)

    # Seed data inside the period
    await _seed_investigation(inv_repo, "conversion_rate_ecommerce", f"alrt_{_uid()}")
    await _seed_alert(alerts_repo, "conversion_rate_ecommerce")
    await memory_repo.remember(
        agent_name="watchdog",
        memory_type="present_in_top_n",
        subject_key="conversion_rate_ecommerce::present_in_top_n",
    )

    result = await assemble_source_material(
        briefing_type=BriefingType.MONTHLY_SCHEDULED.value,
        scope_key="monthly:2026-07",
        period_start=period_start,
        period_end=period_end,
        investigations_repo=inv_repo,
        alerts_repo=alerts_repo,
        memory_repo=memory_repo,
    )

    assert isinstance(result, BriefingSourceMaterial)
    assert result.total_investigations >= 1
    assert result.briefing_type == BriefingType.MONTHLY_SCHEDULED.value
    assert len(result.investigations) >= 1
    assert len(result.alerts_in_period) >= 1
    assert len(result.memory_entries) >= 1


# ---------------------------------------------------------------------------
# METRIC_FOCUS scope
# ---------------------------------------------------------------------------

async def test_metric_focus_scope_filters_by_metric(inv_repo, alerts_repo, memory_repo):
    target_metric = "fan_app_dau"
    other_metric = "streaming_daily_users"
    alert_id = f"alrt_{_uid()}"

    await _seed_investigation(inv_repo, target_metric, alert_id)
    await _seed_investigation(inv_repo, other_metric, f"alrt_{_uid()}")
    await _seed_alert(alerts_repo, target_metric)

    period_start = _now() - timedelta(days=35)
    period_end = _now() + timedelta(hours=1)

    result = await assemble_source_material(
        briefing_type=BriefingType.METRIC_FOCUS.value,
        scope_key=f"metric:{target_metric}:last_30d",
        period_start=period_start,
        period_end=period_end,
        investigations_repo=inv_repo,
        alerts_repo=alerts_repo,
        memory_repo=memory_repo,
    )

    assert all(i.metric_name == target_metric for i in result.investigations)
    assert all(a.metric_name == target_metric for a in result.alerts_in_period)


# ---------------------------------------------------------------------------
# INCIDENT_RECAP scope
# ---------------------------------------------------------------------------

async def test_incident_recap_fetches_alert_and_linked_investigations(
    inv_repo, alerts_repo, memory_repo
):
    alert_id = f"alrt_{_uid()}"
    other_alert_id = f"alrt_{_uid()}"

    await _seed_alert(alerts_repo, "net_sales")
    await _seed_investigation(inv_repo, "net_sales", alert_id)
    await _seed_investigation(inv_repo, "net_sales", other_alert_id)

    # Seed memory referencing alert_id
    await memory_repo.remember(
        agent_name="watchdog",
        memory_type="present_in_top_n",
        subject_key="net_sales::present_in_top_n",
        subject_metadata={"alert_id": alert_id},
    )

    period_start = _now() - timedelta(days=35)
    period_end = _now() + timedelta(hours=1)

    result = await assemble_source_material(
        briefing_type=BriefingType.INCIDENT_RECAP.value,
        scope_key=f"incident:{alert_id}",
        period_start=period_start,
        period_end=period_end,
        investigations_repo=inv_repo,
        alerts_repo=alerts_repo,
        memory_repo=memory_repo,
    )

    assert all(i.alert_id == alert_id for i in result.investigations)
    assert len(result.investigations) == 1


# ---------------------------------------------------------------------------
# Empty period
# ---------------------------------------------------------------------------

async def test_empty_period_returns_valid_source_material(inv_repo, alerts_repo, memory_repo):
    far_future = _now() + timedelta(days=365)
    far_future_end = far_future + timedelta(days=30)

    result = await assemble_source_material(
        briefing_type=BriefingType.MONTHLY_SCHEDULED.value,
        scope_key="monthly:2099-01",
        period_start=far_future,
        period_end=far_future_end,
        investigations_repo=inv_repo,
        alerts_repo=alerts_repo,
        memory_repo=memory_repo,
    )

    assert result.total_investigations == 0
    assert result.investigations == []
    assert result.alerts_in_period == []
    assert result.memory_entries == []
    assert result.persistent_metrics == []


# ---------------------------------------------------------------------------
# Scope key parsers
# ---------------------------------------------------------------------------

def test_parse_metric_scope_key_valid():
    name, days = _parse_metric_scope_key("metric:streaming_daily_users:last_30d")
    assert name == "streaming_daily_users"
    assert days == 30


def test_parse_metric_scope_key_invalid():
    with pytest.raises(ValueError):
        _parse_metric_scope_key("metric:streaming_daily_users")


def test_parse_incident_scope_key_valid():
    alert_id = _parse_incident_scope_key("incident:alrt_abc123")
    assert alert_id == "alrt_abc123"


def test_parse_incident_scope_key_invalid():
    with pytest.raises(ValueError):
        _parse_incident_scope_key("bad_format")
