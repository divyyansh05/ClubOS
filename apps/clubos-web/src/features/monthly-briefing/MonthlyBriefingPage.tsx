import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import { getLatestBriefing } from "../../lib/api";
import type { BriefingResponse } from "../../types/clubos";
import { MetricDetailModal } from "../../components/ui/MetricDetailModal";
import { InfoTooltip } from "../../components/ui/InfoTooltip";
import { ScreenGuide } from "../../components/ui/ScreenGuide";
import { formatMonthYear } from "../../lib/dateFormat";
import { formatMetricValue } from "../../lib/formatNumber";

interface MetricDetail {
  name: string;
  value: string | number;
  category: string;
  explanation: string;
  businessContext: string;
  trendData?: Array<{ month: string; value: number }>;
  additionalInfo?: Record<string, string | number>;
}

export function MonthlyBriefingPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [briefing, setBriefing] = useState<BriefingResponse | null>(null);
  const [selectedMetricDetail, setSelectedMetricDetail] = useState<MetricDetail | null>(null);

  function showMetricDetail(detail: MetricDetail) {
    setSelectedMetricDetail(detail);
  }

  function closeMetricDetail() {
    setSelectedMetricDetail(null);
  }

  useEffect(() => {
    async function loadBriefing() {
      try {
        setLoading(true);
        const data = await getLatestBriefing();
        setBriefing(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load monthly briefing");
      } finally {
        setLoading(false);
      }
    }
    loadBriefing();
  }, []);

  if (loading) {
    return (
      <section className="max-w-screen-xl mx-auto px-6 py-12">
        <h2 className="font-headline text-3xl mb-4">Monthly Briefing</h2>
        <div className="p-8 border border-ink dark:border-stone-700 bg-stone-50 dark:bg-stone-800 font-body">
          Loading monthly briefing...
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="max-w-screen-xl mx-auto px-6 py-12">
        <h2 className="font-headline text-3xl mb-4">Monthly Briefing</h2>
        <div className="p-8 border border-ink dark:border-stone-700 bg-stone-50 dark:bg-stone-800 text-critical-light dark:text-critical-dark font-body">
          <strong>Error:</strong> {error}
        </div>
      </section>
    );
  }

  if (!briefing || !briefing.month) {
    return (
      <section className="max-w-screen-xl mx-auto px-6 py-12">
        <h2 className="font-headline text-3xl mb-4">Monthly Briefing</h2>
        <p className="p-8 border border-ink dark:border-stone-700 bg-stone-50 dark:bg-stone-800 font-body">
          No briefing data available.
        </p>
      </section>
    );
  }

  const healthPct = briefing.health_summary
    ? (briefing.health_summary.good_count / briefing.health_summary.metric_count) * 100
    : 0;

  // Priority color helper
  const getPriorityColor = (category: string) => {
    if (category === "critical") return "border-critical-light dark:border-critical-dark bg-critical-light dark:bg-critical-dark text-critical-light dark:text-critical-dark";
    if (category === "opportunity") return "border-good-light dark:border-good-dark bg-good-light dark:bg-good-dark text-good-light dark:text-good-dark";
    if (category === "benchmark") return "border-info-light dark:border-info-dark bg-info-light dark:bg-info-dark text-info-light dark:text-info-dark";
    if (category === "warning") return "border-warning-light dark:border-warning-dark bg-warning-light dark:bg-warning-dark text-warning-light dark:text-warning-dark";
    return "border-accent-light dark:border-accent-dark bg-accent-light dark:bg-accent-dark text-accent-light dark:text-accent-dark";
  };

  // Donut chart data for health
  const healthChartData = briefing.health_summary ? [
    { name: `Good (${briefing.health_summary.good_count})`, value: briefing.health_summary.good_count, color: "#22C55E" },
    { name: `Review (${briefing.health_summary.review_count})`, value: briefing.health_summary.review_count, color: "#F97316" },
    { name: `Stable (${briefing.health_summary.stable_count})`, value: briefing.health_summary.stable_count, color: "#3B82F6" },
  ] : [];

  return (
    <section className="max-w-screen-xl mx-auto px-6 py-12">
      {/* Hero */}
      <div className="border-b-4 border-ink dark:border-stone-600 pb-8 mb-12">
        <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-4">
          Executive Summary · {briefing.month}
        </div>
        <h1 className="font-headline text-5xl md:text-7xl lg:text-8xl leading-[0.95] tracking-tight mb-6">
          Monthly<br/>Briefing
        </h1>
        <p className="font-body text-lg md:text-xl text-stone-600 dark:text-stone-400 leading-relaxed max-w-2xl">
          Consolidated view of top priorities, anomalies, and signals for executive decision-making this month.
        </p>
      </div>

      {/* Executive Summary */}
      <section className="mb-12 border-2 border-ink dark:border-stone-700 p-8 bg-stone-50 dark:bg-stone-800">
        <h2 className="font-headline text-3xl mb-6">Key Takeaways</h2>
        <ul className="space-y-4 font-body text-base leading-relaxed">
          <li className="flex gap-4">
            <span className="flex-shrink-0 w-8 h-8 border-2 border-critical-light dark:border-critical-dark flex items-center justify-center font-mono text-xs font-bold text-critical-light dark:text-critical-dark">
              1
            </span>
            <span className="text-stone-700 dark:text-stone-300">
              <strong className="text-ink dark:text-stone-100">{briefing.top_priorities.length} priorities</strong> identified for this month based on severity, persistence, and commercial impact
            </span>
          </li>
          <li className="flex gap-4">
            <span className="flex-shrink-0 w-8 h-8 border-2 border-warning-light dark:border-warning-dark flex items-center justify-center font-mono text-xs font-bold text-warning-light dark:text-warning-dark">
              2
            </span>
            <span className="text-stone-700 dark:text-stone-300">
              <strong className="text-ink dark:text-stone-100">{briefing.top_anomalies.length} notable anomalies</strong> showing significant deviations from seasonal baselines
            </span>
          </li>
          {briefing.benchmark_summary && (
            <li className="flex gap-4">
              <span className="flex-shrink-0 w-8 h-8 border-2 border-info-light dark:border-info-dark flex items-center justify-center font-mono text-xs font-bold text-info-light dark:text-info-dark">
                3
              </span>
              <span className="text-stone-700 dark:text-stone-300">
                <strong className="text-ink dark:text-stone-100">{briefing.benchmark_summary.benchmark_underperformance_count} metrics underperforming</strong> vs peer benchmark requiring strategic review
              </span>
            </li>
          )}
          {briefing.strongest_signals.length > 0 && (
            <li className="flex gap-4">
              <span className="flex-shrink-0 w-8 h-8 border-2 border-good-light dark:border-good-dark flex items-center justify-center font-mono text-xs font-bold text-good-light dark:text-good-dark">
                4
              </span>
              <span className="text-stone-700 dark:text-stone-300">
                <strong className="text-ink dark:text-stone-100">{briefing.strongest_signals.length} leading signals</strong> active this month to watch for future performance trends
              </span>
            </li>
          )}
        </ul>
      </section>

      {/* Top 3 Priorities */}
      {briefing.top_priorities.length > 0 && (
        <section className="mb-12">
          <h2 className="font-headline text-3xl mb-6 pb-2 border-b-2 border-ink dark:border-stone-700">
            Top {Math.min(3, briefing.top_priorities.length)} Priorities
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {briefing.top_priorities.slice(0, 3).map((priority) => {
              const colors = getPriorityColor(priority.priority_category);
              const [borderClass, bgClass, textClass] = colors.split(' ');

              return (
                <article
                  key={priority.priority_id}
                  onClick={() => showMetricDetail({
                    name: `Priority #${priority.priority_rank}: ${priority.priority_title}`,
                    value: priority.priority_score.toFixed(2),
                    category: priority.priority_category,
                    explanation: `This priority has a score of ${priority.priority_score.toFixed(2)} and is ranked #${priority.priority_rank} for ${briefing.month}. The priority score combines severity, persistence, commercial impact, peer comparison, and supporting evidence.`,
                    businessContext: priority.priority_category === 'critical'
                      ? `A "Critical" priority with rank #${priority.priority_rank} means this issue requires immediate attention. It's likely impacting commercial outcomes and shows concerning patterns. This should be a top focus area for investigation and action this month.`
                      : priority.priority_category === 'opportunity'
                      ? `An "Opportunity" priority ranked #${priority.priority_rank} represents a growth potential. This metric or area is showing positive signals that could be amplified with focused effort. Consider investing resources to maximize the upside.`
                      : `This priority is flagged for review because it's showing patterns that warrant attention. While not critical, understanding the drivers and determining next steps should be on the agenda for this month.`,
                    additionalInfo: {
                      "Priority Rank": `#${priority.priority_rank}`,
                      "Score": priority.priority_score.toFixed(3),
                      "Category": priority.priority_category,
                      "Month": briefing.month,
                    }
                  })}
                  className={`border-2 ${borderClass} p-6 hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-all`}
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-12 h-12 ${bgClass} flex items-center justify-center font-headline text-2xl text-white`}>
                      {priority.priority_rank}
                    </div>
                    <div>
                      <div className={`font-mono text-xs uppercase tracking-widest ${textClass}`}>
                        {priority.priority_category}
                      </div>
                      <div className={`font-mono text-lg font-bold ${textClass}`}>
                        {priority.priority_score.toFixed(2)}
                      </div>
                    </div>
                  </div>
                  <h3 className="font-headline text-xl mb-3">{priority.priority_title}</h3>
                  <div className="flex gap-2">
                    <span className={`px-2 py-1 border ${borderClass} font-mono text-[10px] uppercase tracking-widest ${textClass}`}>
                      {priority.priority_category}
                    </span>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      )}

      {/* Notable Anomalies */}
      {briefing.top_anomalies.length > 0 && (
        <section className="mb-12">
          <h2 className="font-headline text-3xl mb-6 pb-2 border-b-2 border-ink dark:border-stone-700">
            Notable Anomalies
          </h2>

          <div className="border border-ink dark:border-stone-700">
            <table className="w-full data-table border-ink dark:border-stone-700 font-mono text-sm border-collapse">
              <thead>
                <tr className="bg-stone-100 dark:bg-stone-800">
                  <th className="text-left p-4 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Metric</th>
                  <th className="text-left p-4 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Asset</th>
                  <th className="text-right p-4 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Value</th>
                  <th className="text-right p-4 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Change</th>
                  <th className="text-left p-4 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Status</th>
                </tr>
              </thead>
              <tbody>
                {briefing.top_anomalies.slice(0, 5).map((anomaly) => {
                  const isNegative = anomaly.deviation_from_seasonal_baseline < 0;
                  const textColor = isNegative ? 'text-critical-light dark:text-critical-dark' : 'text-good-light dark:text-good-dark';

                  return (
                    <tr
                      key={`${anomaly.asset_name}_${anomaly.metric_name}`}
                      onClick={() => showMetricDetail({
                        name: `Anomaly: ${anomaly.metric_name}`,
                        value: formatMetricValue(anomaly.metric_name, anomaly.metric_value),
                        category: isNegative ? "Declining Performance" : "Surging Performance",
                        explanation: `${anomaly.metric_name} for ${anomaly.asset_name} is showing a ${Math.abs(anomaly.deviation_from_seasonal_baseline * 100).toFixed(1)}% ${isNegative ? 'decline' : 'surge'} compared to the seasonal baseline. Current value is ${formatMetricValue(anomaly.metric_name, anomaly.metric_value)}.`,
                        businessContext: isNegative
                          ? `A ${Math.abs(anomaly.deviation_from_seasonal_baseline * 100).toFixed(1)}% drop from seasonal expectations is significant. This suggests something changed - could be market conditions, campaign performance, user behavior, or technical issues. Investigation needed to understand root cause and determine if intervention is required.`
                          : `A ${(anomaly.deviation_from_seasonal_baseline * 100).toFixed(1)}% surge above seasonal expectations is notable. This could indicate successful campaigns, viral content, seasonal spikes, or data anomalies. Investigate whether this is sustainable growth or a temporary spike.`,
                        additionalInfo: {
                          "Current Value": formatMetricValue(anomaly.metric_name, anomaly.metric_value),
                          "Deviation": `${(anomaly.deviation_from_seasonal_baseline * 100).toFixed(1)}%`,
                          "Asset": anomaly.asset_name,
                          "Status": isNegative ? "Declining" : "Surging",
                        }
                      })}
                      className="hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-colors"
                    >
                      <td className="p-4 text-ink dark:text-stone-100 font-semibold border border-ink dark:border-stone-700">
                        <div className="flex items-center gap-2">
                          <span>{anomaly.metric_name}</span>
                          <InfoTooltip metricName={anomaly.metric_name} size="sm" />
                        </div>
                      </td>
                      <td className="p-4 border border-ink dark:border-stone-700">{anomaly.asset_name}</td>
                      <td className="p-4 text-right border border-ink dark:border-stone-700">
                        {formatMetricValue(anomaly.metric_name, anomaly.metric_value)}
                      </td>
                      <td className={`p-4 text-right font-bold border border-ink dark:border-stone-700 ${textColor}`}>
                        {(anomaly.deviation_from_seasonal_baseline * 100).toFixed(1)}%
                      </td>
                      <td className={`p-4 border border-ink dark:border-stone-700 ${textColor}`}>
                        {isNegative ? "Declining" : "Surging"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Top Signals to Watch */}
      {briefing.strongest_signals.length > 0 && (
        <section className="mb-12">
          <h2 className="font-headline text-3xl mb-6 pb-2 border-b-2 border-ink dark:border-stone-700">
            Top Signals to Watch
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {briefing.strongest_signals.slice(0, 4).map((signal) => (
              <button
                key={signal.signal_id}
                onClick={() => showMetricDetail({
                  name: `Leading Signal: ${signal.source_metric} → ${signal.target_metric}`,
                  value: `${(signal.strength_score * 100).toFixed(0)}% strength`,
                  category: "Predictive Relationship",
                  explanation: `This signal shows that ${signal.source_metric} from ${signal.source_asset} predicts ${signal.target_metric} in ${signal.target_asset} with ${(signal.strength_score * 100).toFixed(0)}% reliability, ${signal.lag_months} months in advance.`,
                  businessContext: `Watch ${signal.source_metric} closely this month - changes you see now will likely appear in ${signal.target_metric} about ${signal.lag_months} months from now. The ${(signal.strength_score * 100).toFixed(0)}% strength means this prediction is highly reliable. Use it for planning and forecasting.`,
                  additionalInfo: {
                    "Signal Rank": `#${signal.signal_rank}`,
                    "Strength": `${(signal.strength_score * 100).toFixed(0)}%`,
                    "Lead Time": `${signal.lag_months} months`,
                    "Direction": signal.relationship_direction,
                    "Source": `${signal.source_asset} - ${signal.source_metric}`,
                    "Target": `${signal.target_asset} - ${signal.target_metric}`,
                  }
                })}
                className="border-2 border-info-light dark:border-info-dark p-6 hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-colors text-left"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 border-2 border-info-light dark:border-info-dark flex items-center justify-center font-mono text-sm font-bold text-info-light dark:text-info-dark">
                    {signal.signal_rank}
                  </div>
                  <div className="flex items-center gap-2 font-headline text-xl">
                    <span>{signal.source_metric}</span>
                    <InfoTooltip metricName={signal.source_metric} size="sm" />
                    <span>→</span>
                    <span>{signal.target_metric}</span>
                    <InfoTooltip metricName={signal.target_metric} size="sm" />
                  </div>
                </div>
                <p className="font-body text-sm text-stone-600 dark:text-stone-400 mb-3">
                  {signal.source_asset} leads {signal.target_asset} by {signal.lag_months} month{signal.lag_months > 1 ? 's' : ''} ({(signal.strength_score * 100).toFixed(0)}% strength)
                </p>
                <div className="font-mono text-xs text-info-light dark:text-info-dark">
                  {signal.relationship_direction === 'positive' ? 'Positive correlation' : 'Negative correlation'}
                </div>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Benchmark Summary */}
      {briefing.benchmark_summary && (
        <section className="mb-12">
          <h2 className="font-headline text-3xl mb-6 pb-2 border-b-2 border-ink dark:border-stone-700">
            Peer Benchmark Summary
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 border border-ink dark:border-stone-700 p-6">
            <button
              onClick={() => showMetricDetail({
                name: "Benchmarked Metrics",
                value: briefing.benchmark_summary!.benchmarked_metric_count,
                category: "Peer Comparison",
                explanation: `We are comparing ${briefing.benchmark_summary!.benchmarked_metric_count} of your metrics against peer clubs. These are metrics where comparable data exists across multiple clubs in your peer group.`,
                businessContext: `Benchmarking ${briefing.benchmark_summary!.benchmarked_metric_count} metrics gives you a comprehensive view of competitive position. More benchmarked metrics means better coverage of your digital performance vs peers. This helps identify where you're ahead, behind, or on par with the industry.`,
                additionalInfo: {
                  "Benchmarked": briefing.benchmark_summary!.benchmarked_metric_count,
                  "Underperforming": briefing.benchmark_summary!.benchmark_underperformance_count,
                  "Underperformance Rate": `${((briefing.benchmark_summary!.benchmark_underperformance_count / briefing.benchmark_summary!.benchmarked_metric_count) * 100).toFixed(0)}%`,
                }
              })}
              className="text-center hover:bg-stone-100 dark:hover:bg-stone-800 p-4 cursor-pointer transition-colors"
            >
              <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                Benchmarked Metrics
              </div>
              <div className="font-headline text-4xl text-ink dark:text-stone-100">
                {briefing.benchmark_summary.benchmarked_metric_count}
              </div>
            </button>
            <button
              onClick={() => showMetricDetail({
                name: "Underperformances vs Peers",
                value: briefing.benchmark_summary!.benchmark_underperformance_count,
                category: "Competitive Gaps",
                explanation: `${briefing.benchmark_summary!.benchmark_underperformance_count} metrics are currently below your peer median, meaning you're underperforming compared to the average club in your peer group for these specific metrics.`,
                businessContext: `Underperformances highlight areas where competitors are doing better. These ${briefing.benchmark_summary!.benchmark_underperformance_count} gaps are strategic opportunities - fixing them could bring you up to industry standards or beyond. Prioritize based on commercial impact and feasibility of improvement.`,
                additionalInfo: {
                  "Underperforming": briefing.benchmark_summary!.benchmark_underperformance_count,
                  "Total Benchmarked": briefing.benchmark_summary!.benchmarked_metric_count,
                  "Avg Gap to Median": briefing.benchmark_summary!.avg_gap_to_peer_median.toFixed(2),
                  "Worst Gap": briefing.benchmark_summary!.worst_gap_to_peer_median.toFixed(2),
                }
              })}
              className="text-center hover:bg-stone-100 dark:hover:bg-stone-800 p-4 cursor-pointer transition-colors"
            >
              <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                Underperformances
              </div>
              <div className="font-headline text-4xl text-critical-light dark:text-critical-dark">
                {briefing.benchmark_summary.benchmark_underperformance_count}
              </div>
            </button>
            <button
              onClick={() => showMetricDetail({
                name: "Average Gap to Peer Median",
                value: briefing.benchmark_summary!.avg_gap_to_peer_median.toFixed(2),
                category: briefing.benchmark_summary!.avg_gap_to_peer_median < 0 ? "Below Peers" : "Above Peers",
                explanation: `On average across all benchmarked metrics, you are ${Math.abs(briefing.benchmark_summary!.avg_gap_to_peer_median).toFixed(2)} ${briefing.benchmark_summary!.avg_gap_to_peer_median < 0 ? 'behind' : 'ahead of'} the peer median. This number averages out all your competitive positions into one overall gap metric.`,
                businessContext: briefing.benchmark_summary!.avg_gap_to_peer_median < 0
                  ? `Being ${Math.abs(briefing.benchmark_summary!.avg_gap_to_peer_median).toFixed(2)} below the median on average means you're generally underperforming vs peers. This isn't catastrophic - it's a signal to focus on closing gaps where they matter most commercially. Some gaps may be strategic trade-offs.`
                  : `Being ${briefing.benchmark_summary!.avg_gap_to_peer_median.toFixed(2)} above the median on average means you're generally outperforming vs peers. This is a competitive advantage worth maintaining. Keep monitoring individual metrics to ensure the lead continues.`,
                additionalInfo: {
                  "Avg Gap to Median": briefing.benchmark_summary!.avg_gap_to_peer_median.toFixed(3),
                  "Worst Gap": briefing.benchmark_summary!.worst_gap_to_peer_median.toFixed(3),
                  "Underperforming Metrics": briefing.benchmark_summary!.benchmark_underperformance_count,
                }
              })}
              className="text-center hover:bg-stone-100 dark:hover:bg-stone-800 p-4 cursor-pointer transition-colors"
            >
              <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                Avg Gap to Median
              </div>
              <div className={`font-headline text-4xl ${briefing.benchmark_summary.avg_gap_to_peer_median < 0 ? 'text-critical-light dark:text-critical-dark' : 'text-good-light dark:text-good-dark'}`}>
                {briefing.benchmark_summary.avg_gap_to_peer_median.toFixed(1)}
              </div>
            </button>
            <button
              onClick={() => showMetricDetail({
                name: "Worst Gap to Peer Median",
                value: briefing.benchmark_summary!.worst_gap_to_peer_median.toFixed(2),
                category: briefing.benchmark_summary!.worst_gap_to_peer_median < 0 ? "Biggest Weakness" : "Biggest Strength",
                explanation: `Your worst competitive gap is ${Math.abs(briefing.benchmark_summary!.worst_gap_to_peer_median).toFixed(2)} ${briefing.benchmark_summary!.worst_gap_to_peer_median < 0 ? 'behind' : 'ahead of'} the peer median. This represents the single metric where you're furthest from your peer group.`,
                businessContext: briefing.benchmark_summary!.worst_gap_to_peer_median < 0
                  ? `The worst gap of ${Math.abs(briefing.benchmark_summary!.worst_gap_to_peer_median).toFixed(2)} below median highlights your biggest competitive weakness. This metric should be investigated immediately - if it's commercially important, it's a high-priority fix. If it's less important, it may be acceptable.`
                  : `The worst gap of ${briefing.benchmark_summary!.worst_gap_to_peer_median.toFixed(2)} above median shows your biggest competitive strength. This is where you're beating peers most decisively. Understand why you're winning here and potentially replicate the strategy elsewhere.`,
                additionalInfo: {
                  "Worst Gap": briefing.benchmark_summary!.worst_gap_to_peer_median.toFixed(3),
                  "Avg Gap": briefing.benchmark_summary!.avg_gap_to_peer_median.toFixed(3),
                  "Total Benchmarked": briefing.benchmark_summary!.benchmarked_metric_count,
                }
              })}
              className="text-center hover:bg-stone-100 dark:hover:bg-stone-800 p-4 cursor-pointer transition-colors"
            >
              <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                Worst Gap
              </div>
              <div className={`font-headline text-4xl ${briefing.benchmark_summary.worst_gap_to_peer_median < 0 ? 'text-critical-light dark:text-critical-dark' : 'text-good-light dark:text-good-dark'}`}>
                {briefing.benchmark_summary.worst_gap_to_peer_median.toFixed(1)}
              </div>
            </button>
          </div>
        </section>
      )}

      {/* Digital Ecosystem Health */}
      {briefing.health_summary && (
        <section className="mb-12">
          <h2 className="font-headline text-3xl mb-6 pb-2 border-b-2 border-ink dark:border-stone-700">
            Digital Ecosystem Health
          </h2>

          <div className="border border-ink dark:border-stone-700 p-6 bg-stone-50 dark:bg-stone-800 mb-6">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={healthChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={0}
                  dataKey="value"
                >
                  {healthChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
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
                  verticalAlign="bottom"
                  height={36}
                  iconType="circle"
                  wrapperStyle={{
                    fontFamily: "JetBrains Mono, monospace",
                    fontSize: "12px",
                    fontWeight: "500",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 border border-ink dark:border-stone-700 p-6">
            <button
              onClick={() => showMetricDetail({
                name: "Total Metrics Tracked",
                value: briefing.health_summary!.metric_count,
                category: "Digital Ecosystem Coverage",
                explanation: `The system is monitoring ${briefing.health_summary!.metric_count} different performance indicators across all your digital assets. This includes metrics from eCommerce, websites, streaming, mobile apps, and social channels.`,
                businessContext: `Tracking ${briefing.health_summary!.metric_count} metrics gives comprehensive visibility into digital performance. Each metric represents a different aspect of user behavior or business outcomes. The breadth of coverage ensures no important signal is missed.`,
                additionalInfo: {
                  "Total Metrics": briefing.health_summary!.metric_count,
                  "Good Health": briefing.health_summary!.good_count,
                  "Needs Review": briefing.health_summary!.review_count,
                  "Stable": briefing.health_summary!.stable_count,
                }
              })}
              className="text-center hover:bg-stone-100 dark:hover:bg-stone-800 p-4 cursor-pointer transition-colors"
            >
              <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                Total Metrics
              </div>
              <div className="font-headline text-4xl text-ink dark:text-stone-100">
                {briefing.health_summary.metric_count}
              </div>
            </button>
            <button
              onClick={() => showMetricDetail({
                name: "Good Health Status",
                value: briefing.health_summary!.good_count,
                category: "Positive Performance",
                explanation: `${briefing.health_summary!.good_count} metrics (${healthPct.toFixed(0)}% of total) are in "Good" health status. These metrics are performing well according to their historical patterns and seasonal expectations.`,
                businessContext: `Having ${healthPct.toFixed(0)}% of metrics in good health means the majority of your digital ecosystem is functioning normally. These ${briefing.health_summary!.good_count} metrics don't require immediate attention - they're on track or exceeding expectations. Focus resources on the metrics that need review instead.`,
                additionalInfo: {
                  "Good Health": briefing.health_summary!.good_count,
                  "Health Percentage": `${healthPct.toFixed(1)}%`,
                  "Total Metrics": briefing.health_summary!.metric_count,
                }
              })}
              className="text-center hover:bg-stone-100 dark:hover:bg-stone-800 p-4 cursor-pointer transition-colors"
            >
              <div className="flex items-center justify-center gap-2 font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                <span>Good Health</span>
                <InfoTooltip
                  title="Good Health"
                  definition="Metrics performing within expected range."
                  size="sm"
                />
              </div>
              <div className="font-headline text-4xl text-good-light dark:text-good-dark">
                {briefing.health_summary.good_count}
              </div>
              <div className="font-mono text-xs text-stone-500 dark:text-stone-400 mt-1">
                ({healthPct.toFixed(0)}%)
              </div>
            </button>
            <button
              onClick={() => showMetricDetail({
                name: "Metrics Needing Review",
                value: briefing.health_summary!.review_count,
                category: "Attention Required",
                explanation: `${briefing.health_summary!.review_count} metrics are flagged as "Needs Review" because they're showing patterns that deviate from expectations - trending down, highly volatile, or underperforming vs peers.`,
                businessContext: `The ${briefing.health_summary!.review_count} metrics needing review are your action items. These require investigation to understand what's changing and whether intervention is needed. Not all "review" metrics are problems - some may be intentional changes or acceptable trade-offs.`,
                additionalInfo: {
                  "Needs Review": briefing.health_summary!.review_count,
                  "Review Percentage": `${((briefing.health_summary!.review_count / briefing.health_summary!.metric_count) * 100).toFixed(1)}%`,
                  "Good Health": briefing.health_summary!.good_count,
                }
              })}
              className="text-center hover:bg-stone-100 dark:hover:bg-stone-800 p-4 cursor-pointer transition-colors"
            >
              <div className="flex items-center justify-center gap-2 font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                <span>Needs Review</span>
                <InfoTooltip
                  title="Needs Review"
                  definition="Metrics showing deviations that merit investigation."
                  size="sm"
                />
              </div>
              <div className="font-headline text-4xl text-warning-light dark:text-warning-dark">
                {briefing.health_summary.review_count}
              </div>
            </button>
            <button
              onClick={() => showMetricDetail({
                name: "Stable Status Metrics",
                value: briefing.health_summary!.stable_count,
                category: "Steady State",
                explanation: `${briefing.health_summary!.stable_count} metrics are marked "Stable" - they're not trending strongly up or down, just holding steady around their normal levels. Stable doesn't mean bad, it means predictable.`,
                businessContext: `${briefing.health_summary!.stable_count} stable metrics provide a foundation of consistency. They're not growing, but they're also not declining. Stability can be good (mature, reliable channels) or a missed opportunity (channels that should be growing). Context matters.`,
                additionalInfo: {
                  "Stable": briefing.health_summary!.stable_count,
                  "Stable Percentage": `${((briefing.health_summary!.stable_count / briefing.health_summary!.metric_count) * 100).toFixed(1)}%`,
                  "Total Metrics": briefing.health_summary!.metric_count,
                }
              })}
              className="text-center hover:bg-stone-100 dark:hover:bg-stone-800 p-4 cursor-pointer transition-colors"
            >
              <div className="flex items-center justify-center gap-2 font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                <span>Stable</span>
                <InfoTooltip
                  title="Stable"
                  definition="Metrics showing consistent performance with minimal variation."
                  size="sm"
                />
              </div>
              <div className="font-headline text-4xl text-info-light dark:text-info-dark">
                {briefing.health_summary.stable_count}
              </div>
            </button>
          </div>
        </section>
      )}

      {/* Usage Guidance */}
      <section className="border-t-2 border-ink dark:border-stone-700 pt-8">
        <h2 className="font-headline text-2xl mb-4">How to Use This Briefing</h2>
        <div className="font-body text-base text-stone-600 dark:text-stone-400 leading-relaxed">
          <ul className="list-disc list-inside space-y-2 mb-4">
            <li>
              <strong className="text-ink dark:text-stone-100">Priorities:</strong> Review the top ranked issues to determine where to focus attention this month
            </li>
            <li>
              <strong className="text-ink dark:text-stone-100">Anomalies:</strong> Investigate metrics showing large seasonal deviations to understand root causes
            </li>
            <li>
              <strong className="text-ink dark:text-stone-100">Peer benchmark:</strong> Compare performance against peer clubs using the Peer Benchmark screen
            </li>
            <li>
              <strong className="text-ink dark:text-stone-100">Leading signals:</strong> Monitor source metrics that tend to precede commercial outcomes
            </li>
            <li>
              <strong className="text-ink dark:text-stone-100">Health status:</strong> Track overall digital ecosystem stability month over month
            </li>
          </ul>
          <p className="font-mono text-xs text-stone-500 dark:text-stone-400 mt-4">
            This briefing is automatically generated from structured data after each monthly refresh. All rankings and scores are traceable to source data.
          </p>
        </div>
      </section>

      {/* Screen Guide */}
      <div data-screen-guide className="mt-12">
        <ScreenGuide
          screenName="Monthly Briefing"
          sections={[
            {
              title: "What is the Monthly Briefing?",
              content: "The Monthly Briefing is ClubOS's executive summary—a consolidated view of the most important commercial insights for the month. It synthesizes data from the Priority Board, Signal Engine, Peer Benchmark, and Command Center into one digestible report. The briefing highlights top priorities, notable anomalies (metrics showing large deviations), leading signals to watch, peer benchmark gaps, and overall digital ecosystem health."
            },
            {
              title: "How should I use this briefing?",
              content: "Start with the Key Takeaways section to understand the big picture. Then review Top Priorities (ranked issues requiring immediate attention), Notable Anomalies (metrics showing significant seasonal deviations), Top Signals to Watch (leading indicators predicting future performance), Peer Benchmark Summary (competitive position), and Digital Ecosystem Health (overall stability). Use this briefing as a monthly checkpoint: determine where to focus attention, which metrics to investigate, and how Real Madrid is performing vs peers."
            },
            {
              title: "What are 'notable anomalies'?",
              content: "Anomalies are metrics showing large deviations from their seasonal baseline—either surging above expectations or declining below. A 'Declining' anomaly means the metric is underperforming its typical seasonal pattern (e.g., January usually sees 1M unique visitors but this January only 750K). A 'Surging' anomaly means the metric is overperforming (e.g., conversion rate expected at 1.3% but actually 1.8%). Not all anomalies are problems—surges may be opportunities, and declines may be intentional changes."
            },
            {
              title: "How do priorities, signals, and benchmarks connect?",
              content: "Priorities are the current month's top commercial concerns (scored by severity, persistence, peer gap, commercial impact, evidence). Signals are leading indicators that predict future priorities—watch them now to anticipate what will appear on the Priority Board 1-3 months from now. Benchmarks show how Real Madrid compares to peers—metrics underperforming vs benchmark often score high on the Priority Board because the 'peer gap' component is elevated. Together, these three systems give you past performance (benchmarks), present issues (priorities), and future predictions (signals)."
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
