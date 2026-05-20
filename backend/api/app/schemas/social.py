"""
Social media metrics schemas for V1.6.1 - Fifth Digital Platform.

All schemas are Pydantic v2 models for FastAPI response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional


class SocialMetricsMonthly(BaseModel):
    """Monthly social media metrics row from gold_social_metrics table."""

    month: str = Field(..., description="ISO date string YYYY-MM-DD")
    asset_name: str = Field(..., description="Always 'social_media'")

    # Overall metrics
    total_posts: int = Field(..., description="Total posts across all platforms")
    total_engagement: float = Field(..., description="Total engagement (likes + comments + reposts + saves)")
    avg_engagement_per_post: float = Field(..., description="Average engagement per post")
    total_likes: float = Field(..., description="Total likes/reactions across all platforms")
    total_comments: float = Field(..., description="Total comments/replies")
    total_reposts: float = Field(..., description="Total reposts/retweets")
    total_saves: float = Field(..., description="Total post saves")
    total_estimated_views: float = Field(..., description="Total estimated views")
    total_estimated_impressions: float = Field(..., description="Total estimated impressions")

    # Per-platform metrics
    instagram_posts: int
    instagram_engagement: float
    instagram_avg_engagement: float
    instagram_engagement_rate: float

    tiktok_posts: int
    tiktok_engagement: float
    tiktok_avg_engagement: float
    tiktok_engagement_rate: float

    x_posts: int
    x_engagement: float
    x_avg_engagement: float
    x_engagement_rate: float

    facebook_posts: int
    facebook_engagement: float
    facebook_avg_engagement: float
    facebook_engagement_rate: float

    youtube_posts: int
    youtube_engagement: float
    youtube_avg_engagement: float

    # Content type performance
    goal_celebration_avg_engagement: float
    training_avg_engagement: float
    score_graphic_avg_engagement: float
    player_arrival_avg_engagement: float
    lineup_graphic_avg_engagement: float
    birthday_avg_engagement: float
    game_preview_avg_engagement: float

    # Language account breakdown
    spanish_account_engagement: float
    english_account_engagement: float
    arabic_account_engagement: float
    french_account_engagement: float
    other_account_engagement: float

    # Computed metrics
    international_engagement_ratio: float = Field(..., description="Non-Spanish engagement / total")
    top_performing_platform: str = Field(..., description="Platform with highest avg engagement")
    top_performing_content_type: str = Field(..., description="Content type with highest avg engagement")


class SocialPlatformBreakdown(BaseModel):
    """Per-platform social media performance detail."""

    platform: str = Field(..., description="Platform name: instagram, tiktok, x, facebook, youtube")
    posts: int = Field(..., description="Total posts on this platform")
    engagement: float = Field(..., description="Total engagement")
    avg_engagement: float = Field(..., description="Average engagement per post")
    engagement_rate: Optional[float] = Field(None, description="Engagement rate (engagement / max followers)")


class SocialContentPerformance(BaseModel):
    """Content type performance breakdown."""

    content_type: str = Field(..., description="Content type: goal_celebration, training, etc")
    avg_engagement: float = Field(..., description="Average engagement for this content type")


class SocialSummaryResponse(BaseModel):
    """Latest month summary for Social Intelligence dashboard."""

    latest_month: str = Field(..., description="ISO date YYYY-MM-DD")

    # Key metrics
    total_engagement: float
    total_engagement_mom_change: Optional[float] = Field(None, description="Month-over-month % change")

    avg_engagement_per_post: float
    avg_engagement_per_post_mom_change: Optional[float] = None

    instagram_engagement_rate: float
    instagram_engagement_rate_mom_change: Optional[float] = None

    international_engagement_ratio: float
    international_engagement_ratio_mom_change: Optional[float] = None

    # Context
    total_posts: int
    top_performing_platform: str
    top_performing_content_type: str


class SocialMonthlyTrendResponse(BaseModel):
    """12-month trend data for charts."""

    months: list[str] = Field(..., description="List of month ISO dates")
    total_engagement: list[float] = Field(..., description="Monthly engagement values")
    avg_engagement_per_post: list[float] = Field(..., description="Monthly avg engagement values")
    total_posts: list[int] = Field(..., description="Monthly post counts")


class SocialPlatformBreakdownResponse(BaseModel):
    """Platform performance breakdown response."""

    month: str = Field(..., description="ISO date for requested month")
    platforms: list[SocialPlatformBreakdown] = Field(..., description="Per-platform metrics")


class SocialContentPerformanceResponse(BaseModel):
    """Content type performance response."""

    month: str = Field(..., description="ISO date for requested month")
    content_types: list[SocialContentPerformance] = Field(..., description="Per-content-type metrics")


# V1.6.5 — Social Anomaly Detection Schemas

class SocialAnomaly(BaseModel):
    """
    Detected social media anomaly (spike/drop >2 std from mean).

    Used for event confirmation workflow — anomalies can be confirmed as
    real-world events or dismissed as noise.
    """

    month: str = Field(..., description="Month of anomaly (ISO date YYYY-MM-DD)")
    metric: str = Field(..., description="Metric that showed anomaly")
    actual_value: float = Field(..., description="Actual metric value")
    mean_value: float = Field(..., description="Mean value across all months")
    std_value: float = Field(..., description="Standard deviation")
    z_score: float = Field(..., description="Z-score (how many std from mean)")
    direction: str = Field(..., description="'spike' or 'drop'")
    likely_cause: str = Field(..., description="Classified cause: match_result_win, injury_news, etc")
    candidate_event_name: str = Field(..., description="Auto-generated event name for confirmation")
    candidate_category: str = Field(..., description="Suggested event category")
    is_confirmed: bool = Field(..., description="Whether anomaly has been confirmed as an event")
    confidence_level: str = Field(..., description="'high', 'medium', or 'low' based on z-score magnitude")


class SocialAnomalyListResponse(BaseModel):
    """Response for anomaly list endpoints."""

    total_count: int = Field(..., description="Total number of anomalies")
    items: list[SocialAnomaly] = Field(..., description="List of anomalies")


class ConfirmAnomalyRequest(BaseModel):
    """Request body for confirming an anomaly as an event."""

    confirmed_name: str = Field(..., description="Event name (user can edit)")
    confirmed_category: str = Field(..., description="Event category (user can edit)")
    description: str = Field(..., description="Event description")
    impact_magnitude: str = Field(..., description="'high', 'medium', or 'low'")
    affected_assets: str = Field(default="social_media", description="Comma-separated asset names")


# V1.6.6 — International Audience Intelligence Schemas

class LanguageBreakdown(BaseModel):
    """Language/region market breakdown from language account columns."""

    language: str = Field(..., description="Language market: Spanish, English, Arabic, French, Portuguese, Japanese, Chinese, Other")
    account_username: Optional[str] = Field(None, description="Primary account username for this market")
    monthly_engagement: float = Field(..., description="Total engagement from this market")
    follower_count: Optional[int] = Field(None, description="Follower count for this market (if known)")
    engagement_per_follower: Optional[float] = Field(None, description="Engagement / followers")
    pct_of_total_engagement: float = Field(..., description="Percentage of total engagement")
    mom_change: Optional[float] = Field(None, description="Month-over-month change (%)")


class InternationalBreakdownResponse(BaseModel):
    """Response for international audience breakdown endpoint."""

    month: str = Field(..., description="Month ISO date YYYY-MM-DD")
    language_markets: list[LanguageBreakdown] = Field(..., description="Breakdown by language market")
    total_international_engagement: float = Field(..., description="Sum of all non-Spanish engagement")
    international_engagement_ratio: float = Field(..., description="Non-Spanish / total")


class InternationalTrendPoint(BaseModel):
    """Single month data point in international trend."""

    month: str = Field(..., description="Month ISO date")
    spanish_engagement: float
    english_engagement: float
    arabic_engagement: float
    french_engagement: float
    other_engagement: float
    international_ratio: float


class InternationalTrendResponse(BaseModel):
    """12-month trend of international audience breakdown."""

    trend: list[InternationalTrendPoint] = Field(..., description="Monthly data points")


class MarketGrowthRanking(BaseModel):
    """Market growth ranking entry."""

    market: str = Field(..., description="Language market name")
    this_month: float = Field(..., description="Current month engagement")
    prior_month: float = Field(..., description="Prior month engagement")
    mom_change_pct: float = Field(..., description="Month-over-month % change")


class MarketGrowthRankingResponse(BaseModel):
    """Response for market growth ranking endpoint."""

    month: str = Field(..., description="Current month ISO date")
    rankings: list[MarketGrowthRanking] = Field(..., description="Markets ranked by growth")


class InternationalCommercialCorrelation(BaseModel):
    """Correlation between international_engagement_ratio and commercial metric."""

    commercial_metric: str = Field(..., description="Commercial metric name")
    commercial_asset: str = Field(..., description="Asset name")
    correlation: float = Field(..., description="Pearson correlation coefficient")
    lag_months: int = Field(..., description="Lag in months")
    direction: str = Field(..., description="Relationship direction: positive or negative")
    strength_label: str = Field(..., description="Strength: Strong, Moderate, Weak")
    interpretation: str = Field(..., description="Human-readable interpretation")
    passes_threshold: bool = Field(..., description="Whether correlation >= 0.45")


class InternationalCommercialCorrelationResponse(BaseModel):
    """Response for international commercial correlation endpoint."""

    correlations: list[InternationalCommercialCorrelation] = Field(..., description="List of correlations found")
    strongest_correlation: Optional[InternationalCommercialCorrelation] = Field(None, description="Strongest correlation if any pass threshold")
