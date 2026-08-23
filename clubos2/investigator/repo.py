from __future__ import annotations
import asyncio
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from uuid import uuid4

import sqlalchemy as sa

from clubos2.semantic_layer.db import get_session, get_engine
from clubos2.agents.scout_schemas import Citation
from clubos2.investigator.schema import (
    Confidence,
    InvestigationORM,
    InvestigationRead,
    InvestigationStatus,
)


def bootstrap_investigations_db(database_url: str | None = None) -> None:
    """Run migration idempotently."""
    migration = Path(__file__).parent / "migrations" / "001_create_investigations.sql"
    sql = migration.read_text()
    engine = get_engine(database_url)
    with engine.begin() as conn:
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            conn.execute(sa.text(stmt))


def _generate_investigation_id() -> str:
    return f"inv_{uuid4().hex[:16]}"


class InvestigationRepository:
    def _to_read(self, orm: InvestigationORM) -> InvestigationRead:
        return InvestigationRead.model_validate(orm)

    def _start_sync(self, alert_id: str, metric_name: str, triggered_by: str) -> InvestigationRead:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        orm = InvestigationORM(
            investigation_id=_generate_investigation_id(),
            alert_id=alert_id,
            metric_name=metric_name,
            triggered_by=triggered_by,
            status=InvestigationStatus.RUNNING.value,
            citations="[]",
            started_at=now,
        )
        with get_session() as session:
            session.add(orm)
            session.flush()
            result = self._to_read(orm)
        return result

    async def start(self, alert_id: str, metric_name: str, triggered_by: str) -> InvestigationRead:
        return await asyncio.to_thread(self._start_sync, alert_id, metric_name, triggered_by)

    def _complete_sync(
        self,
        investigation_id: str,
        cause_hypothesis: str,
        confidence: str,
        evidence_summary: str,
        citations: list[Citation],
        reasoning_trace: list[dict],
        tools_called: list[str],
        total_steps: int,
        total_tokens: int | None,
        cost_usd: float | None,
        latency_seconds: float,
        trace_url: str | None,
    ) -> InvestigationRead:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        with get_session() as session:
            orm = session.get(InvestigationORM, investigation_id)
            if orm is None:
                raise ValueError(f"Investigation {investigation_id} not found")
            if orm.status != InvestigationStatus.RUNNING.value:
                raise ValueError(f"Cannot complete investigation in status '{orm.status}'")
            orm.status = InvestigationStatus.COMPLETED.value
            orm.cause_hypothesis = cause_hypothesis
            orm.confidence = confidence
            orm.evidence_summary = evidence_summary
            orm.citations = json.dumps([c.model_dump() for c in citations])
            orm.reasoning_trace = json.dumps(reasoning_trace)
            orm.tools_called = json.dumps(tools_called)
            orm.total_steps = total_steps
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
        investigation_id: str,
        cause_hypothesis: str,
        confidence: str,
        evidence_summary: str,
        citations: list[Citation],
        reasoning_trace: list[dict],
        tools_called: list[str],
        total_steps: int,
        total_tokens: int | None,
        cost_usd: float | None,
        latency_seconds: float,
        trace_url: str | None,
    ) -> InvestigationRead:
        return await asyncio.to_thread(
            self._complete_sync,
            investigation_id, cause_hypothesis, confidence, evidence_summary,
            citations, reasoning_trace, tools_called, total_steps, total_tokens,
            cost_usd, latency_seconds, trace_url,
        )

    def _fail_sync(
        self,
        investigation_id: str,
        error_message: str,
        latency_seconds: float,
        partial_reasoning_trace: list[dict] | None = None,
    ) -> InvestigationRead:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        with get_session() as session:
            orm = session.get(InvestigationORM, investigation_id)
            if orm is None:
                raise ValueError(f"Investigation {investigation_id} not found")
            orm.status = InvestigationStatus.FAILED.value
            orm.error_message = error_message
            orm.latency_seconds = latency_seconds
            orm.completed_at = now
            if partial_reasoning_trace:
                orm.reasoning_trace = json.dumps(partial_reasoning_trace)
            session.flush()
            result = self._to_read(orm)
        return result

    async def fail(
        self,
        investigation_id: str,
        error_message: str,
        latency_seconds: float,
        partial_reasoning_trace: list[dict] | None = None,
    ) -> InvestigationRead:
        return await asyncio.to_thread(
            self._fail_sync, investigation_id, error_message, latency_seconds, partial_reasoning_trace
        )

    def _get_by_id_sync(self, investigation_id: str) -> InvestigationRead | None:
        with get_session() as session:
            orm = session.get(InvestigationORM, investigation_id)
            return self._to_read(orm) if orm else None

    async def get_by_id(self, investigation_id: str) -> InvestigationRead | None:
        return await asyncio.to_thread(self._get_by_id_sync, investigation_id)

    def _get_by_alert_sync(self, alert_id: str) -> list[InvestigationRead]:
        with get_session() as session:
            stmt = (
                sa.select(InvestigationORM)
                .where(InvestigationORM.alert_id == alert_id)
                .order_by(InvestigationORM.started_at.desc())
            )
            rows = session.execute(stmt).scalars().all()
            return [self._to_read(r) for r in rows]

    async def get_by_alert(self, alert_id: str) -> list[InvestigationRead]:
        return await asyncio.to_thread(self._get_by_alert_sync, alert_id)

    def _list_recent_sync(
        self,
        limit: int = 50,
        metric_name: str | None = None,
        status: InvestigationStatus | None = None,
        since: datetime | None = None,
    ) -> list[InvestigationRead]:
        with get_session() as session:
            stmt = sa.select(InvestigationORM).order_by(InvestigationORM.started_at.desc()).limit(limit)
            if metric_name:
                stmt = stmt.where(InvestigationORM.metric_name == metric_name)
            if status:
                stmt = stmt.where(InvestigationORM.status == status.value)
            if since:
                stmt = stmt.where(InvestigationORM.started_at >= since)
            rows = session.execute(stmt).scalars().all()
            return [self._to_read(r) for r in rows]

    async def list_recent(
        self,
        limit: int = 50,
        metric_name: str | None = None,
        status: InvestigationStatus | None = None,
        since: datetime | None = None,
    ) -> list[InvestigationRead]:
        return await asyncio.to_thread(self._list_recent_sync, limit, metric_name, status, since)
