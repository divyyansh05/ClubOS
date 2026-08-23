import { useState } from 'react';
import type { ReasoningStep } from '../api/types';

function truncate(s: string, n: number) {
  return s.length <= n ? s : s.slice(0, n).trimEnd() + '…';
}

function StepCard({ step, index }: { step: ReasoningStep; index: number }) {
  const [argsOpen, setArgsOpen] = useState(false);
  const [obsOpen, setObsOpen] = useState(false);

  const hasArgs = step.action_input && Object.keys(step.action_input).length > 0;
  const hasObs = step.observation && step.observation.length > 0;

  return (
    <li className="relative flex gap-4">
      {/* Timeline connector */}
      <div className="flex flex-col items-center">
        <div className="w-7 h-7 rounded-full border-2 border-ink dark:border-stone-600 bg-paper dark:bg-stone-900 flex items-center justify-center flex-shrink-0 z-10">
          <span className="font-mono text-[10px] font-bold">{index + 1}</span>
        </div>
        {/* Vertical line — hidden on last item via CSS */}
        <div className="w-px flex-1 bg-stone-200 dark:bg-stone-700 mt-1" />
      </div>

      {/* Content */}
      <div className="pb-6 flex-1 min-w-0">
        {/* Thought */}
        {step.thought && (
          <div className="mb-2">
            <span className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500">
              Thought
            </span>
            <p className="mt-0.5 font-body text-sm text-stone-600 dark:text-stone-300 italic">
              {step.thought}
            </p>
          </div>
        )}

        {/* Action */}
        <div className="mb-2 flex items-start gap-2 flex-wrap">
          <span className="font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500 mt-0.5">
            Tool
          </span>
          <code className="font-mono text-xs bg-stone-100 dark:bg-stone-800 border border-stone-200 dark:border-stone-700 px-2 py-0.5 text-ink dark:text-stone-100">
            {step.action}
          </code>
          {hasArgs && (
            <button
              onClick={() => setArgsOpen((v) => !v)}
              className="font-mono text-[10px] uppercase tracking-wider text-info-light dark:text-info-dark hover:opacity-70 transition-opacity"
            >
              {argsOpen ? 'hide args ▲' : 'args ▼'}
            </button>
          )}
        </div>
        {argsOpen && hasArgs && (
          <pre className="mb-2 bg-stone-50 dark:bg-stone-800 border border-stone-200 dark:border-stone-700 p-3 text-xs font-mono overflow-x-auto max-h-40 overflow-y-auto">
            {JSON.stringify(step.action_input, null, 2)}
          </pre>
        )}

        {/* Observation */}
        {hasObs && (
          <div>
            <button
              onClick={() => setObsOpen((v) => !v)}
              className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-stone-400 dark:text-stone-500 hover:text-ink dark:hover:text-stone-100 transition-colors"
            >
              <span className="text-stone-300 dark:text-stone-600">{obsOpen ? '▼' : '▶'}</span>
              Result
            </button>
            {obsOpen ? (
              <pre className="mt-1 bg-stone-50 dark:bg-stone-800 border border-stone-200 dark:border-stone-700 p-3 text-xs font-mono overflow-x-auto max-h-48 overflow-y-auto whitespace-pre-wrap">
                {step.observation}
              </pre>
            ) : (
              <p className="mt-0.5 font-mono text-xs text-stone-500 dark:text-stone-400">
                {truncate(step.observation, 120)}
              </p>
            )}
          </div>
        )}
      </div>
    </li>
  );
}

interface ReasoningTraceProps {
  trace: ReasoningStep[];
  traceUrl?: string | null;
}

export function ReasoningTrace({ trace, traceUrl }: ReasoningTraceProps) {
  if (!trace || trace.length === 0) {
    return (
      <div className="py-6 border border-dashed border-stone-200 dark:border-stone-700 text-center space-y-2">
        <p className="font-mono text-xs uppercase tracking-wider text-stone-400 dark:text-stone-500">
          No step-by-step trace recorded
        </p>
        {traceUrl ? (
          <p className="font-body text-sm text-stone-500 dark:text-stone-400">
            Full ReAct loop available in{' '}
            <a
              href={traceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-info-light dark:text-info-dark underline hover:opacity-70 transition-opacity"
            >
              LangSmith trace →
            </a>
          </p>
        ) : (
          <p className="font-body text-sm text-stone-500 dark:text-stone-400">
            This investigation ran before step-level tracing was enabled, or was seeded as eval data.
          </p>
        )}
      </div>
    );
  }

  return (
    <ol className="space-y-0 [&>li:last-child>div:first-child>div:last-child]:hidden">
      {trace.map((step, i) => (
        <StepCard key={step.step_number ?? i} step={step} index={i} />
      ))}
    </ol>
  );
}
