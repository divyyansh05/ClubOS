import { useState, useEffect } from 'react';
import { aiClient } from '../api/aiClient';

/**
 * Renders only the red count bubble — must be placed inside a `relative`
 * span alongside the "AI" nav label. Returns null when no unacknowledged
 * critical alerts exist so it is invisible by default.
 */
export function AlertsHeaderBadge() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    async function poll() {
      try {
        const resp = await aiClient.watchdog.listAlerts({
          limit: 100,
          unacknowledged_only: true,
        });
        const critical = resp.alerts.filter((a) => a.severity === 'critical').length;
        setCount(critical);
      } catch {
        // Non-blocking — badge stays hidden on error
      }
    }

    poll();
    const interval = setInterval(poll, 30_000);
    return () => clearInterval(interval);
  }, []);

  if (count === 0) return null;

  return (
    <span
      className="absolute -top-2 -right-4 bg-critical-light dark:bg-critical-dark text-white text-[10px] font-bold rounded-full h-4 w-4 flex items-center justify-center"
      title={`${count} unacknowledged critical alert${count !== 1 ? 's' : ''}`}
    >
      {count > 9 ? '9+' : count}
    </span>
  );
}
