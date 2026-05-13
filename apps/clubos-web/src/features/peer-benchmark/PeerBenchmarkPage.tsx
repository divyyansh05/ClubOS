import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { getBenchmark } from "../../lib/api";
import type { BenchmarkResponse } from "../../types/clubos";
import { MetricDetailModal } from "../../components/ui/MetricDetailModal";
import { InfoTooltip } from "../../components/ui/InfoTooltip";
import { ScreenGuide } from "../../components/ui/ScreenGuide";
import { getMetricUnit } from "../../lib/metricDefinitions";

const METRICS = [
  { asset: "main_website", metric: "unique_visitors", label: "Website - Unique Visitors" },
  { asset: "main_website", metric: "bounce_rate", label: "Website - Bounce Rate" },
  { asset: "ecommerce", metric: "conversion_rate", label: "eCommerce - Conversion Rate" },
  { asset: "ecommerce", metric: "net_sales", label: "eCommerce - Net Sales" },
  { asset: "ecommerce", metric: "cart_value", label: "eCommerce - Cart Value" },
  { asset: "streaming", metric: "subscriptions", label: "Streaming - Subscriptions" },
  { asset: "streaming", metric: "subscription_rate", label: "Streaming - Subscription Rate" },
  { asset: "fan_app", metric: "app_downloads", label: "Fan App - Downloads" },
];

interface MetricDetail {
  name: string;
  value: string | number;
  category: string;
  explanation: string;
  businessContext: string;
  trendData?: Array<{ month: string; value: number }>;
  additionalInfo?: Record<string, string | number>;
}

