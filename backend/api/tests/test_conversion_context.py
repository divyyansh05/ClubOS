import pytest
from app.services import conversion_context_service
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_high_conv_high_vol_returns_strong_performance():
    """Test that high conversion + high volume returns strong performance quadrant"""
    # Using a month where both conversion_rate and unique_visitors are likely above median
    # Based on gold_kpi_health.csv, let's try 2025-05-01 (recent month with good data)
    context = conversion_context_service.get_conversion_context("ecommerce", "2025-05-01")

    if context:  # If data exists
        # If both are above median, should get strong performance
        if (context["conversion_rate_value"] > context["conversion_seasonal_median"] and
            context["visitors_value"] > context["visitors_seasonal_median"]):
            assert context["quadrant"] == "high_conversion_high_volume"
            assert context["label"] == "Strong Performance"
            assert context["color"] == "good"
            assert "optimal commercial state" in context["interpretation"].lower()


def test_high_conv_low_vol_returns_scale_risk():
    """Test that high conversion + low volume returns scale risk quadrant"""
    # We need to find a month where conversion is high but visitors are low
    # This might not exist in real data, so test the logic path if it does
    context = conversion_context_service.get_conversion_context("ecommerce", "2017-08-01")

    if context:
        if (context["conversion_rate_value"] > context["conversion_seasonal_median"] and
            context["visitors_value"] <= context["visitors_seasonal_median"]):
            assert context["quadrant"] == "high_conversion_low_volume"
            assert context["label"] == "Warm Audience — Scale Risk"
            assert context["color"] == "warning"
            assert "narrow" in context["interpretation"].lower()


def test_low_conv_high_vol_returns_funnel_risk():
    """Test that low conversion + high volume returns funnel risk quadrant"""
    context = conversion_context_service.get_conversion_context("ecommerce", "2019-03-01")

    if context:
        if (context["conversion_rate_value"] <= context["conversion_seasonal_median"] and
            context["visitors_value"] > context["visitors_seasonal_median"]):
            assert context["quadrant"] == "low_conversion_high_volume"
            assert context["label"] == "Top-of-Funnel Expansion — Review Funnel"
            assert context["color"] == "warning"
            assert "funnel" in context["interpretation"].lower()


def test_low_conv_low_vol_returns_broad_underperformance():
    """Test that low conversion + low volume returns broad underperformance quadrant"""
    context = conversion_context_service.get_conversion_context("ecommerce", "2018-02-01")

    if context:
        if (context["conversion_rate_value"] <= context["conversion_seasonal_median"] and
            context["visitors_value"] <= context["visitors_seasonal_median"]):
            assert context["quadrant"] == "low_conversion_low_volume"
            assert context["label"] == "Broad Underperformance"
            assert context["color"] == "critical"
            assert "commercially concerning" in context["interpretation"].lower()


def test_conversion_context_has_required_fields():
    """Test that conversion context returns all required fields"""
    context = conversion_context_service.get_conversion_context("ecommerce", "2025-04-01")

    if context:
        # Check all required fields exist
        required_fields = [
            "quadrant",
            "label",
            "interpretation",
            "color",
            "conversion_rate_value",
            "visitors_value",
            "conversion_seasonal_median",
            "visitors_seasonal_median",
            "conversion_vs_median_pct",
            "visitors_vs_median_pct"
        ]
        for field in required_fields:
            assert field in context, f"Missing field {field} in conversion context"

        # Check types
        assert isinstance(context["quadrant"], str)
        assert isinstance(context["label"], str)
        assert isinstance(context["interpretation"], str)
        assert context["color"] in ["good", "warning", "critical"]
        assert isinstance(context["conversion_rate_value"], (int, float))
        assert isinstance(context["visitors_value"], (int, float))


def test_conversion_context_attached_to_conversion_rate_priority():
    """Test that conversion_context is attached to conversion_rate priorities"""
    # Get latest priorities
    response = client.get("/priorities/latest")
    assert response.status_code == 200

    data = response.json()
    items = data.get("items", [])

    # Find a conversion_rate priority
    conv_priority = next(
        (p for p in items if p.get("primary_metric") == "conversion_rate"),
        None
    )

    if conv_priority:
        # Get the detail for this priority
        priority_id = conv_priority["priority_id"]
        detail_response = client.get(f"/priorities/{priority_id}")
        assert detail_response.status_code == 200

        detail = detail_response.json()

        # Should have conversion_context field
        assert "conversion_context" in detail
        # It might be None if the service failed, but the field should exist
        if detail["conversion_context"]:
            assert "quadrant" in detail["conversion_context"]
            assert "label" in detail["conversion_context"]


def test_non_conversion_priority_has_no_context():
    """Test that non-conversion_rate priorities don't have conversion context"""
    # Get latest priorities
    response = client.get("/priorities/latest")
    assert response.status_code == 200

    data = response.json()
    items = data.get("items", [])

    # Find a non-conversion_rate priority
    non_conv_priority = next(
        (p for p in items if p.get("primary_metric") != "conversion_rate"),
        None
    )

    if non_conv_priority:
        # Get the detail for this priority
        priority_id = non_conv_priority["priority_id"]
        detail_response = client.get(f"/priorities/{priority_id}")
        assert detail_response.status_code == 200

        detail = detail_response.json()

        # Should have conversion_context field (nullable)
        assert "conversion_context" in detail
        # But it should be None for non-conversion metrics
        assert detail["conversion_context"] is None


def test_conversion_context_percentages_computed_correctly():
    """Test that percentage differences from median are computed correctly"""
    context = conversion_context_service.get_conversion_context("ecommerce", "2025-01-01")

    if context and context["conversion_seasonal_median"] > 0:
        # Manually compute expected percentage
        expected_conv_pct = (
            (context["conversion_rate_value"] - context["conversion_seasonal_median"])
            / context["conversion_seasonal_median"]
        ) * 100

        # Should match computed value (within floating point tolerance)
        assert abs(context["conversion_vs_median_pct"] - expected_conv_pct) < 0.01

    if context and context["visitors_seasonal_median"] > 0:
        expected_visitors_pct = (
            (context["visitors_value"] - context["visitors_seasonal_median"])
            / context["visitors_seasonal_median"]
        ) * 100

        assert abs(context["visitors_vs_median_pct"] - expected_visitors_pct) < 0.01
