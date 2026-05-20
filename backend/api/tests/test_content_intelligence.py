"""
Tests for Content Intelligence service (V1.6.4).

Content-to-commercial correlation engine testing.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import content_intelligence_service

client = TestClient(app)


def test_compute_content_correlations_returns_list():
    """Test that compute_content_commercial_correlations returns a list."""
    signals = content_intelligence_service.compute_content_commercial_correlations()
    assert isinstance(signals, list)


def test_all_correlations_exceed_minimum_threshold():
    """Test all returned correlations exceed 0.45 threshold."""
    signals = content_intelligence_service.compute_content_commercial_correlations()

    for signal in signals:
        assert abs(signal.correlation) >= 0.45, (
            f"Signal {signal.content_type} → {signal.commercial_metric} "
            f"has correlation {signal.correlation:.2f}, below 0.45 threshold"
        )


def test_content_signal_has_required_fields():
    """Test ContentSignal has all required fields."""
    signals = content_intelligence_service.compute_content_commercial_correlations()

    if not signals:
        pytest.skip("No signals found in test data")

    signal = signals[0]

    # Required fields
    assert hasattr(signal, "content_type")
    assert hasattr(signal, "commercial_metric")
    assert hasattr(signal, "commercial_asset")
    assert hasattr(signal, "correlation")
    assert hasattr(signal, "lag_months")
    assert hasattr(signal, "direction")
    assert hasattr(signal, "interpretation")
    assert hasattr(signal, "strength_label")
    assert hasattr(signal, "confidence_note")
    assert hasattr(signal, "avg_content_engagement")
    assert hasattr(signal, "sample_size_months")

    # Type checks
    assert isinstance(signal.content_type, str)
    assert isinstance(signal.commercial_metric, str)
    assert isinstance(signal.correlation, float)
    assert signal.lag_months in [0, 1, 2]
    assert signal.direction in ["positive", "negative"]
    assert signal.strength_label in ["Strong", "Moderate", "Weak"]


def test_content_intelligence_endpoint_returns_200():
    """Test GET /social/content-intelligence returns 200."""
    response = client.get("/social/content-intelligence")
    assert response.status_code == 200

    data = response.json()
    assert "latest_month" in data
    assert "signals" in data
    assert "summary" in data
    assert isinstance(data["signals"], list)


def test_summary_endpoint_returns_strongest_correlations():
    """Test GET /social/content-intelligence/summary returns summary."""
    response = client.get("/social/content-intelligence/summary")
    assert response.status_code == 200

    data = response.json()
    assert "total_correlations_found" in data
    assert "avg_correlation_strength" in data
    assert "most_predictive_content_type" in data
    assert "most_influenced_commercial_metric" in data

    # If signals exist, strongest_signal should be populated
    if data["total_correlations_found"] > 0:
        assert "strongest_signal" in data
        assert data["strongest_signal"] is not None


def test_month_endpoint_returns_content_breakdown():
    """Test GET /social/content-intelligence/{month} returns monthly breakdown."""
    # Use a known month from the data
    response = client.get("/social/content-intelligence/2025-01")
    assert response.status_code == 200

    data = response.json()
    assert "month" in data
    assert "content_performances" in data
    assert "commercial_outcomes" in data
    assert "matching_correlations" in data

    assert isinstance(data["content_performances"], list)
    assert isinstance(data["commercial_outcomes"], list)
    assert isinstance(data["matching_correlations"], list)


def test_month_endpoint_404_for_invalid_month():
    """Test GET /social/content-intelligence/{month} returns 404 for invalid month."""
    response = client.get("/social/content-intelligence/1999-01")
    assert response.status_code == 404


def test_correlation_strength_labels_are_correct():
    """Test that strength labels match correlation thresholds."""
    signals = content_intelligence_service.compute_content_commercial_correlations()

    for signal in signals:
        abs_corr = abs(signal.correlation)

        if abs_corr > 0.65:
            assert signal.strength_label == "Strong", (
                f"Signal with correlation {abs_corr:.2f} should be 'Strong'"
            )
        elif abs_corr >= 0.55:
            assert signal.strength_label == "Moderate", (
                f"Signal with correlation {abs_corr:.2f} should be 'Moderate'"
            )
        else:
            assert signal.strength_label == "Weak", (
                f"Signal with correlation {abs_corr:.2f} should be 'Weak'"
            )


def test_interpretation_field_is_non_empty():
    """Test that all signals have non-empty interpretation."""
    signals = content_intelligence_service.compute_content_commercial_correlations()

    for signal in signals:
        assert signal.interpretation, (
            f"Signal {signal.content_type} → {signal.commercial_metric} "
            f"has empty interpretation"
        )
        assert len(signal.interpretation) > 50, (
            f"Signal interpretation too short: {signal.interpretation}"
        )


def test_content_types_are_valid():
    """Test that all content_type values are from expected set."""
    signals = content_intelligence_service.compute_content_commercial_correlations()

    valid_content_types = [
        "goal_celebration",
        "training",
        "score_graphic",
        "player_arrival",
        "lineup_graphic",
        "birthday",
        "game_preview"
    ]

    for signal in signals:
        assert signal.content_type in valid_content_types, (
            f"Unexpected content_type: {signal.content_type}"
        )


def test_commercial_assets_are_valid():
    """Test that all commercial_asset values are from expected set."""
    signals = content_intelligence_service.compute_content_commercial_correlations()

    valid_assets = ["ecommerce", "main_website", "streaming", "fan_app"]

    for signal in signals:
        assert signal.commercial_asset in valid_assets, (
            f"Unexpected commercial_asset: {signal.commercial_asset}"
        )


def test_sample_size_is_sufficient():
    """Test that all signals have sufficient sample size (at least 6 months)."""
    signals = content_intelligence_service.compute_content_commercial_correlations()

    for signal in signals:
        assert signal.sample_size_months >= 6, (
            f"Signal {signal.content_type} → {signal.commercial_metric} "
            f"has insufficient sample size: {signal.sample_size_months}"
        )
