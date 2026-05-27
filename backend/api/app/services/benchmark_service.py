from typing import Any

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
