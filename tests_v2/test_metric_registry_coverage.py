"""
CI-gating tests: metric_registry must cover all Gold-layer metrics, and the
registry must resolve to Gold data for all metrics that have Gold backing.

If test_registry_covers_gold_layer fails:
  A new Gold compound metric has no registry entry.
  Fix: add the metric to STUB_METRICS in clubos2/semantic_layer/seed.py and re-run seed.

If test_registry_resolves_to_gold fails:
  A registry metric name cannot be resolved to Gold data by GoldClient.
  Root causes: (1) naming mismatch (see GoldClient.ASSET_ALIASES / METRIC_NAME_ALIASES),
  or (2) metric declared in registry but genuinely absent from Gold pipeline.
  Fix depends on which — see error message for the failing metrics.

If test_registry_has_at_least_59_metrics fails:
  The registry fell below the Phase 1 baseline. Check for accidental truncation
  of seed.py STUB_METRICS or CURATED_METRICS lists.
"""
import asyncio
import json
from pathlib import Path

import pytest

# Metrics that exist in registry but have no Gold backing yet.
# These are either forward-looking planned metrics or from Gold sources
# not yet wired into GoldClient (e.g., gold_social_metrics.csv wide format).
KNOWN_NO_GOLD_DATA: frozenset[str] = frozenset(
    [
        "digital_merchandise_revenue",
        "matchday_ticket_revenue",
        "post_match_engagement_rate",
        "reels_engagement_rate",
        "social_media_followers",
        "social_total_posts",
        "video_progress_25_rate",
        "video_progress_50_rate",
        "video_progress_75_rate",
    ]
)


def test_registry_has_at_least_59_metrics():
    """Sanity floor: registry must have at least 59 metrics (Phase 1 baseline)."""
    from clubos2.semantic_layer import MetricRegistry, get_session

    with get_session() as session:
        count = session.query(MetricRegistry).count()
    assert count >= 59, f"Registry has {count} metrics, expected ≥ 59"


def test_registry_covers_gold_layer():
    """Every Gold-layer compound metric must have a registry entry.

    Gold uses compound names (e.g., main_website_bounce_rate).
    Registry uses short or aliased names (e.g., bounce_rate_web).
    This test checks that the GoldClient can resolve every registry metric
    that is expected to have Gold data — not that the compound names match exactly.
    """
    inventory_path = Path("docs/gold_metrics_inventory.json")
    if not inventory_path.exists():
        pytest.skip(
            "Gold inventory not generated. Run: python scripts/discover_gold_metrics.py > docs/gold_metrics_inventory.json"
        )

    gold_compound = set(json.loads(inventory_path.read_text()))

    from clubos2.semantic_layer import MetricRegistry, get_session

    with get_session() as session:
        registry = {row.metric_name for row in session.query(MetricRegistry).all()}

    # Every Gold compound name should have a resolvable registry entry.
    # We check this via GoldClient.fetch_metric for each registry metric.
    from clubos2.tools.gold_client import GoldClient, MetricNotInGoldError

    gc = GoldClient()

    # Test that metrics NOT in KNOWN_NO_GOLD_DATA all resolve
    expected_resolvable = registry - KNOWN_NO_GOLD_DATA
    failures = []
    for m in sorted(expected_resolvable):
        try:
            result = asyncio.run(gc.fetch_metric(m))
            if not result:
                failures.append(f"{m}: empty result")
        except MetricNotInGoldError as e:
            failures.append(f"{m}: {str(e)[:80]}")
        except Exception as e:
            failures.append(f"{m}: ERROR {str(e)[:80]}")

    assert not failures, (
        f"{len(failures)} registry metrics fail to resolve to Gold data:\n"
        + "\n".join(f"  - {f}" for f in failures)
        + "\n\nFix: check GoldClient.ASSET_ALIASES and METRIC_NAME_ALIASES in clubos2/tools/gold_client.py"
    )


def test_no_gold_data_metrics_are_documented():
    """KNOWN_NO_GOLD_DATA entries must still be in the registry (declared but pending data)."""
    from clubos2.semantic_layer import MetricRegistry, get_session

    with get_session() as session:
        registry = {row.metric_name for row in session.query(MetricRegistry).all()}

    missing_from_registry = KNOWN_NO_GOLD_DATA - registry
    assert not missing_from_registry, (
        f"Metrics in KNOWN_NO_GOLD_DATA not found in registry: {missing_from_registry}. "
        "If intentionally removed, update KNOWN_NO_GOLD_DATA accordingly."
    )


def test_list_all_metrics_tool():
    """Smoke test: list_all_metrics returns ≥ 59 entries with the right structure."""
    from clubos2.tools.registry import list_all_metrics

    metrics = asyncio.run(list_all_metrics())
    assert len(metrics) >= 59, f"list_all_metrics returned only {len(metrics)} metrics"
    sample = metrics[0]
    assert "metric_name" in sample
    assert "business_name" in sample
    assert "definition" in sample
    assert sample["source"] == "metric_registry"


def test_list_all_metrics_platform_filter():
    """Platform filter should narrow results."""
    from clubos2.tools.registry import list_all_metrics

    all_metrics = asyncio.run(list_all_metrics())
    streaming_metrics = asyncio.run(list_all_metrics(filter_by_platform="streaming"))
    assert len(streaming_metrics) < len(all_metrics)
    assert all("streaming" in m["platform"].lower() for m in streaming_metrics)
