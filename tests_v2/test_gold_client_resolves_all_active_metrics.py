"""CI protection: every is_active=True registry metric must resolve via GoldClient.

This test catches latent bugs like streaming_daily_users at CI time rather
than during frontend testing. It exercises the full resolution path including
prefix-split, suffix-split, and direct matching.
"""
from __future__ import annotations

import pytest

from clubos2.semantic_layer.lookup import get_all_metrics, refresh_cache
from clubos2.tools.gold_client import GoldClient, GoldClientSettings, MetricNotInGoldError


@pytest.fixture(scope="module")
def gold_client() -> GoldClient:
    return GoldClient(GoldClientSettings(gold_snapshots_dir="./data/gold_snapshots"))


@pytest.fixture(scope="module", autouse=True)
def ensure_cache():
    refresh_cache()


@pytest.mark.asyncio
async def test_gold_client_resolves_every_active_metric(gold_client: GoldClient) -> None:
    """Every metric with is_active=True must return at least one row from GoldClient."""
    metrics = get_all_metrics()
    active = [m for m in metrics if getattr(m, "is_active", True)]

    assert len(active) > 0, "No active metrics found — registry empty or refresh failed"

    failures: list[str] = []
    for m in active:
        try:
            rows = await gold_client.fetch_metric(m.metric_name)
            if not rows:
                failures.append(f"{m.metric_name}: returned 0 rows (expected ≥1)")
        except MetricNotInGoldError as e:
            failures.append(f"{m.metric_name}: MetricNotInGoldError — {e}")
        except Exception as e:
            failures.append(f"{m.metric_name}: unexpected error — {type(e).__name__}: {e}")

    if failures:
        pytest.fail(
            f"{len(failures)}/{len(active)} active metrics failed GoldClient resolution:\n"
            + "\n".join(f"  - {f}" for f in failures)
        )


@pytest.mark.asyncio
async def test_inactive_metrics_are_documented(gold_client: GoldClient) -> None:
    """Inactive metrics should be documented in registry and fail gracefully."""
    metrics = get_all_metrics()
    inactive = [m for m in metrics if not getattr(m, "is_active", True)]

    # All inactive metrics should fail gold resolution — this is expected
    for m in inactive:
        try:
            rows = await gold_client.fetch_metric(m.metric_name)
            if rows:
                # Unexpected: inactive metric found in gold — should be re-activated
                pytest.fail(
                    f"{m.metric_name} is marked is_active=False but resolved in gold "
                    f"({len(rows)} rows). Update seed.py to set is_active=True."
                )
        except MetricNotInGoldError:
            pass  # Expected: inactive metric correctly absent from gold


@pytest.mark.asyncio
async def test_streaming_daily_users_resolves(gold_client: GoldClient) -> None:
    """Regression: streaming_daily_users was the first compound-name bug found."""
    rows = await gold_client.fetch_metric("streaming_daily_users")
    assert len(rows) > 0, "streaming_daily_users returned 0 rows"
    assert rows[0]["metric_value"] is not None or rows[0].get("metric_value") is not None


@pytest.mark.asyncio
async def test_ecommerce_metrics_resolve(gold_client: GoldClient) -> None:
    """Regression: suffix-style ecommerce metrics must resolve via _split_metric_name suffix logic."""
    for metric_name in ["conversion_rate_ecommerce", "purchases_ecommerce", "items_ecommerce"]:
        rows = await gold_client.fetch_metric(metric_name)
        assert len(rows) > 0, f"{metric_name} returned 0 rows"


@pytest.mark.asyncio
async def test_web_metrics_resolve(gold_client: GoldClient) -> None:
    """Regression: _web suffix metrics must resolve via main_website ASSET_ALIAS."""
    for metric_name in ["bounce_rate_web", "unique_visitors_web", "visits_web"]:
        rows = await gold_client.fetch_metric(metric_name)
        assert len(rows) > 0, f"{metric_name} returned 0 rows"
