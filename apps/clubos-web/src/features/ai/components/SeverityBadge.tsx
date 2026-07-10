import type { AlertSeverity } from '../api/types';

const SEVERITY_META: Record<AlertSeverity, { label: string; classes: string }> = {
  critical: {
    label: 'Critical',
    classes: 'bg-critical-50 text-critical-light dark:bg-stone-800 dark:text-critical-dark border-critical-light/30 dark:border-critical-dark/30',
  },
  warning: {
    label: 'Warning',
    classes: 'bg-warning-50 text-warning-light dark:bg-stone-800 dark:text-warning-dark border-warning-light/30 dark:border-warning-dark/30',
  },
  info: {
    label: 'Info',
    classes: 'bg-info-50 text-info-light dark:bg-stone-800 dark:text-info-dark border-info-light/30 dark:border-info-dark/30',
  },
};

interface SeverityBadgeProps {
  severity: AlertSeverity;
  size?: 'sm' | 'md';
}

export function SeverityBadge({ severity, size = 'sm' }: SeverityBadgeProps) {
  const meta = SEVERITY_META[severity] ?? SEVERITY_META.info;
  const sizeClass = size === 'md'
    ? 'px-3 py-1 text-xs'
    : 'px-2 py-0.5 text-[10px]';

  return (
    <span className={`inline-flex items-center rounded-full border font-mono uppercase tracking-widest ${sizeClass} ${meta.classes}`}>
      {meta.label}
    </span>
  );
}
