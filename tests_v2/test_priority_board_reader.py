from __future__ import annotations

import asyncio
import pathlib
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import sessionmaker

import clubos2.semantic_layer.db as db_mod
from clubos2.watchdog.priority_board_reader import (
    PriorityBoardDiff,
    PriorityBoardReader,
    PriorityBoardRow,
    PriorityBoardSnapshot,
)
from clubos2.watchdog.snapshot_repo import (
    PriorityBoardSnapshotRepository,
    bootstrap_snapshot_db,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CSV_PATH = "data/gold_snapshots/gold_priority_board.csv"
TEST_DB_PATH = "var/test_snapshot.duckdb"
TEST_URL = f"duckdb:///{TEST_DB_PATH}"


def _make_row(metric_name: str, rank: int, score: float = 0.5) -> PriorityBoardRow:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return PriorityBoardRow(
        metric_name=metric_name,
        business_name=f"Business {metric_name}",
        asset_name="test_asset",
        rank=rank,
        score=score,
        category="test_category",
        severity_component=0.0,
        persistence_component=0.0,
        peer_gap_component=0.0,
        commercial_component=0.0,
        evidence_component=0.0,
        source="synthetic",
        snapshot_time=now,
    )


def _make_snapshot(rows: list[PriorityBoardRow], snapshot_id: str = "snap_test001") -> PriorityBoardSnapshot:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return PriorityBoardSnapshot(
        snapshot_id=snapshot_id,
        captured_at=now,
        rows=rows,
        source_path="synthetic",
        row_count=len(rows),
    )


# ---------------------------------------------------------------------------
# DB fixture for snapshot repo tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def setup_db(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("snapdb")
    db_path = tmp / "test_snapshot.duckdb"
    test_url = f"duckdb:///{db_path}"

    engine = db_mod.get_engine(test_url)
    orig_engine = db_mod._default_engine
    orig_factory = db_mod._SessionFactory
    orig_url = db_mod.DATABASE_URL

    db_mod._default_engine = engine
    db_mod._SessionFactory = sessionmaker(bind=engine)
    db_mod.DATABASE_URL = test_url

    bootstrap_snapshot_db(test_url)

    yield

    db_mod._default_engine = orig_engine
    db_mod._SessionFactory = orig_factory
    db_mod.DATABASE_URL = orig_url


# ---------------------------------------------------------------------------
# Test 1: read_current() returns snapshot with at least 5 rows from real CSV
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_read_current_returns_rows():
    reader = PriorityBoardReader(csv_path=CSV_PATH)
    snapshot = await reader.read_current()

    assert isinstance(snapshot, PriorityBoardSnapshot)
    assert snapshot.row_count >= 5
    assert len(snapshot.rows) >= 5
    assert snapshot.row_count == len(snapshot.rows)
    assert snapshot.snapshot_id.startswith("snap_")
    assert isinstance(snapshot.captured_at, datetime)


# ---------------------------------------------------------------------------
# Test 2: diff with previous=None marks every row as is_new_in_top_n=True
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_diff_no_previous_marks_all_new():
    reader = PriorityBoardReader(csv_path=CSV_PATH)
    current = await reader.read_current()
    diffs = await reader.diff_against_previous(current, previous=None)

    # diffs are keyed by metric_name; duplicates across assets are collapsed
    assert len(diffs) >= 1
    assert len(diffs) <= len(current.rows)
    for diff in diffs:
        assert diff.is_new_in_top_n is True
        assert diff.is_dropped_out is False
        assert diff.previous_rank is None
        assert diff.previous_score is None
        assert diff.rank_delta is None
        assert diff.score_delta is None


# ---------------------------------------------------------------------------
# Test 3: diff with two synthetic snapshots correctly computes rank_delta
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_diff_computes_rank_delta():
    reader = PriorityBoardReader(csv_path=CSV_PATH)

    # metric_a: was rank 3, now rank 1 → rank_delta = 3 - 1 = +2 (improved)
    # metric_b: was rank 1, now rank 2 → rank_delta = 1 - 2 = -1 (worsened)
    prev_rows = [_make_row("metric_a", rank=3, score=0.4), _make_row("metric_b", rank=1, score=0.6)]
    curr_rows = [_make_row("metric_a", rank=1, score=0.5), _make_row("metric_b", rank=2, score=0.55)]

    previous = _make_snapshot(prev_rows, snapshot_id="snap_prev001")
    current = _make_snapshot(curr_rows, snapshot_id="snap_curr001")

    diffs = await reader.diff_against_previous(current, previous)
    diff_by_name = {d.metric_name: d for d in diffs}

    assert "metric_a" in diff_by_name
    assert "metric_b" in diff_by_name

    diff_a = diff_by_name["metric_a"]
    assert diff_a.rank_delta == 2      # prev_rank(3) - curr_rank(1) = 2
    assert diff_a.current_rank == 1
    assert diff_a.previous_rank == 3
    assert abs(diff_a.score_delta - 0.1) < 1e-9

    diff_b = diff_by_name["metric_b"]
    assert diff_b.rank_delta == -1     # prev_rank(1) - curr_rank(2) = -1
    assert diff_b.current_rank == 2
    assert diff_b.previous_rank == 1


# ---------------------------------------------------------------------------
# Test 4: metric in current but not previous → is_new_in_top_n=True, is_dropped_out=False
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_diff_new_metric_flags():
    reader = PriorityBoardReader(csv_path=CSV_PATH)

    prev_rows = [_make_row("metric_old", rank=1)]
    curr_rows = [_make_row("metric_new", rank=1), _make_row("metric_old", rank=2)]

    previous = _make_snapshot(prev_rows, snapshot_id="snap_p4_prev")
    current = _make_snapshot(curr_rows, snapshot_id="snap_p4_curr")

    diffs = await reader.diff_against_previous(current, previous)
    diff_by_name = {d.metric_name: d for d in diffs}

    new_diff = diff_by_name["metric_new"]
    assert new_diff.is_new_in_top_n is True
    assert new_diff.is_dropped_out is False
    assert new_diff.current_rank == 1
    assert new_diff.previous_rank is None


# ---------------------------------------------------------------------------
# Test 5: metric in previous but not current → is_dropped_out=True, is_new_in_top_n=False
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_diff_dropped_metric_flags():
    reader = PriorityBoardReader(csv_path=CSV_PATH)

    prev_rows = [_make_row("metric_gone", rank=1), _make_row("metric_stay", rank=2)]
    curr_rows = [_make_row("metric_stay", rank=1)]

    previous = _make_snapshot(prev_rows, snapshot_id="snap_p5_prev")
    current = _make_snapshot(curr_rows, snapshot_id="snap_p5_curr")

    diffs = await reader.diff_against_previous(current, previous)
    diff_by_name = {d.metric_name: d for d in diffs}

    dropped_diff = diff_by_name["metric_gone"]
    assert dropped_diff.is_dropped_out is True
    assert dropped_diff.is_new_in_top_n is False
    assert dropped_diff.current_rank is None
    assert dropped_diff.previous_rank == 1


# ---------------------------------------------------------------------------
# Test 6: save → get_latest round-trip
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_save_and_get_latest_round_trip(setup_db):
    rows = [
        _make_row("metric_rt_1", rank=1, score=0.9),
        _make_row("metric_rt_2", rank=2, score=0.8),
    ]
    snapshot = _make_snapshot(rows, snapshot_id="snap_roundtrip01")

    repo = PriorityBoardSnapshotRepository()
    returned_id = await repo.save(snapshot)
    assert returned_id == snapshot.snapshot_id

    retrieved = await repo.get_latest()
    assert retrieved is not None
    assert retrieved.snapshot_id == snapshot.snapshot_id
    assert retrieved.row_count == 2
    assert len(retrieved.rows) == 2

    retrieved_by_name = {r.metric_name: r for r in retrieved.rows}
    assert "metric_rt_1" in retrieved_by_name
    assert "metric_rt_2" in retrieved_by_name
    assert retrieved_by_name["metric_rt_1"].rank == 1
    assert retrieved_by_name["metric_rt_2"].score == pytest.approx(0.8)
