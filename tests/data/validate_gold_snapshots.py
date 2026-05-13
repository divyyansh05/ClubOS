#!/usr/bin/env python3
"""
Executable Gold snapshot validation script.

Validates that Gold snapshot files exist, are readable, and contain valid data structures.
Can be run locally to verify snapshot integrity before deploying or after data refresh.

Usage:
    python tests/data/validate_gold_snapshots.py [snapshot_dir]

If no directory is provided, uses data/gold_snapshots by default.
"""

import csv
import json
import sys
from pathlib import Path
from typing import Any


def validate_file_exists(snapshot_dir: Path, filename: str) -> bool:
    """Check if snapshot file exists."""
    filepath = snapshot_dir / filename
    if not filepath.exists():
        print(f"❌ FAIL: {filename} not found")
        return False
    print(f"✅ PASS: {filename} exists")
    return True


def validate_csv_readable(snapshot_dir: Path, filename: str) -> tuple[bool, list[dict[str, Any]]]:
    """Check if CSV file is readable and return rows."""
    filepath = snapshot_dir / filename
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        print(f"✅ PASS: {filename} is readable ({len(rows)} rows)")
        return True, rows
    except Exception as e:
        print(f"❌ FAIL: {filename} cannot be read: {e}")
        return False, []


def validate_priority_board(snapshot_dir: Path) -> bool:
    """Validate gold_priority_board.csv structure."""
    print("\n🔍 Validating gold_priority_board.csv...")

    success, rows = validate_csv_readable(snapshot_dir, "gold_priority_board.csv")
    if not success:
        return False

    if len(rows) == 0:
        print("⚠️  WARN: gold_priority_board has no rows")
        return True

    required_cols = [
        "month", "priority_id", "priority_title", "priority_category",
        "priority_score", "priority_rank", "asset_name", "primary_metric"
    ]

    first_row = rows[0]
    missing_cols = [col for col in required_cols if col not in first_row]

    if missing_cols:
        print(f"❌ FAIL: Missing columns: {missing_cols}")
        return False

    # Check score is numeric
    try:
        float(first_row["priority_score"])
        int(first_row["priority_rank"])
    except ValueError:
        print(f"❌ FAIL: priority_score or priority_rank not numeric")
        return False

    print(f"✅ PASS: gold_priority_board structure valid")
    return True


def validate_kpi_health(snapshot_dir: Path) -> bool:
    """Validate gold_kpi_health.csv structure."""
    print("\n🔍 Validating gold_kpi_health.csv...")

    success, rows = validate_csv_readable(snapshot_dir, "gold_kpi_health.csv")
    if not success:
        return False

    if len(rows) == 0:
        print("❌ FAIL: gold_kpi_health has no rows")
        return False

    required_cols = [
        "month", "asset_name", "metric_name", "metric_value",
        "health_status", "trend_direction"
    ]

    first_row = rows[0]
    missing_cols = [col for col in required_cols if col not in first_row]

    if missing_cols:
        print(f"❌ FAIL: Missing columns: {missing_cols}")
        return False

    # Check health_status values
    valid_statuses = {"good", "review", "stable"}
    status = first_row["health_status"]
    if status not in valid_statuses:
        print(f"❌ FAIL: Invalid health_status '{status}', expected one of {valid_statuses}")
        return False

    print(f"✅ PASS: gold_kpi_health structure valid ({len(rows)} rows)")
    return True


def validate_peer_benchmark(snapshot_dir: Path) -> bool:
    """Validate gold_peer_benchmark.csv structure."""
    print("\n🔍 Validating gold_peer_benchmark.csv...")

    success, rows = validate_csv_readable(snapshot_dir, "gold_peer_benchmark.csv")
    if not success:
        return False

    if len(rows) == 0:
        print("⚠️  WARN: gold_peer_benchmark has no rows")
        return True

    required_cols = [
        "month", "asset_name", "metric_name", "rm_value",
        "peer_median", "rm_rank", "club_count"
    ]

    first_row = rows[0]
    missing_cols = [col for col in required_cols if col not in first_row]

    if missing_cols:
        print(f"❌ FAIL: Missing columns: {missing_cols}")
        return False

    # Check rank is numeric
    try:
        int(first_row["rm_rank"])
        int(first_row["club_count"])
    except ValueError:
        print(f"❌ FAIL: rm_rank or club_count not numeric")
        return False

    print(f"✅ PASS: gold_peer_benchmark structure valid ({len(rows)} rows)")
    return True


