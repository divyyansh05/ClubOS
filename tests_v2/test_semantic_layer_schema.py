from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import inspect, select

from clubos2.semantic_layer import (
    MetricRegistry,
    bootstrap_db,
    get_engine,
    get_session,
)


def test_bootstrap_db_file(tmp_path):
    """Verify that bootstrap_db creates the table in a file-based database."""
    db_file = tmp_path / "test_db.duckdb"
    test_db_url = f"duckdb:///{db_file}"
    engine = get_engine(test_db_url)

    # Before bootstrap, inspect should show no metric_registry table
    inspector = inspect(engine)
    assert "metric_registry" not in inspector.get_table_names()

    # Run bootstrap
    bootstrap_db(test_db_url)

    # After bootstrap, table must exist
    inspector = inspect(engine)
    assert "metric_registry" in inspector.get_table_names()


def test_bootstrap_db_idempotency(tmp_path):
    """Verify that running bootstrap_db twice on the same DB does not raise an error."""
    db_file = tmp_path / "test_db.duckdb"
    test_db_url = f"duckdb:///{db_file}"

    # First run
    bootstrap_db(test_db_url)

    # Second run should run cleanly
    bootstrap_db(test_db_url)

    engine = get_engine(test_db_url)
    inspector = inspect(engine)
    assert "metric_registry" in inspector.get_table_names()


def test_insert_and_query_metric(tmp_path):
    """Verify inserting and querying a sample row in the metric_registry table."""
    db_file = tmp_path / "test_db.duckdb"
    test_db_url = f"duckdb:///{db_file}"
    bootstrap_db(test_db_url)

    with get_session(test_db_url) as session:
        # Create a new MetricRegistry instance
        sample_metric = MetricRegistry(
            metric_name="conversion_rate_ecommerce",
            business_name="eCommerce Conversion Rate",
            definition="Ratio of completed purchases to unique sessions.",
            platform="ecommerce",
            polarity="positive",
            unit="%",
            ambiguous_with="conversion_rate_social,conversion_rate_fan_app",
            disambiguation_rule="If platform is unspecified, default to ecommerce.",
            seasonal_note="January always dips 15-20% post-holiday — not a crisis.",
            typical_range="1.5%-3.5% for Real Madrid eCommerce",
            valid_query_examples='["What is our ecommerce conversion rate?"]',
            invalid_query_examples='["How many people visited the fan app?"]',
            skill_file_path="packages/rag/skills/ecommerce.md",
            owned_by="eCommerce Team",
            last_reviewed=datetime.now(UTC),
        )

        session.add(sample_metric)

    # Query the inserted metric in a new session to ensure persistence
    with get_session(test_db_url) as session:
        stmt = select(MetricRegistry).where(
            MetricRegistry.metric_name == "conversion_rate_ecommerce"
        )
        result = session.execute(stmt).scalar_one_or_none()

        assert result is not None
        assert result.metric_name == "conversion_rate_ecommerce"
        assert result.business_name == "eCommerce Conversion Rate"
        assert result.definition == "Ratio of completed purchases to unique sessions."
        assert result.platform == "ecommerce"
        assert result.polarity == "positive"
        assert result.unit == "%"
        assert result.ambiguous_with == "conversion_rate_social,conversion_rate_fan_app"
        assert result.disambiguation_rule == "If platform is unspecified, default to ecommerce."
        assert result.seasonal_note == "January always dips 15-20% post-holiday — not a crisis."
        assert result.typical_range == "1.5%-3.5% for Real Madrid eCommerce"
        assert result.valid_query_examples == '["What is our ecommerce conversion rate?"]'
        assert result.invalid_query_examples == '["How many people visited the fan app?"]'
        assert result.skill_file_path == "packages/rag/skills/ecommerce.md"
        assert result.owned_by == "eCommerce Team"
        assert isinstance(result.last_reviewed, datetime)
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.updated_at, datetime)


def test_file_database_bootstrap(tmp_path):
    """Verify that bootstrap_db creates the parent directory and DuckDB file for path-based URL."""
    db_dir = tmp_path / "nested" / "var"
    db_file = db_dir / "test_clubos_semantic.duckdb"
    test_db_url = f"duckdb:///{db_file}"

    # Verify directory and file do not exist
    assert not db_dir.exists()

    # Run bootstrap
    bootstrap_db(test_db_url)

    # Verify directory and file were created
    assert db_dir.exists()
    assert db_file.exists()
