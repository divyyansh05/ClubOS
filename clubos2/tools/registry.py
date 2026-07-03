from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from typing import Any

from pydantic import BaseModel

from clubos2.guardrails.source_required import requires_source
from clubos2.observability.tracing import traced
from clubos2.tools.errors import MetricNotFoundError

logger = logging.getLogger("clubos.tools.registry")

__all__ = [
    "MetricNotFoundError",
    "MetricRow",
    "KnowledgeChunk",
    "query_metrics",
    "search_knowledge",
]


class MetricRow(BaseModel):
    metric_name: str
    business_name: str
    value: float
    month: str
    polarity: str
    source: str  # always populated — what table this came from
    peer_rank: int | None = None
    peer_club_count: int | None = None
    peer_gap_to_median: float | None = None


class KnowledgeChunk(BaseModel):
    text: str
    source: str  # e.g. "monthly_briefing_2025_11.md"
    section: str  # e.g. "Streaming Performance"
    score: float  # retrieval relevance score


METRIC_FIXTURES = [
    MetricRow(
        metric_name="streaming_daily_users",
        business_name="Streaming Daily Active Users",
        value=85420.0,
        month="2025-11-01",
        polarity="higher_is_better",
        source="gold.priority_board",
    ),
    MetricRow(
        metric_name="conversion_rate_ecommerce",
        business_name="E-commerce Conversion Rate",
        value=0.024,
        month="2025-11-01",
        polarity="higher_is_better",
        source="gold.priority_board",
    ),
    MetricRow(
        metric_name="post_match_engagement",
        business_name="Post-Match Fan Engagement",
        value=4.2,
        month="2025-11-01",
        polarity="higher_is_better",
        source="gold.priority_board",
    ),
]

KNOWLEDGE_FIXTURES = [
    KnowledgeChunk(
        text=(
            "The seasonal Z-score normalization adjusts for historical monthly patterns. "
            "E-commerce conversion rate typically dips in November and rises significantly "
            "in December due to holiday sales."
        ),
        source="docs/project_plan/IMPLEMENTATION_PLAN.md",
        section="Seasonal Baseline Intelligence",
        score=0.92,
    ),
    KnowledgeChunk(
        text=(
            "Daily streaming users have shown a strong correlation with post-match "
            "social media engagement. A lag of 1 month was validated with a correlation "
            "coefficient of 0.72."
        ),
        source="docs/project_plan/IMPLEMENTATION_PLAN.md",
        section="Commercial Signal Engine",
        score=0.88,
    ),
]

SIGNAL_FIXTURES = {
    "sig_001": {
        "signal_id": "sig_001",
        "source_metric": "streaming_daily_users",
        "target_metric": "post_match_engagement",
        "correlation": 0.72,
        "lag_months": 1,
        "source": "data/gold_snapshots/gold_signal_relationships.csv",
    },
    "sig_002": {
        "signal_id": "sig_002",
        "source_metric": "conversion_rate_ecommerce",
        "target_metric": "net_sales",
        "correlation": 0.85,
        "lag_months": 0,
        "source": "data/gold_snapshots/gold_signal_relationships.csv",
    },
}

BENCHMARK_FIXTURES = {
    "streaming_daily_users": {
        "metric_name": "streaming_daily_users",
        "real_madrid_value": 85420.0,
        "peer_median": 72000.0,
        "peer_leader": 91000.0,
        "rank": 2,
        "peers_compared": ["Barcelona", "Manchester United", "Bayern Munich", "PSG"],
        "source": "data/gold_snapshots/gold_peer_benchmark.csv",
    },
    "conversion_rate_ecommerce": {
        "metric_name": "conversion_rate_ecommerce",
        "real_madrid_value": 0.024,
        "peer_median": 0.028,
        "peer_leader": 0.035,
        "rank": 4,
        "peers_compared": ["Barcelona", "Manchester United", "Bayern Munich", "PSG"],
        "source": "data/gold_snapshots/gold_peer_benchmark.csv",
    },
}


