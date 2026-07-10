import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { aiClient } from '../api/aiClient';
import type { BriefingRead } from '../api/types';
import { StatusPill } from '../components/StatusPill';
import { MarkdownRenderer } from '../components/MarkdownRenderer';
import { Citations } from '../components/Citations';
import { MetricChip } from '../components/MetricChip';
import { formatBriefingTitle } from '../components/BriefingCard';

function formatDateRange(start: string, end: string): string {
  const s = new Date(start);
  const e = new Date(end);
  const opts: Intl.DateTimeFormatOptions = { month: 'long', day: 'numeric' };
  if (s.getFullYear() === e.getFullYear()) {
    return `${s.toLocaleDateString('en-US', opts)} – ${e.toLocaleDateString('en-US', { ...opts, year: 'numeric' })}`;
  }
  return `${s.toLocaleDateString('en-US', { ...opts, year: 'numeric' })} – ${e.toLocaleDateString('en-US', { ...opts, year: 'numeric' })}`;
}

function Skeleton() {
  return (
    <div className="max-w-3xl space-y-6 animate-pulse">
      <div className="h-4 w-20 bg-stone-100 dark:bg-stone-800 rounded" />
      <div className="h-8 w-80 bg-stone-100 dark:bg-stone-800 rounded" />
      <div className="space-y-2">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-4 bg-stone-100 dark:bg-stone-800 rounded" style={{ width: `${75 + (i % 3) * 10}%` }} />
        ))}
      </div>
    </div>
  );
}

function CollapsibleSection({
  title,
  count,
  children,
}: {
  title: string;
  count: number;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  if (count === 0) return null;
  return (
    <div className="border-t border-stone-200 dark:border-stone-700 pt-4">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500 hover:text-ink dark:hover:text-stone-100 transition-colors mb-3"
      >
        <span>{open ? '▼' : '▶'}</span>
        {title} ({count})
      </button>
      {open && <div>{children}</div>}
    </div>
  );
}

export default function AIBriefingDetail() {
  const { briefingId } = useParams<{ briefingId: string }>();
  const [briefing, setBriefing] = useState<BriefingRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!briefingId) return;
    setLoading(true);
    setError(null);
    aiClient.briefer.getById(briefingId)
      .then(setBriefing)
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, [briefingId]);

  if (loading) return <Skeleton />;

  if (error || !briefing) {
    return (
      <div className="space-y-4 max-w-3xl">
        <Link to="/ai/briefings" className="font-mono text-[10px] uppercase tracking-widest text-stone-400 hover:text-ink dark:hover:text-stone-100 transition-colors">
          ← Briefings
        </Link>
        <div className="px-4 py-3 border border-critical-light/40 bg-critical-50 dark:bg-stone-900 dark:border-critical-dark/40">
          <p className="font-mono text-xs text-critical-light dark:text-critical-dark">
            {error ?? 'Briefing not found'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <article className="max-w-3xl space-y-8">
      {/* Breadcrumb */}
      <Link
        to="/ai/briefings"
        className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500 hover:text-ink dark:hover:text-stone-100 transition-colors"
      >
        ← Briefings
      </Link>

      {/* Header */}
      <header className="space-y-3 border-b-2 border-ink dark:border-stone-700 pb-6">
        <div className="flex items-center gap-3 flex-wrap">
          <StatusPill status={briefing.status} />
          {briefing.trace_url && (
            <a
              href={briefing.trace_url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-[10px] uppercase tracking-widest text-info-light dark:text-info-dark hover:opacity-70 transition-opacity"
            >
              View reasoning trace →
            </a>
          )}
        </div>

        <h3 className="font-headline text-3xl tracking-tight">
          {formatBriefingTitle(briefing)}
        </h3>

        {briefing.period_start && briefing.period_end && (
          <p className="font-mono text-xs uppercase tracking-wider text-stone-500 dark:text-stone-400">
            Period: {formatDateRange(briefing.period_start, briefing.period_end)}
          </p>
        )}

        {/* Meta row */}
        <div className="flex flex-wrap gap-4 font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500 pt-1">
          {briefing.latency_seconds != null && <span>{briefing.latency_seconds.toFixed(1)}s</span>}
          {briefing.total_tokens != null && <span>{briefing.total_tokens.toLocaleString()} tokens</span>}
          {briefing.cost_usd != null && <span>${briefing.cost_usd.toFixed(4)}</span>}
          {briefing.completed_at && (
            <span>Generated {new Date(briefing.completed_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
          )}
        </div>
      </header>

      {/* Failed state */}
      {briefing.status === 'failed' && briefing.error_message && (
        <div className="px-4 py-3 border border-critical-light/40 bg-critical-50 dark:bg-stone-900 dark:border-critical-dark/40">
          <p className="font-mono text-xs uppercase tracking-wider text-critical-light dark:text-critical-dark mb-1">Generation Failed</p>
          <p className="font-body text-sm text-stone-700 dark:text-stone-300">{briefing.error_message}</p>
        </div>
      )}

      {/* Executive summary */}
      {briefing.executive_summary && (
        <section className="space-y-3">
          <h4 className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500">
            Executive Summary
          </h4>
          <p className="font-body text-base leading-relaxed text-ink dark:text-stone-100 border-l-2 border-ink dark:border-stone-600 pl-4">
            {briefing.executive_summary}
          </p>
        </section>
      )}

      {/* Full body */}
      {briefing.body_markdown && (
        <section className="space-y-3">
          <h4 className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500">
            Full Report
          </h4>
          <div className="border-t border-stone-200 dark:border-stone-700 pt-4">
            <MarkdownRenderer content={briefing.body_markdown} />
          </div>
        </section>
      )}

      {/* Citations */}
      {briefing.citations.length > 0 && (
        <section>
          <Citations citations={briefing.citations} />
        </section>
      )}

      {/* Collapsible reference sections */}
      <footer className="space-y-2">
        <CollapsibleSection title="Referenced Investigations" count={briefing.investigations_referenced.length}>
          <ul className="space-y-1">
            {briefing.investigations_referenced.map((id) => (
              <li key={id}>
                <Link
                  to={`/ai/investigations/${id}`}
                  className="font-mono text-xs text-info-light dark:text-info-dark hover:opacity-70 transition-opacity"
                >
                  {id}
                </Link>
              </li>
            ))}
          </ul>
        </CollapsibleSection>

        <CollapsibleSection title="Referenced Alerts" count={briefing.alerts_referenced.length}>
          <ul className="space-y-1">
            {briefing.alerts_referenced.map((id) => (
              <li key={id}>
                <Link
                  to={`/ai/alerts/${id}`}
                  className="font-mono text-xs text-info-light dark:text-info-dark hover:opacity-70 transition-opacity"
                >
                  {id}
                </Link>
              </li>
            ))}
          </ul>
        </CollapsibleSection>

        <CollapsibleSection title="Metrics Covered" count={briefing.metrics_covered.length}>
          <div className="flex flex-wrap gap-1.5">
            {briefing.metrics_covered.map((m) => (
              <MetricChip key={m} name={m} />
            ))}
          </div>
        </CollapsibleSection>
      </footer>
    </article>
  );
}
