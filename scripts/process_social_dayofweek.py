#!/usr/bin/env python3
"""
Aggregate gold_social_posts by day of week × platform × match moment.

Reads: data/gold_snapshots/gold_social_posts.csv
Writes: data/gold_snapshots/gold_social_dayofweek.csv

Groups by: day_of_week, platform, match_moment, media_type, variety
Computes: post counts, engagement stats, medians, averages
"""

import csv
import statistics
from pathlib import Path
from collections import defaultdict
from typing import Dict, List


def main():
    # Paths
    project_root = Path(__file__).parent.parent
    source_file = project_root / "data" / "gold_snapshots" / "gold_social_posts.csv"
    output_file = project_root / "data" / "gold_snapshots" / "gold_social_dayofweek.csv"

    print(f"Reading: {source_file}")

    # Group posts by composite key
    groups = defaultdict(list)

    with open(source_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Composite grouping key
            key = (
                row.get('day_of_week', ''),
                row.get('day_number', ''),
                row.get('platform', ''),
                row.get('match_moment', ''),
                row.get('media_type', ''),
                row.get('variety', '')
            )

            groups[key].append({
                'post_date': row.get('post_date', ''),
                'engagement': int(row.get('engagement', 0)),
                'likes': int(row.get('likes', 0)),
                'comments': int(row.get('comments', 0)),
                'reposts': int(row.get('reposts', 0))
            })

    print(f"Groups found: {len(groups):,}")

    # Compute aggregates
    results = []

    for key, posts in groups.items():
        day_of_week, day_number, platform, match_moment, media_type, variety = key

        post_count = len(posts)
        engagements = [p['engagement'] for p in posts]
        likes_list = [p['likes'] for p in posts]
        comments_list = [p['comments'] for p in posts]
        reposts_list = [p['reposts'] for p in posts]

        total_engagement = sum(engagements)
        avg_engagement = total_engagement / post_count if post_count > 0 else 0
        median_engagement = statistics.median(engagements) if engagements else 0

        # Find post with max engagement
        max_post = max(posts, key=lambda p: p['engagement']) if posts else None
        max_engagement_post_date = max_post['post_date'] if max_post else ''

        total_likes = sum(likes_list)
        total_comments = sum(comments_list)
        total_reposts = sum(reposts_list)

        avg_likes = total_likes / post_count if post_count > 0 else 0
        avg_comments = total_comments / post_count if post_count > 0 else 0
        avg_reposts = total_reposts / post_count if post_count > 0 else 0

        results.append({
            'day_of_week': day_of_week,
            'day_number': day_number,
            'platform': platform,
            'match_moment': match_moment,
            'media_type': media_type,
            'variety': variety,
            'post_count': post_count,
            'total_engagement': total_engagement,
            'avg_engagement_per_post': round(avg_engagement, 2),
            'median_engagement_per_post': round(median_engagement, 2),
            'max_engagement_post_date': max_engagement_post_date,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_reposts': total_reposts,
            'avg_likes': round(avg_likes, 2),
            'avg_comments': round(avg_comments, 2),
            'avg_reposts': round(avg_reposts, 2)
        })

    # Sort by day_number, platform for readability
    results.sort(key=lambda r: (r['day_number'], r['platform'], r['match_moment']))

    # Write output
    if results:
        fieldnames = [
            'day_of_week', 'day_number', 'platform', 'match_moment', 'media_type', 'variety',
            'post_count', 'total_engagement', 'avg_engagement_per_post',
            'median_engagement_per_post', 'max_engagement_post_date',
            'total_likes', 'total_comments', 'total_reposts',
            'avg_likes', 'avg_comments', 'avg_reposts'
        ]

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        print(f"✓ gold_social_dayofweek.csv: {len(results):,} rows written")
    else:
        print("⚠ No aggregated data to write")


if __name__ == "__main__":
    main()
