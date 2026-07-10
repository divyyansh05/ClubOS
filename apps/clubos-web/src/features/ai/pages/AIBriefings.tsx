import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { aiClient } from '../api/aiClient';
import type { BriefingRead } from '../api/types';
import { BriefingCard } from '../components/BriefingCard';

// ── Helpers ───────────────────────────────────────────────────────────────────

const CURRENT_YEAR = new Date().getFullYear();
const TEST_YEAR_THRESHOLD = CURRENT_YEAR + 2;

function briefingPeriodYear(b: BriefingRead): number {
  if (b.scope_key.startsWith('monthly:')) {
    const year = parseInt(b.scope_key.slice(8, 12));
    if (!isNaN(year)) return year;
  }
  if (b.period_start) return new Date(b.period_start).getFullYear();
  return new Date(b.started_at).getFullYear();
}

function isTestBriefing(b: BriefingRead): boolean {
  return briefingPeriodYear(b) > TEST_YEAR_THRESHOLD;
}

type SortBy = 'latest' | 'oldest' | 'status';

function sortBriefings(list: BriefingRead[], by: SortBy): BriefingRead[] {
  const copy = [...list];
  if (by === 'latest') {
    return copy.sort((a, b) => briefingPeriodYear(b) - briefingPeriodYear(a) ||
      new Date(b.started_at).getTime() - new Date(a.started_at).getTime());
  }
  if (by === 'oldest') {
    return copy.sort((a, b) => briefingPeriodYear(a) - briefingPeriodYear(b) ||
      new Date(a.started_at).getTime() - new Date(b.started_at).getTime());
  }
  // status: completed → generating → failed
  const ORDER: Record<string, number> = { completed: 0, generating: 1, failed: 2 };
  return copy.sort((a, b) =>
    (ORDER[a.status] ?? 9) - (ORDER[b.status] ?? 9) ||
    new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

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
        {generating ? 'Generating… (~30–60s)' : 'Generate Monthly Briefing'}
      </button>
    </div>
  );
}

function TestBriefingsSection({ briefings }: { briefings: BriefingRead[] }) {
  const [open, setOpen] = useState(false);
  if (briefings.length === 0) return null;

  return (
    <div className="border border-stone-200 dark:border-stone-700 border-dashed">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-stone-50 dark:hover:bg-stone-800/40 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500">
            {open ? '▼' : '▶'}
          </span>
          <span className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500">
            Test / Eval Briefings
          </span>
          <span className="font-mono text-[10px] text-stone-300 dark:text-stone-600">
            ({briefings.length})
          </span>
        </div>
        <span className="font-mono text-[10px] uppercase tracking-widest text-stone-300 dark:text-stone-600">
          Dates outside current range — generated during eval
        </span>
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-stone-200 dark:border-stone-700 border-dashed pt-3">
          {briefings.map((b) => (
            <BriefingCard key={b.briefing_id} briefing={b} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

const SORT_OPTIONS: { value: SortBy; label: string }[] = [
  { value: 'latest', label: 'Latest first' },
  { value: 'oldest', label: 'Oldest first' },
  { value: 'status', label: 'By status' },
];

export default function AIBriefings() {
  const navigate = useNavigate();
  const [briefings, setBriefings] = useState<BriefingRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [lastCached, setLastCached] = useState<boolean | null>(null);
  const [sortBy, setSortBy] = useState<SortBy>('latest');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await aiClient.briefer.list({ limit: 50 });
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

  const realBriefings = sortBriefings(briefings.filter((b) => !isTestBriefing(b)), sortBy);
  const testBriefings = sortBriefings(briefings.filter(isTestBriefing), 'latest');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-4">
          <h3 className="font-headline text-2xl tracking-tight">Executive Briefings</h3>
          {!loading && realBriefings.length > 0 && (
            <span className="font-mono text-xs text-stone-400 dark:text-stone-500 uppercase tracking-wider">
              {realBriefings.length} briefing{realBriefings.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* Sort control */}
          {!loading && briefings.length > 1 && (
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500">
                Sort
              </span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortBy)}
                className="font-mono text-xs px-2 py-1.5 border border-stone-300 dark:border-stone-600 bg-paper dark:bg-stone-900 text-ink dark:text-stone-100 focus:outline-none focus:border-ink dark:focus:border-stone-400 uppercase tracking-wider"
              >
                {SORT_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
          )}

          <button
            onClick={handleGenerateMonthly}
            disabled={generating || loading}
            className="font-mono text-xs uppercase tracking-wider px-4 py-2 border-2 border-ink dark:border-stone-300 hover:bg-ink hover:text-paper dark:hover:bg-stone-300 dark:hover:text-stone-900 transition-colors disabled:opacity-40"
          >
            {generating ? 'Generating…' : 'Generate Monthly Briefing'}
          </button>
        </div>
      </div>

      {/* Cache notice */}
      {lastCached === true && (
        <div className="px-4 py-2 border border-info-light/30 bg-info-50 dark:bg-stone-900 dark:border-info-dark/30">
          <p className="font-mono text-xs text-info-light dark:text-info-dark uppercase tracking-wider">
            Returned cached briefing — still fresh within {briefings.find(b => !isTestBriefing(b))?.freshness_days ?? 7} days.
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

      {/* Loading */}
      {loading && <TableSkeleton />}

      {/* Fetch error */}
      {!loading && error && (
        <div className="px-4 py-3 border border-critical-light/40 bg-critical-50 dark:bg-stone-900 dark:border-critical-dark/40">
          <p className="font-mono text-xs text-critical-light dark:text-critical-dark">{error}</p>
        </div>
      )}

      {/* Real briefings — always visible */}
      {!loading && !error && realBriefings.length === 0 && testBriefings.length === 0 && (
        <EmptyState onGenerate={handleGenerateMonthly} generating={generating} />
      )}

      {!loading && !error && realBriefings.length === 0 && testBriefings.length > 0 && (
        <div className="py-8 text-center">
          <p className="font-body text-sm text-stone-500 dark:text-stone-400 mb-4">
            No production briefings yet.
          </p>
          <button
            onClick={handleGenerateMonthly}
            disabled={generating}
            className="font-mono text-xs uppercase tracking-wider px-4 py-2 border-2 border-ink dark:border-stone-300 hover:bg-ink hover:text-paper dark:hover:bg-stone-300 dark:hover:text-stone-900 transition-colors disabled:opacity-40"
          >
            {generating ? 'Generating…' : 'Generate Monthly Briefing'}
          </button>
        </div>
      )}

      {!loading && !error && realBriefings.length > 0 && (
        <div className="space-y-4">
          {realBriefings.map((b) => (
            <BriefingCard key={b.briefing_id} briefing={b} />
          ))}
        </div>
      )}

      {/* Test briefings — always collapsed at bottom */}
      {!loading && !error && (
        <TestBriefingsSection briefings={testBriefings} />
      )}
    </div>
  );
}
