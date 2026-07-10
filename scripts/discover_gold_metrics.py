"""
Discover all metric names that exist in Gold-layer files.

Uses the same compound naming convention as GoldClient:
    {asset_name}_{metric_name}

e.g., streaming_daily_users, main_website_bounce_rate

Prints a JSON array of compound metric names. Exits 0.
"""
import csv
import json
import sys
from pathlib import Path

DIMENSION_COLUMNS = {
    "year", "month", "quarter", "week", "day",
    "platform", "club_id", "club_name",
    "snapshot_date", "snapshot_id", "run_id",
    "rank", "priority_score",
    "period_start", "period_end",
    "severity_component", "persistence_component", "peer_gap_component",
    "commercial_impact_component", "evidence_component",
    "prior_month_value", "prior_season_same_month_value", "rolling_12m_avg",
    "deviation_from_rolling_avg", "seasonal_z_score", "trend_direction",
    "health_status", "asset_name", "metric_name", "metric_value",
}

LONG_FORMAT_FILES = {
    # file → (asset_col, metric_col)
    "gold_kpi_health.csv": ("asset_name", "metric_name"),
    "gold_peer_benchmark.csv": ("asset_name", "metric_name"),
}

PRIORITY_BOARD_FILE = "gold_priority_board.csv"


def discover_gold_metrics(gold_dir: Path = Path("data/gold_snapshots")) -> set[str]:
    metrics: set[str] = set()

    for csv_path in sorted(gold_dir.rglob("*.csv")):
        fname = csv_path.name

        # Long-format files with (asset_name, metric_name) columns
        if fname in LONG_FORMAT_FILES:
            asset_col, metric_col = LONG_FORMAT_FILES[fname]
            with csv_path.open("r", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    asset = row.get(asset_col, "").strip()
                    metric = row.get(metric_col, "").strip()
                    if asset and metric:
                        metrics.add(f"{asset}_{metric}")
            continue

        # priority_board: use asset_name + primary_metric
        if fname == PRIORITY_BOARD_FILE:
            with csv_path.open("r", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    asset = row.get("asset_name", "").strip()
                    metric = row.get("primary_metric", "").strip()
                    if asset and metric:
                        metrics.add(f"{asset}_{metric}")
            continue

    return metrics


if __name__ == "__main__":
    gold_dir = Path("data/gold_snapshots")
    if not gold_dir.exists():
        print(f"Gold snapshots dir not found: {gold_dir}", file=sys.stderr)
        sys.exit(1)

    metrics = discover_gold_metrics(gold_dir)
    print(json.dumps(sorted(metrics), indent=2))
    print(f"\n# Total distinct metrics in Gold: {len(metrics)}", file=sys.stderr)
