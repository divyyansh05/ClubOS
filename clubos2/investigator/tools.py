from __future__ import annotations
import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import pandas as pd
from langchain_core.tools import tool

from clubos2.observability.tracing import traced
from clubos2.mcp.web_search_client import WebSearchClient
from clubos2.mcp.server_config import WebSearchSettings


def _peer_benchmark_path() -> str:
    """Resolve peer benchmark CSV path from GOLD_SNAPSHOTS_DIR env var (Cloud Run
    CWD is /app/backend/api, so relative paths break)."""
    base = os.environ.get("GOLD_SNAPSHOTS_DIR", "data/gold_snapshots")
    return f"{base.rstrip('/')}/gold_peer_benchmark.csv"


_PEER_BENCHMARK_PATH = _peer_benchmark_path()


@tool
async def query_metrics(
    metric_name: Annotated[str, "Canonical metric name from the registry, e.g. 'streaming_daily_users'"],
    month: Annotated[str | None, "Specific month in YYYY-MM format, or None for most recent"] = None,
) -> list[dict]:
    """Fetch exact numeric values for a metric from the Gold layer.

    Use this when you need a verified number — current value, historical values for trend
    analysis, or specific month lookups. Returns rows with metric_name, value, month, source.

    Always use this for ANY number you mention in your final answer. Never state a value
    that did not come from this tool's output.
    """
    from clubos2.tools.registry import query_metrics as _query_metrics
    rows = await _query_metrics(metric_name, month)
    return [r.model_dump() for r in rows]


@tool
async def search_knowledge(
    query: Annotated[str, "Natural-language search query for skill files and historical briefings"],
    k: Annotated[int, "How many results to return (1-10)"] = 5,
) -> list[dict]:
    """Search internal ClubOS knowledge: skill files (priority_board.md, signal_engine.md)
    and historical briefings.

    Use this for context about HOW ClubOS works (e.g., 'what does the seasonal Z-score
    correct for'), known gotchas (e.g., 'January seasonal patterns'), or past stakeholder
    discussions. Do NOT use this for current numeric values — use query_metrics instead.
    """
    from clubos2.tools.registry import search_knowledge as _search_knowledge
    chunks = await _search_knowledge(query, k)
    return [c.model_dump() for c in chunks]


@tool
async def get_recent_alerts(
    metric_name: Annotated[str, "Metric to fetch alerts for"],
    days: Annotated[int, "How many days back to look"] = 30,
) -> list[dict]:
    """Fetch recent Watchdog alerts for a specific metric.

    Use this to understand the alert history of the metric you're investigating —
    has it alerted before? What types? What pattern?

    This is critical context: if a metric has alerted 3 times in the last week, the
    investigation should treat it as a sustained issue, not a one-off.
    """
    from clubos2.watchdog.alerts_repo import AlertsRepository
    repo = AlertsRepository()
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    alerts = await repo.list_recent(limit=50, since=since, metric_name=metric_name)
    return [a.model_dump(mode="json") for a in alerts]


@tool
async def get_metric_definition(
    metric_name: Annotated[str, "Canonical metric name to look up"],
) -> dict:
    """Get the semantic-layer definition of a metric: business name, definition,
    polarity, seasonal notes, typical range, disambiguation rules.

    Use this FIRST in most investigations to confirm you understand what the metric
    means and what its expected behaviour is. The seasonal_note field is especially
    important — many 'anomalies' are actually expected seasonal patterns.
    """
    from clubos2.semantic_layer.lookup import lookup_metric
    row = lookup_metric(metric_name)
    if row is None:
        return {"error": f"Metric '{metric_name}' not in registry", "source": "metric_registry"}
    result = row.model_dump()
    result["source"] = "metric_registry"
    return result


@tool
async def get_peer_benchmark(
    metric_name: Annotated[str, "Metric to compare against peers"],
    month: Annotated[str | None, "Specific month YYYY-MM, or None for most recent"] = None,
) -> dict:
    """Fetch peer benchmark data for a metric: our value vs peer median and gap.

    Use this to understand whether our metric's behaviour is an industry trend
    (peers also seeing similar changes) or a Real Madrid-specific issue.
    """
    df = pd.read_csv(_PEER_BENCHMARK_PATH)
    rows = df[df["metric_name"] == metric_name]
    if month:
        rows = rows[rows["month"].str.startswith(month)]
    if rows.empty:
        return {
            "error": f"No peer benchmark data for {metric_name}",
            "source": _PEER_BENCHMARK_PATH,
        }
    latest = rows.iloc[-1].to_dict()
    latest["source"] = _PEER_BENCHMARK_PATH
    return latest


@tool
async def web_search(
    query: Annotated[str, "Natural-language web search query. Be specific and time-bounded."],
    recent_only: Annotated[bool, "True to prefer results from the last 30 days"] = True,
) -> list[dict]:
    """Search the public web for external context.

    Use this for external factors that explain a metric change but aren't in our data:
    - Industry news (e.g., 'streaming service outages')
    - Competitor moves (e.g., 'new ecommerce launch competitor X')
    - Real-world events affecting fan engagement (e.g., 'controversial match decision')

    Be SPECIFIC in your queries. 'why did streaming drop' is too vague. 'Real Madrid
    streaming app outage March 2026' is useful.

    External results are LOWER CONFIDENCE than internal data. Cite them, but mark
    your hypothesis as 'medium' or 'low' confidence if it relies on web findings.
    """
    client = WebSearchClient()
    results = await client.search(query, include_recent_only=recent_only)
    return [r.model_dump() for r in results]


INVESTIGATOR_TOOLS = [
    query_metrics,
    search_knowledge,
    get_recent_alerts,
    get_metric_definition,
    get_peer_benchmark,
    web_search,
]
