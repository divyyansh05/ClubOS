from app.clients.databricks import DatabricksClient
from app.config.settings import settings


def _client() -> DatabricksClient:
    return DatabricksClient(settings.clubos_databricks_host, settings.clubos_databricks_token)


def get_latest_health_summary() -> dict:
    rows = _client().read_gold_table("gold_kpi_health")
    if not rows:
        return {
            "latest_month": "",
            "metric_count": 0,
            "good_count": 0,
            "review_count": 0,
            "stable_count": 0,
            "avg_abs_deviation": None,
        }

    latest_month = max(str(r["month"])[:10] for r in rows)
    latest_rows = [r for r in rows if str(r["month"])[:10] == latest_month]

    deviations = [
        abs(float(r["deviation_from_seasonal_baseline"]))
        for r in latest_rows
        if r.get("deviation_from_seasonal_baseline") is not None
    ]

    return {
        "latest_month": latest_month,
        "metric_count": len(latest_rows),
        "good_count": sum(1 for r in latest_rows if str(r.get("health_status")) == "good"),
        "review_count": sum(1 for r in latest_rows if str(r.get("health_status")) == "review"),
        "stable_count": sum(1 for r in latest_rows if str(r.get("health_status")) == "stable"),
        "avg_abs_deviation": (sum(deviations) / len(deviations)) if deviations else None,
    }


def get_asset_health_breakdown() -> dict:
    """
    Get health status breakdown by asset for the latest month.

    Returns dict with asset names as keys, each containing:
    - metric_count: total metrics for this asset
    - good_count: metrics in good health
    - review_count: metrics needing review
    - stable_count: stable metrics
    - health_percentage: percentage of metrics in good health
    """
    rows = _client().read_gold_table("gold_kpi_health")
    if not rows:
        return {}

    latest_month = max(str(r["month"])[:10] for r in rows)
    latest_rows = [r for r in rows if str(r["month"])[:10] == latest_month]

    # Group by asset
    assets = {}
    for row in latest_rows:
        asset = row.get("asset_name", "unknown")
        if asset not in assets:
            assets[asset] = []
        assets[asset].append(row)

    # Compute health stats per asset
    result = {}
    for asset, asset_rows in assets.items():
        good = sum(1 for r in asset_rows if str(r.get("health_status")) == "good")
        review = sum(1 for r in asset_rows if str(r.get("health_status")) == "review")
        stable = sum(1 for r in asset_rows if str(r.get("health_status")) == "stable")
        total = len(asset_rows)

        result[asset] = {
            "metric_count": total,
            "good_count": good,
            "review_count": review,
            "stable_count": stable,
            "health_percentage": (good / total * 100) if total > 0 else 0,
        }

    return result
