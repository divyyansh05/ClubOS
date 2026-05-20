export type PriorityCategory =
  | "growth risk"
  | "conversion weakness"
  | "benchmark underperformance"
  | "engagement opportunity"
  | "resilience concern"
  | "social engagement"; // V1.7 — Social media priorities

export interface ScoreBreakdown {
  severity: number;
  persistence: number;
  peer_gap: number;
  commercial: number;
  evidence: number;
}

export interface HistoricalValue {
  month: string;
  value: number;
}

export interface PeerValue {
  club: string;
  value: number;
}

export interface PriorityCard {
  priority_id: string;
  month: string;
  title: string;
  category: string;
  score: number;
  rank: number;
  asset_name: string;
  primary_metric: string;
  summary_text: string;
  why_it_matters: string;
  suggested_next_investigation: string;
  // New enriched fields
  consecutive_declining_months?: number | null;
  trend_direction?: string | null;
  trend_slope?: number | null;
  score_breakdown?: ScoreBreakdown | null;
  historical_values?: HistoricalValue[] | null;
  peer_values?: PeerValue[] | null;
  peer_median?: number | null;
  peer_leader_value?: number | null;
}

export interface PriorityListResponse {
  latest_month: string;
  items: PriorityCard[];
}

export interface PriorityDetail {
  priority_id: string;
  month: string;
  title: string;
  category: string;
  score: number;
  rank: number;
  asset_name: string;
  primary_metric: string;
  summary_text: string;
  why_it_matters: string;
  suggested_next_investigation: string;
  supporting_metrics: Record<string, any>;
  // New enriched fields
  consecutive_declining_months?: number | null;
  trend_direction?: string | null;
  trend_slope?: number | null;
  score_breakdown?: ScoreBreakdown | null;
  historical_values?: HistoricalValue[] | null;
  peer_values?: PeerValue[] | null;
  peer_median?: number | null;
  peer_leader_value?: number | null;
}

export interface HealthSummary {
  latest_month: string;
  metric_count: number;
  good_count: number;
  review_count: number;
  stable_count: number;
  avg_abs_deviation: number | null;
}

export interface AssetHealthStats {
  metric_count: number;
  good_count: number;
  review_count: number;
  stable_count: number;
  health_percentage: number;
}

export interface AssetHealthBreakdown {
  assets: Record<string, AssetHealthStats>;
}

export interface BenchmarkPoint {
  month: string;
  rm_value: number;
  peer_median: number;
  peer_leader_value: number;
  rm_rank: number;
  club_count: number;
  gap_to_peer_median: number;
  gap_to_leader: number;
  rank_change_12m: number | null;
  gap_change_12m: number | null;
}

export interface BenchmarkResponse {
  asset: string;
  metric: string;
  latest_month: string | null;
  points: BenchmarkPoint[];
}

export interface PriorityConnection {
  has_connection: boolean;
  metric?: string | null;
  rank?: number | null;
  score?: number | null;
  interpretation: string;
  border_color: string;
}

export interface SignalItem {
  signal_id: string;
  source_asset: string;
  source_metric: string;
  target_asset: string;
  target_metric: string;
  lag_months: number;
  relationship_direction: string;
  strength_score: number;
  validation_status: string;
  business_interpretation: string;
  last_validated_month: string;
  // New enriched fields
  current_status?: string | null;
  status_meaning?: string | null;
  source_trend_direction?: string | null;
  source_current_trend?: number | null;
  source_trend_pct_change?: number | null;
  source_current_value?: number | null;
  target_current_value?: number | null;
  target_health_status?: string | null;
  priority_connection?: PriorityConnection | null;
  // V1.5.5: Driver/Outcome Variable Labelling
  driver_label?: string;
  outcome_label?: string;
  causal_direction_statement?: string | null;
  action_statement?: string | null;
  relationship_type?: string | null;
  // V1.6.2: Signal Type Classification
  signal_type?: string | null;
}

export interface SignalResponse {
  latest_validated_month: string | null;
  items: SignalItem[];
}

export interface BriefingPriority {
  priority_id: string;
  priority_rank: number;
  priority_title: string;
  priority_category: string;
  priority_score: number;
}

export interface BriefingAnomaly {
  anomaly_rank: number;
  asset_name: string;
  metric_name: string;
  metric_value: number;
  deviation_from_seasonal_baseline: number;
}

export interface BriefingSignal {
  signal_rank: number;
  signal_id: string;
  source_asset: string;
  source_metric: string;
  target_asset: string;
  target_metric: string;
  lag_months: number;
  relationship_direction: string;
  strength_score: number;
}

export interface BriefingBenchmarkSummary {
  benchmarked_metric_count: number;
  benchmark_underperformance_count: number;
  avg_gap_to_peer_median: number;
  worst_gap_to_peer_median: number;
}

export interface BriefingHealthSummary {
  metric_count: number;
  good_count: number;
  review_count: number;
  stable_count: number;
  avg_abs_deviation: number;
}

export interface BriefingResponse {
  month: string;
  top_priorities: BriefingPriority[];
  top_anomalies: BriefingAnomaly[];
  strongest_signals: BriefingSignal[];
  benchmark_summary: BriefingBenchmarkSummary | null;
  health_summary: BriefingHealthSummary | null;
}

