import type { Confidence } from '../api/types';

const CONFIDENCE_META: Record<Confidence, { label: string; classes: string }> = {
  high: {
    label: 'High confidence',
    classes: 'bg-good-50 text-good-light dark:bg-stone-800 dark:text-good-dark border-good-light/20 dark:border-good-dark/20',
  },
  medium: {
    label: 'Medium confidence',
    classes: 'bg-warning-50 text-warning-light dark:bg-stone-800 dark:text-warning-dark border-warning-light/20 dark:border-warning-dark/20',
  },
  low: {
    label: 'Low confidence',
    classes: 'bg-stone-100 text-stone-500 dark:bg-stone-800 dark:text-stone-400 border-stone-200 dark:border-stone-700',
  },
};

export function ConfidenceBadge({ confidence, size = 'sm' }: { confidence: Confidence | null; size?: 'sm' | 'md' }) {
  if (!confidence) return null;
  const meta = CONFIDENCE_META[confidence];
  const sizeClass = size === 'md' ? 'px-3 py-1 text-xs' : 'px-2 py-0.5 text-[10px]';
  return (
    <span className={`inline-flex items-center rounded-full border font-mono uppercase tracking-widest ${sizeClass} ${meta.classes}`}>
      {size === 'md' ? meta.label : confidence}
    </span>
  );
}
