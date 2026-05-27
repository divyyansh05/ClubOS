import { getMetricDef } from './metricDefinitions'

// ── Core formatters ─────────────────────────────────────

/**
 * Smart abbreviation for large numbers.
 * 1,234 → 1,234
 * 12,345 → 12.3K
 * 1,234,567 → 1.23M
 * 1,234,567,890 → 1.23B
 */
export function abbreviateNumber(value: number): string {
  if (value === null || value === undefined || isNaN(value)) return '—'
  const abs = Math.abs(value)
  const sign = value < 0 ? '-' : ''
  if (abs >= 1_000_000_000)
    return `${sign}${(abs / 1_000_000_000).toFixed(2)}B`
  if (abs >= 1_000_000)
    return `${sign}${(abs / 1_000_000).toFixed(2)}M`
  if (abs >= 10_000)
    return `${sign}${(abs / 1_000).toFixed(1)}K`
  if (abs >= 1_000)
    return `${sign}${abs.toLocaleString('en-GB', { maximumFractionDigits: 0 })}`
  return `${sign}${abs.toLocaleString('en-GB', { maximumFractionDigits: 2 })}`
}

/**
 * Format a percentage value.
 * Input can be 0.013 (raw rate) or 1.3 (already percentage).
 * isRawRate=true means input is 0-1 range → multiply by 100.
 */
export function formatPercent(
  value: number,
  isRawRate = false,
  decimals = 1
): string {
  if (value === null || value === undefined || isNaN(value)) return '—'
  const pct = isRawRate ? value * 100 : value
  return `${pct.toFixed(decimals)}%`
}

/**
 * Format a currency value (euros).
 * 1234567.89 → €1.23M
 */
export function formatEuros(value: number): string {
  if (value === null || value === undefined || isNaN(value)) return '—'
  return `€${abbreviateNumber(value)}`
}

/**
 * Format a Z-score for display.
 * Always show 2 decimal places with sigma symbol.
 */
export function formatZScore(value: number): string {
  if (value === null || value === undefined || isNaN(value)) return '—'
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}σ`
}

/**
 * Format a score component (0-1 range) as percentage.
 * 0.397 → 39.7%
 */
export function formatScore(value: number, decimals = 1): string {
  if (value === null || value === undefined || isNaN(value)) return '—'
  return `${(value * 100).toFixed(decimals)}%`
}

// ── Metric-aware formatter ──────────────────────────────

/**
 * THE MAIN FORMATTER.
 * Given a metric name and a value, returns the correctly
 * formatted string with appropriate units and precision.
 *
 * Usage: formatMetricValue('conversion_rate', 0.013) → '1.3%'
 *        formatMetricValue('net_sales', 1234567) → '€1.23M'
 *        formatMetricValue('unique_visitors', 150029) → '150.0K'
 *        formatMetricValue('bounce_rate', 0.4735) → '47.4%'
 */
export function formatMetricValue(
  metricName: string,
  value: number
): string {
  if (value === null || value === undefined || isNaN(value)) return '—'

  const def = getMetricDef(metricName)

  // Percentage/rate metrics (stored as 0-1 decimals)
  const RATE_METRICS = new Set([
    'conversion_rate', 'bounce_rate', 'checkout_rate',
    'card_addition_rate', 'subscription_rate', 'streamers_rate',
    'video_complete_rate', 'video_progress_75_rate',
    'video_progress_50_rate', 'video_progress_25_rate',
    'video_play_rate', 'engagement_rate', 'instagram_engagement_rate',
    'international_engagement_ratio', 'pct_android',
    'recurrence', 'video_recurrence',
  ])

  // Currency metrics (euros)
  const CURRENCY_METRICS = new Set([
    'net_sales', 'cart_value', 'revenue',
  ])

  // Score/rating metrics (0-5 or 0-10)
  const RATING_METRICS = new Set([
    'user_rating',
  ])

  if (RATE_METRICS.has(metricName)) {
    // If value is clearly already a percentage (>1), don't multiply
    const isRawRate = value <= 1.0
    return formatPercent(value, isRawRate)
  }

  if (CURRENCY_METRICS.has(metricName)) {
    return formatEuros(value)
  }

  if (RATING_METRICS.has(metricName)) {
    return `${value.toFixed(1)} ★`
  }

  // Default: smart abbreviation for counts and other numbers
  return abbreviateNumber(value)
}

/**
 * Format a gap/difference value with direction awareness.
 * Shows + or - prefix, abbreviated, with polarity context.
 */
export function formatGap(
  value: number,
  metricName: string,
  polarity: number = 1
): string {
  if (value === null || value === undefined || isNaN(value)) return '—'
  const formatted = formatMetricValue(metricName, Math.abs(value))
  const sign = value >= 0 ? '+' : '-'
  const direction = (value >= 0 && polarity === 1) ||
                    (value < 0 && polarity === -1)
    ? '▲ ahead'
    : '▼ behind'
  return `${sign}${formatted} (${direction} peer median)`
}
