import { useRef, type KeyboardEvent } from 'react';

interface ChatInputProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: (query: string) => void;
  disabled: boolean;
}

export function ChatInput({ value, onChange, onSubmit, disabled }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !disabled) onSubmit(value);
    }
  }

  return (
    <div className="border-t-2 border-ink dark:border-stone-700 bg-paper dark:bg-stone-900 px-4 py-3">
      <div className="max-w-3xl mx-auto flex gap-3 items-end">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKey}
          disabled={disabled}
          rows={1}
          placeholder="Ask about metrics, alerts, investigations, or request a briefing…"
          className="flex-1 resize-none bg-transparent border-b-2 border-stone-300 dark:border-stone-600 focus:border-ink dark:focus:border-stone-300 outline-none py-1.5 font-body text-sm placeholder:text-stone-400 dark:placeholder:text-stone-500 transition-colors disabled:opacity-50"
          style={{ maxHeight: '8rem', overflowY: 'auto' }}
          onInput={(e) => {
            const el = e.currentTarget;
            el.style.height = 'auto';
            el.style.height = `${Math.min(el.scrollHeight, 128)}px`;
          }}
        />
        <button
          onClick={() => { if (value.trim() && !disabled) onSubmit(value); }}
          disabled={disabled || !value.trim()}
          className="font-mono text-xs uppercase tracking-wider px-4 py-2 border-2 border-ink dark:border-stone-300 hover:bg-ink hover:text-paper dark:hover:bg-stone-300 dark:hover:text-stone-900 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {disabled ? 'Thinking…' : 'Send'}
        </button>
      </div>
      <p className="max-w-3xl mx-auto mt-1 font-mono text-[10px] text-stone-400 dark:text-stone-500 tracking-wider">
        Enter to send · Shift+Enter for newline
      </p>
    </div>
  );
}
