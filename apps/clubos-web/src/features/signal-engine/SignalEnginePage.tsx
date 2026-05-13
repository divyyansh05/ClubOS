import { useEffect, useState } from "react";
import { getSignals } from "../../lib/api";
import type { SignalResponse, SignalItem } from "../../types/clubos";
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
  trendData?: Array<{ month: string; value: number }>;
  additionalInfo?: Record<string, string | number>;
}

export function SignalEnginePage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [signals, setSignals] = useState<SignalResponse | null>(null);
  const [selectedSignal, setSelectedSignal] = useState<SignalItem | null>(null);
  const [selectedMetricDetail, setSelectedMetricDetail] = useState<MetricDetail | null>(null);

  function showMetricDetail(detail: MetricDetail) {
    setSelectedMetricDetail(detail);
  }

  function closeMetricDetail() {
    setSelectedMetricDetail(null);
  }

  useEffect(() => {
    async function loadSignals() {
      try {
        setLoading(true);
        const data = await getSignals();
        setSignals(data);
        setError(null);
        if (data.items.length > 0) {
          setSelectedSignal(data.items[0]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load signals");
      } finally {
        setLoading(false);
      }
    }
    loadSignals();
  }, []);

  if (loading) {
    return (
      <section className="max-w-screen-xl mx-auto px-6 py-12">
        <h2 className="font-headline text-3xl mb-4">Commercial Signal Engine</h2>
        <div className="p-8 border border-ink dark:border-stone-700 bg-stone-50 dark:bg-stone-800 font-body">
          Loading validated signals...
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="max-w-screen-xl mx-auto px-6 py-12">
        <h2 className="font-headline text-3xl mb-4">Commercial Signal Engine</h2>
        <div className="p-8 border border-ink dark:border-stone-700 bg-stone-50 dark:bg-stone-800 text-critical-light dark:text-critical-dark font-body">
          <strong>Error:</strong> {error}
        </div>
      </section>
    );
  }

  if (!signals || signals.items.length === 0) {
    return (
      <section className="max-w-screen-xl mx-auto px-6 py-12">
        <h2 className="font-headline text-3xl mb-4">Commercial Signal Engine</h2>
        <p className="p-8 border border-ink dark:border-stone-700 bg-stone-50 dark:bg-stone-800 font-body">
          No validated signals found.
        </p>
      </section>
    );
  }

  const activeSignals = signals.items.filter((s) => s.validation_status === "active");
  const avgLag = signals.items.reduce((sum, s) => sum + s.lag_months, 0) / signals.items.length;
  const avgStrength = signals.items.reduce((sum, s) => sum + s.strength_score, 0) / signals.items.length;
  const minLag = Math.min(...signals.items.map(s => s.lag_months));
  const maxLag = Math.max(...signals.items.map(s => s.lag_months));
  const lagDisplay = minLag === maxLag ? `${minLag} month${minLag > 1 ? 's' : ''}` : `${minLag}–${maxLag} months`;

  // Additional summary calculations for FIX 6
  const positiveSignals = signals.items.filter((s) => s.relationship_direction === "positive").length;
  const negativeSignals = signals.items.filter((s) => s.relationship_direction === "negative").length;
  const firingSignals = signals.items.filter((s) => s.current_status === "firing_positive" || s.current_status === "firing_negative").length;
  const monitoringSignals = signals.items.filter((s) => s.current_status === "neutral" || s.current_status === "unknown").length;
  const minStrength = Math.min(...signals.items.map(s => s.strength_score));
  const maxStrength = Math.max(...signals.items.map(s => s.strength_score));

  // Helper to get border color for signal
  const getSignalBorderColor = (signal: SignalItem, index: number) => {
    if (signal.validation_status === "active") {
      const colors = [
        "border-good-light dark:border-good-dark",
        "border-info-light dark:border-info-dark",
        "border-accent-light dark:border-accent-dark",
        "border-warning-light dark:border-warning-dark",
      ];
      return colors[index % colors.length];
    }
    return "border-stone-400 dark:border-stone-600";
  };

  const getSignalTextColor = (signal: SignalItem, index: number) => {
    if (signal.validation_status === "active") {
      const colors = [
        "text-good-light dark:text-good-dark",
        "text-info-light dark:text-info-dark",
        "text-accent-light dark:text-accent-dark",
        "text-warning-light dark:text-warning-dark",
      ];
      return colors[index % colors.length];
    }
    return "text-stone-500 dark:text-stone-400";
  };

  return (
    <section className="max-w-screen-xl mx-auto px-6 py-12">
      {/* Hero */}
      <div className="border-b-4 border-ink dark:border-stone-600 pb-8 mb-12">
        <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-4">
          Leading Indicator Analysis
        </div>
        <h1 className="font-headline text-5xl md:text-7xl lg:text-8xl leading-[0.95] tracking-tight mb-6">
          Commercial<br/>Signal Engine
        </h1>
        <p className="font-body text-lg md:text-xl text-stone-600 dark:text-stone-400 leading-relaxed max-w-2xl">
          Validated leading indicators that predict future performance across commercial channels, helping anticipate trends 1-3 months ahead.
        </p>
        <p className="font-mono text-xs text-stone-500 dark:text-stone-400 mt-4">
          Last validated: {signals.latest_validated_month ? formatMonthYear(signals.latest_validated_month) : "N/A"}
        </p>
      </div>

      {/* Summary Cards */}
      <div className="mb-12 border border-ink dark:border-stone-700">
        <div className="grid grid-cols-2 md:grid-cols-4">
          <button
            onClick={() => showMetricDetail({
              name: "Validated Signals",
              value: signals.items.length,
              category: "Leading Indicators",
              explanation: `We have identified and validated ${signals.items.length} leading indicator relationships across your commercial channels. These are metrics that reliably predict future performance 1-3 months in advance.`,
              businessContext: `Having ${signals.items.length} validated signals means you can anticipate changes in key business outcomes before they happen. This early warning system allows proactive decision-making rather than reactive responses. Each signal has been statistically validated to ensure reliability.`,
              additionalInfo: {
                "Total Validated": signals.items.length,
                "Active Signals": activeSignals.length,
                "Last Validated": signals.latest_validated_month || "N/A",
              }
            })}
            className="p-6 border-l-4 border-good-light dark:border-good-dark border-r border-b md:border-b-0 border-ink dark:border-stone-700 hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-colors text-left"
          >
            <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
              <span>Validated Signals</span>
              <InfoTooltip
                title="Validated Signals"
                definition="Leading indicator relationships that have been statistically validated to reliably predict future performance. Each signal passed rigorous validation: Pearson correlation > 0.60, business prior gate (causal logic check), and 103 months of historical data testing."
                example="If Website unique_visitors reliably predicts eCommerce net_sales 1 month later with 70% correlation, that's a validated signal."
                size="sm"
              />
            </div>
            <div className="font-headline text-5xl mb-1 text-ink dark:text-stone-100">
              {signals.items.length}
            </div>
            <div className="h-1 bg-good-light dark:bg-good-dark mb-2"></div>
            <div className="font-mono text-xs text-stone-600 dark:text-stone-400">
              {positiveSignals} positive  ·  {negativeSignals} negative
            </div>
          </button>

          <button
            onClick={() => showMetricDetail({
              name: "Active Status",
              value: activeSignals.length,
              category: "Signal Health",
              explanation: `${activeSignals.length} out of ${signals.items.length} validated signals are currently active and being monitored. A signal is marked "active" when it continues to pass validation checks in recent months.`,
              businessContext: `Active signals are the ones you can rely on right now for forecasting. If a signal becomes inactive, it means the historical relationship has changed or weakened, so we stop using it to avoid misleading predictions. Having ${activeSignals.length} active signals gives you real-time predictive power across multiple channels.`,
              additionalInfo: {
                "Active": activeSignals.length,
                "Total Validated": signals.items.length,
                "Active Rate": `${((activeSignals.length / signals.items.length) * 100).toFixed(0)}%`,
              }
            })}
            className="p-6 border-l-4 border-info-light dark:border-info-dark border-b md:border-b-0 md:border-r border-ink dark:border-stone-700 hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-colors text-left"
          >
            <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
              <span>Active Status</span>
              <InfoTooltip
                title="Active Status"
                definition="A signal is 'active' when it continues to pass validation checks in recent months. Active signals are reliable for current forecasting. If a signal's historical relationship weakens or changes, it becomes inactive to prevent misleading predictions."
                example="If a signal maintained 70% correlation for 100 months but dropped to 45% in the last 6 months, it becomes inactive until the relationship re-stabilizes."
                size="sm"
              />
            </div>
            <div className="font-headline text-5xl mb-1 text-ink dark:text-stone-100">
              {activeSignals.length}
            </div>
            <div className="h-1 bg-info-light dark:bg-info-dark mb-2"></div>
            <div className="font-mono text-xs text-stone-600 dark:text-stone-400">
              {firingSignals} firing now  ·  {monitoringSignals} monitoring
            </div>
          </button>

          <button
            onClick={() => showMetricDetail({
              name: "Average Lead Time",
              value: lagDisplay,
              category: "Predictive Window",
              explanation: `On average, our signals predict future outcomes ${avgLag.toFixed(1)} months in advance. This means when you see a change in a source metric (like website traffic), you can expect to see a corresponding change in the target metric (like sales) about ${avgLag.toFixed(0)} months later.`,
              businessContext: `The ${lagDisplay} lead time is your planning window. It tells you how far ahead you can anticipate changes in key outcomes. This advance notice gives you time to prepare, adjust strategies, or capitalize on opportunities before they fully materialize. Longer lead times mean more time to react; shorter ones mean faster feedback loops.`,
              additionalInfo: {
                "Avg Lead Time": `${avgLag.toFixed(1)} months`,
                "Min Lag": `${minLag} months`,
                "Max Lag": `${maxLag} months`,
              }
            })}
            className="p-6 border-l-4 border-warning-light dark:border-warning-dark border-r border-ink dark:border-stone-700 hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-colors text-left"
          >
            <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
              Avg Lead Time
            </div>
            <div className="font-headline text-5xl mb-1 text-ink dark:text-stone-100">
              {minLag === maxLag ? avgLag.toFixed(0) : `${minLag}–${maxLag}`}
            </div>
            <div className="h-1 bg-warning-light dark:bg-warning-dark mb-2"></div>
            <div className="font-mono text-xs text-stone-600 dark:text-stone-400">
              Earliest warning: {minLag} month{minLag > 1 ? 's' : ''}
            </div>
          </button>

          <button
            onClick={() => showMetricDetail({
              name: "Average Strength",
              value: `${(avgStrength * 100).toFixed(0)}%`,
              category: "Signal Reliability",
              explanation: `Signal strength measures how reliably a source metric predicts the target metric. An average strength of ${(avgStrength * 100).toFixed(0)}% means our signals have a ${(avgStrength * 100).toFixed(0)}% correlation with their predicted outcomes, which is considered strong for business metrics.`,
              businessContext: `Higher strength means more confidence in predictions. A ${(avgStrength * 100).toFixed(0)}% average strength indicates your leading indicators are highly reliable predictors. This means when you see movement in source metrics, you can trust that the predicted changes will likely occur. Lower strength would mean more uncertainty and less actionable signals.`,
              additionalInfo: {
                "Avg Strength": `${(avgStrength * 100).toFixed(1)}%`,
                "Strongest Signal": `${(Math.max(...signals.items.map(s => s.strength_score)) * 100).toFixed(0)}%`,
                "Weakest Signal": `${(Math.min(...signals.items.map(s => s.strength_score)) * 100).toFixed(0)}%`,
              }
            })}
            className="p-6 border-l-4 border-accent-light dark:border-accent-dark hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-colors text-left"
          >
            <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
              Avg Strength
            </div>
            <div className="font-headline text-5xl mb-1 text-ink dark:text-stone-100">
              {(avgStrength * 100).toFixed(0)}%
            </div>
            {/* Mini gauge */}
            <div className="relative h-1.5 bg-stone-200 dark:bg-stone-700 rounded mb-2">
              <div className="absolute left-[60%] top-0 bottom-0 w-px bg-stone-400 dark:bg-stone-600"></div>
              <div
                className="absolute top-0 bottom-0 left-[60%] bg-accent-light dark:bg-accent-dark"
                style={{ width: `${Math.max(0, (avgStrength - 0.60) / 0.40) * 40}%` }}
              ></div>
            </div>
            <div className="font-mono text-xs text-stone-600 dark:text-stone-400">
              Range: {(minStrength * 100).toFixed(0)}%–{(maxStrength * 100).toFixed(0)}%  ·  Threshold: 60%
            </div>
          </button>
        </div>
      </div>

      {/* Signal Cards */}
      <div className="grid grid-cols-1 gap-6 mb-12">
        {signals.items.map((signal, index) => {
          const borderColor = getSignalBorderColor(signal, index);
          const textColor = getSignalTextColor(signal, index);
          const isActive = signal.validation_status === "active";

          return (
            <article
              key={signal.signal_id}
              className={`border-2 ${borderColor} p-8 hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-all ${selectedSignal?.signal_id === signal.signal_id ? 'bg-stone-100 dark:bg-stone-800' : ''}`}
              onClick={() => setSelectedSignal(signal)}
            >
              {/* Status Banner */}
              {signal.current_status && (
                <div className={`mb-4 p-3 border-l-4 ${
                  signal.current_status === 'firing_positive'
                    ? 'border-good-light dark:border-good-dark bg-good-light/10 dark:bg-good-dark/10'
                    : signal.current_status === 'firing_negative'
                    ? 'border-critical-light dark:border-critical-dark bg-critical-light/10 dark:bg-critical-dark/10'
                    : 'border-stone-400 dark:border-stone-600 bg-stone-100 dark:bg-stone-800'
                }`}>
                  <div className={`font-mono text-xs font-semibold ${
                    signal.current_status === 'firing_positive'
                      ? 'text-good-light dark:text-good-dark'
                      : signal.current_status === 'firing_negative'
                      ? 'text-critical-light dark:text-critical-dark'
                      : 'text-stone-600 dark:text-stone-400'
                  }`}>
                    {signal.current_status === 'firing_positive' && `▲ SIGNAL ACTIVE — ${signal.source_metric} rising → ${signal.target_metric} expected to rise in ${signal.lag_months} month${signal.lag_months > 1 ? 's' : ''}`}
                    {signal.current_status === 'firing_negative' && `▼ SIGNAL ACTIVE — ${signal.source_metric} declining → ${signal.target_metric} expected to decline in ${signal.lag_months} month${signal.lag_months > 1 ? 's' : ''}`}
                    {signal.current_status === 'neutral' && `— SIGNAL MONITORING — ${signal.source_metric} stable · No directional signal this month`}
                    {signal.current_status === 'unknown' && `— SIGNAL STATUS UNKNOWN — Source metric data unavailable`}
                  </div>
                </div>
              )}

              <div className="flex items-start justify-between mb-6 flex-wrap gap-4">
                <div className="flex-1">
                  <h3 className="font-headline text-3xl mb-2">
                    {signal.source_metric} → {signal.target_metric}
                  </h3>
                  <div className="font-mono text-sm text-stone-600 dark:text-stone-400">
                    {signal.lag_months}-Month Early Signal  ·  {signal.source_asset} → {signal.target_asset}
                  </div>
                </div>
                <div className="text-right flex flex-col items-end gap-2">
                  <span className="px-3 py-1 bg-stone-200 dark:bg-stone-700 border border-stone-300 dark:border-stone-600 font-mono text-xs font-semibold uppercase tracking-widest text-ink dark:text-stone-100">
                    {signal.lag_months} MO LAG
                  </span>
                  <div>
                    <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-1">
                      Strength
                    </div>
                    <div className={`font-mono text-4xl font-bold ${textColor}`}>
                      {(signal.strength_score * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              </div>

              {/* Flow Diagram */}
              <div className="flex items-center gap-6 mb-6 p-6 border border-stone-300 dark:border-stone-700 bg-stone-50 dark:bg-stone-800 flex-wrap justify-center">
                {/* Source Panel */}
                <div className="flex-1 min-w-[200px] p-4 border border-stone-300 dark:border-stone-700 bg-white dark:bg-stone-900">
                  <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">Source</div>
                  <div className="flex items-center gap-2 mb-1">
                    <div className="font-semibold text-base">{signal.source_metric}</div>
                    <InfoTooltip metricName={signal.source_metric} size="sm" />
                  </div>
                  <div className="text-xs text-stone-600 dark:text-stone-400 mb-3">{signal.source_asset}</div>

                  {signal.source_current_value !== null && signal.source_current_value !== undefined ? (
                    <>
                      <div className="font-mono text-sm text-ink dark:text-stone-100 mb-2">
                        NOW: {signal.source_current_value.toLocaleString()}
                      </div>
                      {signal.source_trend_pct_change !== null && signal.source_trend_pct_change !== undefined && (
                        <div className={`font-mono text-xs font-semibold ${
                          signal.source_trend_pct_change > 0
                            ? 'text-good-light dark:text-good-dark'
                            : signal.source_trend_pct_change < 0
                            ? 'text-critical-light dark:text-critical-dark'
                            : 'text-stone-500 dark:text-stone-400'
                        }`}>
                          {signal.source_trend_pct_change > 0 ? '↑' : signal.source_trend_pct_change < 0 ? '↓' : '→'} {Math.abs(signal.source_trend_pct_change).toFixed(1)}%
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="font-mono text-sm text-stone-400 dark:text-stone-600">—</div>
                  )}
                </div>

                {/* Arrow Connector */}
                <div className="flex-shrink-0 flex flex-col items-center">
                  <div className={`font-mono text-xs uppercase tracking-widest mb-2 ${
                    signal.current_status === 'firing_positive'
                      ? 'text-good-light dark:text-good-dark'
                      : signal.current_status === 'firing_negative'
                      ? 'text-critical-light dark:text-critical-dark'
                      : 'text-stone-500 dark:text-stone-400'
                  }`}>
                    ── {signal.lag_months} month lag ──▶
                  </div>
                </div>

                {/* Target Panel */}
                <div className="flex-1 min-w-[200px] p-4 border border-stone-300 dark:border-stone-700 bg-white dark:bg-stone-900">
                  <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">Target</div>
                  <div className="flex items-center gap-2 mb-1">
                    <div className="font-semibold text-base">{signal.target_metric}</div>
                    <InfoTooltip metricName={signal.target_metric} size="sm" />
                  </div>
                  <div className="text-xs text-stone-600 dark:text-stone-400 mb-3">{signal.target_asset}</div>

                  {signal.target_current_value !== null && signal.target_current_value !== undefined ? (
                    <>
                      <div className="font-mono text-sm text-ink dark:text-stone-100 mb-2">
                        NOW: {signal.target_current_value.toLocaleString()}
                      </div>
                      {signal.target_health_status && (
                        <span className={`px-2 py-1 rounded font-mono text-xs font-semibold uppercase ${
                          signal.target_health_status === 'good'
                            ? 'bg-good-light/20 dark:bg-good-dark/20 text-good-light dark:text-good-dark'
                            : signal.target_health_status === 'review'
                            ? 'bg-critical-light/20 dark:bg-critical-dark/20 text-critical-light dark:text-critical-dark'
                            : 'bg-stone-200 dark:bg-stone-700 text-stone-600 dark:text-stone-400'
                        }`}>
                          {signal.target_health_status}
                        </span>
                      )}
                    </>
                  ) : (
                    <div className="font-mono text-sm text-stone-400 dark:text-stone-600">—</div>
                  )}
                </div>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    showMetricDetail({
                      name: `Signal Strength: ${signal.source_metric} → ${signal.target_metric}`,
                      value: `${(signal.strength_score * 100).toFixed(0)}%`,
                      category: "Statistical Correlation",
                      explanation: `This signal has a strength score of ${(signal.strength_score * 100).toFixed(0)}%, which measures how reliably changes in ${signal.source_metric} predict changes in ${signal.target_metric}. A score above 60% is considered strong; above 80% is very strong.`,
                      businessContext: `The ${(signal.strength_score * 100).toFixed(0)}% strength means when you see ${signal.source_metric} change, you can be ${(signal.strength_score * 100).toFixed(0)}% confident that ${signal.target_metric} will change in the same direction ${signal.lag_months} months later. This reliability lets you plan ahead with confidence rather than guessing.`,
                      additionalInfo: {
                        "Strength Score": `${(signal.strength_score * 100).toFixed(1)}%`,
                        "Source Metric": signal.source_metric,
                        "Target Metric": signal.target_metric,
                        "Validation Status": signal.validation_status,
                      }
                    });
                  }}
                  className="p-3 border border-stone-300 dark:border-stone-700 hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                    <span>Strength</span>
                    <InfoTooltip
                      title="Predictive Strength"
                      definition="Measures how reliably the source metric predicts the target metric, expressed as Pearson correlation coefficient. Higher strength = more confidence in predictions."
                      formula="Pearson r correlation between source (t) and target (t+lag)"
                      example="A 70% strength means when the source metric moves 10%, the target metric typically moves 7% in the predicted direction after the lag period."
                      polarity="Higher is better"
                      size="sm"
                    />
                  </div>
                  <div className="font-mono text-lg font-bold text-ink dark:text-stone-100 mb-2">{(signal.strength_score * 100).toFixed(0)}%</div>

                  {/* Strength Gauge */}
                  <div className="relative h-3 bg-stone-200 dark:bg-stone-700 rounded overflow-hidden mb-1">
                    {/* Threshold marker at 60% */}
                    <div className="absolute left-[60%] top-0 bottom-0 w-px bg-stone-400 dark:bg-stone-600 z-10"></div>
                    {/* Fill bar starting from 60% */}
                    <div
                      className={`absolute top-0 bottom-0 left-[60%] ${
                        signal.strength_score > 0.75
                          ? 'bg-good-light dark:bg-good-dark'
                          : 'bg-warning-light dark:bg-warning-dark'
                      }`}
                      style={{ width: `${Math.max(0, (signal.strength_score - 0.60) / 0.40) * 40}%` }}
                    ></div>
                  </div>
                  <div className="flex justify-between font-mono text-[9px] text-stone-500 dark:text-stone-400 mb-1">
                    <span>THRESHOLD 60%</span>
                    <span>MAX 100%</span>
                  </div>
                  <div className="font-mono text-[9px] text-stone-500 dark:text-stone-400">Validated across 103 months</div>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    showMetricDetail({
                      name: `Lag Time: ${signal.source_metric} → ${signal.target_metric}`,
                      value: `${signal.lag_months} months`,
                      category: "Predictive Window",
                      explanation: `This signal has a ${signal.lag_months}-month lag time, meaning changes in ${signal.source_metric} typically appear in ${signal.target_metric} about ${signal.lag_months} months later. This is the time window between cause and effect.`,
                      businessContext: `The ${signal.lag_months}-month lag gives you a ${signal.lag_months}-month head start. When you see ${signal.source_metric} trending up or down, you know you have ${signal.lag_months} months to prepare for the corresponding change in ${signal.target_metric}. This advance notice is invaluable for planning resources, adjusting budgets, or shifting strategies.`,
                      additionalInfo: {
                        "Lag Time": `${signal.lag_months} months`,
                        "Source": `${signal.source_asset} - ${signal.source_metric}`,
                        "Target": `${signal.target_asset} - ${signal.target_metric}`,
                        "Last Validated": signal.last_validated_month,
                      }
                    });
                  }}
                  className="p-3 border border-stone-300 dark:border-stone-700 text-center hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-colors"
                >
                  <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-1">Lag Time</div>
                  <div className="font-mono text-lg font-bold">{signal.lag_months} mo</div>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    showMetricDetail({
                      name: `Relationship Direction: ${signal.source_metric} → ${signal.target_metric}`,
                      value: signal.relationship_direction === 'positive' ? '↑ Positive' : '↓ Negative',
                      category: signal.relationship_direction === 'positive' ? 'Positive Correlation' : 'Negative Correlation',
                      explanation: signal.relationship_direction === 'positive'
                        ? `This is a positive relationship, meaning when ${signal.source_metric} goes up, ${signal.target_metric} typically goes up ${signal.lag_months} months later. When ${signal.source_metric} goes down, ${signal.target_metric} goes down.`
                        : `This is a negative (inverse) relationship, meaning when ${signal.source_metric} goes up, ${signal.target_metric} typically goes down ${signal.lag_months} months later, and vice versa.`,
                      businessContext: signal.relationship_direction === 'positive'
                        ? `A positive relationship means these metrics move together in the same direction. This is common for metrics in a healthy conversion funnel - more top-of-funnel activity leads to more bottom-of-funnel results. You can use ${signal.source_metric} as an early indicator: if it's growing, expect ${signal.target_metric} to grow too.`
                        : `A negative relationship means these metrics move in opposite directions. This can indicate trade-offs or inverse dynamics in your business. Understanding this inverse relationship helps you anticipate counterintuitive outcomes and plan accordingly.`,
                      additionalInfo: {
                        "Direction": signal.relationship_direction,
                        "Strength": `${(signal.strength_score * 100).toFixed(0)}%`,
                        "Lag": `${signal.lag_months} months`,
                      }
                    });
                  }}
                  className="p-3 border border-stone-300 dark:border-stone-700 text-center hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-colors"
                >
                  <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-1">Direction</div>
                  <div className={`font-mono text-lg font-bold ${signal.relationship_direction === 'positive' ? 'text-good-light dark:text-good-dark' : 'text-critical-light dark:text-critical-dark'}`}>
                    {signal.relationship_direction === 'positive' ? '↑ Positive' : '↓ Negative'}
                  </div>
                </button>
              </div>

              {/* Business Interpretation */}
              {selectedSignal?.signal_id === signal.signal_id && (
                <div className="mt-6 p-6 border-t-2 border-stone-300 dark:border-stone-700">
                  <h4 className="font-headline text-xl mb-4">Business Interpretation</h4>
                  <p className="font-body text-base mb-4 text-stone-600 dark:text-stone-400">
                    {signal.business_interpretation}
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                    <div className="p-4 border border-stone-300 dark:border-stone-700 bg-stone-50 dark:bg-stone-800">
                      <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                        Source Asset
                      </div>
                      <div className="font-semibold">{signal.source_asset}</div>
                    </div>
                    <div className="p-4 border border-stone-300 dark:border-stone-700 bg-stone-50 dark:bg-stone-800">
                      <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                        Target Asset
                      </div>
                      <div className="font-semibold">{signal.target_asset}</div>
                    </div>
                  </div>
                  <div className="mt-4 p-4 border border-stone-300 dark:border-stone-700 bg-stone-50 dark:bg-stone-800">
                    <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                      Last Validated
                    </div>
                    <div className="font-semibold">{signal.last_validated_month}</div>
                  </div>

                  {/* Priority Board Connection */}
                  {signal.priority_connection && (
                    <div className="mt-6">
                      <h4 className="font-headline text-xl mb-4">Connection to Current Priorities</h4>
                      <div className={`p-4 border-l-4 ${
                        signal.priority_connection.border_color === 'critical'
                          ? 'border-critical-light dark:border-critical-dark bg-critical-light/10 dark:bg-critical-dark/10'
                          : signal.priority_connection.border_color === 'good'
                          ? 'border-good-light dark:border-good-dark bg-good-light/10 dark:bg-good-dark/10'
                          : 'border-stone-400 dark:border-stone-600 bg-stone-50 dark:bg-stone-800'
                      } border border-stone-300 dark:border-stone-700`}>
                        <p className="font-body text-sm text-stone-700 dark:text-stone-300">
                          {signal.priority_connection.interpretation}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </article>
          );
        })}
      </div>

      {/* Signal Validation Notes */}
      <section className="border-t-2 border-ink dark:border-stone-700 pt-8">
        <h2 className="font-headline text-2xl mb-6">How These Signals Were Validated</h2>

        {/* Validation Table */}
        <div className="border border-ink dark:border-stone-700 mb-6 overflow-x-auto">
          <table className="w-full data-table border-ink dark:border-stone-700 font-mono text-sm border-collapse">
            <thead>
              <tr className="bg-stone-100 dark:bg-stone-800">
                <th className="text-left p-3 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Signal</th>
                <th className="text-center p-3 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Pearson r</th>
                <th className="text-center p-3 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Lag Tested</th>
                <th className="text-center p-3 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Business Prior</th>
                <th className="text-center p-3 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Status</th>
              </tr>
            </thead>
            <tbody>
              {signals.items.map((signal, index) => (
                <tr key={signal.signal_id} className={index % 2 === 0 ? '' : 'bg-stone-50 dark:bg-stone-800/50'}>
                  <td className="p-3 border border-ink dark:border-stone-700">
                    {signal.source_metric} → {signal.target_metric} ({signal.lag_months}mo)
                  </td>
                  <td className="p-3 text-center border border-ink dark:border-stone-700 font-bold">
                    {signal.strength_score.toFixed(2)}
                  </td>
                  <td className="p-3 text-center border border-ink dark:border-stone-700">
                    1, 2, 3 months
                  </td>
                  <td className="p-3 text-center border border-ink dark:border-stone-700 text-good-light dark:text-good-dark">
                    ✓ Passes
                  </td>
                  <td className="p-3 text-center border border-ink dark:border-stone-700 capitalize">
                    {signal.validation_status}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Validation Criteria List */}
        <div className="font-body text-base text-stone-600 dark:text-stone-400 leading-relaxed">
          <p className="mb-4 font-semibold">
            All signals displayed here passed the following validation criteria:
          </p>
          <ul className="list-disc list-inside space-y-2 mb-4">
            <li>Pearson correlation &gt; 0.60 at specified lag (threshold: 0.60)</li>
            <li>Business prior gate: source logically influences target (traffic drives sales ✓ — sales driving traffic ✗ rejected)</li>
            <li>Tested at 1, 2, and 3 month lags — strongest lag selected per signal</li>
            <li>Validated on 103 months of historical data (2017–2026)</li>
          </ul>
          <p className="font-mono text-xs text-stone-500 dark:text-stone-400">
            Only validated signals are included. If a signal fails re-validation, its status changes to inactive.
          </p>
        </div>
      </section>

      {/* Screen Guide */}
      <div data-screen-guide className="mt-12">
        <ScreenGuide
          screenName="Commercial Signal Engine"
          sections={[
            {
              title: "What are commercial signals?",
              content: "Commercial signals are validated leading indicator relationships where one metric (the source) reliably predicts another metric (the target) 1-3 months in advance. For example, if Website unique_visitors predicts eCommerce net_sales 1 month later with 70% correlation, that's a signal. These relationships give you early warning when key outcomes are about to change, allowing proactive decision-making instead of reactive responses."
            },
            {
              title: "How were these validated?",
              content: "Every signal passed rigorous statistical validation: (1) Pearson correlation > 0.60 at the specified lag (60% minimum threshold), (2) Business prior gate — source must logically influence target (traffic drives sales ✓, but sales driving traffic ✗ rejected), (3) Tested at 1, 2, and 3 month lags — strongest lag selected, (4) Validated on 103 months of historical data (2017-2026). Only signals that pass all criteria are shown. If a signal fails re-validation, its status changes to inactive."
            },
            {
              title: "How to use these signals?",
              content: "When a signal status is 'firing' (positive or negative), it means the source metric is moving and the target metric is expected to move in the predicted direction after the lag period. Use this advance notice to prepare: adjust budgets, shift strategies, or allocate resources. If multiple signals point in the same direction, confidence increases. Check the 'Connection to Current Priorities' section in each signal's detail to see if the predicted change relates to existing Priority Board issues—this helps you anticipate compounding risks or opportunities."
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
