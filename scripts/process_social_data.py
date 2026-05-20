#!/usr/bin/env python3
"""
Process Social Media Analytics data into Gold table format.

Transforms raw social media CSV (478K+ rows) into monthly aggregated
gold_social_metrics.csv (12 rows, one per month 2025).

Usage:
    python scripts/process_social_data.py
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
SOURCE_FILE = PROJECT_ROOT / "data/source/Dataset_Social_Media_Analytics.csv"
OUTPUT_FILE = PROJECT_ROOT / "data/gold_snapshots/gold_social_metrics.csv"

def parse_date_to_month(date_str):
    """Parse DD/MM/YYYY to YYYY-MM-01 format."""
    try:
        dt = pd.to_datetime(date_str, format='%d/%m/%Y')
        return dt.strftime('%Y-%m-01')
    except:
        return None

def normalize_platform(medium):
    """Normalize platform names."""
    medium_lower = str(medium).lower()
    if 'instagram' in medium_lower:
        return 'instagram'
    elif 'tiktok' in medium_lower or 'tik tok' in medium_lower:
        return 'tiktok'
    elif 'twitter' in medium_lower or medium_lower == 'x':
        return 'x'
    elif 'facebook' in medium_lower:
        return 'facebook'
    elif 'youtube' in medium_lower:
        return 'youtube'
    else:
        return 'other'

def normalize_scene(scene_str):
    """Extract primary scene/content type."""
    if pd.isna(scene_str):
        return 'other'
    scene_lower = str(scene_str).lower()

    # Map to standardized content types
    if 'goal' in scene_lower or 'celebration' in scene_lower:
        return 'goal_celebration'
    elif 'training' in scene_lower or 'practice' in scene_lower:
        return 'training'
    elif 'score' in scene_lower or 'scoreboard' in scene_lower or 'result' in scene_lower:
        return 'score_graphic'
    elif 'arrival' in scene_lower or 'player arrival' in scene_lower:
        return 'player_arrival'
    elif 'lineup' in scene_lower or 'starting' in scene_lower:
        return 'lineup_graphic'
    elif 'birthday' in scene_lower or 'anniversary' in scene_lower:
        return 'birthday'
    elif 'preview' in scene_lower or 'match preview' in scene_lower:
        return 'game_preview'
    else:
        return 'other'

def detect_language_account(username):
    """Detect language from account username."""
    if pd.isna(username):
        return 'english'

    username_lower = str(username).lower()

    # Spanish keywords
    if any(word in username_lower for word in ['español', 'spanish', 'c.f.', 'cf']):
        return 'spanish'
    # Arabic keywords
    elif any(word in username_lower for word in ['arabic', 'عربي', 'ar']):
        return 'arabic'
    # French keywords
    elif any(word in username_lower for word in ['français', 'french', 'fr']):
        return 'french'
    # Default to English for main accounts
    elif 'real madrid' in username_lower and not any(word in username_lower for word in ['español', 'arabic', 'french']):
        return 'english'
    else:
        return 'other'

def main():
    print(f"Reading source CSV from: {SOURCE_FILE}")

    # Read CSV with proper encoding
    df = pd.read_csv(SOURCE_FILE, encoding='utf-8-sig')

    print(f"Total rows: {len(df):,}")

    # Filter to Real Madrid CF only
    df = df[df['Entity'] == 'Real Madrid CF'].copy()
    print(f"Real Madrid CF rows: {len(df):,}")

    # Parse date and create month column
    df['month'] = df['Date'].apply(parse_date_to_month)
    df = df[df['month'].notna()]  # Drop rows with invalid dates

    # Normalize platforms and scenes
    df['platform'] = df['Medium'].apply(normalize_platform)
    df['content_type'] = df['Scenes'].apply(normalize_scene)
    df['language_account'] = df['Username'].apply(detect_language_account)

    # Convert numeric columns (handle commas in numbers)
    numeric_cols = ['Engagement', 'Likes, Reactions, +1\'s', 'Comments, Replies',
                    'Reposts, Retweets', 'Post Saves', 'Estimated Views',
                    'Estimated Impressions', 'Follower Count']

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

    # Rename columns for easier access
    df = df.rename(columns={
        'Engagement': 'engagement',
        'Likes, Reactions, +1\'s': 'likes',
        'Comments, Replies': 'comments',
        'Reposts, Retweets': 'reposts',
        'Post Saves': 'saves',
        'Estimated Views': 'views',
        'Estimated Impressions': 'impressions',
        'Follower Count': 'followers'
    })

    print(f"Rows with valid dates: {len(df):,}")
    print(f"Months covered: {df['month'].nunique()}")
    print(f"Date range: {df['month'].min()} to {df['month'].max()}")

    # Group by month and compute aggregations
    monthly_metrics = []

    for month in sorted(df['month'].unique()):
        month_df = df[df['month'] == month]

        # Overall metrics
        total_posts = len(month_df)
        total_engagement = month_df['engagement'].sum()
        avg_engagement_per_post = total_engagement / total_posts if total_posts > 0 else 0
        total_likes = month_df['likes'].sum()
        total_comments = month_df['comments'].sum()
        total_reposts = month_df['reposts'].sum()
        total_saves = month_df['saves'].sum()
        total_estimated_views = month_df['views'].sum()
        total_estimated_impressions = month_df['impressions'].sum()

        # Per-platform metrics
        platform_metrics = {}
        for platform in ['instagram', 'tiktok', 'x', 'facebook', 'youtube']:
            platform_df = month_df[month_df['platform'] == platform]
            platform_posts = len(platform_df)
            platform_engagement = platform_df['engagement'].sum()
            platform_avg = platform_engagement / platform_posts if platform_posts > 0 else 0
            max_followers = platform_df['followers'].max() if len(platform_df) > 0 else 1
            platform_rate = (platform_engagement / max_followers) if max_followers > 0 else 0

            platform_metrics[f'{platform}_posts'] = platform_posts
            platform_metrics[f'{platform}_engagement'] = platform_engagement
            platform_metrics[f'{platform}_avg_engagement'] = platform_avg

            # Engagement rate only for platforms with data
            if platform in ['instagram', 'tiktok', 'x', 'facebook']:
                platform_metrics[f'{platform}_engagement_rate'] = platform_rate

        # Content type performance
        content_metrics = {}
        for content_type in ['goal_celebration', 'training', 'score_graphic',
                            'player_arrival', 'lineup_graphic', 'birthday', 'game_preview']:
            content_df = month_df[month_df['content_type'] == content_type]
            content_posts = len(content_df)
            content_avg = content_df['engagement'].mean() if content_posts > 0 else 0
            content_metrics[f'{content_type}_avg_engagement'] = content_avg

        # Language account breakdown
        lang_metrics = {}
        for lang in ['spanish', 'english', 'arabic', 'french', 'other']:
            lang_df = month_df[month_df['language_account'] == lang]
            lang_metrics[f'{lang}_account_engagement'] = lang_df['engagement'].sum()

        # Computed metrics
        spanish_engagement = lang_metrics['spanish_account_engagement']
        total_non_spanish = total_engagement - spanish_engagement
        international_engagement_ratio = (total_non_spanish / total_engagement) if total_engagement > 0 else 0

        # Top performing platform
        platform_avgs = {
            'instagram': platform_metrics['instagram_avg_engagement'],
            'tiktok': platform_metrics['tiktok_avg_engagement'],
            'x': platform_metrics['x_avg_engagement'],
            'facebook': platform_metrics['facebook_avg_engagement'],
            'youtube': platform_metrics['youtube_avg_engagement']
        }
        top_performing_platform = max(platform_avgs, key=platform_avgs.get)

        # Top performing content type
        content_avgs = {k.replace('_avg_engagement', ''): v for k, v in content_metrics.items()}
        top_performing_content_type = max(content_avgs, key=content_avgs.get) if content_avgs else 'other'

        # Build row
        row = {
            'month': month,
            'asset_name': 'social_media',
            'total_posts': total_posts,
            'total_engagement': total_engagement,
            'avg_engagement_per_post': avg_engagement_per_post,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_reposts': total_reposts,
            'total_saves': total_saves,
            'total_estimated_views': total_estimated_views,
            'total_estimated_impressions': total_estimated_impressions,
            **platform_metrics,
            **content_metrics,
            **lang_metrics,
            'international_engagement_ratio': international_engagement_ratio,
            'top_performing_platform': top_performing_platform,
            'top_performing_content_type': top_performing_content_type
        }

        monthly_metrics.append(row)

    # Create output DataFrame
    output_df = pd.DataFrame(monthly_metrics)

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    output_df.to_csv(OUTPUT_FILE, index=False)

    print(f"\n✅ Output written to: {OUTPUT_FILE}")
    print(f"✅ Rows generated: {len(output_df)}")
    print(f"✅ Columns: {len(output_df.columns)}")
    print(f"\nFirst row preview:")
    print(output_df.head(1).T)

    return output_df

if __name__ == "__main__":
    result = main()
