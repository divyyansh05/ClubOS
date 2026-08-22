import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { aiClient } from '../api/aiClient';
import type { InvestigationRead, InvestigationStatus } from '../api/types';
import { ConfidenceBadge } from '../components/ConfidenceBadge';
import { StatusPill } from '../components/StatusPill';

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: '', label: 'All statuses' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'running', label: 'Running' },
  { value: 'timeout', label: 'Timeout' },
];

function formatDateShort(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

function truncate(s: string, n: number) {
  return s.length <= n ? s : s.slice(0, n).trimEnd() + '…';
}

function TableSkeleton() {
  return (
    <div className="space-y-2">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="h-12 bg-stone-100 dark:bg-stone-800 animate-pulse" />
      ))}
    </div>
  );
}

function InvestigationRow({ inv }: { inv: InvestigationRead }) {
  return (
    <tr className="border-b border-stone-200 dark:border-stone-700 hover:bg-stone-50 dark:hover:bg-stone-800/50 transition-colors group">
      <td className="px-3 py-3">
        <Link
          to={`/ai/investigations/${inv.investigation_id}`}
          className="font-mono text-sm text-ink dark:text-stone-100 hover:text-info-light dark:hover:text-info-dark transition-colors"
        >
          {inv.metric_name || '—'}
        </Link>
      </td>
      <td className="px-3 py-3">
        <ConfidenceBadge confidence={inv.confidence} />
      </td>
      <td className="px-3 py-3">
        <StatusPill status={inv.status} />
      </td>
      <td className="px-3 py-3 font-body text-sm text-stone-600 dark:text-stone-300 max-w-xs">
        {inv.cause_hypothesis
          ? truncate(inv.cause_hypothesis, 80)
          : inv.error_message
          ? <span className="text-critical-light dark:text-critical-dark font-mono text-xs">{truncate(inv.error_message, 60)}</span>
          : <span className="text-stone-400 dark:text-stone-500 italic text-xs">—</span>
        }
      </td>
      <td className="px-3 py-3">
        {inv.alert_id && (
          <Link
            to={`/ai/alerts/${inv.alert_id}`}
            className="font-mono text-[10px] uppercase tracking-wider text-info-light dark:text-info-dark hover:opacity-70 transition-opacity"
          >
            {inv.alert_id.slice(-8)}
          </Link>
        )}
      </td>
      <td className="px-3 py-3 font-mono text-xs text-stone-400 dark:text-stone-500 whitespace-nowrap">
        {formatDateShort(inv.started_at)}
      </td>
      <td className="px-3 py-3 text-right">
        <Link
          to={`/ai/investigations/${inv.investigation_id}`}
          className="font-mono text-[10px] uppercase tracking-wider text-stone-300 dark:text-stone-600 group-hover:text-info-light dark:group-hover:text-info-dark transition-colors"
        >
          →
        </Link>
      </td>
    </tr>
  );
}

export default function AIInvestigations() {
  const [investigations, setInvestigations] = useState<InvestigationRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await aiClient.investigator.list({ limit: 50 });
      setInvestigations(resp.investigations);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = statusFilter
    ? investigations.filter((i) => i.status === statusFilter)
    : investigations;

  const counts = investigations.reduce<Record<string, number>>((acc, i) => {
    acc[i.status] = (acc[i.status] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-4">
          <h3 className="font-headline text-2xl tracking-tight">Investigations</h3>
          {!loading && investigations.length > 0 && (
            <span className="font-mono text-xs text-stone-400 dark:text-stone-500 uppercase tracking-wider">
              {investigations.length} total
            </span>
          )}
        </div>

        {/* Status filter */}
        {!loading && investigations.length > 0 && (
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="font-mono text-xs px-2 py-1.5 border border-stone-300 dark:border-stone-600 bg-paper dark:bg-stone-900 text-ink dark:text-stone-100 focus:outline-none focus:border-ink dark:focus:border-stone-400 uppercase tracking-wider"
          >
            {STATUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}{o.value && counts[o.value] ? ` (${counts[o.value]})` : ''}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Status summary pills */}
      {!loading && investigations.length > 0 && (
        <div className="flex flex-wrap gap-3">
          {Object.entries(counts).map(([status, count]) => (
            <button
              key={status}
              onClick={() => setStatusFilter(statusFilter === status ? '' : status)}
              className={`flex items-center gap-1.5 transition-opacity ${statusFilter && statusFilter !== status ? 'opacity-40' : ''}`}
            >
              <StatusPill status={status as InvestigationStatus} />
              <span className="font-mono text-[10px] text-stone-400 dark:text-stone-500">{count}</span>
            </button>
          ))}
        </div>
      )}

      {/* Loading */}
      {loading && <TableSkeleton />}

      {/* Error */}
      {!loading && error && (
        <div className="px-4 py-3 border border-critical-light/40 bg-critical-50 dark:bg-stone-900 dark:border-critical-dark/40">
          <p className="font-mono text-xs text-critical-light dark:text-critical-dark">{error}</p>
        </div>
      )}

      {/* Empty */}
      {!loading && !error && investigations.length === 0 && (
        <div className="py-16 text-center border-2 border-dashed border-stone-200 dark:border-stone-700">
          <p className="font-headline text-xl tracking-tight mb-2">No investigations yet</p>
          <p className="font-body text-sm text-stone-500 dark:text-stone-400 mb-2">
            Trigger the Watchdog on the Alerts page to detect signals.
          </p>
          <p className="font-body text-sm text-stone-400 dark:text-stone-500">
            Then click "Investigate This Alert" on any alert to run the ReAct investigator.
          </p>
        </div>
      )}

      {/* No filtered results */}
      {!loading && !error && investigations.length > 0 && filtered.length === 0 && (
        <p className="py-8 text-center font-mono text-sm text-stone-400 dark:text-stone-500 uppercase tracking-wider">
          No {statusFilter} investigations
        </p>
      )}

      {/* Table */}
      {!loading && !error && filtered.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse border-2 border-ink dark:border-stone-700">
            <thead>
              <tr className="border-b-2 border-ink dark:border-stone-700 bg-stone-50 dark:bg-stone-800">
                <th className="px-3 py-2 text-left font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Metric</th>
                <th className="px-3 py-2 text-left font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Confidence</th>
                <th className="px-3 py-2 text-left font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Status</th>
                <th className="px-3 py-2 text-left font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Hypothesis</th>
                <th className="px-3 py-2 text-left font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Alert</th>
                <th className="px-3 py-2 text-left font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">Started</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {filtered.map((inv) => (
                <InvestigationRow key={inv.investigation_id} inv={inv} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
