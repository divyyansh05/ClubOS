# Interview Demo Runbook — ClubOS V2 AI Layer

## Overview

**What you're demoing:** A production-grade AI layer built on top of ClubOS V1.
Four agents (Scout, Watchdog, Investigator, Briefer) wired into a React frontend,
driven by a single supervisor endpoint. The interviewer sees live AI reasoning.

**Runtime:** 5–8 minutes for the core loop. 10–12 with deep-dives.

---

## Pre-demo checklist (15 min before)

```bash
# 1. Start the backend (from project root)
PYTHONPATH=$(pwd) uvicorn app.main:app --port 8001 --app-dir backend/api

# 2. Start the frontend
cd apps/clubos-web && npm run dev
# Opens on http://localhost:5174

# 3. Confirm API is alive
curl http://localhost:8001/api/ai/watchdog/alerts
# Should return { "total": N, "alerts": [...] }

# 4. Warm the cache — generate a briefing so it's instant during demo
curl -X POST http://localhost:8001/api/ai/briefer/run_monthly
# Should return briefing_id. If 429, top up API key first (see Fallback).
```

**Pre-flight checklist:**
- [ ] Backend responds on port 8001
- [ ] Frontend loads at http://localhost:5174
- [ ] `/ai/chat` page renders with suggestion chips
- [ ] `/ai/alerts` shows alert table (50+ rows)
- [ ] `/ai/briefings` shows at least one completed briefing
- [ ] Open LangSmith in a separate tab — verify traces are appearing
- [ ] Dark mode ON (matches screenshots, looks cleaner on projection)
- [ ] Browser zoom at 90% (fits full table without horizontal scroll)

---

## Demo sequence (5–8 min)

### 1. The architecture pitch (30s — say while page loads)

> "ClubOS V2 adds an AI layer on top of the existing analytics platform.
> Rather than building one monolithic AI endpoint, I decomposed it into
> four specialist agents — Scout for metrics, Watchdog for anomaly detection,
> Investigator for root-cause analysis, and Briefer for executive summaries.
> A deterministic classifier routes each query to the right agent directly,
> falling back to a LangGraph supervisor for complex multi-step queries."

### 2. Chat — Scout query (60–90s)

Navigate to: **`/ai/chat`**

Type: `what is streaming_daily_users this month?`

*While it loads (3–8s):*
> "The classifier identifies this as a metrics question and routes it directly
> to Scout — no LLM needed for the routing decision, which keeps latency low."

*When response appears:*
- Point to the **DispatchBadge**: "Scout, direct — 4.2 seconds"
- Point to **Citations**: "Every claim is grounded in a source from the semantic layer"
- Click **"View reasoning trace →"**: "This is the full LangSmith trace — every tool call, every retrieval"

### 3. Chat — Supervisor multi-step query (60s)

Type: `compare last month to this month and explain any changes`

*When response appears:*
- Point to badge: "LangGraph Supervisor — multi-step"
- > "This one was ambiguous — it needed to pull two periods, compare them,
>   and synthesise. The supervisor built a plan and executed it step by step."

### 4. Alerts — Watchdog (60s)

Navigate to: **`/ai/alerts`**

> "The Watchdog runs detection rules against the priority board snapshot.
> Six rules: rank jumps, score anomalies, drops out of top N, persistent top."

- Show table: severity badges, rank deltas (red = jumped up, green = dropped)
- Click **Run Watchdog**: "This triggers one detection cycle synchronously."
- Click any **critical row** → alert detail

On alert detail:
> "Full context: what rule fired, what the metric was, the score delta.
> And a direct button to trigger the Investigator on this specific alert."

### 5. Investigations — ReAct loop (60–90s)

Navigate to: **`/ai/investigations`**

> "When an alert is serious enough to investigate, the Investigator runs a
> ReAct loop — Reason, Act, Observe — calling six tools: priority board lookup,
> metric retrieval, historical comparison, web search via Tavily MCP, and more."

- Click any investigation row → detail
- Show **Reasoning Trace** section: "Each step is transparent — thought, tool call, result"
- Click **"Full trace in LangSmith →"**: "The full execution graph, reproducible"

### 6. Briefings — Executive output (60s)

Navigate to: **`/ai/briefings`**

