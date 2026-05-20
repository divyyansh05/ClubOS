---
# ClubOS — UI/UX Design Document
**Version**: 1.0
**Status**: Reconstructed from MVP
**Date**: 2026-05-14
**Author**: Divyansh Shrivastava
---

## 1. Design Philosophy

ClubOS uses a **newsprint editorial aesthetic** — a newspaper-inspired visual language built around serif fonts, dense typographic hierarchy, high-contrast ink-on-paper colour values, and hard border rules instead of shadows. This is a deliberate departure from modern SaaS conventions (Inter, blue gradients, card shadows, rounded corners).

The choice is motivated by three things:

**The "monthly briefing" metaphor.** ClubOS produces one decision document per month. A newspaper also produces one edition on a fixed cadence. The visual language reinforces the product's value proposition: this is the authoritative summary of what happened, not a live feed. The header even shows a running edition date ("Vol. 1.0 · May 2026") using the same language as a newspaper masthead.

**Information density.** Newsprint typography evolved to maximise the amount of readable text per square centimetre. ClubOS surfaces 10 ranked priorities, 8 benchmarked metrics, and 4 validated signals simultaneously. Serif type and thin border rules achieve this density without visual clutter that would come from shadow-heavy card stacks or icon-heavy UI.

**Authority and credibility.** The product is shown to a club's digital business lead and commercial lead — people who attend board meetings. A presentation-ready interface modelled on financial reporting aesthetics (not a product management tool or CRM) signals that the numbers on screen are substantive and defensible, not marketing metrics.

