---
# ClubOS — Application Flow Document
**Version**: 2.0
**Status**: Production MVP deployed on Cloud Run
**Date**: 2026-05-14
---

## 1. Application Entry Point

URL: `http://localhost:5176`

The root path `/` immediately redirects to `/priorities` via a `<Navigate replace />` React Router declaration. The user never sees a splash screen, login, or landing page — they land directly on the Priority Board.

On first visit, a WelcomeBanner renders above the Priority Board content. On subsequent visits the banner is suppressed (localStorage key `clubos_welcome_dismissed` is set).

The app wraps all routes in `BrowserRouter` (HTML5 history API, clean URLs without `#`). All pages render inside `PageShell`, which provides the sticky header with navigation and theme toggle. The `main` element below the header renders the active page component.

Theme initialises from localStorage key `theme`. If no saved preference, falls back to the system `prefers-color-scheme` media query. The `dark` class is applied to `document.documentElement`.

---

## 2. Navigation Structure

The sticky header is divided into two rows:

**Top metadata bar** (always visible):
- Left: `Vol. 1.0 · Edition: [current month year]` — read-only, generated from the current date at render time
- Right: **Theme toggle button** — switches between Dark and Light mode

**Main header row**:
- Left: `ClubOS` wordmark (NavLink) — clicking navigates to `/priorities`
- Right: Eight navigation links

| Nav Label | Route | Default Active? |
|-----------|-------|----------------|
| Board | `/priorities` | Yes (default landing) |
| Center | `/command-center` | No |
| Benchmark | `/benchmark` | No |
| Signals | `/signals` | No |
| Briefing | `/briefing` | No |
| Social | `/social` | No |
| Events | `/events` | No |
| Connectors | `/connectors` | No |

Active state: the current route's nav link gets `border-b-2 border-ink` underline treatment. Hover state applies `text-info-light` (blue tint). Navigation is hidden on mobile (md breakpoint) — mobile navigation is not built in V1.

---

## 3. Screen Flows

### 3.1 Priority Board (`/priorities`)

**Purpose**: Surface the top 10 commercially ranked issues and opportunities for the latest month, with transparent evidence trails for each.

**On load**:
- Calls `GET /priorities/latest` via `getLatestPriorities()`
- Renders `latestMonth` string (e.g. `2026-01-01`) formatted as `"January 2026"` in the hero
- Renders four summary filter cards (Critical count, Opportunity count, Benchmark count, Total)
- Renders all priority cards in a 2-column grid, ordered by rank
- WelcomeBanner renders above the hero if `clubos_welcome_dismissed` is not set in localStorage
- `activeFilter` defaults to `"all"` — all cards are shown

**User actions**:

| Action | Result |
|--------|--------|
| Click **Critical** summary card | Filters grid to cards whose `category` includes `"critical"`. Card gets `ring-2 ring-critical` active state + checkmark badge. Clicking again (toggle) returns to all |
| Click **Opportunity** summary card | Filters to `"opportunity"` category. Toggle behavior same as above |
| Click **Benchmark** summary card | Filters to `"benchmark"` category. Toggle behavior same as above |
| Click **Total Priorities** summary card | Resets `activeFilter` to `"all"`, shows all cards |
| Click any **priority card** (anywhere on card body) | Calls `GET /priorities/{priority_id}` → sets `selectedDetail` state → opens the Priority Evidence Modal |
| Click **"View Evidence"** button on card | Same as clicking the card body — opens Priority Evidence Modal for that priority |
| Click **"Open Analytics Dashboard"** inside modal | Navigates to `/command-center` and closes modal |
| Click **"View Peer Benchmark"** inside modal | Navigates to `/benchmark` (modal stays open — user must also close manually or modal closes on navigation) |
| Click **X** button in modal header | Closes modal (`selectedDetail` → null) |
| Click **modal backdrop** (outside modal) | Closes modal |
| Click **WelcomeBanner "Got it, start exploring"** | Sets `clubos_welcome_dismissed` in localStorage, hides banner |
| Click **WelcomeBanner "How does this work?"** | Sets `clubos_welcome_dismissed`, hides banner, smooth-scrolls to `[data-screen-guide]` element |
| Click **WelcomeBanner X** | Sets `clubos_welcome_dismissed` in localStorage, hides banner |
| Click **ScreenGuide "How to read this screen"** | Toggles expanded state, reveals/hides 5-section FAQ panel |
| Click **InfoTooltip [?]** next to metric name on a card | Opens InfoTooltip popover with metric definition, formula, example, polarity note |

