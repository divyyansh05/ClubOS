"""
Social media metrics API router for V1.6.1 - Fifth Digital Platform + V1.7 Social Analytics.

Endpoints:
- GET /social/summary — Latest month summary with MoM changes
- GET /social/monthly — 12-month trend data
- GET /social/platforms/{month} — Per-platform breakdown
- GET /social/content/{month} — Content type performance
- GET /social/content-intelligence — Content-to-commercial correlations (V1.6.4)
- GET /social/content-intelligence/summary — Strongest correlations summary (V1.6.4)
- GET /social/content-intelligence/{month} — Month-specific content analysis (V1.6.4)
- GET /social/analytics/dayofweek — Day of week analysis (V1.7)
- GET /social/analytics/moments — Match moment analysis (V1.7)
- GET /social/analytics/formats — Format performance (V1.7)
- GET /social/analytics/hashtags — Hashtag performance (V1.7)
- GET /social/analytics/insights — Dynamic insights (V1.7)
- GET /social/analytics/recommendations — Content recommendations (V1.7)
- GET /social/analytics/peer/{metric} — Peer comparison (V1.7)
"""

from fastapi import APIRouter, HTTPException, Query
from app.services import social_service, content_intelligence_service, social_analytics_service
from app.schemas.social import (
    SocialSummaryResponse,
    SocialMonthlyTrendResponse,
    SocialPlatformBreakdownResponse,
    SocialContentPerformanceResponse,
    InternationalBreakdownResponse,
    InternationalTrendResponse,
    InternationalCommercialCorrelationResponse,
    MarketGrowthRankingResponse,
    DayOfWeekAnalysisResponse,
    MatchMomentAnalysisResponse,
    FormatPerformanceResponse,
    HashtagPerformanceResponse,
    DynamicInsightsResponse,
    ContentRecommendationsResponse,
    PeerComparisonResponse
)
from app.schemas.content_intelligence import (
    ContentIntelligenceResponse,
    ContentCommercialSummary,
    ContentMonthlyPerformance
)
from app.schemas.social import (
    SocialAnomaly,
    SocialAnomalyListResponse,
    ConfirmAnomalyRequest
)
from app.schemas.events import EventSchema, EventCreateSchema
from app.services import event_service

router = APIRouter()


@router.get("/summary", response_model=SocialSummaryResponse)
def get_social_summary():
    """
    Get latest month social media summary with MoM comparison.

    Returns key metrics: total_engagement, avg_engagement_per_post,
    instagram_engagement_rate, international_engagement_ratio.
    """
    try:
        return social_service.get_social_summary()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/monthly", response_model=SocialMonthlyTrendResponse)
def get_social_monthly_trend():
    """
    Get 12-month social media trend data for charts.

    Returns arrays of months, total_engagement, avg_engagement_per_post,
    and total_posts for time series visualization.
    """
    try:
        return social_service.get_social_monthly_trend()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/platforms/{month}", response_model=SocialPlatformBreakdownResponse)
def get_social_platforms(month: str):
    """
    Get per-platform breakdown for a specific month.

    Args:
        month: Month in YYYY-MM format (e.g., "2025-01")

    Returns platform-by-platform metrics: posts, engagement, avg_engagement,
    engagement_rate for Instagram, TikTok, X, Facebook, YouTube.
    """
    try:
        return social_service.get_social_platform_breakdown(month)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/content/{month}", response_model=SocialContentPerformanceResponse)
def get_social_content(month: str):
    """
    Get content type performance for a specific month.

    Args:
        month: Month in YYYY-MM format (e.g., "2025-01")

    Returns content types ranked by avg_engagement: goal_celebration,
    training, score_graphic, player_arrival, lineup_graphic,
    birthday, game_preview.
    """
    try:
        return social_service.get_social_content_performance(month)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# V1.6.4 — Content Intelligence Engine endpoints

