"""
Social Benchmark Service - V1.6.3

Provides peer benchmarking for Real Madrid's social media performance
across 10 elite European clubs.

Metrics supported:
- avg_engagement_per_post (default, most commercially meaningful)
- total_engagement
- instagram_engagement_rate
- posting_frequency
"""

from typing import Any, Optional
from app.clients.databricks import DatabricksClient
from app.config.settings import settings


def _client() -> DatabricksClient:
    return DatabricksClient(settings.clubos_databricks_host, settings.clubos_databricks_token)


def _month_str(row: dict[str, Any], key: str = "month") -> str:
    """Extract YYYY-MM-DD date string from row"""
    val = row.get(key, "")
    return str(val)[:10] if val else ""


def get_social_peer_benchmark(metric: str, month_str: Optional[str] = None) -> dict[str, Any]:
    """
    Get peer benchmark for a specific social metric.

    Args:
        metric: One of: avg_engagement_per_post, total_engagement,
                instagram_engagement_rate, posting_frequency
        month_str: Optional month YYYY-MM-DD. If None, uses latest month.

    Returns:
        Dict with all clubs ranked, Real Madrid position, peer median, leader, gaps.
    """

    # Map frontend-friendly metric names to CSV column names
    metric_column_map = {
        "avg_engagement_per_post": "avg_engagement_per_post",
        "total_engagement": "total_engagement",
        "instagram_engagement_rate": "instagram_engagement_rate",
        "posting_frequency": "posting_frequency_per_day",
    }

    if metric not in metric_column_map:
        raise ValueError(f"Unsupported metric: {metric}. Supported: {list(metric_column_map.keys())}")

    column_name = metric_column_map[metric]

    # Read data
    rows = _client().read_gold_table("gold_peer_social_benchmark")
    if not rows:
        return {
            "metric": metric,
            "month": None,
            "clubs": [],
            "rm_rank": None,
            "rm_value": None,
            "peer_median": None,
            "peer_leader_club": None,
            "peer_leader_value": None,
            "gap_to_median": None,
            "gap_to_leader": None,
            "club_count": 0,
        }

    # Filter to requested month (or latest)
    if month_str:
        filtered = [r for r in rows if _month_str(r) == month_str]
    else:
        # Get latest month
        latest_month = max(_month_str(r) for r in rows)
        filtered = [r for r in rows if _month_str(r) == latest_month]
        month_str = latest_month

    if not filtered:
        return {
            "metric": metric,
            "month": month_str,
            "clubs": [],
            "rm_rank": None,
            "rm_value": None,
            "peer_median": None,
            "peer_leader_club": None,
            "peer_leader_value": None,
            "gap_to_median": None,
            "gap_to_leader": None,
            "club_count": 0,
        }

    # Sort clubs by metric value (descending = best first for positive metrics)
    clubs_data = []
    for row in filtered:
        value = float(row.get(column_name, 0))
        club_name = str(row.get("club_name", ""))
        clubs_data.append({
            "club": club_name,
            "value": value,
            "is_real_madrid": club_name == "real_madrid",
        })

    clubs_data.sort(key=lambda x: x["value"], reverse=True)

    # Assign ranks
    for i, club in enumerate(clubs_data):
        club["rank"] = i + 1

    # Find Real Madrid
    rm_club = next((c for c in clubs_data if c["is_real_madrid"]), None)
    rm_rank = rm_club["rank"] if rm_club else None
    rm_value = rm_club["value"] if rm_club else None

    # Compute peer median (all 10 clubs)
    values = [c["value"] for c in clubs_data]
    values_sorted = sorted(values)
    n = len(values_sorted)
    if n == 0:
        peer_median = None
    elif n % 2 == 0:
        peer_median = (values_sorted[n // 2 - 1] + values_sorted[n // 2]) / 2
    else:
        peer_median = values_sorted[n // 2]

    # Leader is rank 1
    leader_club_data = clubs_data[0] if clubs_data else None
    peer_leader_club = leader_club_data["club"] if leader_club_data else None
    peer_leader_value = leader_club_data["value"] if leader_club_data else None

    # Gaps
    gap_to_median = (rm_value - peer_median) if (rm_value is not None and peer_median is not None) else None
    gap_to_leader = (rm_value - peer_leader_value) if (rm_value is not None and peer_leader_value is not None) else None

    return {
        "metric": metric,
        "month": month_str,
        "clubs": clubs_data,
        "rm_rank": rm_rank,
        "rm_value": rm_value,
        "peer_median": peer_median,
        "peer_leader_club": peer_leader_club,
        "peer_leader_value": peer_leader_value,
        "gap_to_median": gap_to_median,
        "gap_to_leader": gap_to_leader,
        "club_count": len(clubs_data),
    }


def get_social_benchmark_trend(metric: str) -> dict[str, Any]:
    """
    Get 12-month ranking trend for Real Madrid on a specific social metric.

    Args:
        metric: One of: avg_engagement_per_post, total_engagement,
                instagram_engagement_rate, posting_frequency

    Returns:
        Dict with monthly rank history for Real Madrid over 12 months.
    """

    # Map metric names
    metric_column_map = {
        "avg_engagement_per_post": "avg_engagement_per_post",
        "total_engagement": "total_engagement",
        "instagram_engagement_rate": "instagram_engagement_rate",
        "posting_frequency": "posting_frequency_per_day",
    }

    if metric not in metric_column_map:
        raise ValueError(f"Unsupported metric: {metric}")

    column_name = metric_column_map[metric]

    # Read data
    rows = _client().read_gold_table("gold_peer_social_benchmark")
    if not rows:
        return {
            "metric": metric,
            "months": [],
        }

    # Group by month
    months = sorted(set(_month_str(r) for r in rows))

    trend_data = []
    for month in months:
        month_rows = [r for r in rows if _month_str(r) == month]

        # Sort by metric
        clubs_data = []
        for row in month_rows:
            value = float(row.get(column_name, 0))
            clubs_data.append({
                "club": str(row.get("club_name", "")),
                "value": value,
            })

        clubs_data.sort(key=lambda x: x["value"], reverse=True)

        # Find Real Madrid rank
        rm_rank = None
        rm_value = None
        for i, club in enumerate(clubs_data):
            if club["club"] == "real_madrid":
                rm_rank = i + 1
                rm_value = club["value"]
                break

        trend_data.append({
            "month": month,
            "rm_rank": rm_rank,
            "rm_value": rm_value,
        })

    return {
        "metric": metric,
        "months": trend_data,
    }


def get_social_benchmark_summary() -> dict[str, Any]:
    """
    Get Real Madrid's position across all social benchmark metrics.

    Returns:
        Dict with Real Madrid's rank for each metric, identifying where they lead
        and where they lag vs peers.
    """

    metrics = [
        "avg_engagement_per_post",
        "total_engagement",
        "instagram_engagement_rate",
        "posting_frequency",
    ]

    summary = []
    for metric in metrics:
        try:
            benchmark = get_social_peer_benchmark(metric, month_str=None)
            summary.append({
                "metric": metric,
                "rm_rank": benchmark["rm_rank"],
                "rm_value": benchmark["rm_value"],
                "peer_median": benchmark["peer_median"],
                "gap_to_median": benchmark["gap_to_median"],
                "status": "leader" if benchmark["rm_rank"] == 1 else "above_median" if benchmark["gap_to_median"] and benchmark["gap_to_median"] > 0 else "below_median",
            })
        except Exception:
            # If metric fails, skip it
            continue

    latest_month = None
    rows = _client().read_gold_table("gold_peer_social_benchmark")
    if rows:
        latest_month = max(_month_str(r) for r in rows)

    return {
        "latest_month": latest_month,
        "metrics": summary,
    }