**Priority Evidence Modal** (opens over the Priority Board; z-index 50):

Triggered by: clicking any priority card or its "View Evidence" button.

If `detailLoading` is true: shows "Loading detail..." inside the modal.

When detail loads, modal shows:
- **Header** (sticky): Priority title, rank badge, asset + metric label, score explanation banner explaining the 5-component formula
- **12-Month Trend Chart**: Recharts `LineChart`, line colour red (down) / green (up) / grey (stable), dashed blue reference line at 6-month average, yellow `ReferenceArea` highlighting the last 3 months, animated pulse dot on the most recent data point. If `historical_values` is empty: shows "Historical data unavailable" placeholder
- **Peer Benchmark Bar Chart** (horizontal): Recharts `BarChart` sorted by value descending, Real Madrid bar in purple (`#9333EA`), peers in grey, dashed blue line at peer median, dashed green line at market leader. Gap annotation below chart shows gap to median and gap to leader with colour-coded sign. If `peer_values` has fewer than 2 entries: shows "Peer benchmark data unavailable"
- **Overview grid**: Category · Score · Rank · Month
- **Why It Matters**: plain-English explanation text
- **Detailed Analysis**: `summary_text` from API
- **Score Breakdown**: stacked horizontal colour bar + table with 5 rows (Severity 30%, Persistence 25%, Peer Gap 20%, Commercial 15%, Evidence 10%), each row has an InfoTooltip [?] explaining the component, includes "Your Score" and "Max Possible" columns with TOTAL row
- **Supporting Evidence table**: up to 5 supporting metrics with name, value, status
- **Competitive Context grid**: key-value pairs from `supporting_metrics.peer_context` (when present)
- **Recommended Next Steps**: `suggested_next_investigation` text + two buttons ("Open Analytics Dashboard →" and "View Peer Benchmark")

**States**:
- Loading state: "Loading latest priorities..." centred text
- Error state: "Error Loading Priorities" headline + error message in red
- Empty state: no priorities renders an empty grid (no explicit empty message in current code)
- Detail loading state: "Loading detail..." inside open modal
- Filter active state: summary card gets `ring-2` highlight + checkmark badge; filtered cards shown, others hidden

---

### 3.2 Command Center (`/command-center`)

**Purpose**: Show the monthly health status of all 59 tracked metrics across the four digital platforms in one consolidated view.

**On load**:
- Calls `GET /health/summary` via `getHealthSummary()`
- Renders four summary stat cards (Total Metrics, Good Health, Review Needed, Stable Status)
- Renders health distribution donut chart (Recharts `PieChart`) with three slices: Good (green), Review (orange), Stable (blue)
- Renders three horizontal progress bar cards below the donut
- Renders the Overall Deviation Index section (large number, clickable)

**User actions**:

| Action | Result |
|--------|--------|
| Click **Total Metrics** card | Opens `MetricDetailModal` — "Total Metrics Tracked" with breakdown of good/review/stable counts |
| Click **Good Health** card | Opens `MetricDetailModal` — explains good health %, count, and what it means |
| Click **Review Needed** card | Opens `MetricDetailModal` — explains review count, %, and how it feeds Priority Board |
| Click **Stable Status** card | Opens `MetricDetailModal` — explains stable count and business interpretation |
| Click **Good Health %** progress bar (below donut) | Opens `MetricDetailModal` — good health percentage with industry benchmark context |
| Click **Review Needed %** progress bar | Opens `MetricDetailModal` — review percentage with action guidance |
| Click **Stable %** progress bar | Opens `MetricDetailModal` — stable percentage with context |
| Click **Deviation Index** large number | Opens `MetricDetailModal` — "Average Absolute Deviation" explanation with interpretation of what the decimal value means |
| Close `MetricDetailModal` (X or backdrop) | Closes modal, returns to Command Center view |
| Click **InfoTooltip [?]** next to "Good Health Status" label | Shows definition, example, polarity note in popover |
| Click **InfoTooltip [?]** next to "Review Needed" label | Shows definition, example |
| Click **InfoTooltip [?]** next to "Stable Status" label | Shows definition, example |
| Click **InfoTooltip [?]** next to "Ecosystem Deviation Index" heading | Shows formula, example, polarity interpretation |
| Click **ScreenGuide** | Toggles 4-section FAQ panel |