export function PeerBenchmarkPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [benchmark, setBenchmark] = useState<BenchmarkResponse | null>(null);
  const [selectedMetric, setSelectedMetric] = useState(METRICS[2]); // ecommerce conversion_rate
  const [selectedMetricDetail, setSelectedMetricDetail] = useState<MetricDetail | null>(null);

  useEffect(() => {
    async function loadBenchmark() {
      try {
        setLoading(true);
        const data = await getBenchmark(selectedMetric.asset, selectedMetric.metric);
        setBenchmark(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load benchmark data");
      } finally {
        setLoading(false);
      }
    }
    loadBenchmark();
  }, [selectedMetric]);

  function handleMetricChange(asset: string, metric: string) {
    const selected = METRICS.find((m) => m.asset === asset && m.metric === metric);
    if (selected) {
      setSelectedMetric(selected);
    }
  }

  function showMetricDetail(metric: MetricDetail) {
    setSelectedMetricDetail(metric);
  }

  function closeMetricDetail() {
    setSelectedMetricDetail(null);
  }

  if (loading) {
    return (
      <section className="max-w-screen-xl mx-auto px-6 py-12">
        <h2 className="font-headline text-3xl mb-4">Peer Benchmark</h2>
        <div className="p-8 border border-ink dark:border-stone-700 bg-stone-50 dark:bg-stone-800 font-body">
          Loading benchmark data...
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="max-w-screen-xl mx-auto px-6 py-12">
        <h2 className="font-headline text-3xl mb-4">Peer Benchmark</h2>
        <div className="p-8 border border-ink dark:border-stone-700 bg-stone-50 dark:bg-stone-800 text-critical-light dark:text-critical-dark font-body">
          <strong>Error:</strong> {error}
        </div>
      </section>
    );
  }

  if (!benchmark || benchmark.points.length === 0) {
    return (
      <section className="max-w-screen-xl mx-auto px-6 py-12">
        <h2 className="font-headline text-3xl mb-4">Peer Benchmark</h2>
        <p className="p-8 border border-ink dark:border-stone-700 bg-stone-50 dark:bg-stone-800 font-body">
          No benchmark data available for this metric.
        </p>
      </section>
    );
  }

  const latestPoint = benchmark.points[benchmark.points.length - 1];

  // Determine border color based on rank
  let borderColor = "border-critical-light dark:border-critical-dark";
  let rankCategory = "Review Needed";
  if (latestPoint.rm_rank <= 2) {
    borderColor = "border-good-light dark:border-good-dark";
    rankCategory = "Good Performance";
  } else if (latestPoint.rm_rank === 3) {
    borderColor = "border-info-light dark:border-info-dark";
    rankCategory = "Mid-Pack";
  }

  const getRankColor = (rank: number) => {
    if (rank === 1) return "text-good-light dark:text-good-dark border-good-light dark:border-good-dark";
    if (rank === 2) return "text-info-light dark:text-info-dark border-info-light dark:border-info-dark";
    if (rank === latestPoint.rm_rank) return "text-critical-light dark:text-critical-dark border-critical-light dark:border-critical-dark bg-critical-light dark:bg-critical-dark";
    if (rank === latestPoint.club_count) return "text-warning-light dark:text-warning-dark border-warning-light dark:border-warning-dark";
    return "text-accent-light dark:text-accent-dark border-accent-light dark:border-accent-dark";
  };

  // Chart data (last 12 months)
  const chartData = benchmark.points.slice(-12).map(point => ({
    month: point.month.substring(0, 7),
    rm: point.rm_value,
    median: point.peer_median,
    leader: point.peer_leader_value,
  }));

  return (
    <section className="max-w-screen-xl mx-auto px-6 py-12">
      {/* Hero */}
      <div className="border-b-4 border-ink dark:border-stone-600 pb-8 mb-12">
        <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-4">
          Competitive Position Analysis
        </div>
        <h1 className="font-headline text-5xl md:text-7xl lg:text-8xl leading-[0.95] tracking-tight mb-6">
          Peer<br/>Benchmark
        </h1>
        <p className="font-body text-lg md:text-xl text-stone-600 dark:text-stone-400 leading-relaxed max-w-2xl">
          Compare Real Madrid's performance against {latestPoint.club_count - 1} peer clubs across key commercial metrics.
        </p>
      </div>

      {/* Metric Selector */}
      <div className="mb-8">
        <label className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 block mb-3">
          Select Metric
        </label>
        <div className="flex items-center gap-3 flex-wrap">
          <select
            className="px-4 py-3 border-2 border-ink dark:border-stone-700 bg-paper dark:bg-stone-900 font-mono text-sm cursor-pointer hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
            value={`${selectedMetric.asset}:${selectedMetric.metric}`}
            onChange={(e) => {
              const [asset, metric] = e.target.value.split(":");
              handleMetricChange(asset, metric);
            }}
          >
            {METRICS.map((m) => (
              <option key={`${m.asset}:${m.metric}`} value={`${m.asset}:${m.metric}`}>
                {m.label}
              </option>
            ))}
          </select>
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm text-stone-600 dark:text-stone-400">About this metric:</span>
            <InfoTooltip metricName={selectedMetric.metric} size="md" />
          </div>
        </div>
      </div>

      {/* Current Position */}
      <section className="mb-12">
        <h2 className="font-headline text-3xl mb-6 pb-2 border-b-2 border-ink dark:border-stone-700">
          Current Position
        </h2>

        <div className={`border-2 ${borderColor} p-8`}>
          <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
            <div>
              <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                {selectedMetric.label}
              </div>
              <div className="font-headline text-4xl mb-2">Real Madrid Position</div>
              <button
                onClick={() => showMetricDetail({
                  name: "Current Rank",
                  value: `#${latestPoint.rm_rank} of ${latestPoint.club_count}`,
                  category: rankCategory,
                  explanation: `Real Madrid ranks #${latestPoint.rm_rank} out of ${latestPoint.club_count} peer clubs for ${selectedMetric.label}. ${latestPoint.rm_rank === 1 ? "This is the top position - Real Madrid leads all peers." : latestPoint.rm_rank <= 2 ? "This is a strong competitive position in the upper tier." : latestPoint.rm_rank === 3 ? "This is a mid-pack position with room for improvement." : "This rank indicates underperformance relative to peers and represents a priority for improvement."}`,
                  businessContext: `Competitive ranking matters because it shows where Real Madrid stands relative to the world's top clubs. ${latestPoint.rm_rank > 3 ? "Being ranked lower means losing ground in commercial competitiveness, which can affect sponsorship deals, fan engagement, and overall revenue potential." : "A strong ranking demonstrates commercial excellence and makes Real Madrid more attractive to partners and fans."}`,
                  additionalInfo: {
                    "Current Rank": `#${latestPoint.rm_rank}`,
                    "Total Clubs": latestPoint.club_count,
                    "Gap to Leader": latestPoint.gap_to_leader.toFixed(4),
                    "Gap to Median": latestPoint.gap_to_peer_median.toFixed(4),
                  }
                })}
                className="font-mono text-xl hover:underline cursor-pointer"
              >
                <span className={`font-bold ${latestPoint.rm_rank <= 2 ? 'text-good-light dark:text-good-dark' : latestPoint.rm_rank === 3 ? 'text-info-light dark:text-info-dark' : 'text-critical-light dark:text-critical-dark'}`}>
                  #{latestPoint.rm_rank}
                </span>
                <span className="text-stone-500 dark:text-stone-400"> out of {latestPoint.club_count} clubs</span>
              </button>
            </div>
            <div className="text-right">
              <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                Current Value
              </div>
              <button
                onClick={() => showMetricDetail({
                  name: selectedMetric.label,
                  value: latestPoint.rm_value.toLocaleString(),
                  category: rankCategory,
                  explanation: `Real Madrid's current value for ${selectedMetric.label} is ${latestPoint.rm_value.toLocaleString()}. This compares to a peer median of ${latestPoint.peer_median.toLocaleString()} and a leader value of ${latestPoint.peer_leader_value.toLocaleString()}.`,
                  businessContext: `This metric represents actual performance data. ${latestPoint.gap_to_peer_median < 0 ? `Being ${Math.abs(latestPoint.gap_to_peer_median).toLocaleString()} below the median indicates an area requiring strategic focus and investment.` : `Performing above the median shows competitive strength in this area.`}`,
                  trendData: benchmark.points.slice(-12).map(p => ({ month: p.month.substring(5, 7), value: p.rm_value })),
                  additionalInfo: {
                    "RM Value": latestPoint.rm_value.toLocaleString(),
                    "Peer Median": latestPoint.peer_median.toLocaleString(),
                    "Peer Leader": latestPoint.peer_leader_value.toLocaleString(),
                    "Month": latestPoint.month,
                  }
                })}
                className={`font-mono text-5xl font-bold hover:underline cursor-pointer ${latestPoint.rm_rank <= 2 ? 'text-good-light dark:text-good-dark' : latestPoint.rm_rank === 3 ? 'text-info-light dark:text-info-dark' : 'text-critical-light dark:text-critical-dark'}`}
              >
                {latestPoint.rm_value.toLocaleString()}
              </button>
            </div>
          </div>

          {/* Position Scale */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
              <div className="text-center">
                <div className={`w-16 h-16 border-2 ${getRankColor(1)} flex items-center justify-center mb-2 font-headline text-2xl`}>
                  1
                </div>
                <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Leader</div>
                <div className="font-mono text-sm font-bold mt-1">{latestPoint.peer_leader_value.toLocaleString()}</div>
              </div>

              <div className="flex-1 h-px bg-stone-300 dark:bg-stone-700 mx-2 min-w-[20px]"></div>

              <div className="text-center">
                <div className={`w-16 h-16 border-2 ${getRankColor(Math.ceil(latestPoint.club_count / 2))} flex items-center justify-center mb-2 font-headline text-2xl`}>
                  M
                </div>
                <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Median</div>
                <div className="font-mono text-sm font-bold mt-1">{latestPoint.peer_median.toLocaleString()}</div>
              </div>

              <div className="flex-1 h-px bg-stone-300 dark:bg-stone-700 mx-2 min-w-[20px]"></div>

              <div className="text-center">
                <div className={`w-16 h-16 border-2 ${getRankColor(latestPoint.rm_rank)} flex items-center justify-center mb-2 font-headline text-2xl ${latestPoint.rm_rank > 2 ? 'text-white' : ''}`}>
                  {latestPoint.rm_rank}
                </div>
                <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Real Madrid</div>
                <div className={`font-mono text-sm font-bold mt-1 ${latestPoint.rm_rank <= 2 ? 'text-good-light dark:text-good-dark' : 'text-critical-light dark:text-critical-dark'}`}>
                  {latestPoint.rm_value.toLocaleString()}
                </div>
              </div>

              <div className="flex-1 h-px bg-stone-300 dark:bg-stone-700 mx-2 min-w-[20px]"></div>

              <div className="text-center">
                <div className={`w-16 h-16 border-2 ${getRankColor(latestPoint.club_count)} flex items-center justify-center mb-2 font-headline text-2xl`}>
                  {latestPoint.club_count}
                </div>
                <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Last Place</div>
                <div className="font-mono text-sm font-bold mt-1">-</div>
              </div>
            </div>
          </div>

          {/* Gap Stats - Now Clickable */}
          <div className="grid grid-cols-2 gap-px bg-ink dark:bg-stone-700 border border-ink dark:border-stone-700">
            <button
              onClick={() => showMetricDetail({
                name: "Gap to Peer Median",
                value: latestPoint.gap_to_peer_median.toLocaleString(),
                category: latestPoint.gap_to_peer_median < 0 ? "Review Needed" : "Good Performance",
                explanation: `Real Madrid is ${Math.abs(latestPoint.gap_to_peer_median).toLocaleString()} ${latestPoint.gap_to_peer_median < 0 ? 'behind' : 'ahead of'} the peer median for ${selectedMetric.label}. The median represents the middle value when all ${latestPoint.club_count} clubs are ranked.`,
                businessContext: `${latestPoint.gap_to_peer_median < 0 ? 'Being behind the median means Real Madrid is performing worse than half of peer clubs. This gap represents lost revenue potential and competitive disadvantage.' : 'Performing above the median demonstrates competitive strength and positions Real Madrid in the upper tier of peer clubs.'}`,
                additionalInfo: {
                  "Gap": latestPoint.gap_to_peer_median.toLocaleString(),
                  "RM Value": latestPoint.rm_value.toLocaleString(),
                  "Peer Median": latestPoint.peer_median.toLocaleString(),
                  "Status": latestPoint.gap_to_peer_median < 0 ? "Behind" : "Ahead",
                }
              })}
              className="bg-paper dark:bg-stone-900 p-4 hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-colors text-left"
            >
              <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-1">
                Gap to Median
              </div>
              <div className="font-mono text-xl font-bold text-ink dark:text-stone-100">
                {latestPoint.gap_to_peer_median > 0 ? "+" : ""}
                {latestPoint.gap_to_peer_median.toLocaleString()}
              </div>
              <div className={`font-mono text-sm ${latestPoint.gap_to_peer_median < 0 ? 'text-critical-light dark:text-critical-dark' : 'text-good-light dark:text-good-dark'}`}>
                {latestPoint.gap_to_peer_median < 0 ? "Behind" : "Ahead"}
              </div>
            </button>
            <button
              onClick={() => showMetricDetail({
                name: "Gap to Leader",
                value: latestPoint.gap_to_leader.toLocaleString(),
                category: latestPoint.gap_to_leader < 0 ? "Growth Opportunity" : "Market Leader",
                explanation: `Real Madrid is ${Math.abs(latestPoint.gap_to_leader).toLocaleString()} ${latestPoint.gap_to_leader < 0 ? 'behind' : 'ahead of'} the peer leader for ${selectedMetric.label}. The leader represents best-in-class performance among peer clubs.`,
                businessContext: `${latestPoint.gap_to_leader < 0 ? 'The gap to the leader shows the ceiling for potential improvement. Closing this gap represents the maximum upside opportunity if Real Madrid achieves industry-leading performance.' : 'Leading peers in this metric demonstrates market-leading performance and sets the standard for competitors.'}`,
                additionalInfo: {
                  "Gap": latestPoint.gap_to_leader.toLocaleString(),
                  "RM Value": latestPoint.rm_value.toLocaleString(),
                  "Leader Value": latestPoint.peer_leader_value.toLocaleString(),
                  "RM Rank": `#${latestPoint.rm_rank}`,
                }
              })}
              className="bg-paper dark:bg-stone-900 p-4 hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-colors text-left"
            >
              <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-1">
                Gap to Leader
              </div>
              <div className="font-mono text-xl font-bold text-ink dark:text-stone-100">
                {latestPoint.gap_to_leader > 0 ? "+" : ""}
                {latestPoint.gap_to_leader.toLocaleString()}
              </div>
              <div className={`font-mono text-sm ${latestPoint.gap_to_leader < 0 ? 'text-critical-light dark:text-critical-dark' : 'text-good-light dark:text-good-dark'}`}>
                {latestPoint.gap_to_leader < 0 ? "Behind" : "Ahead"}
              </div>
            </button>
          </div>
        </div>
      </section>

      {/* 12-Month Trend */}
      <section className="mb-12">
        <div className="flex items-center gap-3 mb-6 pb-2 border-b-2 border-ink dark:border-stone-700">
          <h2 className="font-headline text-3xl">
            12-Month Trend Comparison
          </h2>
          <InfoTooltip metricName={selectedMetric.metric} size="md" />
        </div>

        <div className="border border-ink dark:border-stone-700 p-6 bg-stone-50 dark:bg-stone-800">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#A3A39E" />
              <XAxis
                dataKey="month"
                tick={{ fontSize: 11, fontFamily: "JetBrains Mono, monospace" }}
                stroke="#75756F"
              />
              <YAxis
                tick={{ fontSize: 11, fontFamily: "JetBrains Mono, monospace" }}
                stroke="#75756F"
                label={{ value: getMetricUnit(selectedMetric.metric), angle: -90, position: 'insideLeft', style: { fontSize: 11, fill: '#75756F' } }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "rgba(26, 26, 24, 0.95)",
                  border: "1px solid #434340",
                  borderRadius: "4px",
                  fontFamily: "JetBrains Mono, monospace",
                  fontSize: "11px",
                }}
              />
              <Legend
                iconType="line"
                wrapperStyle={{
                  fontFamily: "JetBrains Mono, monospace",
                  fontSize: "12px",
                  fontWeight: "500",
                }}
              />
              <Line
                type="monotone"
                dataKey="rm"
                stroke="#EF4444"
                strokeWidth={3}
                dot={{ r: 5 }}
                name="Real Madrid"
              />
              <Line
                type="monotone"
                dataKey="median"
                stroke="#3B82F6"
                strokeWidth={3}
                dot={{ r: 5 }}
                name="Peer Median"
              />
              <Line
                type="monotone"
                dataKey="leader"
                stroke="#22C55E"
                strokeWidth={3}
                dot={{ r: 5 }}
                name="Leader"
              />
            </LineChart>
          </ResponsiveContainer>

          {/* Gap Annotation */}
          <div className="mt-4 p-4 border-t border-stone-300 dark:border-stone-700 bg-paper dark:bg-stone-900">
            <p className="font-body text-sm text-stone-600 dark:text-stone-400 leading-relaxed">
              <strong className="text-ink dark:text-stone-100">Understanding the gaps:</strong> Real Madrid (red line) is currently{" "}
              <span className={latestPoint.gap_to_peer_median < 0 ? 'text-critical-600 dark:text-critical-dark font-semibold' : 'text-good-600 dark:text-good-dark font-semibold'}>
                {latestPoint.gap_to_peer_median < 0 ? Math.abs(latestPoint.gap_to_peer_median).toFixed(4) + ' behind' : '+' + latestPoint.gap_to_peer_median.toFixed(4) + ' ahead of'}
              </span>{" "}
              the peer median (blue line) and{" "}
              <span className={latestPoint.gap_to_leader < 0 ? 'text-critical-600 dark:text-critical-dark font-semibold' : 'text-good-600 dark:text-good-dark font-semibold'}>
                {latestPoint.gap_to_leader < 0 ? Math.abs(latestPoint.gap_to_leader).toFixed(4) + ' behind' : '+' + latestPoint.gap_to_leader.toFixed(4) + ' ahead of'}
              </span>{" "}
              the market leader (green line). {latestPoint.gap_to_peer_median < 0 ? 'Closing these gaps represents significant commercial upside potential.' : 'Maintaining performance above peers demonstrates competitive strength.'}
            </p>
          </div>
        </div>
      </section>

      {/* Recent Trend Table - Rows Clickable */}
      <section>
        <h2 className="font-headline text-3xl mb-6 pb-2 border-b-2 border-ink dark:border-stone-700">
          Recent Trend (Last 6 Months)
        </h2>

        <div className="border border-ink dark:border-stone-700">
          <table className="w-full data-table border-ink dark:border-stone-700 font-mono text-sm border-collapse">
            <thead>
              <tr className="bg-stone-100 dark:bg-stone-800">
                <th className="text-left p-4 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Month</th>
                <th className="text-right p-4 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Real Madrid</th>
                <th className="text-right p-4 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Peer Median</th>
                <th className="text-right p-4 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Gap</th>
                <th className="text-right p-4 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Trend</th>
              </tr>
            </thead>
            <tbody>
              {benchmark.points.slice(-6).reverse().map((point) => {
                const prevPointIndex = benchmark.points.findIndex(p => p.month === point.month) - 1;
                const prevPoint = prevPointIndex >= 0 ? benchmark.points[prevPointIndex] : null;
                let trendIcon = "→";
                let trendColor = "text-warning-light dark:text-warning-dark";
                if (prevPoint) {
                  if (point.rm_value > prevPoint.rm_value) {
                    trendIcon = "↑";
                    trendColor = "text-good-light dark:text-good-dark";
                  } else if (point.rm_value < prevPoint.rm_value) {
                    trendIcon = "↓";
                    trendColor = "text-critical-light dark:text-critical-dark";
                  }
                }

                return (
                  <tr
                    key={point.month}
                    onClick={() => showMetricDetail({
                      name: `${selectedMetric.label} - ${point.month}`,
                      value: point.rm_value.toLocaleString(),
                      category: point.gap_to_peer_median < 0 ? "Behind Peers" : "Above Peers",
                      explanation: `In ${point.month}, Real Madrid's ${selectedMetric.label} was ${point.rm_value.toLocaleString()}, ranking #${point.rm_rank} out of ${point.club_count} clubs. This was ${Math.abs(point.gap_to_peer_median).toLocaleString()} ${point.gap_to_peer_median < 0 ? 'below' : 'above'} the peer median of ${point.peer_median.toLocaleString()}.`,
                      businessContext: `Historical performance shows how Real Madrid's competitive position has evolved over time. ${point.gap_to_peer_median < 0 ? 'Consistent underperformance vs peers indicates a structural issue requiring strategic intervention.' : 'Sustained performance above peers demonstrates competitive strength.'}`,
                      additionalInfo: {
                        "Month": point.month,
                        "RM Value": point.rm_value.toLocaleString(),
                        "Peer Median": point.peer_median.toLocaleString(),
                        "Gap": point.gap_to_peer_median.toLocaleString(),
                        "Rank": `#${point.rm_rank}`,
                      }
                    })}
                    className="hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors cursor-pointer"
                  >
                    <td className="p-4 text-ink dark:text-stone-100 font-semibold border border-ink dark:border-stone-700">{point.month}</td>
                    <td className="p-4 text-right font-bold border border-ink dark:border-stone-700">{point.rm_value.toLocaleString()}</td>
                    <td className="p-4 text-right border border-ink dark:border-stone-700">{point.peer_median.toLocaleString()}</td>
                    <td className={`p-4 text-right font-bold border border-ink dark:border-stone-700 ${point.gap_to_peer_median < 0 ? 'text-critical-light dark:text-critical-dark' : 'text-good-light dark:text-good-dark'}`}>
                      {point.gap_to_peer_median > 0 ? "+" : ""}
                      {point.gap_to_peer_median.toLocaleString()}
                    </td>
                    <td className={`p-4 text-right border border-ink dark:border-stone-700 ${trendColor}`}>{trendIcon}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Screen Guide */}
      <div data-screen-guide className="mt-12">
        <ScreenGuide
          screenName="Peer Benchmark"
          sections={[
            {
              title: "What is peer benchmarking?",
              content: "Peer benchmarking compares Real Madrid's performance against 5 European clubs (Barcelona, Bayern Munich, Manchester United, Paris Saint-Germain, Manchester City) across 8 key commercial metrics over 103 months (2017-2026). This shows whether Real Madrid is leading, keeping pace, or falling behind competitors in critical areas like website traffic, eCommerce conversion, streaming subscriptions, and more."
            },
            {
              title: "How to interpret the rankings?",
              content: "Rank #1 means Real Madrid leads all peer clubs—best-in-class performance. Ranks #2-3 indicate competitive upper-tier performance. Rank #4 or below signals underperformance relative to peers and represents a priority for improvement. The 'Gap to Median' shows how far Real Madrid is from the middle value of all clubs, while 'Gap to Leader' shows the ceiling for potential improvement."
            },
            {
              title: "Why do some metrics show values like 0.013 instead of percentages?",
              content: "Conversion rates and other percentage-based metrics are stored as decimals (0.013 = 1.3%). This is standard database practice. Use the [?] icon next to each metric name to see the definition, formula, and example interpretation. The 12-month trend chart shows how Real Madrid's position has evolved over time—consistent underperformance vs peers indicates a structural issue requiring strategic intervention."
            },
            {
              title: "How do these benchmarks connect to priorities?",
              content: "When a Priority Board issue includes a benchmarked metric, the 'Peer Gap' score component measures how far Real Madrid lags behind peers. A large peer gap (high score) means the priority is both an internal problem AND a competitive disadvantage. Focus on priorities with high peer gap scores first—they represent compounding risks where Real Madrid is losing ground to competitors."
            }
          ]}
        />
      </div>

      {/* Metric Detail Modal */}
      {selectedMetricDetail && (
        <MetricDetailModal
          isOpen={!!selectedMetricDetail}
          onClose={closeMetricDetail}
          metricName={selectedMetricDetail.name}
          metricValue={selectedMetricDetail.value}
          metricCategory={selectedMetricDetail.category}
          explanation={selectedMetricDetail.explanation}
          businessContext={selectedMetricDetail.businessContext}
          trendData={selectedMetricDetail.trendData}
          additionalInfo={selectedMetricDetail.additionalInfo}
        />
      )}
    </section>
  );
}
