"""
Tests for V1.8.2 Audit Fixes:
- Fix 1: Neutral polarity always returns stable
- Fix 2: Raw gap column exists in peer benchmark
- Fix 3: Expanded signal detection with provisional field
"""

import pandas as pd
from pathlib import Path


def test_neutral_polarity_always_stable():
    """Fix 1: Verify pct_android (neutral polarity) always has stable health_status."""
    df = pd.read_csv("data/gold_snapshots/gold_kpi_health.csv")
    
    # Filter for pct_android
    pct_android_rows = df[df["metric_name"] == "pct_android"]
    
    # All should be stable
    assert len(pct_android_rows) > 0, "No pct_android rows found"
    assert (pct_android_rows["health_status"] == "stable").all(), \
        "Not all pct_android rows have stable health_status"


def test_total_posts_always_stable():
    """Fix 1: Verify total_posts (neutral polarity) would be stable if present."""
    df = pd.read_csv("data/gold_snapshots/gold_kpi_health.csv")
    
    # total_posts is a social metric, not in internal metrics
    # But the logic is tested via pct_android
    # If total_posts exists, verify it's stable
    total_posts_rows = df[df["metric_name"] == "total_posts"]
    
    if len(total_posts_rows) > 0:
        assert (total_posts_rows["health_status"] == "stable").all(), \
            "Not all total_posts rows have stable health_status"


def test_raw_gap_column_exists():
    """Fix 2: Verify raw_gap_to_peer_median column exists in peer benchmark."""
    df = pd.read_csv("data/gold_snapshots/gold_peer_benchmark.csv")
    
    assert "raw_gap_to_peer_median" in df.columns, \
        "raw_gap_to_peer_median column not found in gold_peer_benchmark"


def test_raw_gap_is_simple_difference():
    """Fix 2: Verify raw_gap = rm_value - peer_median."""
    df = pd.read_csv("data/gold_snapshots/gold_peer_benchmark.csv")
    
    # Check first 10 rows
    for _, row in df.head(10).iterrows():
        expected_gap = row["rm_value"] - row["peer_median"]
        actual_gap = row["raw_gap_to_peer_median"]
        assert abs(expected_gap - actual_gap) < 0.001, \
            f"raw_gap mismatch: expected {expected_gap}, got {actual_gap}"


def test_signal_provisional_field_exists():
    """Fix 3: Verify provisional column exists in signal relationships."""
    df = pd.read_csv("data/gold_snapshots/gold_signal_relationships.csv")
    
    assert "provisional" in df.columns, \
        "provisional column not found in gold_signal_relationships"


def test_all_stored_signals_above_threshold():
    """Fix 3: Verify all signals meet correlation threshold."""
    df = pd.read_csv("data/gold_snapshots/gold_signal_relationships.csv")
    
    if len(df) > 0:
        # Internal signals should be >= 0.60
        assert (df["strength_score"].abs() >= 0.60).all(), \
            "Some signals have strength below 0.60 threshold"


def test_signal_directions_commercially_valid():
    """Fix 3: Verify signal directions are from valid config."""
    df = pd.read_csv("data/gold_snapshots/gold_signal_relationships.csv")
    
    # Valid directions from config
    valid_directions = {
        ("main_website", "ecommerce"),
        ("main_website", "streaming"),
        ("fan_app", "ecommerce"),
        ("fan_app", "streaming"),
        ("social_media", "ecommerce"),
        ("social_media", "main_website"),
        ("social_media", "streaming"),
    }
    
    if len(df) > 0:
        for _, row in df.iterrows():
            direction = (row["source_asset"], row["target_asset"])
            assert direction in valid_directions, \
                f"Invalid signal direction: {direction}"


def test_expanded_signal_coverage():
    """Fix 3: Verify signal detection found more than 2 signals."""
    df = pd.read_csv("data/gold_snapshots/gold_signal_relationships.csv")
    
    # Original implementation found only 2 signals
    # Expanded detection should find significantly more
    assert len(df) > 2, \
        f"Expected more than 2 signals, found {len(df)}"
    
    # Should have diverse source-target pairs
    unique_pairs = df[["source_asset", "target_asset"]].drop_duplicates()
    assert len(unique_pairs) >= 2, \
        "Expected at least 2 different asset pair directions"