- Click most recent briefing
- Scroll through the rendered markdown
> "The Briefer synthesises everything — alerts, investigations, metrics —
> into an executive-level document. This is what a head of digital would read."
- Click **"View reasoning trace →"**: shows the briefing's reasoning path
- Expand **Referenced investigations**: "fully linked to the underlying work"

### 7. Close (30s)

> "The entire AI layer is additive — V1 still runs independently. The backend
> is FastAPI with LangGraph for the multi-step supervisor, ChromaDB for RAG,
> and a semantic layer across 59 metrics. The frontend wires all four agents
> into a unified interface with zero modifications to the existing V1 pages."

---

## Key talking points per interviewer type

| Interviewer focus | Emphasise |
|---|---|
| AI / ML | LangGraph ReAct loop, ChromaDB RAG, deterministic-first classifier, eval pipeline (40 golden questions, RAGAS scorer) |
| Backend | FastAPI router structure, Pydantic schemas, LangSmith tracing, idempotent briefing cache |
| Frontend | Additive architecture (zero V1 modifications), lazy-loaded routes, error boundary, 30s alert polling |
| Product | End-to-end loop: anomaly → alert → investigation → briefing, all linkable |

---

## Fallback plan

### If OpenAI / LLM quota is exhausted (most likely issue)

The chat and investigation pages will show `ERROR · Xs` with the 429 message.
Alerts and Briefings still work (they're data reads, not LLM calls).

**Recovery during demo:**
1. Navigate to `/ai/alerts` — show the table and Run Watchdog (works without LLM)
2. Open a briefing from before the quota ran out — full markdown renders fine
3. > "The LLM API key needs a top-up — but you can see the data layer and
>    frontend are fully functional. Let me show you the code architecture instead."
4. Open `clubos2/supervisor/entry_point.py` and walk through the dispatch logic

### If the frontend won't start (port conflict)

```bash
# Kill whatever is on 5173/5174
lsof -ti:5173,5174 | xargs kill -9
cd apps/clubos-web && npm run dev
```

Or use the pre-recorded screenshots in `docs/frontend_ai_demo_screenshots/`.

### If the backend won't start (port 8001 conflict)

```bash
lsof -ti:8001 | xargs kill -9
PYTHONPATH=$(pwd) uvicorn app.main:app --port 8001 --app-dir backend/api
```

Or use port 8002 and update `.env.development`:
```
VITE_API_BASE_URL=http://localhost:8002
```

### If a specific page crashes (JS error)

The `AIErrorBoundary` catches it — you'll see a clean error screen with a
"Try again" button. Skip to a working page and continue. The rest of the app
is unaffected.

### If everything is broken

Fall back to Postman + code walkthrough:
```bash
# Live API demo via curl
curl -X POST http://localhost:8001/api/ai/supervisor/query \
  -H "Content-Type: application/json" \
  -d '{"query": "what is streaming_daily_users this month?"}'
```

Narrate the architecture from `AGENTS.md` and `clubos2/README.md`.

---

## Architecture quick-reference (for Q&A)

```
POST /api/ai/supervisor/query
  → ClassifierV2 (deterministic rules, zero LLM cost)
      → direct_scout      → Scout (RAG over 59-metric semantic layer)
      → direct_briefer    → Briefer (monthly synthesis)
      → direct_investigator → Investigator (LangGraph ReAct)
      → langgraph_supervisor → Multi-step planner (LangGraph)

Watchdog (cron / manual):
  → 6 detection rules against gold_priority_board.csv
  → Dedup window (7 days LTM)
  → Alerts stored in DuckDB, surfaced via /api/ai/watchdog/alerts

Investigator:
  → 6 tools: priority_board, metric_history, rank_history,
             web_search (Tavily MCP), cross_metric, alert_context
  → LangGraph ReAct loop (max 8 steps)
  → Findings + reasoning trace stored, linked to alert

Eval:
  → 40 golden questions (v3) + 10 holdout
  → Fabrication scorer (0/40 fabrications at baseline)
  → Behavioural scorer (0.85 pass rate at baseline)
  → CI gate: PR fails if either metric regresses
```

---

## One last thing

**Rehearse out loud, three times minimum.**

The first run you'll fumble the narration. By the third you're smooth.
Time each run — target under 8 minutes. If you're over 10, cut the
investigations section and go straight from Alerts to Briefings.
