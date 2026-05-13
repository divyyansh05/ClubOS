import { useState, useEffect } from "react";

const STORAGE_KEY = "clubos_welcome_dismissed";

export function WelcomeBanner() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Check if banner has been dismissed
    const dismissed = localStorage.getItem(STORAGE_KEY);
    if (!dismissed) {
      setIsVisible(true);
    }
  }, []);

  const dismiss = () => {
    localStorage.setItem(STORAGE_KEY, "true");
    setIsVisible(false);
  };

  const scrollToGuide = () => {
    dismiss();
    // Scroll to the guide section at the bottom of the page
    const guideElement = document.querySelector('[data-screen-guide]');
    if (guideElement) {
      guideElement.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div className="border-b-2 border-ink dark:border-stone-700 bg-stone-50 dark:bg-stone-800 p-6 animate-fade-in">
      <div className="max-w-screen-xl mx-auto relative">
        {/* Close button */}
        <button
          onClick={dismiss}
          className="absolute top-0 right-0 w-8 h-8 flex items-center justify-center text-stone-500 dark:text-stone-400 hover:text-stone-700 dark:hover:text-stone-200 transition-colors"
          aria-label="Close welcome banner"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Content */}
        <div className="pr-10">
          <h2 className="font-headline text-3xl mb-3 text-ink dark:text-stone-100">
            Welcome to ClubOS
          </h2>
          <p className="font-body text-base text-stone-700 dark:text-stone-300 leading-relaxed mb-4 max-w-3xl">
            This is your monthly digital business operating system. Every month when new data is uploaded,
            ClubOS automatically analyses 52 metrics across four platforms and ranks the issues and
            opportunities that matter most commercially. Start with the Priority Board — rank #1 is where
            to focus first. Use the <span className="inline-flex items-center justify-center w-4 h-4 mx-1 rounded-full border border-stone-400 dark:border-stone-500 font-mono text-xs">?</span> icons
            throughout the app to understand any metric, chart, or number in plain English.
          </p>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={dismiss}
              className="px-6 py-3 bg-ink dark:bg-stone-700 text-paper dark:text-stone-100 font-mono text-sm uppercase tracking-widest hover:bg-stone-800 dark:hover:bg-stone-600 transition-colors border-2 border-ink dark:border-stone-600"
            >
              Got it, start exploring
            </button>
            <button
              onClick={scrollToGuide}
              className="px-6 py-3 border-2 border-ink dark:border-stone-600 text-ink dark:text-stone-100 font-mono text-sm uppercase tracking-widest hover:bg-stone-100 dark:hover:bg-stone-700 transition-colors flex items-center gap-2"
            >
              <span>How does this work?</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
