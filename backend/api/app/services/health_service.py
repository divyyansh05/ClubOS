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
