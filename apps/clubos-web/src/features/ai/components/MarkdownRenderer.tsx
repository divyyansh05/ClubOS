import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function MarkdownRenderer({ content }: { content: string }) {
  return (
    <div className="markdown-body font-body text-sm leading-relaxed">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="font-headline text-xl tracking-tight mt-4 mb-2 first:mt-0">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="font-headline text-lg tracking-tight mt-3 mb-2 first:mt-0">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="font-body font-semibold text-base mt-3 mb-1 first:mt-0">{children}</h3>
          ),
          p: ({ children }) => (
            <p className="mb-2 last:mb-0">{children}</p>
          ),
          ul: ({ children }) => (
            <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="text-sm">{children}</li>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold">{children}</strong>
          ),
          code: ({ children, className }) => {
            const isBlock = className?.includes('language-');
            if (isBlock) {
              return (
                <pre className="bg-stone-100 dark:bg-stone-800 border border-stone-200 dark:border-stone-700 rounded p-3 my-2 overflow-x-auto">
                  <code className="font-mono text-xs">{children}</code>
                </pre>
              );
            }
            return (
              <code className="font-mono text-xs bg-stone-100 dark:bg-stone-800 px-1 rounded">{children}</code>
            );
          },
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-stone-300 dark:border-stone-600 pl-3 my-2 text-stone-600 dark:text-stone-400 italic">
              {children}
            </blockquote>
          ),
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-info-light dark:text-info-dark underline hover:opacity-80 transition-opacity"
            >
              {children}
            </a>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-2">
              <table className="data-table w-full text-xs">{children}</table>
            </div>
          ),
          th: ({ children }) => (
            <th className="px-2 py-1 text-left font-mono uppercase tracking-wider text-stone-500 dark:text-stone-400">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-2 py-1">{children}</td>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
