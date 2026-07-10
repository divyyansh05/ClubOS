import type { Citation } from '../api/types';

const SOURCE_LABELS: Record<string, string> = {
  'gold.priority_board': 'Priority Board',
  'gold.metrics_monthly': 'Monthly Metrics',
  'gold.peer_benchmark': 'Peer Benchmark',
  'skills.priority_board': 'Priority Board (docs)',
  'skills.command_center': 'Command Center (docs)',
  'metric_registry': 'Metric Registry',
  'watchdog_alerts': 'Alerts',
  'investigations': 'Investigations',
};

function sourceLabel(source: string): string {
  if (SOURCE_LABELS[source]) return SOURCE_LABELS[source];
  if (source.startsWith('web_search:')) return 'Web Search';
  if (source.startsWith('gold.')) return source.replace('gold.', '').replace(/_/g, ' ');
  if (source.startsWith('skills.')) return source.replace('skills.', '').replace(/_/g, ' ') + ' (docs)';
  return source;
}

export function Citations({ citations }: { citations: Citation[] }) {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-2 flex flex-wrap items-center gap-1.5">
      <span className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500">
        Sources:
      </span>
      {citations.map((c, i) => (
        <span
          key={i}
          title={c.quote ?? c.claim}
          className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-300 border border-stone-200 dark:border-stone-700"
        >
          {sourceLabel(c.source)}
        </span>
      ))}
    </div>
  );
}
