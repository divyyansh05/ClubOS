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

    # Platform-level monthly data for multi-line charts (V1.6.7 Fix 2)
    instagram_engagement: list[float] = Field(..., description="Instagram monthly engagement")
    tiktok_engagement: list[float] = Field(..., description="TikTok monthly engagement")
    x_engagement: list[float] = Field(..., description="X/Twitter monthly engagement")
    facebook_engagement: list[float] = Field(..., description="Facebook monthly engagement")
    youtube_engagement: list[float] = Field(..., description="YouTube monthly engagement")


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


# V1.7 — Social Analytics Intelligence Schemas

class DayOfWeekPerformance(BaseModel):
    """Day of week performance data."""

    day_of_week: str = Field(..., description="Day name: Monday, Tuesday, etc")
    day_number: int = Field(..., description="Day number 1-7 (1=Monday)")
    avg_engagement_per_post: float = Field(..., description="Average engagement on this day")
    post_count: int = Field(..., description="Total posts on this day")
    vs_weekly_average_pct: float = Field(..., description="% above/below weekly average")
    best_platform_on_this_day: str = Field(..., description="Platform with highest engagement on this day")


class DayOfWeekAnalysisResponse(BaseModel):
    """Response for day of week analysis endpoint."""

    days: list[DayOfWeekPerformance] = Field(..., description="7 days with performance metrics")
    best_day: Optional[str] = Field(None, description="Day with highest engagement")
    worst_day: Optional[str] = Field(None, description="Day with lowest engagement")
    best_day_avg: float = Field(..., description="Average engagement on best day")
    worst_day_avg: float = Field(..., description="Average engagement on worst day")
    weekly_average: float = Field(..., description="Weekly average engagement")


class MatchMomentPerformance(BaseModel):
    """Match moment performance data."""

    moment: str = Field(..., description="Moment: pre_match, during_match, post_match, non_matchday")
    label: str = Field(..., description="Display label: Pre-Match, During Match, etc")
    avg_engagement: float = Field(..., description="Average engagement for this moment")
    post_count: int = Field(..., description="Total posts for this moment")
    pct_of_total_posts: float = Field(..., description="% of all posts")
    vs_non_matchday_multiplier: float = Field(..., description="Multiplier vs non-matchday baseline")
    opportunity_gap: str = Field(..., description="HIGH if underutilised, NORMAL otherwise")


class MatchMomentAnalysisResponse(BaseModel):
    """Response for match moment analysis endpoint."""

    moments: list[MatchMomentPerformance] = Field(..., description="All match moments")
    underutilised_moments: list[MatchMomentPerformance] = Field(..., description="Moments with HIGH opportunity gap")
    biggest_multiplier: Optional[dict] = Field(None, description="Moment with biggest multiplier")


class FormatPerformance(BaseModel):
    """Content format performance data."""

    variety: str = Field(..., description="Format variety: post, reel, video, etc")
    label: str = Field(..., description="Display label: Instagram Reel, etc")
    platform: str = Field(..., description="Platform name")
    avg_engagement: float = Field(..., description="Average engagement for this format")
    post_count: int = Field(..., description="Total posts for this format")
    vs_standard_post_multiplier: float = Field(..., description="Multiplier vs standard Instagram post")
    recommended: bool = Field(..., description="Whether this format is recommended (>2x multiplier, >50 posts)")


class FormatPerformanceResponse(BaseModel):
    """Response for format performance endpoint."""

    formats: list[FormatPerformance] = Field(..., description="All content formats")
    top_format: Optional[str] = Field(None, description="Top performing format")
    top_format_multiplier: float = Field(..., description="Top format multiplier")
    underused_high_performers: list[FormatPerformance] = Field(..., description="High multiplier but low post count")


class HashtagPerformance(BaseModel):
    """Hashtag performance data."""

    hashtag: str = Field(..., description="Hashtag with # prefix")
    avg_engagement: float = Field(..., description="Average engagement per post with this hashtag")
    post_count: int = Field(..., description="Total posts using this hashtag")
    hashtag_type: str = Field(..., description="Type: branded, event, player, farewell, general")
    vs_no_hashtag_baseline: float = Field(..., description="Multiplier vs posts with no hashtags")
    trend: str = Field(..., description="Trend: seasonal, evergreen, declining")


class HashtagPerformanceResponse(BaseModel):
    """Response for hashtag performance endpoint."""

    hashtags: list[HashtagPerformance] = Field(..., description="All hashtags meeting min_posts threshold")
    top_hashtag_overall: Optional[str] = Field(None, description="Top hashtag by avg engagement")
    top_evergreen_hashtag: Optional[str] = Field(None, description="Top evergreen hashtag")
    top_branded_hashtag: Optional[str] = Field(None, description="Top branded hashtag")
    top_player_hashtag: Optional[str] = Field(None, description="Top player hashtag")


class InsightCard(BaseModel):
    """Dynamic insight card generated from data."""

    insight_id: str = Field(..., description="Unique insight ID")
    category: str = Field(..., description="Category: timing, format, content, hashtag, peer")
    priority: str = Field(..., description="Priority: critical, high, medium")
    headline: str = Field(..., description="One-sentence headline starting with number/% where possible")
    finding: str = Field(..., description="2-3 sentences explaining what the data shows")
    evidence: str = Field(..., description="Specific numbers as evidence")
    recommendation: str = Field(..., description="One specific action the content team can take")
    impact_estimate: str = Field(..., description="Expected impact of implementing recommendation")
    data_source: str = Field(..., description="Data source description")
    refreshes_with_new_data: bool = Field(..., description="Always True - indicates dynamic generation")


class DynamicInsightsResponse(BaseModel):
    """Response for dynamic insights endpoint."""

    insights: list[InsightCard] = Field(..., description="List of auto-generated insights")
    total_count: int = Field(..., description="Total number of insights")


class ContentRecommendation(BaseModel):
    """Content team recommendation."""

    rank: int = Field(..., description="Priority rank (1 = most impactful)")
    action: str = Field(..., description="Action verb: CONVERT, SCHEDULE, INCREASE, REDUCE")
    title: str = Field(..., description="Recommendation title")
    rationale: str = Field(..., description="Why this recommendation matters")
    expected_impact: str = Field(..., description="Expected impact of implementing")
    effort_estimate: str = Field(..., description="Effort: low, medium, high")
    evidence_summary: str = Field(..., description="Evidence supporting this recommendation")
    category: str = Field(..., description="Category: format, timing, content_type, hashtag")


class ContentRecommendationsResponse(BaseModel):
    """Response for content recommendations endpoint."""

    recommendations: list[ContentRecommendation] = Field(..., description="Priority-ranked recommendations")
    total_count: int = Field(..., description="Total number of recommendations")


class PeerComparisonClub(BaseModel):
    """Club performance in peer comparison."""

    club: str = Field(..., description="Club name")
    value: float = Field(..., description="Metric value")


class PeerComparisonResponse(BaseModel):
    """Response for peer comparison analytics endpoint."""

    metric: str = Field(..., description="Metric name")
    clubs: list[PeerComparisonClub] = Field(..., description="All clubs ranked by value")
    real_madrid_rank: Optional[int] = Field(None, description="Real Madrid's rank")
    peer_median: Optional[float] = Field(None, description="Peer median value")
    peer_leader: Optional[str] = Field(None, description="Leader club name")
    peer_leader_value: Optional[float] = Field(None, description="Leader value")