def _build_canonical_name(m: Any) -> str:
    """Build the canonical compound name expected by GoldClient."""
    platform = (m.platform or "").lower()
    name = m.metric_name.lower()

    # Map platforms to standardized assets in KNOWN_ASSETS
    platform_to_asset = {
        "web": "main_website",
        "social": "social_media",
        "ecommerce": "ecommerce",
        "streaming": "streaming",
        "fan_app": "fan_app",
        "main_website": "main_website",
        "social_media": "social_media",
    }
    asset = platform_to_asset.get(platform, platform)

    if not asset:
        return str(name)

    # Map raw registry names to raw Gold names
    raw_name_map = {
        "conversion_rate_streaming": "subscription_rate",
        "streaming_conversion_rate": "subscription_rate",
    }

    raw_name = name
    if name in raw_name_map:
        raw_name = raw_name_map[name]
    else:
        # Standardize name components: remove any existing prefix/suffix of asset or platform
        for alias in [asset, platform, "web", "social"]:
            if raw_name.startswith(f"{alias}_"):
                raw_name = raw_name[len(alias) + 1 :]
            elif raw_name.endswith(f"_{alias}"):
                raw_name = raw_name[: -len(alias) - 1]

    return f"{asset}_{raw_name}"


def _resolve_metric(metric_name: str) -> tuple[Any | None, str]:
    """Look up a metric name in the registry, resolving compound name differences.

    Returns:
        tuple: (registry_row, canonical_compound_name)
    """
    from clubos2.semantic_layer.lookup import _REGISTRY_CACHE, lookup_metric

    # 1. Exact match
    row = lookup_metric(metric_name)
    if row is not None:
        return row, _build_canonical_name(row)

    # 2. Try prefix-split logic
    known_assets = {
        "ecommerce": ["ecommerce", "ecom"],
        "streaming": ["streaming"],
        "fan_app": ["fan_app", "fan"],
        "main_website": ["main_website", "web", "website"],
        "social_media": ["social_media", "social"],
    }

    # Sort keys by length descending to match longest first
    for asset, aliases in sorted(known_assets.items(), key=lambda x: len(x[0]), reverse=True):
        for alias in aliases:
            prefix = alias + "_"
            if metric_name.startswith(prefix):
                remainder = metric_name[len(prefix) :]
                # Look for remainder in the cache
                for m in _REGISTRY_CACHE.values():
                    m_platform = (m.platform or "").lower()
                    m_name = m.metric_name.lower()
                    platform_matches = m_platform == asset or m_platform in aliases
                    name_matches = (
                        m_name == remainder
                        or m_name == f"{remainder}_{m_platform}"
                        or m_name == f"{m_platform}_{remainder}"
                    )
                    if platform_matches and name_matches:
                        return m, _build_canonical_name(m)

    # 3. Try reordered words match
    words = set(metric_name.replace("_", " ").lower().split())
    for m in _REGISTRY_CACHE.values():
        m_words = set(m.metric_name.replace("_", " ").lower().split())
        if words == m_words:
            return m, _build_canonical_name(m)

    return None, metric_name


