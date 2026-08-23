"""Backfill preferred_source and source_authority_note for all active metrics.

Audit finding: kpi_health is a strict superset of priority_board in period
coverage (kpi_health has 6125 triples vs priority_board's 1020). Zero value
divergences for overlapping periods. Therefore kpi_health is unambiguously
authoritative for all cross-source metrics.

Setting preferred_source='gold.kpi_health' for all active metrics means
GoldClient will try kpi_health first, ensuring correct period resolution
and eliminating the wrong-period-returned bug.

Run with backend stopped (DuckDB lock):
    python scripts/backfill_preferred_source.py
"""
from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clubos2.semantic_layer.db import bootstrap_db, get_session
from clubos2.semantic_layer.schema import MetricRegistry
from clubos2.semantic_layer.lookup import get_all_metrics, refresh_cache

AUTHORITY_NOTE = (
    "gold.kpi_health is the authoritative source: it provides raw monthly metric values "
    "for every metric regardless of priority threshold. gold.priority_board is derived and "
    "only contains rows when a metric crosses the priority scoring threshold, creating "
    "sporadic period gaps (4851 periods in kpi_health absent from priority_board as of "
    "2026-07 audit). No value divergences when both sources overlap on the same period. "
    "Set by cross-source data integrity audit."
)


def main() -> None:
    bootstrap_db()
    refresh_cache()

    metrics = get_all_metrics()
    active = [m for m in metrics if m.is_active]
    print(f"Active metrics: {len(active)}")

    with get_session() as session:
        updated = 0
        for m in active:
            row = (
                session.query(MetricRegistry)
                .filter(MetricRegistry.metric_name == m.metric_name)
                .first()
            )
            if row is None:
                print(f"  WARNING: {m.metric_name} not found in DB")
                continue
            row.preferred_source = "gold.kpi_health"
            row.source_authority_note = AUTHORITY_NOTE
            row.updated_at = datetime.now(UTC)
            updated += 1

        session.commit()

    print(f"Updated preferred_source='gold.kpi_health' for {updated} active metrics.")


if __name__ == "__main__":
    main()
