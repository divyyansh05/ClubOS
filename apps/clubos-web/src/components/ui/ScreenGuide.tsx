import { useState } from "react";

interface GuideSection {
  title: string;
  content: string;
}

interface ScreenGuideProps {
  screenName: string;
  sections: GuideSection[];
}

export function ScreenGuide({ screenName, sections }: ScreenGuideProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <section className="border-t-2 border-stone-300 dark:border-stone-700 mt-12 pt-6">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-3 font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400 hover:text-stone-700 dark:hover:text-stone-300 transition-colors cursor-pointer group"
      >
        <span className="inline-flex items-center justify-center w-5 h-5 rounded-full border border-stone-400 dark:border-stone-500 group-hover:border-stone-600 dark:group-hover:border-stone-300 transition-colors">
          <span className="font-sans text-sm">ⓘ</span>
        </span>
        <span>How to read this screen</span>
        <svg
          className={`w-4 h-4 transition-transform ${isExpanded ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isExpanded && (
        <div className="mt-6 border-2 border-stone-300 dark:border-stone-700 p-6 animate-fade-in bg-stone-50 dark:bg-stone-800">
          <h3 className="font-headline text-2xl mb-6 text-ink dark:text-stone-100">
            Understanding the {screenName}
          </h3>

          <div className="space-y-6">
            {sections.map((section, index) => (
              <div key={index}>
                <h4 className="font-body text-lg font-bold mb-2 text-ink dark:text-stone-100">
                  {section.title}
                </h4>
                <p className="font-body text-base text-stone-700 dark:text-stone-300 leading-relaxed">
                  {section.content}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 border border-stone-300 dark:border-stone-700 bg-paper dark:bg-stone-900">
            <p className="font-mono text-xs text-stone-600 dark:text-stone-400">
              <strong className="text-ink dark:text-stone-100">Tip:</strong> Click the [?] icons next to
              any metric name throughout the app to see its definition, formula, and what the numbers mean.
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
