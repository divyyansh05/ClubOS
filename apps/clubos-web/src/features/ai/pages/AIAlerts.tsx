import { useState, useEffect, useCallback } from 'react';
import { aiClient } from '../api/aiClient';
import type { WatchdogAlertRead } from '../api/types';
import { SeverityBadge } from '../components/SeverityBadge';
import { AlertRow } from '../components/AlertRow';

function TableSkeleton() {
  return (
    <div className="space-y-2">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="h-12 bg-stone-100 dark:bg-stone-800 animate-pulse" />
      ))}
    </div>
  );
}

function EmptyState({ onRun, running }: { onRun: () => void; running: boolean }) {
  return (
    <div className="py-16 text-center border-2 border-dashed border-stone-200 dark:border-stone-700">
      <p className="font-body text-stone-500 dark:text-stone-400 mb-4">
        No alerts yet. Run Watchdog to scan for anomalies.
      </p>
      <button
        onClick={onRun}
        disabled={running}
        className="font-mono text-xs uppercase tracking-wider px-4 py-2 border-2 border-ink dark:border-stone-300 hover:bg-ink hover:text-paper dark:hover:bg-stone-300 dark:hover:text-stone-900 transition-colors disabled:opacity-40"
      >
        {running ? 'Running…' : 'Run Watchdog'}
      </button>
    </div>
  );
}

export default function AIAlerts() {
  const [alerts, setAlerts] = useState<WatchdogAlertRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [acknowledging, setAcknowledging] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>('');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await aiClient.watchdog.listAlerts({ limit: 100 });
      setAlerts(resp.alerts);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleRunWatchdog() {
    setRunning(true);
    setRunError(null);
    try {
      await aiClient.watchdog.run({ triggered_by: 'ui' });
      await load();
    } catch (e) {
      setRunError((e as Error).message);
    } finally {
      setRunning(false);
    }
  }

  async function handleAcknowledge(alertId: string) {
    setAcknowledging(alertId);
    try {
      await aiClient.watchdog.acknowledgeAlert(alertId, 'ui_user');
      await load();
    } catch (e) {
      console.error('Acknowledge failed:', e);
    } finally {
      setAcknowledging(null);
    }
  }

  const filtered = severityFilter
    ? alerts.filter((a) => a.severity === severityFilter)
    : alerts;

  const criticalCount = alerts.filter((a) => a.severity === 'critical' && !a.acknowledged_at).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h3 className="font-headline text-2xl tracking-tight">Recent Alerts</h3>
          {criticalCount > 0 && (
            <SeverityBadge severity="critical" size="md" />
          )}
          {!loading && (
            <span className="font-mono text-xs text-stone-400 dark:text-stone-500 uppercase tracking-wider">
              {alerts.length} total
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {/* Severity filter */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="font-mono text-xs uppercase tracking-wider px-2 py-1.5 border border-stone-300 dark:border-stone-600 bg-paper dark:bg-stone-900 text-ink dark:text-stone-100 focus:outline-none focus:border-ink dark:focus:border-stone-400"
          >
            <option value="">All severities</option>
            <option value="critical">Critical</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>

          <button
            onClick={handleRunWatchdog}
            disabled={running || loading}
            className="font-mono text-xs uppercase tracking-wider px-4 py-2 border-2 border-ink dark:border-stone-300 hover:bg-ink hover:text-paper dark:hover:bg-stone-300 dark:hover:text-stone-900 transition-colors disabled:opacity-40"
          >
            {running ? 'Running…' : 'Run Watchdog'}
          </button>
        </div>
      </div>

      {/* Run error */}
      {runError && (
        <div className="px-4 py-3 border border-critical-light/40 bg-critical-50 dark:bg-stone-900 dark:border-critical-dark/40">
          <p className="font-mono text-xs text-critical-light dark:text-critical-dark uppercase tracking-wider">
            Watchdog run failed: {runError}
          </p>
        </div>
      )}

      {/* Content */}
      {loading && <TableSkeleton />}

      {!loading && error && (
        <div className="px-4 py-3 border border-critical-light/40 bg-critical-50 dark:bg-stone-900 dark:border-critical-dark/40">
          <p className="font-mono text-xs text-critical-light dark:text-critical-dark">{error}</p>
        </div>
      )}

      {!loading && !error && alerts.length === 0 && (
        <EmptyState onRun={handleRunWatchdog} running={running} />
      )}

      {!loading && !error && alerts.length > 0 && filtered.length === 0 && (
        <p className="py-8 text-center font-mono text-sm text-stone-400 dark:text-stone-500 uppercase tracking-wider">
          No {severityFilter} alerts
        </p>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse border-2 border-ink dark:border-stone-700">
            <thead>
              <tr className="border-b-2 border-ink dark:border-stone-700 bg-stone-50 dark:bg-stone-800">
                <th className="px-3 py-2 text-left font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Severity</th>
                <th className="px-3 py-2 text-left font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Metric</th>
                <th className="px-3 py-2 text-left font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Type</th>
                <th className="px-3 py-2 text-center font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Rank</th>
                <th className="px-3 py-2 text-center font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Score</th>
                <th className="px-3 py-2 text-left font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Detected</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {filtered.map((alert) => (
                <AlertRow
                  key={alert.alert_id}
                  alert={alert}
                  onAcknowledge={handleAcknowledge}
                  acknowledging={acknowledging === alert.alert_id}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
