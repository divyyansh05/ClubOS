from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.clients.databricks import DatabricksClient
from app.config.settings import settings


def _client() -> DatabricksClient:
    return DatabricksClient(settings.clubos_databricks_host, settings.clubos_databricks_token)


def _to_month_str(value: Any) -> str:
    return str(value)[:10]


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_refresh_status() -> dict[str, Any]:
    client = _client()

    quality_rows = client.read_table("silver_data_quality_checks")
    gold_rows = client.read_gold_table("gold_kpi_health")

    latest_gold_month = max((_to_month_str(r["month"]) for r in gold_rows), default=None)

    if not quality_rows:
        return {
            "status": "unknown",
            "last_run_timestamp": None,
            "latest_gold_month": latest_gold_month,
            "required_failed_checks_count": 0,
            "message": "No quality check logs available yet.",
        }

    run_times = [(_parse_timestamp(r.get("run_timestamp")), str(r.get("run_id", ""))) for r in quality_rows]
    run_times = [t for t in run_times if t[0] is not None]
    if not run_times:
        return {
            "status": "unknown",
            "last_run_timestamp": None,
            "latest_gold_month": latest_gold_month,
            "required_failed_checks_count": 0,
            "message": "Quality check logs found but run timestamps are invalid.",
        }

    latest_run_time, latest_run_id = max(run_times, key=lambda x: x[0])
    latest_rows = [r for r in quality_rows if str(r.get("run_id", "")) == latest_run_id]

    required_failed_checks_count = sum(
        1
        for r in latest_rows
        if str(r.get("severity", "")).upper() == "REQUIRED"
        and str(r.get("status", "")).upper() == "FAIL"
    )

    if required_failed_checks_count > 0:
        status = "failed"
        message = "Latest quality run has failed required checks."
    elif datetime.now(timezone.utc) - latest_run_time > timedelta(days=45):
        status = "stale"
        message = "Latest quality run is older than 45 days."
    else:
        status = "ok"
        message = "Latest quality run passed required checks."

    return {
        "status": status,
        "last_run_timestamp": latest_run_time.isoformat(),
        "latest_gold_month": latest_gold_month,
        "required_failed_checks_count": required_failed_checks_count,
        "message": message,
    }
