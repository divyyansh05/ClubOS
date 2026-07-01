from __future__ import annotations
import asyncio
from datetime import datetime
from pathlib import Path

import sqlalchemy as sa

from clubos2.semantic_layer.db import get_session, get_engine
from clubos2.watchdog.alerts_schema import (
    AlertSeverity,
    WatchdogAlertCreate,
    WatchdogAlertORM,
    WatchdogAlertRead,
)


def bootstrap_watchdog_alerts_db(database_url: str | None = None) -> None:
    """Run migration 001. Idempotent."""
    migration = Path(__file__).parent / "migrations" / "001_create_watchdog_alerts.sql"
    sql = migration.read_text()
    engine = get_engine(database_url)
    with engine.begin() as conn:
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            conn.execute(sa.text(stmt))


class AlertsRepository:
    def _to_read(self, orm: WatchdogAlertORM) -> WatchdogAlertRead:
        return WatchdogAlertRead.model_validate(orm)

    def _create_sync(self, alert: WatchdogAlertCreate) -> WatchdogAlertRead:
        from datetime import timezone

        data = alert.model_dump()
        data["alert_type"] = alert.alert_type.value
        data["severity"] = alert.severity.value
        orm = WatchdogAlertORM(
            **data,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        with get_session() as session:
            session.add(orm)
            session.flush()
            result = self._to_read(orm)
        return result

    async def create(self, alert: WatchdogAlertCreate) -> WatchdogAlertRead:
        return await asyncio.to_thread(self._create_sync, alert)

    def _create_batch_sync(self, alerts: list[WatchdogAlertCreate]) -> list[WatchdogAlertRead]:
        from datetime import timezone

        results = []
        with get_session() as session:
            for alert in alerts:
                data = alert.model_dump()
                data["alert_type"] = alert.alert_type.value
                data["severity"] = alert.severity.value
                orm = WatchdogAlertORM(
                    **data,
                    created_at=datetime.now(timezone.utc).replace(tzinfo=None),
                )
                session.add(orm)
                results.append(orm)
            session.flush()
            out = [self._to_read(r) for r in results]
        return out

    async def create_batch(self, alerts: list[WatchdogAlertCreate]) -> list[WatchdogAlertRead]:
        if not alerts:
            return []
        return await asyncio.to_thread(self._create_batch_sync, alerts)

    def _list_recent_sync(
        self,
        limit: int,
        since: datetime | None,
        metric_name: str | None,
        severity: AlertSeverity | None,
    ) -> list[WatchdogAlertRead]:
        with get_session() as session:
            q = session.query(WatchdogAlertORM).order_by(WatchdogAlertORM.created_at.desc())
            if since:
                q = q.filter(WatchdogAlertORM.created_at >= since)
            if metric_name:
                q = q.filter(WatchdogAlertORM.metric_name == metric_name)
            if severity:
                q = q.filter(WatchdogAlertORM.severity == severity.value)
            rows = q.limit(limit).all()
            return [self._to_read(r) for r in rows]

    async def list_recent(
        self,
        limit: int = 50,
        since: datetime | None = None,
        metric_name: str | None = None,
        severity: AlertSeverity | None = None,
    ) -> list[WatchdogAlertRead]:
        return await asyncio.to_thread(self._list_recent_sync, limit, since, metric_name, severity)

    def _get_by_run_sync(self, run_id: str) -> list[WatchdogAlertRead]:
        with get_session() as session:
            rows = (
                session.query(WatchdogAlertORM)
                .filter(WatchdogAlertORM.run_id == run_id)
                .all()
            )
            return [self._to_read(r) for r in rows]

    async def get_by_run(self, run_id: str) -> list[WatchdogAlertRead]:
        return await asyncio.to_thread(self._get_by_run_sync, run_id)

    def _acknowledge_sync(self, alert_id: str, by_user: str) -> WatchdogAlertRead:
        from datetime import timezone

        with get_session() as session:
            orm = session.get(WatchdogAlertORM, alert_id)
            if orm is None:
                raise KeyError(f"Alert {alert_id} not found")
            orm.acknowledged_at = datetime.now(timezone.utc).replace(tzinfo=None)
            orm.acknowledged_by = by_user
            result = self._to_read(orm)
        return result

    async def acknowledge(self, alert_id: str, by_user: str) -> WatchdogAlertRead:
        return await asyncio.to_thread(self._acknowledge_sync, alert_id, by_user)

    def _get_by_id_sync(self, alert_id: str):
        from clubos2.watchdog.alerts_schema import WatchdogAlertORM
        with get_session() as session:
            orm = session.get(WatchdogAlertORM, alert_id)
            return self._to_read(orm) if orm else None

    async def get_by_id(self, alert_id: str):
        """Fetch a single alert by ID, or None if not found."""
        return await asyncio.to_thread(self._get_by_id_sync, alert_id)
