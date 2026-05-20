import { ReferenceLine } from "recharts";
import type { EventSchema } from "../../types/events";

interface EventMarkerProps {
  event: EventSchema;
  orientation?: "above" | "below";
  xAxisKey?: string; // The data key for x-axis (e.g., "month")
}

const getCategoryIcon = (category: string): string => {
  switch (category) {
    case "player_signing":
    case "player_departure":
      return "\u{1F3BD}"; // trophy/sports
    case "match_result_win":
    case "trophy_win":
      return "\u{1F3C6}"; // trophy
    case "match_result_loss":
    case "trophy_loss":
      return "⚠️";
    case "transfer_window":
      return "\u{1F4C5}"; // calendar
    case "media_event":
      return "\u{1F4F0}"; // newspaper
    case "commercial_event":
      return "\u{1F4B0}"; // money bag
    case "injury_news":
      return "🏥";
    default:
      return "📌";
  }
};

const getMagnitudeBadge = (magnitude: string): { label: string; color: string } => {
  switch (magnitude) {
    case "high":
      return { label: "High", color: "text-critical-600 dark:text-critical-400" };
    case "medium":
      return { label: "Medium", color: "text-warning-600 dark:text-warning-400" };
    case "low":
      return { label: "Low", color: "text-info-600 dark:text-info-400" };
    default:
      return { label: magnitude, color: "text-stone-600" };
  }
};

export default function EventMarker({ event, orientation = "above", xAxisKey = "month" }: EventMarkerProps) {
  const icon = getCategoryIcon(event.event_category);
  const magnitudeBadge = getMagnitudeBadge(event.impact_magnitude);

  // Tooltip content
  const renderTooltip = () => (
    <div className="absolute z-50 hidden group-hover:block bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-white dark:bg-stone-800 border border-stone-200 dark:border-stone-700 rounded-lg shadow-lg">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg">{icon}</span>
          <h4 className="font-semibold text-sm text-ink dark:text-paper">{event.event_name}</h4>
        </div>
        <span className={`text-xs font-mono ${magnitudeBadge.color}`}>{magnitudeBadge.label}</span>
      </div>
      <p className="text-xs text-stone-600 dark:text-stone-400 mb-2">{event.event_date}</p>
      <p className="text-xs text-stone-700 dark:text-stone-300 mb-2">{event.event_description}</p>
      {event.affected_assets.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {event.affected_assets.map((asset) => (
            <span
              key={asset}
              className="px-2 py-0.5 text-xs rounded bg-stone-100 dark:bg-stone-700 text-stone-700 dark:text-stone-300"
            >
              {asset}
            </span>
          ))}
        </div>
      )}
      {/* Triangle pointer */}
      <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[6px] border-t-white dark:border-t-stone-800"></div>
    </div>
  );

  return (
    <g className="group relative">
      <ReferenceLine
        x={event.event_date}
        stroke="#F59E0B"
        strokeDasharray="3 3"
        strokeWidth={1.5}
        isFront
        label={{
          value: icon,
          position: orientation === "above" ? "top" : "bottom",
          fill: "#F59E0B",
          fontSize: 16,
        }}
      />
      {/* Note: Tooltip rendering in recharts is complex - we'll handle this in the parent component */}
    </g>
  );
}
