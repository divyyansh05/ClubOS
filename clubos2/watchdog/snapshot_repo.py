from __future__ import annotations
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Text, DateTime

from clubos2.semantic_layer.db import get_session, get_engine
from clubos2.watchdog.priority_board_reader import PriorityBoardSnapshot, PriorityBoardRow


class SnapshotBase(DeclarativeBase):
    pass


class PriorityBoardSnapshotORM(SnapshotBase):
    __tablename__ = "priority_board_snapshots"

    snapshot_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    rows_json: Mapped[str] = mapped_column(Text, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


def bootstrap_snapshot_db(database_url: str | None = None) -> None:
    migration = Path(__file__).parent / "migrations" / "003_create_priority_board_snapshots.sql"
    sql = migration.read_text()
    engine = get_engine(database_url)
    with engine.begin() as conn:
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            conn.execute(sa.text(stmt))


def _snapshot_to_json(snapshot: PriorityBoardSnapshot) -> str:
    return snapshot.model_dump_json()


def _json_to_snapshot(orm: PriorityBoardSnapshotORM) -> PriorityBoardSnapshot:
    data = json.loads(orm.rows_json)
    return PriorityBoardSnapshot.model_validate(data)


class PriorityBoardSnapshotRepository:
    def _save_sync(self, snapshot: PriorityBoardSnapshot) -> str:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        orm = PriorityBoardSnapshotORM(
            snapshot_id=snapshot.snapshot_id,
            captured_at=snapshot.captured_at,
            source_path=snapshot.source_path,
            rows_json=_snapshot_to_json(snapshot),
            row_count=snapshot.row_count,
            created_at=now,
        )
        with get_session() as session:
            session.merge(orm)
        return snapshot.snapshot_id

    async def save(self, snapshot: PriorityBoardSnapshot) -> str:
        return await asyncio.to_thread(self._save_sync, snapshot)

    def _get_latest_sync(self) -> PriorityBoardSnapshot | None:
        with get_session() as session:
            orm = (
                session.query(PriorityBoardSnapshotORM)
                .order_by(PriorityBoardSnapshotORM.captured_at.desc())
                .first()
            )
            return _json_to_snapshot(orm) if orm else None

    async def get_latest(self) -> PriorityBoardSnapshot | None:
        return await asyncio.to_thread(self._get_latest_sync)

    def _get_previous_sync(self, before_snapshot_id: str) -> PriorityBoardSnapshot | None:
        with get_session() as session:
            ref = session.get(PriorityBoardSnapshotORM, before_snapshot_id)
            if ref is None:
                return None
            orm = (
                session.query(PriorityBoardSnapshotORM)
                .filter(PriorityBoardSnapshotORM.captured_at < ref.captured_at)
                .order_by(PriorityBoardSnapshotORM.captured_at.desc())
                .first()
            )
            return _json_to_snapshot(orm) if orm else None

    async def get_previous(self, before_snapshot_id: str) -> PriorityBoardSnapshot | None:
        return await asyncio.to_thread(self._get_previous_sync, before_snapshot_id)

    def _prune_older_than_sync(self, days: int) -> int:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
        with get_session() as session:
            return (
                session.query(PriorityBoardSnapshotORM)
                .filter(PriorityBoardSnapshotORM.captured_at < cutoff)
                .delete()
            )

    async def prune_older_than(self, days: int = 90) -> int:
        return await asyncio.to_thread(self._prune_older_than_sync, days)