**States**:
- Loading state: "Loading digital ecosystem health..." in bordered box
- Error state: "Error:" + message in red
- Empty state (no healthSummary): "No health data available."

---

### 3.3 Peer Benchmark (`/benchmark`)

**Purpose**: Compare Real Madrid's performance against five peer clubs on eight benchmarked KPIs, with 12-month trend history and gap analysis.

**On load**:
- Default selected metric: `ecommerce:conversion_rate` (hardcoded default in `useState`)
- Calls `GET /benchmark/ecommerce/conversion_rate` via `getBenchmark(asset, metric)`
- Renders metric selector dropdown, current position panel, 12-month trend chart, recent trend table (last 6 months)

**Available metrics in selector** (8 total):
1. Website - Unique Visitors (`main_website / unique_visitors`)
2. Website - Bounce Rate (`main_website / bounce_rate`)
3. eCommerce - Conversion Rate (`ecommerce / conversion_rate`) ← default
4. eCommerce - Net Sales (`ecommerce / net_sales`)
5. eCommerce - Cart Value (`ecommerce / cart_value`)
6. Streaming - Subscriptions (`streaming / subscriptions`)
7. Streaming - Subscription Rate (`streaming / subscription_rate`)
8. Fan App - Downloads (`fan_app / app_downloads`)

**User actions**:

| Action | Result |
|--------|--------|
| Change **metric selector dropdown** | Sets `selectedMetric` state → triggers `useEffect` → calls `GET /benchmark/{asset}/{metric}` → rerenders all panels with new data |
| Click **rank value** (e.g. "#4 out of 6 clubs") | Opens `MetricDetailModal` with current rank, club count, gap to leader, gap to median in additionalInfo |
| Click **current metric value** (large coloured number) | Opens `MetricDetailModal` with RM value, peer median, peer leader, 12-month trend sparkline |
| Click **"Gap to Median"** stat card | Opens `MetricDetailModal` explaining the gap, whether RM is behind or ahead |
| Click **"Gap to Leader"** stat card | Opens `MetricDetailModal` explaining gap to market leader |
| Click **any row** in Recent Trend table | Opens `MetricDetailModal` for that specific month — shows RM value, peer median, gap, rank for that month |
| Hover **chart line** | Recharts tooltip shows month label + RM / Peer Median / Leader values |
| Click **InfoTooltip [?]** next to selector label | Shows definition, formula, polarity note for selected metric |
| Click **InfoTooltip [?]** next to "12-Month Trend" heading | Same tooltip for selected metric |
| Close `MetricDetailModal` | Returns to Peer Benchmark view |
| Click **ScreenGuide** | Toggles 4-section FAQ panel |

**Position scale diagram** (visual only, not clickable): Displays four position icons in a horizontal row — Leader (rank 1 value), Median (M value), Real Madrid (rank badge with colour), Last Place. Rank badge colour: rank 1-2 = green, rank 3 = blue, Real Madrid's rank = highlighted in critical red if rank > 2 with white text.

**12-Month Trend Chart**: Three lines — Real Madrid (red, `#EF4444`), Peer Median (blue, `#3B82F6`), Leader (green, `#22C55E`). Gap annotation paragraph below chart updates dynamically to describe whether RM is ahead or behind the median and leader for the latest month.

**States**:
- Loading state: "Loading benchmark data..."
- Error state: "Error:" + message in red
- Empty state (no data): "No benchmark data available for this metric."

---

### 3.4 Signal Engine (`/signals`)

**Purpose**: Display 2-3 validated leading indicators that predict future commercial outcomes 1-3 months in advance.

**On load**:
- Calls `GET /signals` via `getSignals()`
- Sets `selectedSignal` to `items[0]` automatically (first signal expanded by default)
- Renders 4 summary stat cards (Validated Signals, Active Status, Avg Lead Time, Avg Strength)
- Renders signal cards in a single-column grid
- Renders signal validation notes section (methodology table + criteria list)

**User actions**:

