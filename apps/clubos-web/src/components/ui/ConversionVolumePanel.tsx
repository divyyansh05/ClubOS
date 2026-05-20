interface ConversionVolumePanelProps {
  conversion_context: {
    quadrant: string;
    label: string;
    interpretation: string;
    color: string;
    conversion_rate_value: number;
    visitors_value: number;
    conversion_seasonal_median: number;
    visitors_seasonal_median: number;
    conversion_vs_median_pct: number;
    visitors_vs_median_pct: number;
  };
}

export function ConversionVolumePanel({ conversion_context }: ConversionVolumePanelProps) {
  const {
    quadrant,
    label,
    interpretation,
    color,
    conversion_rate_value,
    visitors_value,
    conversion_seasonal_median,
    visitors_seasonal_median,
    conversion_vs_median_pct,
    visitors_vs_median_pct,
  } = conversion_context;

  // Determine border and bg colors
  const colorClasses = {
    good: "border-good-light dark:border-good-dark bg-good-50 dark:bg-good-dark/10",
    warning: "border-warning-light dark:border-warning-dark bg-warning-50 dark:bg-warning-dark/10",
    critical: "border-critical-light dark:border-critical-dark bg-critical-50 dark:bg-critical-dark/10"
  };

  const badgeColorClasses = {
    good: "bg-good-light dark:bg-good-dark text-white",
    warning: "bg-warning-light dark:bg-warning-dark text-white",
    critical: "bg-critical-light dark:bg-critical-dark text-white"
  };

  const borderClass = colorClasses[color as keyof typeof colorClasses] || colorClasses.warning;
  const badgeClass = badgeColorClasses[color as keyof typeof badgeColorClasses] || badgeColorClasses.warning;

  // Determine quadrant position for visualization
  const convAboveMedian = conversion_rate_value > conversion_seasonal_median;
  const volAboveMedian = visitors_value > visitors_seasonal_median;

  return (
    <div className={`p-6 rounded-lg border-2 ${borderClass} mb-8`}>
      <div className="mb-4">
        <h3 className="font-headline text-xl mb-2">Conversion Rate + Volume Context</h3>
        <p className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400">
          Supervisor note: "Conversion rate should be interpreted alongside volume and historical behaviour, not as a standalone KPI."
        </p>
      </div>

      {/* Two-column stat row */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="p-4 bg-white/50 dark:bg-stone-900/50 rounded border border-stone-200 dark:border-stone-700">
          <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-1">
            Conversion Rate
          </div>
          <div className="font-headline text-3xl mb-1">
            {(conversion_rate_value * 100).toFixed(2)}%
          </div>
          <div className={`font-mono text-xs ${conversion_vs_median_pct >= 0 ? 'text-good-600 dark:text-good-dark' : 'text-critical-600 dark:text-critical-dark'}`}>
            {conversion_vs_median_pct >= 0 ? '+' : ''}{conversion_vs_median_pct.toFixed(1)}% vs seasonal median
          </div>
        </div>

        <div className="p-4 bg-white/50 dark:bg-stone-900/50 rounded border border-stone-200 dark:border-stone-700">
          <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-1">
            Unique Visitors
          </div>
          <div className="font-headline text-3xl mb-1">
            {visitors_value.toLocaleString('en-US', { maximumFractionDigits: 0 })}
          </div>
          <div className={`font-mono text-xs ${visitors_vs_median_pct >= 0 ? 'text-good-600 dark:text-good-dark' : 'text-critical-600 dark:text-critical-dark'}`}>
            {visitors_vs_median_pct >= 0 ? '+' : ''}{visitors_vs_median_pct.toFixed(1)}% vs seasonal median
          </div>
        </div>
      </div>

      {/* Quadrant label badge */}
      <div className="mb-4">
        <span className={`px-4 py-2 rounded-full font-mono text-sm font-bold ${badgeClass}`}>
          {label}
        </span>
      </div>

      {/* Interpretation text */}
      <div className="mb-6 p-4 bg-white/50 dark:bg-stone-900/50 rounded border border-stone-200 dark:border-stone-700">
        <p className="text-sm text-stone-700 dark:text-stone-300 leading-relaxed">
          {interpretation}
        </p>
      </div>

      {/* Quadrant grid visualization */}
      <div>
        <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-3">
          Quadrant Position
        </div>
        <div className="relative grid grid-cols-2 gap-2 border-2 border-ink dark:border-stone-700 bg-stone-100 dark:bg-stone-900">
          {/* Top-left: High Conv, Low Vol */}
          <div className={`p-4 border-r-2 border-b-2 border-ink dark:border-stone-700 ${
            convAboveMedian && !volAboveMedian ? 'bg-warning-50 dark:bg-warning-dark/20' : 'bg-stone-50 dark:bg-stone-800'
          }`}>
            <div className="font-mono text-xs font-bold mb-1">Scale Risk</div>
            <div className="font-mono text-[10px] text-stone-500 dark:text-stone-400">High Conv / Low Vol</div>
            {convAboveMedian && !volAboveMedian && (
              <div className="mt-2 w-4 h-4 rounded-full bg-sport-blue-600 border-2 border-white dark:border-stone-900"></div>
            )}
          </div>

          {/* Top-right: High Conv, High Vol */}
          <div className={`p-4 border-b-2 border-ink dark:border-stone-700 ${
            convAboveMedian && volAboveMedian ? 'bg-good-50 dark:bg-good-dark/20' : 'bg-stone-50 dark:bg-stone-800'
          }`}>
            <div className="font-mono text-xs font-bold mb-1">Strong</div>
            <div className="font-mono text-[10px] text-stone-500 dark:text-stone-400">High Conv / High Vol</div>
            {convAboveMedian && volAboveMedian && (
              <div className="mt-2 w-4 h-4 rounded-full bg-sport-blue-600 border-2 border-white dark:border-stone-900"></div>
            )}
          </div>

          {/* Bottom-left: Low Conv, Low Vol */}
          <div className={`p-4 border-r-2 border-ink dark:border-stone-700 ${
            !convAboveMedian && !volAboveMedian ? 'bg-critical-50 dark:bg-critical-dark/20' : 'bg-stone-50 dark:bg-stone-800'
          }`}>
            <div className="font-mono text-xs font-bold mb-1">Underperform</div>
            <div className="font-mono text-[10px] text-stone-500 dark:text-stone-400">Low Conv / Low Vol</div>
            {!convAboveMedian && !volAboveMedian && (
              <div className="mt-2 w-4 h-4 rounded-full bg-sport-blue-600 border-2 border-white dark:border-stone-900"></div>
            )}
          </div>

          {/* Bottom-right: Low Conv, High Vol */}
          <div className={`p-4 ${
            !convAboveMedian && volAboveMedian ? 'bg-warning-50 dark:bg-warning-dark/20' : 'bg-stone-50 dark:bg-stone-800'
          }`}>
            <div className="font-mono text-xs font-bold mb-1">Funnel Risk</div>
            <div className="font-mono text-[10px] text-stone-500 dark:text-stone-400">Low Conv / High Vol</div>
            {!convAboveMedian && volAboveMedian && (
              <div className="mt-2 w-4 h-4 rounded-full bg-sport-blue-600 border-2 border-white dark:border-stone-900"></div>
            )}
          </div>
        </div>

        {/* Axis labels */}
        <div className="mt-2 flex justify-between font-mono text-[10px] text-stone-500 dark:text-stone-400">
          <span>← Visitor Volume</span>
          <span>Visitor Volume →</span>
        </div>
        <div className="mt-1 flex justify-center font-mono text-[10px] text-stone-500 dark:text-stone-400 rotate-90 origin-center absolute" style={{left: '-60px', top: '50%', transform: 'translateY(-50%) rotate(-90deg)'}}>
          Conversion Rate ↑
        </div>
      </div>
    </div>
  );
}
