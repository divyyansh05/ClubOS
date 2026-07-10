import { Link } from 'react-router-dom';
import { StatusPill } from './StatusPill';
import type { BriefingRead } from '../api/types';

export function formatBriefingTitle(b: BriefingRead): string {
  if (b.scope_key.startsWith('monthly:')) {
    const ym = b.scope_key.replace('monthly:', '');
    const [year, month] = ym.split('-').map(Number);
    const d = new Date(year, month - 1, 1);
    return `Monthly Briefing · ${d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}`;
  }
  if (b.period_start) {
    const d = new Date(b.period_start);
    return `Briefing · ${d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}`;
  }
  return `Briefing · ${b.briefing_id.slice(-8)}`;
}

function truncate(text: string, max: number): string {
  if (text.length <= max) return text;
  return text.slice(0, max).trimEnd() + '…';
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  });
}

export function BriefingCard({ briefing, isCached }: { briefing: BriefingRead; isCached?: boolean }) {
  return (
    <Link
      to={`/ai/briefings/${briefing.briefing_id}`}
      className="block border-2 border-ink dark:border-stone-700 hover:border-info-light dark:hover:border-info-dark transition-colors group"
    >
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-3">
          <h4 className="font-headline text-xl tracking-tight group-hover:text-info-light dark:group-hover:text-info-dark transition-colors">
            {formatBriefingTitle(briefing)}
          </h4>
          <div className="flex items-center gap-2 flex-shrink-0">
            {isCached && (
              <span className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500">
                cached
              </span>
            )}
            <StatusPill status={briefing.status} />
          </div>
        </div>

        {/* Executive summary preview */}
        {briefing.executive_summary ? (
          <p className="font-body text-sm text-stone-600 dark:text-stone-300 leading-relaxed mb-4">
            {truncate(briefing.executive_summary, 220)}
          </p>
        ) : briefing.status === 'failed' && briefing.error_message ? (
          <p className="font-mono text-xs text-critical-light dark:text-critical-dark mb-4">
            {truncate(briefing.error_message, 180)}
          </p>
        ) : (
          <p className="font-body text-sm text-stone-400 dark:text-stone-500 italic mb-4">
            {briefing.status === 'generating' ? 'Generating…' : 'No summary available'}
          </p>
        )}

        {/* Metadata row */}
        <div className="flex flex-wrap items-center gap-4 font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500">
          <span>{formatDate(briefing.started_at)}</span>
          {briefing.investigations_referenced.length > 0 && (
            <span>{briefing.investigations_referenced.length} investigation{briefing.investigations_referenced.length !== 1 ? 's' : ''}</span>
          )}
          {briefing.metrics_covered.length > 0 && (
            <span>{briefing.metrics_covered.length} metric{briefing.metrics_covered.length !== 1 ? 's' : ''}</span>
          )}
          {briefing.latency_seconds != null && (
            <span>{briefing.latency_seconds.toFixed(1)}s</span>
          )}
          {briefing.cost_usd != null && (
            <span>${briefing.cost_usd.toFixed(4)}</span>
          )}
          <span className="ml-auto text-stone-300 dark:text-stone-600 group-hover:text-info-light dark:group-hover:text-info-dark transition-colors">→</span>
        </div>
      </div>
    </Link>
  );
}
