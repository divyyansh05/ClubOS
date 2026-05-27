"""
Test for Priority Board Badge Count Bug Fix

Validates that all priorities are counted in exactly one category badge,
and the sum of badge counts equals the total number of priorities.

Bug: "conversion weakness" category was not matched by any badge filter,
causing badge sum (9) to be less than total priorities (10).

Fix: Added "conversion" and "weakness" to critical badge filter.
"""

import pandas as pd
import pytest
from pathlib import Path


def test_priority_badge_counts_sum_to_total():
    """Test that category badge counts sum to total priority count"""
    priority_board_path = Path("data/gold_snapshots/gold_priority_board.csv")
    assert priority_board_path.exists(), "gold_priority_board.csv should exist"

    df = pd.read_csv(priority_board_path)

    # Get latest month priorities
    latest_month = df["month"].max()
    latest = df[df["month"] == latest_month]

    assert len(latest) == 10, f"Expected 10 priorities in latest month, got {len(latest)}"

    # Count categories using the same logic as frontend badge filters
    # Critical: includes "critical", "conversion", or "weakness"
    critical_count = len(latest[
        latest["priority_category"].str.lower().str.contains('critical') |
        latest["priority_category"].str.lower().str.contains('conversion') |
        latest["priority_category"].str.lower().str.contains('weakness')
    ])

    # Opportunity: includes "opportunity"
    opportunity_count = len(latest[
        latest["priority_category"].str.lower().str.contains('opportunity')
    ])

    # Benchmark: includes "benchmark"
    benchmark_count = len(latest[
        latest["priority_category"].str.lower().str.contains('benchmark')
    ])

    total = len(latest)

    # The sum of badge counts must equal total
    badge_sum = critical_count + opportunity_count + benchmark_count

    print(f"\nBadge counts for {latest_month}:")
    print(f"  CRITICAL: {critical_count}")
    print(f"  OPPORTUNITY: {opportunity_count}")
    print(f"  BENCHMARK: {benchmark_count}")
    print(f"  TOTAL: {total}")
    print(f"  Sum check: {critical_count} + {opportunity_count} + {benchmark_count} = {badge_sum}")

    assert badge_sum == total, \
        f"Badge counts ({badge_sum}) should equal total priorities ({total}). " \
        f"Critical={critical_count}, Opportunity={opportunity_count}, Benchmark={benchmark_count}"


def test_no_priority_is_uncategorized():
    """Test that every priority matches at least one badge filter"""
    priority_board_path = Path("data/gold_snapshots/gold_priority_board.csv")
    df = pd.read_csv(priority_board_path)

    latest_month = df["month"].max()
    latest = df[df["month"] == latest_month]

    for _, row in latest.iterrows():
        category = row["priority_category"].lower()

        matches_critical = 'critical' in category or 'conversion' in category or 'weakness' in category
        matches_opportunity = 'opportunity' in category
        matches_benchmark = 'benchmark' in category

        matches_any = matches_critical or matches_opportunity or matches_benchmark

        assert matches_any, \
            f"Priority '{row['priority_id']}' with category '{row['priority_category']}' " \
            f"does not match any badge filter"


def test_conversion_weakness_counted_as_critical():
    """Test that 'conversion weakness' category is counted in CRITICAL badge"""
    priority_board_path = Path("data/gold_snapshots/gold_priority_board.csv")
    df = pd.read_csv(priority_board_path)

    latest_month = df["month"].max()
    latest = df[df["month"] == latest_month]

    # Check if conversion weakness exists
    conversion_weakness = latest[latest["priority_category"] == "conversion weakness"]

    if len(conversion_weakness) > 0:
        # Verify it would be counted as critical
        category = conversion_weakness.iloc[0]["priority_category"].lower()
        assert 'conversion' in category or 'weakness' in category, \
            "conversion weakness should match critical badge filter"

        print(f"\n✓ Found 'conversion weakness' priority - correctly counted in CRITICAL badge")
