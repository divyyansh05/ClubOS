from __future__ import annotations

import logging
import time
from typing import Any

from pydantic import BaseModel

from clubos2.observability.tracing import traced
from clubos2.semantic_layer.db import get_session
from clubos2.semantic_layer.schema import MetricRegistry, MetricRegistryRead

logger = logging.getLogger("clubos.semantic_layer.lookup")


# Pydantic model for ambiguity warnings
class AmbiguityWarning(BaseModel):
    detected_term: str  # what in the query was ambiguous
    candidate_metrics: list[str]  # the metric_names it could refer to
    default: str | None  # which metric to default to per the rule
    rule_text: str  # the human-written disambiguation_rule


# Ambiguity configs with qualifiers to resolve them
AMBIGUITY_CONFIGS: list[dict[str, Any]] = [
    {
        "terms": ["conversion rate", "conversion"],
        "candidates": ["conversion_rate_ecommerce", "conversion_rate_streaming"],
        "default": "conversion_rate_ecommerce",
        "qualifiers": {
            "conversion_rate_ecommerce": [
                "ecommerce",
                "e-commerce",
                "shop",
                "store",
                "purchase",
                "sales",
            ],
            "conversion_rate_streaming": [
                "streaming",
                "subscribe",
                "subscription",
                "video",
                "play",
            ],
        },
    },
    {
        "terms": ["daily active users", "daily users", "dau"],
        "candidates": ["streaming_daily_users", "fan_app_dau"],
        "default": "streaming_daily_users",
        "qualifiers": {
            "streaming_daily_users": ["streaming", "video", "play"],
            "fan_app_dau": ["app", "fan app", "mobile", "ios", "android"],
        },
    },
    {
        "terms": ["unique visitors", "visitors"],
        "candidates": [
            "unique_visitors_web",
            "unique_visitors_ecommerce",
            "unique_visitors_streaming",
            "unique_visitors_fan_app",
        ],
        "default": "unique_visitors_web",
        "qualifiers": {
            "unique_visitors_web": ["web", "website", "main"],
            "unique_visitors_ecommerce": ["ecommerce", "e-commerce", "shop", "store"],
            "unique_visitors_streaming": ["streaming", "video"],
            "unique_visitors_fan_app": ["app", "fan app", "mobile"],
        },
    },
    {
        "terms": ["engagement rate", "engagement"],
        "candidates": ["post_match_engagement_rate", "reels_engagement_rate"],
        "default": "post_match_engagement_rate",
        "qualifiers": {
            "post_match_engagement_rate": ["post-match", "post match", "match", "game"],
            "reels_engagement_rate": ["reels", "instagram", "video", "short"],
        },
    },
    {
        "terms": ["bounce rate", "bounce"],
        "candidates": ["bounce_rate_web", "recurrence_web"],
        "default": "bounce_rate_web",
        "qualifiers": {
            "bounce_rate_web": ["bounce"],
            "recurrence_web": ["recurrence", "recurring"],
        },
    },
]

# Module-level dictionary cache
_REGISTRY_CACHE: dict[str, MetricRegistryRead] = {}


def refresh_cache(database_url: str | None = None) -> None:
    """Refresh the in-memory cache of the metric registry from the database."""
    global _REGISTRY_CACHE
    new_cache = {}
    try:
        with get_session(database_url) as session:
            metrics = session.query(MetricRegistry).all()
            for m in metrics:
                read_model = MetricRegistryRead.model_validate(m)
                new_cache[read_model.metric_name] = read_model
        _REGISTRY_CACHE = new_cache
    except Exception as e:
        logger.warning(f"Failed to refresh metric registry cache: {e}")


# Initialize cache at module load time
try:
    refresh_cache()
except Exception:
    pass


@traced(name="semantic_layer:lookup_metric", run_type="tool")
def lookup_metric(metric_name: str) -> MetricRegistryRead | None:
    """Exact key lookup. Returns the registry row or None.

    Deterministic — same input always returns same output.
    """
    start_time = time.perf_counter()
    metric = _REGISTRY_CACHE.get(metric_name)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    if elapsed_ms > 10.0:
        logger.warning(f"lookup_metric({metric_name}) took {elapsed_ms:.2f}ms (> 10ms)")
    return metric


@traced(name="semantic_layer:lookup_metrics_by_terms", run_type="tool")
def lookup_metrics_by_terms(terms: list[str]) -> list[MetricRegistryRead]:
    """For natural-language queries: takes a list of extracted terms (e.g.

    ['conversion rate', 'eCommerce']) and returns matching registry rows. Matches
    against metric_name AND business_name (case-insensitive). Returns ALL
    matches (caller handles ambiguity).
    """
    if not terms:
        return []

    matched = []
    lower_terms = [t.lower() for t in terms]

    for metric in _REGISTRY_CACHE.values():
        name_lower = metric.metric_name.lower()
        business_lower = metric.business_name.lower()

        # Check if any term is in metric_name or business_name
        for term in lower_terms:
            if term in name_lower or term in business_lower:
                matched.append(metric)
                break  # avoid duplicate additions if multiple terms match the same metric

    return matched


@traced(name="semantic_layer:detect_ambiguity", run_type="tool")
def detect_ambiguity(query: str) -> list[AmbiguityWarning]:
    """Scans the user's query for terms that match `ambiguous_with` relationships

    in the registry. Returns warnings the Scout can use to ask clarifying
    questions OR apply default disambiguation rules.
    """
    query_lower = query.lower()
    warnings: list[AmbiguityWarning] = []

    for config in AMBIGUITY_CONFIGS:
        # Check if any term representing the ambiguity is present in the query
        matched_term = None
        for term in config["terms"]:
            if term in query_lower:
                matched_term = term
                break

        if not matched_term:
            continue

        # We matched an ambiguous term. Let's see if the qualifiers resolve it.
        matching_candidates = []
        for candidate, qualifiers in config["qualifiers"].items():
            if any(q in query_lower for q in qualifiers):
                matching_candidates.append(candidate)

        # If exactly one candidate has qualifiers matching the query, the ambiguity is resolved
        if len(matching_candidates) == 1:
            continue

        # Otherwise, the query is ambiguous.
        default_metric_name = config["default"]
        default_metric = lookup_metric(default_metric_name)
        rule_text = (
            default_metric.disambiguation_rule
            if default_metric and default_metric.disambiguation_rule
            else "No disambiguation rule found."
        )

        warnings.append(
            AmbiguityWarning(
                detected_term=matched_term,
                candidate_metrics=config["candidates"],
                default=default_metric_name,
                rule_text=rule_text,
            )
        )

    return warnings


@traced(name="semantic_layer:get_disambiguation_rule", run_type="tool")
def get_disambiguation_rule(metric_name: str) -> str | None:
    """Direct lookup of the disambiguation_rule field."""
    metric = lookup_metric(metric_name)
    return metric.disambiguation_rule if metric else None


def get_all_metrics(
    platform: str | None = None,
    polarity: str | None = None,
) -> list[MetricRegistryRead]:
    """Return all metrics from the registry cache, with optional filters.

    Args:
        platform: Filter by platform (website, ecommerce, streaming, social, app, fan_app, matchday).
        polarity: Filter by polarity (positive, negative, neutral).
    """
    results = list(_REGISTRY_CACHE.values())
    if platform:
        results = [m for m in results if m.platform and platform.lower() in m.platform.lower()]
    if polarity:
        results = [m for m in results if m.polarity and polarity.lower() in m.polarity.lower()]
    return sorted(results, key=lambda m: m.metric_name)