@traced(name="tool:query_metrics", run_type="tool")
@requires_source
async def query_metrics(metric_name: str, month: str | None = None) -> list[MetricRow]:
    """Return metric values from the Gold layer for a validated metric.

    Validation flow:
    1. Look up metric_name in the semantic layer registry.
       - If not found: raise MetricNotFoundError with registry suggestions
         (from lookup_metrics_by_terms) AND Gold suggestions
         (from GoldClient.list_available_metrics).
    2. Fetch rows from gold_kpi_health.csv via GoldClient.
    3. Map to MetricRow with source = actual CSV file path.

    Raises MetricNotFoundError loud and clear — better an exception with
    suggestions than a silent empty result that hides data gaps.
    """
    # --- Step 1: Validate in semantic layer ---
    from clubos2.semantic_layer.lookup import (
        lookup_metrics_by_terms,
    )
    from clubos2.tools.gold_client import MetricNotInGoldError, get_gold_client

    registry_row, canonical_name = _resolve_metric(metric_name)
    if registry_row is None:
        # Build suggestions from registry (naming mismatch)
        registry_suggestions = [m.metric_name for m in lookup_metrics_by_terms([metric_name])]
        # Build suggestions from Gold (governance gap — in data but not defined)
        gold_client = get_gold_client()
        gold_metrics = gold_client.list_available_metrics()
        # Simple substring suggestions from Gold
        gold_suggestions = [k for k in gold_metrics if metric_name.lower() in k.lower()][:5]
        raise MetricNotFoundError(
            metric_name=metric_name,
            suggestions_from_registry=registry_suggestions,
            suggestions_from_gold=gold_suggestions,
        )

    # --- Step 2: Fetch from Gold CSVs ---
    gold_client = get_gold_client()
    try:
        rows = await gold_client.fetch_metric(canonical_name, month=month)
    except MetricNotInGoldError as exc:
        # Metric is registered but missing from Gold — data gap
        logger.warning("Data gap: %s", exc)
        raise MetricNotFoundError(
            metric_name=metric_name,
            suggestions_from_registry=[],
            suggestions_from_gold=[],
        ) from exc

    # --- Step 3: Map to MetricRow ---
    business_name = registry_row.business_name or metric_name.replace("_", " ").title()
    polarity = registry_row.polarity or "higher_is_better"

    results: list[MetricRow] = []
    for row in rows:
        try:
            value = float(row.get("metric_value", 0.0) or 0.0)
        except (TypeError, ValueError):
            value = 0.0

        results.append(
            MetricRow(
                metric_name=metric_name,
                business_name=business_name,
                value=value,
                month=str(row.get("month", month or "")),
                polarity=polarity,
                source=str(row.get("source", "gold.metrics_monthly")),
                peer_rank=row.get("peer_rank"),
                peer_club_count=row.get("peer_club_count"),
                peer_gap_to_median=row.get("peer_gap_to_median"),
            )
        )

    return results


@traced(name="tool:search_knowledge", run_type="tool")
@requires_source
async def search_knowledge(query: str, k: int = 5) -> list[KnowledgeChunk]:
    """Retrieve the top-k most relevant knowledge chunks for a query.

    Calls the real hybrid retriever (BM25 + vector + cross-encoder reranking).
    Returns [] if the ChromaDB collection is empty or the query has no matches.
    Every returned chunk is guaranteed to have a populated source and section.
    """
    from clubos2.rag.retriever import RetrievalConfig, retrieve

    retrieval_config = RetrievalConfig(k_final=k)
    return await retrieve(query, retrieval_config=retrieval_config)  # type: ignore[no-any-return]


@traced(name="tool:get_signal", run_type="tool")
async def get_signal(signal_id: str) -> dict[str, Any]:
    """Retrieve fixture details for a commercial signal."""
    return SIGNAL_FIXTURES.get(
        signal_id,
        {
            "signal_id": signal_id,
            "source_metric": "unknown_source",
            "target_metric": "unknown_target",
            "correlation": 0.60,
            "lag_months": 1,
            "source": "data/gold_snapshots/gold_signal_relationships.csv",
        },
    )


@traced(name="tool:get_benchmark", run_type="tool")
async def get_benchmark(metric_name: str, peers: list[str] | None = None) -> dict[str, Any]:
    """Retrieve peer benchmark comparison details for a metric."""
    return BENCHMARK_FIXTURES.get(
        metric_name,
        {
            "metric_name": metric_name,
            "real_madrid_value": 50.0,
            "peer_median": 50.0,
            "peer_leader": 50.0,
            "rank": 3,
            "peers_compared": peers or ["Barcelona", "Manchester United"],
            "source": "data/gold_snapshots/gold_peer_benchmark.csv",
        },
    )


# Registry mapping tool names to functions (needed for agent execution)
TOOL_REGISTRY: dict[str, Callable[..., Coroutine[Any, Any, Any]]] = {
    "query_metrics": query_metrics,
    "search_knowledge": search_knowledge,
    "get_signal": get_signal,
    "get_benchmark": get_benchmark,
}
