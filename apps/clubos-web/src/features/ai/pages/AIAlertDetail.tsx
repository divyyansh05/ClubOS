import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { aiClient } from '../api/aiClient';
import type { WatchdogAlertRead, InvestigationRead } from '../api/types';
import { SeverityBadge } from '../components/SeverityBadge';

const ALERT_TYPE_LABELS: Record<string, string> = {
  new_in_top_n: 'New in Top N',
  rank_jumped_into_top: 'Rank Jump Into Top',
  rank_dropped_significantly: 'Rank Dropped Significantly',
  score_jump: 'Score Jump',
  dropped_out_of_top_n: 'Dropped Out of Top N',
  persistent_top: 'Persistent Top',
};

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex gap-4 py-2 border-b border-stone-100 dark:border-stone-800 last:border-0">
      <dt className="w-40 flex-shrink-0 font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500 pt-0.5">
        {label}
      </dt>
      <dd className="font-mono text-sm text-ink dark:text-stone-100">{value}</dd>
    </div>
  );
}

export default function AIAlertDetail() {
  const { alertId } = useParams<{ alertId: string }>();
  const navigate = useNavigate();

  const [alert, setAlert] = useState<WatchdogAlertRead | null>(null);
  const [investigations, setInvestigations] = useState<InvestigationRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [investigating, setInvestigating] = useState(false);
  const [investigateError, setInvestigateError] = useState<string | null>(null);
  const [snapshotExpanded, setSnapshotExpanded] = useState(false);

  useEffect(() => {
    if (!alertId) return;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [foundAlert, invResp] = await Promise.all([
          aiClient.watchdog.getAlertById(alertId!),
          aiClient.investigator.list({ alert_id: alertId }),
        ]);
        if (!foundAlert) {
          setError(`Alert ${alertId} not found.`);
        } else {
          setAlert(foundAlert);
          setInvestigations(invResp.investigations);
        }
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [alertId]);

  async function handleInvestigate() {
    if (!alertId) return;
    setInvestigating(true);
    setInvestigateError(null);
    try {
      const result = await aiClient.investigator.run(alertId, { triggered_by: 'ui' });
      navigate(`/ai/investigations/${result.investigation_id}`);
    } catch (e) {
      setInvestigateError((e as Error).message);
      setInvestigating(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 bg-stone-100 dark:bg-stone-800 animate-pulse" />
        <div className="h-4 w-full bg-stone-100 dark:bg-stone-800 animate-pulse" />
        <div className="h-4 w-3/4 bg-stone-100 dark:bg-stone-800 animate-pulse" />
      </div>
    );
  }

  if (error || !alert) {
    return (
      <div className="space-y-4">
        <Link to="/ai/alerts" className="font-mono text-xs uppercase tracking-wider text-stone-400 hover:text-ink dark:hover:text-stone-100 transition-colors">
          ← Alerts
        </Link>
        <div className="px-4 py-3 border border-critical-light/40 bg-critical-50 dark:bg-stone-900 dark:border-critical-dark/40">
          <p className="font-mono text-xs text-critical-light dark:text-critical-dark">
            {error ?? 'Alert not found'}
          </p>
        </div>
      </div>
    );
  }

  const scoreDelta = alert.score_previous != null
    ? (alert.score_current - alert.score_previous)
    : null;

  let snapshotParsed: unknown = null;
  try { snapshotParsed = JSON.parse(alert.context_snapshot); } catch { snapshotParsed = alert.context_snapshot; }

  return (
    <article className="space-y-8 max-w-3xl">
      {/* Breadcrumb */}
      <Link
        to="/ai/alerts"
        className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500 hover:text-ink dark:hover:text-stone-100 transition-colors"
      >
        ← Alerts
      </Link>

      {/* Header */}
      <header className="space-y-3">
        <div className="flex items-center gap-3 flex-wrap">
          <SeverityBadge severity={alert.severity} size="md" />
          {alert.acknowledged_at && (
            <span className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500">
              Acknowledged
            </span>
          )}
        </div>
        <h3 className="font-headline text-3xl tracking-tight">{alert.metric_name}</h3>
        <p className="font-mono text-xs uppercase tracking-wider text-stone-500 dark:text-stone-400">
          {ALERT_TYPE_LABELS[alert.alert_type] ?? alert.alert_type}
        </p>
      </header>

      {/* Details */}
      <section>
        <h4 className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500 mb-3">
          Alert Details
        </h4>
        <dl className="border-t border-stone-200 dark:border-stone-700">
          <DetailRow label="Detected" value={formatDateTime(alert.created_at)} />
          <DetailRow
            label="Current Rank"
            value={
              <span>
                #{alert.current_rank}
                {alert.previous_rank != null && (
                  <span className={`ml-2 text-xs ${
                    alert.rank_delta != null && alert.rank_delta > 0
                      ? 'text-critical-light dark:text-critical-dark'
                      : 'text-good-light dark:text-good-dark'
                  }`}>
                    (was #{alert.previous_rank}
                    {alert.rank_delta != null
                      ? `, Δ${alert.rank_delta > 0 ? '+' : ''}${alert.rank_delta}`
                      : ''})
                  </span>
                )}
              </span>
            }
          />
          <DetailRow
            label="Score"
            value={
              <span>
                {alert.score_current.toFixed(3)}
                {scoreDelta != null && (
                  <span className={`ml-2 text-xs ${scoreDelta > 0 ? 'text-critical-light dark:text-critical-dark' : 'text-good-light dark:text-good-dark'}`}>
                    ({scoreDelta > 0 ? '+' : ''}{scoreDelta.toFixed(3)})
                  </span>
                )}
              </span>
            }
          />
          <DetailRow label="Rule Fired" value={alert.triggered_by_rule} />
          <DetailRow label="Source" value={alert.source} />
          <DetailRow label="Run ID" value={<span className="text-xs">{alert.run_id}</span>} />
          {alert.acknowledged_at && (
            <DetailRow
              label="Acknowledged"
              value={`${formatDateTime(alert.acknowledged_at)} by ${alert.acknowledged_by ?? 'unknown'}`}
            />
          )}
        </dl>
      </section>

      {/* Context snapshot */}
      <section>
        <button
          onClick={() => setSnapshotExpanded((v) => !v)}
          className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500 hover:text-ink dark:hover:text-stone-100 transition-colors mb-2"
        >
          <span>{snapshotExpanded ? '▼' : '▶'}</span>
          Context Snapshot
        </button>
        {snapshotExpanded && (
          <pre className="bg-stone-50 dark:bg-stone-800 border border-stone-200 dark:border-stone-700 p-4 text-xs font-mono overflow-x-auto max-h-64 overflow-y-auto">
            {typeof snapshotParsed === 'string'
              ? snapshotParsed
              : JSON.stringify(snapshotParsed, null, 2)}
          </pre>
        )}
      </section>

      {/* Investigations */}
      <section className="space-y-4">
        <h4 className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500">
          Investigations ({investigations.length})
        </h4>

        {investigations.length === 0 ? (
          <div className="space-y-3">
            <p className="font-body text-sm text-stone-500 dark:text-stone-400">
              No investigations yet for this alert.
            </p>

            {investigateError && (
              <div className="px-4 py-3 border border-critical-light/40 bg-critical-50 dark:bg-stone-900 dark:border-critical-dark/40">
                <p className="font-mono text-xs text-critical-light dark:text-critical-dark">
                  {investigateError}
                </p>
              </div>
            )}

            <button
              onClick={handleInvestigate}
              disabled={investigating}
              className="font-mono text-xs uppercase tracking-wider px-4 py-2 border-2 border-ink dark:border-stone-300 hover:bg-ink hover:text-paper dark:hover:bg-stone-300 dark:hover:text-stone-900 transition-colors disabled:opacity-40"
            >
              {investigating ? 'Investigating… (15–45s)' : 'Investigate This Alert'}
            </button>
          </div>
        ) : (
          <ul className="space-y-2">
            {investigations.map((inv) => (
              <li key={inv.investigation_id}>
                <Link
                  to={`/ai/investigations/${inv.investigation_id}`}
                  className="flex items-center gap-3 p-3 border border-stone-200 dark:border-stone-700 hover:border-ink dark:hover:border-stone-400 transition-colors group"
                >
                  <span className={`font-mono text-[10px] uppercase tracking-widest rounded-full px-2 py-0.5 ${
                    inv.confidence === 'high' ? 'bg-good-50 text-good-light dark:bg-stone-800 dark:text-good-dark'
                    : inv.confidence === 'medium' ? 'bg-warning-50 text-warning-light dark:bg-stone-800 dark:text-warning-dark'
                    : 'bg-stone-100 text-stone-500 dark:bg-stone-800 dark:text-stone-400'
                  }`}>
                    {inv.confidence ?? inv.status}
                  </span>
                  <span className="font-body text-sm text-stone-600 dark:text-stone-300 group-hover:text-ink dark:group-hover:text-stone-100 transition-colors flex-1">
                    {inv.cause_hypothesis ?? '(investigation pending)'}
                  </span>
                  <span className="font-mono text-xs text-stone-400 dark:text-stone-500">→</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </article>
  );
}
