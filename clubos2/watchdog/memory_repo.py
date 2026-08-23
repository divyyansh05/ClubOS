from __future__ import annotations
import asyncio
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from pathlib import Path

import sqlalchemy as sa

from clubos2.semantic_layer.db import get_session, get_engine
from clubos2.watchdog.memory_schema import AgentMemoryORM, AgentMemoryRead


def bootstrap_agent_memory_db(database_url: str | None = None) -> None:
    """Run migration 002. Idempotent."""
    migration = Path(__file__).parent / "migrations" / "002_create_agent_memory.sql"
    sql = migration.read_text()
    engine = get_engine(database_url)
    with engine.begin() as conn:
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            conn.execute(sa.text(stmt))


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AgentMemoryRepository:
    def _to_read(self, orm: AgentMemoryORM) -> AgentMemoryRead:
        return AgentMemoryRead.model_validate(orm)

    def _remember_sync(
        self,
        agent_name: str,
        memory_type: str,
        subject_key: str,
        subject_metadata: dict | None,
        ttl: timedelta | None,
        confidence: float | None,
    ) -> AgentMemoryRead:
        now = _now_utc()
        expires_at = (now + ttl) if ttl else None
        orm = AgentMemoryORM(
            memory_id=f"mem_{uuid4().hex[:16]}",
            agent_name=agent_name,
            memory_type=memory_type,
            subject_key=subject_key,
            subject_metadata=json.dumps(subject_metadata) if subject_metadata else None,
            occurred_at=now,
            expires_at=expires_at,
            confidence=confidence,
            created_at=now,
        )
        with get_session() as session:
            session.add(orm)
            session.flush()
            result = self._to_read(orm)
        return result

    async def remember(
        self,
        agent_name: str,
        memory_type: str,
        subject_key: str,
        subject_metadata: dict | None = None,
        ttl: timedelta | None = None,
        confidence: float | None = None,
    ) -> AgentMemoryRead:
        return await asyncio.to_thread(
            self._remember_sync,
            agent_name,
            memory_type,
            subject_key,
            subject_metadata,
            ttl,
            confidence,
        )

    def _has_recent_sync(
        self, agent_name: str, subject_key: str, within: timedelta
    ) -> bool:
        cutoff = _now_utc() - within
        now = _now_utc()
        with get_session() as session:
            q = session.query(AgentMemoryORM).filter(
                AgentMemoryORM.agent_name == agent_name,
                AgentMemoryORM.subject_key == subject_key,
                AgentMemoryORM.occurred_at >= cutoff,
                sa.or_(
                    AgentMemoryORM.expires_at == None,  # noqa: E711
                    AgentMemoryORM.expires_at > now,
                ),
            )
            return q.count() > 0

    async def has_recent(
        self, agent_name: str, subject_key: str, within: timedelta
    ) -> bool:
        return await asyncio.to_thread(
            self._has_recent_sync, agent_name, subject_key, within
        )

    def _last_seen_sync(
        self, agent_name: str, subject_key: str
    ) -> AgentMemoryRead | None:
        with get_session() as session:
            orm = (
                session.query(AgentMemoryORM)
                .filter(
                    AgentMemoryORM.agent_name == agent_name,
                    AgentMemoryORM.subject_key == subject_key,
                )
                .order_by(AgentMemoryORM.occurred_at.desc())
                .first()
            )
            return self._to_read(orm) if orm else None

    async def last_seen(
        self, agent_name: str, subject_key: str
    ) -> AgentMemoryRead | None:
        return await asyncio.to_thread(self._last_seen_sync, agent_name, subject_key)

    def _purge_expired_sync(self) -> int:
        now = _now_utc()
        with get_session() as session:
            q = session.query(AgentMemoryORM).filter(
                AgentMemoryORM.expires_at != None,  # noqa: E711
                AgentMemoryORM.expires_at < now,
            )
            count = q.count()
            q.delete(synchronize_session=False)
        return count

    async def purge_expired(self) -> int:
        return await asyncio.to_thread(self._purge_expired_sync)

    def _count_within_sync(
        self, agent_name: str, subject_key: str, within: timedelta
    ) -> int:
        cutoff = _now_utc() - within
        now = _now_utc()
        with get_session() as session:
            return (
                session.query(AgentMemoryORM)
                .filter(
                    AgentMemoryORM.agent_name == agent_name,
                    AgentMemoryORM.subject_key == subject_key,
                    AgentMemoryORM.occurred_at >= cutoff,
                    sa.or_(
                        AgentMemoryORM.expires_at == None,  # noqa: E711
                        AgentMemoryORM.expires_at > now,
                    ),
                )
                .count()
            )

    async def count_within(
        self, agent_name: str, subject_key: str, within: timedelta
    ) -> int:
        return await asyncio.to_thread(
            self._count_within_sync, agent_name, subject_key, within
        )

    def _list_in_period_sync(
        self,
        period_start: datetime,
        period_end: datetime,
        subject_key_prefix: str | None = None,
        limit: int = 200,
    ) -> list[AgentMemoryRead]:
        with get_session() as session:
            q = (
                session.query(AgentMemoryORM)
                .filter(
                    AgentMemoryORM.occurred_at >= period_start,
                    AgentMemoryORM.occurred_at <= period_end,
                )
                .order_by(AgentMemoryORM.occurred_at.desc())
            )
            if subject_key_prefix:
                q = q.filter(AgentMemoryORM.subject_key.like(f"{subject_key_prefix}%"))
            return [self._to_read(r) for r in q.limit(limit).all()]

    async def list_in_period(
        self,
        period_start: datetime,
        period_end: datetime,
        subject_key_prefix: str | None = None,
        limit: int = 200,
    ) -> list[AgentMemoryRead]:
        """List memory entries with occurred_at in [period_start, period_end].

        Optionally filter to entries whose subject_key starts with subject_key_prefix.
        Used by Briefer input assembly to pull recurring-pattern context.
        """
        return await asyncio.to_thread(
            self._list_in_period_sync, period_start, period_end, subject_key_prefix, limit
        )

    async def remember_top_n_presence(
        self,
        metric_names: list[str],
        run_id: str,
        ttl: timedelta = timedelta(days=30),
    ) -> None:
        for metric_name in metric_names:
            await self.remember(
                agent_name="watchdog",
                memory_type="present_in_top_n",
                subject_key=f"{metric_name}::present_in_top_n",
                subject_metadata={"run_id": run_id},
                ttl=ttl,
            )
