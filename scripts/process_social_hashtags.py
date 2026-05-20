#!/usr/bin/env python3
"""
Explode and aggregate hashtag performance from gold_social_posts.

Reads: data/gold_snapshots/gold_social_posts.csv
Writes: data/gold_snapshots/gold_social_hashtags.csv

Explodes hashtags column (one row per hashtag per post).
Groups by: hashtag, platform, month
Classifies: is_branded, is_event, is_player, is_farewell
"""

import csv
from pathlib import Path
from collections import defaultdict
from typing import Dict, List


# Classification lists from prompt
BRANDED_HASHTAGS = {
    'rmcity', 'realmadrid', 'madridistas', 'halamadrideternamente'
}

EVENT_HASHTAGS = {
    'ucl', 'laliga', 'elclasico', 'championsleague', 'nationsleague',
    'ucldraw', 'supercopa', 'copadelrey', 'fifaclubworldcup'
}

PLAYER_HASHTAGS = {
    'mbappe', 'vinicius', 'bellingham', 'modric', 'rodrygo',
    'valverde', 'tchouameni', 'rudiger', 'militao', 'alaba',
    'courtois', 'camavinga', 'guler', 'mbappé', 'welcometrent',
    'joselu', 'kroos', 'nacho', 'brahim', 'carvajal'
}


def classify_hashtag(hashtag: str) -> Dict[str, bool]:
    """Classify hashtag into categories."""
    ht_lower = hashtag.lower()

    is_branded = ht_lower in BRANDED_HASHTAGS
    is_event = ht_lower in EVENT_HASHTAGS or any(e in ht_lower for e in EVENT_HASHTAGS)
    is_player = ht_lower in PLAYER_HASHTAGS
    is_farewell = ht_lower.startswith('gracias')  # #graciasluka, #graciascarlo, etc.

    return {
        'is_branded': is_branded,
        'is_event': is_event,
        'is_player': is_player,
        'is_farewell': is_farewell
    }


def main():
    # Paths
    project_root = Path(__file__).parent.parent
    source_file = project_root / "data" / "gold_snapshots" / "gold_social_posts.csv"
    output_file = project_root / "data" / "gold_snapshots" / "gold_social_hashtags.csv"

    print(f"Reading: {source_file}")

    # Explode hashtags and group
    groups = defaultdict(list)
    total_posts = 0
    total_hashtags_exploded = 0

    with open(source_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            total_posts += 1
            hashtags_str = row.get('hashtags', '')

            if not hashtags_str:
                continue

            # Split comma-separated hashtags
            hashtags = hashtags_str.split(',')

            for hashtag in hashtags:
                hashtag = hashtag.strip()
                if not hashtag:
                    continue

                total_hashtags_exploded += 1

                # Grouping key
                key = (
                    hashtag,
                    row.get('platform', ''),
                    row.get('month', '')
                )

                groups[key].append({
                    'post_id': row.get('post_id', ''),
                    'engagement': int(row.get('engagement', 0))
                })

    print(f"Total posts: {total_posts:,}")
    print(f"Total hashtags exploded: {total_hashtags_exploded:,}")
    print(f"Unique (hashtag, platform, month) groups: {len(groups):,}")

    # Compute aggregates
    results = []

    for key, posts in groups.items():
        hashtag, platform, month = key

        post_count = len(posts)
        engagements = [p['engagement'] for p in posts]

        total_engagement = sum(engagements)
        avg_engagement = total_engagement / post_count if post_count > 0 else 0
        posts_with_this_hashtag = post_count

        # Classify hashtag
        classification = classify_hashtag(hashtag)

        results.append({
            'hashtag': f'#{hashtag}',  # Add # prefix for display
            'platform': platform,
            'month': month,
            'post_count': post_count,
            'total_engagement': total_engagement,
            'avg_engagement_per_post': round(avg_engagement, 2),
            'posts_with_this_hashtag': posts_with_this_hashtag,
            'is_branded': classification['is_branded'],
            'is_event': classification['is_event'],
            'is_player': classification['is_player'],
            'is_farewell': classification['is_farewell']
        })

    # Sort by total_engagement descending (most impactful first)
    results.sort(key=lambda r: r['total_engagement'], reverse=True)

    # Write output
    if results:
        fieldnames = [
            'hashtag', 'platform', 'month', 'post_count', 'total_engagement',
            'avg_engagement_per_post', 'posts_with_this_hashtag',
            'is_branded', 'is_event', 'is_player', 'is_farewell'
        ]

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        print(f"✓ gold_social_hashtags.csv: {len(results):,} rows written")
    else:
        print("⚠ No hashtag data to write")


if __name__ == "__main__":
    main()
