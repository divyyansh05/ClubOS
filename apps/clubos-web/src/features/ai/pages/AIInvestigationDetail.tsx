import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { aiClient } from '../api/aiClient';
import type { InvestigationRead } from '../api/types';
import { ConfidenceBadge } from '../components/ConfidenceBadge';
import { StatusPill } from '../components/StatusPill';
import { MarkdownRenderer } from '../components/MarkdownRenderer';
import { Citations } from '../components/Citations';
import { ReasoningTrace } from '../components/ReasoningTrace';

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex gap-4 py-2 border-b border-stone-100 dark:border-stone-800 last:border-0">
      <dt className="w-36 flex-shrink-0 font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500 pt-0.5">
        {label}
      </dt>
      <dd className="font-mono text-sm text-ink dark:text-stone-100 flex-1">{value}</dd>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="max-w-3xl space-y-6 animate-pulse">
      <div className="h-4 w-28 bg-stone-100 dark:bg-stone-800 rounded" />
      <div className="h-8 w-72 bg-stone-100 dark:bg-stone-800 rounded" />
      {[...Array(4)].map((_, i) => (
        <div key={i} className="h-4 bg-stone-100 dark:bg-stone-800 rounded" style={{ width: `${60 + i * 10}%` }} />
      ))}
    </div>
  );
}

export default function AIInvestigationDetail() {
  const { investigationId } = useParams<{ investigationId: string }>();
  const [inv, setInv] = useState<InvestigationRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!investigationId) return;
    setLoading(true);
    setError(null);
    aiClient.investigator.getById(investigationId)
      .then(setInv)
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, [investigationId]);

  if (loading) return <Skeleton />;

  if (error || !inv) {
    return (
      <div className="space-y-4 max-w-3xl">
        <Link to="/ai/investigations" className="font-mono text-[10px] uppercase tracking-widest text-stone-400 hover:text-ink dark:hover:text-stone-100 transition-colors">
          ← Investigations
        </Link>
        <div className="px-4 py-3 border border-critical-light/40 bg-critical-50 dark:bg-stone-900 dark:border-critical-dark/40">
          <p className="font-mono text-xs text-critical-light dark:text-critical-dark">
            {error ?? 'Investigation not found'}
          </p>
        </div>
      </div>
    );
  }

  const durationSeconds = inv.completed_at && inv.started_at
    ? ((new Date(inv.completed_at).getTime() - new Date(inv.started_at).getTime()) / 1000)
    : inv.latency_seconds;

  return (
    <article className="max-w-3xl space-y-8">
      {/* Breadcrumb */}
      <Link
        to="/ai/investigations"
        className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500 hover:text-ink dark:hover:text-stone-100 transition-colors"
      >
        ← Investigations
      </Link>

      {/* Header */}
      <header className="space-y-3 border-b-2 border-ink dark:border-stone-700 pb-6">
        <div className="flex items-center gap-3 flex-wrap">
          <StatusPill status={inv.status} />
          {inv.confidence && <ConfidenceBadge confidence={inv.confidence} size="md" />}
          {inv.trace_url && (
            <a
              href={inv.trace_url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-[10px] uppercase tracking-widest text-info-light dark:text-info-dark hover:opacity-70 transition-opacity"
            >
              View LangSmith trace →
            </a>
          )}
        </div>

        <h3 className="font-headline text-3xl tracking-tight">
          Investigation: {inv.metric_name || 'Unknown metric'}
        </h3>

        {/* Meta row */}
        <div className="flex flex-wrap gap-4 font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500">
          {durationSeconds != null && <span>{durationSeconds.toFixed(1)}s</span>}
          {inv.total_steps != null && <span>{inv.total_steps} step{inv.total_steps !== 1 ? 's' : ''}</span>}
          {inv.total_tokens != null && <span>{inv.total_tokens.toLocaleString()} tokens</span>}
          {inv.cost_usd != null && inv.cost_usd > 0 && <span>${inv.cost_usd.toFixed(4)}</span>}
          <span>Started {formatDateTime(inv.started_at)}</span>
        </div>
      </header>

      {/* Details table */}
      <section>
        <h4 className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500 mb-3">
          Details
        </h4>
        <dl className="border-t border-stone-200 dark:border-stone-700">
          <DetailRow
            label="Alert"
            value={
              inv.alert_id
                ? <Link to={`/ai/alerts/${inv.alert_id}`} className="text-info-light dark:text-info-dark hover:opacity-70 transition-opacity">{inv.alert_id}</Link>
                : '—'
            }
          />
          <DetailRow label="Triggered by" value={inv.triggered_by} />
          {inv.tools_called.length > 0 && (
            <DetailRow
              label="Tools used"
              value={
                <div className="flex flex-wrap gap-1.5">
                  {[...new Set(inv.tools_called)].map((t) => (
                    <code key={t} className="text-xs bg-stone-100 dark:bg-stone-800 border border-stone-200 dark:border-stone-700 px-1.5 py-0.5">
                      {t}
                    </code>
                  ))}
                </div>
              }
            />
          )}
        </dl>
      </section>

      {/* Failed state */}
      {inv.status === 'failed' && inv.error_message && (
        <section>
          <div className="px-4 py-3 border border-critical-light/40 bg-critical-50 dark:bg-stone-900 dark:border-critical-dark/40">
            <p className="font-mono text-xs uppercase tracking-wider text-critical-light dark:text-critical-dark mb-1">
              Investigation Failed
            </p>
            <p className="font-body text-sm text-stone-700 dark:text-stone-300">{inv.error_message}</p>
          </div>
        </section>
      )}

      {/* Cause hypothesis */}
      {inv.cause_hypothesis && (
        <section className="space-y-2">
          <h4 className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500">
            Cause Hypothesis
          </h4>
          <p className="font-body text-base leading-relaxed text-ink dark:text-stone-100 border-l-2 border-ink dark:border-stone-600 pl-4">
            {inv.cause_hypothesis}
          </p>
        </section>
      )}

      {/* Evidence summary */}
      {inv.evidence_summary && (
        <section className="space-y-3">
          <h4 className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500">
            Evidence
          </h4>
          <div className="border-t border-stone-200 dark:border-stone-700 pt-4">
            <MarkdownRenderer content={inv.evidence_summary} />
          </div>
        </section>
      )}

      {/* Reasoning trace */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500">
            Reasoning Trace
            {inv.reasoning_trace.length > 0 && (
              <span className="ml-2 text-stone-300 dark:text-stone-600">({inv.reasoning_trace.length} steps)</span>
            )}
          </h4>
          {inv.trace_url && (
            <a
              href={inv.trace_url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-[10px] uppercase tracking-widest text-info-light dark:text-info-dark hover:opacity-70 transition-opacity"
            >
              Full trace in LangSmith →
            </a>
          )}
        </div>
        <div className="border-t border-stone-200 dark:border-stone-700 pt-4">
          <ReasoningTrace trace={inv.reasoning_trace} traceUrl={inv.trace_url} />
        </div>
      </section>

      {/* Citations */}
      {inv.citations.length > 0 && (
        <section className="space-y-2">
          <h4 className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500">
            Citations
          </h4>
          <Citations citations={inv.citations} />
        </section>
      )}
    </article>
  );
}
