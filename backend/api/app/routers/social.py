"""
Social media metrics API router for V1.6.1 - Fifth Digital Platform.

Endpoints:
- GET /social/summary — Latest month summary with MoM changes
- GET /social/monthly — 12-month trend data
- GET /social/platforms/{month} — Per-platform breakdown
- GET /social/content/{month} — Content type performance
- GET /social/content-intelligence — Content-to-commercial correlations (V1.6.4)
- GET /social/content-intelligence/summary — Strongest correlations summary (V1.6.4)
- GET /social/content-intelligence/{month} — Month-specific content analysis (V1.6.4)
"""

from fastapi import APIRouter, HTTPException
from app.services import social_service, content_intelligence_service
from app.schemas.social import (
    SocialSummaryResponse,
    SocialMonthlyTrendResponse,
    SocialPlatformBreakdownResponse,
    SocialContentPerformanceResponse,
    InternationalBreakdownResponse,
    InternationalTrendResponse,
    InternationalCommercialCorrelationResponse,
    MarketGrowthRankingResponse
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
def get_market_growth_ranking():
    """
    Get market growth ranking (which language markets growing fastest) (V1.6.6).

    Returns language markets sorted by month-over-month engagement change.
    Shows which international markets are accelerating vs decelerating.
    """
    try:
        result = social_service.get_market_growth_ranking()
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
