#!/usr/bin/env python3
"""
Process Peer Social Data for V1.6.3

Reads the source social media CSV containing data for 10 elite European clubs,
aggregates by club and month, computes key social benchmarking metrics, and
writes to gold_peer_social_benchmark.csv.

Output: 120 rows (10 clubs × 12 months for 2025)
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# Paths
SOURCE_CSV = Path(__file__).parent.parent / "data" / "source" / "Dataset_Social_Media_Analytics.csv"
OUTPUT_CSV = Path(__file__).parent.parent / "data" / "gold_snapshots" / "gold_peer_social_benchmark.csv"

# Club name mapping (source → output)
CLUB_NAME_MAP = {
    "Real Madrid CF": "real_madrid",
    "FC Barcelona": "fc_barcelona",
    "Liverpool FC": "liverpool",
    "Manchester City FC": "man_city",
    "Manchester United FC": "man_united",
    "Arsenal FC": "arsenal",
    "Chelsea FC": "chelsea",
    "FC Bayern": "fc_bayern",
    "PSG": "psg",
    "Juventus FC": "juventus",
}


def process_peer_social_data():
    """Main processing function"""

    print(f"Reading source data from {SOURCE_CSV}...")
    df = pd.read_csv(SOURCE_CSV)

    print(f"Source data shape: {df.shape}")
    print(f"Entities found: {sorted(df['Entity'].unique())}")

    # Filter to only the 10 clubs we want
    df = df[df['Entity'].isin(CLUB_NAME_MAP.keys())].copy()
    print(f"After filtering to 10 clubs: {df.shape}")

    # Parse date column (day-first format: DD/MM/YYYY)
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
    df['month'] = df['Date'].dt.to_period('M').astype(str) + '-01'

    # Count unique scene types per post for content diversity
    # Scenes column contains comma-separated scene types
    def count_scenes(scenes_str):
        if pd.isna(scenes_str) or scenes_str == '':
            return 0
        return len(set(str(scenes_str).split(',')))

    df['scene_count'] = df['Scenes'].apply(count_scenes)

    # Group by Entity (club) and month
    print("Aggregating by club and month...")

    agg_dict = {
        'Engagement': 'sum',  # total_engagement
        'ID': 'count',  # total_posts (count of posts)
        'Medium': lambda x: x.value_counts().index[0] if len(x) > 0 else None,  # top platform
        'scene_count': 'sum',  # sum of unique scene types across all posts
    }

    monthly = df.groupby(['Entity', 'month']).agg(agg_dict).reset_index()
    monthly.columns = ['Entity', 'month', 'total_engagement', 'total_posts', 'top_platform', 'total_scene_types']

    # Compute derived metrics
    monthly['avg_engagement_per_post'] = monthly['total_engagement'] / monthly['total_posts']

    # Content diversity score = unique scene types / total posts (capped at 1.0)
    monthly['content_diversity_score'] = (monthly['total_scene_types'] / monthly['total_posts']).clip(upper=1.0)

    # Posting frequency per day (posts per month / ~30 days)
    monthly['posting_frequency_per_day'] = monthly['total_posts'] / 30.0

    # For Instagram engagement rate, we need to get Instagram-specific data
    # Re-aggregate Instagram only
    df_instagram = df[df['Medium'] == 'Instagram'].copy()
    instagram_monthly = df_instagram.groupby(['Entity', 'month']).agg({
        'Engagement': 'sum',
        'Follower Count': 'mean',  # Average follower count across posts in the month
    }).reset_index()
    instagram_monthly.columns = ['Entity', 'month', 'instagram_engagement', 'instagram_followers']
    instagram_monthly['instagram_engagement_rate'] = (
        instagram_monthly['instagram_engagement'] / instagram_monthly['instagram_followers']
    ).fillna(0)

    # Merge Instagram metrics
    monthly = monthly.merge(
        instagram_monthly[['Entity', 'month', 'instagram_engagement_rate']],
        on=['Entity', 'month'],
        how='left'
    )
    monthly['instagram_engagement_rate'] = monthly['instagram_engagement_rate'].fillna(0)

    # Map club names
    monthly['club_name'] = monthly['Entity'].map(CLUB_NAME_MAP)

    # Select and reorder columns
    output = monthly[[
        'month',
        'club_name',
        'avg_engagement_per_post',
        'total_posts',
        'total_engagement',
        'instagram_engagement_rate',
        'content_diversity_score',
        'posting_frequency_per_day',
    ]].copy()

    # Sort by month and club
    output = output.sort_values(['month', 'club_name']).reset_index(drop=True)

    print(f"\nOutput shape: {output.shape} (expected 120 rows for 10 clubs × 12 months)")
    print(f"Months covered: {sorted(output['month'].unique())}")
    print(f"Clubs: {sorted(output['club_name'].unique())}")

    # Validate
    month_count = output['month'].nunique()
    club_count = output['club_name'].nunique()
    expected_rows = month_count * club_count
    actual_rows = len(output)

    print(f"\nValidation:")
    print(f"  Unique months: {month_count}")
    print(f"  Unique clubs: {club_count}")
    print(f"  Expected rows: {expected_rows}")
    print(f"  Actual rows: {actual_rows}")

    if actual_rows != expected_rows:
        print(f"  ⚠️  WARNING: Row count mismatch! Some club-month combinations missing.")
        missing = expected_rows - actual_rows
        print(f"  Missing {missing} rows")

    # Show sample Real Madrid stats
    rm = output[output['club_name'] == 'real_madrid']
    if len(rm) > 0:
        avg_eng = rm['avg_engagement_per_post'].mean()
        print(f"\nReal Madrid avg engagement per post (2025 mean): {avg_eng:,.0f}")

    # Show ranking for avg_engagement_per_post in latest month
    latest_month = output['month'].max()
    latest = output[output['month'] == latest_month].copy()
    latest = latest.sort_values('avg_engagement_per_post', ascending=False).reset_index(drop=True)
    latest['rank'] = range(1, len(latest) + 1)

    print(f"\nLatest month ({latest_month}) avg_engagement_per_post ranking:")
    for _, row in latest.iterrows():
        marker = " ← Real Madrid" if row['club_name'] == 'real_madrid' else ""
        print(f"  #{row['rank']}: {row['club_name']:15s}  {row['avg_engagement_per_post']:>10,.0f}{marker}")

    # Write output
    print(f"\nWriting to {OUTPUT_CSV}...")
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_CSV, index=False)
    print("✅ Done!")


if __name__ == "__main__":
    process_peer_social_data()
