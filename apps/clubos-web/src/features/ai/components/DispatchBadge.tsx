import type { SupervisorResponse, DispatchPath } from '../api/types';

const DISPATCH_META: Record<DispatchPath, { label: string; classes: string }> = {
  direct_scout: {
    label: 'Scout',
    classes: 'bg-info-50 text-info-light dark:bg-stone-800 dark:text-info-dark border-info-light/20 dark:border-info-dark/20',
  },
  direct_investigator: {
    label: 'Investigator',
    classes: 'bg-accent-50 text-accent-light dark:bg-stone-800 dark:text-accent-dark border-accent-light/20 dark:border-accent-dark/20',
  },
  direct_briefer: {
    label: 'Briefer',
    classes: 'bg-good-50 text-good-light dark:bg-stone-800 dark:text-good-dark border-good-light/20 dark:border-good-dark/20',
  },
  langgraph_supervisor: {
    label: 'Supervisor · multi-step',
    classes: 'bg-sport-blue-50 text-sport-blue-600 dark:bg-stone-800 dark:text-sport-blue-400 border-sport-blue-200 dark:border-sport-blue-800',
  },
  error: {
    label: 'Error',
    classes: 'bg-critical-50 text-critical-light dark:bg-stone-800 dark:text-critical-dark border-critical-light/20 dark:border-critical-dark/20',
  },
};

export function DispatchBadge({ response }: { response: SupervisorResponse }) {
  const meta = DISPATCH_META[response.dispatch_path] ?? DISPATCH_META.error;

  return (
    <div className={`inline-flex items-center gap-2 rounded-full px-3 py-1 border text-[10px] font-mono uppercase tracking-widest mb-2 ${meta.classes}`}>
      <span>{meta.label}</span>
      <span className="opacity-60">·</span>
      <span>{response.latency_seconds.toFixed(2)}s</span>
    </div>
  );
}
