import type {
  PriorityListResponse,
  PriorityDetail,
  HealthSummary,
  AssetHealthBreakdown,
  BenchmarkResponse,
  SignalResponse,
  BriefingResponse,
  SocialSummary,
  SocialMonthlyTrend,
  SocialPlatformBreakdownResponse,
  SocialContentPerformanceResponse,
  ContentIntelligenceResponse,
  ContentCommercialSummary,
  ContentMonthlyPerformance,
  SocialAnomalyListResponse,
  DayOfWeekAnalysisResponse,
  MatchMomentAnalysisResponse,
  FormatPerformanceResponse,
  HashtagPerformanceResponse,
  DynamicInsightsResponse,
  ContentRecommendationsResponse,
  PeerComparisonResponse,
} from "../types/clubos";
import type {
  EventListResponse,
  EventSchema,
  EventCreateSchema,
} from "../types/events";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export interface ScoringConfig {
  formula_weights: {
    severity: number;
    persistence: number;
    peer_gap: number;
    commercial: number;
    evidence: number;
  };
  severity_z_score_max: number;
  persistence_window_months: number;
  peer_rank_scores: Record<string, number>;
  evidence_max_count: number;
  health_status_thresholds: {
    review_below: number;
    good_above: number;
  };
}

export async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed for ${path}`);
  }
  return response.json() as Promise<T>;
}

export async function getLatestPriorities(): Promise<PriorityListResponse> {
  return fetchJson<PriorityListResponse>("/priorities/latest");
}

export async function getPriorityDetail(priorityId: string): Promise<PriorityDetail> {
  return fetchJson<PriorityDetail>(`/priorities/${priorityId}`);
}

export async function getHealthSummary(): Promise<HealthSummary> {
  return fetchJson<HealthSummary>("/health/summary");
}

export async function getAssetHealthBreakdown(): Promise<AssetHealthBreakdown> {
  return fetchJson<AssetHealthBreakdown>("/health/assets");
}

export async function getBenchmark(asset: string, metric: string): Promise<BenchmarkResponse> {
  return fetchJson<BenchmarkResponse>(`/benchmark/${asset}/${metric}`);
}

export interface AvailableMetric {
  asset_name: string;
  metric_name: string;
  label: string;
  asset_label: string;
}

export async function getAvailableMetrics(): Promise<AvailableMetric[]> {
  return fetchJson<AvailableMetric[]>("/benchmark/available-metrics");
}

export async function getSignals(signalType?: string): Promise<SignalResponse> {
  const params = new URLSearchParams();
  if (signalType) params.append("signal_type", signalType);
  const queryString = params.toString();
  return fetchJson<SignalResponse>(`/signals${queryString ? `?${queryString}` : ""}`);
}

export async function getLatestBriefing(): Promise<BriefingResponse> {
  return fetchJson<BriefingResponse>("/briefing/latest");
}

export async function fetchEvents(filters?: { category?: string; year?: string }): Promise<EventListResponse> {
  const params = new URLSearchParams();
  if (filters?.category) params.append("category", filters.category);
  if (filters?.year) params.append("year", filters.year);
  const queryString = params.toString();
  return fetchJson<EventListResponse>(`/events${queryString ? `?${queryString}` : ""}`);
}

export async function fetchEventsForMonth(month: string): Promise<EventListResponse> {
  return fetchJson<EventListResponse>(`/events/${month}`);
}

export async function createEvent(data: EventCreateSchema): Promise<EventSchema> {
  const response = await fetch(`${API_BASE_URL}/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to create event`);
  }
  return response.json() as Promise<EventSchema>;
}

export async function deleteEvent(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/events/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(`Failed to delete event`);
  }
}

export async function fetchEventsNearMetric(asset: string, metric: string, month: string): Promise<EventListResponse> {
  return fetchJson<EventListResponse>(`/events/near/${asset}/${metric}/${month}`);
}

export async function fetchSeasonalBaseline(asset: string, metric: string): Promise<any> {
  return fetchJson<any>(`/analytics/seasonal/${asset}/${metric}`);
}

// Social Media API calls (V1.6.1)
export async function fetchSocialSummary(month?: string): Promise<SocialSummary> {
  const url = month ? `/social/summary?month=${month}` : "/social/summary";
  return fetchJson<SocialSummary>(url);
}

export async function fetchSocialMonthly(): Promise<SocialMonthlyTrend> {
  return fetchJson<SocialMonthlyTrend>("/social/monthly");
}

export async function fetchSocialPlatforms(month: string): Promise<SocialPlatformBreakdownResponse> {
  return fetchJson<SocialPlatformBreakdownResponse>(`/social/platforms/${month}`);
}

export async function fetchSocialContent(month: string): Promise<SocialContentPerformanceResponse> {
  return fetchJson<SocialContentPerformanceResponse>(`/social/content/${month}`);
}

// Social Benchmark API calls (V1.6.3)
export async function getSocialBenchmark(metric: string, month?: string): Promise<SocialBenchmarkResponse> {
  const params = new URLSearchParams();
  if (month) params.append("month", month);
  const queryString = params.toString();
  return fetchJson<SocialBenchmarkResponse>(`/benchmark/social/${metric}${queryString ? `?${queryString}` : ""}`);
}

export async function getSocialBenchmarkTrend(metric: string): Promise<SocialBenchmarkTrendResponse> {
  return fetchJson<SocialBenchmarkTrendResponse>(`/benchmark/social/${metric}/trend`);
}

export async function getSocialBenchmarkSummary(): Promise<SocialBenchmarkSummaryResponse> {
  return fetchJson<SocialBenchmarkSummaryResponse>("/benchmark/social/summary");
}

// Content Intelligence API calls (V1.6.4)
export async function fetchContentIntelligence(): Promise<ContentIntelligenceResponse> {
  return fetchJson<ContentIntelligenceResponse>("/social/content-intelligence");
}

export async function fetchContentIntelligenceSummary(): Promise<ContentCommercialSummary> {
  return fetchJson<ContentCommercialSummary>("/social/content-intelligence/summary");
}

export async function fetchContentIntelligenceMonth(month: string): Promise<ContentMonthlyPerformance> {
  return fetchJson<ContentMonthlyPerformance>(`/social/content-intelligence/${month}`);
}

// Social Anomaly API calls (V1.6.5)
export async function fetchSocialAnomalies(): Promise<SocialAnomalyListResponse> {
  return fetchJson<SocialAnomalyListResponse>("/social/anomalies");
}

export async function fetchUnconfirmedAnomalies(): Promise<SocialAnomalyListResponse> {
  return fetchJson<SocialAnomalyListResponse>("/social/anomalies/unconfirmed");
}

export async function confirmAnomaly(
  month: string,
  data: {
    confirmed_name: string;
    confirmed_category: string;
    description: string;
    impact_magnitude: string;
    affected_assets: string;
  }
): Promise<EventSchema> {
  const response = await fetch(`${API_BASE_URL}/social/anomalies/${month}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to confirm anomaly`);
  }
  return response.json() as Promise<EventSchema>;
}

export async function dismissAnomaly(month: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/social/anomalies/${month}/dismiss`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`Failed to dismiss anomaly`);
  }
}

