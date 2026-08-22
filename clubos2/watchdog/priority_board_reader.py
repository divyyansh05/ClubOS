from __future__ import annotations
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

import pandas as pd
from pydantic import BaseModel


class PriorityBoardSchemaError(Exception):
    """Raised when the CSV is missing required columns."""


REQUIRED_COLUMNS = {
    "month", "priority_rank", "priority_score", "asset_name",
    "primary_metric", "priority_title", "priority_category",
    "supporting_metrics_json",
}


class PriorityBoardRow(BaseModel):
    metric_name: str          # from primary_metric
    business_name: str        # from priority_title
    asset_name: str
    rank: int                 # from priority_rank
    score: float              # from priority_score
    category: str             # from priority_category
    severity_component: float
    persistence_component: float
    peer_gap_component: float
    commercial_component: float
    evidence_component: float
    source: str
    snapshot_time: datetime


class PriorityBoardSnapshot(BaseModel):
    snapshot_id: str
    captured_at: datetime
    rows: list[PriorityBoardRow]
    source_path: str
    row_count: int


class PriorityBoardDiff(BaseModel):
    metric_name: str
    business_name: str
    current_rank: int | None
    current_score: float | None
    previous_rank: int | None
    previous_score: float | None
    rank_delta: int | None
    score_delta: float | None
    is_new_in_top_n: bool
    is_dropped_out: bool
    is_persistent: bool


def _parse_score_components(json_str: str) -> dict:
    """Extract score_components from supporting_metrics_json."""
    try:
        data = json.loads(json_str)
        return data.get("score_components", {})
    except (json.JSONDecodeError, TypeError):
        return {}


def _csv_row_to_model(row: pd.Series, now: datetime, source: str) -> PriorityBoardRow:
    comps = _parse_score_components(str(row.get("supporting_metrics_json", "{}")))
    return PriorityBoardRow(
        metric_name=str(row["primary_metric"]),
        business_name=str(row["priority_title"]),
        asset_name=str(row["asset_name"]),
        rank=int(row["priority_rank"]),
        score=float(row["priority_score"]),
        category=str(row["priority_category"]),
        severity_component=float(comps.get("severity", 0.0)),
        persistence_component=float(comps.get("persistence", 0.0)),
        peer_gap_component=float(comps.get("peer_gap", 0.0)),
        commercial_component=float(comps.get("commercial_weight", 0.0)),
        evidence_component=float(comps.get("supporting_evidence", 0.0)),
        source=source,
        snapshot_time=now,
    )


class PriorityBoardReader:
    """Reads and diffs Priority Board snapshots from the gold CSV."""

    # Default to most recent data (highest rank = most critical)
    TOP_N = 10

    def __init__(self, csv_path: str = "data/gold_snapshots/gold_priority_board.csv"):
        self.csv_path = Path(csv_path)

    def _read_current_sync(self) -> PriorityBoardSnapshot:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Priority Board CSV not found: {self.csv_path}")

        df = pd.read_csv(self.csv_path)
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise PriorityBoardSchemaError(f"CSV missing columns: {missing}")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        source = str(self.csv_path)

        # Get most recent month's data (last month in the CSV)
        if "month" in df.columns:
            latest_month = df["month"].max()
            df = df[df["month"] == latest_month]

        rows = [_csv_row_to_model(row, now, source) for _, row in df.iterrows()]
        rows.sort(key=lambda r: r.rank)

        return PriorityBoardSnapshot(
            snapshot_id=f"snap_{uuid4().hex[:16]}",
            captured_at=now,
            rows=rows,
            source_path=source,
            row_count=len(rows),
        )

    async def read_current(self) -> PriorityBoardSnapshot:
        return await asyncio.to_thread(self._read_current_sync)

    async def diff_against_previous(
        self,
        current: PriorityBoardSnapshot,
        previous: PriorityBoardSnapshot | None,
    ) -> list[PriorityBoardDiff]:
        """Compute per-metric changes. Returns one diff per metric in either snapshot."""
        current_by_name = {r.metric_name: r for r in current.rows}
        previous_by_name = {r.metric_name: r for r in (previous.rows if previous else [])}
        all_metrics = set(current_by_name) | set(previous_by_name)

        diffs = []
        for name in all_metrics:
            curr = current_by_name.get(name)
            prev = previous_by_name.get(name)

            rank_delta = None
            score_delta = None
            if curr and prev:
                rank_delta = prev.rank - curr.rank  # positive = moved up (better)
                score_delta = curr.score - prev.score

            diffs.append(PriorityBoardDiff(
                metric_name=name,
                business_name=(curr or prev).business_name,
                current_rank=curr.rank if curr else None,
                current_score=curr.score if curr else None,
                previous_rank=prev.rank if prev else None,
                previous_score=prev.score if prev else None,
                rank_delta=rank_delta,
                score_delta=score_delta,
                is_new_in_top_n=(curr is not None and prev is None),
                is_dropped_out=(curr is None and prev is not None),
                is_persistent=False,  # set by the persistent_top rule separately
            ))

        return diffs