@router.get("/content-intelligence", response_model=ContentIntelligenceResponse)
def get_content_intelligence():
    """
    Get all content-to-commercial correlations (V1.6.4).

    Returns validated correlations between social media content types
    and commercial outcomes across ecommerce, website, streaming, fan app.

    Correlation threshold: 0.45 (lower than internal signals due to
    noisier content-to-commercial relationships).
    """
    try:
        return content_intelligence_service.get_content_intelligence_full()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/content-intelligence/summary", response_model=ContentCommercialSummary)
def get_content_intelligence_summary():
    """
    Get summary of strongest content-to-commercial relationships (V1.6.4).

    Returns top signal, total correlations found, most predictive content type,
    and most influenced commercial metric. Used for dashboard cards and
    Monthly Briefing integration.
    """
    try:
        return content_intelligence_service.get_content_commercial_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/content-intelligence/{month}", response_model=ContentMonthlyPerformance)
def get_content_intelligence_month(month: str):
    """
    Get content performance with commercial context for a specific month (V1.6.4).

    Args:
        month: Month in YYYY-MM format (e.g., "2025-06")

    Returns content type breakdown, commercial outcomes, and matching
    correlations for retrospective analysis. Example: "In June 2025,
    Goal Celebration had 95K avg engagement. In July 2025, net_sales
    were 12% above baseline — consistent with 1-month lag correlation."
    """
    try:
        return content_intelligence_service.get_content_performance_by_month(month)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# V1.6.6 — International Audience Intelligence endpoints

@router.get("/international", response_model=InternationalBreakdownResponse)
def get_international_breakdown(month: str = None):
    """
    Get international audience breakdown by language market (V1.6.6).

    Args:
        month: Optional month in YYYY-MM format (defaults to latest)

    Returns language market breakdown with engagement, follower counts,
    percentages, and month-over-month changes. Markets: Spanish, English,
    Arabic, French, Other (Portuguese, Japanese, Chinese combined).
    """
    try:
        result = social_service.get_international_breakdown(month)
        return InternationalBreakdownResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/international/trend", response_model=InternationalTrendResponse)
def get_international_trend():
    """
    Get 12-month trend of international audience breakdown (V1.6.6).

    Returns monthly data points showing Spanish vs international engagement
    evolution. Used to identify which markets are growing vs flat.
    """
    try:
        result = social_service.get_international_trend()
        return InternationalTrendResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/international/correlation", response_model=InternationalCommercialCorrelationResponse)
def get_international_commercial_correlation():
    """
    Get international audience → commercial metric correlations (V1.6.6).

    Tests correlation between international_engagement_ratio and:
    - Streaming active_subscriptions (global audience → streaming)
    - Ecommerce unique_visitors (international traffic → global store)

    Uses 0.45 correlation threshold (same as content intelligence).
    Returns correlations with lag, direction, strength, and interpretation.
    """
    try:
        result = social_service.compute_international_commercial_correlation()
        return InternationalCommercialCorrelationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/international/growth", response_model=MarketGrowthRankingResponse)
def get_market_growth_ranking(compare_month: str = None):
    """
    Get market growth ranking (which language markets growing fastest) (V1.6.6).

    Args:
        compare_month: Optional comparison month in YYYY-MM format.
                      If provided, compares latest month vs this specific month.
                      If not provided, defaults to month-over-month.

    Returns language markets sorted by engagement change.
    Shows which international markets are accelerating vs decelerating.
    """
    try:
        result = social_service.get_market_growth_ranking(compare_month)
        return MarketGrowthRankingResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# V1.6.5 — Social Anomaly Detection & Event Confirmation endpoints