// ========================================
// Social Media Types (V1.6.1)
// ========================================

export interface SocialMetrics {
  month: string;
  asset_name: string;
  total_posts: number;
  total_engagement: number;
  avg_engagement_per_post: number;
  total_likes: number;
  total_comments: number;
  total_reposts: number;
  total_saves: number;
  total_estimated_views: number;
  total_estimated_impressions: number;
  instagram_posts: number;
  instagram_engagement: number;
  instagram_avg_engagement: number;
  instagram_engagement_rate: number;
  tiktok_posts: number;
  tiktok_engagement: number;
  tiktok_avg_engagement: number;
  tiktok_engagement_rate: number;
  x_posts: number;
  x_engagement: number;
  x_avg_engagement: number;
  x_engagement_rate: number;
  facebook_posts: number;
  facebook_engagement: number;
  facebook_avg_engagement: number;
  facebook_engagement_rate: number;
  youtube_posts: number;
  youtube_engagement: number;
  youtube_avg_engagement: number;
  goal_celebration_avg_engagement: number;
  training_avg_engagement: number;
  score_graphic_avg_engagement: number;
  player_arrival_avg_engagement: number;
  lineup_graphic_avg_engagement: number;
  birthday_avg_engagement: number;
  game_preview_avg_engagement: number;
  spanish_account_engagement: number;
  english_account_engagement: number;
  arabic_account_engagement: number;
  french_account_engagement: number;
  other_account_engagement: number;
  international_engagement_ratio: number;
  top_performing_platform: string;
  top_performing_content_type: string;
}

export interface SocialPlatformData {
  platform: string;
  posts: number;
  engagement: number;
  avg_engagement: number;
  engagement_rate: number | null;
}

export interface SocialContentData {
  content_type: string;
  avg_engagement: number;
}

export interface SocialSummary {
  latest_month: string;
  total_engagement: number;
  total_engagement_mom_change: number | null;
  avg_engagement_per_post: number;
  avg_engagement_per_post_mom_change: number | null;
  instagram_engagement_rate: number;
  instagram_engagement_rate_mom_change: number | null;
  international_engagement_ratio: number;
  international_engagement_ratio_mom_change: number | null;
  total_posts: number;
  top_performing_platform: string;
  top_performing_content_type: string;
}

export interface SocialMonthlyTrend {
  months: string[];
  total_engagement: number[];
  avg_engagement_per_post: number[];
  total_posts: number[];
  // Platform-level data for multi-line charts
  instagram_engagement: number[];
  tiktok_engagement: number[];
  x_engagement: number[];
  facebook_engagement: number[];
  youtube_engagement: number[];
}

export interface SocialPlatformBreakdownResponse {
  month: string;
  platforms: SocialPlatformData[];
}

export interface SocialContentPerformanceResponse {
  month: string;
  content_types: SocialContentData[];
}

// ========================================
// Social Benchmark Types (V1.6.3)
// ========================================

export interface SocialBenchmarkEntry {
  club: string;
  value: number;
  rank: number;
  is_real_madrid: boolean;
}

export interface SocialBenchmarkResponse {
  metric: string;
  month: string | null;
  clubs: SocialBenchmarkEntry[];
  rm_rank: number | null;
  rm_value: number | null;
  peer_median: number | null;
  peer_leader_club: string | null;
  peer_leader_value: number | null;
  gap_to_median: number | null;
  gap_to_leader: number | null;
  club_count: number;
}

export interface SocialBenchmarkTrendPoint {
  month: string;
  rm_rank: number | null;
  rm_value: number | null;
}

export interface SocialBenchmarkTrendResponse {
  metric: string;
  months: SocialBenchmarkTrendPoint[];
}

export interface SocialBenchmarkMetricSummary {
  metric: string;
  rm_rank: number | null;
  rm_value: number | null;
  peer_median: number | null;
  gap_to_median: number | null;
  status: string;
}

export interface SocialBenchmarkSummaryResponse {
  latest_month: string | null;
  metrics: SocialBenchmarkMetricSummary[];
}

// ========================================
// Content Intelligence Types (V1.6.4)
// ========================================

export interface ContentSignal {
  content_type: string;
  commercial_metric: string;
  commercial_asset: string;
  correlation: number;
  lag_months: number;
  direction: string;
  interpretation: string;
  strength_label: string;
  confidence_note: string;
  avg_content_engagement: number;
  sample_size_months: number;
}

export interface ContentCommercialSummary {
  strongest_signal: ContentSignal | null;
  total_correlations_found: number;
  avg_correlation_strength: number;
  most_predictive_content_type: string;
  most_influenced_commercial_metric: string;
}

export interface ContentMonthlyPerformance {
  month: string;
  content_performances: Array<{ content_type: string; avg_engagement: number }>;
  commercial_outcomes: Array<{
    metric: string;
    asset: string;
    value: number;
    vs_baseline_pct: number | null;
  }>;
  matching_correlations: string[];
}

