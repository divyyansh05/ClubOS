from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

import clubos2.semantic_layer.db as db_mod
from clubos2.agents.scout_schemas import Citation
from clubos2.briefer.agent_schemas import BriefingContent, BriefingInput, BriefingType
from clubos2.briefer.orchestrator import format_source_for_llm, run_briefing
from clubos2.briefer.repo import BriefingRepository, bootstrap_briefings_db
from clubos2.briefer.schema import BriefingStatus
from clubos2.investigator.repo import InvestigationRepository, bootstrap_investigations_db
from clubos2.watchdog.alerts_repo import AlertsRepository, bootstrap_watchdog_alerts_db
from clubos2.watchdog.alerts_schema import AlertSeverity, AlertType, WatchdogAlertCreate
from clubos2.watchdog.memory_repo import AgentMemoryRepository, bootstrap_agent_memory_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def test_db_url(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("dbs") / "test_orchestrator.duckdb"
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
    engine = db_mod.get_engine(test_db_url)
    monkeypatch_module.setattr(db_mod, "_default_engine", engine)
    monkeypatch_module.setattr(db_mod, "_SessionFactory", sessionmaker(bind=engine))


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _uid() -> str:
    return uuid4().hex[:8]


def _briefing_input(
    scope_key: str = "monthly:2026-01",
    briefing_type: BriefingType = BriefingType.MONTHLY_SCHEDULED,
    force_regenerate: bool = False,
    freshness_days: int = 7,
) -> BriefingInput:
    now = _now()
    return BriefingInput(
        briefing_type=briefing_type,
        scope_key=scope_key,
        period_start=now - timedelta(days=30),
        period_end=now,
        triggered_by="test",
        freshness_days=freshness_days,
        force_regenerate=force_regenerate,
    )


def _fake_content() -> BriefingContent:
    return BriefingContent(
        executive_summary="Q1 was stable. No critical incidents were recorded.",
        body_markdown="# Monthly Briefing\n\nNo investigations concluded this period.",
        citations=[Citation(claim="No incidents", source="investigations", section=None, quote=None)],
        investigations_referenced=[],
        alerts_referenced=[],
        metrics_covered=[],
    )


# ---------------------------------------------------------------------------
# format_source_for_llm (pure function)
# ---------------------------------------------------------------------------

def test_format_source_for_llm_empty_period():
    """Empty source material → valid formatted string with zero-count aggregates."""
    from clubos2.briefer.input_assembly import BriefingSourceMaterial
    source = BriefingSourceMaterial(
        period_start=_now() - timedelta(days=30),
        period_end=_now(),
        briefing_type="monthly_scheduled",
        scope_key="monthly:2026-01",
        investigations=[],
        alerts_in_period=[],
        memory_entries=[],
        total_investigations=0,
        high_confidence_count=0,
        medium_confidence_count=0,
        low_confidence_count=0,
        metrics_investigated=[],
        persistent_metrics=[],
    )
    text = format_source_for_llm(source)
    assert "No investigations concluded" in text
    assert "Total investigations: 0" in text
    assert "Briefing Input" in text


# ---------------------------------------------------------------------------
# Dedup cache hit — no LLM call
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cache_hit_returns_cached_briefing_without_llm_call():
    """Pre-populate a fresh briefing → second call returns it as cached."""
    scope_key = f"monthly:cache-hit-{_uid()}"
    repo = BriefingRepository()

    # Create a completed briefing manually
    row = await repo.start(
        briefing_type=BriefingType.MONTHLY_SCHEDULED.value,
        scope_key=scope_key,
        period_start=_now() - timedelta(days=30),
        period_end=_now(),
        triggered_by="test",
        freshness_days=7,
    )
    content = _fake_content()
    await repo.complete(
        briefing_id=row.briefing_id,
        executive_summary=content.executive_summary,
        body_markdown=content.body_markdown,
        citations=content.citations,
        investigations_referenced=content.investigations_referenced,
        alerts_referenced=content.alerts_referenced,
        metrics_covered=content.metrics_covered,
        total_tokens=None,
        cost_usd=None,
        latency_seconds=1.0,
        trace_url=None,
    )

    inp = _briefing_input(scope_key=scope_key)

    llm_call_count = 0

    async def mock_call_llm(*args, **kwargs):
        nonlocal llm_call_count
        llm_call_count += 1
        return _fake_content()

    with patch("clubos2.briefer.orchestrator.call_llm", side_effect=mock_call_llm):
        result = await run_briefing(inp)

    assert result.was_cached is True
    assert result.status == "cached"
    assert result.briefing_id == row.briefing_id
    assert llm_call_count == 0, "LLM must NOT be called on cache hit"


# ---------------------------------------------------------------------------
# Dedup cache miss — briefing older than freshness window
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cache_miss_when_briefing_too_old():
    """Fresh briefing exists but older than freshness_days → LLM called, new briefing generated."""
    scope_key = f"monthly:cache-miss-stale-{_uid()}"
    repo = BriefingRepository()

    row = await repo.start(
        briefing_type=BriefingType.MONTHLY_SCHEDULED.value,
        scope_key=scope_key,
        period_start=_now() - timedelta(days=40),
        period_end=_now() - timedelta(days=10),
        triggered_by="test",
        freshness_days=7,
    )
    # Manually set completed_at to 10 days ago (stale)
    import clubos2.semantic_layer.db as _db
    import sqlalchemy as sa
    from clubos2.briefer.schema import BriefingORM, BriefingStatus as BS
    content = _fake_content()
    stale_time = _now() - timedelta(days=10)
    with _db.get_session() as session:
        orm = session.get(BriefingORM, row.briefing_id)
        orm.status = BS.COMPLETED.value
        orm.executive_summary = content.executive_summary
        orm.body_markdown = content.body_markdown
        orm.citations = json.dumps([c.model_dump() for c in content.citations])
        orm.investigations_referenced = "[]"
        orm.alerts_referenced = "[]"
        orm.metrics_covered = "[]"
        orm.completed_at = stale_time
        session.flush()

    inp = _briefing_input(scope_key=scope_key, freshness_days=7)

    llm_call_count = 0

    async def mock_call_llm(*args, **kwargs):
        nonlocal llm_call_count
        llm_call_count += 1
        return _fake_content()

    with patch("clubos2.briefer.orchestrator.call_llm", side_effect=mock_call_llm):
        result = await run_briefing(inp)

    assert result.was_cached is False
    assert result.status == "completed"
    assert result.briefing_id != row.briefing_id, "New briefing_id must be generated"
    assert llm_call_count == 1


# ---------------------------------------------------------------------------
# force_regenerate bypasses cache
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_force_regenerate_bypasses_cache():
    """force_regenerate=True generates a new briefing even when a fresh cache entry exists."""
    scope_key = f"monthly:force-regen-{_uid()}"
    repo = BriefingRepository()

    row = await repo.start(
        briefing_type=BriefingType.MONTHLY_SCHEDULED.value,
        scope_key=scope_key,
        period_start=_now() - timedelta(days=30),
        period_end=_now(),
        triggered_by="test",
        freshness_days=7,
    )
    content = _fake_content()
    await repo.complete(
        briefing_id=row.briefing_id,
        executive_summary=content.executive_summary,
        body_markdown=content.body_markdown,
        citations=content.citations,
        investigations_referenced=content.investigations_referenced,
        alerts_referenced=content.alerts_referenced,
        metrics_covered=content.metrics_covered,
        total_tokens=None,
        cost_usd=None,
        latency_seconds=1.0,
        trace_url=None,
    )

    inp = _briefing_input(scope_key=scope_key, force_regenerate=True)

    async def mock_call_llm(*args, **kwargs):
        return _fake_content()

    with patch("clubos2.briefer.orchestrator.call_llm", side_effect=mock_call_llm):
        result = await run_briefing(inp)

    assert result.was_cached is False
    assert result.status == "completed"
    assert result.briefing_id != row.briefing_id


# ---------------------------------------------------------------------------
# Empty period — no investigations — briefing still generates
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_empty_period_generates_valid_briefing():
    """No investigations in period → briefing generates with 'no investigations' content."""
    scope_key = f"monthly:empty-period-{_uid()}"
    inp = _briefing_input(scope_key=scope_key)

    async def mock_call_llm(*args, **kwargs):
        return BriefingContent(
            executive_summary="No critical investigations were triggered this month.",
            body_markdown="# Monthly Briefing\n\nNo investigations concluded in this period.",
            citations=[],
            investigations_referenced=[],
            alerts_referenced=[],
            metrics_covered=[],
        )

    with patch("clubos2.briefer.orchestrator.call_llm", side_effect=mock_call_llm):
        result = await run_briefing(inp)

    assert result.status == "completed"
    assert result.was_cached is False
    assert result.content is not None
    assert "No" in result.content.executive_summary

    # Row persisted
    repo = BriefingRepository()
    persisted = await repo.get_by_id(result.briefing_id)
    assert persisted is not None
    assert persisted.status == BriefingStatus.COMPLETED.value


# ---------------------------------------------------------------------------
# LLM call failure → status='failed', row created and marked failed
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_llm_failure_produces_failed_result():
    """If LLM raises, result has status='failed' and error is captured."""
    scope_key = f"monthly:llm-fail-{_uid()}"
    inp = _briefing_input(scope_key=scope_key)

    async def mock_call_llm(*args, **kwargs):
        raise RuntimeError("OpenAI timeout")

    with patch("clubos2.briefer.orchestrator.call_llm", side_effect=mock_call_llm):
        result = await run_briefing(inp)

    assert result.status == "failed"
    assert result.content is None
    assert "OpenAI timeout" in (result.error or "")

    # Briefing row must exist and be marked failed
    repo = BriefingRepository()
    persisted = await repo.get_by_id(result.briefing_id)
    assert persisted is not None
    assert persisted.status == BriefingStatus.FAILED.value


# ---------------------------------------------------------------------------
# Source assembly failure → status='failed', NO row created
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_source_assembly_failure_no_row_created():
    """If source assembly raises, result is failed and NO briefings row is inserted."""
    scope_key = f"monthly:assembly-fail-{_uid()}"
    inp = _briefing_input(scope_key=scope_key)

    async def mock_assemble(*args, **kwargs):
        raise RuntimeError("DB unreachable")

    with patch("clubos2.briefer.orchestrator.assemble_source_material", side_effect=mock_assemble):
        result = await run_briefing(inp)

    assert result.status == "failed"
    assert result.content is None
    assert "Source assembly failed" in (result.error or "")

    # The briefing_id is a generated fallback — row should NOT exist
    repo = BriefingRepository()
    persisted = await repo.get_by_id(result.briefing_id)
    assert persisted is None