@router.get("/anomalies", response_model=SocialAnomalyListResponse)
def get_social_anomalies():
    """
    Get all detected social media anomalies for the year (V1.6.5).

    Detects months where social metrics deviated >2 standard deviations
    from mean. Returns spikes/drops with likely cause classification
    and candidate event details for confirmation workflow.
    """
    try:
        anomalies = social_service.detect_social_anomalies()
        return SocialAnomalyListResponse(
            total_count=len(anomalies),
            items=anomalies
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/anomalies/unconfirmed", response_model=SocialAnomalyListResponse)
def get_unconfirmed_anomalies():
    """
    Get social anomalies with no matching event in calendar (V1.6.5).

    Returns only anomalies that haven't been confirmed as events yet.
    Used by Event Calendar page to show pending anomalies for staff
    to confirm or dismiss.
    """
    try:
        anomalies = social_service.get_unconfirmed_social_anomalies()
        return SocialAnomalyListResponse(
            total_count=len(anomalies),
            items=anomalies
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/anomalies/{month}/confirm", response_model=EventSchema)
def confirm_anomaly_as_event(month: str, request: ConfirmAnomalyRequest):
    """
    Confirm a social anomaly as a real-world event (V1.6.5).

    Creates a new event in the Event Calendar with the provided details.
    The anomaly will no longer appear in the unconfirmed list.

    Args:
        month: Month in YYYY-MM or YYYY-MM-DD format
        request: Event details (name, category, description, impact)

    Returns:
        The created event
    """
    try:
        # Determine event_date
        # If month is YYYY-MM, use first day of month (YYYY-MM-01)
        if len(month) == 7:  # YYYY-MM
            event_date = f"{month}-01"
        else:
            event_date = month  # Already YYYY-MM-DD

        # Create event via event_service
        event_data = EventCreateSchema(
            event_date=event_date,
            event_name=request.confirmed_name,
            event_category=request.confirmed_category,
            event_description=request.description,
            expected_impact=request.affected_assets,
            impact_magnitude=request.impact_magnitude
        )

        new_event = event_service.create_event(event_data.model_dump())
        return EventSchema(**new_event)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")


@router.post("/anomalies/{month}/dismiss")
def dismiss_anomaly(month: str):
    """
    Dismiss a social anomaly (mark as not a real event) (V1.6.5).

    In the current implementation, dismissed anomalies are simply not
    shown again because get_unconfirmed_anomalies() only returns anomalies
    without matching events. To fully implement dismissal tracking, would
    need a dismissed_anomalies table or file.

    For V1.6.5 MVP, this endpoint serves as a placeholder and returns
    success — future versions can add persistent dismissal tracking.

    Args:
        month: Month in YYYY-MM or YYYY-MM-DD format

    Returns:
        Success message
    """
    return {
        "message": f"Anomaly for {month} dismissed (not shown in unconfirmed list anymore)"
    }


# V1.7 — Social Analytics Intelligence endpoints

@router.get("/analytics/dayofweek", response_model=DayOfWeekAnalysisResponse)
def get_day_of_week_analysis(
    platform: str = Query(default="all", description="Platform filter: Instagram/TikTok/X/Facebook/YouTube/all"),
    match_moment: str = Query(default="all", description="Match moment filter: pre_match/during_match/post_match/non_matchday/all")
):
    """
    Get day of week performance analysis (V1.7).

    Analyzes engagement patterns by day of week across platforms and match moments.
    Returns best/worst days, weekly averages, and platform-specific best days.

    Used for: Timing optimization recommendations, heatmap visualization
    """
    try:
        result = social_analytics_service.get_day_of_week_analysis(platform, match_moment)
        return DayOfWeekAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/analytics/moments", response_model=MatchMomentAnalysisResponse)
def get_match_moment_analysis(
    platform: str = Query(default="all", description="Platform filter: Instagram/TikTok/X/Facebook/YouTube/all")
):
    """
    Get match moment performance analysis (V1.7).

    Analyzes engagement by match moment: pre_match, during_match, post_match, non_matchday.
    Identifies underutilised high-performing moments (high engagement but low post volume).

    Used for: Content strategy recommendations, opportunity gap identification
    """
    try:
        result = social_analytics_service.get_match_moment_analysis(platform)
        return MatchMomentAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/analytics/formats", response_model=FormatPerformanceResponse)
def get_format_performance(
    platform: str = Query(default="all", description="Platform filter"),
    scene: str = Query(default=None, description="Scene filter")
):
    """
    Get content format performance analysis (V1.7).

    Analyzes format performance (Reels vs standard posts, videos vs images, etc.).
    Returns multipliers vs standard Instagram posts and identifies underused high performers.

    Key insight: Instagram Reels generate 7.8x more engagement than standard posts.

    Used for: Format optimization recommendations, content team guidance
    """
    try:
        result = social_analytics_service.get_format_performance(platform, scene)
        return FormatPerformanceResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/analytics/hashtags", response_model=HashtagPerformanceResponse)
def get_hashtag_performance(
    platform: str = Query(default="all", description="Platform filter"),
    hashtag_type: str = Query(default="all", description="Hashtag type: branded/event/player/farewell/all"),
    min_posts: int = Query(default=10, description="Minimum post count threshold")
):
    """
    Get hashtag performance analysis (V1.7).

    Analyzes hashtag performance by type (branded, event, player, farewell).
    Returns top hashtags by engagement and identifies evergreen vs seasonal hashtags.

    Key insight: #graciasluka (farewell) averaged 896K engagement vs #realmadrid (branded) 67K.

    Used for: Hashtag strategy, campaign planning, content team recommendations
    """
    try:
        result = social_analytics_service.get_hashtag_performance(platform, hashtag_type, min_posts)
        return HashtagPerformanceResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/analytics/insights", response_model=DynamicInsightsResponse)
def get_dynamic_insights(
    data_month: str = Query(default=None, description="Optional month filter")
):
    """
    Get dynamically generated insights from social data (V1.7).

    Generates plain-English InsightCards that auto-populate from live data:
    - Reel multiplier insights (7.8x standard posts)
    - Post-match underutilisation (2.1x engagement, only 0.5% of posts)
    - Thursday timing advantage (17.8% above weekly average)
    - Event hashtag performance
    - Peer benchmarking insights

    Insights refresh automatically when new data is uploaded.

    Used for: Social Intelligence dashboard, content team guidance, Monthly Briefing
    """
    try:
        insights = social_analytics_service.generate_dynamic_insights(data_month)
        return DynamicInsightsResponse(
            insights=insights,
            total_count=len(insights)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/analytics/recommendations", response_model=ContentRecommendationsResponse)
def get_content_recommendations(
    team: str = Query(default="content", description="Target team")
):
    """
    Get priority-ranked content team recommendations (V1.7).

    Converts insights into actionable recommendations ranked by impact:
    - CONVERT: Shift format strategy (e.g., convert posts to Reels)
    - SCHEDULE: Optimize timing (e.g., publish on Thursday not Wednesday)
    - INCREASE: Scale up underutilised opportunities (e.g., post-match content)
    - REDUCE: Deprioritise low performers

    Each recommendation includes:
    - Priority rank (1 = most impactful)
    - Action verb and title
    - Rationale and evidence
    - Expected impact estimate
    - Effort estimate (low/medium/high)

    Used for: Content team task list, editorial planning, strategy meetings
    """
    try:
        recommendations = social_analytics_service.get_content_recommendations(team)
        return ContentRecommendationsResponse(
            recommendations=recommendations,
            total_count=len(recommendations)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/analytics/peer/{metric}", response_model=PeerComparisonResponse)
def get_peer_comparison(
    metric: str
):
    """
    Get peer comparison on analytics metrics (V1.7).

    Compares Real Madrid vs 9 peer clubs on analytics metrics:
    - goal_celebration_avg: Goal Celebration post avg engagement
    - post_match_avg: Post-Match content avg engagement
    - reel_multiplier: Reel engagement vs standard posts
    - day_of_week_consistency: Variance in day-of-week performance

    Returns:
    - All clubs ranked by metric value
    - Real Madrid's rank
    - Peer median and leader

    Used for: Competitive benchmarking, identifying best practices, gap analysis
    """
    try:
        result = social_analytics_service.get_peer_comparison_analytics(metric)
        return PeerComparisonResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