| Action | Result |
|--------|--------|
| Click **Validated Signals** summary card | Opens `MetricDetailModal` — explains count, active vs total, last validated date |
| Click **Active Status** summary card | Opens `MetricDetailModal` — explains active vs total, active rate %, firing vs monitoring count |
| Click **Avg Lead Time** summary card | Opens `MetricDetailModal` — explains avg lag, min/max lag, planning window concept |
| Click **Avg Strength** summary card | Opens `MetricDetailModal` — explains avg strength %, strongest/weakest signal, 60% threshold |
| Click **signal card** (anywhere on card body) | Sets `selectedSignal` to that signal → expands Business Interpretation panel + Priority Connection panel inside that card. Previous selection collapses. Cards are not modals — the detail panel is inline within the card |
| Click **Strength** stat button inside signal card | Opens `MetricDetailModal` — explains strength score, formula, reliability at this %. Uses `e.stopPropagation()` so does not also trigger card selection |
| Click **Lag Time** stat button inside signal card | Opens `MetricDetailModal` — explains lag months, planning window, how to use lead time. Uses `e.stopPropagation()` |
| Click **Direction** stat button inside signal card | Opens `MetricDetailModal` — explains positive vs negative correlation, business interpretation. Uses `e.stopPropagation()` |
| Click **InfoTooltip [?]** next to "Validated Signals" label | Shows definition + example |
| Click **InfoTooltip [?]** next to "Active Status" label | Shows definition + example of inactive signal |
| Click **InfoTooltip [?]** next to "Strength" label inside signal | Shows formula, Pearson r interpretation, "higher is better" polarity |
| Click **InfoTooltip [?]** next to source metric name | Shows metric definition |
| Click **InfoTooltip [?]** next to target metric name | Shows metric definition |
| Close `MetricDetailModal` | Returns to Signal Engine view |
| Click **ScreenGuide** | Toggles 3-section FAQ panel |

**Signal card anatomy** (for the selected/expanded signal):
- Status banner at top: green if `firing_positive` (▲ source rising, target expected to rise), red if `firing_negative` (▼ source declining, target expected to decline), grey if `neutral` or `unknown`
- Flow diagram: Source panel (asset, metric, current value, trend % change) → arrow with lag label → Target panel (asset, metric, current value, health status badge)
- Stats grid: Strength gauge bar (threshold marker at 60%), Lag Time, Direction badge
- Business Interpretation section (expanded only): plain-English text, source asset, target asset, last validated month
- Priority Board Connection (if `priority_connection` present): contextual interpretation of how this signal relates to current priorities

**States**:
- Loading state: "Loading validated signals..."
- Error state: "Error:" + message in red
- Empty state: "No validated signals found."

---

### 3.5 Monthly Briefing (`/briefing`)

**Purpose**: Auto-generated executive summary combining top priorities, notable anomalies, leading signals, peer benchmark position, and ecosystem health into one leadership-ready monthly report.

**On load**:
- Calls `GET /briefing/latest` via `getLatestBriefing()`
- Renders all sections sequentially: Key Takeaways → Top 3 Priorities → Notable Anomalies → Top Signals → Benchmark Summary → Ecosystem Health Donut + Stats → Usage Guidance

**User actions**:

| Action | Result |
|--------|--------|
| Click **priority card** (top 3 section) | Opens `MetricDetailModal` — priority rank, score, category, business context |
| Click **anomaly table row** | Opens `MetricDetailModal` — metric name, current value, deviation %, asset, declining/surging status |
| Click **signal card** (top signals section) | Opens `MetricDetailModal` — source→target, strength, lag, direction, source/target asset details |
| Click **Benchmarked Metrics** stat | Opens `MetricDetailModal` — benchmarked count, underperformance count, underperformance rate |
| Click **Underperformances** stat | Opens `MetricDetailModal` — underperforming count, avg gap, worst gap |
| Click **Avg Gap to Median** stat | Opens `MetricDetailModal` — avg gap value, worst gap, whether RM is above/below peers |
| Click **Worst Gap** stat | Opens `MetricDetailModal` — worst single gap, whether it's biggest weakness or strength |
| Click **Total Metrics** health stat | Opens `MetricDetailModal` — total count with good/review/stable breakdown |
| Click **Good Health** health stat | Opens `MetricDetailModal` — good count, health percentage, business context |
| Click **Needs Review** health stat | Opens `MetricDetailModal` — review count, review percentage, action guidance |
| Click **Stable** health stat | Opens `MetricDetailModal` — stable count, stable percentage, context |
| Click **InfoTooltip [?]** next to "Good Health" health label | Shows definition of Good Health status |
| Click **InfoTooltip [?]** next to "Needs Review" label | Shows definition of Review Needed |
| Click **InfoTooltip [?]** next to "Stable" label | Shows definition of Stable |
| Click **InfoTooltip [?]** next to anomaly metric names | Shows metric definition |
| Click **InfoTooltip [?]** next to signal metric names | Shows metric definition |
| Close `MetricDetailModal` | Returns to Monthly Briefing view |
| Click **ScreenGuide** | Toggles 4-section FAQ panel |

