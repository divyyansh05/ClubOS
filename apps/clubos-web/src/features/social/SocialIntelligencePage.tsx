import { useEffect, useState } from "react";
import {
  fetchSocialSummary,
  fetchSocialMonthly,
  fetchSocialPlatforms,
  fetchSocialContent,
  fetchContentIntelligence,
  fetchInternationalBreakdown,
  fetchMarketGrowthRanking,
  fetchInternationalCorrelation
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
  InternationalCommercialCorrelationResponse
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

  useEffect(() => {
    async function loadData() {
      try {
        const [summaryData, trendData, intelligenceData, internationalBreakdown, growthRanking, correlationData] = await Promise.all([
          fetchSocialSummary(),
          fetchSocialMonthly(),
          fetchContentIntelligence(),
          fetchInternationalBreakdown(),
          fetchMarketGrowthRanking(),
          fetchInternationalCorrelation(),
        ]);

        setSummary(summaryData);
        setMonthlyTrend(trendData);
        setContentIntelligence(intelligenceData);
        setInternationalData(internationalBreakdown);
        setMarketGrowth(growthRanking);
        setInternationalCorrelation(correlationData);

        // Set initial selected signal (strongest)
        if (intelligenceData.signals.length > 0) {
          setSelectedSignal(intelligenceData.signals[0]);
        }

        // Load platform and content data for latest month
        if (summaryData.latest_month) {
          const monthStr = summaryData.latest_month.substring(0, 7); // YYYY-MM
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
  const formatEngagement = (num: number) => {
    if (num >= 1_000_000_000) return `${(num / 1_000_000_000).toFixed(2)}B`;
    if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(2)}M`;
    if (num >= 1_000) return `${(num / 1_000).toFixed(2)}K`;
    return num.toFixed(0);
  };

  const formatPercentage = (num: number) => `${(num * 100).toFixed(1)}%`;
  const formatMoMChange = (change: number | null) => {
    if (change === null) return null;
    const sign = change > 0 ? "+" : "";
    return `${sign}${change.toFixed(1)}%`;
  };

  // Prepare chart data
  const trendChartData = monthlyTrend.months.map((month, idx) => ({
    month: new Date(month).toLocaleDateString("en-US", { month: "short" }),
    engagement: monthlyTrend.total_engagement[idx],
    posts: monthlyTrend.total_posts[idx],
  }));

  const platformChartData = platformData.map((p) => ({
    name: p.platform.charAt(0).toUpperCase() + p.platform.slice(1),
    avg_engagement: p.avg_engagement,
    posts: p.posts,
  }));

  const contentChartData = contentData.map((c) => ({
    name: c.content_type,
    avg_engagement: c.avg_engagement,
  }));

  // Stat card component
  const StatCard = ({
    title,
    value,
    change,
  }: {
    title: string;
    value: string;
    change: string | null;
  }) => (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</h3>
      </div>
      <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">{value}</div>
      {change && (
        <div
          className={`text-sm ${
            change.startsWith("+") ? "text-green-600" : "text-red-600"
          }`}
        >
          {change.startsWith("+") ? "↑" : "↓"} {change} MoM
        </div>
      )}
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Section 1: Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">Social Intelligence</h1>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          Real Madrid's social media performance across five platforms — the fifth digital pillar of ClubOS.
          55,598 posts analyzed, 4.08B total engagement in 2025.
        </p>
      </div>

      {/* Section 2: Summary Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Engagement"
          value={formatEngagement(summary.total_engagement)}
          change={formatMoMChange(summary.total_engagement_mom_change)}
        />
        <StatCard
          title="Avg Engagement Per Post"
          value={formatEngagement(summary.avg_engagement_per_post)}
          change={formatMoMChange(summary.avg_engagement_per_post_mom_change)}
        />
        <StatCard
          title="Instagram Engagement Rate"
          value={formatPercentage(summary.instagram_engagement_rate)}
          change={formatMoMChange(summary.instagram_engagement_rate_mom_change)}
        />
        <StatCard
          title="International Engagement"
          value={formatPercentage(summary.international_engagement_ratio)}
          change={formatMoMChange(summary.international_engagement_ratio_mom_change)}
        />
      </div>

      {/* Section 3: Monthly Engagement Trend */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">12-Month Engagement Trend</h2>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={trendChartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="month" stroke="#9CA3AF" />
            <YAxis stroke="#9CA3AF" tickFormatter={(val) => formatEngagement(val)} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1F2937",
                border: "1px solid #374151",
                borderRadius: "8px",
              }}
              labelStyle={{ color: "#F3F4F6" }}
              formatter={(value: number) => formatEngagement(value)}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="engagement"
              stroke="#3B82F6"
              strokeWidth={2}
              name="Total Engagement"
              dot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Section 4: Platform Performance Breakdown */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Platform Performance (Latest Month)
        </h2>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={platformChartData} layout="horizontal">
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis type="number" stroke="#9CA3AF" tickFormatter={(val) => formatEngagement(val)} />
            <YAxis type="category" dataKey="name" stroke="#9CA3AF" />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1F2937",
                border: "1px solid #374151",
                borderRadius: "8px",
              }}
              formatter={(value: number) => formatEngagement(value)}
            />
            <Legend />
            <Bar dataKey="avg_engagement" fill="#3B82F6" name="Avg Engagement Per Post" />
          </BarChart>
        </ResponsiveContainer>
        <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
          Top platform: <span className="font-semibold text-blue-600 dark:text-blue-400">
            {summary.top_performing_platform}
          </span>
        </div>
      </div>

      {/* Section 5: Content Intelligence (V1.6.4) */}
      {contentIntelligence && contentIntelligence.signals.length > 0 && (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 mb-8">
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
                    <th className="text-center p-3">Lag</th>
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
                      <td className="p-3 text-center">{signal.lag_months}mo</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {selectedSignal && (
              <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950 border border-blue-300 dark:border-blue-700 rounded">
                <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
                  {selectedSignal.content_type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())} →{" "}
                  {selectedSignal.commercial_metric} (
                  {(selectedSignal.correlation * 100).toFixed(0)}% correlation)
                </h4>
                <p className="text-sm text-blue-800 dark:text-blue-200">
                  {selectedSignal.interpretation}
                </p>
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
                When <strong>{contentIntelligence.summary.strongest_signal.content_type.replace(/_/g, " ")}</strong> posts
                generate high engagement, <strong>{contentIntelligence.summary.strongest_signal.commercial_metric}</strong> on{" "}
                <strong>{contentIntelligence.summary.strongest_signal.commercial_asset}</strong> tends to be{" "}
                <strong>{contentIntelligence.summary.strongest_signal.direction}</strong> approximately{" "}
                <strong>{contentIntelligence.summary.strongest_signal.lag_months} month(s)</strong> later.
              </p>
              <div className="flex items-center gap-4 text-sm">
                <span className="text-green-700 dark:text-green-300">
                  Correlation strength: <strong>{(contentIntelligence.summary.strongest_signal.correlation * 100).toFixed(0)}%</strong>
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
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Content Type Performance (Latest Month)
        </h2>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={contentChartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="name" stroke="#9CA3AF" angle={-15} textAnchor="end" height={100} />
            <YAxis stroke="#9CA3AF" tickFormatter={(val) => formatEngagement(val)} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1F2937",
                border: "1px solid #374151",
                borderRadius: "8px",
              }}
              formatter={(value: number) => formatEngagement(value)}
            />
            <Legend />
            <Bar dataKey="avg_engagement" fill="#10B981" name="Avg Engagement" />
          </BarChart>
        </ResponsiveContainer>
        <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
          Top content type: <span className="font-semibold text-green-600 dark:text-green-400">
            {summary.top_performing_content_type}
          </span>
        </div>
      </div>

      {/* Section 7: International Audience Intelligence (V1.6.6) */}
      {internationalData && (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 mb-8">
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
            <ResponsiveContainer width="100%" height={350}>
              <BarChart
                data={internationalData.language_markets.map((m) => ({
                  name: m.language,
                  engagement: m.monthly_engagement,
                  pct: m.pct_of_total_engagement,
                }))}
                layout="horizontal"
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis type="number" stroke="#9CA3AF" tickFormatter={(val) => formatEngagement(val)} />
                <YAxis type="category" dataKey="name" stroke="#9CA3AF" width={80} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1F2937",
                    border: "1px solid #374151",
                    borderRadius: "8px",
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
                <Legend />
                <Bar
                  dataKey="engagement"
                  fill={(entry: any) => (entry.name === "Spanish" ? "#3B82F6" : "#10B981")}
                  name="Monthly Engagement"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Sub-section C: Market Growth Ranking */}
          {marketGrowth && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                Market Growth Ranking — Month-over-Month Change
              </h3>
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
