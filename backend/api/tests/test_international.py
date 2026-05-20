"""
Tests for V1.6.6 — International Audience Intelligence.

Tests:
- get_international_breakdown returns all languages
- pct_of_total sums to 100
- get_international_trend returns 12 months
- market growth ranking is sorted
- international endpoints return 200
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import social_service

client = TestClient(app)


def test_international_breakdown_returns_all_languages():
    """Verify international breakdown includes all language markets."""
    result = social_service.get_international_breakdown()

    assert "language_markets" in result
    languages = [m["language"] for m in result["language_markets"]]

    # Must include Spanish, English, Arabic, French, Other
    assert "Spanish" in languages
    assert "English" in languages
    assert "Arabic" in languages
    assert "French" in languages
    assert "Other" in languages


def test_pct_of_total_sums_to_100():
    """Verify percentages sum to approximately 100%."""
    result = social_service.get_international_breakdown()

    language_markets = result["language_markets"]
    total_pct = sum(m["pct_of_total_engagement"] for m in language_markets)

    # Allow small floating point error
    assert 99.9 <= total_pct <= 100.1


def test_international_trend_returns_12_months():
    """Verify trend endpoint returns 12 months of data."""
    result = social_service.get_international_trend()

    assert "trend" in result
    assert len(result["trend"]) == 12

    # Each month should have required fields
    for point in result["trend"]:
        assert "month" in point
        assert "spanish_engagement" in point
        assert "english_engagement" in point
        assert "arabic_engagement" in point
        assert "french_engagement" in point
        assert "other_engagement" in point
        assert "international_ratio" in point


def test_market_growth_ranking_is_sorted():
    """Verify market growth ranking is sorted by MoM change descending."""
    result = social_service.get_market_growth_ranking()

    assert "rankings" in result
    rankings = result["rankings"]

    # Check sorted by mom_change_pct descending
    for i in range(len(rankings) - 1):
        assert rankings[i]["mom_change_pct"] >= rankings[i + 1]["mom_change_pct"]


def test_international_endpoint_returns_200():
    """Verify /social/international endpoint works."""
    response = client.get("/social/international")
    assert response.status_code == 200

    data = response.json()
    assert "month" in data
    assert "language_markets" in data
    assert "total_international_engagement" in data
    assert "international_engagement_ratio" in data


def test_international_trend_endpoint_returns_200():
    """Verify /social/international/trend endpoint works."""
    response = client.get("/social/international/trend")
    assert response.status_code == 200

    data = response.json()
    assert "trend" in data
    assert len(data["trend"]) == 12


def test_international_correlation_endpoint_returns_200():
    """Verify /social/international/correlation endpoint works."""
    response = client.get("/social/international/correlation")
    assert response.status_code == 200

    data = response.json()
    assert "correlations" in data
    assert "strongest_correlation" in data


def test_market_growth_endpoint_returns_200():
    """Verify /social/international/growth endpoint works."""
    response = client.get("/social/international/growth")
    assert response.status_code == 200

    data = response.json()
    assert "month" in data
    assert "rankings" in data


def test_language_breakdown_has_required_fields():
    """Verify each language market has required fields."""
    result = social_service.get_international_breakdown()

    for market in result["language_markets"]:
        assert "language" in market
        assert "monthly_engagement" in market
        assert "pct_of_total_engagement" in market
        # mom_change can be None for first month
        assert "mom_change" in market


def test_international_engagement_ratio_is_valid():
    """Verify international_engagement_ratio is between 0 and 1."""
    result = social_service.get_international_breakdown()

    ratio = result["international_engagement_ratio"]
    assert 0 <= ratio <= 1
