import { useEffect, useState, useMemo } from "react";
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
} from "../../types/clubos";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { ScreenGuide } from "../../components/ui/ScreenGuide";

// ─── Tab definitions ─────────────────────────────────────────────────────────
//
// Four tabs, each answering a distinct business question:
//
//  OVERVIEW     → "What's our headline number this month?"
//                 KPI stat cards + month selector + top-level summary
//
//  PERFORMANCE  → "How did each platform trend over time?"
//                 12-month multi-platform trend chart + platform breakdown
//
//  STRATEGY     → "When, what, and how should we post?"
//                 Timing (day-of-week heatmap, match moments, format table)
//                 + Content type performance + Content intelligence correlations
//                 + Hashtag leaderboard and recommendations
//                 All grouped because they share a single answer: "how to optimise
//                 content production decisions."
//
//  INTELLIGENCE → "What does this tell us commercially?"
//                 Dynamic insights + Ranked recommendations for the content team
//                 + International audience intelligence + Commercial correlations
//                 These are all about "so what does this mean for the business?"

type SocialTab = "overview" | "performance" | "strategy" | "intelligence";

const SOCIAL_TABS: { id: SocialTab; label: string; subtitle: string }[] = [
  { id: "overview",     label: "Overview",     subtitle: "What's our headline number?" },
  { id: "performance",  label: "Performance",  subtitle: "How did each platform trend?" },
  { id: "strategy",     label: "Strategy",     subtitle: "When, what & how to post?" },
  { id: "intelligence", label: "Intelligence", subtitle: "What does this mean commercially?" },
];

// ─── Platform brand colors (for chart Cell overrides) ─────────────────────

const PLATFORM_COLORS: Record<string, string> = {
  instagram: "#E1306C",
  tiktok:    "#69C9D0",
  x:         "#1DA1F2",
  facebook:  "#4267B2",
  youtube:   "#FF0000",
};

// ─── Content type colors (design-system aligned) ──────────────────────────

