# ClubOS MVP Demo Script

## Demo Preparation

**Before starting:**
1. Backend running: `cd backend/api && uvicorn app.main:app --reload`
2. Frontend running: `cd apps/clubos-web && npm run dev`
3. Navigate to: `http://localhost:5176`
4. Verify all tests passing: `./scripts/run_all_tests.sh`

**Demo environment:**
- Latest month: **2026-01-01**
- Backend mode: **Gold snapshot** (local data)
- Data: Real Madrid digital business metrics (2017-2026)

---

## Demo Flow (8-10 minutes)

### 1. Introduction (1 minute)

**Opening statement:**
> "ClubOS is a recurring monthly digital business operating system for elite football clubs. Unlike a static dashboard, it automatically refreshes each month to show what changed, what deserves attention, and where the club stands against peers. Let me walk you through the MVP."

**Landing page: Priority Board**
- Explain this is the default landing page (not Command Center)
- Hero workflow: ranked priorities first, exploration second

---

### 2. Priority Board (3 minutes)

**What to show:**
- Summary strip at top:
  - 3 critical priorities
  - 1 opportunity
  - 5 benchmark underperformances
  - 20 total priorities
- Top-ranked priority card:
  - **#1: Conversion Weakness in Ecommerce** (score 0.96)
  - Category badge
  - Asset (eCommerce) + Metric (conversion_rate)
  - Why it matters: "measurable peer benchmark context and defined competitive gap"
  - Summary: down vs prior month with seasonal deviation

**Key points:**
- Priorities are ranked by deterministic formula (severity + persistence + peer_gap + commercial_weight + supporting_evidence)
- NOT random AI rankings
- Every score is traceable

**Click "View evidence" on top priority:**
- Modal opens showing:
  - Score breakdown (5 components with visual bars)
  - Overview grid (month, asset, metric, rank, score)
  - Why it matters
  - **Supporting evidence payload** (JSON with peer context, severity inputs, persistence, supporting metric rows)
  - Next investigation suggestion

**Close modal**

**Demo rule:** Emphasize that the score breakdown is visible, not hidden black-box logic.

---

### 3. Peer Benchmark (2 minutes)

**Navigate to Peer Benchmark** (sidebar)

**What to show:**
- Metric selector dropdown
- Select: **eCommerce - Conversion Rate** (already selected or select it)
- Current position snapshot:
  - Real Madrid rank: **#4 out of 5** peer clubs
  - RM value vs peer median vs peer leader
  - Gap to median: **-0.0046** (behind)
  - Gap to leader: **-0.0054** (behind)
- 12-month movement (if available)
- Recent 12-month trend table

**Key points:**
- Only shows benchmark-supported KPIs (8 metrics across 4 assets)
- Peer data from 5 elite clubs
- Gaps are polarity-aware (negative = behind for conversion_rate)
- Rank and gaps recalculated monthly

**Try another metric:** Select "Website - Unique Visitors" to show variety

---

### 4. Commercial Signal Engine (2 minutes)

**Navigate to Signal Engine** (sidebar)

**What to show:**
- Overview: 2 validated signals, 2 active
- Signal cards:
  - **#1: main_website unique_visitors → ecommerce net_sales (1mo lag)**
    - Strength: 70%
    - Direction: positive
    - Status: active
- Click on signal to show detail view:
  - Source/target metadata
  - Lag window
  - Business interpretation: "Top-of-funnel traffic volume strongly leads ecommerce net_sales shortly after"
  - Usage guidance

**Key points:**
- Only validated signals (passed statistical stability tests)
- NOT speculative correlations
- Business-interpretable
- Can inform monthly planning (watch website traffic to predict sales)

---

### 5. Monthly Briefing (2 minutes)

**Navigate to Monthly Briefing** (sidebar)

**What to show:**
- Executive summary intro
- **Top 3 priorities** section:
  - #1, #2, #3 with category, score
- **Notable anomalies**:
  - Top 3 metrics with largest seasonal deviations
  - Example: ecommerce other_channels_purchases (-85.88% from baseline)
- **Peer benchmark summary**:
  - 19 benchmarked metrics
  - 5 underperformances
  - Avg/worst gaps
- **Leading signals to watch**
  - 2 active signals listed
- **Digital ecosystem health**:
  - 59 total metrics
  - 23 good (39%)
  - 23 review
  - 13 stable
- **Usage guidance footer**

**Key points:**
- Deterministic monthly summary
- All from structured Gold table data
- No AI wording (could be added later as optional)
- Leadership-ready format

---

