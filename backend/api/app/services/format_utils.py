"""
Number formatting utilities for human-readable display.

Matches frontend formatNumber.ts behavior for consistency.
"""
from typing import Union


def abbreviate_number(value: Union[int, float]) -> str:
    """
    Smart abbreviation for large numbers.
    1,234 → 1,234
    12,345 → 12.3K
    1,234,567 → 1.23M
    1,234,567,890 → 1.23B
    """
    if value is None or (isinstance(value, float) and value != value):  # Check for NaN
        return "—"

    abs_val = abs(value)
    sign = "-" if value < 0 else ""

    if abs_val >= 1_000_000_000:
        return f"{sign}{abs_val / 1_000_000_000:.2f}B"
    if abs_val >= 1_000_000:
        return f"{sign}{abs_val / 1_000_000:.2f}M"
    if abs_val >= 10_000:
        return f"{sign}{abs_val / 1_000:.1f}K"
    if abs_val >= 1_000:
        return f"{sign}{abs_val:,.0f}"
    return f"{sign}{abs_val:.2f}"


def format_percent(value: Union[int, float], is_raw_rate: bool = False, decimals: int = 1) -> str:
    """
    Format a percentage value.
    Input can be 0.013 (raw rate) or 1.3 (already percentage).
    is_raw_rate=True means input is 0-1 range → multiply by 100.
    """
    if value is None or (isinstance(value, float) and value != value):
        return "—"

    pct = value * 100 if is_raw_rate else value
    return f"{pct:.{decimals}f}%"


def format_euros(value: Union[int, float]) -> str:
    """
    Format a currency value (euros).
    1234567.89 → €1.23M
    """
    if value is None or (isinstance(value, float) and value != value):
        return "—"

    return f"€{abbreviate_number(value)}"


def format_metric_value(metric_name: str, value: Union[int, float]) -> str:
    """
    THE MAIN FORMATTER.
    Given a metric name and a value, returns the correctly
    formatted string with appropriate units and precision.

    Usage: format_metric_value('conversion_rate', 0.013) → '1.3%'
           format_metric_value('net_sales', 1234567) → '€1.23M'
           format_metric_value('unique_visitors', 150029) → '150.0K'
           format_metric_value('bounce_rate', 0.4735) → '47.4%'
    """
    if value is None or (isinstance(value, float) and value != value):
        return "—"

    # Percentage/rate metrics (stored as 0-1 decimals)
    RATE_METRICS = {
        'conversion_rate', 'bounce_rate', 'checkout_rate',
        'card_addition_rate', 'subscription_rate', 'streamers_rate',
        'video_complete_rate', 'video_progress_75_rate',
        'video_progress_50_rate', 'video_progress_25_rate',
        'video_play_rate', 'engagement_rate', 'instagram_engagement_rate',
        'international_engagement_ratio', 'pct_android',
        'recurrence', 'video_recurrence',
    }

    # Currency metrics (euros)
    CURRENCY_METRICS = {
        'net_sales', 'cart_value', 'revenue',
    }

    # Score/rating metrics (0-5 or 0-10)
    RATING_METRICS = {
        'user_rating',
    }

    if metric_name in RATE_METRICS:
        # If value is clearly already a percentage (>1), don't multiply
        is_raw_rate = value <= 1.0
        return format_percent(value, is_raw_rate)

    if metric_name in CURRENCY_METRICS:
        return format_euros(value)

    if metric_name in RATING_METRICS:
        return f"{value:.1f} ★"

    # Default: smart abbreviation for counts and other numbers
    return abbreviate_number(value)