const CONTENT_TYPE_COLORS: Record<string, string> = {
  score_graphic:    "#2563EB",  // info-600
  goal_celebration: "#16A34A",  // good-600
  lineup_graphic:   "#EA580C",  // warning-600
  player_arrival:   "#DC2626",  // critical-600
  game_preview:     "#9333EA",  // accent-600
  training:         "#0D9488",  // teal
  birthday:         "#CA8A04",  // sport-gold-600
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatEngagement(val: number): string {
  if (val >= 1e9) return `${(val / 1e9).toFixed(1)}B`;
  if (val >= 1e6) return `${(val / 1e6).toFixed(0)}M`;
  if (val >= 1e3) return `${(val / 1e3).toFixed(0)}K`;
  return val.toString();
}

function formatPercentage(num: number): string {
  return `${(num * 100).toFixed(1)}%`;
}

function formatMoMChange(change: number | null): string | null {
  if (change === null) return null;
  const sign = change > 0 ? "+" : "";
  return `${sign}${change.toFixed(1)}%`;
}

function getContentTypeColor(contentType: string): string {
  const key = contentType.toLowerCase().replace(/ /g, "_");
  return CONTENT_TYPE_COLORS[key] || "#2563EB";
}

// ─── Sub-components ──────────────────────────────────────────────────────────

interface StatCardProps {
  cardId: string;
  title: string;
  value: string;
  change: string | null;
  contextLine?: string;
  onNavigate?: () => void;
}

function StatCard({ cardId, title, value, change, contextLine, onNavigate }: StatCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const isPositive = change !== null && (change.startsWith("+") || parseFloat(change) > 0);

  return (
    <div>
      <div
        className="bg-paper dark:bg-stone-800 p-6 border-2 border-ink dark:border-stone-700 cursor-pointer hover:shadow-sport transition-all duration-200"
        onClick={() => setIsExpanded((e) => !e)}
        id={`stat-card-${cardId}`}
      >
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400">
            {title}
          </h3>
          <span className="font-mono text-xs text-stone-400 dark:text-stone-500">
            {isExpanded ? "▲" : "▼"}
          </span>
        </div>
        <div className="font-mono text-3xl font-semibold text-ink dark:text-stone-100 mb-1">
          {value}
        </div>
        {change && (
          <div
            className={`font-mono text-xs font-semibold ${
              isPositive
                ? "text-good-light dark:text-good-dark"
                : "text-critical-light dark:text-critical-dark"
            }`}
          >
            {isPositive ? "↑" : "↓"} {change} MoM
          </div>
        )}
        {contextLine && (
          <p className="font-body text-xs text-stone-500 dark:text-stone-400 mt-2 leading-relaxed">
            {contextLine}
          </p>
        )}
      </div>

      {isExpanded && (
        <div className="border-2 border-t-0 border-ink dark:border-stone-700 p-4 bg-stone-50 dark:bg-stone-900 animate-fade-in flex flex-col gap-3">
          <p className="font-body text-sm text-stone-700 dark:text-stone-300">
            {cardId === "total-engagement" &&
              "Platform breakdown: Instagram leads with highest engagement share."}
            {cardId === "avg-per-post" &&
              "Year average across all platforms. Individual platform performance varies."}
            {cardId === "instagram-share" &&
              "Instagram's contribution to total social engagement. Dominates Real Madrid's social reach."}
            {cardId === "international" &&
              "High international reach supports global eCommerce and streaming growth."}
          </p>
          {onNavigate && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onNavigate();
              }}
              className="self-start font-mono text-xs uppercase tracking-wider text-stone-500 dark:text-stone-400 hover:text-ink dark:hover:text-stone-200 hover:underline flex items-center gap-1 transition-all"
            >
              Go deeper &rarr;
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function SocialIntelligencePage() {
  // ── Data state ──────────────────────────────────────────────────────────
  const [summary, setSummary] = useState<SocialSummary | null>(null);
  const [monthlyTrend, setMonthlyTrend] = useState<SocialMonthlyTrend | null>(null);
  const [platformData, setPlatformData] = useState<SocialPlatformData[]>([]);
  const [contentData, setContentData] = useState<SocialContentData[]>([]);
  const [contentIntelligence, setContentIntelligence] = useState<ContentIntelligenceResponse | null>(null);
  const [selectedSignal, setSelectedSignal] = useState<ContentSignal | null>(null);
  const [internationalData, setInternationalData] = useState<InternationalBreakdownResponse | null>(null);
  const [marketGrowth, setMarketGrowth] = useState<MarketGrowthRankingResponse | null>(null);
  const [internationalCorrelation, setInternationalCorrelation] = useState<InternationalCommercialCorrelationResponse | null>(null);
  const [insights, setInsights] = useState<DynamicInsightsResponse | null>(null);
  const [recommendations, setRecommendations] = useState<ContentRecommendationsResponse | null>(null);
  const [dayOfWeekData, setDayOfWeekData] = useState<DayOfWeekAnalysisResponse | null>(null);
  const [matchMomentData, setMatchMomentData] = useState<MatchMomentAnalysisResponse | null>(null);
  const [formatData, setFormatData] = useState<FormatPerformanceResponse | null>(null);
  const [hashtagData, setHashtagData] = useState<HashtagPerformanceResponse | null>(null);

  // ── UI state ────────────────────────────────────────────────────────────
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<SocialTab>("overview");
  const [strategySubSection, setStrategySubSection] = useState<"timing" | "content" | "hashtags">("timing");
  const [intelligenceSubSection, setIntelligenceSubSection] = useState<"insights" | "international">("insights");
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(["all"]);
  const [expandedStatCard, setExpandedStatCard] = useState<string | null>(null);
  const [platformMetricView, setPlatformMetricView] = useState<"avg" | "total">("avg");
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);
  const [selectedContentType, setSelectedContentType] = useState<string | null>(null);
  const [marketCompareMode, setMarketCompareMode] = useState<"mom" | "yoy" | "custom">("mom");
  const [marketCompareMonth, setMarketCompareMonth] = useState<string | null>(null);
  const [insightFilter, setInsightFilter] = useState<string>("all");
  const [hashtagFilter, setHashtagFilter] = useState<string>("all");
  const [expandedInsight, setExpandedInsight] = useState<string | null>(null);

  // ── Reactive dark mode for charts ──────────────────────────────────────
  const [isDark, setIsDark] = useState(() =>
    typeof window !== "undefined"
      ? document.documentElement.classList.contains("dark")
      : false
  );

  useEffect(() => {
    const observer = new MutationObserver(() => {
      setIsDark(document.documentElement.classList.contains("dark"));
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  const chartColors = useMemo(
    () => ({
      axis:         isDark ? "#A3A39E" : "#5C5C56",     // stone-400 / stone-600
      grid:         isDark ? "#434340" : "#E8E8E5",     // stone-700 / stone-200
      text:         isDark ? "#D1D1CC" : "#1A1A1A",     // stone-300 / ink
      tooltipBg:    isDark ? "#2B2B28" : "#FAFAF8",     // stone-800 / paper
      tooltipBorder:isDark ? "#434340" : "#1A1A1A",     // stone-700 / ink
      tooltipText:  isDark ? "#F5F5F3" : "#1A1A1A",     // stone-100 / ink
    }),
    [isDark]
  );

  const tooltipStyle = useMemo(
    () => ({
      backgroundColor: chartColors.tooltipBg,
      border: `2px solid ${chartColors.tooltipBorder}`,
      borderRadius: 0,
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: "11px",
      color: chartColors.tooltipText,
    }),
    [chartColors]
  );

  // ── Data loading ────────────────────────────────────────────────────────
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

        if (intelligenceData.signals.length > 0) {
          setSelectedSignal(intelligenceData.signals[0]);
        }

        if (summaryData.latest_month) {
          const monthStr = summaryData.latest_month.substring(0, 7);
          setSelectedMonth(monthStr);
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

  useEffect(() => {
    if (!selectedMonth) return;
    async function loadMonthData() {
      try {
        const [platforms, content, summaryData] = await Promise.all([
          fetchSocialPlatforms(selectedMonth!),
          fetchSocialContent(selectedMonth!),
          fetchSocialSummary(selectedMonth!),
        ]);
        setPlatformData(platforms.platforms);
        setContentData(content.content_types);
        setSummary(summaryData);
      } catch (error) {
        console.error("Failed to load month data:", error);
      }
    }
    loadMonthData();
  }, [selectedMonth]);

  useEffect(() => {
    if (!summary) return;
    async function loadMarketGrowth() {
      try {
        let compareMonth: string | undefined;
        if (marketCompareMode === "yoy") {
          const latestMonth = summary!.latest_month.substring(0, 7);
          const year = parseInt(latestMonth.split("-")[0]);
          const month = latestMonth.split("-")[1];
          compareMonth = `${year - 1}-${month}`;
        } else if (marketCompareMode === "custom" && marketCompareMonth) {
          compareMonth = marketCompareMonth;
        }
        const growthData = await fetchMarketGrowthRanking(compareMonth);
        setMarketGrowth(growthData);
      } catch (error) {
        console.error("Failed to load market growth:", error);
      }
    }
    loadMarketGrowth();
  }, [marketCompareMode, marketCompareMonth, summary]);

  // ── Chart data ───────────────────────────────────────────────────────────
  const trendChartData = useMemo(
    () =>
      monthlyTrend
        ? monthlyTrend.months.map((month, idx) => ({
            month: new Date(month).toLocaleDateString("en-US", { month: "short", year: "numeric" }),
            monthShort: new Date(month).toLocaleDateString("en-US", { month: "short" }),
            total_engagement:    monthlyTrend.total_engagement[idx],
            instagram:           monthlyTrend.instagram_engagement[idx],
            tiktok:              monthlyTrend.tiktok_engagement[idx],
            x:                   monthlyTrend.x_engagement[idx],
            facebook:            monthlyTrend.facebook_engagement[idx],
            youtube:             monthlyTrend.youtube_engagement[idx],
            posts:               monthlyTrend.total_posts[idx],
          }))
        : [],
    [monthlyTrend]
  );

  const platformChartData = useMemo(
    () =>
      [...platformData]
        .map((p) => ({
          name:             p.platform.charAt(0).toUpperCase() + p.platform.slice(1),
          platformKey:      p.platform.toLowerCase(),
          avg_engagement:   p.avg_engagement,
          total_engagement: p.engagement,
          posts:            p.posts,
        }))
        .sort((a, b) => {
          const aVal = platformMetricView === "avg" ? a.avg_engagement : a.total_engagement;
          const bVal = platformMetricView === "avg" ? b.avg_engagement : b.total_engagement;
          return bVal - aVal;
        }),
    [platformData, platformMetricView]
  );

  const contentChartData = useMemo(
    () => contentData.map((c) => ({ name: c.content_type, avg_engagement: c.avg_engagement })),
    [contentData]
  );

  const availableMonths = useMemo(
    () =>
      monthlyTrend
        ? monthlyTrend.months.map((m, idx) => ({
            label:    new Date(m).toLocaleDateString("en-US", { month: "short" }),
            value:    m.substring(0, 7),
            isLatest: idx === monthlyTrend.months.length - 1,
          }))
        : [],
    [monthlyTrend]
  );

  // ── Platform filter handlers ──────────────────────────────────────────────
  const handlePlatformFilterClick = (platform: string, event: React.MouseEvent) => {
    if (platform === "all") { setSelectedPlatforms(["all"]); return; }
    if (event.shiftKey) {
      setSelectedPlatforms((prev) => {
        const filtered = prev.filter((p) => p !== "all");
        if (filtered.includes(platform)) {
          const updated = filtered.filter((p) => p !== platform);
          return updated.length === 0 ? ["all"] : updated;
        }
        return [...filtered, platform];
      });
    } else {
      setSelectedPlatforms([platform]);
    }
  };

  const getPlatformOpacity = (platform: string) => {
    if (selectedPlatforms.includes("all")) return 1;
    return selectedPlatforms.includes(platform) ? 1 : 0.15;
  };

  // ── Shared styles ─────────────────────────────────────────────────────────
  const sectionCard = "bg-paper dark:bg-stone-800 border-2 border-ink dark:border-stone-700 p-6 mb-8";
  const sectionTitle = "font-headline text-2xl text-ink dark:text-stone-100 mb-2";
  const sectionSubtitle = "font-body text-sm text-stone-600 dark:text-stone-400 mb-6";
  const subSectionTitle = "font-body text-lg font-semibold text-ink dark:text-stone-100 mb-4";
  const pillBase = "font-mono text-xs uppercase tracking-wider border-2 transition-colors px-3 py-1";
  const pillActive = "border-ink bg-ink text-paper dark:border-stone-300 dark:bg-stone-300 dark:text-stone-900";
  const pillInactive = "border-stone-300 dark:border-stone-600 text-stone-600 dark:text-stone-400 hover:border-stone-500 dark:hover:border-stone-400";
  const tableHeader = "border border-stone-300 dark:border-stone-700 p-3 text-left font-mono text-xs uppercase tracking-wider text-stone-500 dark:text-stone-400 bg-stone-100 dark:bg-stone-900";
  const tableCell = "border border-stone-300 dark:border-stone-700 p-3 font-body text-sm text-ink dark:text-stone-200";
  const tableCellMono = "border border-stone-300 dark:border-stone-700 p-3 font-mono text-sm text-ink dark:text-stone-200";

  // ── Loading / error ───────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="font-mono text-sm uppercase tracking-widest text-stone-500 dark:text-stone-400">
          Loading social intelligence…
        </div>
      </div>
    );
  }

  if (!summary || !monthlyTrend) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="font-mono text-sm text-critical-600 dark:text-critical-dark">
          Failed to load social data
        </div>
      </div>
    );
  }

  // ── Tab content renderers ─────────────────────────────────────────────────

  // ── OVERVIEW ─────────────────────────────────────────────────────────────
  const renderOverview = () => {
    const activePlatform = selectedPlatforms[0] || "all";
    const isAll = activePlatform === "all";

    // Find the selected platform data for the month
    const p = platformData.find((d) => d.platform.toLowerCase() === activePlatform.toLowerCase());

    const totalEngagement = isAll ? summary.total_engagement : (p ? p.engagement : 0);
    const avgEngagement = isAll ? summary.avg_engagement_per_post : (p ? p.avg_engagement : 0);

    // Platform share of total engagement
    const platformShare = isAll
      ? summary.instagram_engagement_rate
      : (summary.total_engagement > 0 && p ? (p.engagement / summary.total_engagement) : 0);

    // Compute platform-specific MoM Change
    let engagementChange = isAll ? summary.total_engagement_mom_change : null;
    let avgChange = isAll ? summary.avg_engagement_per_post_mom_change : null;
    let shareChange = isAll ? summary.instagram_engagement_rate_mom_change : null;

    if (!isAll && selectedMonth && monthlyTrend) {
      const monthIdx = monthlyTrend.months.findIndex((m) => m.startsWith(selectedMonth));
      if (monthIdx > 0) {
        let currentEngagementFromTrend = 0;
        let priorEngagement = 0;

        const platformKey = activePlatform.toLowerCase();
        if (platformKey === "instagram") {
          currentEngagementFromTrend = monthlyTrend.instagram_engagement[monthIdx];
          priorEngagement = monthlyTrend.instagram_engagement[monthIdx - 1];
        } else if (platformKey === "tiktok") {
          currentEngagementFromTrend = monthlyTrend.tiktok_engagement[monthIdx];
          priorEngagement = monthlyTrend.tiktok_engagement[monthIdx - 1];
        } else if (platformKey === "x") {
          currentEngagementFromTrend = monthlyTrend.x_engagement[monthIdx];
          priorEngagement = monthlyTrend.x_engagement[monthIdx - 1];
        } else if (platformKey === "facebook") {
          currentEngagementFromTrend = monthlyTrend.facebook_engagement[monthIdx];
          priorEngagement = monthlyTrend.facebook_engagement[monthIdx - 1];
        } else if (platformKey === "youtube") {
          currentEngagementFromTrend = monthlyTrend.youtube_engagement[monthIdx];
          priorEngagement = monthlyTrend.youtube_engagement[monthIdx - 1];
        }

        if (priorEngagement > 0) {
          engagementChange = ((currentEngagementFromTrend - priorEngagement) / priorEngagement) * 100;
        }
      }
    }

    const platformLabel = isAll ? "All Platforms" : activePlatform.charAt(0).toUpperCase() + activePlatform.slice(1);

    return (
      <div>
        {/* Filters Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Month selector */}
          {availableMonths.length > 0 && (
            <div className="border-2 border-ink dark:border-stone-700 p-4 bg-stone-50 dark:bg-stone-900">
              <div className="flex items-center gap-2 mb-3">
                <span className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400">
                  Select Month — Filter Metrics &amp; Details
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {availableMonths.map((month) => (
                  <button
                    key={month.value}
                    id={`month-${month.value}`}
                    onClick={() => setSelectedMonth(month.value)}
                    className={`${pillBase} ${selectedMonth === month.value ? pillActive : pillInactive}`}
                  >
                    {month.label}
                    {month.isLatest && (
                      <span className="ml-1 font-mono text-[9px] text-stone-400 dark:text-stone-500">LATEST</span>
                    )}
                  </button>
                ))}
              </div>
              {selectedMonth && (
                <p className="font-mono text-xs text-stone-400 dark:text-stone-500 mt-2">
                  Selected:{" "}
                  {new Date(selectedMonth + "-01").toLocaleDateString("en-US", {
                    month: "long",
                    year: "numeric",
                  })}
                </p>
              )}
            </div>
          )}

          {/* Platform selector */}
          <div className="border-2 border-ink dark:border-stone-700 p-4 bg-stone-50 dark:bg-stone-900">
            <div className="flex items-center gap-2 mb-3">
              <span className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400">
                Select Platform — Filter Overview Metrics
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {[
                { key: "all",       label: "All Platforms",  color: null },
                { key: "instagram", label: "Instagram",      color: "#E1306C" },
                { key: "tiktok",    label: "TikTok",         color: "#69C9D0" },
                { key: "x",         label: "X",              color: "#1DA1F2" },
                { key: "facebook",  label: "Facebook",       color: "#4267B2" },
                { key: "youtube",   label: "YouTube",        color: "#FF0000" },
              ].map(({ key, label, color }) => {
                const isActive = selectedPlatforms.includes(key);
                const hasBrandColor = isActive && color !== null;
                return (
                  <button
                    key={key}
                    id={`overview-platform-${key}`}
                    onClick={() => {
                      if (key === "all") {
                        setSelectedPlatforms(["all"]);
                      } else {
                        setSelectedPlatforms([key]);
                      }
                    }}
                    className={`${pillBase} transition-all ${
                      hasBrandColor ? "" : isActive ? pillActive : pillInactive
                    }`}
                    style={hasBrandColor ? { backgroundColor: color!, borderColor: color!, color: "#fff" } : undefined}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
            <p className="font-mono text-xs text-stone-400 dark:text-stone-500 mt-2">
              Selected: {isAll ? "All Platforms" : platformLabel}
            </p>
          </div>
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            cardId="total-engagement"
            title={isAll ? "Total Engagement" : `${platformLabel} Engagement`}
            value={formatEngagement(totalEngagement)}
            change={formatMoMChange(engagementChange)}
            contextLine={isAll ? `Across all platforms. Peak: ${formatEngagement(Math.max(...monthlyTrend.total_engagement))}` : `Total engagement for ${platformLabel} in selected month.`}
            onNavigate={() => setActiveTab("performance")}
          />
          <StatCard
            cardId="avg-per-post"
            title={isAll ? "Avg Engagement Per Post" : `${platformLabel} Avg Engagement`}
            value={formatEngagement(avgEngagement)}
            change={formatMoMChange(avgChange)}
            contextLine={isAll ? `Year average: ${formatEngagement(monthlyTrend.avg_engagement_per_post.reduce((a, b) => a + b, 0) / monthlyTrend.avg_engagement_per_post.length)}` : `Average engagement per post on ${platformLabel}.`}
            onNavigate={() => setActiveTab("performance")}
          />
          <StatCard
            cardId="instagram-share"
            title={isAll ? "Instagram Share of Engagement" : `${platformLabel} Share of Engagement`}
            value={formatPercentage(platformShare)}
            change={formatMoMChange(shareChange)}
            contextLine={isAll ? "Instagram's contribution to total social engagement." : `${platformLabel}'s contribution to total social engagement.`}
            onNavigate={() => setActiveTab("performance")}
          />
          <StatCard
            cardId="international"
            title="International Engagement"
            value={formatPercentage(summary.international_engagement_ratio)}
            change={formatMoMChange(summary.international_engagement_ratio_mom_change)}
            contextLine={`${(summary.international_engagement_ratio * 100).toFixed(1)}% of Real Madrid's audience is international.`}
            onNavigate={() => {
              setActiveTab("intelligence");
              setIntelligenceSubSection("international");
            }}
          />
        </div>

        {/* Quick summary metrics */}
        <div className={sectionCard}>
          <h2 className={sectionTitle}>Performance Summary</h2>
          <p className={sectionSubtitle}>
            55,598 posts analyzed · 4.08B total engagement in 2025
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Top Platform", value: summary.top_performing_platform },
              { label: "Top Content Type", value: summary.top_performing_content_type?.replace(/_/g, " ") },
              { label: "Latest Month", value: summary.latest_month?.substring(0, 7) },
              { label: "Platforms Tracked", value: "5" },
            ].map((stat) => (
              <div key={stat.label} className="border border-stone-200 dark:border-stone-700 p-4 bg-stone-50 dark:bg-stone-900">
                <div className="font-mono text-xs uppercase tracking-widest text-stone-400 dark:text-stone-500 mb-1">
                  {stat.label}
                </div>
                <div className="font-mono text-base font-semibold text-ink dark:text-stone-100 uppercase">
                  {stat.value || "—"}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  // ── INSIGHTS ──────────────────────────────────────────────────────────────
  const renderInsights = () => (
    <div>
      {insights && insights.insights.length > 0 && (
        <div className="mb-12">
          <div className="mb-6">
            <h2 className={sectionTitle}>INSIGHTS — What the data is telling you</h2>
            <p className={sectionSubtitle}>
              Auto-generated from {insights.total_count} insights across 55,598 posts.
            </p>
          </div>

          <div className="flex flex-wrap gap-2 mb-6">
            {["all", "timing", "format", "content", "hashtag", "peer"].map((filter) => (
              <button
                key={filter}
                id={`insight-filter-${filter}`}
                onClick={() => setInsightFilter(filter)}
                className={`${pillBase} ${insightFilter === filter ? pillActive : pillInactive}`}
              >
                {filter === "all" ? "All Insights" : filter}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {insights.insights
              .filter((i) => insightFilter === "all" || i.category === insightFilter)
              .map((insight) => (
                <div
                  key={insight.insight_id}
                  className="border-2 border-ink dark:border-stone-700 p-6 bg-paper dark:bg-stone-800"
                >
                  <div className="flex items-center justify-between mb-4">
                    <span
                      className={`font-mono text-xs uppercase tracking-wider px-3 py-1 border ${
                        insight.priority === "critical"
                          ? "border-critical-600 bg-critical-50 dark:bg-stone-900 text-critical-700 dark:text-critical-dark"
                          : insight.priority === "high"
                          ? "border-warning-600 bg-warning-50 dark:bg-stone-900 text-warning-700 dark:text-warning-dark"
                          : "border-info-600 bg-info-50 dark:bg-stone-900 text-info-700 dark:text-info-dark"
                      }`}
                    >
                      {insight.priority}
                    </span>
                    <span className="font-mono text-xs uppercase tracking-widest text-stone-400 dark:text-stone-500">
                      {insight.category}
                    </span>
                  </div>

                  <h3 className="font-headline text-xl text-ink dark:text-stone-100 mb-3">
                    {insight.headline}
                  </h3>

                  <p className="font-body text-sm text-stone-700 dark:text-stone-300 mb-4 leading-relaxed">
                    {insight.finding}
                  </p>

                  <div className="p-3 border border-stone-200 dark:border-stone-700 bg-stone-50 dark:bg-stone-900 font-mono text-xs text-stone-700 dark:text-stone-300 mb-4">
                    <strong className="text-stone-900 dark:text-stone-100">Evidence:</strong>{" "}
                    {insight.evidence}
                  </div>

                  <div className="p-4 border-l-4 border-warning-600 dark:border-warning-dark bg-warning-50 dark:bg-stone-900 mb-3">
                    <div className="font-mono text-xs uppercase tracking-wider text-warning-700 dark:text-warning-dark mb-1">
                      Recommendation
                    </div>
                    <div className="font-body text-sm text-stone-700 dark:text-stone-300">
                      {insight.recommendation}
                    </div>
                  </div>

                  <p className="font-mono text-xs text-stone-500 dark:text-stone-500">
                    <strong>Impact:</strong> {insight.impact_estimate}
                  </p>

                  <button
                    onClick={() =>
                      setExpandedInsight(
                        expandedInsight === insight.insight_id ? null : insight.insight_id
                      )
                    }
                    className="mt-3 font-mono text-xs uppercase tracking-wider text-info-600 dark:text-info-dark hover:underline"
                  >
                    {expandedInsight === insight.insight_id
                      ? "Hide details ▲"
                      : "View analysis →"}
                  </button>
                </div>
              ))}
          </div>
        </div>
      )}

      {recommendations && recommendations.recommendations.length > 0 && (
        <div>
          <h2 className={sectionTitle}>RECOMMENDATIONS — For the content team</h2>
          <p className={sectionSubtitle}>
            Priority-ranked actions based on 2025 performance data.
          </p>
          <div className="space-y-4">
            {recommendations.recommendations.map((rec) => (
              <div
                key={rec.rank}
                className="border-2 border-ink dark:border-stone-700 p-6 bg-paper dark:bg-stone-800"
              >
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-10 h-10 bg-gradient-sport flex items-center justify-center font-mono text-lg font-semibold text-white">
                    {rec.rank}
                  </div>
                  <div className="flex-1">
                    <div className="flex flex-wrap gap-2 mb-3">
                      <span
                        className={`font-mono text-xs uppercase tracking-wider px-3 py-1 border ${
                          rec.action === "CONVERT"
                            ? "border-accent-600 bg-accent-50 dark:bg-stone-900 text-accent-700 dark:text-accent-dark"
                            : rec.action === "SCHEDULE"
                            ? "border-info-600 bg-info-50 dark:bg-stone-900 text-info-700 dark:text-info-dark"
                            : rec.action === "INCREASE"
                            ? "border-good-600 bg-good-50 dark:bg-stone-900 text-good-700 dark:text-good-dark"
                            : "border-critical-600 bg-critical-50 dark:bg-stone-900 text-critical-700 dark:text-critical-dark"
                        }`}
                      >
                        {rec.action}
                      </span>
                      <span
                        className={`font-mono text-xs uppercase tracking-wider px-3 py-1 border ${
                          rec.effort_estimate === "low"
                            ? "border-good-600 text-good-700 dark:text-good-dark"
                            : rec.effort_estimate === "medium"
                            ? "border-warning-600 text-warning-700 dark:text-warning-dark"
                            : "border-critical-600 text-critical-700 dark:text-critical-dark"
                        }`}
                      >
                        {rec.effort_estimate} effort
                      </span>
                    </div>
                    <h3 className="font-headline text-xl text-ink dark:text-stone-100 mb-2">
                      {rec.title}
                    </h3>
                    <p className="font-body text-sm text-stone-700 dark:text-stone-300 mb-3">
                      {rec.rationale}
                    </p>
                    <div className="p-3 border-l-4 border-info-600 dark:border-info-dark bg-info-50 dark:bg-stone-900">
                      <div className="font-body text-sm text-stone-700 dark:text-stone-300">
                        <strong className="text-ink dark:text-stone-100">Expected Impact:</strong>{" "}
                        {rec.expected_impact}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // ── TRENDS ────────────────────────────────────────────────────────────────
  const renderTrends = () => (
    <div className={sectionCard}>
      <h2 className={sectionTitle}>12-Month Engagement Trend</h2>
      <p className={sectionSubtitle}>
        Click any platform to isolate. Shift+click to compare multiple platforms.
      </p>

      <div className="flex flex-wrap gap-2 mb-6">
        {[
          { key: "all",       label: "All",       color: null },
          { key: "instagram", label: "Instagram", color: "#E1306C" },
          { key: "tiktok",    label: "TikTok",    color: "#69C9D0" },
          { key: "x",         label: "X",         color: "#1DA1F2" },
          { key: "facebook",  label: "Facebook",  color: "#4267B2" },
          { key: "youtube",   label: "YouTube",   color: "#FF0000" },
        ].map(({ key, label, color }) => {
          const isActive = selectedPlatforms.includes(key);
          const hasBrandColor = isActive && color !== null;
          return (
            <button
              key={key}
              id={`platform-filter-${key}`}
              onClick={(e) => handlePlatformFilterClick(key, e)}
              className={`${pillBase} transition-all ${
                hasBrandColor ? "" : isActive ? pillActive : pillInactive
              }`}
              style={hasBrandColor ? { backgroundColor: color!, borderColor: color!, color: "#fff" } : undefined}
            >
              {label}
            </button>
          );
        })}
      </div>

      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={trendChartData}>
          <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} horizontal={true} vertical={false} />
          <XAxis dataKey="monthShort" stroke={chartColors.axis} tick={{ fill: chartColors.text, fontSize: 11 }} />
          <YAxis stroke={chartColors.axis} tick={{ fill: chartColors.text, fontSize: 11 }} tickFormatter={formatEngagement} />
          <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => formatEngagement(v)} labelFormatter={(label) => trendChartData.find((d) => d.monthShort === label)?.month || label} />
          <Legend wrapperStyle={{ color: chartColors.text, fontFamily: "'JetBrains Mono', monospace", fontSize: "11px" }} />
          <Line type="monotone" dataKey="total_engagement" stroke="#A3A39E" strokeWidth={1.5} strokeDasharray="4 4" name="Total" dot={false} opacity={0.4} />
          <Line type="monotone" dataKey="instagram" stroke="#E1306C" strokeWidth={2} name="Instagram" dot={false} activeDot={{ r: 4 }} opacity={getPlatformOpacity("instagram")} />
          <Line type="monotone" dataKey="tiktok"    stroke="#69C9D0" strokeWidth={2} name="TikTok"    dot={false} activeDot={{ r: 4 }} opacity={getPlatformOpacity("tiktok")} />
          <Line type="monotone" dataKey="x"         stroke="#1DA1F2" strokeWidth={2} name="X"         dot={false} activeDot={{ r: 4 }} opacity={getPlatformOpacity("x")} />
          <Line type="monotone" dataKey="facebook"  stroke="#4267B2" strokeWidth={2} name="Facebook"  dot={false} activeDot={{ r: 4 }} opacity={getPlatformOpacity("facebook")} />
          <Line type="monotone" dataKey="youtube"   stroke="#FF0000" strokeWidth={2} name="YouTube"   dot={false} activeDot={{ r: 4 }} opacity={getPlatformOpacity("youtube")} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );

  // ── PLATFORMS ─────────────────────────────────────────────────────────────
  const renderPlatforms = () => (
    <div>
      <div className={sectionCard}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className={sectionTitle}>Platform Performance</h2>
            <p className="font-body text-sm text-stone-600 dark:text-stone-400">
              Selected month:{" "}
              {selectedMonth
                ? new Date(selectedMonth + "-01").toLocaleDateString("en-US", { month: "long", year: "numeric" })
                : "—"}
            </p>
          </div>
          <div className="flex gap-2">
            {(["avg", "total"] as const).map((view) => (
              <button
                key={view}
                id={`platform-metric-${view}`}
                onClick={() => setPlatformMetricView(view)}
                className={`${pillBase} ${platformMetricView === view ? pillActive : pillInactive}`}
              >
                {view === "avg" ? "Avg Per Post" : "Total"}
              </button>
            ))}
          </div>
        </div>

        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={platformChartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} horizontal={false} />
            <XAxis type="number" stroke={chartColors.axis} tick={{ fill: chartColors.text, fontSize: 11 }} tickFormatter={formatEngagement} />
            <YAxis type="category" dataKey="name" stroke={chartColors.axis} tick={{ fill: chartColors.text, fontSize: 11 }} width={75} />
            <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => formatEngagement(v)} />
            <Bar dataKey={platformMetricView === "avg" ? "avg_engagement" : "total_engagement"}
                 name={platformMetricView === "avg" ? "Avg Engagement/Post" : "Total Engagement"}>
              {platformChartData.map((entry) => (
                <Cell
                  key={entry.platformKey}
                  fill={PLATFORM_COLORS[entry.platformKey] || "#2563EB"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        <div className="mt-4 font-mono text-xs text-stone-500 dark:text-stone-400 uppercase tracking-widest">
          Top platform:{" "}
          <span className="text-ink dark:text-stone-100 font-semibold">
            {summary.top_performing_platform}
          </span>
        </div>
      </div>
    </div>
  );

  // ── TIMING ────────────────────────────────────────────────────────────────
  const renderTiming = () => (
    <div>
      {/* Day of Week Heatmap */}
      {dayOfWeekData && (
        <div className={sectionCard}>
          <h2 className={sectionTitle}>Day of Week Performance</h2>
          <p className={sectionSubtitle}>Average engagement per post by posting day.</p>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className={tableHeader}>Metric</th>
                  {dayOfWeekData.days.map((day) => (
                    <th key={day.day_of_week} className={tableHeader}>
                      {day.day_of_week.substring(0, 3)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className={tableCell + " font-semibold"}>Avg Eng/Post</td>
                  {dayOfWeekData.days.map((day) => {
                    const vals = dayOfWeekData.days.map((d) => d.avg_engagement_per_post);
                    const min = Math.min(...vals);
                    const max = Math.max(...vals);
                    const opacity = ((day.avg_engagement_per_post - min) / (max - min)) * 0.75 + 0.25;
                    const isHigh = opacity > 0.6;
                    return (
                      <td
                        key={day.day_of_week}
                        className="border border-stone-300 dark:border-stone-700 p-3 text-center font-mono text-xs"
                        style={{
                          backgroundColor: `rgba(22, 163, 74, ${opacity})`,   // good-600 RGB
                          color: isHigh ? "#fff" : (isDark ? "#D1D1CC" : "#1A1A1A"),
                        }}
                        title={`${day.day_of_week}: ${day.avg_engagement_per_post.toLocaleString()} avg (${day.vs_weekly_average_pct > 0 ? "+" : ""}${day.vs_weekly_average_pct}% vs weekly avg)`}
                      >
                        {(day.avg_engagement_per_post / 1000).toFixed(0)}K
                      </td>
                    );
                  })}
                </tr>
                <tr>
                  <td className={tableCell + " font-semibold"}>vs Weekly Avg</td>
                  {dayOfWeekData.days.map((day) => (
                    <td
                      key={day.day_of_week}
                      className={`${tableCellMono} text-center ${
                        day.vs_weekly_average_pct > 0
                          ? "text-good-light dark:text-good-dark"
                          : "text-critical-light dark:text-critical-dark"
                      }`}
                    >
                      {day.vs_weekly_average_pct > 0 ? "+" : ""}
                      {day.vs_weekly_average_pct}%
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
          <p className="font-mono text-xs text-stone-500 dark:text-stone-400 mt-3 uppercase tracking-widest">
            Best day:{" "}
            <span className="text-ink dark:text-stone-100 font-semibold">
              {dayOfWeekData.best_day}
            </span>{" "}
            — avg {dayOfWeekData.best_day_avg.toLocaleString()}
          </p>
        </div>
      )}

      {/* Match Moment */}
      {matchMomentData && (
        <div className={sectionCard}>
          <h2 className={sectionTitle}>Match Moment Performance</h2>
          <p className={sectionSubtitle}>Engagement per post across different match contexts.</p>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={matchMomentData.moments} layout="vertical" margin={{ left: 110 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11 }} stroke={chartColors.axis} tickFormatter={formatEngagement} />
              <YAxis type="category" dataKey="label" tick={{ fontSize: 11 }} stroke={chartColors.axis} width={100} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => formatEngagement(v)} />
              <Bar dataKey="avg_engagement" name="Avg Engagement" fill="#2563EB" />
            </BarChart>
          </ResponsiveContainer>

          {matchMomentData.underutilised_moments.length > 0 && (
            <div className="mt-6 border-l-4 border-warning-600 dark:border-warning-dark bg-warning-50 dark:bg-stone-900 p-4">
              <div className="font-mono text-xs uppercase tracking-wider text-warning-700 dark:text-warning-dark mb-2">
                Underutilised Opportunity
              </div>
              {matchMomentData.underutilised_moments.map((moment) => (
                <p key={moment.moment} className="font-body text-sm text-stone-700 dark:text-stone-300 mb-2">
                  <strong className="text-ink dark:text-stone-100">{moment.label}</strong> averages{" "}
                  {formatEngagement(moment.avg_engagement)} engagement (
                  {moment.vs_non_matchday_multiplier.toFixed(1)}x non-matchday) but represents only{" "}
                  {moment.pct_of_total_posts.toFixed(1)}% of posts.
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Format Performance */}
      {formatData && (
        <div className={sectionCard}>
          <h2 className={sectionTitle}>Format Performance</h2>
          <p className={sectionSubtitle}>
            {formatData.top_format} generates {formatData.top_format_multiplier.toFixed(1)}x more engagement than standard posts.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className={tableHeader}>Format</th>
                  <th className={tableHeader}>Platform</th>
                  <th className={tableHeader + " text-right"}>Avg Eng/Post</th>
                  <th className={tableHeader + " text-right"}>Posts</th>
                  <th className={tableHeader + " text-right"}>vs Standard</th>
                  <th className={tableHeader + " text-center"}>Recommended</th>
                </tr>
              </thead>
              <tbody>
                {formatData.formats.slice(0, 10).map((format, idx) => (
                  <tr key={idx} className={idx % 2 === 0 ? "bg-paper dark:bg-stone-800" : "bg-stone-50 dark:bg-stone-900"}>
                    <td className={tableCell + " font-semibold"}>{format.label}</td>
                    <td className={tableCell}>{format.platform}</td>
                    <td className={tableCellMono + " text-right"}>{format.avg_engagement.toLocaleString()}</td>
                    <td className={tableCell + " text-right"}>{format.post_count.toLocaleString()}</td>
                    <td className={tableCellMono + " text-right font-semibold"}>{format.vs_standard_post_multiplier.toFixed(1)}x</td>
                    <td className="border border-stone-300 dark:border-stone-700 p-3 text-center font-mono text-sm">
                      {format.recommended ? (
                        <span className="text-good-light dark:text-good-dark font-bold">✓</span>
                      ) : format.vs_standard_post_multiplier > 1.5 ? (
                        <span className="text-stone-400 dark:text-stone-500">—</span>
                      ) : (
                        <span className="text-critical-light dark:text-critical-dark">✗</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );

  // ── HASHTAGS ──────────────────────────────────────────────────────────────
  const renderHashtags = () => (
    <div>
      {hashtagData && (
        <>
          {/* Leaderboard */}
          <div className={sectionCard}>
            <h2 className={sectionTitle}>Hashtag Intelligence</h2>
            <p className={sectionSubtitle}>What amplifies reach — filter by hashtag type.</p>
            <div className="flex flex-wrap gap-2 mb-6">
              {["all", "event", "player", "branded", "farewell"].map((type) => (
                <button
                  key={type}
                  id={`hashtag-filter-${type}`}
                  onClick={() => setHashtagFilter(type)}
                  className={`${pillBase} ${hashtagFilter === type ? pillActive : pillInactive}`}
                >
                  {type === "all" ? "All" : type}
                </button>
              ))}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <th className={tableHeader}>#</th>
                    <th className={tableHeader}>Hashtag</th>
                    <th className={tableHeader + " text-right"}>Avg Engagement</th>
                    <th className={tableHeader + " text-right"}>Posts</th>
                    <th className={tableHeader}>Type</th>
                  </tr>
                </thead>
                <tbody>
                  {hashtagData.hashtags
                    .filter((ht) => hashtagFilter === "all" || ht.hashtag_type === hashtagFilter)
                    .slice(0, 15)
                    .map((hashtag, idx) => (
                      <tr
                        key={hashtag.hashtag}
                        className={`${idx % 2 === 0 ? "bg-paper dark:bg-stone-800" : "bg-stone-50 dark:bg-stone-900"}`}
                      >
                        <td className={tableCellMono + " text-stone-400 dark:text-stone-500"}>{idx + 1}</td>
                        <td className={tableCellMono + " text-info-600 dark:text-info-dark font-semibold"}>{hashtag.hashtag}</td>
                        <td className={tableCellMono + " text-right"}>{hashtag.avg_engagement.toLocaleString()}</td>
                        <td className={tableCell + " text-right"}>{hashtag.post_count}</td>
                        <td className="border border-stone-300 dark:border-stone-700 p-3">
                          <span
                            className={`font-mono text-xs uppercase tracking-wider px-2 py-1 border ${
                              hashtag.hashtag_type === "farewell"
                                ? "border-accent-600 text-accent-700 dark:text-accent-dark"
                                : hashtag.hashtag_type === "event"
                                ? "border-good-600 text-good-700 dark:text-good-dark"
                                : hashtag.hashtag_type === "player"
                                ? "border-info-600 text-info-700 dark:text-info-dark"
                                : "border-warning-600 text-warning-700 dark:text-warning-dark"
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

          {/* Category comparison */}
          <div className={sectionCard}>
            <h2 className={sectionTitle}>Hashtag Category Performance</h2>
            <p className={sectionSubtitle}>Average engagement by hashtag category — farewell/tribute events dominate.</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              {["farewell", "event", "player", "branded"].map((type) => {
                const typeHt = hashtagData.hashtags.filter((ht) => ht.hashtag_type === type);
                const avg = typeHt.length > 0 ? typeHt.reduce((s, ht) => s + ht.avg_engagement, 0) / typeHt.length : 0;
                return (
                  <div key={type} className="border-2 border-ink dark:border-stone-700 p-4 bg-paper dark:bg-stone-800">
                    <div className="font-mono text-xs uppercase tracking-widest text-stone-400 dark:text-stone-500 mb-1">{type}</div>
                    <div className="font-mono text-2xl font-semibold text-ink dark:text-stone-100">
                      {avg > 0 ? (avg / 1000).toFixed(0) + "K" : "N/A"}
                    </div>
                    <div className="font-mono text-xs text-stone-500 dark:text-stone-500 mt-1">avg engagement</div>
                  </div>
                );
              })}
            </div>

            <div className="border-l-4 border-info-600 dark:border-info-dark bg-info-50 dark:bg-stone-900 p-4">
              <div className="font-mono text-xs uppercase tracking-wider text-info-700 dark:text-info-dark mb-2">
                Hashtag Recommendations — 3 to prioritise
              </div>
              <ol className="space-y-2 font-body text-sm text-stone-700 dark:text-stone-300">
                <li>
                  <strong className="text-ink dark:text-stone-100">1. {hashtagData.top_hashtag_overall || "#event-hashtag"}:</strong>{" "}
                  Planned event content (El Clásico, UCL draw) — highest overall engagement
                </li>
                <li>
                  <strong className="text-ink dark:text-stone-100">2. {hashtagData.top_player_hashtag || "#player-hashtag"}:</strong>{" "}
                  Top-performing player features — strongest player engagement
                </li>
                <li>
                  <strong className="text-ink dark:text-stone-100">3. {hashtagData.top_evergreen_hashtag || "#evergreen-hashtag"}:</strong>{" "}
                  Always-on content — consistent performance across seasons
                </li>
              </ol>
            </div>
          </div>
        </>
      )}
    </div>
  );

  // ── CONTENT ───────────────────────────────────────────────────────────────
  const renderContent = () => (
    <div>
      {/* Content Type Bar Chart */}
      <div className={sectionCard}>
        <h2 className={sectionTitle}>Content Type Performance</h2>
        <p className={sectionSubtitle}>
          Average engagement per post by content type — click a bar to drill down.{" "}
          Top type:{" "}
          <span className="font-mono text-xs uppercase tracking-widest text-ink dark:text-stone-100">
            {summary.top_performing_content_type}
          </span>
        </p>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            data={contentChartData}
            onClick={(data) => {
              if (data?.activePayload?.[0]) {
                const clicked = data.activePayload[0].payload.name;
                setSelectedContentType(selectedContentType === clicked ? null : clicked);
              }
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} vertical={false} />
            <XAxis dataKey="name" stroke={chartColors.axis} tick={{ fill: chartColors.text, fontSize: 11 }} angle={-15} textAnchor="end" height={80} />
            <YAxis stroke={chartColors.axis} tick={{ fill: chartColors.text, fontSize: 11 }} tickFormatter={formatEngagement} />
            <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => formatEngagement(v)} />
            <Bar dataKey="avg_engagement" name="Avg Engagement" cursor="pointer">
              {contentChartData.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={getContentTypeColor(entry.name)}
                  opacity={selectedContentType && selectedContentType !== entry.name ? 0.3 : 1}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        {selectedContentType && (
          <div className="mt-6 border-2 border-info-600 dark:border-info-dark p-6 bg-info-50 dark:bg-stone-900 animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-headline text-xl text-ink dark:text-stone-100">
                Drill-Down › {selectedContentType}
              </h3>
              <button
                onClick={() => setSelectedContentType(null)}
                className="font-mono text-xs uppercase tracking-wider text-stone-500 dark:text-stone-400 hover:text-stone-700 dark:hover:text-stone-300 border border-stone-300 dark:border-stone-600 px-3 py-1"
              >
                Close ✕
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div className="border border-stone-300 dark:border-stone-700 p-4 bg-paper dark:bg-stone-800">
                <div className="font-mono text-xs uppercase tracking-widest text-stone-400 dark:text-stone-500 mb-1">
                  Avg Engagement / Post
                </div>
                <div className="font-mono text-2xl font-semibold text-ink dark:text-stone-100">
                  {formatEngagement(contentChartData.find((c) => c.name === selectedContentType)?.avg_engagement || 0)}
                </div>
              </div>
            </div>

            {contentIntelligence &&
              contentIntelligence.signals.filter(
                (s) => s.content_type.replace(/_/g, " ").toLowerCase() === selectedContentType.toLowerCase()
              ).length > 0 && (
                <div>
                  <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-3">
                    Commercial Correlations
                  </div>
                  {contentIntelligence.signals
                    .filter((s) => s.content_type.replace(/_/g, " ").toLowerCase() === selectedContentType.toLowerCase())
                    .slice(0, 3)
                    .map((signal, idx) => (
                      <div key={idx} className="mb-3 p-3 border border-stone-200 dark:border-stone-700 bg-paper dark:bg-stone-800">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-body text-sm font-semibold text-ink dark:text-stone-100">
                            {signal.commercial_metric} ({signal.commercial_asset})
                          </span>
                          <span className={`font-mono text-xs uppercase tracking-wider px-2 py-1 border ${signal.strength_label === "Strong" ? "border-good-600 text-good-700 dark:text-good-dark" : "border-warning-600 text-warning-700 dark:text-warning-dark"}`}>
                            {signal.strength_label} · {signal.lag_months}mo lag
                          </span>
                        </div>
                        <p className="font-body text-xs text-stone-700 dark:text-stone-300">
                          {signal.interpretation}
                        </p>
                      </div>
                    ))}
                </div>
              )}
          </div>
        )}
      </div>

      {/* Content Intelligence */}
      {contentIntelligence && contentIntelligence.signals.length > 0 && (
        <div className={sectionCard}>
          <h2 className={sectionTitle}>Content Intelligence</h2>
          <p className={sectionSubtitle}>
            Correlation analysis between content types and commercial outcomes.
          </p>

          <div className="overflow-x-auto mb-6">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className={tableHeader}>Content Type</th>
                  <th className={tableHeader + " text-right"}>Avg Eng/Post</th>
                  <th className={tableHeader}>Correlates with</th>
                  <th className={tableHeader + " text-center"}>Strength</th>
                  <th className={tableHeader + " text-center"}>Lag</th>
                  <th className={tableHeader + " text-center"}>Direction</th>
                </tr>
              </thead>
              <tbody>
                {contentIntelligence.signals.slice(0, 7).map((signal, idx) => (
                  <tr
                    key={idx}
                    className={`cursor-pointer transition-colors ${
                      idx % 2 === 0 ? "bg-paper dark:bg-stone-800" : "bg-stone-50 dark:bg-stone-900"
                    } ${selectedSignal === signal ? "outline outline-2 outline-info-600" : ""}`}
                    onClick={() => setSelectedSignal(signal)}
                  >
                    <td className={tableCell + " font-semibold"}>
                      {signal.content_type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                    </td>
                    <td className={tableCellMono + " text-right"}>{signal.avg_content_engagement.toLocaleString()}</td>
                    <td className={tableCell}>{signal.commercial_metric} ({signal.commercial_asset})</td>
                    <td className="border border-stone-300 dark:border-stone-700 p-3 text-center">
                      <span className={`font-mono text-xs uppercase tracking-wider px-2 py-1 border ${signal.strength_label === "Strong" ? "border-good-600 text-good-700 dark:text-good-dark" : signal.strength_label === "Moderate" ? "border-warning-600 text-warning-700 dark:text-warning-dark" : "border-stone-400 text-stone-500"}`}>
                        {signal.strength_label}
                      </span>
                    </td>
                    <td className={tableCellMono + " text-center"}>{signal.lag_months}mo</td>
                    <td className={`border border-stone-300 dark:border-stone-700 p-3 text-center font-mono text-sm font-semibold ${signal.direction === "positive" ? "text-good-light dark:text-good-dark" : "text-warning-light dark:text-warning-dark"}`}>
                      {signal.direction === "positive" ? "↑ Positive" : "↓ Inverse"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {selectedSignal && (
            <div className="border-2 border-info-600 dark:border-info-dark p-5 bg-info-50 dark:bg-stone-900 animate-fade-in">
              <h4 className="font-headline text-lg text-ink dark:text-stone-100 mb-2">
                {selectedSignal.content_type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())} →{" "}
                {selectedSignal.commercial_metric} ({(selectedSignal.correlation * 100).toFixed(0)}% correlation)
              </h4>
              <p className="font-body text-sm text-stone-700 dark:text-stone-300 mb-3">
                {selectedSignal.interpretation}
              </p>
              <div className="border border-stone-200 dark:border-stone-700 p-3 bg-paper dark:bg-stone-800">
                <p className="font-mono text-xs uppercase tracking-wider text-ink dark:text-stone-100 mb-1">
                  {selectedSignal.direction === "positive" ? "✓ Positive Signal" : "⚠ Inverse Signal"}
                </p>
                <p className="font-body text-xs text-stone-700 dark:text-stone-300">
                  {selectedSignal.confidence_note}
                </p>
              </div>
            </div>
          )}

          {/* Summary stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            {[
              { label: "Total Correlations Found", value: contentIntelligence.summary.total_correlations_found },
              { label: "Most Predictive Content", value: contentIntelligence.summary.most_predictive_content_type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()) },
              { label: "Avg Correlation", value: `${(contentIntelligence.summary.avg_correlation_strength * 100).toFixed(0)}%` },
            ].map((stat) => (
              <div key={stat.label} className="border border-stone-200 dark:border-stone-700 p-4 bg-stone-50 dark:bg-stone-900">
                <div className="font-mono text-xs uppercase tracking-widest text-stone-400 dark:text-stone-500 mb-1">{stat.label}</div>
                <div className="font-mono text-2xl font-semibold text-ink dark:text-stone-100">{stat.value}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // ── INTERNATIONAL ─────────────────────────────────────────────────────────
  const renderInternational = () => (
    <div>
      {internationalData && (
        <div className={sectionCard}>
          <h2 className={sectionTitle}>International Audience Intelligence</h2>
          <p className={sectionSubtitle}>
            Real Madrid's global fanbase by language market. International engagement is a leading indicator for global commercial reach.
          </p>

          {/* Hero stat */}
          <div className="mb-8 border-2 border-ink dark:border-stone-700 p-8 text-center bg-stone-50 dark:bg-stone-900">
            <div className="font-mono text-5xl font-semibold text-info-600 dark:text-info-dark mb-2">
              {formatPercentage(internationalData.international_engagement_ratio)}
            </div>
            <p className="font-body text-base text-stone-700 dark:text-stone-300 mb-2">
              of Real Madrid's social engagement comes from international accounts
            </p>
            {summary.international_engagement_ratio_mom_change !== null && (
              <div
                className={`font-mono text-xs font-semibold ${
                  summary.international_engagement_ratio_mom_change > 0
                    ? "text-good-light dark:text-good-dark"
                    : "text-critical-light dark:text-critical-dark"
                }`}
              >
                {summary.international_engagement_ratio_mom_change > 0 ? "↑" : "↓"}{" "}
                {Math.abs(summary.international_engagement_ratio_mom_change).toFixed(1)}% vs prior month
              </div>
            )}
          </div>

          {/* Language market chart */}
          <div className="mb-8">
            <h3 className={subSectionTitle}>
              Engagement by Language Market —{" "}
              {new Date(internationalData.month).toLocaleDateString("en-US", { month: "short", year: "numeric" })}
            </h3>
            {!internationalData.language_markets || internationalData.language_markets.length === 0 ? (
              <div className="flex items-center justify-center h-40 border-2 border-stone-300 dark:border-stone-700 bg-stone-50 dark:bg-stone-900">
                <p className="font-mono text-xs uppercase tracking-wider text-stone-400 dark:text-stone-500">
                  No language breakdown data available for this month
                </p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart
                  data={internationalData.language_markets.map((m) => ({
                    name: m.language,
                    engagement: m.monthly_engagement,
                    pct: m.pct_of_total_engagement,
                  }))}
                  layout="vertical"
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} horizontal={false} />
                  <XAxis type="number" stroke={chartColors.axis} tick={{ fill: chartColors.text, fontSize: 11 }} tickFormatter={formatEngagement} />
                  <YAxis type="category" dataKey="name" stroke={chartColors.axis} tick={{ fill: chartColors.text, fontSize: 11 }} width={70} />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(value: number, name: string) => {
                      if (name === "engagement") {
                        const m = internationalData.language_markets.find((mk) => mk.monthly_engagement === value);
                        return [`${formatEngagement(value)} (${m?.pct_of_total_engagement?.toFixed(1)}%)`, "Engagement"];
                      }
                      return [value, name];
                    }}
                  />
                  <Bar dataKey="engagement" name="Monthly Engagement">
                    {internationalData.language_markets.map((m) => (
                      <Cell key={m.language} fill={m.language === "Spanish" ? "#2563EB" : "#16A34A"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Market growth ranking */}
          {marketGrowth && (
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <h3 className={subSectionTitle}>Market Growth Ranking</h3>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs uppercase tracking-widest text-stone-400 dark:text-stone-500">Compare:</span>
                  <select
                    id="market-compare-mode"
                    value={marketCompareMode}
                    onChange={(e) => setMarketCompareMode(e.target.value as "mom" | "yoy" | "custom")}
                    className="font-mono text-xs border-2 border-ink dark:border-stone-600 bg-paper dark:bg-stone-800 text-ink dark:text-stone-100 px-2 py-1"
                  >
                    <option value="mom">Month over Month</option>
                    <option value="yoy">Year over Year</option>
                    <option value="custom">Custom Month</option>
                  </select>
                  {marketCompareMode === "custom" && availableMonths.length > 0 && (
                    <select
                      id="market-compare-month"
                      value={marketCompareMonth || ""}
                      onChange={(e) => setMarketCompareMonth(e.target.value)}
                      className="font-mono text-xs border-2 border-ink dark:border-stone-600 bg-paper dark:bg-stone-800 text-ink dark:text-stone-100 px-2 py-1"
                    >
                      <option value="">Select month…</option>
                      {availableMonths.map((m) => (
                        <option key={m.value} value={m.value}>{m.label} 2025</option>
                      ))}
                    </select>
                  )}
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr>
                      <th className={tableHeader}>Market</th>
                      <th className={tableHeader + " text-right"}>This Month</th>
                      <th className={tableHeader + " text-right"}>Prior</th>
                      <th className={tableHeader + " text-right"}>Change</th>
                    </tr>
                  </thead>
                  <tbody>
                    {marketGrowth.rankings.map((ranking, idx) => (
                      <tr key={idx} className={idx % 2 === 0 ? "bg-paper dark:bg-stone-800" : "bg-stone-50 dark:bg-stone-900"}>
                        <td className={tableCell + " font-semibold"}>{ranking.market}</td>
                        <td className={tableCellMono + " text-right"}>{formatEngagement(ranking.this_month)}</td>
                        <td className={tableCellMono + " text-right"}>{formatEngagement(ranking.prior_month)}</td>
                        <td className={`border border-stone-300 dark:border-stone-700 p-3 text-right font-mono text-sm font-semibold ${
                          ranking.mom_change_pct > 0 ? "text-good-light dark:text-good-dark"
                          : ranking.mom_change_pct < 0 ? "text-critical-light dark:text-critical-dark"
                          : "text-stone-400"
                        }`}>
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

          {/* Commercial correlation */}
          {internationalCorrelation?.strongest_correlation ? (
            <div className="border-l-4 border-good-600 dark:border-good-dark bg-good-50 dark:bg-stone-900 p-5">
              <h3 className="font-headline text-lg text-ink dark:text-stone-100 mb-2">
                International Audience → Commercial Impact
              </h3>
              <p className="font-body text-sm text-stone-700 dark:text-stone-300 mb-3">
                {internationalCorrelation.strongest_correlation.interpretation}
              </p>
              <div className="flex flex-wrap gap-4 font-mono text-xs">
                <span className="text-stone-600 dark:text-stone-400">
                  Correlation:{" "}
                  <strong className="text-ink dark:text-stone-100">
                    {(internationalCorrelation.strongest_correlation.correlation * 100).toFixed(0)}%
                  </strong>
                </span>
                <span className="text-stone-600 dark:text-stone-400">
                  Lag:{" "}
                  <strong className="text-ink dark:text-stone-100">
                    {internationalCorrelation.strongest_correlation.lag_months} month(s)
                  </strong>
                </span>
                <span className="text-stone-600 dark:text-stone-400">
                  Metric:{" "}
                  <strong className="text-ink dark:text-stone-100">
                    {internationalCorrelation.strongest_correlation.commercial_metric}
                  </strong>
                </span>
              </div>
            </div>
          ) : internationalCorrelation ? (
            <div className="border border-stone-200 dark:border-stone-700 p-5 bg-stone-50 dark:bg-stone-900">
              <h3 className="font-body text-base font-semibold text-ink dark:text-stone-100 mb-2">Commercial Correlation Analysis</h3>
              <p className="font-body text-sm text-stone-600 dark:text-stone-400">
                12 months of data may be insufficient for robust correlation detection. As more data accumulates, correlations between international engagement and commercial metrics may emerge.
              </p>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );

  // ── Render ────────────────────────────────────────────────────────────────

  // ── Strategy tab: three logical sub-sections within one tab ─────────────
  const renderStrategy = () => (
    <div>
      {/* Strategy sub-navigation — lighter than main tabs */}
      <div className="flex gap-6 mb-8 border-b border-stone-300 dark:border-stone-700">
        {([
          { id: "timing" as const,   label: "Timing" },
          { id: "content" as const,  label: "Content" },
          { id: "hashtags" as const, label: "Hashtags" },
        ] as { id: typeof strategySubSection; label: string }[]).map((sub) => (
          <button
            key={sub.id}
            id={`strategy-sub-${sub.id}`}
            onClick={() => setStrategySubSection(sub.id)}
            className={`font-mono text-xs uppercase tracking-wider pb-3 border-b-2 -mb-px transition-colors duration-150 ${
              strategySubSection === sub.id
                ? "border-stone-500 dark:border-stone-400 text-ink dark:text-stone-100"
                : "border-transparent text-stone-400 dark:text-stone-500 hover:text-stone-600 dark:hover:text-stone-300"
            }`}
          >
            {sub.label}
          </button>
        ))}
      </div>
      {strategySubSection === "timing" && renderTiming()}
      {strategySubSection === "content" && renderContent()}
      {strategySubSection === "hashtags" && renderHashtags()}
    </div>
  );

  // ── Intelligence tab: two logical sub-sections within one tab ───────────
  const renderIntelligence = () => (
    <div>
      {/* Intelligence sub-navigation */}
      <div className="flex gap-6 mb-8 border-b border-stone-300 dark:border-stone-700">
        {([
          { id: "insights" as const,       label: "Insights & Recommendations" },
          { id: "international" as const,  label: "International Audience" },
        ] as { id: typeof intelligenceSubSection; label: string }[]).map((sub) => (
          <button
            key={sub.id}
            id={`intelligence-sub-${sub.id}`}
            onClick={() => setIntelligenceSubSection(sub.id)}
            className={`font-mono text-xs uppercase tracking-wider pb-3 border-b-2 -mb-px transition-colors duration-150 ${
              intelligenceSubSection === sub.id
                ? "border-stone-500 dark:border-stone-400 text-ink dark:text-stone-100"
                : "border-transparent text-stone-400 dark:text-stone-500 hover:text-stone-600 dark:hover:text-stone-300"
            }`}
          >
            {sub.label}
          </button>
        ))}
      </div>
      {intelligenceSubSection === "insights" && renderInsights()}
      {intelligenceSubSection === "international" && renderInternational()}
    </div>
  );

  const tabContent: Record<SocialTab, React.ReactNode> = {
    overview:     renderOverview(),
    performance:  <div>{renderTrends()}{renderPlatforms()}</div>,
    strategy:     renderStrategy(),
    intelligence: renderIntelligence(),
  };

  return (
    <div className="max-w-screen-xl mx-auto px-6">
      {/* ── Page header ──────────────────────────────────────────────────── */}
      <div className="py-8 border-b-2 border-ink dark:border-stone-700 mb-0">
        <h1 className="font-headline text-4xl md:text-5xl tracking-tight text-ink dark:text-stone-100 mb-1">
          Social Intelligence
        </h1>
        <p className="font-body text-base text-stone-600 dark:text-stone-400">
          Real Madrid's social media performance across five platforms — the fifth digital pillar of ClubOS.
        </p>
      </div>

      {/* ── Sticky sub-tab navigation ─────────────────────────────────────── */}
      <div className="sticky top-[var(--header-height,112px)] z-30 bg-paper/95 dark:bg-stone-900/95 backdrop-blur-sm border-b-2 border-ink dark:border-stone-700 -mx-6 px-6">
        <nav
          className="flex overflow-x-auto gap-0 no-scrollbar"
          aria-label="Social Intelligence sections"
        >
          {SOCIAL_TABS.map((tab) => (
            <button
              key={tab.id}
              id={`social-tab-${tab.id}`}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-shrink-0 px-6 py-3 border-b-2 transition-colors duration-150 text-left ${
                activeTab === tab.id
                  ? "border-ink dark:border-stone-300"
                  : "border-transparent hover:border-stone-300 dark:hover:border-stone-600"
              }`}
            >
              <div className={`font-mono text-xs uppercase tracking-wider ${
                activeTab === tab.id ? "text-ink dark:text-stone-100" : "text-stone-400 dark:text-stone-500"
              }`}>
                {tab.label}
              </div>
              <div className={`font-body text-[11px] mt-0.5 hidden md:block ${
                activeTab === tab.id ? "text-stone-500 dark:text-stone-400" : "text-stone-300 dark:text-stone-600"
              }`}>
                {tab.subtitle}
              </div>
            </button>
          ))}
        </nav>
      </div>

      {/* ── Active tab content ────────────────────────────────────────────── */}
      <div className="py-8">
        {tabContent[activeTab]}
      </div>

      {/* ── Screen Guide ─────────────────────────────────────────────────── */}
      <div className="pb-12" data-screen-guide>
        <ScreenGuide
          screenName="Social Intelligence"
          sections={[
            {
              title: "What social media metrics mean",
              content:
                "Social engagement (likes, comments, shares, saves) measures fan interaction intensity. Higher engagement = stronger emotional connection to content.",
            },
            {
              title: "Why engagement rate matters more than raw engagement",
              content:
                "Engagement rate (engagement divided by follower count) normalizes for audience size. A 1.9% Instagram rate means 1.9% of followers engage with each post — exceptional for an account with 180M followers.",
            },
            {
              title: "International engagement ratio",
              content:
                "Percentage of engagement from non-Spanish accounts. High ratio (89%+) indicates global brand strength and commercial reach beyond the domestic market.",
            },
            {
              title: "Platform performance",
              content:
                "TikTok often shows highest avg engagement per post due to algorithm favoring viral content. Instagram leads in total volume due to its largest follower base.",
            },
            {
              title: "Content → Commercial correlations",
              content:
                "Correlation analysis between content types and commercial outcomes (sales, subscriptions, web traffic). Use these insights to align content strategy with revenue goals.",
            },
          ]}
        />
      </div>
    </div>
  );
}
