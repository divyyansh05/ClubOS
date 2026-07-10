import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { aiClient } from '../api/aiClient';
import type { BriefingRead } from '../api/types';
import { BriefingCard } from '../components/BriefingCard';

function TableSkeleton() {
  return (
    <div className="space-y-4">
      {[...Array(3)].map((_, i) => (
        <div key={i} className="border-2 border-stone-100 dark:border-stone-800 p-6 space-y-3 animate-pulse">
          <div className="h-6 w-64 bg-stone-100 dark:bg-stone-800 rounded" />
          <div className="h-4 w-full bg-stone-100 dark:bg-stone-800 rounded" />
          <div className="h-4 w-3/4 bg-stone-100 dark:bg-stone-800 rounded" />
        </div>
      ))}
    </div>
  );
}

function EmptyState({ onGenerate, generating }: { onGenerate: () => void; generating: boolean }) {
  return (
    <div className="py-16 text-center border-2 border-dashed border-stone-200 dark:border-stone-700">
      <p className="font-headline text-xl tracking-tight mb-2">No briefings yet</p>
      <p className="font-body text-sm text-stone-500 dark:text-stone-400 mb-6">
        Generate a monthly executive briefing from all available data.
      </p>
      <button
        onClick={onGenerate}
        disabled={generating}
        className="font-mono text-xs uppercase tracking-wider px-4 py-2 border-2 border-ink dark:border-stone-300 hover:bg-ink hover:text-paper dark:hover:bg-stone-300 dark:hover:text-stone-900 transition-colors disabled:opacity-40"
      >
        {generating ? 'Generating… (this takes ~30–60s)' : 'Generate Monthly Briefing'}
      </button>
    </div>
  );
}

export default function AIBriefings() {
  const navigate = useNavigate();
  const [briefings, setBriefings] = useState<BriefingRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [lastCached, setLastCached] = useState<boolean | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await aiClient.briefer.list({ limit: 20 });
      setBriefings(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleGenerateMonthly() {
    setGenerating(true);
    setGenerateError(null);
    setLastCached(null);
    try {
      const result = await aiClient.briefer.runMonthly();
      setLastCached(result.was_cached);
      await load();
      navigate(`/ai/briefings/${result.briefing_id}`);
    } catch (e) {
      setGenerateError((e as Error).message);
      setGenerating(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h3 className="font-headline text-2xl tracking-tight">Executive Briefings</h3>
          {!loading && briefings.length > 0 && (
            <span className="font-mono text-xs text-stone-400 dark:text-stone-500 uppercase tracking-wider">
              {briefings.length} total
            </span>
          )}
        </div>
        <button
          onClick={handleGenerateMonthly}
          disabled={generating || loading}
          className="font-mono text-xs uppercase tracking-wider px-4 py-2 border-2 border-ink dark:border-stone-300 hover:bg-ink hover:text-paper dark:hover:bg-stone-300 dark:hover:text-stone-900 transition-colors disabled:opacity-40"
        >
          {generating ? 'Generating…' : 'Generate Monthly Briefing'}
        </button>
      </div>

      {/* Cache notice */}
      {lastCached === true && (
        <div className="px-4 py-2 border border-info-light/30 bg-info-50 dark:bg-stone-900 dark:border-info-dark/30">
          <p className="font-mono text-xs text-info-light dark:text-info-dark uppercase tracking-wider">
            Returned cached briefing — still fresh within {briefings[0]?.freshness_days ?? 7} days. Use force_regenerate to override.
          </p>
        </div>
      )}

      {/* Generate error */}
      {generateError && (
        <div className="px-4 py-3 border border-critical-light/40 bg-critical-50 dark:bg-stone-900 dark:border-critical-dark/40">
          <p className="font-mono text-xs text-critical-light dark:text-critical-dark">
            Generation failed: {generateError}
          </p>
        </div>
      )}

      {/* Content */}
      {loading && <TableSkeleton />}

      {!loading && error && (
        <div className="px-4 py-3 border border-critical-light/40 bg-critical-50 dark:bg-stone-900 dark:border-critical-dark/40">
          <p className="font-mono text-xs text-critical-light dark:text-critical-dark">{error}</p>
        </div>
      )}

      {!loading && !error && briefings.length === 0 && (
        <EmptyState onGenerate={handleGenerateMonthly} generating={generating} />
      )}

      {!loading && !error && briefings.length > 0 && (
        <div className="space-y-4">
          {briefings.map((b) => (
            <BriefingCard key={b.briefing_id} briefing={b} />
          ))}
        </div>
      )}
    </div>
  );
}
