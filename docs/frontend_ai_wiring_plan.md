# Frontend AI Wiring — Discovery Notes

## Stack detected
- Framework: React 18.3.1, TypeScript 5.5.4, Vite 5.4.21
- Routing: react-router-dom v6.30.3 (BrowserRouter, client-side)
- Data fetching: useState + useEffect + fetch (no React Query / SWR / Zustand)
- Styling: Tailwind CSS v3.4.19, class-based dark mode (`darkMode: 'class'`)
- Component library: Custom (Recharts for charts only, no shadcn/ui / MUI / Chakra)

## Key files
- Routes: `apps/clubos-web/src/app/App.tsx`
- Nav + shell: `apps/clubos-web/src/components/ui/PageShell.tsx`
- API client: `apps/clubos-web/src/lib/api.ts`
- Types: `apps/clubos-web/src/types/clubos.ts`, `src/types/events.ts`
- Global styles: `apps/clubos-web/src/styles/global.css`
- Tailwind config: `apps/clubos-web/tailwind.config.js`
- Vite config: `apps/clubos-web/vite.config.ts`

## Design tokens (from UIUX.md)

### Primary color
- `sport-blue-500`: `#3B82F6` (primary brand blue)
- `sport-blue-600`: `#2563EB` (link hover, nav active)
- `sport-blue-900`: `#1E3A8A` (deep navy, header gradient start)

### Semantic colors
| State | Light mode | Dark mode |
|-------|-----------|-----------|
| Critical / error | `#DC2626` | `#EF4444` |
| Warning | `#EA580C` | `#F97316` |
| Info | `#2563EB` | `#3B82F6` |
| Good / success | `#16A34A` | `#22C55E` |
| Accent / benchmark | `#9333EA` | `#A855F7` |

### Tailwind class mapping
- critical: `text-critical-light dark:text-critical-dark`, `bg-critical-50`
- warning: `text-warning-light dark:text-warning-dark`, `bg-warning-50`
- info/scout: `text-info-light dark:text-info-dark`, `bg-info-50`
- good/briefer: `text-good-light dark:text-good-dark`, `bg-good-50`
- accent/investigator: `text-accent-light dark:text-accent-dark`, `bg-accent-50`

### Typography
| Role | Family | Weight | Tailwind |
|------|--------|--------|---------|
| Headlines | DM Serif Display | 400 | `font-headline tracking-tight` |
| Body | IBM Plex Serif | 400, 600, 700 | `font-body` |
| UI/Nav | Inter | 400–700 | `font-sans` |
| Numbers/code | JetBrains Mono | 400–600 | `font-mono` |

Rules:
- All numbers/scores: always `font-mono`
- Nav items: `font-sans text-sm uppercase tracking-wider`
- Metadata bar: `font-mono text-[10px] uppercase tracking-widest`

### Spacing
- Standard card padding: `p-6` (24px)
- Grid gaps: `gap-4` (16px)
- Page content: `px-6 py-8`
- Max width: `max-w-screen-xl mx-auto`

### Border / radius conventions
- Cards: `border-2 border-ink dark:border-stone-700` — square corners preferred
- Max border radius: `rounded` (4px); most elements have no rounding
- Table: `.data-table` CSS class (collapse + 1px borders on all cells)
- Badges/pills: `rounded-full px-3 py-1 text-xs font-mono uppercase tracking-wider`

### Gradients (for AI dispatch badges)
- Scout (info): `bg-info-50 dark:bg-stone-800 text-info-light dark:text-info-dark`
- Investigator (warning/accent): `bg-accent-50 dark:bg-stone-800 text-accent-light dark:text-accent-dark`
- Briefer (good): `bg-good-50 dark:bg-stone-800 text-good-light dark:text-good-dark`
- Supervisor (sport-blue): `bg-sport-blue-50 dark:bg-stone-800 text-sport-blue-600 dark:text-sport-blue-400`
- Error (critical): `bg-critical-50 dark:bg-stone-800 text-critical-light dark:text-critical-dark`

