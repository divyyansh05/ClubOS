import { MarkdownRenderer } from './MarkdownRenderer';
import { DispatchBadge } from './DispatchBadge';
import { Citations } from './Citations';
import { TypingIndicator } from './TypingIndicator';
import { extractCitations } from '../api/types';
import type { Turn } from '../pages/AIChat';

export function MessageBubble({ turn }: { turn: Turn }) {
  if (turn.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] px-4 py-2.5 border-2 border-ink dark:border-stone-600 bg-stone-100 dark:bg-stone-800 font-body text-sm">
          {turn.content}
        </div>
      </div>
    );
  }

  if (turn.loading) {
    return (
      <div className="flex justify-start">
        <div className="max-w-[75%] px-4 py-3 border border-stone-200 dark:border-stone-700 bg-paper dark:bg-stone-900">
          <TypingIndicator />
        </div>
      </div>
    );
  }

  if (turn.error) {
    return (
      <div className="flex justify-start">
        <div className="max-w-[75%] px-4 py-3 border border-critical-light/40 dark:border-critical-dark/40 bg-critical-50 dark:bg-stone-900">
          <p className="font-mono text-xs uppercase tracking-wider text-critical-light dark:text-critical-dark mb-1">
            Error
          </p>
          <p className="font-body text-sm text-stone-700 dark:text-stone-300">{turn.error}</p>
        </div>
      </div>
    );
  }

  const citations = turn.response ? extractCitations(turn.response) : [];

  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] px-4 py-3 border border-stone-200 dark:border-stone-700 bg-paper dark:bg-stone-900">
        {turn.response && <DispatchBadge response={turn.response} />}

        <div className="text-ink dark:text-stone-100">
          <MarkdownRenderer content={turn.content} />
        </div>

        <Citations citations={citations} />

        {turn.response?.trace_url && (
          <div className="mt-2">
            <a
              href={turn.response.trace_url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-[10px] uppercase tracking-widest text-info-light dark:text-info-dark hover:opacity-70 transition-opacity"
            >
              View reasoning trace →
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