**Ecosystem health donut chart**: Visual only — hovering shows Recharts tooltip with count per status. Not clickable as a whole; individual stats below the chart are clickable.

**States**:
- Loading state: "Loading monthly briefing..."
- Error state: "Error:" + message in red
- Empty state (no briefing or no `month`): "No briefing data available."

---

### 3.6 Social Intelligence (`/social`)

**Purpose**: Analyze unified social media performance across platforms, tracking 7 specific metrics such as engagement, impressions, and followers.

**On load**:
- Calls `GET /analytics/seasonal?asset=social`
- Renders total metrics summary and charts for social activity.
- Visualizes platform-level breakdowns and trends.

---

### 3.7 Event Calendar (`/events`)

**Purpose**: Manage real-world context (match days, kit launches) that suppress anomalies or explain spikes.

**On load**:
- Calls `GET /events`
- Displays list of configured events, their date ranges, and categories.
- User can interact to filter events by `match`, `campaign`, or `external`.
- Events defined here are rendered as `⚡` annotations on charts across the platform.

---

### 3.8 Connectors (`/connectors`)

**Purpose**: Manage data ingestion plugins, verify credentials, and test Slack notification alerts.

**On load**:
- Calls `GET /connectors/status`
- Displays dynamic grid of all registered integrations (e.g. YouTube Data API, Wikipedia, Slack).
- Status badge shows `Connected`, `Not Configured`, or `Error`.

**User actions**:
- Click **"Test Alert"** on Slack connector: Calls `POST /notifications/test-slack` to fire a sample priority shift alert to the configured channel.

---

## 4. Global Elements

### 4.1 Navigation Bar

Present on every page via `PageShell`. Sticky (`position: sticky; top: 0; z-index: 40`).

Two visual rows:
1. Metadata bar: edition string + theme toggle
2. Brand + nav links

Active route detection: React Router's `NavLink` `isActive` prop adds `border-b-2 border-ink` underline to the active link. Non-active links show on hover with `text-info-light` tint.

ClubOS wordmark is a `NavLink to="/priorities"` — clicking from any screen navigates to Priority Board.

### 4.2 Theme Toggle (Light/Dark)

**Location**: Top-right of the header metadata bar, labelled "Dark" (in light mode) or "Light" (in dark mode) — the label shows what clicking will switch TO.

**Initialisation order**:
1. Read `localStorage.getItem('theme')`
2. If no saved key, check `window.matchMedia('(prefers-color-scheme: dark)').matches`
3. Apply `dark` class to `document.documentElement` accordingly

**On click**:
- Toggles `isDark` React state
- Adds or removes `.dark` class from `document.documentElement`
- Writes `"dark"` or `"light"` to `localStorage.setItem('theme', ...)`
- All Tailwind `dark:` variants update immediately (CSS class-based)

**Persistence**: Survives page reload via localStorage. Survives tab navigation. Does not sync across tabs in real time.

### 4.3 InfoTooltip System

**Component**: `InfoTooltip.tsx` at `src/components/ui/InfoTooltip.tsx`

**Trigger**: The `[?]` circular icon button that appears inline next to metric names, stat labels, and score component names throughout the app.

**Props accepted**: `metricName` (looks up definition from `lib/metricDefinitions`), or explicit `title`, `definition`, `formula`, `example`, `polarity`, `benchmarked` props for custom tooltips.

**Sizes**: `sm` (small, inline with text), `md` (slightly larger, standalone)

**Behaviour**: Click to open popover. Popover shows: title, definition text, optional formula, optional example, optional polarity note, optional "benchmarked metric" badge. Clicking elsewhere or the icon again closes it. Does not use a modal — renders as a positioned overlay.

