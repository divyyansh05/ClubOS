from __future__ import annotations

import json

from sqlalchemy import select

from clubos2.semantic_layer import MetricRegistry, get_session
from clubos2.semantic_layer.seed import CURATED_METRICS, run_seed


def test_seed_basic_population(tmp_path):
    """Verify that run_seed populates the database and does not raise errors."""
    db_file = tmp_path / "test_seed.duckdb"
    test_db_url = f"duckdb:///{db_file}"

    # Run seed
    rows_processed = run_seed(dry_run=False, database_url=test_db_url)
    assert rows_processed == 76

    with get_session(test_db_url) as session:
        # Check that we have exactly 62 rows in the table
        total_rows = session.query(MetricRegistry).count()
        assert total_rows == 76


def test_seed_curated_metrics_non_null(tmp_path):
    """Verify the top 10 fully-curated metrics have all fields populated correctly."""
    db_file = tmp_path / "test_seed.duckdb"
    test_db_url = f"duckdb:///{db_file}"

    run_seed(dry_run=False, database_url=test_db_url)

    curated_names = {m["metric_name"] for m in CURATED_METRICS}
    assert len(curated_names) == 10

    with get_session(test_db_url) as session:
        for name in curated_names:
            stmt = select(MetricRegistry).where(MetricRegistry.metric_name == name)
            metric = session.execute(stmt).scalar_one_or_none()

            assert metric is not None
            assert metric.definition is not None
            assert len(metric.definition) > 10
            assert metric.platform is not None
            assert metric.polarity in ("positive", "negative")
            assert metric.unit is not None
            assert metric.typical_range is not None

            # Verify query examples are valid JSON
            assert metric.valid_query_examples is not None
            valid_examples = json.loads(metric.valid_query_examples)
            assert isinstance(valid_examples, list)
            assert len(valid_examples) >= 3

            assert metric.invalid_query_examples is not None
            invalid_examples = json.loads(metric.invalid_query_examples)
            assert isinstance(invalid_examples, list)
            assert len(invalid_examples) >= 1


def test_conversion_rate_ambiguity_references(tmp_path):
    """Verify conversion_rate_ecommerce and conversion_rate_streaming reference each other."""
    db_file = tmp_path / "test_seed.duckdb"
    test_db_url = f"duckdb:///{db_file}"

    run_seed(dry_run=False, database_url=test_db_url)

    with get_session(test_db_url) as session:
        ecomm_stmt = select(MetricRegistry).where(
            MetricRegistry.metric_name == "conversion_rate_ecommerce"
        )
        ecomm = session.execute(ecomm_stmt).scalar_one_or_none()

        stream_stmt = select(MetricRegistry).where(
            MetricRegistry.metric_name == "conversion_rate_streaming"
        )
        stream = session.execute(stream_stmt).scalar_one_or_none()

        assert ecomm is not None
        assert stream is not None

        assert "conversion_rate_streaming" in ecomm.ambiguous_with
        assert "conversion_rate_ecommerce" in stream.ambiguous_with
        assert ecomm.disambiguation_rule is not None
        assert stream.disambiguation_rule is not None


def test_seed_idempotency(tmp_path):
    """Verify that re-running the seed does not duplicate rows."""
    db_file = tmp_path / "test_seed.duckdb"
    test_db_url = f"duckdb:///{db_file}"

    # Run seed once
    run_seed(dry_run=False, database_url=test_db_url)
    with get_session(test_db_url) as session:
        count_first = session.query(MetricRegistry).count()
        assert count_first == 76

    # Run seed a second time
    run_seed(dry_run=False, database_url=test_db_url)
    with get_session(test_db_url) as session:
        count_second = session.query(MetricRegistry).count()
        assert count_second == 76


def test_net_sales_seasonal_note(tmp_path):
    """Verify that net_sales row has the January seasonal note populated."""
    db_file = tmp_path / "test_seed.duckdb"
    test_db_url = f"duckdb:///{db_file}"

    run_seed(dry_run=False, database_url=test_db_url)

    with get_session(test_db_url) as session:
        stmt = select(MetricRegistry).where(MetricRegistry.metric_name == "net_sales")
        net_sales = session.execute(stmt).scalar_one_or_none()

        assert net_sales is not None
        assert net_sales.seasonal_note is not None
        assert "January always dips 15-20% post-holiday" in net_sales.seasonal_note
