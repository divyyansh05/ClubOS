from __future__ import annotations

import pytest

from clubos2.semantic_layer import (
    AmbiguityWarning,
    detect_ambiguity,
    get_disambiguation_rule,
    lookup_metric,
    lookup_metrics_by_terms,
    refresh_cache,
)
from clubos2.semantic_layer.seed import run_seed


@pytest.fixture(scope="module", autouse=True)
def setup_test_db(tmp_path_factory):
    """Bootstrap and seed a module-level temporary DuckDB database for lookup tests."""
    db_file = tmp_path_factory.mktemp("db") / "test_lookup.duckdb"
    test_db_url = f"duckdb:///{db_file}"

    # Run the seed to populate the test DB with 59 metrics
    run_seed(dry_run=False, database_url=test_db_url)

    # Force lookup cache to load from this test database URL
    refresh_cache(database_url=test_db_url)

    yield test_db_url


def test_lookup_metric_exists():
    """Verify lookup_metric returns a populated MetricRegistryRead for an existing metric."""
    metric = lookup_metric("streaming_daily_users")
    assert metric is not None
    assert metric.metric_name == "streaming_daily_users"
    assert metric.business_name == "Streaming Daily Active Users"
    assert metric.platform == "streaming"
    assert metric.polarity == "positive"


def test_lookup_metric_does_not_exist():
    """Verify lookup_metric returns None for a non-existent metric."""
    metric = lookup_metric("does_not_exist")
    assert metric is None


def test_lookup_metrics_by_terms_matches():
    """Verify lookup_metrics_by_terms returns multiple matches matching terms case-insensitively."""
    matches = lookup_metrics_by_terms(["conversion"])
    metric_names = {m.metric_name for m in matches}

    assert len(matches) >= 2
    assert "conversion_rate_ecommerce" in metric_names
    assert "conversion_rate_streaming" in metric_names


def test_lookup_metrics_by_terms_empty():
    """Verify lookup_metrics_by_terms returns empty list when no terms match or terms are empty."""
    assert lookup_metrics_by_terms([]) == []
    assert lookup_metrics_by_terms(["nonexistent_term_xyz"]) == []


def test_detect_ambiguity_warning():
    """Verify detect_ambiguity returns a warning for ambiguous terms like 'conversion rate'."""
    warnings = detect_ambiguity("what is our conversion rate?")
    assert len(warnings) == 1

    warning = warnings[0]
    assert isinstance(warning, AmbiguityWarning)
    assert warning.detected_term == "conversion rate"
    assert "conversion_rate_ecommerce" in warning.candidate_metrics
    assert "conversion_rate_streaming" in warning.candidate_metrics
    assert warning.default == "conversion_rate_ecommerce"
    assert "ecommerce purchase conversions" in warning.rule_text.lower()


def test_detect_ambiguity_no_warning():
    """Verify detect_ambiguity returns an empty list when qualifier resolves the ambiguity."""
    # 'streaming' qualifier resolves DAU/daily users ambiguity
    warnings = detect_ambiguity("what is our streaming daily users?")
    assert len(warnings) == 0


def test_detect_ambiguity_unrelated():
    """Verify detect_ambiguity returns an empty list for completely unrelated queries."""
    warnings = detect_ambiguity("show me the net sales")
    assert len(warnings) == 0


def test_get_disambiguation_rule_exists():
    """Verify get_disambiguation_rule returns the correct rule text for a metric."""
    rule = get_disambiguation_rule("conversion_rate_ecommerce")
    assert rule is not None
    assert "ecommerce purchase conversions" in rule.lower()


def test_get_disambiguation_rule_none():
    """Verify get_disambiguation_rule returns None for non-existent or no-rule metrics."""
    # non-existent
    assert get_disambiguation_rule("does_not_exist") is None
    # existing but stub metric (eCommerce purchases has no disambiguation_rule seeded)
    assert get_disambiguation_rule("purchases_ecommerce") is None


def test_traced_decorators_applied():
    """Verify that every lookup function is decorated with @traced(..., run_type='tool')."""
    import sys
    from unittest.mock import MagicMock, patch

    mock_traced = MagicMock(side_effect=lambda name, run_type: lambda f: f)

    # Evict lookup modules from cache so they re-import and invoke decorators
    sys.modules.pop("clubos2.semantic_layer.lookup", None)
    sys.modules.pop("clubos2.semantic_layer", None)

    with patch("clubos2.observability.tracing.traced", mock_traced):
        import clubos2.semantic_layer.lookup as lookup  # noqa: F401

    # Check if correct arguments were passed to traced decorator
    mock_traced.assert_any_call(name="semantic_layer:lookup_metric", run_type="tool")
    mock_traced.assert_any_call(name="semantic_layer:lookup_metrics_by_terms", run_type="tool")
    mock_traced.assert_any_call(name="semantic_layer:detect_ambiguity", run_type="tool")
    mock_traced.assert_any_call(name="semantic_layer:get_disambiguation_rule", run_type="tool")