## API configuration
- No Vite proxy configured — backend URL via `VITE_API_BASE_URL` env var
- Dev: `VITE_API_BASE_URL=http://localhost:8000` (in `.env.development`)
- Existing client pattern: `const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ""`
- Generic fetch: `fetchJson<T>(path)` in `src/lib/api.ts` — POST calls need wrapper

## Existing patterns to reuse
- `PageShell` wraps every page — reuse it; just add a new route in `App.tsx` and nav entry in `PageShell.tsx`
- Data fetch pattern: `useEffect(() => { async function load() { setLoading(true); try { ... } catch { setError(...) } finally { setLoading(false) } } load(); }, [])`
- Badge pill: `rounded-full px-3 py-1 text-xs font-mono uppercase tracking-wider bg-{semantic}-50 text-{semantic}-light`
- Notification badge (for header alerts count): `bg-amber-500 text-white text-[10px] font-bold rounded-full h-4 w-4 flex items-center justify-center`
- `MetricDetailModal` — glass-modal pattern (reuse for investigation detail if needed)
- Dark mode: always include `dark:` variant for all color classes

## Adding a nav item to PageShell
Add to `navItems` array in `apps/clubos-web/src/components/ui/PageShell.tsx` (lines 6-16):
```typescript
{ to: "/ai", label: "AI" }
```
NavLink active class: `border-b-2 border-ink dark:border-stone-300 pb-1`

## Actual backend endpoints (verified from router files)

### Supervisor
- `POST /api/ai/supervisor/query` → `SupervisorResponse`

### Watchdog
- `POST /api/ai/watchdog/run` body: `{ dedup_window_days?, top_n?, triggered_by? }` → `WatchdogRunResponse`
- `GET /api/ai/watchdog/alerts?limit&since_hours&metric_name&severity&run_id&unacknowledged_only` → `{ total, alerts: WatchdogAlertRead[], filters_applied }`
- `POST /api/ai/watchdog/alerts/{alert_id}/acknowledge` body: `{ acknowledged_by: string }` → `{ alert_id, acknowledged_at, acknowledged_by }`

### Investigator
- `POST /api/ai/investigator/run/{alert_id}` body: `{ triggered_by?, max_steps? }` → `InvestigateResponse`
- `GET /api/ai/investigator?limit&metric_name&status&alert_id` → `{ total, investigations: InvestigationRead[], filters_applied }`
- `GET /api/ai/investigator/{investigation_id}` → `InvestigationRead`

### Briefer
- `POST /api/ai/briefer/run_monthly?year_month=YYYY-MM` → `BriefingRunResult`
- `POST /api/ai/briefer/run` body: full `BriefingRunRequest` → `BriefingRunResult`
- `GET /api/ai/briefer?limit&briefing_type` → `BriefingRead[]`
- `GET /api/ai/briefer/{briefing_id}` → `BriefingRead`

## Files to add (Part 1)
- `src/features/ai/api/types.ts` — all TypeScript types matching Pydantic schemas
- `src/features/ai/api/endpoints.ts` — URL constants
- `src/features/ai/api/aiClient.ts` — HTTP client for all AI endpoints
- `src/features/ai/components/` — shared AI UI components (Part 3+)
- `src/features/ai/pages/` — route-level page components (Part 2+)
- `src/features/ai/hooks/` — custom hooks (Part 2+)

## Files NOT to modify
- Any existing v1 pages under `src/features/`
- `src/styles/global.css` (additive CSS only in AI-specific files)
- `src/types/clubos.ts` (AI types go in `src/features/ai/api/types.ts`)
- `tailwind.config.js` (use only existing tokens)
- `src/lib/api.ts` (AI client is self-contained in `src/features/ai/api/aiClient.ts`)

Exception: `src/app/App.tsx` and `src/components/ui/PageShell.tsx` get additive entries only (new route + new nav item). No restructuring.
