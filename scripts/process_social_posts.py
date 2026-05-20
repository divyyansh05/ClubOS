#!/usr/bin/env python3
"""
Process source social media data into post-level gold table.

Reads: data/source/Dataset_Social_Media_Analytics.csv
Writes: data/gold_snapshots/gold_social_posts.csv

Filters to Entity == "Real Madrid CF" and extracts:
- Post metadata (id, platform, media type, variety)
- Post content (text truncated to 500 chars, hashtags extracted)
- Temporal data (date, day of week, month)
- Match moment classification (based on Scenes field)
- Engagement metrics (engagement, likes, comments, reposts, saves, views, impressions)
"""

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def extract_hashtags(text: str) -> str:
    """Extract all hashtags from post text, return as comma-separated lowercase string."""
    if not text:
        return ""

    # Match words starting with #
    hashtags = re.findall(r'#(\w+)', text)
    # Lowercase and deduplicate
    unique_hashtags = list(dict.fromkeys([h.lower() for h in hashtags]))
    return ",".join(unique_hashtags)


def classify_match_moment(scene: str) -> str:
    """Classify match moment based on Scenes field."""
    if not scene:
        return "other"

    scene_lower = scene.lower()

    # Pre-match
    pre_match_scenes = [
        'game preview', 'pre-game warmup', 'lineup graphic',
        'player arrival', 'global start time'
    ]
    for s in pre_match_scenes:
        if s in scene_lower:
            return "pre_match"

    # During match
    during_match_scenes = [
        'score graphic', 'action', 'goal celebration',
        'action, goal celebration', 'substitution', 'goal graphic'
    ]
    for s in during_match_scenes:
        if s in scene_lower:
            return "during_match"

    # Post-match
    post_match_scenes = ['post-game congrats', 'post-game']
    for s in post_match_scenes:
        if s in scene_lower:
            return "post_match"

    # Non-matchday
    non_matchday_scenes = [
        'training', 'birthday', 'press conference',
        'quote graphic', 'dressing room'
    ]
    for s in non_matchday_scenes:
        if s in scene_lower:
            return "non_matchday"

    return "other"


def parse_date(date_str: str) -> Dict[str, str]:
    """Parse DD/MM/YYYY date and extract day_of_week, day_number, month."""
    try:
        # Parse DD/MM/YYYY format
        dt = datetime.strptime(date_str, "%d/%m/%Y")

        # Day of week (Monday, Tuesday, etc.)
        day_of_week = dt.strftime("%A")

        # Day number (1=Monday, 7=Sunday)
        day_number = dt.isoweekday()

        # Month in YYYY-MM format
        month = dt.strftime("%Y-%m")

        # Keep original date format
        post_date = date_str

        return {
            "post_date": post_date,
            "day_of_week": day_of_week,
            "day_number": str(day_number),
            "month": month
        }
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
        return {
            "post_date": date_str,
            "day_of_week": "",
            "day_number": "",
            "month": ""
        }


def safe_int(value: str) -> int:
    """Convert string to int, return 0 if empty/invalid."""
    try:
        return int(float(value)) if value else 0
    except (ValueError, TypeError):
        return 0


def main():
    # Paths
    project_root = Path(__file__).parent.parent
    source_file = project_root / "data" / "source" / "Dataset_Social_Media_Analytics.csv"
    output_file = project_root / "data" / "gold_snapshots" / "gold_social_posts.csv"

    print(f"Reading source: {source_file}")
    print(f"Filtering to Entity == 'Real Madrid CF'...")

    # Read source and filter
    real_madrid_posts = []
    total_rows = 0

    with open(source_file, 'r', encoding='utf-8-sig') as f:  # utf-8-sig to handle BOM
        reader = csv.DictReader(f)

        for row in reader:
            total_rows += 1

            entity = row.get('Entity', '').strip()
            if entity == 'Real Madrid CF':
                # Extract and transform
                post_text = row.get('Text', '')[:500]  # Truncate to 500 chars
                hashtags = extract_hashtags(row.get('Text', ''))
                date_info = parse_date(row.get('Date', ''))
                scene = row.get('Scenes', '')
                match_moment = classify_match_moment(scene)

                real_madrid_posts.append({
                    'post_id': row.get('ID', ''),
                    'entity': row.get('Entity', ''),
                    'username': row.get('Username', ''),
                    'platform': row.get('Medium', ''),
                    'media_type': row.get('Media Type', ''),
                    'variety': row.get('Variety', ''),
                    'post_text': post_text,
                    'post_date': date_info['post_date'],
                    'day_of_week': date_info['day_of_week'],
                    'day_number': date_info['day_number'],
                    'month': date_info['month'],
                    'scene': scene,
                    'match_moment': match_moment,
                    'engagement': safe_int(row.get('Engagement', 0)),
                    'likes': safe_int(row.get("Likes, Reactions, +1's", 0)),
                    'comments': safe_int(row.get('Comments, Replies', 0)),
                    'reposts': safe_int(row.get('Reposts, Retweets', 0)),
                    'saves': safe_int(row.get('Post Saves', 0)),
                    'estimated_views': safe_int(row.get('Estimated Views', 0)),
                    'estimated_impressions': safe_int(row.get('Estimated Impressions', 0)),
                    'follower_count': safe_int(row.get('Follower Count', 0)),
                    'hashtags': hashtags
                })

    print(f"Total rows processed: {total_rows:,}")
    print(f"Real Madrid posts: {len(real_madrid_posts):,}")

    # Write output
    if real_madrid_posts:
        fieldnames = [
            'post_id', 'entity', 'username', 'platform', 'media_type', 'variety',
            'post_text', 'post_date', 'day_of_week', 'day_number', 'month',
            'scene', 'match_moment', 'engagement', 'likes', 'comments', 'reposts',
            'saves', 'estimated_views', 'estimated_impressions', 'follower_count', 'hashtags'
        ]

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(real_madrid_posts)

        print(f"✓ gold_social_posts.csv: {len(real_madrid_posts):,} rows written")
    else:
        print("⚠ No Real Madrid posts found in source data")


if __name__ == "__main__":
    main()
