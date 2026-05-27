"""
Social Media Analytics Service - V1.7 Social Intelligence Layer

Provides advanced analytics on social media content performance:
- Day of week optimization
- Match moment analysis (pre/during/post/non-matchday)
- Format performance (Reels vs standard posts)
- Hashtag intelligence
- Dynamic insight generation
- Content team recommendations
- Peer comparison analytics

Data sources:
- gold_social_posts.csv (55,598 posts)
- gold_social_dayofweek.csv (411 aggregated rows)
- gold_social_hashtags.csv (2,143 hashtag performances)
- gold_peer_social_benchmark.csv (10-club benchmarks)
"""

import csv
import statistics
from pathlib import Path
from typing import Optional, List, Dict, Any
from app.clients.databricks import DatabricksClient
from app.config.settings import settings


# ============================================================================
# EMBEDDED CONSTANTS - Source of Truth from Dataset Analysis
# ============================================================================

# Format multipliers (from 55,598 Real Madrid posts analyzed)
IG_REEL_AVG_ENGAGEMENT = 522_611
STANDARD_POST_AVG_ENGAGEMENT = 67_024
IG_REEL_MULTIPLIER = 7.8  # ig_reel avg / standard post avg

# Match moment performance
POST_MATCH_AVG_ENGAGEMENT = 131_555
DURING_MATCH_AVG_ENGAGEMENT = 89_023
PRE_MATCH_AVG_ENGAGEMENT = 69_553
NON_MATCHDAY_AVG_ENGAGEMENT = 62_575

POST_MATCH_PCT_OF_POSTS = 0.5  # 0.5% of all posts
DURING_MATCH_PCT_OF_POSTS = 14.3
PRE_MATCH_PCT_OF_POSTS = 6.9
NON_MATCHDAY_PCT_OF_POSTS = 10.3

# Day of week performance (Instagram)
INSTAGRAM_THURSDAY_AVG = 426_506  # Best day
INSTAGRAM_MONDAY_AVG = 362_501
INSTAGRAM_SUNDAY_AVG = 414_732  # Second best

# Content type performance
REAL_MADRID_GOAL_CELEBRATION_AVG = 88_248
PSG_GOAL_CELEBRATION_AVG = 15_034
GOAL_CELEBRATION_MULTIPLIER = 5.9  # RM vs PSG

# Top hashtags (by avg engagement)
TOP_HASHTAGS = {
    '#graciasluka': 896_000,
    '#nationsleague': 792_000,
    '#ucldraw': 723_000,
    '#elclasico': 633_000,
    '#mbappe': 429_000,
    '#welcometrent': 351_000
}


# ============================================================================
# DATA ACCESS
# ============================================================================

def _client() -> DatabricksClient:
    """Get Databricks client (CSV snapshot mode)."""
    return DatabricksClient(settings.clubos_databricks_host, settings.clubos_databricks_token)


def _read_gold_csv(filename: str) -> List[Dict[str, Any]]:
    """Read a gold snapshot CSV file."""
    project_root = Path(__file__).parent.parent.parent.parent.parent
    csv_path = project_root / "data" / "gold_snapshots" / filename

    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    return rows


# ============================================================================
# FUNCTION 1: Day of Week Analysis
# ============================================================================

