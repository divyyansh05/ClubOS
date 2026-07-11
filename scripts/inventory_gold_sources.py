"""Inventory all gold snapshot CSVs: metric coverage, period range, row count.

Output: docs/gold_source_inventory.json
Run: python scripts/inventory_gold_sources.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

GOLD_DIR = Path("data/gold_snapshots")
OUT_DIR = Path("docs")


def _extract_metrics(df: pd.DataFrame, csv_name: str) -> list[str]:
    """Pull distinct metric identifiers from a CSV, handling both narrow
    (asset_name + metric column) and wide formats."""
    if "primary_metric" in df.columns:
        return sorted(df["primary_metric"].dropna().unique().tolist())
    if "metric_name" in df.columns:
        return sorted(df["metric_name"].dropna().unique().tolist())
    # Wide format — every non-dimension column is a metric
    dimension_cols = {
        "month", "year", "quarter", "week", "day",
        "asset_name", "club_name", "club_id", "platform",
        "snapshot_date", "run_id", "period", "period_start", "period_end",
    }
    return sorted(c for c in df.columns if c not in dimension_cols)


def _period_range(df: pd.DataFrame) -> tuple[str | None, str | None]:
    for col in ("month", "period", "snapshot_date", "period_start"):
        if col in df.columns:
            vals = df[col].dropna()
            if len(vals):
                return str(vals.min()), str(vals.max())
    return None, None


def inventory() -> dict:
    result = {}
    for csv_path in sorted(GOLD_DIR.glob("*.csv")):
        try:
            df = pd.read_csv(csv_path, low_memory=False)
        except Exception as e:
            result[f"gold.{csv_path.stem}"] = {"error": str(e)}
            continue

        metrics = _extract_metrics(df, csv_path.stem)
        pmin, pmax = _period_range(df)

        has_asset = "asset_name" in df.columns
        n_pairs = 0
        if has_asset and ("primary_metric" in df.columns or "metric_name" in df.columns):
            metric_col = "primary_metric" if "primary_metric" in df.columns else "metric_name"
            period_col = next((c for c in ("month", "period") if c in df.columns), None)
            if period_col:
                n_pairs = df[[period_col, "asset_name", metric_col]].drop_duplicates().__len__()

        result[f"gold.{csv_path.stem}"] = {
            "source_file": csv_path.name,
            "row_count": len(df),
            "distinct_metrics": metrics,
            "metric_count": len(metrics),
            "has_asset_column": has_asset,
            "period_min": pmin,
            "period_max": pmax,
            "distinct_asset_metric_period_triples": n_pairs,
            "columns": df.columns.tolist(),
        }

    return result


def find_cross_source_metrics(inv: dict) -> dict[str, list[str]]:
    metric_to_sources: dict[str, list[str]] = defaultdict(list)
    for source, info in inv.items():
        if "error" in info:
            continue
        for m in info.get("distinct_metrics", []):
            metric_to_sources[m].append(source)
    return {m: srcs for m, srcs in metric_to_sources.items() if len(srcs) > 1}


def main() -> None:
    inv = inventory()
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "gold_source_inventory.json").write_text(json.dumps(inv, indent=2))

    print(f"Inventoried {len(inv)} gold sources:")
    for name, info in sorted(inv.items()):
        if "error" in info:
            print(f"  {name}: ERROR ({info['error']})")
        else:
            print(
                f"  {name}: {info['metric_count']} metrics, "
                f"{info['row_count']} rows, "
                f"{info.get('period_min')} → {info.get('period_max')}, "
                f"{info.get('distinct_asset_metric_period_triples')} (asset,metric,period) triples"
            )

    cross = find_cross_source_metrics(inv)
    (OUT_DIR / "cross_source_metrics.json").write_text(json.dumps(cross, indent=2))
    print(f"\nTotal distinct metrics across all gold: {sum(len(i.get('distinct_metrics',[])) for i in inv.values() if 'error' not in i)}")
    print(f"Metrics appearing in 2+ sources: {len(cross)}")


if __name__ == "__main__":
    main()
