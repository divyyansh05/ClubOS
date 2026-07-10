import { ErrorBoundary } from 'react-error-boundary';
import type { FallbackProps } from 'react-error-boundary';
import type { ReactNode } from 'react';

function AIErrorFallback({ error: rawError, resetErrorBoundary }: FallbackProps) {
  const error = rawError instanceof Error ? rawError : new Error(String(rawError));
  return (
    <div className="max-w-screen-xl mx-auto px-6 py-16 text-center space-y-6">
      <div className="space-y-2">
        <p className="font-mono text-[10px] uppercase tracking-widest text-critical-light dark:text-critical-dark">
          AI section error
        </p>
        <h2 className="font-headline text-2xl tracking-tight">Something went wrong</h2>
        <p className="font-body text-sm text-stone-500 dark:text-stone-400 max-w-md mx-auto">
          The AI section encountered an unexpected error. The rest of ClubOS is unaffected.
        </p>
      </div>

      <pre className="inline-block text-left bg-stone-50 dark:bg-stone-800 border border-stone-200 dark:border-stone-700 px-4 py-3 font-mono text-xs text-critical-light dark:text-critical-dark max-w-lg overflow-x-auto">
        {error.message}
      </pre>

      <div>
        <button
          onClick={resetErrorBoundary}
          className="font-mono text-xs uppercase tracking-wider px-4 py-2 border-2 border-ink dark:border-stone-300 hover:bg-ink hover:text-paper dark:hover:bg-stone-300 dark:hover:text-stone-900 transition-colors"
        >
          Try again
        </button>
      </div>
    </div>
  );
}

export function AIErrorBoundary({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary FallbackComponent={AIErrorFallback}>
      {children}
    </ErrorBoundary>
  );
}
