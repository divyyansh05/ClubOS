import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import { getHealthSummary } from "../../lib/api";
import type { HealthSummary } from "../../types/clubos";
import { MetricDetailModal } from "../../components/ui/MetricDetailModal";
import { InfoTooltip } from "../../components/ui/InfoTooltip";
import { ScreenGuide } from "../../components/ui/ScreenGuide";
import { formatMonthYear } from "../../lib/dateFormat";

interface MetricDetail {
  name: string;
  value: string | number;
  category: string;
  explanation: string;
  businessContext: string;
  additionalInfo?: Record<string, string | number>;
}

export function CommandCenterPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [healthSummary, setHealthSummary] = useState<HealthSummary | null>(null);
  const [selectedMetric, setSelectedMetric] = useState<MetricDetail | null>(null);

  useEffect(() => {
    async function loadHealthSummary() {
      try {
        setLoading(true);
        const data = await getHealthSummary();
        setHealthSummary(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load health summary");
      } finally {
        setLoading(false);
      }
    }
    loadHealthSummary();
  }, []);

  function showMetricDetail(metric: MetricDetail) {
    setSelectedMetric(metric);
  }

  function closeMetricDetail() {
    setSelectedMetric(null);
  }

  if (loading) {
    return (
      <section className="max-w-screen-xl mx-auto px-6 py-12">
        <h2 className="font-headline text-3xl mb-4">Command Center</h2>
        <div className="p-8 border border-ink dark:border-stone-700 bg-stone-50 dark:bg-stone-800 font-body">
          Loading digital ecosystem health...
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="max-w-screen-xl mx-auto px-6 py-12">
        <h2 className="font-headline text-3xl mb-4">Command Center</h2>
        <div className="p-8 border border-ink dark:border-stone-700 bg-stone-50 dark:bg-stone-800 text-critical-light dark:text-critical-dark font-body">
          <strong>Error:</strong> {error}
        </div>
      </section>
    );
  }

  if (!healthSummary) {
    return (
      <section className="max-w-screen-xl mx-auto px-6 py-12">
        <h2 className="font-headline text-3xl mb-4">Command Center</h2>
        <p className="p-8 border border-ink dark:border-stone-700 bg-stone-50 dark:bg-stone-800 font-body">
          No health data available.
        </p>
      </section>
    );
  }

  const healthPercentage = (healthSummary.good_count / healthSummary.metric_count) * 100;
  const reviewPercentage = (healthSummary.review_count / healthSummary.metric_count) * 100;
  const stablePercentage = (healthSummary.stable_count / healthSummary.metric_count) * 100;

  // Donut chart data
  const chartData = [
    { name: `Good Health (${healthSummary.good_count})`, value: healthSummary.good_count, color: "good" },
    { name: `Review Needed (${healthSummary.review_count})`, value: healthSummary.review_count, color: "warning" },
    { name: `Stable (${healthSummary.stable_count})`, value: healthSummary.stable_count, color: "info" },
  ];

  // Colors for chart
  const COLORS = {
    good: "#22C55E",
    warning: "#F97316",
    info: "#3B82F6",
  };

  return (
    <section className="max-w-screen-xl mx-auto px-6 py-12">
      {/* Hero */}
      <div className="border-b-4 border-ink dark:border-stone-600 pb-8 mb-12">
        <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-4">
          Ecosystem Health Monitor
        </div>
        <h1 className="font-headline text-5xl md:text-7xl lg:text-8xl leading-[0.95] tracking-tight mb-6">
          Command<br/>Center
        </h1>
        <p className="font-body text-lg md:text-xl text-stone-600 dark:text-stone-400 leading-relaxed max-w-2xl">
          Real-time health overview of {healthSummary.metric_count} commercial metrics across all assets, categorized by performance status and deviation from target.
        </p>
        <p className="font-mono text-xs text-stone-500 dark:text-stone-400 mt-4">
          Reporting month: {formatMonthYear(healthSummary.latest_month)}
        </p>
      </div>

      {/* Summary Cards - Now Clickable */}
      <div className="mb-12 border border-ink dark:border-stone-700">
        <div className="grid grid-cols-2 md:grid-cols-4">
          <button
            onClick={() => showMetricDetail({
              name: "Total Metrics Tracked",
              value: healthSummary.metric_count,
              category: "System Metric",
              explanation: `We are currently tracking ${healthSummary.metric_count} different performance indicators across all digital channels. This includes metrics from the website, social media, ecommerce, ticketing, and other digital touchpoints.`,
              businessContext: "This number represents the breadth of your digital monitoring system. A comprehensive tracking system helps identify issues early and spot opportunities across all channels. Each metric is automatically monitored monthly to detect changes that require attention.",
              additionalInfo: {
                "Good Health": healthSummary.good_count,
                "Review Needed": healthSummary.review_count,
                "Stable": healthSummary.stable_count,
              }
            })}
            className="p-6 border-l-4 border-accent-light dark:border-accent-dark border-r border-b md:border-b-0 border-ink dark:border-stone-700 hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-all text-left"
          >
            <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
              Total Metrics
            </div>
            <div className="font-headline text-5xl mb-1 text-ink dark:text-stone-100">
              {healthSummary.metric_count}
            </div>
            <div className="h-1 bg-accent-light dark:bg-accent-dark"></div>
          </button>

          <button
            onClick={() => showMetricDetail({
              name: "Metrics in Good Health",
              value: healthSummary.good_count,
              category: "Good Health",
              explanation: `${healthSummary.good_count} metrics (${healthPercentage.toFixed(0)}% of total) are currently performing within their expected range. These metrics show no significant deviations from seasonal patterns and are tracking as expected.`,
              businessContext: "Metrics in 'Good Health' are performing normally and don't require immediate action. This indicates stable performance across these areas of your digital business. A higher percentage of good health metrics suggests overall system stability.",
              additionalInfo: {
                "Percentage": `${healthPercentage.toFixed(1)}%`,
                "Total Metrics": healthSummary.metric_count,
                "Latest Month": healthSummary.latest_month,
              }
            })}
            className="p-6 border-l-4 border-good-light dark:border-good-dark border-b md:border-b-0 md:border-r border-ink dark:border-stone-700 hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-all text-left"
          >
            <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
              <span>Good Health</span>
              <InfoTooltip
                title="Good Health Status"
                definition="Metrics performing within their expected range, showing no significant deviations from seasonal patterns. These metrics are tracking as expected and don't require immediate action."
                example="If Website unique_visitors typically ranges between 800K-1.2M in January and this January shows 950K, that's good health—within normal bounds."
                polarity="Higher percentage is better"
                size="sm"
              />
            </div>
            <div className="font-headline text-5xl mb-1 text-ink dark:text-stone-100">
              {healthSummary.good_count}
            </div>
            <div className="h-1 bg-good-light dark:bg-good-dark"></div>
          </button>

          <button
            onClick={() => showMetricDetail({
              name: "Metrics Needing Review",
              value: healthSummary.review_count,
              category: "Review Needed",
              explanation: `${healthSummary.review_count} metrics (${reviewPercentage.toFixed(0)}% of total) are showing deviations that merit investigation. These metrics have moved outside their normal seasonal range and may indicate emerging issues or opportunities.`,
              businessContext: "Metrics flagged for review don't necessarily indicate problems - they're simply showing unexpected patterns that warrant attention. Some may be positive changes (opportunities), while others may need corrective action. These are prioritized on the Priority Board based on severity and commercial impact.",
              additionalInfo: {
                "Percentage": `${reviewPercentage.toFixed(1)}%`,
                "Good Health": healthSummary.good_count,
                "Stable": healthSummary.stable_count,
              }
            })}
            className="p-6 border-l-4 border-warning-light dark:border-warning-dark border-r border-ink dark:border-stone-700 hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-all text-left"
          >
            <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
              <span>Review Needed</span>
              <InfoTooltip
                title="Review Needed Status"
                definition="Metrics showing deviations that merit investigation. These metrics have moved outside their normal seasonal range and may indicate emerging issues or opportunities. Not all review-needed metrics are problems—some may be positive changes."
                example="If conversion_rate typically hovers around 1.3% but drops to 0.9% this month, it's flagged for review. The Priority Board ranks these by severity and commercial impact."
                polarity="Lower percentage is better (fewer problems)"
                size="sm"
              />
            </div>
            <div className="font-headline text-5xl mb-1 text-ink dark:text-stone-100">
              {healthSummary.review_count}
            </div>
            <div className="h-1 bg-warning-light dark:bg-warning-dark"></div>
          </button>

          <button
            onClick={() => showMetricDetail({
              name: "Stable Metrics",
              value: healthSummary.stable_count,
              category: "Stable Status",
              explanation: `${healthSummary.stable_count} metrics (${stablePercentage.toFixed(0)}% of total) show consistent performance with minimal variation. These metrics maintain steady patterns month over month with no significant changes.`,
              businessContext: "Stable metrics indicate areas of your business that are operating consistently. While not necessarily growing, they provide a reliable baseline. Stability can be positive (consistent good performance) or may indicate areas where you're not seeing the growth you'd like.",
              additionalInfo: {
                "Percentage": `${stablePercentage.toFixed(1)}%`,
                "Total Metrics": healthSummary.metric_count,
                "Review Needed": healthSummary.review_count,
              }
            })}
            className="p-6 border-l-4 border-info-light dark:border-info-dark hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-all text-left"
          >
            <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
              <span>Stable Status</span>
              <InfoTooltip
                title="Stable Status"
                definition="Metrics showing consistent performance with minimal variation month over month. These metrics maintain steady patterns with no significant changes—neither growing nor declining noticeably."
                example="If Website session_duration stays between 2.8-3.2 minutes every month for 6 months straight, it's stable. No red flags, but also no growth signal."
                polarity="Neutral (context-dependent)"
                size="sm"
              />
            </div>
            <div className="font-headline text-5xl mb-1 text-ink dark:text-stone-100">
              {healthSummary.stable_count}
            </div>
            <div className="h-1 bg-info-light dark:bg-info-dark"></div>
          </button>
        </div>
      </div>

      {/* Health Distribution */}
      <section className="mb-12">
        <h2 className="font-headline text-3xl mb-6 pb-2 border-b-2 border-ink dark:border-stone-700">
          Health Distribution
        </h2>

        <div className="border border-ink dark:border-stone-700 p-8 bg-stone-50 dark:bg-stone-800">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={80}
                outerRadius={120}
                paddingAngle={0}
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[entry.color as keyof typeof COLORS]} />
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

        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-px bg-ink dark:bg-stone-700 border border-ink dark:border-stone-700">
          <button
            onClick={() => showMetricDetail({
              name: "Good Health Percentage",
              value: `${healthPercentage.toFixed(1)}%`,
              category: "Good Health",
              explanation: `${healthPercentage.toFixed(1)}% of your tracked metrics are in good health. This represents ${healthSummary.good_count} out of ${healthSummary.metric_count} total metrics performing within their normal expected range.`,
              businessContext: "A higher good health percentage indicates overall digital ecosystem stability. Industry benchmarks suggest aiming for 60-70% of metrics in good health, with the remainder split between areas for review and stable baseline metrics.",
              additionalInfo: {
                "Count": healthSummary.good_count,
                "Total": healthSummary.metric_count,
                "Month": healthSummary.latest_month,
              }
            })}
            className="bg-paper dark:bg-stone-900 p-6 hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-all text-left"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400">
                <span>Good Health</span>
                <InfoTooltip
                  title="Good Health"
                  definition="Metrics performing within expected range."
                  size="sm"
                />
              </div>
              <div className="font-mono text-2xl font-bold text-good-light dark:text-good-dark">
                {healthPercentage.toFixed(0)}%
              </div>
            </div>
            <div className="h-3 border border-good-light dark:border-good-dark">
              <div
                className="h-full bg-good-light dark:bg-good-dark"
                style={{ width: `${healthPercentage}%` }}
              />
            </div>
            <p className="font-body text-sm mt-3 text-stone-600 dark:text-stone-400">
              {healthSummary.good_count} metrics performing within target range
            </p>
          </button>

          <button
            onClick={() => showMetricDetail({
              name: "Review Needed Percentage",
              value: `${reviewPercentage.toFixed(1)}%`,
              category: "Review Needed",
              explanation: `${reviewPercentage.toFixed(1)}% of your metrics need review. These ${healthSummary.review_count} metrics are deviating from expected patterns and have been flagged for investigation.`,
              businessContext: "Metrics needing review are automatically prioritized based on severity, persistence, peer context, and commercial impact. Check the Priority Board to see which ones require immediate attention versus monitoring.",
              additionalInfo: {
                "Count": healthSummary.review_count,
                "Critical": "Check Priority Board",
                "Month": healthSummary.latest_month,
              }
            })}
            className="bg-paper dark:bg-stone-900 p-6 hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-all text-left"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400">
                <span>Review Needed</span>
                <InfoTooltip
                  title="Review Needed"
                  definition="Metrics showing deviations that merit investigation."
                  size="sm"
                />
              </div>
              <div className="font-mono text-2xl font-bold text-warning-light dark:text-warning-dark">
                {reviewPercentage.toFixed(0)}%
              </div>
            </div>
            <div className="h-3 border border-warning-light dark:border-warning-dark">
              <div
                className="h-full bg-warning-light dark:bg-warning-dark"
                style={{ width: `${reviewPercentage}%` }}
              />
            </div>
            <p className="font-body text-sm mt-3 text-stone-600 dark:text-stone-400">
              {healthSummary.review_count} metrics deviating from expected performance
            </p>
          </button>

          <button
            onClick={() => showMetricDetail({
              name: "Stable Percentage",
              value: `${stablePercentage.toFixed(1)}%`,
              category: "Stable Status",
              explanation: `${stablePercentage.toFixed(1)}% of metrics are stable, showing ${healthSummary.stable_count} metrics with consistent, predictable patterns month over month.`,
              businessContext: "Stable metrics represent your baseline performance. While stability is good for operational predictability, consider whether these areas present growth opportunities or if consistent performance aligns with strategic goals.",
              additionalInfo: {
                "Count": healthSummary.stable_count,
                "Total": healthSummary.metric_count,
                "Month": healthSummary.latest_month,
              }
            })}
            className="bg-paper dark:bg-stone-900 p-6 hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-all text-left"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400">
                <span>Stable Status</span>
                <InfoTooltip
                  title="Stable Status"
                  definition="Metrics showing consistent performance with minimal variation."
                  size="sm"
                />
              </div>
              <div className="font-mono text-2xl font-bold text-info-light dark:text-info-dark">
                {stablePercentage.toFixed(0)}%
              </div>
            </div>
            <div className="h-3 border border-info-light dark:border-info-dark">
              <div
                className="h-full bg-info-light dark:bg-info-dark"
                style={{ width: `${stablePercentage}%` }}
              />
            </div>
            <p className="font-body text-sm mt-3 text-stone-600 dark:text-stone-400">
              {healthSummary.stable_count} metrics showing no significant change
            </p>
          </button>
        </div>
      </section>

      {/* Deviation Indicator - Now Clickable */}
      {healthSummary.avg_abs_deviation !== null && (
        <section>
          <div className="flex items-center gap-3 mb-6 pb-2 border-b-2 border-ink dark:border-stone-700">
            <h2 className="font-headline text-3xl">
              Overall Deviation Index
            </h2>
            <InfoTooltip
              title="Ecosystem Deviation Index"
              definition="Measures how far the current month's metrics deviate from their expected seasonal patterns, averaged across all tracked metrics. Lower deviation = more predictable, stable performance. Higher deviation = significant changes happening across multiple areas."
              formula="Average of |actual_value - seasonal_baseline| / seasonal_baseline across all metrics"
              example="If avg deviation is 0.250, it means metrics are on average 25% away from their seasonal baseline. A value of 0.050 (5%) indicates very stable performance matching expectations."
              polarity="Lower is more stable (closer to zero is better)"
              size="md"
            />
          </div>

          <button
            onClick={() => showMetricDetail({
              name: "Average Absolute Deviation",
              value: healthSummary.avg_abs_deviation.toFixed(3),
              category: "System Metric",
              explanation: `The average absolute deviation is ${healthSummary.avg_abs_deviation.toFixed(3)}. This number measures how far the current month's metrics deviate from their expected seasonal patterns, averaged across all ${healthSummary.metric_count} tracked metrics.`,
              businessContext: "Lower deviation indicates more predictable, stable performance across your digital ecosystem. Higher deviation suggests significant changes happening across multiple areas. This metric helps you quickly assess overall system stability. Values closer to zero indicate performance matching seasonal expectations.",
              additionalInfo: {
                "Current Value": healthSummary.avg_abs_deviation.toFixed(3),
                "Metrics Tracked": healthSummary.metric_count,
                "Interpretation": "Lower is more stable",
                "Month": healthSummary.latest_month,
              }
            })}
            className="w-full border-2 border-ink dark:border-stone-700 p-12 text-center hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-all"
          >
            <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-4">
              Average Deviation from Seasonal Baseline
            </div>
            <div className="font-headline text-7xl md:text-9xl mb-4 text-warning-light dark:text-warning-dark">
              {healthSummary.avg_abs_deviation.toFixed(3)}
            </div>
            <p className="font-body text-base mt-6 text-stone-600 dark:text-stone-400 max-w-2xl mx-auto">
              Click to learn what this metric means and why it matters for your business.
            </p>
          </button>
        </section>
      )}

      {/* Screen Guide */}
      <div data-screen-guide className="mt-12">
        <ScreenGuide
          screenName="Command Center"
          sections={[
            {
              title: "What is the Command Center?",
              content: "The Command Center is ClubOS's real-time health monitor for all 52 commercial metrics across 4 platforms (Website, Social, eCommerce, Ticketing). Each month, the system automatically categorizes every metric as 'Good Health' (performing within expected range), 'Review Needed' (deviating from seasonal patterns), or 'Stable' (consistent with minimal variation). This gives you an instant overview of ecosystem stability."
            },
            {
              title: "What do the health statuses mean?",
              content: "Good Health (green) means metrics are tracking as expected—no action needed. Review Needed (orange) means metrics have moved outside their normal seasonal range and merit investigation—not all are problems, some may be opportunities. Stable (blue) means metrics show consistent performance month over month with no significant changes. The percentages show the distribution: aim for 60-70% Good Health for overall stability."
            },
            {
              title: "What is the Ecosystem Deviation Index?",
              content: "The Deviation Index measures how far the current month's metrics deviate from their expected seasonal patterns, averaged across all metrics. Lower values (closer to zero) indicate stable, predictable performance matching seasonal expectations. Higher values suggest significant changes happening across multiple areas. For example, 0.250 means metrics are on average 25% away from their seasonal baseline, while 0.050 (5%) indicates very stable performance."
            },
            {
              title: "How does this connect to the Priority Board?",
              content: "The Command Center shows the big picture—overall ecosystem health. The Priority Board drills down to specific issues requiring immediate attention. Metrics flagged as 'Review Needed' here are automatically evaluated for the Priority Board based on severity, persistence, peer gap, commercial impact, and supporting evidence. Check the Priority Board to see which Review Needed metrics are most urgent."
            }
          ]}
        />
      </div>

      {/* Metric Detail Modal */}
      {selectedMetric && (
        <MetricDetailModal
          isOpen={!!selectedMetric}
          onClose={closeMetricDetail}
          metricName={selectedMetric.name}
          metricValue={selectedMetric.value}
          metricCategory={selectedMetric.category}
          explanation={selectedMetric.explanation}
          businessContext={selectedMetric.businessContext}
          additionalInfo={selectedMetric.additionalInfo}
        />
      )}
    </section>
  );
}