**Where InfoTooltips appear**:
- Priority Board: next to primary metric name on each card; next to Severity, Persistence, Peer Gap, Commercial, Evidence in the evidence modal score breakdown table
- Command Center: next to "Good Health Status", "Review Needed", "Stable Status", "Ecosystem Deviation Index" labels
- Peer Benchmark: next to metric selector label, next to "12-Month Trend" section heading
- Signal Engine: next to "Validated Signals" label, "Active Status" label, "Strength" label, source and target metric names in flow diagram
- Monthly Briefing: next to anomaly metric names, signal metric names, Good Health / Needs Review / Stable labels in health section

### 4.4 MetricDetailModal

**Component**: `MetricDetailModal.tsx` at `src/components/ui/MetricDetailModal.tsx`

**Trigger**: Clicking any interactive data number, stat card, table row, or anomaly row on Command Center, Peer Benchmark, Signal Engine, or Monthly Briefing pages. (Priority Board uses its own evidence modal — not `MetricDetailModal`.)

**Props**:
- `isOpen`: boolean controlling visibility
- `onClose`: callback to close
- `metricName`: displayed as headline
- `metricValue`: displayed in large coloured type
- `metricCategory`: determines colour scheme (good/critical/warning/info/accent)
- `explanation`: "What This Means" section body
- `businessContext`: "Why It Matters" section body
- `trendData` (optional): renders a `LineChart` in "Trend Over Time" section
- `additionalInfo` (optional): renders a key-value grid in "Additional Details" section

**Close behaviour**: Clicking the X button in top-right or clicking the backdrop (`bg-ink/80` overlay) calls `onClose`.

**Does not block**: `e.stopPropagation()` on the inner panel ensures backdrop click only fires when clicking outside the white panel.

### 4.5 ScreenGuide

**Component**: `ScreenGuide.tsx` at `src/components/ui/ScreenGuide.tsx`

