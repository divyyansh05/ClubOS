import { useEffect, useState } from "react";
import {
  fetchSocialSummary,
  fetchSocialMonthly,
  fetchSocialPlatforms,
  fetchSocialContent,
  fetchContentIntelligence,
  fetchInternationalBreakdown,
  fetchMarketGrowthRanking,
  fetchInternationalCorrelation,
  fetchDynamicInsights,
  fetchContentRecommendations,
  fetchDayOfWeekAnalysis,
  fetchMatchMomentAnalysis,
  fetchFormatPerformance,
  fetchHashtagPerformance,
} from "../../lib/api";
import type {
  SocialSummary,
  SocialMonthlyTrend,
  SocialPlatformData,
  SocialContentData,
  ContentIntelligenceResponse,
  ContentSignal,
  InternationalBreakdownResponse,
  MarketGrowthRankingResponse,
  InternationalCommercialCorrelationResponse,
  DynamicInsightsResponse,
  ContentRecommendationsResponse,
  DayOfWeekAnalysisResponse,
  MatchMomentAnalysisResponse,
  FormatPerformanceResponse,
  HashtagPerformanceResponse,
  InsightCard,
} from "../../types/clubos";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

export default function SocialIntelligencePage() {
  const [summary, setSummary] = useState<SocialSummary | null>(null);
  const [monthlyTrend, setMonthlyTrend] = useState<SocialMonthlyTrend | null>(null);
  const [platformData, setPlatformData] = useState<SocialPlatformData[]>([]);
  const [contentData, setContentData] = useState<SocialContentData[]>([]);
  const [contentIntelligence, setContentIntelligence] = useState<ContentIntelligenceResponse | null>(null);
  const [selectedSignal, setSelectedSignal] = useState<ContentSignal | null>(null);
  const [internationalData, setInternationalData] = useState<InternationalBreakdownResponse | null>(null);
  const [marketGrowth, setMarketGrowth] = useState<MarketGrowthRankingResponse | null>(null);
  const [internationalCorrelation, setInternationalCorrelation] = useState<InternationalCommercialCorrelationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [guideExpanded, setGuideExpanded] = useState(false);
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(["all"]);
  const [expandedStatCard, setExpandedStatCard] = useState<string | null>(null);
  const [platformMetricView, setPlatformMetricView] = useState<"avg" | "total">("avg");
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null); // YYYY-MM format
  const [selectedContentType, setSelectedContentType] = useState<string | null>(null);
  const [marketCompareMode, setMarketCompareMode] = useState<"mom" | "yoy" | "custom">("mom");
  const [marketCompareMonth, setMarketCompareMonth] = useState<string | null>(null);

  // V1.7 — Analytics data state
  const [insights, setInsights] = useState<DynamicInsightsResponse | null>(null);
  const [recommendations, setRecommendations] = useState<ContentRecommendationsResponse | null>(null);
  const [dayOfWeekData, setDayOfWeekData] = useState<DayOfWeekAnalysisResponse | null>(null);
  const [matchMomentData, setMatchMomentData] = useState<MatchMomentAnalysisResponse | null>(null);
  const [formatData, setFormatData] = useState<FormatPerformanceResponse | null>(null);
  const [hashtagData, setHashtagData] = useState<HashtagPerformanceResponse | null>(null);
  const [insightFilter, setInsightFilter] = useState<string>("all");
  const [hashtagFilter, setHashtagFilter] = useState<string>("all");
  const [expandedInsight, setExpandedInsight] = useState<string | null>(null);
  const [expandedHashtag, setExpandedHashtag] = useState<string | null>(null);

  // Dark mode detection and chart colors
  const isDark = document.documentElement.classList.contains('dark');
  const chartColors = {
    axis: isDark ? '#A0A0A0' : '#666666',
    grid: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
    text: isDark ? '#D0D0D0' : '#333333',
    tooltipBg: isDark ? '#2A2A2A' : '#FFFFFF',
    tooltipBorder: isDark ? '#444444' : '#CCCCCC',
    tooltipText: isDark ? '#FFFFFF' : '#000000',
  };

  useEffect(() => {
    async function loadData() {
      try {
        const [
          summaryData,
          trendData,
          intelligenceData,
          internationalBreakdown,
          growthRanking,
          correlationData,
          insightsData,
          recommendationsData,
          dayOfWeekAnalysis,
          matchMomentAnalysis,
          formatPerformance,
          hashtagPerformance,
        ] = await Promise.all([
          fetchSocialSummary(),
          fetchSocialMonthly(),
          fetchContentIntelligence(),
          fetchInternationalBreakdown(),
          fetchMarketGrowthRanking(),
          fetchInternationalCorrelation(),
          fetchDynamicInsights(),
          fetchContentRecommendations(),
          fetchDayOfWeekAnalysis(),
          fetchMatchMomentAnalysis(),
          fetchFormatPerformance(),
          fetchHashtagPerformance(),
        ]);

        setSummary(summaryData);
        setMonthlyTrend(trendData);
        setContentIntelligence(intelligenceData);
        setInternationalData(internationalBreakdown);
        setMarketGrowth(growthRanking);
        setInternationalCorrelation(correlationData);
        setInsights(insightsData);
        setRecommendations(recommendationsData);
        setDayOfWeekData(dayOfWeekAnalysis);
        setMatchMomentData(matchMomentAnalysis);
        setFormatData(formatPerformance);
        setHashtagData(hashtagPerformance);

        // Set initial selected signal (strongest)
        if (intelligenceData.signals.length > 0) {
          setSelectedSignal(intelligenceData.signals[0]);
        }

        // Load platform and content data for latest month
        if (summaryData.latest_month) {
          const monthStr = summaryData.latest_month.substring(0, 7); // YYYY-MM
          setSelectedMonth(monthStr); // Set initial selected month
          const [platforms, content] = await Promise.all([
            fetchSocialPlatforms(monthStr),
            fetchSocialContent(monthStr),
          ]);
          setPlatformData(platforms.platforms);
          setContentData(content.content_types);
        }
      } catch (error) {
        console.error("Failed to load social data:", error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  // Reload platform and content data when selected month changes
  useEffect(() => {
    if (!selectedMonth) return;

    async function loadMonthData() {
      try {
        const [platforms, content] = await Promise.all([
          fetchSocialPlatforms(selectedMonth),
          fetchSocialContent(selectedMonth),
        ]);
        setPlatformData(platforms.platforms);
        setContentData(content.content_types);
      } catch (error) {
        console.error("Failed to load month data:", error);
      }
    }

    loadMonthData();
  }, [selectedMonth]);

  // Reload market growth data when compare mode/month changes
  useEffect(() => {
    if (!summary) return;

    async function loadMarketGrowth() {
      try {
        let compareMonth: string | undefined = undefined;

        if (marketCompareMode === "yoy") {
          // Year-over-year: same month last year
          const latestMonth = summary.latest_month.substring(0, 7); // YYYY-MM
          const year = parseInt(latestMonth.split("-")[0]);
          const month = latestMonth.split("-")[1];
          compareMonth = `${year - 1}-${month}`;
        } else if (marketCompareMode === "custom" && marketCompareMonth) {
          compareMonth = marketCompareMonth;
        }
        // MoM: leave undefined (backend default)

        const growthData = await fetchMarketGrowthRanking(compareMonth);
        setMarketGrowth(growthData);
      } catch (error) {
        console.error("Failed to load market growth:", error);
      }
    }

    loadMarketGrowth();
  }, [marketCompareMode, marketCompareMonth, summary]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-gray-600 dark:text-gray-400">Loading social intelligence...</div>
      </div>
    );
  }

  if (!summary || !monthlyTrend) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-red-600 dark:text-red-400">Failed to load social data</div>
      </div>
    );
  }

  // Format engagement numbers
  const formatEngagement = (val: number) => {
    if (val >= 1e9) return `${(val / 1e9).toFixed(1)}B`;
    if (val >= 1e6) return `${(val / 1e6).toFixed(0)}M`;
    if (val >= 1e3) return `${(val / 1e3).toFixed(0)}K`;
    return val.toString();
  };

  const formatPercentage = (num: number) => `${(num * 100).toFixed(1)}%`;
  const formatMoMChange = (change: number | null) => {
    if (change === null) return null;
    const sign = change > 0 ? "+" : "";
    return `${sign}${change.toFixed(1)}%`;
  };

  // Prepare chart data
  const trendChartData = monthlyTrend.months.map((month, idx) => ({
    month: new Date(month).toLocaleDateString("en-US", { month: "short", year: "numeric" }),
    monthShort: new Date(month).toLocaleDateString("en-US", { month: "short" }),
    total_engagement: monthlyTrend.total_engagement[idx],
    instagram: monthlyTrend.instagram_engagement[idx],
    tiktok: monthlyTrend.tiktok_engagement[idx],
    x: monthlyTrend.x_engagement[idx],
    facebook: monthlyTrend.facebook_engagement[idx],
    youtube: monthlyTrend.youtube_engagement[idx],
    posts: monthlyTrend.total_posts[idx],
  }));

  const platformChartData = platformData
    .map((p) => ({
      name: p.platform.charAt(0).toUpperCase() + p.platform.slice(1),
      avg_engagement: p.avg_engagement,
      total_engagement: p.engagement,
      posts: p.posts,
    }))
    .sort((a, b) => {
      const aVal = platformMetricView === "avg" ? a.avg_engagement : a.total_engagement;
      const bVal = platformMetricView === "avg" ? b.avg_engagement : b.total_engagement;
      return bVal - aVal; // Descending order
    });

  const contentChartData = contentData.map((c) => ({
    name: c.content_type,
    avg_engagement: c.avg_engagement,
  }));

  // Platform filter handlers
  const handlePlatformFilterClick = (platform: string, event: React.MouseEvent) => {
    if (platform === "all") {
      setSelectedPlatforms(["all"]);
      return;
    }

    // Shift+click for multi-select
    if (event.shiftKey) {
      setSelectedPlatforms(prev => {
        const filtered = prev.filter(p => p !== "all");
        if (filtered.includes(platform)) {
          // Remove platform
          const updated = filtered.filter(p => p !== platform);
          return updated.length === 0 ? ["all"] : updated;
        } else {
          // Add platform
          return [...filtered, platform];
        }
      });
    } else {
      // Single select
      setSelectedPlatforms([platform]);
    }
  };

  // Platform opacity based on filter
  const getPlatformOpacity = (platform: string) => {
    if (selectedPlatforms.includes("all")) return 1;
    return selectedPlatforms.includes(platform) ? 1 : 0.2;
  };

  // Content type colors (consistent assignment)
  const getContentTypeColor = (contentType: string) => {
    const normalized = contentType.toLowerCase().replace(/ /g, "_");
    const colorMap: Record<string, string> = {
      score_graphic: isDark ? "#60A5FA" : "#2563EB",      // info blue
      goal_celebration: isDark ? "#22C55E" : "#16A34A",   // success green
      lineup_graphic: isDark ? "#F97316" : "#EA580C",      // warning orange
      player_arrival: isDark ? "#EF4444" : "#DC2626",      // danger red
      game_preview: "#9B59B6",                             // purple
      training: "#1ABC9C",                                 // teal
      birthday: "#F39C12",                                 // amber
    };
    return colorMap[normalized] || "#3B82F6";
  };

  // Stat card component with context and click behavior
  const StatCard = ({
    cardId,
    title,
    value,
    change,
    contextLine,
  }: {
    cardId: string;
    title: string;
    value: string;
    change: string | null;
    contextLine?: string;
  }) => {
    const isExpanded = expandedStatCard === cardId;

    return (
      <div>
        <div
          className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border-[0.5px] border-gray-300 dark:border-gray-600 cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => setExpandedStatCard(isExpanded ? null : cardId)}
          style={{ borderColor: 'var(--color-border-tertiary, #d1d5db)' }}
        >
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</h3>
          </div>
          <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">{value}</div>
          {change && (
            <div
              className={`text-sm font-semibold ${
                change.startsWith("+") || parseFloat(change) > 0
                  ? "text-green-600 dark:text-green-400"
                  : "text-red-600 dark:text-red-400"
              }`}
            >
              {change.startsWith("+") || parseFloat(change) > 0 ? "↑" : "↓"} {change} MoM
            </div>
          )}
          {contextLine && (
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">{contextLine}</p>
          )}
        </div>

        {isExpanded && (
          <div className="mt-2 p-4 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded transition-all duration-200 ease-in-out">
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {cardId === "total-engagement" && "Platform breakdown: Instagram leads with highest engagement share. Click-through analysis coming soon."}
              {cardId === "avg-per-post" && `Year average across all platforms. Individual platform performance varies.`}
              {cardId === "instagram-rate" && "Instagram's contribution to total social engagement. Dominates Real Madrid's social reach."}
              {cardId === "international" && `86.7% means ${(0.867 * 100).toFixed(0)}% of Real Madrid's audience is international. High international reach supports global eCommerce and streaming growth.`}
            </p>
          </div>
        )}
      </div>
    );
  };

  // Generate month pills data
  const availableMonths = monthlyTrend
    ? monthlyTrend.months.map((m, idx) => ({
        label: new Date(m).toLocaleDateString("en-US", { month: "short" }),
        value: m.substring(0, 7), // YYYY-MM
        isLatest: idx === monthlyTrend.months.length - 1,
      }))
    : [];

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Section 1: Header */}
      <div className="mb-6">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">Social Intelligence</h1>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          Real Madrid's social media performance across five platforms — the fifth digital pillar of ClubOS.
          55,598 posts analyzed, 4.08B total engagement in 2025.
        </p>
      </div>

      {/* Month Selector */}
      {availableMonths.length > 0 && (
        <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">2025</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {availableMonths.map((month) => (
              <button
                key={month.value}
                onClick={() => setSelectedMonth(month.value)}
                className={`px-3 py-1 rounded text-sm font-semibold transition-colors ${
                  selectedMonth === month.value
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
                }`}
              >
                {month.label}
              </button>
            ))}
          </div>
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
            Selected: {selectedMonth ? new Date(selectedMonth + "-01").toLocaleDateString("en-US", { month: "long", year: "numeric" }) : "None"} — Updates platform and content sections below
          </p>
        </div>
      )}

      {/* V1.7 Section: Dynamic Insights Panel — FIRST section for maximum visibility */}
      {insights && insights.insights.length > 0 && (
        <div className="mb-12">
          <div className="mb-6">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              INSIGHTS — What the data is telling you
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Auto-generated from {insights.total_count} insights across 55,598 posts. Updates when new data is uploaded.
            </p>
          </div>

          {/* Filter pills */}
          <div className="flex flex-wrap gap-2 mb-6">
            {["all", "timing", "format", "content", "hashtag", "peer"].map((filter) => (
              <button
                key={filter}
                onClick={() => setInsightFilter(filter)}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
                  insightFilter === filter
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
                }`}
              >
                {filter === "all" ? "All Insights" : filter.charAt(0).toUpperCase() + filter.slice(1)}
              </button>
            ))}
          </div>

          {/* Insight cards grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {insights.insights
              .filter((insight) => insightFilter === "all" || insight.category === insightFilter)
              .map((insight) => (
                <div
                  key={insight.insight_id}
                  className="border border-gray-300 dark:border-gray-600 rounded-lg p-6 bg-white dark:bg-gray-800 shadow-sm hover:shadow-md transition-shadow"
                >
                  {/* Header row */}
                  <div className="flex items-center justify-between mb-4">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${
                        insight.priority === "critical"
                          ? "bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300"
                          : insight.priority === "high"
                          ? "bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300"
                          : "bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300"
                      }`}
                    >
                      {insight.priority}
                    </span>
                    <span className="text-2xl">
                      {insight.category === "timing"
                        ? "⏰"
                        : insight.category === "format"
                        ? "🖼️"
                        : insight.category === "content"
                        ? "📊"
                        : insight.category === "hashtag"
                        ? "#"
                        : "👥"}
                    </span>
                  </div>

                  {/* Headline */}
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">
                    {insight.headline}
                  </h3>

                  {/* Finding */}
                  <p className="text-sm text-gray-700 dark:text-gray-300 mb-4 leading-relaxed">
                    {insight.finding}
                  </p>

                  {/* Evidence strip */}
                  <div className="p-3 bg-gray-100 dark:bg-gray-700 rounded mb-4 font-mono text-xs text-gray-800 dark:text-gray-200">
                    <strong>Evidence:</strong> {insight.evidence}
                  </div>

                  {/* Recommendation button */}
                  <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border-l-4 border-amber-500 rounded mb-3">
                    <div className="flex items-start gap-2">
                      <span className="text-lg">💡</span>
                      <div>
                        <div className="font-semibold text-amber-900 dark:text-amber-300 text-sm mb-1">
                          Recommendation
                        </div>
                        <div className="text-sm text-amber-800 dark:text-amber-400">
                          {insight.recommendation}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Impact estimate */}
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                    <strong>Impact:</strong> {insight.impact_estimate}
                  </p>

                  {/* Data source tag */}
                  <p className="text-xs text-gray-500 dark:text-gray-500 italic">
                    {insight.data_source}
                  </p>

                  {/* Expandable detail (optional for future) */}
                  <button
                    onClick={() =>
                      setExpandedInsight(expandedInsight === insight.insight_id ? null : insight.insight_id)
                    }
                    className="mt-3 text-xs text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    {expandedInsight === insight.insight_id ? "Hide details ↑" : "View detailed analysis →"}
                  </button>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* V1.7 Section: Content Team Recommendations */}
      {recommendations && recommendations.recommendations.length > 0 && (
        <div className="mb-12">
          <div className="mb-6">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              RECOMMENDATIONS — For the content team
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Priority-ranked actions based on 2025 performance data. Updated automatically when new data is available.
            </p>
          </div>

          {/* Recommendations list */}
          <div className="space-y-4">
            {recommendations.recommendations.map((rec) => (
              <div
                key={rec.rank}
                className="border border-gray-300 dark:border-gray-600 rounded-lg p-6 bg-white dark:bg-gray-800 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="flex items-start gap-4">
                  {/* Rank badge */}
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 rounded-full bg-blue-600 text-white flex items-center justify-center text-xl font-bold">
                      {rec.rank}
                    </div>
                  </div>

                  <div className="flex-1">
                    {/* Action label */}
                    <div className="mb-2">
                      <span
                        className={`px-3 py-1 rounded font-mono text-xs font-bold uppercase tracking-wider ${
                          rec.action === "CONVERT"
                            ? "bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300"
                            : rec.action === "SCHEDULE"
                            ? "bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300"
                            : rec.action === "INCREASE"
                            ? "bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300"
                            : "bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300"
                        }`}
                      >
                        {rec.action}
                      </span>
                      <span
                        className={`ml-2 px-2 py-1 rounded text-xs font-semibold ${
                          rec.effort_estimate === "low"
                            ? "bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300"
                            : rec.effort_estimate === "medium"
                            ? "bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300"
                            : "bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300"
                        }`}
                      >
                        {rec.effort_estimate.toUpperCase()} EFFORT
                      </span>
                    </div>

                    {/* Title */}
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                      {rec.title}
                    </h3>

                    {/* Rationale */}
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
                      {rec.rationale}
                    </p>

                    {/* Impact estimate box */}
                    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded mb-3">
                      <div className="text-sm text-blue-900 dark:text-blue-300">
                        <strong>Expected Impact:</strong> {rec.expected_impact}
                      </div>
                    </div>

                    {/* Evidence button */}
                    <button
                      onClick={() => {
                        // Toggle evidence visibility (implement if needed)
                      }}
                      className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      Evidence → {rec.evidence_summary}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* V1.7 Section: Day of Week Performance View */}
      <div className="mb-12">
        <div className="mb-6">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            TIMING ANALYSIS — When to post
          </h2>
        </div>

        {/* Sub-section A: Day of Week Heatmap */}
        {dayOfWeekData && (
          <div className="mb-8">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Day of Week Performance
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <th className="border border-gray-300 dark:border-gray-600 p-2 bg-gray-100 dark:bg-gray-700 text-xs font-semibold">
                      Day
                    </th>
                    {dayOfWeekData.days.map((day) => (
                      <th
                        key={day.day_of_week}
                        className="border border-gray-300 dark:border-gray-600 p-2 bg-gray-100 dark:bg-gray-700 text-xs font-semibold"
                      >
                        {day.day_of_week.substring(0, 3)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="border border-gray-300 dark:border-gray-600 p-2 text-xs font-semibold bg-gray-50 dark:bg-gray-800">
                      Avg Eng
                    </td>
                    {dayOfWeekData.days.map((day) => {
                      const opacity =
                        ((day.avg_engagement_per_post - Math.min(...dayOfWeekData.days.map((d) => d.avg_engagement_per_post))) /
                          (Math.max(...dayOfWeekData.days.map((d) => d.avg_engagement_per_post)) -
                            Math.min(...dayOfWeekData.days.map((d) => d.avg_engagement_per_post)))) *
                          0.8 +
                        0.2;

                      return (
                        <td
                          key={day.day_of_week}
                          className="border border-gray-300 dark:border-gray-600 p-3 text-center text-xs font-mono"
                          style={{
                            backgroundColor: `rgba(34, 197, 94, ${opacity})`,
                            color: opacity > 0.5 ? "white" : "black",
                          }}
                          title={`${day.day_of_week}: ${day.avg_engagement_per_post.toLocaleString()} avg engagement (${
                            day.vs_weekly_average_pct > 0 ? "+" : ""
                          }${day.vs_weekly_average_pct}% vs weekly avg)`}
                        >
                          {(day.avg_engagement_per_post / 1000).toFixed(0)}K
                        </td>
                      );
                    })}
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-3">
              <strong>Best day overall:</strong> {dayOfWeekData.best_day} (avg{" "}
              {dayOfWeekData.best_day_avg.toLocaleString()})
            </p>
          </div>
        )}

        {/* Sub-section B: Match Moment Performance Chart */}
        {matchMomentData && (
          <div className="mb-8">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Match Moment Performance
            </h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={matchMomentData.moments} layout="vertical" margin={{ left: 100 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                <XAxis type="number" tick={{ fontSize: 11 }} stroke={chartColors.axis} />
                <YAxis type="category" dataKey="label" tick={{ fontSize: 11 }} stroke={chartColors.axis} width={90} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: chartColors.tooltipBg,
                    border: `1px solid ${chartColors.tooltipBorder}`,
                    borderRadius: "4px",
                  }}
                />
                <Bar dataKey="avg_engagement" fill="#3B82F6" />
              </BarChart>
            </ResponsiveContainer>

            {/* Underutilisation Alert */}
            {matchMomentData.underutilised_moments.length > 0 && (
              <div className="mt-4 p-4 bg-amber-50 dark:bg-amber-900/20 border-l-4 border-amber-500 rounded">
                <div className="flex items-start gap-2">
                  <span className="text-xl">⚠️</span>
                  <div>
                    <div className="font-semibold text-amber-900 dark:text-amber-300 mb-2">
                      UNDERUTILISED OPPORTUNITY
                    </div>
                    {matchMomentData.underutilised_moments.map((moment) => (
                      <p key={moment.moment} className="text-sm text-amber-800 dark:text-amber-400 mb-2">
                        <strong>{moment.label}</strong> averages {moment.avg_engagement.toLocaleString()} engagement ({moment.vs_non_matchday_multiplier.toFixed(1)}x non-matchday) but represents only{" "}
                        {moment.pct_of_total_posts.toFixed(1)}% of posts. Increasing {moment.label.toLowerCase()} volume is a high-ROI opportunity.
                      </p>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Sub-section C: Format Performance Table */}
        {formatData && (
          <div className="mb-8">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Format Performance
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-gray-100 dark:bg-gray-700">
                    <th className="border border-gray-300 dark:border-gray-600 p-3 text-left text-xs font-semibold">
                      Format
                    </th>
                    <th className="border border-gray-300 dark:border-gray-600 p-3 text-left text-xs font-semibold">
                      Platform
                    </th>
                    <th className="border border-gray-300 dark:border-gray-600 p-3 text-right text-xs font-semibold">
                      Avg Eng/Post
                    </th>
                    <th className="border border-gray-300 dark:border-gray-600 p-3 text-right text-xs font-semibold">
                      Posts
                    </th>
                    <th className="border border-gray-300 dark:border-gray-600 p-3 text-right text-xs font-semibold">
                      vs Standard Post
                    </th>
                    <th className="border border-gray-300 dark:border-gray-600 p-3 text-center text-xs font-semibold">
                      Recommended
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {formatData.formats.slice(0, 10).map((format, idx) => (
                    <tr key={idx} className={idx % 2 === 0 ? "bg-white dark:bg-gray-800" : "bg-gray-50 dark:bg-gray-900"}>
                      <td className="border border-gray-300 dark:border-gray-600 p-3 text-sm font-semibold">
                        {format.label}
                      </td>
                      <td className="border border-gray-300 dark:border-gray-600 p-3 text-sm">
                        {format.platform}
                      </td>
                      <td className="border border-gray-300 dark:border-gray-600 p-3 text-sm text-right font-mono">
                        {format.avg_engagement.toLocaleString()}
                      </td>
                      <td className="border border-gray-300 dark:border-gray-600 p-3 text-sm text-right">
                        {format.post_count.toLocaleString()}
                      </td>
                      <td className="border border-gray-300 dark:border-gray-600 p-3 text-sm text-right font-bold">
                        {format.vs_standard_post_multiplier.toFixed(1)}x
                      </td>
                      <td className="border border-gray-300 dark:border-gray-600 p-3 text-center">
                        {format.recommended ? (
                          <span className="text-green-600 dark:text-green-400 text-xl">✓</span>
                        ) : format.vs_standard_post_multiplier > 1.5 ? (
                          <span className="text-amber-600 dark:text-amber-400">—</span>
                        ) : (
                          <span className="text-red-600 dark:text-red-400">✗</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-3">
              <strong>Key finding:</strong> {formatData.top_format} generates{" "}
              {formatData.top_format_multiplier.toFixed(1)}x more engagement than standard posts.
            </p>
          </div>
        )}
      </div>

      {/* V1.7 Section: Hashtag Performance Index */}
      {hashtagData && (
        <div className="mb-12">
          <div className="mb-6">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              HASHTAG INTELLIGENCE — What amplifies reach
            </h2>
          </div>

          {/* Sub-section A: Hashtag Leaderboard */}
          <div className="mb-8">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Hashtag Leaderboard
            </h3>

            {/* Filter pills */}
            <div className="flex flex-wrap gap-2 mb-4">
              {["all", "event", "player", "branded", "farewell"].map((type) => (
                <button
                  key={type}
                  onClick={() => setHashtagFilter(type)}
                  className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
                    hashtagFilter === type
                      ? "bg-blue-600 text-white"
                      : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
                  }`}
                >
                  {type === "all" ? "All" : type.charAt(0).toUpperCase() + type.slice(1)}
                </button>
              ))}
            </div>

            {/* Hashtag table */}
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-gray-100 dark:bg-gray-700">
                    <th className="border border-gray-300 dark:border-gray-600 p-3 text-left text-xs font-semibold">
                      #
                    </th>
                    <th className="border border-gray-300 dark:border-gray-600 p-3 text-left text-xs font-semibold">
                      Hashtag
                    </th>
                    <th className="border border-gray-300 dark:border-gray-600 p-3 text-right text-xs font-semibold">
                      Avg Engagement
                    </th>
                    <th className="border border-gray-300 dark:border-gray-600 p-3 text-right text-xs font-semibold">
                      Posts
                    </th>
                    <th className="border border-gray-300 dark:border-gray-600 p-3 text-left text-xs font-semibold">
                      Type
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {hashtagData.hashtags
                    .filter((ht) => hashtagFilter === "all" || ht.hashtag_type === hashtagFilter)
                    .slice(0, 15)
                    .map((hashtag, idx) => (
                      <tr
                        key={hashtag.hashtag}
                        className={`cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${
                          idx % 2 === 0 ? "bg-white dark:bg-gray-800" : "bg-gray-50 dark:bg-gray-900"
                        }`}
                        onClick={() => setExpandedHashtag(expandedHashtag === hashtag.hashtag ? null : hashtag.hashtag)}
                      >
                        <td className="border border-gray-300 dark:border-gray-600 p-3 text-sm font-bold text-gray-600 dark:text-gray-400">
                          {idx + 1}
                        </td>
                        <td className="border border-gray-300 dark:border-gray-600 p-3 text-sm font-mono font-semibold text-blue-600 dark:text-blue-400">
                          {hashtag.hashtag}
                        </td>
                        <td className="border border-gray-300 dark:border-gray-600 p-3 text-sm text-right font-mono">
                          {hashtag.avg_engagement.toLocaleString()}
                        </td>
                        <td className="border border-gray-300 dark:border-gray-600 p-3 text-sm text-right">
                          {hashtag.post_count}
                        </td>
                        <td className="border border-gray-300 dark:border-gray-600 p-3 text-sm">
                          <span
                            className={`px-2 py-1 rounded text-xs font-semibold ${
                              hashtag.hashtag_type === "farewell"
                                ? "bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300"
                                : hashtag.hashtag_type === "event"
                                ? "bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300"
                                : hashtag.hashtag_type === "player"
                                ? "bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300"
                                : hashtag.hashtag_type === "branded"
                                ? "bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300"
                                : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                            }`}
                          >
                            {hashtag.hashtag_type}
                          </span>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Sub-section B: 4-Box Category Comparison */}
          <div className="mb-8">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Hashtag Category Performance
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {["farewell", "event", "player", "branded"].map((type) => {
                const typeHashtags = hashtagData.hashtags.filter((ht) => ht.hashtag_type === type);
                const avgEngagement =
                  typeHashtags.length > 0
                    ? typeHashtags.reduce((sum, ht) => sum + ht.avg_engagement, 0) / typeHashtags.length
                    : 0;

                return (
                  <div
                    key={type}
                    className="p-4 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                  >
                    <div className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1 uppercase">
                      {type}
                    </div>
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      {avgEngagement > 0 ? (avgEngagement / 1000).toFixed(0) + "K" : "N/A"}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                      avg engagement
                    </div>
                  </div>
                );
              })}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-4">
              Farewell/tribute hashtags generate significantly more engagement than branded hashtags, indicating emotional milestone content dramatically outperforms routine promotional content.
            </p>
          </div>

          {/* Sub-section C: Top 3 Recommendations */}
          <div className="mb-8">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Hashtag Recommendations
            </h3>
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded">
              <div className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-3">
                3 hashtags your content team should prioritise:
              </div>
              <ol className="space-y-2 text-sm text-blue-800 dark:text-blue-400">
                <li>
                  <strong>1. {hashtagData.top_hashtag_overall || "#event-hashtag"}:</strong> Planned event content (El Clásico, UCL draw) — highest overall engagement
                </li>
                <li>
                  <strong>2. {hashtagData.top_player_hashtag || "#player-hashtag"}:</strong> When featuring top-performing players — strongest player engagement
                </li>
                <li>
                  <strong>3. {hashtagData.top_evergreen_hashtag || "#evergreen-hashtag"}:</strong> Always-on content — consistent performance across seasons
                </li>
              </ol>
            </div>
          </div>
        </div>
      )}

      {/* Section 2: Summary Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          cardId="total-engagement"
          title="Total Engagement"
          value={formatEngagement(summary.total_engagement)}
          change={formatMoMChange(summary.total_engagement_mom_change)}
          contextLine={`Across all platforms this month. Peak this year: ${monthlyTrend ? formatEngagement(Math.max(...monthlyTrend.total_engagement)) : "N/A"}. Current ranks ${monthlyTrend ? monthlyTrend.total_engagement.indexOf(summary.total_engagement) + 1 : "N/A"} of 12.`}
        />
        <StatCard
          cardId="avg-per-post"
          title="Avg Engagement Per Post"
          value={formatEngagement(summary.avg_engagement_per_post)}
          change={formatMoMChange(summary.avg_engagement_per_post_mom_change)}
          contextLine={`Average interaction per post across all platforms. Higher = each post reaching and resonating more. Year average: ${monthlyTrend ? formatEngagement(monthlyTrend.avg_engagement_per_post.reduce((a, b) => a + b, 0) / monthlyTrend.avg_engagement_per_post.length) : "N/A"}.`}
        />
        <StatCard
          cardId="instagram-share"
          title="Instagram Share of Total Engagement"
          value={formatPercentage(summary.instagram_engagement_rate)}
          change={formatMoMChange(summary.instagram_engagement_rate_mom_change)}
          contextLine="Instagram's contribution to total social engagement. Instagram dominates Real Madrid's social reach."
        />
        <StatCard
          cardId="international"
          title="International Engagement"
          value={formatPercentage(summary.international_engagement_ratio)}
          change={formatMoMChange(summary.international_engagement_ratio_mom_change)}
          contextLine={`Share of engagement from non-Spanish language accounts. ${(summary.international_engagement_ratio * 100).toFixed(1)}% of Real Madrid's audience is international. High international reach supports global eCommerce and streaming growth.`}
        />
      </div>

      {/* Section 3: Monthly Engagement Trend — Multi-Platform */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border-[0.5px] border-gray-300 dark:border-gray-600 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">12-Month Engagement Trend</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Click any platform to isolate. Shift+click to compare.
        </p>

        {/* Platform Filter Pills */}
        <div className="flex flex-wrap gap-2 mb-4">
          <button
            onClick={(e) => handlePlatformFilterClick("all", e)}
            className={`px-3 py-1 rounded text-sm font-semibold transition-colors ${
              selectedPlatforms.includes("all")
                ? "bg-gray-700 dark:bg-gray-600 text-white"
                : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
            }`}
          >
            All
          </button>
          <button
            onClick={(e) => handlePlatformFilterClick("instagram", e)}
            className={`px-3 py-1 rounded text-sm font-semibold transition-colors ${
              selectedPlatforms.includes("instagram")
                ? "text-white"
                : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
            }`}
            style={selectedPlatforms.includes("instagram") ? { backgroundColor: "#E1306C" } : {}}
          >
            Instagram
          </button>
          <button
            onClick={(e) => handlePlatformFilterClick("tiktok", e)}
            className={`px-3 py-1 rounded text-sm font-semibold transition-colors ${
              selectedPlatforms.includes("tiktok")
                ? "text-white"
                : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
            }`}
            style={selectedPlatforms.includes("tiktok") ? { backgroundColor: "#69C9D0" } : {}}
          >
            TikTok
          </button>
          <button
            onClick={(e) => handlePlatformFilterClick("x", e)}
            className={`px-3 py-1 rounded text-sm font-semibold transition-colors ${
              selectedPlatforms.includes("x")
                ? "text-white"
                : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
            }`}
            style={selectedPlatforms.includes("x") ? { backgroundColor: "#1DA1F2" } : {}}
          >
            X
          </button>
          <button
            onClick={(e) => handlePlatformFilterClick("facebook", e)}
            className={`px-3 py-1 rounded text-sm font-semibold transition-colors ${
              selectedPlatforms.includes("facebook")
                ? "text-white"
                : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
            }`}
            style={selectedPlatforms.includes("facebook") ? { backgroundColor: "#4267B2" } : {}}
          >
            Facebook
          </button>
          <button
            onClick={(e) => handlePlatformFilterClick("youtube", e)}
            className={`px-3 py-1 rounded text-sm font-semibold transition-colors ${
              selectedPlatforms.includes("youtube")
                ? "text-white"
                : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
            }`}
            style={selectedPlatforms.includes("youtube") ? { backgroundColor: "#FF0000" } : {}}
          >
            YouTube
          </button>
        </div>

        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={trendChartData}>
            <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
            <XAxis dataKey="monthShort" stroke={chartColors.axis} tick={{ fill: chartColors.text }} />
            <YAxis stroke={chartColors.axis} tick={{ fill: chartColors.text }} tickFormatter={(val) => formatEngagement(val)} />
            <Tooltip
              contentStyle={{
                backgroundColor: chartColors.tooltipBg,
                border: `1px solid ${chartColors.tooltipBorder}`,
                borderRadius: "8px",
                color: chartColors.tooltipText
              }}
              formatter={(value: number, name: string) => {
                return [formatEngagement(value), name];
              }}
              labelFormatter={(label) => {
                const dataPoint = trendChartData.find(d => d.monthShort === label);
                return dataPoint ? dataPoint.month : label;
              }}
            />
            <Legend wrapperStyle={{ color: chartColors.text }} />
            {/* Total as background reference line (dashed, low opacity) */}
            <Line
              type="monotone"
              dataKey="total_engagement"
              stroke="#9CA3AF"
              strokeWidth={2}
              strokeDasharray="5 5"
              name="Total"
              dot={false}
              opacity={0.3}
            />
            {/* Platform lines with brand colors */}
            <Line
              type="monotone"
              dataKey="instagram"
              stroke="#E1306C"
              strokeWidth={2}
              name="Instagram"
              dot={{ r: 4 }}
              opacity={getPlatformOpacity("instagram")}
            />
            <Line
              type="monotone"
              dataKey="tiktok"
              stroke="#69C9D0"
              strokeWidth={2}
              name="TikTok"
              dot={{ r: 4 }}
              opacity={getPlatformOpacity("tiktok")}
            />
            <Line
              type="monotone"
              dataKey="x"
              stroke="#1DA1F2"
              strokeWidth={2}
              name="X"
              dot={{ r: 4 }}
              opacity={getPlatformOpacity("x")}
            />
            <Line
              type="monotone"
              dataKey="facebook"
              stroke="#4267B2"
              strokeWidth={2}
              name="Facebook"
              dot={{ r: 4 }}
              opacity={getPlatformOpacity("facebook")}
            />
            <Line
              type="monotone"
              dataKey="youtube"
              stroke="#FF0000"
              strokeWidth={2}
              name="YouTube"
              dot={{ r: 4 }}
              opacity={getPlatformOpacity("youtube")}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Section 4: Platform Performance Breakdown */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border-[0.5px] border-gray-300 dark:border-gray-600 mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Platform Performance (Latest Month)
          </h2>
          <div className="flex gap-2">
            <button
              onClick={() => setPlatformMetricView("avg")}
              className={`px-3 py-1 rounded text-sm font-semibold transition-colors ${
                platformMetricView === "avg"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
              }`}
            >
              Avg Per Post
            </button>
            <button
              onClick={() => setPlatformMetricView("total")}
              className={`px-3 py-1 rounded text-sm font-semibold transition-colors ${
                platformMetricView === "total"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
              }`}
            >
              Total Engagement
            </button>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={platformChartData} layout="horizontal">
            <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
            <XAxis type="number" stroke={chartColors.axis} tick={{ fill: chartColors.text }} tickFormatter={(val) => formatEngagement(val)} />
            <YAxis type="category" dataKey="name" stroke={chartColors.axis} tick={{ fill: chartColors.text }} />
            <Tooltip
              contentStyle={{
                backgroundColor: chartColors.tooltipBg,
                border: `1px solid ${chartColors.tooltipBorder}`,
                borderRadius: "8px",
                color: chartColors.tooltipText
              }}
              formatter={(value: number) => formatEngagement(value)}
            />
            <Legend wrapperStyle={{ color: chartColors.text }} />
            <Bar
              dataKey={platformMetricView === "avg" ? "avg_engagement" : "total_engagement"}
              name={platformMetricView === "avg" ? "Avg Engagement Per Post" : "Total Engagement"}
              fill={(entry: any) => {
                // Use platform brand colors
                const platform = entry.name.toLowerCase();
                if (platform === "instagram") return "#E1306C";
                if (platform === "tiktok") return "#69C9D0";
                if (platform === "x") return "#1DA1F2";
                if (platform === "facebook") return "#4267B2";
                if (platform === "youtube") return "#FF0000";
                return "#3B82F6";
              }}
            />
          </BarChart>
        </ResponsiveContainer>
        <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
          Top platform: <span className="font-mono text-[10px] uppercase tracking-[1.2px] font-semibold text-gray-700 dark:text-gray-300">
            {summary.top_performing_platform}
          </span>
        </div>
      </div>

      {/* Section 5: Content Intelligence (V1.6.4) */}
      {contentIntelligence && contentIntelligence.signals.length > 0 && (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border-[0.5px] border-gray-300 dark:border-gray-600 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Content Intelligence — What Content Drives Revenue
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
            Correlation analysis between content types and commercial outcomes. Stronger correlations
            suggest content strategy decisions that may influence commercial performance.
          </p>

          {/* Sub-section A: Content Performance Ranking */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              Content Performance Ranking
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full border border-gray-300 dark:border-gray-600 text-sm">
                <thead className="bg-gray-100 dark:bg-gray-700">
                  <tr>
                    <th className="text-left p-3 border-r border-gray-300 dark:border-gray-600">Content Type</th>
                    <th className="text-right p-3 border-r border-gray-300 dark:border-gray-600">Avg Eng/Post</th>
                    <th className="text-left p-3 border-r border-gray-300 dark:border-gray-600">Correlates with</th>
                    <th className="text-center p-3 border-r border-gray-300 dark:border-gray-600">Strength</th>
                    <th className="text-center p-3 border-r border-gray-300 dark:border-gray-600">Lag</th>
                    <th className="text-center p-3">Direction</th>
                  </tr>
                </thead>
                <tbody>
                  {contentIntelligence.signals.slice(0, 7).map((signal, idx) => (
                    <tr
                      key={idx}
                      className={`cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 ${
                        idx % 2 === 0 ? "" : "bg-gray-50 dark:bg-gray-800"
                      } ${selectedSignal === signal ? "bg-blue-50 dark:bg-blue-900" : ""}`}
                      onClick={() => setSelectedSignal(signal)}
                    >
                      <td className="p-3 border-r border-gray-300 dark:border-gray-600 font-medium">
                        {signal.content_type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                      </td>
                      <td className="p-3 text-right border-r border-gray-300 dark:border-gray-600">
                        {signal.avg_content_engagement.toLocaleString()}
                      </td>
                      <td className="p-3 border-r border-gray-300 dark:border-gray-600">
                        {signal.commercial_metric} ({signal.commercial_asset})
                      </td>
                      <td className="p-3 text-center border-r border-gray-300 dark:border-gray-600">
                        <span
                          className={`px-2 py-1 rounded text-xs font-semibold ${
                            signal.strength_label === "Strong"
                              ? "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200"
                              : signal.strength_label === "Moderate"
                              ? "bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200"
                              : "bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200"
                          }`}
                        >
                          {signal.strength_label}
                        </span>
                      </td>
                      <td className="p-3 text-center border-r border-gray-300 dark:border-gray-600">{signal.lag_months}mo</td>
                      <td className="p-3 text-center">
                        {signal.direction === "positive" ? (
                          <span className="text-green-600 dark:text-green-400 font-semibold" title="Positive correlation: Higher content engagement correlates with higher outcome values">
                            ↑ Positive
                          </span>
                        ) : (
                          <span className="text-amber-600 dark:text-amber-400 font-semibold" title="Inverse relationship: Higher content engagement correlates with lower outcome values — this does not mean the outcome goes negative, just that it tends to be below average">
                            ↓ Inverse
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {selectedSignal && (
              <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950 border border-blue-300 dark:border-blue-700 rounded">
                <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
                  {selectedSignal.content_type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())} →{" "}
                  {selectedSignal.commercial_metric} ({(selectedSignal.correlation * 100).toFixed(0)}% correlation)
                </h4>
                <p className="text-sm text-blue-800 dark:text-blue-200 mb-3">
                  {selectedSignal.interpretation}
                </p>

                {/* What this means explanation */}
                <div className="mt-3 p-3 bg-white dark:bg-gray-800 border border-blue-200 dark:border-blue-800 rounded">
                  <p className="text-xs font-semibold text-blue-900 dark:text-blue-100 mb-1">
                    {selectedSignal.direction === "positive" ? "✓ Positive Signal" : "⚠️ Inverse Signal"}
                  </p>
                  <p className="text-xs text-blue-800 dark:text-blue-200">
                    {selectedSignal.direction === "positive" ? (
                      <>
                        When {selectedSignal.content_type.replace(/_/g, " ")} engagement rises, {selectedSignal.commercial_metric} tends to follow upward {selectedSignal.lag_months} month{selectedSignal.lag_months > 1 ? 's' : ''} later.
                      </>
                    ) : (
                      <>
                        This is a negative correlation (r={selectedSignal.correlation.toFixed(2)}). It does NOT mean {selectedSignal.commercial_metric} goes to zero or becomes negative.
                        It means months with very high {selectedSignal.content_type.replace(/_/g, " ")} engagement tend to coincide with below-average {selectedSignal.commercial_metric} {selectedSignal.lag_months} month{selectedSignal.lag_months > 1 ? 's' : ''} later,
                        and vice versa. Possible explanation: {selectedSignal.content_type.replace(/_/g, " ")} posts spike around major events that create unusual patterns in downstream metrics.
                        Treat as a signal to monitor, not a causal rule.
                      </>
                    )}
                  </p>
                </div>

                <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
                  {selectedSignal.confidence_note}
                </p>
              </div>
            )}
          </div>

          {/* Sub-section B: Strongest Signal Card */}
          {contentIntelligence.summary.strongest_signal && (
            <div className="mb-6 p-6 bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-950 dark:to-blue-950 border-l-4 border-green-600 dark:border-green-400 rounded">
              <h3 className="text-lg font-semibold text-green-900 dark:text-green-100 mb-2">
                Strongest Content → Commercial Signal
              </h3>
              <p className="text-base text-green-800 dark:text-green-200 mb-2">
                {contentIntelligence.summary.strongest_signal.interpretation}
              </p>
              <div className="flex items-center gap-4 text-sm">
                <span className="text-green-700 dark:text-green-300">
                  Correlation strength: <strong className="font-mono">{Math.abs(contentIntelligence.summary.strongest_signal.correlation * 100).toFixed(0)}%</strong>
                </span>
                <span className="text-green-700 dark:text-green-300">
                  Direction: <strong>{contentIntelligence.summary.strongest_signal.direction === "positive" ? "↑ Positive" : "↓ Inverse"}</strong>
                </span>
                <span className="text-green-700 dark:text-green-300">
                  Sample: {contentIntelligence.summary.strongest_signal.sample_size_months} months
                </span>
              </div>
            </div>
          )}

          {/* Sub-section C: Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded border border-gray-300 dark:border-gray-600">
              <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Total Correlations Found</div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {contentIntelligence.summary.total_correlations_found}
              </div>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded border border-gray-300 dark:border-gray-600">
              <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Most Predictive Content</div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {contentIntelligence.summary.most_predictive_content_type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
              </div>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded border border-gray-300 dark:border-gray-600">
              <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Avg Correlation</div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {(contentIntelligence.summary.avg_correlation_strength * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Section 6: Content Type Performance (Latest Month) */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border-[0.5px] border-gray-300 dark:border-gray-600 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Content Type Performance (Latest Month)
        </h2>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={contentChartData} onClick={(data) => {
            if (data && data.activePayload && data.activePayload[0]) {
              const clickedType = data.activePayload[0].payload.name;
              setSelectedContentType(selectedContentType === clickedType ? null : clickedType);
            }
          }}>
            <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
            <XAxis dataKey="name" stroke={chartColors.axis} tick={{ fill: chartColors.text }} angle={-15} textAnchor="end" height={100} />
            <YAxis stroke={chartColors.axis} tick={{ fill: chartColors.text }} tickFormatter={(val) => formatEngagement(val)} />
            <Tooltip
              contentStyle={{
                backgroundColor: chartColors.tooltipBg,
                border: `1px solid ${chartColors.tooltipBorder}`,
                borderRadius: "8px",
                color: chartColors.tooltipText
              }}
              formatter={(value: number) => formatEngagement(value)}
            />
            <Legend wrapperStyle={{ color: chartColors.text }} />
            <Bar
              dataKey="avg_engagement"
              name="Avg Engagement"
              fill={(entry: any) => getContentTypeColor(entry.name)}
              cursor="pointer"
            />
          </BarChart>
        </ResponsiveContainer>
        <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
          Top content type: <span className="font-mono text-[10px] uppercase tracking-[1.2px] font-semibold text-gray-700 dark:text-gray-300">
            {summary.top_performing_content_type}
          </span>
        </div>

        {/* Expanded Drill-Down Panel */}
        {selectedContentType && monthlyTrend && (
          <div className="mt-4 p-6 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950 border border-blue-300 dark:border-blue-700 rounded">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100">
                Content Intelligence &gt; {selectedContentType}
              </h3>
              <button
                onClick={() => setSelectedContentType(null)}
                className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 font-semibold"
              >
                Close
              </button>
            </div>

            {/* Section A: Performance Stats */}
            <div className="mb-6 p-4 bg-white dark:bg-gray-800 rounded border border-blue-200 dark:border-blue-800">
              <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Performance Stats</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Avg Engagement Per Post:</span>
                  <div className="text-xl font-bold text-gray-900 dark:text-white">
                    {formatEngagement(contentChartData.find(c => c.name === selectedContentType)?.avg_engagement || 0)}
                  </div>
                </div>
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Year Average:</span>
                  <div className="text-xl font-bold text-gray-900 dark:text-white">
                    {monthlyTrend ? formatEngagement(
                      monthlyTrend.months.reduce((sum, _, idx) => {
                        const fieldName = selectedContentType.toLowerCase().replace(/ /g, '_') + '_avg_engagement';
                        return sum + (monthlyTrend.months[idx] ? 0 : 0);
                      }, 0) / monthlyTrend.months.length
                    ) : 'N/A'}
                  </div>
                </div>
              </div>
            </div>

            {/* Section B: Commercial Correlations */}
            {contentIntelligence && contentIntelligence.signals.filter(s =>
              s.content_type.replace(/_/g, ' ').toLowerCase() === selectedContentType.toLowerCase()
            ).length > 0 && (
              <div className="mb-6 p-4 bg-white dark:bg-gray-800 rounded border border-blue-200 dark:border-blue-800">
                <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Commercial Correlations</h4>
                {contentIntelligence.signals
                  .filter(s => s.content_type.replace(/_/g, ' ').toLowerCase() === selectedContentType.toLowerCase())
                  .slice(0, 3)
                  .map((signal, idx) => (
                    <div key={idx} className="mb-3 p-3 bg-gray-50 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-gray-900 dark:text-gray-100">
                          {signal.commercial_metric} ({signal.commercial_asset})
                        </span>
                        <span className={`text-xs font-semibold px-2 py-1 rounded ${
                          signal.strength_label === "Strong"
                            ? "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200"
                            : "bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200"
                        }`}>
                          {signal.strength_label} · {signal.lag_months}mo lag
                        </span>
                      </div>
                      <p className="text-xs text-gray-700 dark:text-gray-300">{signal.interpretation}</p>
                    </div>
                  ))}
              </div>
            )}

            {/* Section C: Monthly Trend */}
            <div className="p-4 bg-white dark:bg-gray-800 rounded border border-blue-200 dark:border-blue-800">
              <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Monthly Trend — {selectedContentType}
              </h4>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
                12-month engagement trend for this content type across 2025
              </p>
              <div className="h-40 flex items-center justify-center text-gray-500 dark:text-gray-400 text-sm">
                Monthly trend visualization for {selectedContentType} — chart implementation pending
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Section 7: International Audience Intelligence (V1.6.6) */}
      {internationalData && (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border-[0.5px] border-gray-300 dark:border-gray-600 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            International Audience Intelligence
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
            Real Madrid's global fanbase by language market. International engagement is a leading indicator for global commercial reach.
          </p>

          {/* Sub-section A: International Engagement Ratio Hero Stat */}
          <div className="mb-6 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950 p-6 rounded-lg border border-blue-300 dark:border-blue-700">
            <div className="text-center">
              <div className="text-6xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                {formatPercentage(internationalData.international_engagement_ratio)}
              </div>
              <p className="text-lg text-gray-700 dark:text-gray-300 mb-1">
                of Real Madrid's social engagement comes from international accounts
              </p>
              {summary.international_engagement_ratio_mom_change !== null && (
                <div
                  className={`text-sm font-semibold ${
                    summary.international_engagement_ratio_mom_change > 0
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {summary.international_engagement_ratio_mom_change > 0 ? "↑" : "↓"}{" "}
                  {Math.abs(summary.international_engagement_ratio_mom_change).toFixed(1)}% vs prior month
                </div>
              )}
            </div>
          </div>

          {/* Sub-section B: Market Breakdown Chart */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              Engagement by Language Market — {new Date(internationalData.month).toLocaleDateString("en-US", { month: "short", year: "numeric" })}
            </h3>
            {!internationalData.language_markets || internationalData.language_markets.length === 0 ? (
              <div className="flex items-center justify-center h-60 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded">
                <p className="text-gray-600 dark:text-gray-400">No language breakdown data available for this month.</p>
              </div>
            ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart
                data={internationalData.language_markets.map((m) => ({
                  name: m.language,
                  engagement: m.monthly_engagement,
                  pct: m.pct_of_total_engagement,
                }))}
                layout="horizontal"
              >
                <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                <XAxis type="number" stroke={chartColors.axis} tick={{ fill: chartColors.text }} tickFormatter={(val) => formatEngagement(val)} />
                <YAxis type="category" dataKey="name" stroke={chartColors.axis} tick={{ fill: chartColors.text }} width={80} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: chartColors.tooltipBg,
                    border: `1px solid ${chartColors.tooltipBorder}`,
                    borderRadius: "8px",
                    color: chartColors.tooltipText
                  }}
                  formatter={(value: number, name: string) => {
                    if (name === "engagement") {
                      const marketData = internationalData.language_markets.find(
                        (m) => m.monthly_engagement === value
                      );
                      const pct = marketData?.pct_of_total_engagement || 0;
                      return [`${formatEngagement(value)} (${pct.toFixed(1)}%)`, "Engagement"];
                    }
                    return [value, name];
                  }}
                />
                <Legend wrapperStyle={{ color: chartColors.text }} />
                <Bar
                  dataKey="engagement"
                  fill={(entry: any) => (entry.name === "Spanish" ? "#3B82F6" : "#10B981")}
                  name="Monthly Engagement"
                />
              </BarChart>
            </ResponsiveContainer>
            )}
          </div>

          {/* Sub-section C: Market Growth Ranking */}
          {marketGrowth && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Market Growth Ranking
                </h3>
                <div className="flex gap-2 items-center">
                  <span className="text-xs text-gray-600 dark:text-gray-400">Compare Mode:</span>
                  <select
                    value={marketCompareMode}
                    onChange={(e) => setMarketCompareMode(e.target.value as "mom" | "yoy" | "custom")}
                    className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  >
                    <option value="mom">Month over Month</option>
                    <option value="yoy">Year over Year</option>
                    <option value="custom">vs Selected Month</option>
                  </select>
                  {marketCompareMode === "custom" && availableMonths.length > 0 && (
                    <select
                      value={marketCompareMonth || ""}
                      onChange={(e) => setMarketCompareMonth(e.target.value)}
                      className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    >
                      <option value="">Select month...</option>
                      {availableMonths.map((m) => (
                        <option key={m.value} value={m.value}>
                          {m.label} 2025
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full border border-gray-300 dark:border-gray-600 text-sm">
                  <thead className="bg-gray-100 dark:bg-gray-700">
                    <tr>
                      <th className="text-left p-3 border-r border-gray-300 dark:border-gray-600">Market</th>
                      <th className="text-right p-3 border-r border-gray-300 dark:border-gray-600">This Month</th>
                      <th className="text-right p-3 border-r border-gray-300 dark:border-gray-600">Prior Month</th>
                      <th className="text-right p-3">Change</th>
                    </tr>
                  </thead>
                  <tbody>
                    {marketGrowth.rankings.map((ranking, idx) => (
                      <tr
                        key={idx}
                        className={idx % 2 === 0 ? "" : "bg-gray-50 dark:bg-gray-800"}
                      >
                        <td className="p-3 border-r border-gray-300 dark:border-gray-600 font-medium">
                          {ranking.market}
                        </td>
                        <td className="p-3 text-right border-r border-gray-300 dark:border-gray-600">
                          {formatEngagement(ranking.this_month)}
                        </td>
                        <td className="p-3 text-right border-r border-gray-300 dark:border-gray-600">
                          {formatEngagement(ranking.prior_month)}
                        </td>
                        <td
                          className={`p-3 text-right font-semibold ${
                            ranking.mom_change_pct > 0
                              ? "text-green-600 dark:text-green-400"
                              : ranking.mom_change_pct < 0
                              ? "text-red-600 dark:text-red-400"
                              : "text-gray-600 dark:text-gray-400"
                          }`}
                        >
                          {ranking.mom_change_pct > 0 ? "↑" : ranking.mom_change_pct < 0 ? "↓" : "—"}{" "}
                          {ranking.mom_change_pct !== 0 ? `${Math.abs(ranking.mom_change_pct).toFixed(1)}%` : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Sub-section D: Commercial Correlation Card */}
          {internationalCorrelation && internationalCorrelation.strongest_correlation && (
            <div className="p-6 bg-green-50 dark:bg-green-950 border border-green-300 dark:border-green-700 rounded">
              <h3 className="text-lg font-semibold text-green-900 dark:text-green-100 mb-2">
                International Audience → Commercial Impact
              </h3>
              <p className="text-base text-green-800 dark:text-green-200 mb-2">
                {internationalCorrelation.strongest_correlation.interpretation}
              </p>
              <div className="flex items-center gap-4 text-sm">
                <span className="text-green-700 dark:text-green-300">
                  Correlation strength: <strong>{(internationalCorrelation.strongest_correlation.correlation * 100).toFixed(0)}%</strong>
                </span>
                <span className="text-green-700 dark:text-green-300">
                  Lag: <strong>{internationalCorrelation.strongest_correlation.lag_months} month(s)</strong>
                </span>
                <span className="text-green-700 dark:text-green-300">
                  Metric: <strong>{internationalCorrelation.strongest_correlation.commercial_metric}</strong>
                </span>
              </div>
            </div>
          )}

          {internationalCorrelation && !internationalCorrelation.strongest_correlation && (
            <div className="p-6 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Commercial Correlation Analysis
              </h3>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                12 months of data may be insufficient for robust correlation detection. As more data accumulates,
                correlations between international engagement and commercial metrics (streaming subscriptions,
                ecommerce traffic) may emerge.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Section 8: ScreenGuide */}
      <div className="bg-gray-50 dark:bg-gray-900 p-6 rounded-lg border border-gray-300 dark:border-gray-600">
        <button
          onClick={() => setGuideExpanded(!guideExpanded)}
          className="w-full flex items-center justify-between text-left"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {guideExpanded ? "▼" : "▶"} Screen Guide
          </h3>
        </button>
        {guideExpanded && (
          <div className="mt-4 space-y-2 text-sm text-gray-700 dark:text-gray-300">
            <p>
              <strong>What social media metrics mean:</strong> Social engagement (likes, comments, shares, saves)
              measures fan interaction intensity. Higher engagement = stronger emotional connection to content.
            </p>
            <p>
              <strong>Why engagement rate matters more than raw engagement:</strong> Engagement rate (engagement
              divided by follower count) normalizes for audience size. A 1.9% Instagram rate means 1.9% of followers
              engage with each post — this is exceptional for an account with 180M followers.
            </p>
            <p>
              <strong>International engagement ratio:</strong> Percentage of engagement from non-Spanish accounts.
              High ratio (89%+) indicates global brand strength and commercial reach beyond domestic market.
            </p>
            <p>
              <strong>Platform performance:</strong> TikTok often shows highest avg engagement per post due to
              algorithm favoring viral content. Instagram leads in total volume due to largest follower base.
            </p>
            <p>
              <strong>Content intelligence:</strong> Birthday posts and goal celebrations typically drive highest
              engagement. Training content shows steady baseline engagement. Use this to optimize content calendar.
            </p>
            <p>
              <strong>Content → Commercial correlations:</strong> V1.6.4 introduces correlation analysis between
              content types and commercial outcomes (sales, subscriptions, web traffic). Lower threshold (45% vs 60%)
              because content influences commercial metrics through longer causal chains. Use these insights to align
              content strategy with revenue goals.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
