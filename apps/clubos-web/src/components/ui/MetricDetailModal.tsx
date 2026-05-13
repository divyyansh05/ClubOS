import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface MetricDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  metricName: string;
  metricValue: string | number;
  metricCategory: string;
  explanation: string;
  businessContext: string;
  trendData?: Array<{ month: string; value: number }>;
  additionalInfo?: Record<string, string | number>;
}

export function MetricDetailModal({
  isOpen,
  onClose,
  metricName,
  metricValue,
  metricCategory,
  explanation,
  businessContext,
  trendData,
  additionalInfo,
}: MetricDetailModalProps) {
  if (!isOpen) return null;

  const getCategoryColor = (category: string) => {
    const lowerCategory = category.toLowerCase();
    if (lowerCategory.includes('good') || lowerCategory.includes('opportunity')) {
      return {
        border: 'border-good-light dark:border-good-dark',
        bg: 'bg-good-light dark:bg-good-dark',
        text: 'text-good-light dark:text-good-dark',
      };
    }
    if (lowerCategory.includes('critical') || lowerCategory.includes('review')) {
      return {
        border: 'border-critical-light dark:border-critical-dark',
        bg: 'bg-critical-light dark:bg-critical-dark',
        text: 'text-critical-light dark:text-critical-dark',
      };
    }
    if (lowerCategory.includes('warning')) {
      return {
        border: 'border-warning-light dark:border-warning-dark',
        bg: 'bg-warning-light dark:bg-warning-dark',
        text: 'text-warning-light dark:text-warning-dark',
      };
    }
    if (lowerCategory.includes('stable') || lowerCategory.includes('info')) {
      return {
        border: 'border-info-light dark:border-info-dark',
        bg: 'bg-info-light dark:bg-info-dark',
        text: 'text-info-light dark:text-info-dark',
      };
    }
    return {
      border: 'border-accent-light dark:border-accent-dark',
      bg: 'bg-accent-light dark:bg-accent-dark',
      text: 'text-accent-light dark:text-accent-dark',
    };
  };

  const colors = getCategoryColor(metricCategory);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/80 dark:bg-stone-950/90"
      onClick={onClose}
    >
      <div
        className="relative bg-paper dark:bg-stone-900 border-2 border-ink dark:border-stone-700 max-w-4xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className={`border-b-2 ${colors.border} p-8 sticky top-0 bg-paper dark:bg-stone-900 z-10`}>
          <div className="flex items-start justify-between">
            <div>
              <div className={`font-mono text-[10px] uppercase tracking-widest ${colors.text} mb-2`}>
                {metricCategory}
              </div>
              <h2 className="font-headline text-4xl md:text-5xl leading-tight tracking-tight mb-2">
                {metricName}
              </h2>
              <div className={`font-mono text-3xl font-bold ${colors.text} mt-4`}>
                {typeof metricValue === 'number' ? metricValue.toLocaleString() : metricValue}
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-stone-200 dark:hover:bg-stone-800 border border-transparent hover:border-ink dark:hover:border-stone-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-8 space-y-8">
          {/* What This Means */}
          <section>
            <h3 className="font-headline text-2xl mb-4 pb-2 border-b border-stone-300 dark:border-stone-700">
              What This Means
            </h3>
            <p className="font-body text-base leading-relaxed text-stone-700 dark:text-stone-300">
              {explanation}
            </p>
          </section>

          {/* Business Context */}
          <section>
            <h3 className="font-headline text-2xl mb-4 pb-2 border-b border-stone-300 dark:border-stone-700">
              Why It Matters
            </h3>
            <p className="font-body text-base leading-relaxed text-stone-700 dark:text-stone-300">
              {businessContext}
            </p>
          </section>

          {/* Trend Chart */}
          {trendData && trendData.length > 0 && (
            <section>
              <h3 className="font-headline text-2xl mb-4 pb-2 border-b border-stone-300 dark:border-stone-700">
                Trend Over Time
              </h3>
              <div className="border border-ink dark:border-stone-700 p-6 bg-stone-50 dark:bg-stone-800">
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#A3A39E" />
                    <XAxis
                      dataKey="month"
                      tick={{ fontSize: 11, fontFamily: "JetBrains Mono, monospace" }}
                      stroke="#75756F"
                    />
                    <YAxis
                      tick={{ fontSize: 11, fontFamily: "JetBrains Mono, monospace" }}
                      stroke="#75756F"
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
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke={colors.text.includes('good') ? '#22C55E' : colors.text.includes('critical') ? '#EF4444' : '#3B82F6'}
                      strokeWidth={3}
                      dot={{ r: 5 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </section>
          )}

          {/* Additional Info */}
          {additionalInfo && Object.keys(additionalInfo).length > 0 && (
            <section>
              <h3 className="font-headline text-2xl mb-4 pb-2 border-b border-stone-300 dark:border-stone-700">
                Additional Details
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Object.entries(additionalInfo).map(([key, value]) => (
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
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
