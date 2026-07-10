import { NavLink, Outlet } from 'react-router-dom';

const subNavItems = [
  { to: '/ai/chat', label: 'Chat' },
  { to: '/ai/alerts', label: 'Alerts' },
  { to: '/ai/investigations', label: 'Investigations' },
  { to: '/ai/briefings', label: 'Briefings' },
];

export function AILayout() {
  return (
    <section>
      {/* Section header */}
      <div className="border-b-2 border-ink dark:border-stone-700">
        <div className="max-w-screen-xl mx-auto px-6 pt-8 pb-0">
          <h2 className="font-headline text-3xl tracking-tight mb-4">AI Assistant</h2>

          {/* Sub-navigation tab bar */}
          <nav className="flex gap-8 font-sans text-sm" aria-label="AI section navigation">
            {subNavItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `uppercase tracking-wider pb-3 border-b-2 transition-colors ${
                    isActive
                      ? 'border-ink dark:border-stone-300 text-ink dark:text-stone-100'
                      : 'border-transparent text-stone-500 dark:text-stone-400 hover:text-info-light dark:hover:text-info-dark'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </div>

      {/* Page content */}
      <div className="max-w-screen-xl mx-auto px-6 py-8">
        <Outlet />
      </div>
    </section>
  );
}