def validate_signal_relationships(snapshot_dir: Path) -> bool:
    """Validate gold_signal_relationships.csv structure."""
    print("\n🔍 Validating gold_signal_relationships.csv...")

    success, rows = validate_csv_readable(snapshot_dir, "gold_signal_relationships.csv")
    if not success:
        return False

    if len(rows) == 0:
        print("⚠️  WARN: gold_signal_relationships has no rows")
        return True

    required_cols = [
        "source_asset", "source_metric", "target_asset", "target_metric",
        "lag_months", "validation_status"
    ]

    first_row = rows[0]
    missing_cols = [col for col in required_cols if col not in first_row]

    if missing_cols:
        print(f"❌ FAIL: Missing columns: {missing_cols}")
        return False

    # Check validation_status
    valid_statuses = {"active", "inactive"}
    status = first_row["validation_status"]
    if status not in valid_statuses:
        print(f"❌ FAIL: Invalid validation_status '{status}', expected one of {valid_statuses}")
        return False

    print(f"✅ PASS: gold_signal_relationships structure valid ({len(rows)} rows)")
    return True


def validate_monthly_brief_inputs(snapshot_dir: Path) -> bool:
    """Validate gold_monthly_brief_inputs.csv structure."""
    print("\n🔍 Validating gold_monthly_brief_inputs.csv...")

    success, rows = validate_csv_readable(snapshot_dir, "gold_monthly_brief_inputs.csv")
    if not success:
        return False

    if len(rows) == 0:
        print("❌ FAIL: gold_monthly_brief_inputs has no rows")
        return False

    required_cols = [
        "month", "top_priority_ids_json", "top_anomalies_json",
        "strongest_signal_ids_json", "benchmark_summary_json", "health_summary_json"
    ]

    first_row = rows[0]
    missing_cols = [col for col in required_cols if col not in first_row]

    if missing_cols:
        print(f"❌ FAIL: Missing columns: {missing_cols}")
        return False

    # Validate JSON fields are parseable
    json_fields = [
        "top_priority_ids_json", "top_anomalies_json",
        "strongest_signal_ids_json", "benchmark_summary_json", "health_summary_json"
    ]

    for field in json_fields:
        try:
            json.loads(first_row[field])
        except json.JSONDecodeError:
            print(f"❌ FAIL: {field} contains invalid JSON")
            return False

    print(f"✅ PASS: gold_monthly_brief_inputs structure valid ({len(rows)} rows)")
    return True


def main() -> int:
    """Run all validations and return exit code."""
    if len(sys.argv) > 1:
        snapshot_dir = Path(sys.argv[1])
    else:
        snapshot_dir = Path(__file__).parent.parent.parent / "data" / "gold_snapshots"

    print(f"📂 Validating Gold snapshots in: {snapshot_dir}")
    print("=" * 60)

    if not snapshot_dir.exists():
        print(f"❌ FAIL: Snapshot directory does not exist: {snapshot_dir}")
        return 1

    # Run all validations
    validations = [
        validate_file_exists(snapshot_dir, "gold_priority_board.csv"),
        validate_file_exists(snapshot_dir, "gold_kpi_health.csv"),
        validate_file_exists(snapshot_dir, "gold_peer_benchmark.csv"),
        validate_file_exists(snapshot_dir, "gold_signal_relationships.csv"),
        validate_file_exists(snapshot_dir, "gold_monthly_brief_inputs.csv"),
        validate_priority_board(snapshot_dir),
        validate_kpi_health(snapshot_dir),
        validate_peer_benchmark(snapshot_dir),
        validate_signal_relationships(snapshot_dir),
        validate_monthly_brief_inputs(snapshot_dir),
    ]

    print("\n" + "=" * 60)
    if all(validations):
        print("✅ ALL VALIDATIONS PASSED")
        return 0
    else:
        print("❌ SOME VALIDATIONS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
