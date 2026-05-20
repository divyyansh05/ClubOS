"""
Content Intelligence schemas for V1.6.4 - Content-to-Commercial Correlation Engine.

Maps social media content types to commercial outcomes via lagged correlation analysis.
"""

from pydantic import BaseModel
from typing import Optional


class ContentSignal(BaseModel):
    """
    A validated correlation between a content type and a commercial metric.

    Lower threshold than internal signals (0.45 vs 0.60) because content correlations
    are inherently noisier — content strategy influences commercial outcomes but
    through longer causal chains with more confounding factors.
    """
    content_type: str  # goal_celebration, training, score_graphic, etc.
    commercial_metric: str  # net_sales, conversion_rate, unique_visitors, etc.
    commercial_asset: str  # ecommerce, main_website, fan_app, streaming
    correlation: float  # Pearson r (-1 to 1)
    lag_months: int  # 0, 1, or 2 months
    direction: str  # "positive" or "negative"
    interpretation: str  # Business-readable explanation
    strength_label: str  # "Strong" (>0.65), "Moderate" (0.55-0.65), "Weak" (0.45-0.55)
    confidence_note: str  # "Based on 12 months of data — provisional"
    avg_content_engagement: float  # Average engagement per post for this content type
    sample_size_months: int  # Number of months used in correlation


class ContentCommercialSummary(BaseModel):
    """
    Summary of strongest content-to-commercial relationships.

    Used for dashboard header cards and Monthly Briefing integration.
    """
    strongest_signal: Optional[ContentSignal] = None
    total_correlations_found: int
    avg_correlation_strength: float
    most_predictive_content_type: str  # Content type appearing in most correlations
    most_influenced_commercial_metric: str  # Commercial metric appearing in most correlations


class ContentMonthlyPerformance(BaseModel):
    """
    Content type performance for a specific month with commercial context.

    Retrospective view: "In June 2025, Goal Celebration had 95K avg engagement.
    In July 2025, net_sales were 12% above baseline — consistent with the known
    1-month lag correlation."
    """
    month: str  # YYYY-MM-01
    content_performances: list[dict]  # [{content_type, avg_engagement, post_count}, ...]
    commercial_outcomes: list[dict]  # [{metric, asset, value, vs_baseline_pct}, ...]
    matching_correlations: list[str]  # Interpretations of correlations active this month


class ContentIntelligenceResponse(BaseModel):
    """
    Full response for GET /social/content-intelligence endpoint.
    """
    latest_month: str
    signals: list[ContentSignal]
    summary: ContentCommercialSummary