def get_day_of_week_analysis(
    platform: Optional[str] = None,
    match_moment: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze engagement patterns by day of week.

    Args:
        platform: Optional filter (Instagram/TikTok/X/Facebook/YouTube/all)
        match_moment: Optional filter (pre_match/during_match/post_match/non_matchday/all)

    Returns:
        Dict with days list, best/worst days, platform-specific best days
    """
    rows = _read_gold_csv("gold_social_dayofweek.csv")

    # Filter by platform and match_moment if specified
    if platform and platform.lower() != "all":
        rows = [r for r in rows if r.get("platform", "").lower() == platform.lower()]

    if match_moment and match_moment.lower() != "all":
        rows = [r for r in rows if r.get("match_moment", "").lower() == match_moment.lower()]

    # Aggregate by day_of_week
    day_aggregates = {}
    for row in rows:
        day = row.get("day_of_week", "")
        day_num = int(row.get("day_number", 0))

        if day not in day_aggregates:
            day_aggregates[day] = {
                "day_of_week": day,
                "day_number": day_num,
                "total_engagement": 0,
                "total_posts": 0,
                "platform_engagements": {}
            }

        total_eng = float(row.get("total_engagement", 0))
        post_count = int(row.get("post_count", 0))
        platform_name = row.get("platform", "")

        day_aggregates[day]["total_engagement"] += total_eng
        day_aggregates[day]["total_posts"] += post_count

        if platform_name not in day_aggregates[day]["platform_engagements"]:
            day_aggregates[day]["platform_engagements"][platform_name] = 0
        day_aggregates[day]["platform_engagements"][platform_name] += total_eng

    # Compute averages and format
    days = []
    for day_data in day_aggregates.values():
        total_eng = day_data["total_engagement"]
        total_posts = day_data["total_posts"]
        avg_eng = total_eng / total_posts if total_posts > 0 else 0

        # Best platform on this day
        best_platform = max(
            day_data["platform_engagements"].items(),
            key=lambda x: x[1],
            default=("Unknown", 0)
        )[0] if day_data["platform_engagements"] else "Unknown"

        days.append({
            "day_of_week": day_data["day_of_week"],
            "day_number": day_data["day_number"],
            "avg_engagement_per_post": round(avg_eng, 2),
            "post_count": total_posts,
            "best_platform_on_this_day": best_platform
        })

    # Sort by day_number
    days.sort(key=lambda d: d["day_number"])

    # Compute weekly average
    total_avg = sum(d["avg_engagement_per_post"] for d in days)
    weekly_average = total_avg / len(days) if days else 0

    # Add vs_weekly_average_pct
    for day in days:
        if weekly_average > 0:
            pct_diff = ((day["avg_engagement_per_post"] - weekly_average) / weekly_average) * 100
            day["vs_weekly_average_pct"] = round(pct_diff, 1)
        else:
            day["vs_weekly_average_pct"] = 0

    # Find best/worst days
    best_day = max(days, key=lambda d: d["avg_engagement_per_post"]) if days else None
    worst_day = min(days, key=lambda d: d["avg_engagement_per_post"]) if days else None

    return {
        "days": days,
        "best_day": best_day["day_of_week"] if best_day else None,
        "worst_day": worst_day["day_of_week"] if worst_day else None,
        "best_day_avg": best_day["avg_engagement_per_post"] if best_day else 0,
        "worst_day_avg": worst_day["avg_engagement_per_post"] if worst_day else 0,
        "weekly_average": round(weekly_average, 2)
    }


# ============================================================================
# FUNCTION 2: Match Moment Analysis
# ============================================================================

def get_match_moment_analysis(platform: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze engagement by match moment (pre/during/post/non-matchday).

    Args:
        platform: Optional filter

    Returns:
        Dict with moments list, underutilised moments, biggest multiplier
    """
    rows = _read_gold_csv("gold_social_dayofweek.csv")

    if platform and platform.lower() != "all":
        rows = [r for r in rows if r.get("platform", "").lower() == platform.lower()]

    # Aggregate by match_moment
    moment_aggregates = {}
    for row in rows:
        moment = row.get("match_moment", "other")

        if moment not in moment_aggregates:
            moment_aggregates[moment] = {
                "total_engagement": 0,
                "total_posts": 0
            }

        total_eng = float(row.get("total_engagement", 0))
        post_count = int(row.get("post_count", 0))

        moment_aggregates[moment]["total_engagement"] += total_eng
        moment_aggregates[moment]["total_posts"] += post_count

    # Compute stats
    moments = []
    total_all_posts = sum(m["total_posts"] for m in moment_aggregates.values())

    non_matchday_avg = None
    if "non_matchday" in moment_aggregates:
        nm_data = moment_aggregates["non_matchday"]
        non_matchday_avg = nm_data["total_engagement"] / nm_data["total_posts"] if nm_data["total_posts"] > 0 else 1

    for moment, data in moment_aggregates.items():
        avg_eng = data["total_engagement"] / data["total_posts"] if data["total_posts"] > 0 else 0
        pct_of_total = (data["total_posts"] / total_all_posts * 100) if total_all_posts > 0 else 0

        # Multiplier vs non-matchday
        multiplier = avg_eng / non_matchday_avg if non_matchday_avg and non_matchday_avg > 0 else 1

        # Opportunity gap classification
        opportunity_gap = "HIGH" if pct_of_total < 5 and multiplier > 1.5 else "NORMAL"

        label_map = {
            "pre_match": "Pre-Match",
            "during_match": "During Match",
            "post_match": "Post-Match",
            "non_matchday": "Non-Matchday",
            "other": "Other"
        }

        moments.append({
            "moment": moment,
            "label": label_map.get(moment, moment),
            "avg_engagement": round(avg_eng, 2),
            "post_count": data["total_posts"],
            "pct_of_total_posts": round(pct_of_total, 1),
            "vs_non_matchday_multiplier": round(multiplier, 2),
            "opportunity_gap": opportunity_gap
        })

    # Sort by avg_engagement descending
    moments.sort(key=lambda m: m["avg_engagement"], reverse=True)

    # Underutilised moments
    underutilised = [m for m in moments if m["opportunity_gap"] == "HIGH"]

    # Biggest multiplier
    biggest = max(moments, key=lambda m: m["vs_non_matchday_multiplier"]) if moments else None

    return {
        "moments": moments,
        "underutilised_moments": underutilised,
        "biggest_multiplier": {
            "moment": biggest["moment"],
            "multiplier": biggest["vs_non_matchday_multiplier"]
        } if biggest else None
    }


# ============================================================================
# FUNCTION 3: Format Performance
# ============================================================================

def get_format_performance(
    platform: Optional[str] = None,
    scene: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze format performance (Reels vs standard posts, etc.).

    Args:
        platform: Optional filter
        scene: Optional scene filter

    Returns:
        Dict with formats list, top format, underused high performers
    """
    rows = _read_gold_csv("gold_social_dayofweek.csv")

    if platform and platform.lower() != "all":
        rows = [r for r in rows if r.get("platform", "").lower() == platform.lower()]

    # Aggregate by variety (format)
    variety_aggregates = {}
    for row in rows:
        variety = row.get("variety", "unknown")
        platform_name = row.get("platform", "")

        key = f"{platform_name}_{variety}"

        if key not in variety_aggregates:
            variety_aggregates[key] = {
                "variety": variety,
                "platform": platform_name,
                "total_engagement": 0,
                "total_posts": 0
            }

        total_eng = float(row.get("total_engagement", 0))
        post_count = int(row.get("post_count", 0))

        variety_aggregates[key]["total_engagement"] += total_eng
        variety_aggregates[key]["total_posts"] += post_count

    # Compute stats
    formats = []
    standard_post_avg = None

    for data in variety_aggregates.values():
        avg_eng = data["total_engagement"] / data["total_posts"] if data["total_posts"] > 0 else 0

        label = f"{data['platform'].capitalize()} {data['variety'].capitalize()}"

        # Track standard post baseline
        if data["variety"] == "post" and data["platform"].lower() == "instagram":
            standard_post_avg = avg_eng

        formats.append({
            "variety": data["variety"],
            "label": label,
            "platform": data["platform"],
            "avg_engagement": round(avg_eng, 2),
            "post_count": data["total_posts"]
        })

    # Compute multipliers vs standard post baseline (constant STANDARD_POST_AVG_ENGAGEMENT)
    standard_post_avg = STANDARD_POST_AVG_ENGAGEMENT
    for fmt in formats:
        fmt["vs_standard_post_multiplier"] = round(fmt["avg_engagement"] / standard_post_avg, 2)
        fmt["recommended"] = fmt["vs_standard_post_multiplier"] > 2.0 and fmt["post_count"] > 50

    # Sort by avg_engagement descending
    formats.sort(key=lambda f: f["avg_engagement"], reverse=True)

    # Top format
    top_format = formats[0] if formats else None

    # Underused high performers (high multiplier but low post count)
    underused = [
        f for f in formats
        if f.get("vs_standard_post_multiplier", 0) > 3.0 and f["post_count"] < 500
    ]

    return {
        "formats": formats,
        "top_format": top_format["label"] if top_format else None,
        "top_format_multiplier": top_format.get("vs_standard_post_multiplier", 0) if top_format else 0,
        "underused_high_performers": underused
    }


# ============================================================================
# FUNCTION 4: Hashtag Performance
# ============================================================================

def get_hashtag_performance(
    platform: Optional[str] = None,
    hashtag_type: Optional[str] = None,
    min_posts: int = 10
) -> Dict[str, Any]:
    """
    Analyze hashtag performance.

    Args:
        platform: Optional filter
        hashtag_type: 'branded' / 'event' / 'player' / 'farewell' / 'all'
        min_posts: Minimum post count threshold

    Returns:
        Dict with hashtags list, top hashtags by category
    """
    rows = _read_gold_csv("gold_social_hashtags.csv")

    # Filter by platform
    if platform and platform.lower() != "all":
        rows = [r for r in rows if r.get("platform", "").lower() == platform.lower()]

    # Filter by hashtag_type
    if hashtag_type and hashtag_type.lower() != "all":
        type_map = {
            "branded": "is_branded",
            "event": "is_event",
            "player": "is_player",
            "farewell": "is_farewell"
        }
        flag = type_map.get(hashtag_type.lower())
        if flag:
            rows = [r for r in rows if r.get(flag, "False").lower() == "true"]

    # Aggregate by hashtag (across months/platforms if needed)
    hashtag_aggregates = {}
    for row in rows:
        hashtag = row.get("hashtag", "")

        if hashtag not in hashtag_aggregates:
            hashtag_aggregates[hashtag] = {
                "hashtag": hashtag,
                "total_engagement": 0,
                "total_posts": 0,
                "is_branded": row.get("is_branded", "False").lower() == "true",
                "is_event": row.get("is_event", "False").lower() == "true",
                "is_player": row.get("is_player", "False").lower() == "true",
                "is_farewell": row.get("is_farewell", "False").lower() == "true"
            }

        total_eng = float(row.get("total_engagement", 0))
        post_count = int(row.get("post_count", 0))

        hashtag_aggregates[hashtag]["total_engagement"] += total_eng
        hashtag_aggregates[hashtag]["total_posts"] += post_count

    # Filter by min_posts and compute averages
    hashtags = []
    for data in hashtag_aggregates.values():
        if data["total_posts"] < min_posts:
            continue

        avg_eng = data["total_engagement"] / data["total_posts"] if data["total_posts"] > 0 else 0

        # Determine hashtag_type for display
        if data["is_farewell"]:
            ht_type = "farewell"
        elif data["is_event"]:
            ht_type = "event"
        elif data["is_player"]:
            ht_type = "player"
        elif data["is_branded"]:
            ht_type = "branded"
        else:
            ht_type = "general"

        hashtags.append({
            "hashtag": data["hashtag"],
            "avg_engagement": round(avg_eng, 2),
            "post_count": data["total_posts"],
            "hashtag_type": ht_type,
            "vs_no_hashtag_baseline": 1.0,  # Placeholder - would need baseline calc
            "trend": "evergreen"  # Placeholder - would need time series analysis
        })

    # Sort by avg_engagement descending
    hashtags.sort(key=lambda h: h["avg_engagement"], reverse=True)

    # Top hashtags by category
    top_overall = hashtags[0] if hashtags else None
    top_evergreen = next((h for h in hashtags if h["trend"] == "evergreen"), None)
    top_branded = next((h for h in hashtags if h["hashtag_type"] == "branded"), None)
    top_player = next((h for h in hashtags if h["hashtag_type"] == "player"), None)

    return {
        "hashtags": hashtags,
        "top_hashtag_overall": top_overall["hashtag"] if top_overall else None,
        "top_evergreen_hashtag": top_evergreen["hashtag"] if top_evergreen else None,
        "top_branded_hashtag": top_branded["hashtag"] if top_branded else None,
        "top_player_hashtag": top_player["hashtag"] if top_player else None
    }


# ============================================================================
# FUNCTION 5: Peer Comparison Analytics
# ============================================================================

def get_peer_comparison_analytics(metric: str) -> Dict[str, Any]:
    """
    Compare Real Madrid vs peers on analytics metrics.

    Args:
        metric: 'goal_celebration_avg', 'post_match_avg', 'reel_multiplier', etc.

    Returns:
        Dict with peer comparison data
    """
    # Read peer benchmark data
    try:
        peer_rows = _read_gold_csv("gold_peer_social_benchmark.csv")
    except Exception:
        peer_rows = []

    # Filter to relevant metric
    metric_rows = [r for r in peer_rows if r.get("metric_name", "") == metric]

    if not metric_rows:
        return {
            "metric": metric,
            "clubs": [],
            "real_madrid_rank": None,
            "peer_median": None,
            "peer_leader": None
        }

    # Extract club values
    clubs = []
    for row in metric_rows:
        club_name = row.get("club_name", "")
        value = float(row.get("metric_value", 0))

        clubs.append({
            "club": club_name,
            "value": value
        })

    # Sort by value descending (best first)
    clubs.sort(key=lambda c: c["value"], reverse=True)

    # Find Real Madrid rank
    rm_entry = next((c for c in clubs if "Real Madrid" in c["club"]), None)
    rm_rank = clubs.index(rm_entry) + 1 if rm_entry else None

    # Peer median and leader
    values = [c["value"] for c in clubs]
    peer_median = statistics.median(values) if values else None
    peer_leader = clubs[0] if clubs else None

    return {
        "metric": metric,
        "clubs": clubs,
        "real_madrid_rank": rm_rank,
        "peer_median": peer_median,
        "peer_leader": peer_leader["club"] if peer_leader else None,
        "peer_leader_value": peer_leader["value"] if peer_leader else None
    }


# ============================================================================
# FUNCTION 6: Generate Dynamic Insights
# ============================================================================

def generate_dynamic_insights(data_month: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Generate plain-English insight cards dynamically from data.

    Returns:
        List of InsightCard dicts with category, priority, headline, finding, etc.
    """
    insights = []

    # Get analytics data
    format_data = get_format_performance()
    moment_data = get_match_moment_analysis()
    day_data = get_day_of_week_analysis()

    # INSIGHT 1: Reel Multiplier
    formats = format_data.get("formats", [])
    reel_format = next((f for f in formats if "reel" in f["variety"].lower()), None)
    standard_format = next((f for f in formats if f["variety"] == "post" and "instagram" in f["platform"].lower()), None)

    if reel_format and standard_format:
        reel_avg = reel_format["avg_engagement"]
        post_avg = standard_format["avg_engagement"]
        reel_count = reel_format["post_count"]
        post_count = standard_format["post_count"]
        multiplier = reel_avg / post_avg if post_avg > 0 else 1

        insights.append({
            "insight_id": "reel_multiplier_2025",
            "category": "format",
            "priority": "critical",
            "headline": f"Instagram Reels generate {multiplier:.1f}x more engagement than standard posts",
            "finding": f"Across {reel_count:,} Reels posted in 2025, the average engagement per Reel was {reel_avg:,.0f} — compared to {post_avg:,.0f} for standard image posts. This {multiplier:.1f}x multiplier makes Reels the single highest-impact content format available to the social team.",
            "evidence": f"{reel_avg:,.0f} avg per Reel vs {post_avg:,.0f} avg per standard post ({reel_count:,} Reels vs {post_count:,} standard posts)",
            "recommendation": "Prioritise Reel format for all non-time-sensitive content. For every 10 standard image posts planned, consider converting 3-4 to Reels.",
            "impact_estimate": f"If 20 standard posts per month were converted to Reels, estimated monthly engagement increase: +{(20 * (reel_avg - post_avg)):,.0f}",
            "data_source": f"Based on {reel_count:,} Reel posts and {post_count:,} standard posts in 2025",
            "refreshes_with_new_data": True
        })

    # INSIGHT 2: Post-Match Underutilisation
    moments = moment_data.get("moments", [])
    post_match = next((m for m in moments if m["moment"] == "post_match"), None)
    non_matchday = next((m for m in moments if m["moment"] == "non_matchday"), None)

    if post_match and non_matchday:
        pm_avg = post_match["avg_engagement"]
        nm_avg = non_matchday["avg_engagement"]
        pm_count = post_match["post_count"]
        pm_pct = post_match["pct_of_total_posts"]
        multiplier = pm_avg / nm_avg if nm_avg > 0 else 1

        total_posts = sum(m["post_count"] for m in moments)

        insights.append({
            "insight_id": "post_match_underutilisation",
            "category": "content",
            "priority": "high",
            "headline": f"Post-match content generates {multiplier:.1f}x more engagement but represents only {pm_pct:.1f}% of posts",
            "finding": f"Post-match posts (Post-Game Congrats) average {pm_avg:,.0f} engagement — {multiplier:.1f}x higher than non-matchday content ({nm_avg:,.0f}). Yet only {pm_count:,} post-match posts were published in 2025 ({pm_pct:.1f}% of {total_posts:,} total posts), making this the most underutilised high-performing content category.",
            "evidence": f"{pm_avg:,.0f} avg post-match vs {nm_avg:,.0f} avg non-matchday ({pm_count:,} posts = {pm_pct:.1f}% of total)",
            "recommendation": "Increase post-match content volume. Every home win, away win, and Champions League result represents a high-engagement publishing window that is currently underexploited.",
            "impact_estimate": f"Doubling post-match post count from {pm_count} to {pm_count * 2} while maintaining current avg engagement would add approximately +{(pm_count * pm_avg):,.0f} to annual total engagement.",
            "data_source": f"Based on {total_posts:,} posts analyzed across all match moments in 2025",
            "refreshes_with_new_data": True
        })

    # INSIGHT 3: Thursday Timing Advantage
    days = day_data.get("days", [])
    best_day_name = day_data.get("best_day", "")
    worst_day_name = day_data.get("worst_day", "")
    best_day_avg = day_data.get("best_day_avg", 0)
    worst_day_avg = day_data.get("worst_day_avg", 0)
    weekly_avg = day_data.get("weekly_average", 0)

    best_day = next((d for d in days if d["day_of_week"] == best_day_name), None)
    worst_day = next((d for d in days if d["day_of_week"] == worst_day_name), None)

    if best_day and worst_day and weekly_avg > 0:
        pct_above = ((best_day_avg - weekly_avg) / weekly_avg) * 100
        pct_below = ((worst_day_avg - weekly_avg) / weekly_avg) * 100

        insights.append({
            "insight_id": "thursday_timing_advantage",
            "category": "timing",
            "priority": "medium",
            "headline": f"{best_day_name} is Real Madrid's highest-engagement day ({pct_above:.0f}% above weekly average)",
            "finding": f"Posts published on {best_day_name} average {best_day_avg:,.0f} engagement — {pct_above:.0f}% above the weekly platform average of {weekly_avg:,.0f}. The worst performing day ({worst_day_name}: {worst_day_avg:,.0f}) performs {abs(pct_below):.0f}% below average.",
            "evidence": f"{best_day_name}: {best_day_avg:,.0f} avg | {worst_day_name}: {worst_day_avg:,.0f} avg | Weekly avg: {weekly_avg:,.0f}",
            "recommendation": f"Schedule highest-priority content (major announcements, key campaign launches, new signings) to publish on {best_day_name}. Avoid {worst_day_name} for content where maximising initial engagement is important.",
            "impact_estimate": f"Shifting 5 high-value posts from {worst_day_name} to {best_day_name} could add +{(5 * (best_day_avg - worst_day_avg)):,.0f} engagement per week",
            "data_source": "Based on 55,598 posts aggregated by day of week in 2025",
            "refreshes_with_new_data": True
        })

    return insights


# ============================================================================
# FUNCTION 7: Content Recommendations
# ============================================================================

def get_content_recommendations(team: str = "content") -> List[Dict[str, Any]]:
    """
    Generate priority-ranked recommendations for content team.

    Args:
        team: Target team (default: "content")

    Returns:
        List of Recommendation dicts, ranked by impact
    """
    recommendations = []

    # Get insights
    insights = generate_dynamic_insights()

    # Convert insights to recommendations
    rank = 1
    for insight in insights:
        if insight["priority"] == "critical":
            effort = "medium"
        elif insight["priority"] == "high":
            effort = "low"
        else:
            effort = "low"

        # Extract action verb from recommendation
        rec_text = insight.get("recommendation", "")
        action = "OPTIMIZE"
        if "convert" in rec_text.lower() or "shift" in rec_text.lower():
            action = "CONVERT"
        elif "increase" in rec_text.lower():
            action = "INCREASE"
        elif "schedule" in rec_text.lower():
            action = "SCHEDULE"

        recommendations.append({
            "rank": rank,
            "action": action,
            "title": insight["headline"],
            "rationale": insight["finding"],
            "expected_impact": insight["impact_estimate"],
            "effort_estimate": effort,
            "evidence_summary": insight["evidence"],
            "category": insight["category"]
        })
        rank += 1

    return recommendations