// International Audience API calls (V1.6.6)
export async function fetchInternationalBreakdown(month?: string): Promise<InternationalBreakdownResponse> {
  const url = month ? `/social/international?month=${month}` : "/social/international";
  return fetchJson<InternationalBreakdownResponse>(url);
}

export async function fetchInternationalTrend(): Promise<InternationalTrendResponse> {
  return fetchJson<InternationalTrendResponse>("/social/international/trend");
}

export async function fetchInternationalCorrelation(): Promise<InternationalCommercialCorrelationResponse> {
  return fetchJson<InternationalCommercialCorrelationResponse>("/social/international/correlation");
}

export async function fetchMarketGrowthRanking(compareMonth?: string): Promise<MarketGrowthRankingResponse> {
  const url = compareMonth
    ? `/social/international/growth?compare_month=${compareMonth}`
    : "/social/international/growth";
  return fetchJson<MarketGrowthRankingResponse>(url);
}

// Social Analytics Intelligence API calls (V1.7)
export async function fetchDayOfWeekAnalysis(platform = "all", matchMoment = "all"): Promise<DayOfWeekAnalysisResponse> {
  const params = new URLSearchParams();
  if (platform !== "all") params.append("platform", platform);
  if (matchMoment !== "all") params.append("match_moment", matchMoment);
  const queryString = params.toString();
  return fetchJson<DayOfWeekAnalysisResponse>(`/social/analytics/dayofweek${queryString ? `?${queryString}` : ""}`);
}

export async function fetchMatchMomentAnalysis(platform = "all"): Promise<MatchMomentAnalysisResponse> {
  const params = new URLSearchParams();
  if (platform !== "all") params.append("platform", platform);
  const queryString = params.toString();
  return fetchJson<MatchMomentAnalysisResponse>(`/social/analytics/moments${queryString ? `?${queryString}` : ""}`);
}

export async function fetchFormatPerformance(platform = "all", scene?: string): Promise<FormatPerformanceResponse> {
  const params = new URLSearchParams();
  if (platform !== "all") params.append("platform", platform);
  if (scene) params.append("scene", scene);
  const queryString = params.toString();
  return fetchJson<FormatPerformanceResponse>(`/social/analytics/formats${queryString ? `?${queryString}` : ""}`);
}

export async function fetchHashtagPerformance(
  platform = "all",
  hashtagType = "all",
  minPosts = 10
): Promise<HashtagPerformanceResponse> {
  const params = new URLSearchParams();
  if (platform !== "all") params.append("platform", platform);
  if (hashtagType !== "all") params.append("hashtag_type", hashtagType);
  params.append("min_posts", minPosts.toString());
  const queryString = params.toString();
  return fetchJson<HashtagPerformanceResponse>(`/social/analytics/hashtags${queryString ? `?${queryString}` : ""}`);
}

export async function fetchDynamicInsights(dataMonth?: string): Promise<DynamicInsightsResponse> {
  const params = new URLSearchParams();
  if (dataMonth) params.append("data_month", dataMonth);
  const queryString = params.toString();
  return fetchJson<DynamicInsightsResponse>(`/social/analytics/insights${queryString ? `?${queryString}` : ""}`);
}

export async function fetchContentRecommendations(team = "content"): Promise<ContentRecommendationsResponse> {
  const params = new URLSearchParams();
  if (team !== "content") params.append("team", team);
  const queryString = params.toString();
  return fetchJson<ContentRecommendationsResponse>(`/social/analytics/recommendations${queryString ? `?${queryString}` : ""}`);
}

export async function fetchPeerComparison(metric: string): Promise<PeerComparisonResponse> {
  return fetchJson<PeerComparisonResponse>(`/social/analytics/peer/${metric}`);
}

export async function fetchScoringConfig(): Promise<ScoringConfig> {
  return fetchJson<ScoringConfig>("/config/scoring");
}
