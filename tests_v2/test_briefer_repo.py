from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy.orm import sessionmaker

import clubos2.semantic_layer.db as db_mod
from clubos2.agents.scout_schemas import Citation
from clubos2.briefer.repo import BriefingRepository, bootstrap_briefings_db
from clubos2.briefer.schema import BriefingStatus, BriefingType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def test_db_url(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("dbs") / "test_briefings.duckdb"
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
    engine = db_mod.get_engine(test_db_url)
    monkeypatch_module.setattr(db_mod, "_default_engine", engine)
    monkeypatch_module.setattr(db_mod, "_SessionFactory", sessionmaker(bind=engine))


@pytest.fixture
def repo() -> BriefingRepository:
    return BriefingRepository()


def _period():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return now - timedelta(days=30), now


def _citations() -> list[Citation]:
    return [
        Citation(
            claim="Streaming users dropped 12%",
            source="investigations",
            section="evidence",
            quote="cause_hypothesis: app store delays",
        )
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_start_creates_generating_row(repo):
    start, end = _period()
    row = await repo.start(
        briefing_type=BriefingType.MONTHLY_SCHEDULED.value,
        scope_key="monthly:2026-03",
        period_start=start,
        period_end=end,
        triggered_by="test",
    )
    assert row.briefing_id.startswith("brf_")
    assert row.status == BriefingStatus.GENERATING
    assert row.scope_key == "monthly:2026-03"
    assert row.citations == []
    assert row.investigations_referenced == []


async def test_complete_populates_all_fields(repo):
    start, end = _period()
    row = await repo.start(
        briefing_type=BriefingType.AD_HOC_SUMMARY.value,
        scope_key="adhoc:test001",
        period_start=start,
        period_end=end,
        triggered_by="test",
    )

    completed = await repo.complete(
        briefing_id=row.briefing_id,
        executive_summary="Three investigations concluded this month.",
        body_markdown="# Briefing\n\nDetails here.",
        citations=_citations(),
        investigations_referenced=["inv_abc", "inv_def"],
        alerts_referenced=["alrt_xyz"],
        metrics_covered=["streaming_daily_users"],
        total_tokens=1200,
        cost_usd=0.002,
        latency_seconds=3.5,
        trace_url=None,
    )

    assert completed.status == BriefingStatus.COMPLETED
    assert completed.executive_summary == "Three investigations concluded this month."
    assert len(completed.citations) == 1
    assert completed.investigations_referenced == ["inv_abc", "inv_def"]
    assert completed.alerts_referenced == ["alrt_xyz"]
    assert completed.metrics_covered == ["streaming_daily_users"]
    assert completed.total_tokens == 1200
    assert completed.completed_at is not None


async def test_fail_marks_failed(repo):
    start, end = _period()
    row = await repo.start(
        briefing_type=BriefingType.METRIC_FOCUS.value,
        scope_key="metric:net_sales:last_30d",
        period_start=start,
        period_end=end,
        triggered_by="test",
    )

    failed = await repo.fail(
        briefing_id=row.briefing_id,
        error_message="LLM timeout",
        latency_seconds=30.0,
    )

    assert failed.status == BriefingStatus.FAILED
    assert failed.error_message == "LLM timeout"
    assert failed.completed_at is not None


async def test_find_fresh_returns_completed_match(repo):
    start, end = _period()
    row = await repo.start(
        briefing_type=BriefingType.MONTHLY_SCHEDULED.value,
        scope_key="monthly:2026-04",
        period_start=start,
        period_end=end,
        triggered_by="test",
    )
    await repo.complete(
        briefing_id=row.briefing_id,
        executive_summary="April summary.",
        body_markdown="# April",
        citations=[],
        investigations_referenced=[],
        alerts_referenced=[],
        metrics_covered=[],
        total_tokens=None,
        cost_usd=None,
        latency_seconds=2.0,
        trace_url=None,
    )

    found = await repo.find_fresh(scope_key="monthly:2026-04", max_age_days=7)
    assert found is not None
    assert found.briefing_id == row.briefing_id
    assert found.status == BriefingStatus.COMPLETED


async def test_find_fresh_returns_none_for_different_scope(repo):
    found = await repo.find_fresh(scope_key="monthly:2099-01", max_age_days=7)
    assert found is None


async def test_find_fresh_respects_freshness_window(repo):
    """A briefing older than max_age_days must NOT be returned."""
    import sqlalchemy as sa
    from clubos2.briefer.schema import BriefingORM
    from clubos2.semantic_layer.db import get_session

    start, end = _period()
    row = await repo.start(
        briefing_type=BriefingType.MONTHLY_SCHEDULED.value,
        scope_key="monthly:2025-01",
        period_start=start,
        period_end=end,
        triggered_by="test",
    )
    await repo.complete(
        briefing_id=row.briefing_id,
        executive_summary="Old briefing.",
        body_markdown="# Old",
        citations=[],
        investigations_referenced=[],
        alerts_referenced=[],
        metrics_covered=[],
        total_tokens=None,
        cost_usd=None,
        latency_seconds=1.0,
        trace_url=None,
    )

    # Back-date completed_at to 10 days ago so it falls outside a 7-day window
    old_completed_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=10)
    with get_session() as session:
        orm = session.get(BriefingORM, row.briefing_id)
        assert orm is not None
        orm.completed_at = old_completed_at
        session.flush()

    found = await repo.find_fresh(scope_key="monthly:2025-01", max_age_days=7)
    assert found is None


async def test_get_by_id(repo):
    start, end = _period()
    row = await repo.start(
        briefing_type=BriefingType.INCIDENT_RECAP.value,
        scope_key="incident:alrt_test01",
        period_start=start,
        period_end=end,
        triggered_by="test",
    )

    fetched = await repo.get_by_id(row.briefing_id)
    assert fetched is not None
    assert fetched.briefing_id == row.briefing_id


async def test_get_by_id_returns_none_for_missing(repo):
    result = await repo.get_by_id("brf_doesnotexist")
    assert result is None


async def test_list_recent_with_filters(repo):
    # list_recent should return something
    results = await repo.list_recent(limit=50)
    assert isinstance(results, list)
    assert len(results) > 0

    # Filter by type
    monthly = await repo.list_recent(limit=50, briefing_type=BriefingType.MONTHLY_SCHEDULED.value)
    assert all(r.briefing_type == BriefingType.MONTHLY_SCHEDULED for r in monthly)

    # Filter by since — future date should return nothing
    future = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=999)
    none_results = await repo.list_recent(limit=50, since=future)
    assert none_results == []


async def test_concurrent_starts_with_same_scope_key_both_succeed(repo):
    """Both rows succeed — dedup happens at orchestrator level, not DB level."""
    import asyncio
    start, end = _period()

    async def do_start():
        return await repo.start(
            briefing_type=BriefingType.AD_HOC_SUMMARY.value,
            scope_key="adhoc:concurrent_test",
            period_start=start,
            period_end=end,
            triggered_by="test",
        )

    r1, r2 = await asyncio.gather(do_start(), do_start())
    assert r1.briefing_id != r2.briefing_id
    assert r1.scope_key == r2.scope_key == "adhoc:concurrent_test"
