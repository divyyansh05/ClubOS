import type { BriefingStatus, InvestigationStatus } from '../api/types';

type AnyStatus = BriefingStatus | InvestigationStatus | string;

const STATUS_META: Record<string, { label: string; classes: string }> = {
  completed: {
    label: 'Completed',
    classes: 'bg-good-50 text-good-light dark:bg-stone-800 dark:text-good-dark border-good-light/20 dark:border-good-dark/20',
  },
  generating: {
    label: 'Generating',
    classes: 'bg-info-50 text-info-light dark:bg-stone-800 dark:text-info-dark border-info-light/20 dark:border-info-dark/20',
  },
  running: {
    label: 'Running',
    classes: 'bg-info-50 text-info-light dark:bg-stone-800 dark:text-info-dark border-info-light/20 dark:border-info-dark/20',
  },
  failed: {
    label: 'Failed',
    classes: 'bg-critical-50 text-critical-light dark:bg-stone-800 dark:text-critical-dark border-critical-light/20 dark:border-critical-dark/20',
  },
  timeout: {
    label: 'Timeout',
    classes: 'bg-warning-50 text-warning-light dark:bg-stone-800 dark:text-warning-dark border-warning-light/20 dark:border-warning-dark/20',
  },
};

export function StatusPill({ status }: { status: AnyStatus }) {
  const meta = STATUS_META[status] ?? {
    label: status,
    classes: 'bg-stone-100 text-stone-500 dark:bg-stone-800 dark:text-stone-400 border-stone-200 dark:border-stone-700',
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest ${meta.classes}`}>
      {meta.label}
    </span>
  );
}
