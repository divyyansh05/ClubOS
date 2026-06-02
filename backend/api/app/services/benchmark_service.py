from typing import Any
from pathlib import Path
import pandas as pd
import json

from app.clients.databricks import DatabricksClient
from app.config.settings import settings


def _client() -> DatabricksClient:
    return DatabricksClient(settings.clubos_databricks_host, settings.clubos_databricks_token)


def _month_str(row: dict[str, Any]) -> str:
    val = row.get("month", "")
    return str(val)[:10] if val else ""


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip().lower()
    return text in {"", "nan", "none", "null"}


def _optional_int(value: Any) -> int | None:
    if _is_missing(value):
        return None
    return int(float(value))


def _optional_float(value: Any) -> float | None:
    if _is_missing(value):
        return None
    return float(value)


def get_benchmark_view(asset: str, metric: str) -> dict[str, Any]:
    rows = _client().read_gold_table("gold_peer_benchmark")
    filtered = [
        row for row in rows
        if str(row.get("asset_name")) == asset and str(row.get("metric_name")) == metric
    ]
    points = sorted(filtered, key=_month_str)

    normalized = [{
        "month": _month_str(r),
        "rm_value": float(r["rm_value"]),
        "peer_median": float(r["peer_median"]),
        "peer_leader_value": float(r["peer_leader_value"]),
        "rm_rank": int(r["rm_rank"]),
        "club_count": int(r["club_count"]),
        "raw_gap_to_peer_median": float(r["raw_gap_to_peer_median"]),
        "gap_to_peer_median": float(r["gap_to_peer_median"]),
        "gap_to_leader": float(r["gap_to_leader"]),
        "rank_change_12m": _optional_int(r.get("rank_change_12m")),
        "gap_change_12m": _optional_float(r.get("gap_change_12m")),
    } for r in points]

    latest_month = normalized[-1]["month"] if normalized else None
    return {
        "asset": asset,
        "metric": metric,
        "latest_month": latest_month,
        "points": normalized,
    }


def get_club_comparison(asset: str, metric: str) -> dict[str, Any]:
    """
    Get all clubs (RM + peers) for latest month with values and ranks.
    Reads from source Excel files to get individual club data.
    """
    # Map asset to sheet name
    sheet_map = {
        "main_website": "Main_Website",
        "ecommerce": "eCommerce",
        "streaming": "Streaming",
        "fan_app": "Fan_App",
    }

    sheet_name = sheet_map.get(asset)
    if not sheet_name:
        return {"month": None, "clubs": [], "peer_median": None}

    # Locate source files (relative to project root)
    # Go up from backend/api/app/services to project root
    project_root = Path(__file__).parents[4]
    source_dir = project_root / "data" / "source" / "GroupE.pack.english" / "Tema5.data_visualization.dataset"
    internal_path = source_dir / "Tema5.internal_metrics.dataset.xlsx"
    benchmark_path = source_dir / "Tema5.benchmark.dataset.xlsx"

    if not internal_path.exists() or not benchmark_path.exists():
        # Fallback: try to get data from gold_peer_benchmark only
        rows = _client().read_gold_table("gold_peer_benchmark")
        filtered = [
            row for row in rows
            if str(row.get("asset_name")) == asset and str(row.get("metric_name")) == metric
        ]
        if not filtered:
            return {"month": None, "clubs": [], "peer_median": None}

        latest = sorted(filtered, key=_month_str)[-1]
        # Can only return RM value since we don't have individual club data
        return {
            "month": _month_str(latest),
            "clubs": [{
                "club": "Real Madrid",
                "value": float(latest["rm_value"]),
                "rank": int(latest["rm_rank"]),
                "is_real_madrid": True,
            }],
            "peer_median": float(latest["peer_median"]),
        }

    try:
        # Read RM value from internal metrics
        internal_df = pd.read_excel(internal_path, sheet_name=sheet_name)
        latest_month = internal_df['month'].max()
        internal_latest = internal_df[internal_df['month'] == latest_month]

        if metric not in internal_df.columns:
            return {"month": None, "clubs": [], "peer_median": None}

        rm_value = float(internal_latest[metric].iloc[0])

        # Read peer values from benchmark
        benchmark_df = pd.read_excel(benchmark_path, sheet_name=sheet_name)
        benchmark_latest = benchmark_df[benchmark_df['month'] == latest_month]

        if metric not in benchmark_df.columns:
            return {"month": None, "clubs": [], "peer_median": None}

        # Combine all clubs
        clubs_list = []
        for _, row in benchmark_latest.iterrows():
            clubs_list.append({
                "club": str(row['club']),
                "value": float(row[metric]),
            })

        clubs_list.append({
            "club": "Real Madrid",
            "value": rm_value,
        })

        # Get polarity from metric dictionary
        metric_dict_path = project_root / "databricks" / "seeds" / "metric_dictionary.json"
        polarity = 1
        if metric_dict_path.exists():
            with open(metric_dict_path) as f:
                mdict = json.load(f)
                polarity = mdict.get(metric, {}).get("polarity", 1)

        # Sort and rank
        clubs_list.sort(key=lambda x: x["value"], reverse=(polarity == 1))
        for rank, club in enumerate(clubs_list, 1):
            club["rank"] = rank
            club["is_real_madrid"] = club["club"] == "Real Madrid"

        # Compute peer median (excluding RM)
        peer_values = [c["value"] for c in clubs_list if not c["is_real_madrid"]]
        peer_median = float(pd.Series(peer_values).median()) if peer_values else None

        return {
            "month": str(latest_month)[:10],
            "clubs": clubs_list,
            "peer_median": peer_median,
        }

    except Exception:
        # Fallback to empty response if Excel read fails
        return {"month": None, "clubs": [], "peer_median": None}
