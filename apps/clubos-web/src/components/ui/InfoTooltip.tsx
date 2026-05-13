import { useState, useRef, useEffect } from "react";
import { getMetricDef, getPolaritySymbol } from "../../lib/metricDefinitions";

type InfoTooltipProps =
  | {
      metricName: string;
      size?: "sm" | "md";
    }
  | {
      title: string;
      definition: string;
      formula?: string;
      polarity?: string;
      example?: string;
      benchmarked?: boolean;
      size?: "sm" | "md";
    };

export function InfoTooltip(props: InfoTooltipProps) {
  // Determine if we're using metricName mode or explicit props
  const isMetricMode = "metricName" in props;

  let title: string;
  let definition: string;
  let formula: string | undefined;
  let polarity: string | undefined;
  let example: string | undefined;
  let benchmarked: boolean;
  let size: "sm" | "md";

  if (isMetricMode) {
    const metricDef = getMetricDef(props.metricName);
    if (!metricDef) {
      // Metric not found - don't render tooltip
      return null;
    }
    title = metricDef.label;
    definition = metricDef.definition;
    formula = metricDef.formula;
    polarity = metricDef.polarityLabel;
    example = metricDef.example;
    benchmarked = metricDef.benchmarked;
    size = props.size || "sm";
  } else {
    title = props.title;
    definition = props.definition;
    formula = props.formula;
    polarity = props.polarity;
    example = props.example;
    benchmarked = props.benchmarked || false;
    size = props.size || "sm";
  }
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState<"above" | "below">("above");
  const buttonRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  // Calculate position on open
  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const buttonRect = buttonRef.current.getBoundingClientRect();
      const spaceAbove = buttonRect.top;
      const spaceBelow = window.innerHeight - buttonRect.bottom;

      // Prefer above, but use below if not enough space
      setPosition(spaceAbove >= 300 ? "above" : "below");
    }
  }, [isOpen]);

  // Close on click outside
  useEffect(() => {
    if (!isOpen) return;

    function handleClickOutside(event: MouseEvent) {
      if (
        panelRef.current &&
        !panelRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen]);

  const iconSize = size === "sm" ? "w-4 h-4" : "w-5 h-5";
  const fontSize = size === "sm" ? "text-xs" : "text-sm";

  return (
    <div className="inline-block relative">
      <button
        ref={buttonRef}
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        className={`${iconSize} rounded-full border border-stone-400 dark:border-stone-500 flex items-center justify-center font-mono ${fontSize} text-stone-600 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-800 hover:border-stone-500 dark:hover:border-stone-400 transition-colors cursor-help`}
        title="Click for definition"
        type="button"
      >
        ?
      </button>

      {isOpen && (
        <div
          ref={panelRef}
          className={`absolute ${
            position === "above" ? "bottom-full mb-2" : "top-full mt-2"
          } left-1/2 -translate-x-1/2 z-50 w-80 animate-fade-in`}
          style={{ maxWidth: "calc(100vw - 2rem)" }}
        >
          <div className="border-2 border-ink dark:border-stone-700 bg-paper dark:bg-stone-800 p-4 shadow-lg rounded">
            {/* Title */}
            <h4 className="font-headline text-lg mb-2 text-ink dark:text-stone-100">
              {title}
            </h4>

            {/* Definition */}
            <p className="font-body text-sm text-stone-700 dark:text-stone-300 leading-relaxed mb-3">
              {definition}
            </p>

            {/* Formula */}
            {formula && (
              <div className="mb-3 p-2 bg-stone-100 dark:bg-stone-900 border border-stone-300 dark:border-stone-700">
                <div className="font-mono text-xs text-stone-600 dark:text-stone-400 mb-1">
                  Formula:
                </div>
                <div className="font-mono text-xs text-ink dark:text-stone-100">
                  {formula}
                </div>
              </div>
            )}

            {/* Polarity */}
            {polarity && (
              <div className="mb-3">
                <span
                  className={`inline-block px-2 py-1 rounded-full font-mono text-xs font-semibold ${
                    polarity.includes("Higher")
                      ? "bg-good-50 dark:bg-good-dark/20 text-good-600 dark:text-good-dark"
                      : polarity.includes("Lower")
                      ? "bg-critical-50 dark:bg-critical-dark/20 text-critical-600 dark:text-critical-dark"
                      : "bg-stone-200 dark:bg-stone-700 text-stone-700 dark:text-stone-300"
                  }`}
                >
                  {polarity.includes("Higher") && "↑ "}
                  {polarity.includes("Lower") && "↓ "}
                  {polarity.includes("Neutral") && "→ "}
                  {polarity}
                </span>
              </div>
            )}

            {/* Example */}
            {example && (
              <p className="font-body text-xs italic text-stone-500 dark:text-stone-400 leading-relaxed mb-3">
                <span className="font-mono not-italic">e.g.</span> {example}
              </p>
            )}

            {/* Benchmarked */}
            {benchmarked && (
              <div>
                <span className="inline-block px-2 py-1 rounded font-mono text-xs font-semibold bg-info-50 dark:bg-info-dark/20 text-info-600 dark:text-info-dark">
                  Peer benchmarked
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