**Location**: Bottom of every page, above the page footer, inside a `<div data-screen-guide>` wrapper (used by WelcomeBanner's "How does this work?" scroll target).

**Default state**: Collapsed. Shows only "ⓘ How to read this screen" toggle button with a chevron-down arrow.

**Expanded state**: Renders the full FAQ panel with `screenName` as the panel headline and all `sections` as titled paragraphs. Each screen has its own set of 3-5 questions. Ends with a tip: "Click the [?] icons next to any metric name throughout the app to see its definition, formula, and what the numbers mean."

**Toggle**: Click the button → `isExpanded` flips. Chevron rotates 180° when expanded. Panel animates in via `animate-fade-in` class.

**Not persisted**: Collapsed state resets on page navigation (component unmounts).

### 4.6 WelcomeBanner

**Component**: `WelcomeBanner.tsx` at `src/components/ui/WelcomeBanner.tsx`

**Location**: Priority Board only — rendered at the very top of `PriorityBoardPage`, above the hero section.

**localStorage key**: `clubos_welcome_dismissed`

**Appears when**: `localStorage.getItem("clubos_welcome_dismissed")` returns null or undefined — i.e. first visit or after clearing storage.

**Hidden when**: key is set to `"true"`.

**Content**: Headline "Welcome to ClubOS", 2-sentence product description, two action buttons.

**Dismiss actions**:
1. **"Got it, start exploring"** button → sets key, hides banner
2. **"How does this work?"** button → sets key, hides banner, smooth-scrolls to `[data-screen-guide]` element at bottom of page
3. **X** button (top-right) → sets key, hides banner

Once dismissed: does not reappear on any subsequent visit or page navigation, unless localStorage is manually cleared.

---

## 5. Complete User Journey — Demo Flow

This is the recommended walkthrough for a first-time stakeholder demo. It follows the flow from the screen blueprint and demonstrates ClubOS as a recurring operating system.

**Step 1 — Open the app → Priority Board loads**
User opens `http://localhost:5176`. Redirected to `/priorities`. WelcomeBanner appears. User clicks "Got it, start exploring." Priority Board is visible with ranked cards.

**Step 2 — Read the top priority → understand the ranked system**
User reads the rank #1 card. Sees: category label (e.g. "Critical"), asset (e.g. "ecommerce"), metric (e.g. "conversion_rate"), 6-month sparkline trending down, 5-component score bar, "Why It Matters" text.

**Step 3 — Click the card → open the Priority Evidence Modal**
User clicks anywhere on the rank #1 card. Modal opens. User reads:
- 12-month trend chart with 6-month average reference line
- Peer bar chart showing Real Madrid vs 5 peer clubs
- Score breakdown table (Severity / Persistence / Peer Gap / Commercial / Evidence components)
- "Why This Priority Scored X.XX" — the number is decomposed row by row
- Supporting evidence metrics
- Recommended next steps

**Step 4 — Click a score component InfoTooltip [?]**
User clicks the [?] next to "Peer Gap" in the score breakdown table. Tooltip explains: "Compares Real Madrid's performance against 5 European clubs. A higher peer gap score means Real Madrid is significantly behind the peer median or leader." User sees formula and example calculation. Closes tooltip.

**Step 5 — Navigate to Peer Benchmark via modal button**
User clicks "View Peer Benchmark" at the bottom of the modal. Modal stays; navigation completes to `/benchmark`. User closes modal (or it closes on route change). Now on Peer Benchmark screen.

**Step 6 — Peer Benchmark → select a metric → read rank and gap**
`ecommerce:conversion_rate` is already selected (default). User sees: rank badge (#4 of 6 clubs), current value, gap to peer median (negative = behind), gap to leader. User reads 12-month trend chart — three lines (RM, Median, Leader). Sees the annotation explaining gap magnitude. User clicks a row in the 6-month trend table. MetricDetailModal opens showing that month's position. User closes modal.

**Step 7 — Navigate to Signal Engine → read validated signals**
User clicks "Signals" in the nav. Signal Engine loads. User sees 4 summary cards (e.g. "3 Validated Signals", "3 Active", "2 month avg lag", "72% avg strength"). First signal card is pre-expanded with Business Interpretation visible. User reads the flow diagram: source metric → lag arrow → target metric. User clicks the Strength stat button to open MetricDetailModal with the Pearson r explanation. Closes modal.

**Step 8 — Navigate to Monthly Briefing → read executive summary**
User clicks "Briefing" in the nav. Monthly Briefing loads. User reads Key Takeaways (4 numbered bullet points). Sees Top 3 Priorities summarised as compact cards. Clicks one — MetricDetailModal opens with priority context. Closes. Reads Notable Anomalies table. Reads Top Signals section. Reads Peer Benchmark Summary (4 stats: benchmarked count, underperformances, avg gap, worst gap). Reads Ecosystem Health donut chart + stat row.

**Step 9 — Return to Priority Board → complete the loop**
User clicks "Board" in the nav or the ClubOS wordmark. Priority Board reloads from cached state. User sees the same ranked list. Understands: the same workflow runs every month — new data in, same five screens, new ranked priorities out.

---

## 6. Error and Edge Case Flows

| Scenario | What the user sees | Recovery path |
|----------|-------------------|---------------|
| Backend not running (no server at port 8000) | Each page shows its error state: headline + red error message like "Failed to load priorities" (the fetch rejects and `setError` is called) | User must start backend server (`uvicorn app.main:app --reload` from `/backend`) and refresh the browser |
| Databricks not connected and no snapshot CSVs | Backend starts in an error state; API endpoints return 500. Frontend shows error states on all pages | Copy Gold table CSVs into `data/gold_snapshots/` folder and restart backend. Snapshot mode activates automatically |
| No data for selected metric in Peer Benchmark | "No benchmark data available for this metric." shown inside the benchmark section (empty `points` array check) | User selects a different metric from the dropdown |
| Priority detail API fails (404 or 500) | `console.error` is logged; modal remains open showing "Loading detail..." indefinitely because `detailLoading` is set to false but `selectedDetail` stays null — modal closes on next close action | User clicks X to close modal and tries another priority card |
| API timeout (fetch hangs) | `fetch` has no explicit timeout; browser default applies (~2 minutes). Loading state persists until timeout then shows error | Refresh the page |
| Empty priorities list (API returns zero items) | Priority Board renders with empty grid (no cards), summary filter cards show 0 counts | Check that Gold snapshot CSVs are present and backend is serving the latest month's data |
| WelcomeBanner scrolls to ScreenGuide but no guide element found | `document.querySelector('[data-screen-guide]')` returns null; `scrollIntoView` is not called (no crash) — banner still dismisses | No action needed; user still dismissed the banner |
| Theme preference conflicts (localStorage says dark, system says light) | localStorage takes precedence over system preference | User can toggle via the header button at any time to override |

---
