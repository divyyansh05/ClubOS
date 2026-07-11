"""Tests for the real query_metrics tool (Prompt 3.4).

Tests use:
- A real seeded semantic layer (DuckDB in tmp_path) for registry lookups.
- A real GoldClient pointing at the actual DATA/gold_snapshots/ CSVs.
- No mocking of the Gold layer — we verify against real data.
"""

from __future__ import annotations

import os

import pytest

from clubos2.tools.errors import MetricNotFoundError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_registry(db_url: str) -> None:
    """Bootstrap and seed the semantic layer registry into a test DuckDB."""
    from clubos2.semantic_layer.db import bootstrap_db
    from clubos2.semantic_layer.seed import run_seed

    bootstrap_db(db_url)
    run_seed(dry_run=False, database_url=db_url)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_query_metrics_returns_real_data(tmp_path):
    """streaming_daily_users should return rows with a canonical gold.* source."""
    db_url = f"duckdb:///{tmp_path}/test_semantic.duckdb"
    _seed_registry(db_url)

    # Patch env so lookup.py uses our test DB
    with (
        pytest.MonkeyPatch().context() as mp,
    ):
        mp.setenv("SEMANTIC_DB_URL", db_url)

        # Force cache refresh so it uses the test DB
        from clubos2.semantic_layer import lookup

        lookup.refresh_cache(db_url)

        from clubos2.tools.registry import query_metrics

        rows = await query_metrics("streaming_daily_users")

    assert len(rows) > 0, "Expected at least one row for streaming_daily_users"

    row = rows[0]
    assert row.metric_name == "streaming_daily_users"
    assert row.value > 0, "metric_value should be non-zero"
    VALID = ("gold.", "skills.", "metric_registry", "watchdog_alerts", "investigations", "web_search:")
    assert any(row.source.startswith(p) for p in VALID), f"Non-canonical source: {row.source}"
    # Source order is registry-declared (preferred_source). kpi_health is the
    # default authoritative source since the 2026-07 cross-source audit.
    assert row.source in ("gold.kpi_health", "gold.priority_board"), \
        f"Expected a gold source, got: {row.source}"


@pytest.mark.asyncio
async def test_query_metrics_source_is_real_csv_path(tmp_path):
    """MetricRow.source must be canonical (gold.<table>), not a file path."""
    db_url = f"duckdb:///{tmp_path}/test_semantic.duckdb"
    _seed_registry(db_url)

    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("SEMANTIC_DB_URL", db_url)
        from clubos2.semantic_layer import lookup

        lookup.refresh_cache(db_url)

        from clubos2.tools.registry import query_metrics

        rows = await query_metrics("ecommerce_net_sales")

    VALID = ("gold.", "skills.", "metric_registry", "watchdog_alerts", "investigations", "web_search:")
    for row in rows:
        assert any(row.source.startswith(p) for p in VALID), (
            f"Non-canonical source: {row.source!r}"
        )


@pytest.mark.asyncio
async def test_query_metrics_with_month_filter(tmp_path):
    """Filtering by month should return only that month's rows."""
    db_url = f"duckdb:///{tmp_path}/test_semantic.duckdb"
    _seed_registry(db_url)

    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("SEMANTIC_DB_URL", db_url)
        from clubos2.semantic_layer import lookup

        lookup.refresh_cache(db_url)

        from clubos2.tools.registry import query_metrics

        rows = await query_metrics("streaming_daily_users", month="2025-11-01")

    # If this month exists in Gold, every row should be for that month
    if rows:
        for row in rows:
            assert row.month == "2025-11-01", f"Unexpected month: {row.month}"


@pytest.mark.asyncio
async def test_query_metrics_unknown_metric_raises_error(tmp_path):
    """Unknown metric name must raise MetricNotFoundError with suggestions."""
    db_url = f"duckdb:///{tmp_path}/test_semantic.duckdb"
    _seed_registry(db_url)

    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("SEMANTIC_DB_URL", db_url)
        from clubos2.semantic_layer import lookup

        lookup.refresh_cache(db_url)

        from clubos2.tools.registry import query_metrics

        with pytest.raises(MetricNotFoundError) as exc_info:
            await query_metrics("nonexistent_metric_xyz")

    err = exc_info.value
    assert err.metric_name == "nonexistent_metric_xyz"
    # Error message should be human-readable
    assert "nonexistent_metric_xyz" in str(err)


@pytest.mark.asyncio
async def test_query_metrics_ambiguous_name_raises_with_suggestions(tmp_path):
    """'conversion_rate' (no platform) should raise with registry suggestions."""
    db_url = f"duckdb:///{tmp_path}/test_semantic.duckdb"
    _seed_registry(db_url)

    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("SEMANTIC_DB_URL", db_url)
        from clubos2.semantic_layer import lookup

        lookup.refresh_cache(db_url)

        from clubos2.tools.registry import query_metrics

        with pytest.raises(MetricNotFoundError) as exc_info:
            # 'conversion_rate' is not a registered metric_name; the registry has
            # 'ecommerce_conversion_rate' and 'streaming_conversion_rate'
            await query_metrics("conversion_rate")

    err = exc_info.value
    # Should suggest the platform-specific variants from registry
    assert (
        len(err.suggestions_from_registry) > 0 or len(err.suggestions_from_gold) > 0
    ), "Expected at least some suggestions from registry or Gold"


@pytest.mark.asyncio
async def test_query_metrics_all_rows_have_source(tmp_path):
    """Every returned MetricRow must have a populated source field."""
    db_url = f"duckdb:///{tmp_path}/test_semantic.duckdb"
    _seed_registry(db_url)

    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("SEMANTIC_DB_URL", db_url)
        from clubos2.semantic_layer import lookup

        lookup.refresh_cache(db_url)

        from clubos2.tools.registry import query_metrics

        rows = await query_metrics("streaming_daily_users")

    for row in rows:
        assert row.source, "source must not be empty"
        assert row.metric_name, "metric_name must not be empty"
        assert row.month, "month must not be empty"