Specific choices this philosophy drives: 2px `border-ink` rules instead of box shadows on cards, DM Serif Display for page titles rather than a geometric sans, JetBrains Mono for every number and score rather than a proportional font, and a warm off-white (`paper: #FAFAF8`) rather than pure white. In dark mode, the background shifts to `stone-900` (#1A1A18), maintaining the same warm tonal quality.

---

## 2. Design System

### 2.1 Color Palette

#### Base Palette

| Token | Hex Value | Usage |
|-------|-----------|-------|
| `paper` | `#FAFAF8` | Light mode page background, card backgrounds |
| `ink` | `#1A1A1A` | Light mode primary text, borders, buttons |
| `stone-50` | `#FAFAF8` | Lightest surface (same as paper) |
| `stone-100` | `#F5F5F3` | Secondary backgrounds, welcome banner background |
| `stone-200` | `#E8E8E5` | Subtle borders, dividers |
| `stone-300` | `#D1D1CC` | Placeholder text, inactive borders |
| `stone-400` | `#A3A39E` | Muted labels, secondary metadata |
| `stone-500` | `#75756F` | Subdued text: edition strings, metric unit labels |
| `stone-600` | `#5C5C56` | Dark secondary text |
| `stone-700` | `#434340` | Dark mode button backgrounds |
| `stone-800` | `#2B2B28` | Dark mode card surfaces, chart tooltips |
| `stone-900` | `#1A1A18` | Dark mode page background |
| `stone-950` | `#0F0F0E` | Darkest surface, used sparingly |

#### Sport Brand Colors

| Token | Hex Value | Usage |
|-------|-----------|-------|
| `sport-blue-50` | `#EFF6FF` | Light tint backgrounds |
| `sport-blue-100` | `#DBEAFE` | Light hover states |
| `sport-blue-200` | `#BFDBFE` | Light accent borders |
| `sport-blue-300` | `#93C5FD` | Mid-range accent |
| `sport-blue-400` | `#60A5FA` | Interactive highlights |
| `sport-blue-500` | `#3B82F6` | Primary brand blue, info hover states |
| `sport-blue-600` | `#2563EB` | Link hover, nav active states (`info-light`) |
| `sport-blue-700` | `#1D4ED8` | Darker blue variant |
| `sport-blue-800` | `#1E40AF` | Gradient start for sport gradient |
| `sport-blue-900` | `#1E3A8A` | Deep navy, header gradient start |
| `sport-gold-50` | `#FEFCE8` | Light gold tint |
| `sport-gold-100` | `#FEF9C3` | Light gold surface |
| `sport-gold-200` | `#FEF08A` | Gold highlight |
| `sport-gold-300` | `#FDE047` | Bright gold |
| `sport-gold-400` | `#FACC15` | Gold accent |
| `sport-gold-500` | `#EAB308` | Primary gold, gradient start |
| `sport-gold-600` | `#CA8A04` | Gold mid-tone |
| `sport-gold-700` | `#A16207` | Dark gold |
| `sport-gold-800` | `#854D0E` | Deep gold |
| `sport-gold-900` | `#713F12` | Darkest gold |

#### Semantic Colors

| Token | Hex Value | Usage |
|-------|-----------|-------|
| `critical-light` | `#DC2626` | Critical state in light mode (text, borders) |
| `critical-dark` | `#EF4444` | Critical state in dark mode |
| `critical-50` | `#FEF2F2` | Critical background tint |
| `critical-500` | `#EF4444` | Critical badge fill |
| `critical-600` | `#DC2626` | Critical border, icon |
| `critical-700` | `#B91C1C` | Critical pressed state |
| `warning-light` | `#EA580C` | Warning state in light mode |
| `warning-dark` | `#F97316` | Warning state in dark mode |
| `warning-50` | `#FFF7ED` | Warning background tint |
| `warning-500` | `#F97316` | Warning badge fill |
| `warning-600` | `#EA580C` | Warning border, icon |
| `warning-700` | `#C2410C` | Warning pressed state |
| `info-light` | `#2563EB` | Info / link hover in light mode |
| `info-dark` | `#3B82F6` | Info / link hover in dark mode |
| `info-50` | `#EFF6FF` | Info background tint |
| `info-500` | `#3B82F6` | Info badge fill |
| `info-600` | `#2563EB` | Info border |
| `info-700` | `#1D4ED8` | Info pressed state |
| `good-light` | `#16A34A` | Positive state in light mode |
| `good-dark` | `#22C55E` | Positive state in dark mode |
| `good-50` | `#F0FDF4` | Positive background tint |
| `good-500` | `#22C55E` | Positive badge fill |
| `good-600` | `#16A34A` | Positive border, trend arrows |
| `good-700` | `#15803D` | Positive pressed state |
| `accent-light` | `#9333EA` | Accent / benchmark category in light mode |
| `accent-dark` | `#A855F7` | Accent / benchmark category in dark mode |
| `accent-50` | `#FAF5FF` | Accent background tint |
| `accent-500` | `#A855F7` | Accent badge fill |
| `accent-600` | `#9333EA` | Accent border |
| `accent-700` | `#7E22CE` | Accent pressed state |

#### Gradients

| Token | Value | Usage |
|-------|-------|-------|
| `gradient-sport` | `#1E3A8A → #DC2626` (135°) | Priority card rank badges, hero elements |
| `gradient-sport-subtle` | `#3B82F6 → #EF4444` (135°) | Softer brand gradient |
| `gradient-gold` | `#EAB308 → #F97316` (135°) | Gold / opportunity highlights |
| `gradient-blue` | `#2563EB → #7C3AED` (135°) | Informational gradients |
| `gradient-success` | `#16A34A → #22C55E` (135°) | Positive trend fills |

---

### 2.2 Semantic Colors

Semantic colors encode data state directly in the visual system. Any element carrying a semantic color token communicates a data meaning — not just decoration.

**Critical (`critical-*`)** — Red family. Used for Priority Board items scoring above 0.8, for trend comparisons where a metric is significantly below target, and for negative comparison values in chart tooltips. In both light and dark modes, critical elements should feel urgent without being alarming.

**Warning (`warning-*`)** — Orange family. Used for the "warning" priority category (moderate concern, score 0.5–0.8), and for trend deviations that are significant but not at threshold level. The orange is warm and readable against both `paper` and `stone-900` backgrounds.

**Good (`good-*`)** — Green family. Used for metrics trending positively, for the "opportunity" category pill, and for positive percentage comparisons in chart tooltips (e.g. "+12.3% vs 6-mo avg"). Green in both variants maintains WCAG AA contrast against the background surfaces.

**Info (`info-*`)** — Blue family. Used for the "benchmark" category (peer-driven context), for interactive hover states on navigation links, and for the `stable` data state. Blue signals "context" rather than urgency.

**Accent (`accent-*`)** — Purple family. Used for the MetricDetailModal category badge when the category is `stable` or when no clearer semantic colour applies. Also used for the AI-generated summary label on the Monthly Briefing screen.

**No semantic color is used for decoration.** If an element does not carry a data state meaning, it uses the stone scale (neutral) or ink/paper base tokens.

---

### 2.3 Typography

| Role | Font Family | Weight | Usage |
|------|-------------|--------|-------|
| Headline (`font-headline`) | DM Serif Display, serif | 400 (regular) | Page titles, priority card headings, modal metric names, section titles |
| Body (`font-body`) | IBM Plex Serif, serif | 400, 600, 700 | Descriptive body text, card descriptions, briefing summaries, tooltip month labels |
| UI Sans (`font-sans`) | Inter, sans-serif | 400, 500, 600, 700 | Navigation links, form labels, button text where mono is not used |
| Mono (`font-mono`) | JetBrains Mono, monospace | 400, 500, 600 | All numeric values, scores, percentages, metric names, category labels, edition strings, uppercase tracking labels |

**Typography decisions:**

- All `<h1>` through `<h6>` elements inherit `font-headline tracking-tight` via global base styles — headlines are always DM Serif Display.
- Numbers and scores are always rendered in `font-mono` regardless of context. This ensures columnar alignment in tables, makes scores visually distinct from prose, and signals data precision.
- The metadata bar ("Vol. 1.0 · Edition: May 2026") uses `font-mono text-[10px] uppercase tracking-widest` — an explicit typographic reference to a newspaper publication line.
- Navigation items use `font-sans text-sm uppercase tracking-wider` — cleaner than serif for short interactive labels but still elevated above default body style.

---

### 2.4 Dark / Light Theme

**Implementation method:** Tailwind's `class` strategy (`darkMode: 'class'`). Dark mode activates when the `dark` class is present on `<html>`. The `PageShell` component manages this via a React `isDark` state, applied as a class to `document.documentElement`.

**Initialization sequence (on first load):**
1. Read `localStorage.getItem('theme')`.
2. If value is `'dark'` → apply dark mode.
3. If value is `'light'` → apply light mode.
4. If no value exists → check `window.matchMedia('(prefers-color-scheme: dark)')`.
5. Apply whichever the system reports.

**Persistence:** Every toggle writes the chosen theme (`'dark'` or `'light'`) to `localStorage` under the key `'theme'`. This persists across browser sessions and navigation between pages.

**Toggle location:** The theme toggle button sits in the top-right of the header metadata bar, rendered as the text "Dark" (visible in light mode) or "Light" (visible in dark mode) in `font-mono text-[10px] uppercase tracking-widest`. It has no icon — pure typographic control, consistent with the newsprint aesthetic.

**Newsprint texture in dark mode:** The global `body::before` pseudo-element renders a 4×4px grid using two overlapping `linear-gradient` patterns at 2% opacity. In dark mode, the grid switches to `rgba(255,255,255,0.02)` opacity lines. This gives dark mode a subtle tactile texture that echoes newsprint rather than being a flat digital black.

**Coverage:** Every Tailwind class that defines a visible color has a `dark:` variant. Borders shift from `border-ink` to `dark:border-stone-700`, backgrounds from `bg-paper` to `dark:bg-stone-900`, text from `text-ink` to `dark:text-stone-100`.

---

## 3. Layout Principles

**Maximum width:** `max-w-screen-xl` (`1280px`) centered with `mx-auto`, padded by `px-6` (24px each side). All five screens use this constraint — no full-bleed content areas except the sticky header itself and the full-width WelcomeBanner.

**Sticky header:** `position: sticky; top: 0; z-index: 40; backdrop-blur-sm`. The header never scrolls away. It maintains `bg-paper/95` (95% opacity) with blur so content beneath is visible but unreadable — preventing the header from becoming visually competitive with data below it.

**Content padding:** The main content area beneath the header begins with `px-6 py-8` on all five screens, creating consistent breathing room from the header border.

**Card grid system:** Priority Board uses a 2-column responsive grid (`grid grid-cols-1 md:grid-cols-2`). Command Center uses 4 summary cards in a row, then 3 distribution bars below. Each screen's grid is defined per-page, not globally — layouts are tailored to data density requirements.

**Border language:** Heavy `border-2` (2px) rules separate major structural zones (header bottom border, section header borders, card borders). Lighter `border` (1px) rules separate internal card elements, table rows, and metadata. No element uses border-radius larger than `rounded` (4px); most cards have no rounding at all — square corners reinforce the editorial register.

**Spacing system:** Tailwind's default 4px base unit applies throughout. Common rhythm: `p-6` (24px) for card internal padding, `gap-4` (16px) between grid items, `mb-2`/`mb-4` for typographic spacing within cards. Custom spacing is not extended in `tailwind.config.js` — the default 4px scale is sufficient.

**No sidebar.** Navigation lives entirely in the header. This maximises horizontal content width at every screen size and ensures the same layout constraint (`max-w-screen-xl`) applies to both navigation and content.

---

## 4. Component Library

### 4.1 Priority Card

The Priority Card is ClubOS's most information-dense UI element. It surfaces a ranked priority issue with enough context to decide whether to investigate further.

**Visual structure (top to bottom):**
1. **Rank badge** — circular SVG element, `bg-gradient-sport` (navy → red gradient), white text in `font-mono`. Positioned top-left.
2. **Category pill** — `CRITICAL / OPPORTUNITY / BENCHMARK / WARNING` label. Coloured by semantic token (see §4.4). Positioned adjacent to rank badge.
3. **Priority title** — `font-headline` 1.25rem, `tracking-tight`. One or two lines.
4. **Asset · Metric label** — `font-mono text-xs uppercase text-stone-500`. e.g. "ECOMMERCE · CONVERSION\_RATE".
5. **Score bar** — horizontal `div` with gradient fill proportional to priority score (0–1). Colour transitions from `good` (low score) through `warning` to `critical` (high score). Score value printed in `font-mono` to the right.
6. **Score components** — five small labelled sub-bars or percentages: Severity, Persistence, Peer Gap, Commercial, Evidence. Visible on hover or in the expanded evidence modal.
7. **Short description** — `font-body text-sm` two-to-three sentence summary of what the metric is doing.
8. **"View Evidence" button** — `border-2 border-ink font-mono text-xs uppercase`. Triggers the Priority Evidence Modal.

**States:**
- **Default:** 2px border-ink, white background (light) / stone-800 (dark).
- **Hover:** `hover-glow` applies `shadow-sport` — a blue-shifted drop shadow that subtly lifts the card.
- **Selected / Active (evidence modal open):** card maintains hover appearance; modal overlays entire viewport.

**Information hierarchy principle:** The rank number and category pill are visually dominant. Title is second. Score bar is third. Raw metric values are de-emphasised (mono, small, secondary colour) — scouts care about urgency rank, not raw numbers.

---

### 4.2 InfoTooltip

InfoTooltip is a small circular `?` button that appears inline next to any number or label that needs plain-English context. It is the primary mechanism for making every data point in ClubOS self-explanatory.

**Visual design:** `w-4 h-4` circle with `border border-stone-400 dark:border-stone-500`, transparent fill, `font-mono text-xs` interior character "?". The circle is intentionally small — it should not compete with the data label it accompanies.

**Trigger:** Clicking the `?` icon opens a panel (not a full-screen modal). The panel is `max-w-xs` wide, rendered in `border-2 border-ink bg-paper dark:bg-stone-800 p-3 shadow-lg`. It contains a metric label in `font-mono text-xs uppercase tracking-widest`, a plain-English explanation in `font-body text-sm`, and optionally a business context sentence.

**Positioning:** Panel appears adjacent to the trigger icon, offset to avoid clipping on viewport edges. Clicking anywhere outside the panel closes it.

**Scope:** InfoTooltip is used on metric name labels throughout Command Center, Peer Benchmark, Monthly Briefing, and Signal Engine. It is distinct from the MetricDetailModal — InfoTooltip is for brief inline clarification; MetricDetailModal is the full drilldown triggered by clicking a metric value.

---

### 4.3 Score Bar / Stacked Bar

Two variants of horizontal bar chart used in the Priority Board.

**Simple Score Bar:** A single `<div>` with a percentage `width` derived from the priority score (0–1 → 0–100%). Fill uses a gradient that progresses from `good` (left, low score) through `warning` (mid) to `critical` (right, high score). Height is `h-2` or `h-3`. The bar container is full-width of its parent column.

**Stacked Component Bar (evidence modal):** Five equal segments representing the five weighted score components (Severity 30%, Persistence 25%, Peer Gap 20%, Commercial 15%, Evidence 10%). Each segment is coloured independently by its value magnitude — a segment with a high input value shows a stronger/deeper colour. Segments are separated by 1px gaps. Hovering a segment highlights it and shows the component weight and value in a tooltip.

**Color logic:**
- Score < 0.4 → `good` family (green)
- Score 0.4–0.7 → `warning` family (orange)
- Score > 0.7 → `critical` family (red)

Score bars never show rounded ends — sharp left and right edges maintain the editorial register.

---

### 4.4 Status Pills / Badges

Rounded pill badges communicate the category of each priority. They appear on Priority Cards and as filter buttons on the Priority Board.

| Category | Background | Text | Border | Semantic meaning |
|----------|-----------|------|--------|-----------------|
| `CRITICAL` | `critical-50` / `critical-700` (dark) | `critical-700` / `critical-50` | `critical-600` | Score > 0.8; immediate attention required |
| `OPPORTUNITY` | `good-50` / `good-700` | `good-700` / `good-50` | `good-600` | Positive trend with a peer gap to close |
| `BENCHMARK` | `accent-50` / `accent-700` | `accent-700` / `accent-50` | `accent-600` | Peer-driven underperformance |
| `WARNING` | `warning-50` / `warning-700` | `warning-700` / `warning-50` | `warning-600` | Moderate concern; score 0.5–0.8 |

**Shape:** `rounded-full px-3 py-1 text-xs font-mono uppercase tracking-wider`. The pill is always uppercase, monospace — consistent with the product's convention of treating all category identifiers as data codes rather than prose labels.

**Filter buttons (Priority Board top bar):** Larger than inline pills. `px-4 py-2 border-2`. Active filter: border fills with the category colour and text inverts. Inactive filter: outline-only with the category colour.

---

### 4.5 Modal / Overlay

Two distinct modal implementations exist in ClubOS.

**MetricDetailModal (reusable — used across 4 screens):**
- **Backdrop:** `fixed inset-0 bg-black/60 z-50`. Clicking backdrop closes the modal.
- **Panel:** `glass-modal` utility class (`backdrop-blur-2xl bg-white/95 dark:bg-stone-900/95 border border-stone-200/60 dark:border-stone-700/60 shadow-glass-lg`). Max-width `max-w-2xl`, `rounded` (minimal), `p-6`. Positioned `mx-4 my-8` from viewport edges, scrolls internally if content overflows.
- **Close button:** Absolute-positioned top-right `×` icon in `text-stone-500`, `hover:text-stone-700`.
- **Header:** Metric name in `font-headline text-4xl`, category badge inline, current value in `font-mono font-bold text-3xl`. Value colour matches category semantic colour.
- **Body sections:** Explanation (plain English, `font-body`), Business Context, optional trend chart (Recharts LineChart), optional additional info grid (2-column `dl` list of key-value pairs).
- **Entry animation:** `animate-scale-in` — scale from 0.95 → 1 over 0.2s.

**Priority Evidence Modal (Priority Board only):**
- Larger overlay: occupies the full viewport on mobile, `max-w-4xl` on desktop.
- Contains: 12-month trend chart (Recharts LineChart), peer bar chart (horizontal BarChart), score breakdown table, supporting metrics table, competitive context grid, action buttons ("Open Analytics Dashboard" → `/command-center`, "View Peer Benchmark" → `/benchmark`).
- Not a reusable component — inline state in `PriorityBoardPage`.

---

### 4.6 Navigation Bar

**Structure:** Single sticky `<header>` with two horizontal zones:

1. **Metadata bar** (thin strip, `py-2`, `border-b border-stone-300`):
   - Left: `font-mono text-[10px] uppercase tracking-widest text-stone-500` — "Vol. 1.0 · Edition: {Month Year}"
   - Right: theme toggle button — text reads "Dark" (light mode) or "Light" (dark mode), same mono style.

2. **Main header** (`py-6`):
   - Left: ClubOS logo link (`NavLink to="/priorities"`) — `font-headline text-4xl md:text-5xl tracking-tight` with `font-mono text-[10px] uppercase tracking-widest text-stone-500` tagline beneath it.
   - Right: Navigation links — `hidden md:flex gap-8 font-sans text-sm uppercase tracking-wider`. Five items: Board, Center, Benchmark, Signals, Briefing.

**Active state:** Active `NavLink` gets `border-b-2 border-ink dark:border-stone-300 pb-1`. No background fill, no colour change — a simple underline rule is the only active indicator, consistent with newspaper section headers.

**Hover state:** `hover:text-info-light dark:hover:text-info-dark` — links lighten to blue on hover. Transition is `duration-150 ease-out` (global default).

**Logo click:** Clicking the ClubOS wordmark navigates to `/priorities` (Priority Board). There is no "Home" nav item — the logo serves that role.

---

### 4.7 ScreenGuide

The ScreenGuide is a collapsible FAQ panel anchored to the bottom of each screen. It explains how to read the screen, what the metrics mean, and what actions are available — written for a user who is exploring ClubOS for the first time.

**Visual design:**
- **Collapsed state:** A single `border-2 border-ink` button spanning full content width. Label: "How to read this screen" with a right-aligned chevron icon (`▼`). Font: `font-mono text-sm uppercase tracking-wider`.
- **Expanded state:** Below the button, a `border-2 border-ink p-6 bg-stone-50 dark:bg-stone-800` panel reveals the FAQ content. The chevron rotates 180° (CSS `transform rotate-180`). Content is `font-body text-sm` prose.
- **Anchor:** The wrapping element carries a `data-screen-guide` attribute. The WelcomeBanner's "How does this work?" button uses `document.querySelector('[data-screen-guide]').scrollIntoView({ behavior: 'smooth' })` to bring the guide into view.

**State:** `isExpanded` boolean in local component state. It is **not** persisted — the guide collapses on every page navigation. Returning to the same screen always shows it collapsed.

**Toggle animation:** Height transition handled by CSS max-height or conditional render (implementation varies by screen). The chevron rotation is `transition-transform duration-150`.

---

## 5. Data Visualisation Patterns

### 5.1 Line Charts (Trend)

Used in: Command Center (health trend), Peer Benchmark (12-month gap chart), MetricDetailModal (trendData prop), Priority Evidence Modal.

**Library:** Recharts `LineChart` with `ResponsiveContainer`.

**Axis style:** `XAxis` and `YAxis` use `stroke="currentColor"` at reduced opacity, `tick={{ fill: 'currentColor', fontSize: 11 }}`, no axis lines on non-primary axes. Tick count kept minimal — 6 months on x-axis, 4–5 ticks on y-axis — to avoid clutter.

**Line style:** `strokeWidth={2}`, no dots by default (`dot={false}`), `activeDot={{ r: 4, fill: colorVar }}` on hover. Real Madrid series is always rendered in `#DC2626` (critical-light / red — the club colour in the data context). Peer median is `#6B7280` (stone dashed). Leader line is `#22C55E` (good-dark, green).

**Reference lines:** `ReferenceLine` from Recharts at the peer median value, rendered as a dashed grey line (`stroke="#A3A39E" strokeDasharray="4 4"`). Labelled "Peer Median" in `font-mono text-xs`.

**Custom tooltip:** The `ChartTooltip` component (see §5.1 source) renders inside a `border-2 border-ink bg-paper dark:bg-stone-800 p-3 shadow-lg rounded max-w-xs` panel. Contents: metric label (mono, uppercase), value in `font-headline text-2xl`, month in `font-body text-sm`, comparison to 6-month average in `font-mono text-xs` coloured by direction (`good-600` positive, `critical-600` negative).

**Grid:** `CartesianGrid strokeDasharray="3 3"` at `stroke="#E8E8E5"` (stone-200) in light mode, `stroke="#434340"` (stone-700) in dark mode. Horizontal grid lines only — no vertical.

---

### 5.2 Bar Charts (Peer Benchmark)

Used in: Peer Benchmark screen (ranking bar chart), Priority Evidence Modal (peer comparison bars).

**Library:** Recharts `BarChart` with `layout="vertical"` for horizontal bars.

**Bar structure:** One bar per club (6 total: Real Madrid + 5 peers). Each bar's length is proportional to the metric value. Real Madrid's bar is rendered in `#DC2626` (red). Peer bars are rendered in `#A3A39E` (stone-400, neutral grey). Hovering a bar highlights it with increased opacity.

**Reference line:** A vertical `ReferenceLine` at the peer median value — dashed, `stroke="#75756F"` (stone-500), labelled.

**Gap labels:** Each bar has an end-label showing the gap to peer median (`+X%` in green or `-X%` in red) in `font-mono text-xs`.

**No axis labels on y-axis for peer names** — club names are anonymised identifiers (masia\_fc, merseyside\_red, etc.); they appear as tick labels in `font-mono text-xs text-stone-500`.

---

### 5.3 Sparklines (Mini Trend on Cards)

Used in: Command Center summary cards (4 small inline trends), Monthly Briefing priority cards.

**Dimensions:** Approximately 80–120px wide × 32–40px tall. No axes, no labels, no tooltip — pure shape conveys direction.

**Implementation:** Recharts `LineChart` with `margin={{ top: 2, right: 2, bottom: 2, left: 2 }}`, no `XAxis`, no `YAxis`, no `CartesianGrid`.

**Color logic:**
- Trend direction positive (metric improving) → `#22C55E` (good-dark)
- Trend direction negative (metric worsening) → `#EF4444` (critical-dark)
- Trend flat / stable → `#A3A39E` (stone-400)

**Stroke:** `strokeWidth={1.5}`, no dots. The line alone communicates trajectory — the minimal format suits the card's space constraint.

---

## 6. Interaction Patterns

| Interaction | Behaviour |
|-------------|-----------|
| Hover on priority card | `shadow-sport` drop shadow appears (`transition-all duration-200`). No scale change — avoids layout shift in 2-column grid. |
| Click "View Evidence" button | Opens Priority Evidence Modal (full-viewport overlay). Card remains in background with reduced opacity from backdrop. |
| Click category filter button (Board, Opportunity, Critical, etc.) | Filters priority card grid to matching category. Other cards disappear. Active button fills with category colour. Clicking active button again resets to "all". |
| Click any metric value in Command Center, Benchmark, Briefing | Opens `MetricDetailModal` with the metric name, current value, plain-English explanation, and optional trend chart. |
| Click InfoTooltip `?` icon | Opens small inline panel adjacent to the icon. Clicking elsewhere closes it. |
| Toggle dark/light theme | Writes `'dark'` or `'light'` to `localStorage.theme`. Adds/removes `.dark` class on `<html>`. All `dark:` Tailwind variants activate/deactivate. Transition: `duration-150` on all colour properties globally. |
| Expand ScreenGuide | `isExpanded` state toggles true. Content panel renders below button. Chevron rotates 180°. State resets to `false` on page navigation. |
| Click WelcomeBanner "Got it" | Sets `localStorage.clubos_welcome_dismissed = 'true'`. Banner fades out (`isVisible` → false). Never shown again to this browser. |
| Click WelcomeBanner "How does this work?" | Same dismissal as "Got it", then calls `scrollIntoView({ behavior: 'smooth', block: 'start' })` on `[data-screen-guide]`. |
| Click backdrop of any modal | `onClose` prop called. Modal closes. Focus returns to triggering element. |
| Click signal card (Signal Engine) | `selectedSignal` state set to clicked signal ID. Card expands to show full context inline. Previously selected card collapses. Strength/Lag/Direction inner buttons use `e.stopPropagation()` — they do not trigger card selection. |
| Select metric in Peer Benchmark dropdown | API call to `GET /benchmark/{asset}/{metric}` fires immediately. Charts and stat cards re-render with new data. Loading state shows skeleton placeholder while fetching. |

---

## 7. Responsive Behaviour

ClubOS is designed **desktop-first**. The primary use case is a digital business lead reviewing the monthly priority list on a laptop or external monitor. No mobile-first or touch-first decisions were made in the MVP.

**Breakpoints (Tailwind defaults):**
- `md` (768px): Navigation links appear (`hidden md:flex`). Below 768px, the nav links are hidden — no hamburger menu is implemented in the MVP.
- `lg` (1024px): Most content grids shift from 1-column to 2-column.
- `xl` (1280px): `max-w-screen-xl` cap is reached; content centres with horizontal margin.

**What breaks below 768px:**
- Navigation disappears entirely. Users can still navigate via the ClubOS logo link to `/priorities` but cannot reach other screens without typing URLs.
- Priority Board 2-column grid collapses to single-column (`grid-cols-1`).
- Chart widths reflow via `ResponsiveContainer` — Recharts handles chart responsiveness automatically.
- Score bars and data tables may become horizontally scrollable if column count is not reduced.

**Overflow strategy:** Most data tables use `overflow-x-auto` on their wrapping `<div>`. This allows horizontal scroll on narrow viewports rather than breaking layout.

**Known mobile gap:** No hamburger menu, no bottom tab bar, no mobile-specific chart simplifications. Acknowledged in the MVP as out of scope — the product targets desktop usage at football clubs.

---

## 8. Accessibility Considerations

**Keyboard navigation:** All interactive elements (`<button>`, `<a>`, `NavLink`) are natively focusable. Focus states are provided by Tailwind's default `focus:ring` utilities via the `@tailwindcss/forms` plugin. Modal focus trapping is not explicitly implemented in the MVP — focus does not automatically move to the modal on open, and `Tab` can reach elements behind the backdrop.

**ARIA labels:** The theme toggle button has `aria-label="Toggle theme"`. The WelcomeBanner close button has `aria-label="Close welcome banner"`. Priority card "View Evidence" buttons do not carry `aria-label` — they rely on visible text.

**Colour contrast:**
- Light mode: `ink` (#1A1A1A) on `paper` (#FAFAF8) achieves approximately 18:1 contrast ratio — exceeds WCAG AA and AAA.
- Dark mode: `stone-100` (#F5F5F3) on `stone-900` (#1A1A18) achieves approximately 14:1 — exceeds WCAG AAA.
- Semantic colours (`critical-600` on `critical-50`, `good-600` on `good-50`) meet WCAG AA (4.5:1 minimum for text).

**Screen readers:** Recharts SVG charts do not include `<title>` or `<desc>` elements in the MVP. Chart data is not accessible to screen readers. This is a known gap.

**Motion:** All animations are brief (`duration-150` to `duration-300`). No `prefers-reduced-motion` media query is implemented. The WelcomeBanner `animate-fade-in` and card hover transitions may affect users with vestibular disorders — a future enhancement.

**Semantic HTML:** Headings are in correct DOM order (`h1` ClubOS wordmark, `h2` section titles, `h3` card titles). The navigation uses `<nav>` with `NavLink` elements. Modals use `<div>` rather than `<dialog>` — focus trapping and ARIA role enhancements are deferred.

---

## 9. Design Decisions and Rationale

| Decision | Rationale |
|----------|-----------|
| Newsprint aesthetic over modern SaaS | Signals editorial authority and "monthly briefing" cadence. Differentiates from generic BI tools. Dense typography is appropriate for the data volume (52 metrics, 10 priorities per screen). Printable layouts are a side benefit. |
| Monospace font for all numbers and scores | Ensures columnar alignment in tables. Signals data precision to analysts. Creates visual distinction between "this is a data value" (mono) and "this is a label" (headline or body). |
| Dark mode as equal default (follows system) | No hardcoded default — system `prefers-color-scheme` is respected first. Analysts running ClubOS in presentation rooms with dimmed lighting benefit from dark mode. Both modes are fully designed, not afterthoughts. |
| No sidebar navigation | A sidebar consumes ~250px of horizontal space that is better used for data tables and charts. Five screens fit comfortably in a header-based tab pattern. Sidebar patterns imply a hierarchical navigation model; ClubOS five screens are peer-level, not hierarchical. |
| Priority Board as landing screen | The hero feature must be the first thing a user sees. Routing `/` → `/priorities` forces this. A general dashboard or "overview" landing page would dilute focus — the product's value is the ranked priority list. |
| `border-2 border-ink` rules instead of shadows | Newspaper columns are divided by rules (thin lines), not shadows. Hard borders maintain visual crispness at all zoom levels and in print contexts. `box-shadow` can look soft and imprecise on high-DPI displays. |
| `glass-modal` for modals (frosted glass) | Modals appear over live chart content. A frosted backdrop (`backdrop-blur-2xl bg-white/95`) allows the user to perceive underlying data through the modal without it being readable — reinforcing context without distraction. |
| Animate-fade-in on WelcomeBanner | The banner should appear gracefully on first visit — a sudden pop-in would feel like an error. `opacity-0 → opacity-100` over 0.3s is barely perceptible but avoids the flash. |
| `data-screen-guide` attribute as anchor | Avoids coupling the WelcomeBanner scroll behaviour to a specific element ID or ref. Any screen can place a `data-screen-guide` element; the banner's "How does this work?" button will scroll to it without knowing the page structure. |
| Sport gradient (`navy → red`) for rank badges | Blue and red are Real Madrid's colours. The gradient is used only for the highest-hierarchy elements (rank badges, hero CTAs) to convey that these are the most important items on the page. Overuse would dilute the signal. |
