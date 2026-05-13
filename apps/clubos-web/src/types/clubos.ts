export type PriorityCategory =
  | "growth risk"
  | "conversion weakness"
  | "benchmark underperformance"
  | "engagement opportunity"
  | "resilience concern";

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