### 6. Command Center (optional, if time)

**Navigate to Command Center** (sidebar)

**What to show:**
- Health overview cards (total metrics, good, review, stable)
- Health breakdown bars
- Average absolute deviation: 0.27

**Key point:** Overall digital ecosystem pulse check.

---

## Demo Wrap-up (1 minute)

**Closing summary:**
> "ClubOS demonstrates a recurring monthly operating system for digital business. Every month:
> - New data comes in
> - The same workflow runs
> - Clear priorities come out
>
> All logic is deterministic and traceable. Priority scores have breakdowns. Benchmark positions are polarity-aware. Signals are statistically validated.
>
> This MVP covers the 5 core modules: Priority Board, Command Center, Peer Benchmark, Signal Engine, and Monthly Briefing."

**Technical stack (if asked):**
- **Data:** Databricks medallion architecture (Bronze → Silver → Gold)
- **Backend:** FastAPI (Python 3.11)
- **Frontend:** React + TypeScript (Vite)
- **Quality:** 23 executable tests protecting core workflows

---

## Fallback Plan

**If a module fails during demo:**

### Priority Board fails:
- **Fallback:** Open `/health/summary` endpoint directly → show JSON
- **Explain:** Backend API still works; frontend React issue
- **Pivot:** Walk through API contracts in browser

### Backend API fails:
- **Fallback:** Show local Gold snapshots in `data/gold_snapshots/`
- **Explain:** Data layer still valid; API connectivity issue
- **Pivot:** Open CSV files, show deterministic Gold outputs

### Frontend fails (white screen):
- **Fallback:** Use browser DevTools Network tab → show API responses
- **Explain:** Data flow working; rendering issue
- **Pivot:** Show backend endpoint responses as JSON

### Complete failure:
- **Fallback:** Show test suite output
- **Run:** `./scripts/run_all_tests.sh`
- **Explain:** "Here's proof the system works" (all tests passing)
- **Pivot:** Walk through test code + Gold snapshots

---

## Demo Anti-Patterns (What NOT to do)

❌ Don't claim day-level precision (data is monthly)
❌ Don't claim AI invented the priorities (deterministic scoring)
❌ Don't claim novelty without evidence ("no club has ever...")
❌ Don't hide score breakdowns (transparency is the feature)
❌ Don't lead with charts (lead with ranked priorities)
❌ Don't oversell what the data supports

---

## Demo Talking Points

**Product positioning:**
- Monthly operating system, not one-off dashboard
- Recurring workflow, same process every month
- Decision support, not passive exploration

**Technical credibility:**
- Deterministic priority scoring (not AI black box)
- Polarity-aware benchmarking (bounce_rate = lower is better)
- Statistically validated signals (not random correlations)
- Traceable evidence chains (every score has breakdown)

**Business value:**
- Answers "what deserves attention first?" (Priority Board)
- Answers "where are we vs peers?" (Peer Benchmark)
- Answers "what predicts commercial outcomes?" (Signal Engine)
- Leadership-ready monthly summary (Monthly Briefing)

---

## Post-Demo Q&A Prep

**Expected questions:**

**Q: Is this AI-powered?**
A: AI can enhance wording later (optional), but core logic is deterministic. Priority scores use a weighted formula, signals use statistical validation, benchmarks use peer data. If AI fails, product still works.

**Q: What about real-time data?**
A: Current data is monthly. ClubOS is designed for recurring monthly refresh, not real-time dashboards. This matches how clubs receive digital business reporting.

**Q: How do you handle new clubs?**
A: Peer benchmark uses 5 clubs. Adding a new club requires: (1) benchmark data for that club, (2) re-running Silver/Gold notebooks. No code changes needed.

**Q: Can you export this?**
A: Monthly Briefing can be copy-pasted or screenshot for presentations. PDF export could be added. Tableau integration is documented as optional layer.

**Q: Is this production-ready?**
A: This is a working MVP with 23 executable regression tests. For production: add auth, deploy to cloud, add monitoring, harden Databricks orchestration.

---

## Demo Confidence Checklist

Before demo, verify:
- ✅ Backend returns 200 for all endpoints
- ✅ Frontend loads all 6 pages (no 404s)
- ✅ Test suite passes: `./scripts/run_all_tests.sh`
- ✅ Latest priority appears on Priority Board
- ✅ Evidence modal opens and shows score breakdown
- ✅ Peer benchmark chart renders for conversion_rate
- ✅ Signals list shows 2 active signals
- ✅ Monthly briefing shows top 3 priorities

**If all ✅ → demo-safe.**
