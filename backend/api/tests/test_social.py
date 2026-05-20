"""
Tests for social media endpoints (V1.6.1).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_social_summary_returns_200():
    """Test that /social/summary returns 200 with expected fields."""
    response = client.get("/social/summary")
    assert response.status_code == 200

    data = response.json()
    assert "latest_month" in data
    assert "total_engagement" in data
    assert "avg_engagement_per_post" in data
    assert "instagram_engagement_rate" in data
    assert "international_engagement_ratio" in data
    assert "total_posts" in data
    assert "top_performing_platform" in data
    assert "top_performing_content_type" in data


def test_social_monthly_returns_12_rows():
    """Test that /social/monthly returns 12 months of data."""
    response = client.get("/social/monthly")
    assert response.status_code == 200

    data = response.json()
    assert "months" in data
    assert "total_engagement" in data
    assert "avg_engagement_per_post" in data
    assert "total_posts" in data

    # Should have 12 months for 2025
    assert len(data["months"]) == 12
    assert len(data["total_engagement"]) == 12
    assert len(data["avg_engagement_per_post"]) == 12
    assert len(data["total_posts"]) == 12


def test_social_platforms_returns_platform_breakdown():
    """Test that /social/platforms/{month} returns per-platform data."""
    response = client.get("/social/platforms/2025-01")
    assert response.status_code == 200

    data = response.json()
    assert "month" in data
    assert "platforms" in data

    platforms = data["platforms"]
    assert len(platforms) == 5  # Instagram, TikTok, X, Facebook, YouTube

    platform_names = [p["platform"] for p in platforms]
    assert "instagram" in platform_names
    assert "tiktok" in platform_names
    assert "x" in platform_names
    assert "facebook" in platform_names
    assert "youtube" in platform_names

    # Check structure of first platform
    first_platform = platforms[0]
    assert "platform" in first_platform
    assert "posts" in first_platform
    assert "engagement" in first_platform
    assert "avg_engagement" in first_platform


def test_social_content_returns_scene_data():
    """Test that /social/content/{month} returns content type performance."""
    response = client.get("/social/content/2025-01")
    assert response.status_code == 200

    data = response.json()
    assert "month" in data
    assert "content_types" in data

    content_types = data["content_types"]
    assert len(content_types) == 7  # 7 content types tracked

    # Check structure
    first_content = content_types[0]
    assert "content_type" in first_content
    assert "avg_engagement" in first_content


def test_social_metrics_in_metric_dictionary():
    """
    Test that social metrics were added to metric_dictionary.json.

    This test reads the metric dictionary JSON directly to verify
    the new metrics have correct polarity values.
    """
    import json
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent.parent
    metric_dict_path = project_root / "databricks/seeds/metric_dictionary.json"

    with open(metric_dict_path, "r") as f:
        metric_dict = json.load(f)

    # Check social metrics exist with correct polarity
    assert "total_engagement" in metric_dict
    assert metric_dict["total_engagement"]["polarity"] == 1

    assert "avg_engagement_per_post" in metric_dict
    assert metric_dict["avg_engagement_per_post"]["polarity"] == 1

    assert "engagement_rate" in metric_dict
    assert metric_dict["engagement_rate"]["polarity"] == 1

    assert "instagram_engagement" in metric_dict
    assert metric_dict["instagram_engagement"]["polarity"] == 1

    assert "total_posts" in metric_dict
    assert metric_dict["total_posts"]["polarity"] == 0

    assert "international_engagement_ratio" in metric_dict
    assert metric_dict["international_engagement_ratio"]["polarity"] == 1

    assert "total_estimated_views" in metric_dict
    assert metric_dict["total_estimated_views"]["polarity"] == 1


def test_social_platforms_404_for_invalid_month():
    """Test that requesting an invalid month returns 404."""
    response = client.get("/social/platforms/2099-12")
    assert response.status_code == 404


def test_social_content_404_for_invalid_month():
    """Test that requesting an invalid month returns 404."""
    response = client.get("/social/content/2099-12")
    assert response.status_code == 404
