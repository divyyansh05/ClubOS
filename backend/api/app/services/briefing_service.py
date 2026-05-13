import json
from typing import Any

from app.clients.databricks import DatabricksClient
from app.config.settings import settings


def _client() -> DatabricksClient:
    return DatabricksClient(settings.clubos_databricks_host, settings.clubos_databricks_token)


def _month_str(row: dict[str, Any]) -> str:
    return str(row["month"])[:10]


def get_latest_briefing() -> dict[str, Any]:
    rows = _client().read_gold_table("gold_monthly_brief_inputs")
    if not rows:
        return {
            "month": "",
            "top_priorities": [],
            "top_anomalies": [],
            "strongest_signals": [],
            "benchmark_summary": None,
            "health_summary": None,
        }

    latest = max(rows, key=_month_str)

    # Parse JSON strings
    top_priorities = json.loads(str(latest.get("top_priority_ids_json", "[]")))
    top_anomalies = json.loads(str(latest.get("top_anomalies_json", "[]")))
    strongest_signals = json.loads(str(latest.get("strongest_signal_ids_json", "[]")))
    benchmark_summary_raw = str(latest.get("benchmark_summary_json", "{}"))
    health_summary_raw = str(latest.get("health_summary_json", "{}"))

    # Parse benchmark and health summaries (can be empty objects)
    try:
        benchmark_summary = json.loads(benchmark_summary_raw) if benchmark_summary_raw and benchmark_summary_raw != "{}" else None
    except (json.JSONDecodeError, ValueError):
        benchmark_summary = None

    try:
        health_summary = json.loads(health_summary_raw) if health_summary_raw and health_summary_raw != "{}" else None
    except (json.JSONDecodeError, ValueError):
        health_summary = None

    return {
        "month": _month_str(latest),
        "top_priorities": top_priorities,
        "top_anomalies": top_anomalies,
        "strongest_signals": strongest_signals,
        "benchmark_summary": benchmark_summary,
        "health_summary": health_summary,
    }
