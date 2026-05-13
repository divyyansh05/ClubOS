import { getMetricDef, getMetricUnit } from "../../lib/metricDefinitions";

interface ChartTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
  metricName: string;
  sixMonthAvg?: number;
}

export function ChartTooltip({
  active,
  payload,
  label,
  metricName,
  sixMonthAvg,
}: ChartTooltipProps) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const metricDef = getMetricDef(metricName);
  const unit = getMetricUnit(metricName);
  const value = payload[0].value;

  // Format month label
  const formatMonth = (dateStr: string): string => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", { month: "long", year: "numeric" });
  };

  // Format value based on unit
  const formatValue = (val: number): string => {
    if (unit === "%") {
      return `${(val * 100).toFixed(2)}%`;
    }
    if (unit === "€") {
      return `€${val.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    if (unit === "★") {
      return `${val.toFixed(1)}★`;
    }
    if (unit === "min") {
      return `${val.toFixed(1)} min`;
    }
    if (unit === "×") {
      return `${val.toFixed(2)}×`;
    }
    return val.toLocaleString("en-US");
  };

  // Calculate comparison to 6-month average
  let comparison = "";
  if (sixMonthAvg !== undefined && sixMonthAvg !== null && sixMonthAvg !== 0) {
    const diff = ((value - sixMonthAvg) / sixMonthAvg) * 100;
    const sign = diff >= 0 ? "+" : "";
    comparison = `${sign}${diff.toFixed(1)}% vs 6-mo avg`;
  }

  return (
    <div className="border-2 border-ink dark:border-stone-700 bg-paper dark:bg-stone-800 p-3 shadow-lg rounded max-w-xs">
      {/* Metric Label */}
      <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 mb-1">
        {metricDef?.label || metricName}
      </div>

      {/* Value */}
      <div className="font-headline text-2xl text-ink dark:text-stone-100 mb-1">
        {formatValue(value)}
      </div>

      {/* Month */}
      <div className="font-body text-sm text-stone-600 dark:text-stone-300 mb-2">
        {formatMonth(label || "")}
      </div>

      {/* Comparison */}
      {comparison && (
        <div
          className={`font-mono text-xs ${
            comparison.startsWith("+")
              ? "text-good-600 dark:text-good-dark"
              : "text-critical-600 dark:text-critical-dark"
          }`}
        >
          {comparison}
        </div>
      )}
    </div>
  );
}
