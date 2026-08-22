export function MetricChip({ name }: { name: string }) {
  return (
    <span className="inline-flex items-center rounded-full px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-300 border border-stone-200 dark:border-stone-700">
      {name.replace(/_/g, ' ')}
    </span>
  );
}
