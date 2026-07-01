from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from pydantic import BaseModel

from clubos2.observability.tracing import traced
from clubos2.watchdog.alerts_repo import AlertsRepository, bootstrap_watchdog_alerts_db
from clubos2.watchdog.detection_rules import DetectionContext, apply_all_rules
from clubos2.watchdog.memory_repo import AgentMemoryRepository, bootstrap_agent_memory_db
from clubos2.watchdog.priority_board_reader import PriorityBoardReader
from clubos2.watchdog.snapshot_repo import PriorityBoardSnapshotRepository, bootstrap_snapshot_db

logger = logging.getLogger("clubos.watchdog.orchestrator")


def bootstrap_all(database_url: str | None = None) -> None:
    """Run all three Watchdog migrations. Idempotent. Call once at startup."""
    bootstrap_watchdog_alerts_db(database_url)
    bootstrap_agent_memory_db(database_url)
    bootstrap_snapshot_db(database_url)


class WatchdogRunResult(BaseModel):
    run_id: str
    started_at: datetime
    finished_at: datetime
    duration_seconds: float
    metrics_evaluated: int
    rules_evaluated: int
    rules_fired: int
    alerts_created: int
    alerts_deduped: int
    snapshot_id: str
    alert_ids: list[str]
    errors: list[str]


@traced(name="watchdog:run", run_type="chain")
async def run_watchdog(
    dedup_window_days: int = 7,
    top_n: int = 10,
    csv_path: str = "data/gold_snapshots/gold_priority_board.csv",
) -> WatchdogRunResult:
    """One full Watchdog detection cycle.

    Pipeline:
      1. Generate run_id
      2. Read current Priority Board snapshot
      3. Get previous snapshot from repo
      4. Diff current vs previous
      5. Apply all detection rules (sync + async/LTM-aware)
      6. Deduplicate fired alerts via LTM (suppress if same metric+alert_type fired recently)
      7. Persist deduped alerts in one batch
      8. Record LTM memories for dedup AND for persistent_top future runs
      9. Save current snapshot for next run's diff baseline
      10. Purge expired memories
      11. Return WatchdogRunResult
    """
    # Pre-initialize before try block so the except block always has valid references
    diffs = []
    results = []
    fired = []
    persisted = []
    alert_ids: list[str] = []
    deduped_count = 0
    current_snapshot = None

    run_id = f"wdog_{uuid4().hex[:16]}"
    started_at = datetime.now(timezone.utc).replace(tzinfo=None)
    errors: list[str] = []

    try:
        reader = PriorityBoardReader(csv_path=csv_path)
        alerts_repo = AlertsRepository()
        memory_repo = AgentMemoryRepository()
        snapshot_repo = PriorityBoardSnapshotRepository()

        # Step 2: read current snapshot
        current_snapshot = await reader.read_current()
        current_snapshot = current_snapshot.model_copy(
            update={"snapshot_id": f"snap_{uuid4().hex[:16]}"}
        )

        # Step 3: get previous snapshot
        previous_snapshot = await snapshot_repo.get_latest()

        # Step 4: diff
        diffs = await reader.diff_against_previous(current_snapshot, previous_snapshot)

        # Step 5: apply all rules
        ctx = DetectionContext(top_n=top_n, run_id=run_id)
        results = await apply_all_rules(diffs, ctx, memory_repo)
        fired = [r for r in results if r.fired and r.alert is not None]

        # Step 6: deduplication
        to_persist = []
        for result in fired:
            subject = f"{result.alert.metric_name}::{result.alert.alert_type.value}"
            if await memory_repo.has_recent(
                agent_name="watchdog",
                subject_key=subject,
                within=timedelta(days=dedup_window_days),
            ):
                deduped_count += 1
                logger.debug("Deduped alert: %s", subject)
                continue
            to_persist.append(result.alert)

        # Step 7: persist alerts
        persisted = await alerts_repo.create_batch(to_persist)
        alert_ids = [a.alert_id for a in persisted]

        # Step 8a: record alert_fired memories (for dedup on future runs)
        for alert in persisted:
            await memory_repo.remember(
                agent_name="watchdog",
                memory_type="alert_fired",
                subject_key=f"{alert.metric_name}::{alert.alert_type.value}",
                subject_metadata={"alert_id": alert.alert_id, "run_id": run_id},
                ttl=timedelta(days=dedup_window_days),
            )

        # Step 8b: bulk-record present_in_top_n memories for persistent_top rule
        in_top_n_metrics = [row.metric_name for row in current_snapshot.rows if row.rank <= top_n]
        await memory_repo.remember_top_n_presence(in_top_n_metrics, run_id=run_id)

        # Step 9: save snapshot for next run's diff baseline
        await snapshot_repo.save(current_snapshot)

        # Step 10: housekeeping
        await memory_repo.purge_expired()

    except Exception as e:
        errors.append(f"Watchdog run failed: {e}")
        logger.exception("Watchdog orchestrator crashed")

    finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
    return WatchdogRunResult(
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=(finished_at - started_at).total_seconds(),
        metrics_evaluated=len(diffs),
        rules_evaluated=len(results),
        rules_fired=len(fired),
        alerts_created=len(persisted),
        alerts_deduped=deduped_count,
        snapshot_id=current_snapshot.snapshot_id if current_snapshot else "",
        alert_ids=alert_ids,
        errors=errors,
    )


if __name__ == "__main__":
    import asyncio
    import json

    bootstrap_all()
    result = asyncio.run(run_watchdog())
    print(json.dumps(result.model_dump(mode="json"), indent=2))
