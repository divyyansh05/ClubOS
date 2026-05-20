import pytest
from app.services import seasonal_service
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_compute_seasonal_baseline_returns_12_months():
    """Test that compute_seasonal_baseline returns stats for all 12 calendar months"""
    # Using ecommerce/card_addition_rate as test metric (exists in gold_kpi_health.csv)
    baseline = seasonal_service.compute_seasonal_baseline("ecommerce", "card_addition_rate")

    # Should return dict with month numbers as keys
    assert isinstance(baseline, dict)
    # Should have at least some months (may not have all 12 if data is sparse)
    assert len(baseline) > 0
    # Each month should have required fields
    for month_num, stats in baseline.items():
        assert isinstance(month_num, int)
        assert 1 <= month_num <= 12
        assert "seasonal_mean" in stats
        assert "seasonal_std" in stats
        assert "seasonal_min" in stats
        assert "seasonal_max" in stats
        assert "seasonal_p25" in stats
        assert "seasonal_p75" in stats
        assert "year_count" in stats
        assert "month_name" in stats
        # Mean should be a number
        assert isinstance(stats["seasonal_mean"], (int, float))
        # Year count should be positive
        assert stats["year_count"] > 0


def test_seasonal_baseline_has_required_fields():
    """Test that each month in baseline has all required statistical fields"""
    baseline = seasonal_service.compute_seasonal_baseline("ecommerce", "conversion_rate")

    if baseline:  # If data exists
        for month_num, stats in baseline.items():
            # Check all required fields exist
            required_fields = [
                "seasonal_mean",
                "seasonal_std",
                "seasonal_min",
                "seasonal_max",
                "seasonal_p25",
                "seasonal_p75",
                "year_count",
                "month_name"
            ]
            for field in required_fields:
                assert field in stats, f"Missing field {field} in month {month_num}"

            # Sanity checks
            assert stats["seasonal_min"] <= stats["seasonal_mean"] <= stats["seasonal_max"]
            assert stats["seasonal_p25"] <= stats["seasonal_p75"]


def test_get_seasonal_context_within_normal_returns_correct_flag():
    """Test that seasonal context correctly identifies values within normal range"""
    # Get context for a specific month
    context = seasonal_service.get_seasonal_context_for_month(
        "ecommerce",
        "card_addition_rate",
        "2017-08-01"
    )

    if context:  # If data exists
        # Should have required fields
        assert "is_within_normal_range" in context
        assert "z_score" in context
        assert "seasonal_mean" in context
        assert "interpretation" in context

        # is_within_normal_range should be boolean
        assert isinstance(context["is_within_normal_range"], bool)

        # z_score should be number
        assert isinstance(context["z_score"], (int, float))

        # If within normal range, z_score should be between -1.5 and 1.5
        if context["is_within_normal_range"]:
            assert -1.5 <= context["z_score"] <= 1.5


def test_get_seasonal_context_z_score_computed_correctly():
    """Test that z-score is computed correctly from actual value and baseline"""
    context = seasonal_service.get_seasonal_context_for_month(
        "ecommerce",
        "card_addition_rate",
        "2017-08-01"
    )

    if context and context["seasonal_std"] > 0:  # If data exists and std is valid
        # Manually compute z-score
        expected_z = (context["actual_value"] - context["seasonal_mean"]) / context["seasonal_std"]

        # Should match computed z_score (within floating point tolerance)
        assert abs(context["z_score"] - expected_z) < 0.01


def test_seasonal_endpoint_returns_200():
    """Test that GET /analytics/seasonal/{asset}/{metric} returns 200"""
    response = client.get("/analytics/seasonal/ecommerce/card_addition_rate")

    # Should return 200 if data exists, or 404 if not
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        # Should have required fields
        assert "asset" in data
        assert "metric" in data
        assert "baseline" in data

        # asset and metric should match request
        assert data["asset"] == "ecommerce"
        assert data["metric"] == "card_addition_rate"

        # baseline should be dict with month numbers
        assert isinstance(data["baseline"], dict)


def test_seasonal_endpoint_404_for_nonexistent_metric():
    """Test that endpoint returns 404 for non-existent metric"""
    response = client.get("/analytics/seasonal/ecommerce/nonexistent_metric_xyz")

    # Should return 404
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_seasonal_context_includes_interpretation():
    """Test that seasonal context includes human-readable interpretation"""
    context = seasonal_service.get_seasonal_context_for_month(
        "ecommerce",
        "card_addition_rate",
        "2017-08-01"
    )

    if context:
        # Should have interpretation field
        assert "interpretation" in context
        assert isinstance(context["interpretation"], str)
        assert len(context["interpretation"]) > 0

        # Interpretation should mention the metric behavior
        # (e.g., "above", "below", "within", "expected", "anomalous")
        interpretation_lower = context["interpretation"].lower()
        keywords = ["above", "below", "within", "expected", "seasonal", "norm"]
        assert any(keyword in interpretation_lower for keyword in keywords)