export interface ContentIntelligenceResponse {
  latest_month: string;
  signals: ContentSignal[];
  summary: ContentCommercialSummary;
}

// ========================================
// Social Anomaly Types (V1.6.5)
// ========================================

export interface SocialAnomaly {
  month: string;
  metric: string;
  actual_value: number;
  mean_value: number;
  std_value: number;
  z_score: number;
  direction: string;  // "spike" or "drop"
  likely_cause: string;
  candidate_event_name: string;
  candidate_category: string;
  is_confirmed: boolean;
  confidence_level: string;  // "high", "medium", "low"
}

export interface SocialAnomalyListResponse {
  total_count: number;
  items: SocialAnomaly[];
}

// ========================================
// International Audience Types (V1.6.6)
// ========================================

export interface LanguageBreakdown {
  language: string;
  account_username: string | null;
  monthly_engagement: number;
  follower_count: number | null;
  engagement_per_follower: number | null;
  pct_of_total_engagement: number;
  mom_change: number | null;
}

export interface InternationalBreakdownResponse {
  month: string;
  language_markets: LanguageBreakdown[];
  total_international_engagement: number;
  international_engagement_ratio: number;
}

export interface InternationalTrendPoint {
  month: string;
  spanish_engagement: number;
  english_engagement: number;
  arabic_engagement: number;
  french_engagement: number;
  other_engagement: number;
  international_ratio: number;
}

export interface InternationalTrendResponse {
  trend: InternationalTrendPoint[];
}

export interface MarketGrowthRanking {
  market: string;
  this_month: number;
  prior_month: number;
  mom_change_pct: number;
}

export interface MarketGrowthRankingResponse {
  month: string;
  rankings: MarketGrowthRanking[];
}

export interface InternationalCommercialCorrelation {
  commercial_metric: string;
  commercial_asset: string;
  correlation: number;
  lag_months: number;
  direction: string;
  strength_label: string;
  interpretation: string;
  passes_threshold: boolean;
}

export interface InternationalCommercialCorrelationResponse {
  correlations: InternationalCommercialCorrelation[];
  strongest_correlation: InternationalCommercialCorrelation | null;
}

// V1.7 — Social Analytics Intelligence Types

export interface DayOfWeekPerformance {
  day_of_week: string;
  day_number: number;
  avg_engagement_per_post: number;
  post_count: number;
  vs_weekly_average_pct: number;
  best_platform_on_this_day: string;
}

export interface DayOfWeekAnalysisResponse {
  days: DayOfWeekPerformance[];
  best_day: string | null;
  worst_day: string | null;
  best_day_avg: number;
  worst_day_avg: number;
  weekly_average: number;
}

export interface MatchMomentPerformance {
  moment: string;
  label: string;
  avg_engagement: number;
  post_count: number;
  pct_of_total_posts: number;
  vs_non_matchday_multiplier: number;
  opportunity_gap: string;
}

export interface MatchMomentAnalysisResponse {
  moments: MatchMomentPerformance[];
  underutilised_moments: MatchMomentPerformance[];
  biggest_multiplier: {
    moment: string;
    multiplier: number;
  } | null;
}

export interface FormatPerformance {
  variety: string;
  label: string;
  platform: string;
  avg_engagement: number;
  post_count: number;
  vs_standard_post_multiplier: number;
  recommended: boolean;
}

export interface FormatPerformanceResponse {
  formats: FormatPerformance[];
  top_format: string | null;
  top_format_multiplier: number;
  underused_high_performers: FormatPerformance[];
}

export interface HashtagPerformance {
  hashtag: string;
  avg_engagement: number;
  post_count: number;
  hashtag_type: string;
  vs_no_hashtag_baseline: number;
  trend: string;
}

export interface HashtagPerformanceResponse {
  hashtags: HashtagPerformance[];
  top_hashtag_overall: string | null;
  top_evergreen_hashtag: string | null;
  top_branded_hashtag: string | null;
  top_player_hashtag: string | null;
}

export interface InsightCard {
  insight_id: string;
  category: "timing" | "format" | "content" | "hashtag" | "peer";
  priority: "critical" | "high" | "medium";
  headline: string;
  finding: string;
  evidence: string;
  recommendation: string;
  impact_estimate: string;
  data_source: string;
  refreshes_with_new_data: boolean;
}

export interface DynamicInsightsResponse {
  insights: InsightCard[];
  total_count: number;
}

export interface ContentRecommendation {
  rank: number;
  action: "CONVERT" | "SCHEDULE" | "INCREASE" | "REDUCE";
  title: string;
  rationale: string;
  expected_impact: string;
  effort_estimate: "low" | "medium" | "high";
  evidence_summary: string;
  category: "format" | "timing" | "content_type" | "hashtag";
}

export interface ContentRecommendationsResponse {
  recommendations: ContentRecommendation[];
  total_count: number;
}

export interface PeerComparisonClub {
  club: string;
  value: number;
}

export interface PeerComparisonResponse {
  metric: string;
  clubs: PeerComparisonClub[];
  real_madrid_rank: number | null;
  peer_median: number | null;
  peer_leader: string | null;
  peer_leader_value: number | null;
}
