import { NavLink } from "react-router-dom";
import type { PropsWithChildren } from "react";
import { useState, useEffect } from "react";
import { fetchUnconfirmedAnomalies } from "../../lib/api";

const navItems = [
  { to: "/priorities", label: "Board" },
  { to: "/command-center", label: "Center" },
  { to: "/benchmark", label: "Benchmark" },
  { to: "/signals", label: "Signals" },
  { to: "/events", label: "Events" },
  { to: "/social", label: "Social" },
  { to: "/connectors", label: "Connectors" },
  { to: "/briefing", label: "Briefing" },
  { to: "/upcoming", label: "Upcoming" }
];

export function PageShell({ children }: PropsWithChildren) {
  const [isDark, setIsDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return document.documentElement.classList.contains('dark');
    }
    return false;
  });

  // V1.6.5 — Track unconfirmed anomaly count for notification badge
  const [anomalyCount, setAnomalyCount] = useState(0);

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

  // V1.6.5 — Load unconfirmed anomaly count for badge
  useEffect(() => {
    async function loadAnomalyCount() {
      try {
        const data = await fetchUnconfirmedAnomalies();
        setAnomalyCount(data.total_count);
      } catch (err) {
        console.error("Failed to load anomaly count:", err);
        // Non-blocking — just don't show badge
      }
    }

    loadAnomalyCount();

    // Refresh every 5 minutes
    const interval = setInterval(loadAnomalyCount, 5 * 60 * 1000);
    return () => clearInterval(interval);
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
                  <span className="relative">
                    {item.label}
                    {/* V1.6.5 — Notification badge for Events */}
                    {item.to === "/events" && anomalyCount > 0 && (
                      <span className="absolute -top-2 -right-4 bg-amber-500 text-white text-[10px] font-bold rounded-full h-4 w-4 flex items-center justify-center">
                        {anomalyCount}
                      </span>
                    )}
                  </span>
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
