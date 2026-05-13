import { NavLink } from "react-router-dom";
import type { PropsWithChildren } from "react";
import { useState, useEffect } from "react";

const navItems = [
  { to: "/priorities", label: "Board" },
  { to: "/command-center", label: "Center" },
  { to: "/benchmark", label: "Benchmark" },
  { to: "/signals", label: "Signals" },
  { to: "/briefing", label: "Briefing" }
];

export function PageShell({ children }: PropsWithChildren) {
  const [isDark, setIsDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return document.documentElement.classList.contains('dark');
    }
    return false;
  });

  useEffect(() => {
    // Initialize dark mode from localStorage or system preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const shouldBeDark = savedTheme === 'dark' || (!savedTheme && prefersDark);

    if (shouldBeDark) {
      document.documentElement.classList.add('dark');
      setIsDark(true);
    } else {
      document.documentElement.classList.remove('dark');
      setIsDark(false);
    }
  }, []);

  const toggleTheme = () => {
    const newIsDark = !isDark;
    setIsDark(newIsDark);

    if (newIsDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  };

  // Get current month/year for edition
  const now = new Date();
  const edition = now.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

  return (
    <div className="min-h-screen bg-paper dark:bg-stone-900 text-ink dark:text-stone-100">
      {/* Header - newspaper masthead inspired */}
      <header className="border-b-2 border-ink dark:border-stone-700 bg-paper/95 dark:bg-stone-900/95 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-screen-xl mx-auto px-6">
          {/* Top metadata bar */}
          <div className="py-2 border-b border-stone-300 dark:border-stone-700 flex items-center justify-between">
            <div className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400">
              Vol. 1.0 · Edition: {edition}
            </div>
            <button
              onClick={toggleTheme}
              className="font-mono text-[10px] uppercase tracking-widest hover:text-info-light dark:hover:text-info-dark transition-colors"
              aria-label="Toggle theme"
            >
              <span className="dark:hidden">Dark</span>
              <span className="hidden dark:inline">Light</span>
            </button>
          </div>

          {/* Main header */}
          <div className="py-6 flex items-center justify-between">
            <NavLink to="/priorities" className="cursor-pointer">
              <h1 className="font-headline text-4xl md:text-5xl tracking-tight">ClubOS</h1>
              <p className="font-mono text-[10px] uppercase tracking-widest text-stone-500 dark:text-stone-400 mt-1">
                Monthly digital business operating system
              </p>
            </NavLink>

            {/* Navigation */}
            <nav className="hidden md:flex gap-8 font-sans text-sm">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `uppercase tracking-wider hover:text-info-light dark:hover:text-info-dark transition-colors ${
                      isActive
                        ? 'border-b-2 border-ink dark:border-stone-300 pb-1'
                        : ''
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main>{children}</main>
    </div>
  );
}
