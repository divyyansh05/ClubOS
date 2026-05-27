import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getLatestPriorities, getPriorityDetail, fetchEventsNearMetric, fetchSeasonalBaseline } from "../../lib/api";
import type { PriorityCard, PriorityDetail } from "../../types/clubos";
import type { EventSchema } from "../../types/events";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, BarChart, Bar, Cell, ReferenceArea } from "recharts";
import { ConversionVolumePanel } from "../../components/ui/ConversionVolumePanel";
import { InfoTooltip } from "../../components/ui/InfoTooltip";
import { ChartTooltip } from "../../components/ui/ChartTooltip";
import { WelcomeBanner } from "../../components/ui/WelcomeBanner";
import { ScreenGuide } from "../../components/ui/ScreenGuide";
import { ScoreComponentBar } from "../../components/ui/ScoreComponentBar";
import { getMetricDef, getMetricUnit, getPolaritySymbol } from "../../lib/metricDefinitions";
import { formatMonthYear } from "../../lib/dateFormat";

const SCORING_WEIGHTS = {
  severity: 0.30,
  persistence: 0.25,
  peer_gap: 0.20,
  commercial: 0.15,
  evidence: 0.10
};

export function PriorityBoardPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [latestMonth, setLatestMonth] = useState<string>("");
  const [priorities, setPriorities] = useState<PriorityCard[]>([]);
  const [filteredPriorities, setFilteredPriorities] = useState<PriorityCard[]>([]);
  const [selectedDetail, setSelectedDetail] = useState<PriorityDetail | null>(null);
  const [socialEvidenceTab, setSocialEvidenceTab] = useState<"trend" | "timing" | "format">("trend"); // V1.7 — Tabs for social evidence modal
  const [detailLoading, setDetailLoading] = useState(false);
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const [nearbyEvents, setNearbyEvents] = useState<EventSchema[]>([]);
  const [seasonalBaseline, setSeasonalBaseline] = useState<any>(null);

  useEffect(() => {
    async function loadPriorities() {
      try {
        setLoading(true);
        const data = await getLatestPriorities();
        setLatestMonth(data.latest_month);
        setPriorities(data.items);
        setFilteredPriorities(data.items);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load priorities");
      } finally {
        setLoading(false);
      }
    }
    loadPriorities();
  }, []);

  function filterByCategory(category: string) {
    // Toggle behavior: if clicking active filter, return to "all"
    if (activeFilter === category && category !== "all") {
      setActiveFilter("all");
      setFilteredPriorities(priorities);
      return;
    }

    setActiveFilter(category);
    if (category === "all") {
      setFilteredPriorities(priorities);
    } else {
      // Use same matching logic as badge counts to ensure consistency
      setFilteredPriorities(
        priorities.filter((p) => {
          const cat = p.category.toLowerCase();

          if (category === "critical") {
            return cat.includes('critical') || cat.includes('conversion') || cat.includes('weakness');
          } else if (category === "opportunity") {
            return cat.includes('opportunity');
          } else if (category === "benchmark") {
            return cat.includes('benchmark');
          } else {
            // Fallback to simple string match for any other categories
            return cat.includes(category.toLowerCase());
          }
        })
      );
    }
  }

  async function openDetail(priorityId: string) {
    try {
      setDetailLoading(true);
      const detail = await getPriorityDetail(priorityId);
      setSelectedDetail(detail);

      // Fetch nearby events for this metric
      try {
        const eventsData = await fetchEventsNearMetric(detail.asset_name, detail.primary_metric, detail.month);
        setNearbyEvents(eventsData.items);
      } catch (eventErr) {
        console.error("Failed to load events:", eventErr);
        setNearbyEvents([]);
      }

      // Fetch seasonal baseline for this metric (V1.5.3)
      try {
        const seasonalData = await fetchSeasonalBaseline(detail.asset_name, detail.primary_metric);
        setSeasonalBaseline(seasonalData.baseline);
      } catch (seasonalErr) {
        console.error("Failed to load seasonal baseline:", seasonalErr);
        setSeasonalBaseline(null);
      }
    } catch (err) {
      console.error("Failed to load priority detail:", err);
    } finally {
      setDetailLoading(false);
    }
  }

  function closeDetail() {
    setSelectedDetail(null);
  }

  function openAnalyticsDashboard() {
    if (selectedDetail) {
      // Navigate to Command Center to show ecosystem health
      navigate('/command-center');
      closeDetail();
    }
  }

  function getColorForCategory(category: string): string {
    if (category.toLowerCase().includes('critical')) return 'critical';
    if (category.toLowerCase().includes('opportunity')) return 'good';
    if (category.toLowerCase().includes('benchmark')) return 'info';
    if (category.toLowerCase().includes('warning')) return 'warning';
    // V1.8.5 — Social priorities use purple/accent color (all social categories)
    if (category.toLowerCase().includes('social')) return 'accent';
    return 'accent';
  }

  function getColorClasses(colorType: string) {
    const colors = {
      critical: {
        border: 'border-critical-light dark:border-critical-dark',
        bg: 'bg-critical-light dark:bg-critical-dark',
        text: 'text-critical-light dark:text-critical-dark',
        bar: 'bg-critical-light dark:bg-critical-dark',
      },
      warning: {
        border: 'border-warning-light dark:border-warning-dark',
        bg: 'bg-warning-light dark:bg-warning-dark',
        text: 'text-warning-light dark:text-warning-dark',
        bar: 'bg-warning-light dark:bg-warning-dark',
      },
      good: {
        border: 'border-good-light dark:border-good-dark',
        bg: 'bg-good-light dark:bg-good-dark',
        text: 'text-good-light dark:text-good-dark',
        bar: 'bg-good-light dark:bg-good-dark',
      },
      info: {
        border: 'border-info-light dark:border-info-dark',
        bg: 'bg-info-light dark:bg-info-dark',
        text: 'text-info-light dark:text-info-dark',
        bar: 'bg-info-light dark:bg-info-dark',
      },
      accent: {
        border: 'border-accent-light dark:border-accent-dark',
        bg: 'bg-accent-light dark:bg-accent-dark',
        text: 'text-accent-light dark:text-accent-dark',
        bar: 'bg-accent-light dark:bg-accent-dark',
      },
    };
    return colors[colorType as keyof typeof colors] || colors.accent;
  }

  function formatAssetName(assetName: string): string {
    // V1.8.5 — Format asset names for display badges
    const assetMap: Record<string, string> = {
      'ecommerce': 'ECOMMERCE',
      'main_website': 'MAIN WEBSITE',
      'streaming': 'STREAMING',
      'fan_app': 'FAN APP',
      'social_media': 'SOCIAL',
    };
    return assetMap[assetName] || assetName.toUpperCase();
  }

  if (loading) {
    return (
      <div className="max-w-screen-xl mx-auto px-6 py-12">
        <div className="text-center">
          <div className="font-mono text-sm uppercase tracking-widest text-stone-500 dark:text-stone-400">
            Loading latest priorities...
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-screen-xl mx-auto px-6 py-12">
        <div className="text-center">
          <h2 className="font-headline text-3xl mb-4">Error Loading Priorities</h2>
          <p className="text-critical-light dark:text-critical-dark">{error}</p>
        </div>
      </div>
    );
  }

  // Count by category
  const criticalCount = priorities.filter((p) =>
    p.category.toLowerCase().includes('critical') ||
    p.category.toLowerCase().includes('conversion') ||
    p.category.toLowerCase().includes('weakness')
  ).length;
  const opportunityCount = priorities.filter((p) => p.category.toLowerCase().includes('opportunity')).length;
  const benchmarkCount = priorities.filter((p) => p.category.toLowerCase().includes('benchmark')).length;

  return (
    <main className="max-w-screen-xl mx-auto px-6 py-12">
      {/* Welcome Banner - First-run guidance */}
      <WelcomeBanner />

      {/* Hero */}
      <div className="border-b-4 border-ink dark:border-stone-600 pb-8 mb-12">
        <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-4">
          Priority Intelligence Report
        </div>
        <h1 className="font-headline text-5xl md:text-7xl lg:text-8xl leading-[0.95] tracking-tight mb-6">
          Priority<br/>Board
        </h1>
        <p className="font-body text-lg md:text-xl text-stone-600 dark:text-stone-400 leading-relaxed max-w-2xl mb-2">
          Top {priorities.length} commercial concerns requiring immediate attention for {formatMonthYear(latestMonth)}, ranked by severity, persistence, and competitive gap.
        </p>
      </div>

      {/* Summary Cards - Clickable Filters */}
      <div className="mb-12 grid grid-cols-2 md:grid-cols-4 gap-4">
          <button
            onClick={() => filterByCategory('critical')}
            className={`glass-card p-6 rounded-2xl transition-all hover-glow relative overflow-hidden group ${
              activeFilter === 'critical' ? 'ring-2 ring-critical-light dark:ring-critical-dark shadow-sport' : ''
            }`}
            title={activeFilter === 'critical' ? 'Click to show all priorities' : 'Filter by critical priorities'}
          >
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-critical-light to-critical-dark"></div>
            {activeFilter === 'critical' && (
              <div className="absolute top-2 right-2 w-6 h-6 rounded-full bg-critical-light dark:bg-critical-dark text-white flex items-center justify-center">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"/>
                </svg>
              </div>
            )}
            <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-3">
              Critical
            </div>
            <div className="font-headline text-5xl text-critical-light dark:text-critical-dark">
              {criticalCount}
            </div>
          </button>

          <button
            onClick={() => filterByCategory('opportunity')}
            className={`glass-card p-6 rounded-2xl transition-all hover-glow relative overflow-hidden group ${
              activeFilter === 'opportunity' ? 'ring-2 ring-good-light dark:ring-good-dark shadow-sport' : ''
            }`}
            title={activeFilter === 'opportunity' ? 'Click to show all priorities' : 'Filter by opportunity priorities'}
          >
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-good-light to-good-dark"></div>
            {activeFilter === 'opportunity' && (
              <div className="absolute top-2 right-2 w-6 h-6 rounded-full bg-good-light dark:bg-good-dark text-white flex items-center justify-center">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"/>
                </svg>
              </div>
            )}
            <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-3">
              Opportunity
            </div>
            <div className="font-headline text-5xl text-good-light dark:text-good-dark">
              {opportunityCount}
            </div>
          </button>

          <button
            onClick={() => filterByCategory('benchmark')}
            className={`glass-card p-6 rounded-2xl transition-all hover-glow relative overflow-hidden group ${
              activeFilter === 'benchmark' ? 'ring-2 ring-info-light dark:ring-info-dark shadow-sport' : ''
            }`}
            title={activeFilter === 'benchmark' ? 'Click to show all priorities' : 'Filter by benchmark priorities'}
          >
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-info-light to-info-dark"></div>
            {activeFilter === 'benchmark' && (
              <div className="absolute top-2 right-2 w-6 h-6 rounded-full bg-info-light dark:bg-info-dark text-white flex items-center justify-center">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"/>
                </svg>
              </div>
            )}
            <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-3">
              Benchmark
            </div>
            <div className="font-headline text-5xl text-info-light dark:text-info-dark">
              {benchmarkCount}
            </div>
          </button>

          <button
            onClick={() => filterByCategory('all')}
            className={`glass-card p-6 rounded-2xl transition-all hover-glow relative overflow-hidden group ${
              activeFilter === 'all' ? 'ring-2 ring-sport-blue-600 shadow-sport' : ''
            }`}
            title="Show all priorities"
          >
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-sport"></div>
            {activeFilter === 'all' && (
              <div className="absolute top-2 right-2 w-6 h-6 rounded-full bg-sport-blue-600 text-white flex items-center justify-center">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"/>
                </svg>
              </div>
            )}
            <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-3">
              Total Priorities
            </div>
            <div className="font-headline text-5xl text-sport-blue-600">
              {priorities.length}
            </div>
          </button>
      </div>

      {/* Priority Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredPriorities.map((priority) => {
          const colorType = getColorForCategory(priority.category);
          const colors = getColorClasses(colorType);

          return (
            <article
              key={priority.priority_id}
              className={`glass-card p-8 cursor-pointer hover-lift animate-fade-in rounded-2xl relative overflow-hidden group`}
              onClick={() => openDetail(priority.priority_id)}
            >
              {/* Gradient accent overlay */}
              <div className={`absolute top-0 left-0 w-2 h-full ${colors.bg} opacity-80 group-hover:w-3 transition-all`}></div>

              {/* Event-Driven Banner (V1.5.2) */}
              {priority.anomaly_context?.context_type === "event_driven" && (
                <div className="mb-6 p-4 bg-amber-50 dark:bg-amber-900/20 border-l-4 border-amber-500 rounded-r-lg">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">📅</span>
                    <div className="flex-1">
                      <div className="font-semibold text-amber-900 dark:text-amber-300 text-sm mb-1">
                        EVENT-DRIVEN MOVEMENT
                      </div>
                      <div className="font-mono text-xs text-amber-800 dark:text-amber-400 mb-1">
                        {priority.anomaly_context.event_name} · {priority.anomaly_context.event_date}
                      </div>
                      <div className="text-xs text-amber-700 dark:text-amber-400">
                        {priority.anomaly_context.interpretation}
                      </div>
                      {priority.event_suppressed && (
                        <div className="mt-2 text-xs italic text-amber-600 dark:text-amber-500">
                          Score includes event-driven component — may normalize next month
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Header */}
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-baseline gap-4">
                  <div className={`font-headline text-6xl leading-none ${colors.text}`}>
                    {priority.rank}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`font-mono text-[10px] uppercase tracking-widest ${colors.text}`}>
                        {priority.category}
                      </span>
                      {priority.anomaly_context?.context_type === "event_driven" && (
                        <span className="px-2 py-0.5 rounded-full font-mono text-[10px] font-semibold tracking-wide bg-amber-500 text-white">
                          EVENT CONTEXT
                        </span>
                      )}
                      {priority.consecutive_declining_months && priority.consecutive_declining_months >= 2 && (
                        <span
                          className={`px-2 py-0.5 rounded-full font-mono text-[10px] font-semibold tracking-wide ${
                            priority.consecutive_declining_months >= 6
                              ? 'bg-critical-light dark:bg-critical-dark text-white'
                              : priority.consecutive_declining_months >= 4
                              ? 'bg-critical-light dark:bg-critical-dark text-white'
                              : 'bg-warning-light dark:bg-warning-dark text-white'
                          }`}
                          title={`Declining for ${priority.consecutive_declining_months} consecutive months`}
                        >
                          ↓ {priority.consecutive_declining_months} months
                        </span>
                      )}
                    </div>
                    <h2 className="font-headline text-2xl md:text-3xl leading-tight tracking-tight">
                      {priority.title}
                    </h2>
                  </div>
                </div>
              </div>

              {/* Metadata */}
              <div className="grid grid-cols-2 gap-4 mb-4 text-xs">
                <div>
                  <div className="font-mono uppercase tracking-widest text-stone-500 dark:text-stone-400">Asset</div>
                  <div className="font-semibold text-ink dark:text-stone-100">{formatAssetName(priority.asset_name)}</div>
                </div>
                <div>
                  <div className="font-mono uppercase tracking-widest text-stone-500 dark:text-stone-400">Metric</div>
                  <div className="flex items-center gap-2">
                    <div className="font-semibold text-ink dark:text-stone-100">{priority.primary_metric}</div>
                    <InfoTooltip metricName={priority.primary_metric} size="sm" />
                  </div>
                </div>
              </div>

              {/* Score Bar */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400">
                    Priority Score
                  </span>
                  <span className={`font-mono text-xl font-bold ${colors.text}`}>
                    {priority.score.toFixed(2)}
                  </span>
                </div>
                <div className="relative h-3 bg-stone-200 dark:bg-stone-800 rounded-full overflow-hidden shadow-inner">
                  <div
                    className={`absolute inset-y-0 left-0 ${colors.bg} rounded-full shadow-lg transition-all duration-500 ease-out group-hover:shadow-xl`}
                    style={{ width: `${priority.score * 100}%` }}
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent to-white/20"></div>
                  </div>
                </div>

                {/* Score Breakdown Bar */}
                {priority.score_breakdown && (
                  <div className="mt-3">
                    <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-1">
                      Score Components
                    </div>
                    <ScoreComponentBar
                      severity={priority.score_breakdown.severity}
                      persistence={priority.score_breakdown.persistence}
                      peerGap={priority.score_breakdown.peer_gap}
                      commercial={priority.score_breakdown.commercial}
                      evidence={priority.score_breakdown.evidence}
                      weights={SCORING_WEIGHTS}
                    />
                  </div>
                )}
              </div>

              {/* Why It Matters */}
              <div className="p-4 rounded-lg bg-gradient-to-br from-stone-50 to-stone-100 dark:from-stone-800 dark:to-stone-900 border border-stone-200 dark:border-stone-700/50 mb-4">
                <p className="font-sans text-sm text-stone-700 dark:text-stone-300 leading-relaxed">
                  <strong className="font-semibold text-ink dark:text-stone-100">Why It Matters:</strong> {priority.why_it_matters}
                </p>
                {priority.anomaly_context?.context_type === "partially_explained" && (
                  <div className="mt-3 pt-3 border-t border-stone-300 dark:border-stone-600">
                    <p className="text-xs text-amber-700 dark:text-amber-400">
                      ⚡ Partially explained by {priority.anomaly_context.event_name} — interpret with context
                    </p>
                  </div>
                )}
              </div>

              {/* Mini Sparkline (6-month trend) */}
              {priority.historical_values && priority.historical_values.length >= 2 && (
                <div className="mb-4 px-2">
                  <div className="font-mono text-[9px] uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-1">
                    6-Month Trend
                  </div>
                  <ResponsiveContainer width="100%" height={30}>
                    <LineChart
                      data={priority.historical_values.slice(-6)}
                      margin={{ top: 2, right: 2, bottom: 2, left: 2 }}
                    >
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke={
                          priority.trend_direction === 'up'
                            ? '#10b981'
                            : priority.trend_direction === 'down'
                            ? '#ef4444'
                            : '#6b7280'
                        }
                        strokeWidth={1.5}
                        dot={false}
                        isAnimationActive={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Action Button */}
              <div className={`px-6 py-3 text-center ${colors.bg} text-white font-mono text-xs uppercase tracking-widest hover:shadow-lg transition-all rounded-lg flex items-center justify-center gap-2`}>
                View Evidence
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"/>
                </svg>
              </div>
            </article>
          );
        })}
      </div>

      {/* Modal */}
      {selectedDetail && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 dark:bg-black/80 backdrop-blur-sm animate-fade-in"
          onClick={closeDetail}
        >
          <div
            className="relative glass-modal max-w-5xl w-full max-h-[90vh] overflow-y-auto rounded-3xl shadow-2xl animate-scale-in"
            onClick={(e) => e.stopPropagation()}
          >
            {detailLoading ? (
              <div className="p-12 text-center font-mono text-sm uppercase tracking-widest text-stone-500 dark:text-stone-400">
                Loading detail...
              </div>
            ) : (
              <>
                {/* Modal Header */}
                <div className="border-b-2 border-ink dark:border-stone-700 p-8 sticky top-0 bg-paper dark:bg-stone-900 z-10">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                        Priority Evidence Report · #{selectedDetail.rank}
                      </div>
                      <h2 className="font-headline text-4xl md:text-5xl leading-tight tracking-tight mb-2">
                        {selectedDetail.title}
                      </h2>
                      <div className="font-mono text-xs text-stone-600 dark:text-stone-400">
                        {selectedDetail.asset_name} · {selectedDetail.primary_metric}
                      </div>
                    </div>
                    <button
                      onClick={closeDetail}
                      className="p-2 hover:bg-stone-200 dark:hover:bg-stone-800 border border-transparent hover:border-ink dark:hover:border-stone-600 transition-colors"
                    >
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/>
                      </svg>
                    </button>
                  </div>

                  {/* Metric Context Banner */}
                  <div className="border-t border-stone-300 dark:border-stone-700 p-4 bg-info-50 dark:bg-info-dark/10">
                    <p className="font-body text-sm text-stone-700 dark:text-stone-300 leading-relaxed">
                      <strong className="font-semibold text-ink dark:text-stone-100">How this priority was scored:</strong> This priority scored {selectedDetail.score.toFixed(2)} because it combines severity (30%), persistence (25%), peer gap (20%), commercial impact (15%), and evidence (10%). Each component contributes to the total based on its weight. Click any metric name's{" "}
                      <span className="inline-flex items-center justify-center w-4 h-4 mx-0.5 rounded-full border border-stone-400 dark:border-stone-500 font-mono text-xs">?</span>{" "}
                      icon to see what it means.
                    </p>
                  </div>
                </div>

                {/* Modal Body */}
                <div className="p-8 space-y-8">
                  {/* Conversion Volume Panel (V1.5.4) - Only for conversion_rate */}
                  {selectedDetail.primary_metric === "conversion_rate" && selectedDetail.conversion_context && (
                    <ConversionVolumePanel conversion_context={selectedDetail.conversion_context} />
                  )}

                  {/* V1.7 — Social Priority Evidence Modal with Tabs */}
                  {selectedDetail.asset_name === "social_media" && (
                    <div className="mb-6">
                      {/* Tab Navigation */}
                      <div className="flex gap-2 mb-4 border-b border-stone-300 dark:border-stone-700">
                        {[
                          { id: "trend", label: "Trend" },
                          { id: "timing", label: "Timing Analysis" },
                          { id: "format", label: "Format Breakdown" },
                        ].map((tab) => (
                          <button
                            key={tab.id}
                            onClick={() => setSocialEvidenceTab(tab.id as typeof socialEvidenceTab)}
                            className={`px-4 py-2 font-semibold text-sm transition-colors ${
                              socialEvidenceTab === tab.id
                                ? "border-b-2 border-blue-600 text-blue-600 dark:text-blue-400"
                                : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
                            }`}
                          >
                            {tab.label}
                          </button>
                        ))}
                      </div>

                      {/* Tab Content */}
                      {socialEvidenceTab === "trend" && selectedDetail.historical_values && selectedDetail.historical_values.length > 0 && (
                        <div className="border border-stone-300 dark:border-stone-700 p-6 bg-stone-50 dark:bg-stone-800/50 rounded-lg">
                          <h3 className="font-headline text-xl mb-4">
                            {selectedDetail.primary_metric} — Last 12 Months
                          </h3>
                          <ResponsiveContainer width="100%" height={200}>
                            <LineChart data={selectedDetail.historical_values}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#A3A39E" opacity={0.3} />
                              <XAxis
                                dataKey="month"
                                tick={{ fontSize: 11, fontFamily: "JetBrains Mono, monospace" }}
                                stroke="#75756F"
                              />
                              <YAxis tick={{ fontSize: 11, fontFamily: "JetBrains Mono, monospace" }} stroke="#75756F" />
                              <Tooltip />
                              <Line type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={2} dot={{ r: 4 }} />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      )}

                      {socialEvidenceTab === "timing" && (
                        <div className="border border-stone-300 dark:border-stone-700 p-6 bg-stone-50 dark:bg-stone-800/50 rounded-lg">
                          <h3 className="font-headline text-xl mb-4">Match Moment Performance</h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                            Placeholder: Match moment breakdown chart will be fetched from analytics API and displayed here.
                            Shows pre_match, during_match, post_match, non_matchday engagement patterns.
                          </p>
                          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded">
                            <p className="text-sm text-blue-900 dark:text-blue-300">
                              This tab will show a horizontal bar chart of match moment performance with underutilisation alerts.
                            </p>
                          </div>
                        </div>
                      )}

                      {socialEvidenceTab === "format" && (
                        <div className="border border-stone-300 dark:border-stone-700 p-6 bg-stone-50 dark:bg-stone-800/50 rounded-lg">
                          <h3 className="font-headline text-xl mb-4">Format Performance</h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                            Placeholder: Format breakdown table will be fetched from analytics API and displayed here.
                            Shows Reel vs standard post multipliers, video vs image performance.
                          </p>
                          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded">
                            <p className="text-sm text-blue-900 dark:text-blue-300">
                              This tab will show a table of content formats ranked by avg engagement with "Recommended" flags.
                              Key insight: Instagram Reels generate 7.8x more engagement than standard posts.
                            </p>
                          </div>
                        </div>
                      )}

                      {/* Relevant Insight Card */}
                      <div className="mt-6 p-6 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 shadow-sm">
                        <div className="flex items-center justify-between mb-3">
                          <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300">
                            HIGH
                          </span>
                          <span className="text-2xl">📊</span>
                        </div>
                        <h4 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                          Relevant Insight for {selectedDetail.primary_metric}
                        </h4>
                        <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
                          This section will show the most relevant InsightCard from the analytics API that relates to this metric.
                          For example, if the priority is about engagement_rate, it would show the "Instagram Reels generate 7.8x more engagement" insight.
                        </p>
                        <div className="p-3 bg-gray-100 dark:bg-gray-700 rounded font-mono text-xs text-gray-800 dark:text-gray-200">
                          <strong>Evidence:</strong> Dynamic evidence from analytics data will appear here
                        </div>
                      </div>

                      {/* Content Team Recommendation */}
                      <div className="mt-4 p-4 bg-amber-50 dark:bg-amber-900/20 border-l-4 border-amber-500 rounded">
                        <div className="flex items-start gap-2">
                          <span className="text-lg">📋</span>
                          <div>
                            <div className="font-semibold text-amber-900 dark:text-amber-300 mb-2">
                              Content Team Action
                            </div>
                            <p className="text-sm text-amber-800 dark:text-amber-400">
                              This section will show the most relevant recommendation from the content team recommendations API.
                              For example: "Prioritise Reel format for all non-time-sensitive content. For every 10 standard image posts planned, consider converting 3-4 to Reels."
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* V1.8.5 — Social Priority Callout Box */}
                  {selectedDetail.asset_name === "social_media" && (
                    <div className="mb-6 p-4 border border-accent-light dark:border-accent-dark rounded-lg bg-accent-50 dark:bg-accent-dark/10">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">🎯</span>
                        <div className="flex-1">
                          <h4 className="font-semibold text-accent-light dark:text-accent-dark mb-2">
                            Social Media Platform Analysis
                          </h4>
                          <p className="text-sm text-stone-700 dark:text-stone-300 mb-3">
                            This priority is from the Social Media platform.
                            For full platform breakdown, content performance, and international audience analysis →
                          </p>
                          <button
                            onClick={() => {
                              closeDetail();
                              navigate('/social');
                            }}
                            className="px-4 py-2 rounded-lg font-semibold text-sm bg-accent-light dark:bg-accent-dark text-white hover:opacity-90 transition-opacity inline-flex items-center gap-2"
                          >
                            View Social Intelligence Screen
                            <span>↗</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* 12-Month Trend Chart (for non-social priorities) */}
                  {selectedDetail.asset_name !== "social_media" && selectedDetail.historical_values && selectedDetail.historical_values.length > 0 ? (
                    <section>
                      {(() => {
                        // Calculate 6-month average
                        const last6Values = selectedDetail.historical_values.slice(-6).map(d => d.value);
                        const sixMonthAvg = last6Values.reduce((sum, val) => sum + val, 0) / last6Values.length;

                        // Get metric definition for unit and polarity
                        const metricDef = getMetricDef(selectedDetail.primary_metric);
                        const unit = getMetricUnit(selectedDetail.primary_metric);
                        const polaritySymbol = metricDef ? getPolaritySymbol(metricDef.polarity) : '';

                        // Calculate ReferenceArea boundaries (last 3 months)
                        const last3Months = selectedDetail.historical_values.slice(-3);
                        const refAreaStart = last3Months[0]?.month;
                        const refAreaEnd = last3Months[last3Months.length - 1]?.month;

                        return (
                          <>
                            <div className="flex items-center gap-2 mb-4 pb-2 border-b border-stone-300 dark:border-stone-700">
                              <h3 className="font-headline text-2xl">
                                {selectedDetail.primary_metric} — Last 12 Months
                              </h3>
                              <InfoTooltip metricName={selectedDetail.primary_metric} size="md" />
                              {metricDef && (
                                <span
                                  className={`px-2 py-1 rounded-full font-mono text-xs font-semibold ${
                                    metricDef.polarity === 1
                                      ? 'bg-good-50 dark:bg-good-dark/20 text-good-600 dark:text-good-dark'
                                      : metricDef.polarity === -1
                                      ? 'bg-critical-50 dark:bg-critical-dark/20 text-critical-600 dark:text-critical-dark'
                                      : 'bg-stone-200 dark:bg-stone-700 text-stone-700 dark:text-stone-300'
                                  }`}
                                >
                                  {polaritySymbol} {metricDef.polarityLabel}
                                </span>
                              )}
                            </div>
                            <div className="border border-stone-300 dark:border-stone-700 p-6 bg-stone-50 dark:bg-stone-800/50 rounded-lg">
                              <ResponsiveContainer width="100%" height={200}>
                                <LineChart data={selectedDetail.historical_values}>
                                  <CartesianGrid strokeDasharray="3 3" stroke="#A3A39E" opacity={0.3} />
                                  <XAxis
                                    dataKey="month"
                                    tick={{ fontSize: 11, fontFamily: "JetBrains Mono, monospace" }}
                                    stroke="#75756F"
                                    tickFormatter={(value) => {
                                      const date = new Date(value);
                                      return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
                                    }}
                                  />
                                  <YAxis
                                    tick={{ fontSize: 11, fontFamily: "JetBrains Mono, monospace" }}
                                    stroke="#75756F"
                                    width={60}
                                    label={{ value: unit, angle: -90, position: 'insideLeft', style: { fontSize: 11, fill: '#75756F' } }}
                                  />
                                  <Tooltip content={<ChartTooltip metricName={selectedDetail.primary_metric} sixMonthAvg={sixMonthAvg} />} />
                                  {/* 6-month rolling average reference line */}
                                  <ReferenceLine
                                    y={sixMonthAvg}
                                    stroke="#2563EB"
                                    strokeDasharray="5 5"
                                    strokeWidth={1.5}
                                    label={{ value: '6-mo rolling avg', position: 'right', fontSize: 10, fill: '#2563EB' }}
                                  />
                                  {/* Last 3 months highlight area */}
                                  {refAreaStart && refAreaEnd && (
                                    <ReferenceArea
                                      x1={refAreaStart}
                                      x2={refAreaEnd}
                                      fill="#fbbf24"
                                      fillOpacity={0.1}
                                      stroke="#fbbf24"
                                      strokeOpacity={0.3}
                                      label={{ value: 'Last 3 months', position: 'top', fontSize: 9, fill: '#fbbf24' }}
                                    />
                                  )}
                                  {/* Event markers */}
                                  {nearbyEvents.map((event, idx) => (
                                    <ReferenceLine
                                      key={`event-${event.event_id}-${idx}`}
                                      x={event.event_date}
                                      stroke="#F59E0B"
                                      strokeDasharray="3 3"
                                      strokeWidth={1.5}
                                      label={{
                                        value: '⚡',
                                        position: 'top',
                                        fontSize: 14,
                                        fill: '#F59E0B'
                                      }}
                                    />
                                  ))}
                                  <Line
                                    type="monotone"
                                    dataKey="value"
                                    stroke={
                                      selectedDetail.trend_direction === 'down'
                                        ? '#EF4444'
                                        : selectedDetail.trend_direction === 'up'
                                        ? '#22C55E'
                                        : '#75756F'
                                    }
                                    strokeWidth={2}
                                    dot={(props: any) => {
                                      const isLast = props.index === selectedDetail.historical_values!.length - 1;
                                      if (isLast) {
                                        return (
                                          <circle
                                            cx={props.cx}
                                            cy={props.cy}
                                            r={5}
                                            fill={props.stroke}
                                            className="animate-pulse"
                                          />
                                        );
                                      }
                                      return <circle cx={props.cx} cy={props.cy} r={3} fill={props.stroke} />;
                                    }}
                                  />
                                </LineChart>
                              </ResponsiveContainer>
                              {/* Event Markers Legend */}
                              {nearbyEvents.length > 0 && (
                                <div className="mt-4 p-3 border-t border-stone-300 dark:border-stone-700">
                                  <p className="font-mono text-xs text-stone-600 dark:text-stone-400 mb-2">
                                    <strong className="text-amber-600 dark:text-amber-400">⚡ Event Markers:</strong> {nearbyEvents.length} event{nearbyEvents.length !== 1 ? 's' : ''} detected within 30 days of this metric's movement
                                  </p>
                                  <div className="flex flex-wrap gap-2">
                                    {nearbyEvents.slice(0, 3).map((event) => (
                                      <span
                                        key={event.event_id}
                                        className="px-2 py-1 text-xs rounded bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800"
                                        title={event.event_description}
                                      >
                                        {event.event_name}
                                      </span>
                                    ))}
                                    {nearbyEvents.length > 3 && (
                                      <span className="px-2 py-1 text-xs rounded bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-400">
                                        +{nearbyEvents.length - 3} more
                                      </span>
                                    )}
                                  </div>
                                </div>
                              )}
                              {/* Seasonal Intelligence Legend (V1.5.3) */}
                              {seasonalBaseline && (
                                <div className="mt-2 p-3 border-t border-stone-300 dark:border-stone-700">
                                  <p className="font-mono text-xs text-stone-600 dark:text-stone-400">
                                    <strong className="text-good-600 dark:text-good-dark">📊 Seasonal Intelligence:</strong> Chart shows 6-month rolling average (blue dashed line). Historical seasonal patterns available for each calendar month based on {Object.keys(seasonalBaseline).length} months of data.
                                  </p>
                                </div>
                              )}
                            </div>
                          </>
                        );
                      })()}
                    </section>
                  ) : (
                    <section>
                      <h3 className="font-headline text-2xl mb-4 pb-2 border-b border-stone-300 dark:border-stone-700">
                        Historical Trend
                      </h3>
                      <div className="p-6 bg-stone-50 dark:bg-stone-800/50 rounded-lg border border-stone-300 dark:border-stone-700">
                        <p className="font-mono text-sm text-stone-500 dark:text-stone-400 text-center">
                          Historical data unavailable
                        </p>
                      </div>
                    </section>
                  )}

                  {/* Seasonal Context Card (V1.5.3) */}
                  {selectedDetail.seasonal_context && (
                    <section>
                      <h3 className="font-headline text-2xl mb-4 pb-2 border-b border-stone-300 dark:border-stone-700">
                        Seasonal Intelligence
                      </h3>
                      <div className={`p-6 rounded-lg border-2 ${
                        selectedDetail.seasonal_context.is_within_normal_range
                          ? 'bg-good-50 dark:bg-good-dark/10 border-good-light dark:border-good-dark'
                          : Math.abs(selectedDetail.seasonal_context.z_score) >= 2.0
                          ? 'bg-critical-50 dark:bg-critical-dark/10 border-critical-light dark:border-critical-dark'
                          : 'bg-warning-50 dark:bg-warning-dark/10 border-warning-light dark:border-warning-dark'
                      }`}>
                        {/* Header Info */}
                        <div className="mb-4">
                          <div className="font-semibold text-ink dark:text-stone-100 mb-2">
                            {selectedDetail.primary_metric} in {selectedDetail.seasonal_context.month_name}
                          </div>
                          <div className="font-mono text-sm text-stone-700 dark:text-stone-300 mb-1">
                            Historical baseline: <span className="font-bold">{selectedDetail.seasonal_context.seasonal_mean.toFixed(4)}</span>
                            {' '}(based on {selectedDetail.seasonal_context.year_count} years of data)
                          </div>
                          <div className="font-mono text-sm text-stone-700 dark:text-stone-300">
                            Current reading: <span className="font-bold">{selectedDetail.seasonal_context.actual_value.toFixed(4)}</span> —{' '}
                            <span className={`font-semibold ${
                              selectedDetail.seasonal_context.is_within_normal_range
                                ? 'text-good-600 dark:text-good-dark'
                                : 'text-critical-600 dark:text-critical-dark'
                            }`}>
                              {selectedDetail.seasonal_context.is_within_normal_range ? 'within' : 'outside'} seasonal norm
                            </span>
                          </div>
                        </div>

                        {/* Interpretation */}
                        <div className="mb-4 p-3 bg-white/50 dark:bg-stone-900/50 rounded border border-stone-200 dark:border-stone-700">
                          <p className="text-sm text-stone-700 dark:text-stone-300 leading-relaxed">
                            {selectedDetail.seasonal_context.interpretation}
                          </p>
                        </div>

                        {/* Visual Range Bar */}
                        <div>
                          <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-2">
                            Historical Range for {selectedDetail.seasonal_context.month_name}
                          </div>
                          <div className="relative h-8 bg-stone-200 dark:bg-stone-800 rounded-lg overflow-hidden">
                            {/* Background gradient from min to max */}
                            <div className="absolute inset-0 bg-gradient-to-r from-critical-light/20 via-good-light/20 to-critical-light/20"></div>

                            {/* P25-P75 normal range highlight */}
                            <div
                              className="absolute top-0 bottom-0 bg-good-light/30 dark:bg-good-dark/30 border-l-2 border-r-2 border-good-light dark:border-good-dark"
                              style={{
                                left: `${((selectedDetail.seasonal_context.seasonal_p25 - selectedDetail.seasonal_context.seasonal_min) / (selectedDetail.seasonal_context.seasonal_max - selectedDetail.seasonal_context.seasonal_min)) * 100}%`,
                                right: `${100 - ((selectedDetail.seasonal_context.seasonal_p75 - selectedDetail.seasonal_context.seasonal_min) / (selectedDetail.seasonal_context.seasonal_max - selectedDetail.seasonal_context.seasonal_min)) * 100}%`
                              }}
                            ></div>

                            {/* Current value marker */}
                            <div
                              className="absolute top-0 bottom-0 w-1 bg-sport-blue-600 shadow-lg"
                              style={{
                                left: `${((selectedDetail.seasonal_context.actual_value - selectedDetail.seasonal_context.seasonal_min) / (selectedDetail.seasonal_context.seasonal_max - selectedDetail.seasonal_context.seasonal_min)) * 100}%`
                              }}
                              title={`Current: ${selectedDetail.seasonal_context.actual_value.toFixed(4)}`}
                            >
                              <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-3 h-3 bg-sport-blue-600 rotate-45"></div>
                            </div>

                            {/* Min/Max labels */}
                            <div className="absolute inset-0 flex items-center justify-between px-2 font-mono text-xs text-stone-600 dark:text-stone-400">
                              <span title={`Min: ${selectedDetail.seasonal_context.seasonal_min.toFixed(4)}`}>min</span>
                              <span title={`Mean: ${selectedDetail.seasonal_context.seasonal_mean.toFixed(4)}`}>mean</span>
                              <span title={`Max: ${selectedDetail.seasonal_context.seasonal_max.toFixed(4)}`}>max</span>
                            </div>
                          </div>
                          <div className="mt-2 flex justify-between font-mono text-xs text-stone-500 dark:text-stone-400">
                            <span>{selectedDetail.seasonal_context.seasonal_min.toFixed(4)}</span>
                            <span className="text-good-600 dark:text-good-dark" title="Normal range (p25–p75)">
                              [{selectedDetail.seasonal_context.seasonal_p25.toFixed(4)} – {selectedDetail.seasonal_context.seasonal_p75.toFixed(4)}]
                            </span>
                            <span>{selectedDetail.seasonal_context.seasonal_max.toFixed(4)}</span>
                          </div>
                        </div>

                        {/* Z-score badge */}
                        <div className="mt-4 flex items-center gap-2">
                          <span className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400">
                            Z-score:
                          </span>
                          <span className={`px-3 py-1 rounded-full font-mono text-sm font-bold ${
                            Math.abs(selectedDetail.seasonal_context.z_score) >= 2.0
                              ? 'bg-critical-light dark:bg-critical-dark text-white'
                              : Math.abs(selectedDetail.seasonal_context.z_score) >= 1.5
                              ? 'bg-warning-light dark:bg-warning-dark text-white'
                              : 'bg-good-light dark:bg-good-dark text-white'
                          }`}>
                            {selectedDetail.seasonal_context.z_score >= 0 ? '+' : ''}{selectedDetail.seasonal_context.z_score.toFixed(2)}σ
                          </span>
                          <span className="text-xs text-stone-600 dark:text-stone-400">
                            ({Math.abs(selectedDetail.seasonal_context.z_score) < 1.5 ? 'Normal variation' : Math.abs(selectedDetail.seasonal_context.z_score) < 2.0 ? 'Noteworthy' : 'Anomalous'})
                          </span>
                        </div>
                      </div>
                    </section>
                  )}

                  {/* Peer Benchmark Bar Chart */}
                  {selectedDetail.peer_values && selectedDetail.peer_values.length >= 2 ? (
                    <section>
                      {(() => {
                        // Get metric definition for unit
                        const metricDef = getMetricDef(selectedDetail.primary_metric);
                        const unit = getMetricUnit(selectedDetail.primary_metric);

                        // Get Real Madrid's value for gap calculation
                        const rmEntry = selectedDetail.peer_values.find(p => p.club === 'Real Madrid');
                        const rmValue = rmEntry?.value || 0;

                        // Calculate gaps
                        let gapToMedian = '';
                        let gapToLeader = '';
                        if (selectedDetail.peer_median !== null && selectedDetail.peer_median !== undefined) {
                          const diff = rmValue - selectedDetail.peer_median;
                          const sign = diff >= 0 ? '+' : '';
                          gapToMedian = `${sign}${diff.toFixed(4)}`;
                        }
                        if (selectedDetail.peer_leader_value !== null && selectedDetail.peer_leader_value !== undefined) {
                          const diff = rmValue - selectedDetail.peer_leader_value;
                          const sign = diff >= 0 ? '+' : '';
                          gapToLeader = `${sign}${diff.toFixed(4)}`;
                        }

                        return (
                          <>
                            <div className="flex items-center gap-2 mb-4 pb-2 border-b border-stone-300 dark:border-stone-700">
                              <h3 className="font-headline text-2xl">
                                Club Rankings — {selectedDetail.primary_metric} (Latest Month)
                              </h3>
                              <InfoTooltip metricName={selectedDetail.primary_metric} size="md" />
                            </div>
                            <div className="border border-stone-300 dark:border-stone-700 p-6 bg-stone-50 dark:bg-stone-800/50 rounded-lg">
                              <ResponsiveContainer width="100%" height={180}>
                                <BarChart
                                  data={[...selectedDetail.peer_values].sort((a, b) => {
                                    // Sort by value descending (best at top)
                                    // Polarity handling would go here, but simplified for now
                                    return b.value - a.value;
                                  })}
                                  layout="vertical"
                                  margin={{ left: 100 }}
                                >
                                  <CartesianGrid strokeDasharray="3 3" stroke="#A3A39E" opacity={0.3} />
                                  <XAxis
                                    type="number"
                                    tick={{ fontSize: 11, fontFamily: "JetBrains Mono, monospace" }}
                                    stroke="#75756F"
                                    label={{ value: unit, position: 'insideBottom', offset: -5, style: { fontSize: 11, fill: '#75756F' } }}
                                  />
                                  <YAxis
                                    type="category"
                                    dataKey="club"
                                    tick={{ fontSize: 11, fontFamily: "JetBrains Mono, monospace" }}
                                    stroke="#75756F"
                                    width={90}
                                  />
                                  <Tooltip
                                    contentStyle={{
                                      backgroundColor: "rgba(26, 26, 24, 0.95)",
                                      border: "1px solid #434340",
                                      borderRadius: "4px",
                                      fontFamily: "JetBrains Mono, monospace",
                                      fontSize: "11px",
                                      color: "#F5F5F3",
                                    }}
                                  />
                                  {selectedDetail.peer_median !== null && selectedDetail.peer_median !== undefined && (
                                    <ReferenceLine
                                      x={selectedDetail.peer_median}
                                      stroke="#2563EB"
                                      strokeDasharray="3 3"
                                      label={{ value: 'Peer Median', position: 'top', fontSize: 10, fill: '#2563EB' }}
                                    />
                                  )}
                                  {selectedDetail.peer_leader_value !== null && selectedDetail.peer_leader_value !== undefined && (
                                    <ReferenceLine
                                      x={selectedDetail.peer_leader_value}
                                      stroke="#22C55E"
                                      strokeDasharray="5 5"
                                      label={{ value: 'Market Leader', position: 'top', fontSize: 10, fill: '#22C55E' }}
                                    />
                                  )}
                                  <Bar dataKey="value">
                                    {selectedDetail.peer_values.map((entry, index) => (
                                      <Cell
                                        key={`cell-${index}`}
                                        fill={
                                          entry.club === 'Real Madrid'
                                            ? '#9333EA'
                                            : '#75756F'
                                        }
                                      />
                                    ))}
                                  </Bar>
                                </BarChart>
                              </ResponsiveContainer>

                              {selectedDetail.peer_values.some((entry) => entry.is_estimated) && (
                                <div className="mt-3 p-3 rounded-lg border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20">
                                  <p className="font-mono text-xs text-amber-800 dark:text-amber-300">
                                    Note: Some peer bars are modeled/estimated from aggregate benchmark stats (mean/median/leader), not direct club-level observed values.
                                  </p>
                                </div>
                              )}

                              {/* Gap Annotation */}
                              {(gapToMedian || gapToLeader) && (
                                <div className="mt-4 p-3 border-t border-stone-300 dark:border-stone-700">
                                  <p className="font-mono text-xs text-stone-600 dark:text-stone-400">
                                    <strong className="text-ink dark:text-stone-100">Real Madrid vs Peers:</strong>{" "}
                                    {gapToMedian && (
                                      <span>
                                        Gap to median: <span className={parseFloat(gapToMedian) >= 0 ? 'text-good-600 dark:text-good-dark' : 'text-critical-600 dark:text-critical-dark'}>{gapToMedian}</span>
                                      </span>
                                    )}
                                    {gapToMedian && gapToLeader && ' · '}
                                    {gapToLeader && (
                                      <span>
                                        Gap to leader: <span className={parseFloat(gapToLeader) >= 0 ? 'text-good-600 dark:text-good-dark' : 'text-critical-600 dark:text-critical-dark'}>{gapToLeader}</span>
                                      </span>
                                    )}
                                  </p>
                                </div>
                              )}
                            </div>
                          </>
                        );
                      })()}
                    </section>
                  ) : (
                    <section>
                      <h3 className="font-headline text-2xl mb-4 pb-2 border-b border-stone-300 dark:border-stone-700">
                        Peer Benchmark
                      </h3>
                      <div className="p-6 bg-stone-50 dark:bg-stone-800/50 rounded-lg border border-stone-300 dark:border-stone-700">
                        {selectedDetail.asset_name === "social_media" ? (
                          <div className="text-center">
                            <p className="font-mono text-sm text-stone-500 dark:text-stone-400 mb-3">
                              Peer social benchmark comparison available on the Social Intelligence screen
                            </p>
                            <button
                              onClick={() => {
                                closeDetail();
                                navigate('/social');
                              }}
                              className="px-3 py-1.5 rounded font-mono text-xs bg-accent-light dark:bg-accent-dark text-white hover:opacity-90 transition-opacity"
                            >
                              View Social Benchmarking →
                            </button>
                          </div>
                        ) : (
                          <p className="font-mono text-sm text-stone-500 dark:text-stone-400 text-center">
                            Peer benchmark data unavailable
                          </p>
                        )}
                      </div>
                    </section>
                  )}

                  {/* Overview Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-ink dark:bg-stone-700 border border-ink dark:border-stone-700">
                    <div className="bg-paper dark:bg-stone-900 p-4">
                      <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Category</div>
                      <div className="font-mono text-sm font-semibold mt-1 text-ink dark:text-stone-100">{selectedDetail.category}</div>
                    </div>
                    <div className="bg-paper dark:bg-stone-900 p-4">
                      <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Score</div>
                      <div className={`font-mono text-sm font-semibold mt-1 ${getColorClasses(getColorForCategory(selectedDetail.category)).text}`}>
                        {selectedDetail.score.toFixed(2)}
                      </div>
                    </div>
                    <div className="bg-paper dark:bg-stone-900 p-4">
                      <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Rank</div>
                      <div className="font-mono text-sm font-semibold mt-1 text-ink dark:text-stone-100">#{selectedDetail.rank}</div>
                    </div>
                    <div className="bg-paper dark:bg-stone-900 p-4">
                      <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Month</div>
                      <div className="font-mono text-sm font-semibold mt-1 text-ink dark:text-stone-100">{selectedDetail.month}</div>
                    </div>
                  </div>

                  {/* Why It Matters */}
                  <section>
                    <h3 className="font-headline text-2xl mb-4 pb-2 border-b border-stone-300 dark:border-stone-700">
                      Why It Matters
                    </h3>
                    <p className="font-body text-base leading-relaxed text-stone-700 dark:text-stone-300">
                      {selectedDetail.why_it_matters}
                    </p>
                  </section>

                  {/* Event Context (V1.5.2) */}
                  <section>
                    <h3 className="font-headline text-2xl mb-4 pb-2 border-b border-stone-300 dark:border-stone-700">
                      Event Context
                    </h3>
                    {selectedDetail.anomaly_context && selectedDetail.anomaly_context.context_type !== "unexplained" ? (
                      <div className="p-4 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
                        <div className="flex items-start gap-3 mb-3">
                          <span className="text-2xl">📅</span>
                          <div className="flex-1">
                            <div className="font-semibold text-amber-900 dark:text-amber-300 mb-1">
                              {selectedDetail.anomaly_context.event_name}
                            </div>
                            <div className="font-mono text-xs text-amber-800 dark:text-amber-400 mb-2">
                              {selectedDetail.anomaly_context.event_date} · {selectedDetail.anomaly_context.event_category?.replace(/_/g, ' ')}
                            </div>
                            <div className="text-sm text-amber-700 dark:text-amber-400 mb-3">
                              {selectedDetail.anomaly_context.interpretation}
                            </div>
                            <div className="flex items-center gap-2">
                              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                                selectedDetail.anomaly_context.context_type === "event_driven"
                                  ? "bg-amber-500 text-white"
                                  : "bg-amber-200 dark:bg-amber-800 text-amber-900 dark:text-amber-300"
                              }`}>
                                {selectedDetail.anomaly_context.adjusted_status}
                              </span>
                              {selectedDetail.event_suppressed && (
                                <span className="text-xs italic text-amber-600 dark:text-amber-500">
                                  May normalize next month
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="p-4 rounded-lg bg-stone-100 dark:bg-stone-800 border border-stone-200 dark:border-stone-700">
                        <p className="text-sm text-stone-600 dark:text-stone-400">
                          No registered events within 30 days of this data point. Movement is unexplained by known club events.
                        </p>
                      </div>
                    )}
                  </section>

                  {/* Summary */}
                  <section>
                    <h3 className="font-headline text-2xl mb-4 pb-2 border-b border-stone-300 dark:border-stone-700">
                      Detailed Analysis
                    </h3>
                    <p className="font-body text-base leading-relaxed text-stone-700 dark:text-stone-300">
                      {selectedDetail.summary_text}
                    </p>
                  </section>

                  {/* Score Breakdown */}
                  {selectedDetail.score_breakdown && (
                    <section>
                      <h3 className="font-headline text-2xl mb-4 pb-2 border-b border-stone-300 dark:border-stone-700">
                        Why This Priority Scored {selectedDetail.score.toFixed(2)}
                      </h3>
                      <p className="font-body text-sm mb-6 text-stone-600 dark:text-stone-400">
                        The priority score is calculated from 5 weighted components. Each component contributes to the total based on its weight.
                      </p>

                      {/* Horizontal Stacked Bar */}
                      <div className="mb-6">
                        <div className="h-3 flex overflow-hidden rounded border border-stone-300 dark:border-stone-700">
                          <div
                            className="bg-critical-light dark:bg-critical-dark transition-all"
                            style={{ width: `${(selectedDetail.score_breakdown.severity / 1.00) * 100}%` }}
                            title={`Severity: ${selectedDetail.score_breakdown.severity.toFixed(3)}`}
                          ></div>
                          <div
                            className="bg-warning-light dark:bg-warning-dark transition-all"
                            style={{ width: `${(selectedDetail.score_breakdown.persistence / 1.00) * 100}%` }}
                            title={`Persistence: ${selectedDetail.score_breakdown.persistence.toFixed(3)}`}
                          ></div>
                          <div
                            className="bg-info-light dark:bg-info-dark transition-all"
                            style={{ width: `${(selectedDetail.score_breakdown.peer_gap / 1.00) * 100}%` }}
                            title={`Peer Gap: ${selectedDetail.score_breakdown.peer_gap.toFixed(3)}`}
                          ></div>
                          <div
                            className="bg-good-light dark:bg-good-dark transition-all"
                            style={{ width: `${(selectedDetail.score_breakdown.commercial / 1.00) * 100}%` }}
                            title={`Commercial: ${selectedDetail.score_breakdown.commercial.toFixed(3)}`}
                          ></div>
                          <div
                            className="bg-accent-light dark:bg-accent-dark transition-all"
                            style={{ width: `${(selectedDetail.score_breakdown.evidence / 1.00) * 100}%` }}
                            title={`Evidence: ${selectedDetail.score_breakdown.evidence.toFixed(3)}`}
                          ></div>
                        </div>
                      </div>

                      {/* Score Breakdown Table */}
                      <div className="border border-ink dark:border-stone-700">
                        <table className="w-full data-table border-ink dark:border-stone-700 font-mono text-sm border-collapse">
                          <thead>
                            <tr className="bg-stone-100 dark:bg-stone-800">
                              <th className="text-left p-3 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Component</th>
                              <th className="text-right p-3 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Weight</th>
                              <th className="text-right p-3 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Component Score</th>
                              <th className="text-right p-3 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Contribution</th>
                              <th className="text-right p-3 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Max</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr>
                              <td className="p-3 border border-ink dark:border-stone-700">
                                <div className="flex items-center gap-2">
                                  <span>Severity</span>
                                  <InfoTooltip
                                    title="Severity"
                                    definition="Measures how far the metric has declined from its baseline. A higher severity score means the metric has deteriorated significantly compared to its historical average."
                                    formula="(baseline - current_value) / baseline × weight"
                                    size="sm"
                                  />
                                </div>
                              </td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700">30%</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700 text-stone-600 dark:text-stone-400">{selectedDetail.score_breakdown.severity.toFixed(3)} / 1.00</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700 font-bold">{selectedDetail.score_breakdown.severity_contribution.toFixed(3)}</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700">0.300</td>
                            </tr>
                            <tr className="bg-stone-50 dark:bg-stone-800/50">
                              <td className="p-3 border border-ink dark:border-stone-700">
                                <div className="flex items-center gap-2">
                                  <span>Persistence</span>
                                  <InfoTooltip
                                    title="Persistence"
                                    definition="Tracks how many consecutive months the metric has been declining. A higher persistence score indicates the problem is sustained over time, not a one-time anomaly."
                                    formula="consecutive_declining_months / 12 × weight"
                                    example="If a metric has declined for 6 consecutive months, persistence = (6/12) × 0.25 = 0.125"
                                    size="sm"
                                  />
                                </div>
                              </td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700">25%</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700 text-stone-600 dark:text-stone-400">{selectedDetail.score_breakdown.persistence.toFixed(3)} / 1.00</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700 font-bold">{selectedDetail.score_breakdown.persistence_contribution.toFixed(3)}</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700">0.250</td>
                            </tr>
                            <tr>
                              <td className="p-3 border border-ink dark:border-stone-700">
                                <div className="flex items-center gap-2">
                                  <span>Peer Gap</span>
                                  <InfoTooltip
                                    title="Peer Gap"
                                    definition="Compares Real Madrid's performance against 5 European clubs (Barcelona, Bayern Munich, Manchester United, Paris Saint-Germain, Manchester City). A higher peer gap score means Real Madrid is significantly behind the peer median or leader."
                                    formula="(peer_median - rm_value) / peer_median × weight"
                                    example="If Real Madrid's conversion rate is 0.013 and peer median is 0.018, peer gap = (0.018-0.013)/0.018 × 0.20 = 0.056"
                                    benchmarked={true}
                                    size="sm"
                                  />
                                </div>
                              </td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700">20%</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700 text-stone-600 dark:text-stone-400">{selectedDetail.score_breakdown.peer_gap.toFixed(3)} / 1.00</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700 font-bold">{selectedDetail.score_breakdown.peer_gap_contribution.toFixed(3)}</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700">0.200</td>
                            </tr>
                            <tr className="bg-stone-50 dark:bg-stone-800/50">
                              <td className="p-3 border border-ink dark:border-stone-700">
                                <div className="flex items-center gap-2">
                                  <span>Commercial</span>
                                  <InfoTooltip
                                    title="Commercial"
                                    definition="Assesses the revenue or cost implications of this issue. Metrics with high commercial impact (e.g., conversion_rate, net_sales, total_attendance) receive higher commercial scores because they directly affect the bottom line."
                                    formula="commercial_impact_tier × weight"
                                    example="Conversion rate has high commercial impact because it multiplies website traffic into revenue. A 1% decline in conversion rate can mean millions in lost sales."
                                    size="sm"
                                  />
                                </div>
                              </td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700">15%</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700 text-stone-600 dark:text-stone-400">{selectedDetail.score_breakdown.commercial.toFixed(3)} / 1.00</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700 font-bold">{selectedDetail.score_breakdown.commercial_contribution.toFixed(3)}</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700">0.150</td>
                            </tr>
                            <tr>
                              <td className="p-3 border border-ink dark:border-stone-700">
                                <div className="flex items-center gap-2">
                                  <span>Evidence</span>
                                  <InfoTooltip
                                    title="Evidence"
                                    definition="Measures how many supporting metrics confirm the problem. If multiple related metrics (e.g., unique_visitors, conversion_rate, and net_sales) are all declining together, the evidence score increases, indicating the issue is real and widespread."
                                    formula="supporting_metrics_count / max_supporting_metrics × weight"
                                    example="If 5 supporting metrics all show the same declining pattern, evidence = (5/10) × 0.10 = 0.050"
                                    size="sm"
                                  />
                                </div>
                              </td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700">10%</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700 text-stone-600 dark:text-stone-400">{selectedDetail.score_breakdown.evidence.toFixed(3)} / 1.00</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700 font-bold">{selectedDetail.score_breakdown.evidence_contribution.toFixed(3)}</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700">0.100</td>
                            </tr>
                            <tr className="bg-stone-100 dark:bg-stone-800 font-bold">
                              <td className="p-3 border border-ink dark:border-stone-700">TOTAL</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700">100%</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700">—</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700 text-lg">{selectedDetail.score.toFixed(3)}</td>
                              <td className="p-3 text-right border border-ink dark:border-stone-700">1.000</td>
                            </tr>
                          </tbody>
                        </table>
                        <p className="mt-2 px-3 py-2 bg-stone-50 dark:bg-stone-800 border-t border-stone-300 dark:border-stone-700 font-mono text-xs text-stone-600 dark:text-stone-400">
                          Component Score shows raw performance (0–1.0). Contribution shows weighted impact on final score.
                        </p>
                      </div>
                    </section>
                  )}

                  {/* Supporting Metrics Table */}
                  {selectedDetail.supporting_metrics?.metrics && Array.isArray(selectedDetail.supporting_metrics.metrics) && selectedDetail.supporting_metrics.metrics.length > 0 && (
                    <section>
                      <h3 className="font-headline text-2xl mb-4 pb-2 border-b border-stone-300 dark:border-stone-700">
                        Supporting Evidence
                      </h3>
                      <div className="border border-ink dark:border-stone-700">
                        <table className="w-full data-table border-ink dark:border-stone-700 font-mono text-sm border-collapse">
                          <thead>
                            <tr className="bg-stone-100 dark:bg-stone-800">
                              <th className="text-left p-3 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Metric</th>
                              <th className="text-right p-3 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Value</th>
                              <th className="text-right p-3 font-semibold uppercase text-xs tracking-widest border border-ink dark:border-stone-700">Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {selectedDetail.supporting_metrics.metrics.slice(0, 5).map((metric: any, idx: number) => (
                              <tr key={idx} className="hover:bg-stone-100 dark:hover:bg-stone-800">
                                <td className="p-3 border border-ink dark:border-stone-700">{metric.name || metric.metric_name || 'N/A'}</td>
                                <td className="p-3 text-right border border-ink dark:border-stone-700 font-semibold">
                                  {typeof metric.value === 'number' ? metric.value.toLocaleString() : metric.value}
                                </td>
                                <td className="p-3 text-right border border-ink dark:border-stone-700">
                                  {metric.status || metric.health_status || '-'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </section>
                  )}

                  {/* Peer Context */}
                  {selectedDetail.supporting_metrics?.peer_context && (
                    <section>
                      <h3 className="font-headline text-2xl mb-4 pb-2 border-b border-stone-300 dark:border-stone-700">
                        Competitive Context
                      </h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {Object.entries(selectedDetail.supporting_metrics.peer_context).map(([key, value]) => (
                          <div key={key} className="p-4 border border-stone-300 dark:border-stone-700 bg-stone-50 dark:bg-stone-800">
                            <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-1">
                              {key.replace(/_/g, ' ')}
                            </div>
                            <div className="font-mono text-lg font-semibold text-ink dark:text-stone-100">
                              {typeof value === 'number' ? value.toLocaleString() : value}
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Gap Annotation (V1.8.3) */}
                      {selectedDetail.supporting_metrics.peer_context.raw_gap_to_peer_median !== undefined && (() => {
                        const metricDef = getMetricDef(selectedDetail.primary_metric);
                        const polarity = metricDef?.polarity ?? 1;
                        const rawGap = selectedDetail.supporting_metrics.peer_context.raw_gap_to_peer_median;
                        const gapIsGood = (polarity === 1 && rawGap > 0) || (polarity === -1 && rawGap < 0);
                        const peerMedian = selectedDetail.supporting_metrics.peer_context.peer_median;
                        const peerLeader = selectedDetail.supporting_metrics.peer_context.peer_leader_value;

                        return (
                          <div className="mt-4 p-4 border border-stone-300 dark:border-stone-700 bg-paper dark:bg-stone-900">
                            {gapIsGood ? (
                              <p className="font-mono text-sm text-good-light dark:text-good-dark">
                                <span className="font-bold">▲ Real Madrid is ahead of peer median on this metric</span>
                                {polarity === -1 && rawGap < 0 && (
                                  <span className="block mt-1 text-xs text-stone-600 dark:text-stone-400">
                                    (Lower is better for this metric — being below median is an advantage)
                                  </span>
                                )}
                              </p>
                            ) : (
                              <p className="font-mono text-sm text-critical-light dark:text-critical-dark">
                                <span className="font-bold">▼ Real Madrid is {Math.abs(rawGap).toFixed(4)} behind peer median</span>
                                {polarity === -1 && rawGap > 0 && (
                                  <span className="block mt-1 text-xs text-stone-600 dark:text-stone-400">
                                    (Lower is better for this metric — being above median indicates underperformance)
                                  </span>
                                )}
                              </p>
                            )}

                            {/* Note when peer median equals peer leader */}
                            {peerMedian !== undefined && peerLeader !== undefined && Math.abs(peerLeader - peerMedian) < 0.0001 && (
                              <p className="mt-2 font-mono text-xs text-stone-500 dark:text-stone-400">
                                All benchmarked clubs show similar values for this metric this month.
                              </p>
                            )}
                          </div>
                        );
                      })()}
                    </section>
                  )}

                  {/* Next Investigation */}
                  <section className="border-t-2 border-ink dark:border-stone-700 pt-8">
                    <h3 className="font-headline text-2xl mb-4">Recommended Next Steps</h3>
                    <p className="font-body text-base leading-relaxed mb-6 text-stone-700 dark:text-stone-300">
                      {selectedDetail.suggested_next_investigation}
                    </p>
                    <div className="flex gap-4 flex-wrap">
                      <button
                        onClick={openAnalyticsDashboard}
                        className={`px-6 py-3 ${getColorClasses(getColorForCategory(selectedDetail.category)).bg} text-white font-mono text-xs uppercase tracking-widest hover:opacity-90 shadow-sm active:scale-98 transition-all`}
                      >
                        Open Analytics Dashboard →
                      </button>
                      <button
                        onClick={() => navigate('/benchmark')}
                        className="px-6 py-3 border-2 border-info-light dark:border-info-dark text-info-light dark:text-info-dark font-mono text-xs uppercase tracking-widest hover:bg-stone-100 dark:hover:bg-stone-800 transition-all"
                      >
                        View Peer Benchmark
                      </button>
                    </div>
                  </section>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Screen Guide - How to read this screen */}
      <div data-screen-guide>
        <ScreenGuide
          screenName="Priority Board"
          sections={[
            {
              title: "What is the Priority Board?",
              content: "The Priority Board is ClubOS's deterministic prioritization engine. Every month, the system analyzes 52 metrics across 4 platforms and ranks the top 10 commercial concerns that require immediate attention. Each priority is scored using 5 weighted components: severity (30%), persistence (25%), peer gap (20%), commercial impact (15%), and supporting evidence (10%). The higher the score, the more urgent the issue or opportunity."
            },
            {
              title: "How is priority rank calculated?",
              content: "Each priority receives a deterministic score between 0.00 and 1.00 based on the weighted formula. Severity measures how far the metric has declined from its baseline. Persistence tracks how many consecutive months it has declined. Peer gap compares Real Madrid's performance against 5 European clubs. Commercial impact assesses revenue/cost implications. Evidence measures how many supporting metrics confirm the problem. Priorities are then ranked #1 (highest score) to #10 (lowest score)."
            },
            {
              title: "What do the category labels mean?",
              content: "Critical priorities (red) indicate severe performance issues requiring immediate action—these typically score above 0.70 and show sustained decline. Opportunity priorities (green) represent upside potential or emerging competitive advantages. Benchmark priorities (blue) are areas where Real Madrid significantly lags peer clubs. Warning priorities (amber) are early signals worth monitoring but not yet critical."
            },
            {
              title: "What should I do with this list?",
              content: "Start with rank #1—it is the commercially most important issue this month. Click 'View Evidence' to see the full analysis: 12-month trend, peer benchmark, score breakdown, and supporting metrics. The 'Recommended Next Steps' section provides actionable guidance. Work through priorities in rank order. If a priority is outside your domain, forward it to the relevant team with context from the evidence report."
            },
            {
              title: "Why do I see values like 0.013 instead of percentages?",
              content: "Conversion rates and other percentage-based metrics are stored as decimals (0.013 = 1.3%). This is standard database practice. Throughout ClubOS, hover over any metric name to see its [?] icon—click it for the definition, formula, and example to understand how to interpret the numbers. Charts automatically format values with units (%, €, ★, etc.) for clarity."
            }
          ]}
        />
      </div>
    </main>
  );
}
