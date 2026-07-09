from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from uuid import uuid4

import sqlalchemy as sa

from clubos2.semantic_layer.db import get_session, get_engine
from clubos2.agents.scout_schemas import Citation
from clubos2.briefer.schema import BriefingORM, BriefingRead, BriefingStatus


def bootstrap_briefings_db(database_url: str | None = None) -> None:
    """Run briefings migration idempotently."""
    migration = Path(__file__).parent / "migrations" / "001_create_briefings.sql"
    sql = migration.read_text()
    engine = get_engine(database_url)
    with engine.begin() as conn:
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            conn.execute(sa.text(stmt))


def _generate_briefing_id() -> str:
    return f"brf_{uuid4().hex[:16]}"


class BriefingRepository:
    def _to_read(self, orm: BriefingORM) -> BriefingRead:
        return BriefingRead.model_validate(orm)

    # ------------------------------------------------------------------
    # start
    # ------------------------------------------------------------------

    def _start_sync(
        self,
        briefing_type: str,
        scope_key: str,
        period_start: datetime,
        period_end: datetime,
        triggered_by: str,
        freshness_days: int = 7,
    ) -> BriefingRead:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        orm = BriefingORM(
            briefing_id=_generate_briefing_id(),
            briefing_type=briefing_type,
            scope_key=scope_key,
            period_start=period_start,
            period_end=period_end,
            triggered_by=triggered_by,
            status=BriefingStatus.GENERATING.value,
            citations="[]",
            investigations_referenced="[]",
            alerts_referenced="[]",
            metrics_covered="[]",
            freshness_days=freshness_days,
            started_at=now,
        )
        with get_session() as session:
            session.add(orm)
            session.flush()
            result = self._to_read(orm)
        return result

    async def start(
        self,
        briefing_type: str,
        scope_key: str,
        period_start: datetime,
        period_end: datetime,
        triggered_by: str,
        freshness_days: int = 7,
    ) -> BriefingRead:
        return await asyncio.to_thread(
            self._start_sync,
            briefing_type, scope_key, period_start, period_end, triggered_by, freshness_days,
        )

    # ------------------------------------------------------------------
    # complete
    # ------------------------------------------------------------------

    def _complete_sync(
        self,
        briefing_id: str,
        executive_summary: str,
        body_markdown: str,
        citations: list[Citation],
        investigations_referenced: list[str],
        alerts_referenced: list[str],
        metrics_covered: list[str],
        total_tokens: int | None,
        cost_usd: float | None,
        latency_seconds: float,
        trace_url: str | None,
    ) -> BriefingRead:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        with get_session() as session:
            orm = session.get(BriefingORM, briefing_id)
            if orm is None:
                raise ValueError(f"Briefing {briefing_id} not found")
            orm.status = BriefingStatus.COMPLETED.value
            orm.executive_summary = executive_summary
            orm.body_markdown = body_markdown
            orm.citations = json.dumps([c.model_dump() for c in citations])
            orm.investigations_referenced = json.dumps(investigations_referenced)
            orm.alerts_referenced = json.dumps(alerts_referenced)
            orm.metrics_covered = json.dumps(metrics_covered)
            orm.total_tokens = total_tokens
            orm.cost_usd = cost_usd
            orm.latency_seconds = latency_seconds
            orm.trace_url = trace_url
            orm.completed_at = now
            session.flush()
            result = self._to_read(orm)
        return result

    async def complete(
        self,
        briefing_id: str,
        executive_summary: str,
        body_markdown: str,
        citations: list[Citation],
        investigations_referenced: list[str],
        alerts_referenced: list[str],
        metrics_covered: list[str],
        total_tokens: int | None,
        cost_usd: float | None,
        latency_seconds: float,
        trace_url: str | None,
    ) -> BriefingRead:
        return await asyncio.to_thread(
            self._complete_sync,
            briefing_id, executive_summary, body_markdown, citations,
            investigations_referenced, alerts_referenced, metrics_covered,
            total_tokens, cost_usd, latency_seconds, trace_url,
        )

    # ------------------------------------------------------------------
    # fail
    # ------------------------------------------------------------------

    def _fail_sync(
        self,
        briefing_id: str,
        error_message: str,
        latency_seconds: float,
    ) -> BriefingRead:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        with get_session() as session:
            orm = session.get(BriefingORM, briefing_id)
            if orm is None:
                raise ValueError(f"Briefing {briefing_id} not found")
            orm.status = BriefingStatus.FAILED.value
            orm.error_message = error_message
            orm.latency_seconds = latency_seconds
            orm.completed_at = now
            session.flush()
            result = self._to_read(orm)
        return result

    async def fail(
        self,
        briefing_id: str,
        error_message: str,
        latency_seconds: float,
    ) -> BriefingRead:
        return await asyncio.to_thread(self._fail_sync, briefing_id, error_message, latency_seconds)

    # ------------------------------------------------------------------
    # find_fresh — THE DEDUP CACHE PRIMITIVE
    # ------------------------------------------------------------------

    def _find_fresh_sync(self, scope_key: str, max_age_days: int = 7) -> BriefingRead | None:
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=max_age_days)
        with get_session() as session:
            stmt = (
                sa.select(BriefingORM)
                .where(BriefingORM.scope_key == scope_key)
                .where(BriefingORM.status == BriefingStatus.COMPLETED.value)
                .where(BriefingORM.completed_at >= cutoff)
                .order_by(BriefingORM.completed_at.desc())
                .limit(1)
            )
            orm = session.execute(stmt).scalars().first()
            return self._to_read(orm) if orm else None

    async def find_fresh(self, scope_key: str, max_age_days: int = 7) -> BriefingRead | None:
        return await asyncio.to_thread(self._find_fresh_sync, scope_key, max_age_days)

    # ------------------------------------------------------------------
    # get_by_id
    # ------------------------------------------------------------------

    def _get_by_id_sync(self, briefing_id: str) -> BriefingRead | None:
        with get_session() as session:
            orm = session.get(BriefingORM, briefing_id)
            return self._to_read(orm) if orm else None

    async def get_by_id(self, briefing_id: str) -> BriefingRead | None:
        return await asyncio.to_thread(self._get_by_id_sync, briefing_id)

    # ------------------------------------------------------------------
    # list_recent
    # ------------------------------------------------------------------

    def _list_recent_sync(
        self,
        limit: int = 20,
        briefing_type: str | None = None,
        since: datetime | None = None,
    ) -> list[BriefingRead]:
        with get_session() as session:
            stmt = (
                sa.select(BriefingORM)
                .order_by(BriefingORM.started_at.desc())
                .limit(limit)
            )
            if briefing_type:
                stmt = stmt.where(BriefingORM.briefing_type == briefing_type)
            if since:
                stmt = stmt.where(BriefingORM.started_at >= since)
            rows = session.execute(stmt).scalars().all()
            return [self._to_read(r) for r in rows]

    async def list_recent(
        self,
        limit: int = 20,
        briefing_type: str | None = None,
        since: datetime | None = None,
    ) -> list[BriefingRead]:
        return await asyncio.to_thread(self._list_recent_sync, limit, briefing_type, since)
