import { useState, useEffect, useRef } from 'react';
import { aiClient } from '../api/aiClient';
import { extractAnswerText } from '../api/types';
import type { SupervisorResponse } from '../api/types';
import { MessageBubble } from '../components/MessageBubble';
import { ChatInput } from '../components/ChatInput';

export interface Turn {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  response?: SupervisorResponse;
  loading?: boolean;
  error?: string;
}

const SUGGESTIONS = [
  'What is streaming_daily_users this month?',
  'Show me the monthly summary for last month',
  'Compare last month to this month and explain any changes',
];

function SuggestionChip({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="text-left px-3 py-2 border border-stone-200 dark:border-stone-700 hover:border-ink dark:hover:border-stone-400 font-body text-sm text-stone-600 dark:text-stone-300 hover:text-ink dark:hover:text-stone-100 transition-colors"
    >
      {label}
    </button>
  );
}

function ChatEmptyState({ onSuggest }: { onSuggest: (q: string) => void }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center py-16 gap-6">
      <div className="text-center">
        <h3 className="font-headline text-2xl tracking-tight mb-2">AI Assistant</h3>
        <p className="font-body text-sm text-stone-500 dark:text-stone-400 max-w-sm">
          Ask about metrics, alerts, investigations, or request a monthly briefing.
        </p>
      </div>
      <div className="flex flex-col gap-2 w-full max-w-md">
        {SUGGESTIONS.map((s) => (
          <SuggestionChip key={s} label={s} onClick={() => onSuggest(s)} />
        ))}
      </div>
    </div>
  );
}

export default function AIChat() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns]);

  async function handleSubmit(query: string) {
    if (!query.trim() || submitting) return;

    const userId = `u_${Date.now()}`;
    const assistantId = `a_${Date.now()}`;

    setTurns((t) => [
      ...t,
      { id: userId, role: 'user', content: query },
      { id: assistantId, role: 'assistant', content: '', loading: true },
    ]);
    setInput('');
    setSubmitting(true);

    try {
      const response = await aiClient.supervisor.query({ query });
      const answerText = extractAnswerText(response);

      setTurns((t) =>
        t.map((x) =>
          x.id === assistantId
            ? { ...x, content: answerText, response, loading: false }
            : x
        )
      );
    } catch (e) {
      setTurns((t) =>
        t.map((x) =>
          x.id === assistantId
            ? { ...x, content: '', loading: false, error: (e as Error).message }
            : x
        )
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 200px)', minHeight: '500px' }}>
      {/* Message list */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-2 py-4 flex flex-col gap-4">
          {turns.length === 0 ? (
            <ChatEmptyState onSuggest={(q) => { setInput(q); handleSubmit(q); }} />
          ) : (
            turns.map((turn) => <MessageBubble key={turn.id} turn={turn} />)
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Sticky input */}
      <ChatInput
        value={input}
        onChange={setInput}
        onSubmit={handleSubmit}
        disabled={submitting}
      />
    </div>
  );
}
