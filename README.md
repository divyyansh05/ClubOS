# ClubOS

**An agentic AI operating system for the digital business of elite football clubs.**

ClubOS turns nine years of a football club's digital business data — across web, e-commerce, streaming, social, and mobile app — into a system that does more than display charts. It monitors the business continuously, investigates what changed and why, composes leadership-ready briefings, and answers natural-language questions with cited, verifiable numbers. It was built for Real Madrid's digital business analytics team during an AI engineering internship, on top of a live production data platform.

> **New data in. Same workflow. Clear priorities out — now with agents that monitor, investigate, and explain.**

---

## Table of Contents

**Part I — The Problem and the Solution** (business & deployment perspective)
- [The Problem](#the-problem)
- [What ClubOS Does](#what-clubos-does)
- [Who Uses It and How](#who-uses-it-and-how)
- [The Monthly Workflow](#the-monthly-workflow)
- [The Five Screens + The AI Layer](#the-five-screens--the-ai-layer)
- [Why This Matters Commercially](#why-this-matters-commercially)

**Part II — How It's Built** (engineering perspective)
- [System Architecture](#system-architecture)
- [The Four Agents](#the-four-agents)
- [The Hybrid Supervisor](#the-hybrid-supervisor)
- [Retrieval Architecture](#retrieval-architecture)
- [The Semantic Layer](#the-semantic-layer)
- [Evaluation and Guardrails](#evaluation-and-guardrails)
- [Data Integrity](#data-integrity)
- [Deployment](#deployment)
- [Technical Stack](#technical-stack)

**Part III — Running It**
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Testing](#testing)
- [Repository Structure](#repository-structure)

---

# Part I — The Problem and the Solution

## The Problem

Every elite football club runs a large digital business: a website with millions of monthly visitors, an e-commerce store, a subscription streaming platform, social channels with hundreds of millions of followers, and a mobile app. Each of these generates continuous data. Each is owned by a different team, in a different tool, formatted differently, updated on a different cadence.

When commercial leadership needs to answer a question as simple as *"which parts of our fan business need attention this month, and why?"*, the honest answer is that getting to that answer used to take weeks. Analysts exported data from four or five systems, reconciled it by hand in spreadsheets, made judgement calls about what looked concerning, chased down explanations, and produced a slide deck. By the time the review was ready, the month was over and the next one had begun.

This is not a tooling problem in the usual sense. The dashboards existed. The data existed. What was missing was a **coherence layer** — something that could look across every platform at once, apply a consistent framework for judging what matters, explain *why* things changed, and surface all of it in one place, on demand, every month, without weeks of manual work.

ClubOS is that layer.

## What ClubOS Does

ClubOS operates the digital business the way a small, tireless analytics team would — if that team never slept, never lost context between months, and cited a source for every number it ever produced.

It does five things:

1. **Ranks what matters.** A deterministic priority engine scores 59 business metrics across five platforms every month on a five-component formula (severity, persistence, peer gap, commercial impact, evidence) and produces a single ranked Priority Board: what to fix first.

2. **Monitors continuously.** A monitoring agent (Watchdog) watches the Priority Board for meaningful change — a metric entering the top ten, a rank jump, a score swing — and raises alerts the moment something warrants attention, deduplicated so leadership isn't spammed.

3. **Investigates automatically.** When a critical alert fires, an investigation agent (Investigator) is triggered automatically. It reasons step by step — pulling metric history, peer benchmarks, internal context, and public web signals — and produces a cited hypothesis for *why* the change happened, with a full audit trail of its reasoning.

4. **Briefs leadership.** A briefing agent (Briefer) composes a monthly executive summary from the month's investigations and alerts — the leadership review that used to take weeks, generated on demand, with every claim traced to a source.

5. **Answers questions.** A question-answering agent (Scout) responds to natural-language questions about any metric — *"what's our streaming conversion rate and is it a problem?"* — with the real number, the context to interpret it, and citations back to the exact data source. It never invents a number.

## Who Uses It and How

ClubOS is built for the people who run a club's digital commercial business — the Head of Data, digital business analysts, and commercial leadership. It meets them where they already work.

- **In the browser.** The five core screens plus an AI Assistant panel where they can chat with Scout, review alerts, read investigations, and generate briefings.
- **In Slack.** Alerts, briefings, and a `@clubos` query interface arrive in the channels the team already lives in. Critical actions — like approving an auto-triggered investigation's conclusion before it reaches leadership — run through a human-in-the-loop approval flow.
- **As a tool for other AI systems.** ClubOS exposes itself as an MCP (Model Context Protocol) server, so an analyst using Claude Desktop or any MCP-aware client can query the club's business directly from their own AI assistant.

The system personalizes to each user — remembering the metrics they care about and the context of prior conversations — so the analyst focused on e-commerce and the one focused on streaming each get an experience shaped around their remit.

## The Monthly Workflow

ClubOS is not a one-off dashboard. It is a recurring monthly operating rhythm:

1. **New data lands** in the Databricks Gold layer (the medallion pipeline runs Bronze → Silver → Gold).
2. **The Priority Board recomputes** — same deterministic formula, updated numbers, new ranking.
3. **Watchdog diffs** the new board against last month and raises alerts on meaningful change.
4. **Critical alerts auto-trigger Investigator**, which produces cited explanations in the background.
5. **Briefer composes** the monthly executive briefing from the month's investigations and alerts — automatically, on a schedule, or on demand.
6. **Leadership reads the briefing**, asks Scout follow-up questions, and decides where to act.

Same process every month. New data in, same workflow, clear priorities out.

## The Five Screens + The AI Layer

| Screen | Route | What it answers |
|--------|-------|----------------|
| **Priority Board** | `/priorities` | What should we fix first this month? *(hero feature)* |
| **Command Center** | `/command-center` | How healthy is our entire digital portfolio? |
| **Peer Benchmark** | `/benchmark` | Where do we stand vs competitor clubs? |
| **Signal Engine** | `/signals` | What is likely to change in the next 1–3 months? |
| **Monthly Briefing** | `/briefing` | What does leadership need to know right now? |
| **AI Assistant** | `/ai/*` | Ask anything; review alerts, investigations, and briefings live |

The AI Assistant section is where the four agents surface directly to the user:

- **`/ai/chat`** — natural-language Q&A routed to the right agent, with citations and a link to the full reasoning trace on every answer
- **`/ai/alerts`** — Watchdog alerts with severity, one-click "investigate" action
- **`/ai/investigations`** — Investigator findings with the step-by-step ReAct reasoning trace made visible
- **`/ai/briefings`** — generated executive briefings, rendered as leadership-ready documents

## Why This Matters Commercially

The digital business of an elite club is worth hundreds of millions in annual revenue across memberships, merchandise, streaming subscriptions, and sponsorship-linked engagement. The difference between catching a conversion-rate decline in week one versus month three is measured directly in lost revenue.

ClubOS compresses the club's decision loop from weeks to minutes and does it with a discipline that makes the output trustworthy at the executive level: **every number is cited, no number is ever fabricated, and every AI conclusion carries an inspectable audit trail.** That trust property is what lets an AI system operate a real business rather than just describe it.

---

# Part II — How It's Built

This half is for engineers. It covers the architecture, the agent design, the retrieval strategy, and the evaluation discipline that make ClubOS trustworthy in production.

## System Architecture

ClubOS is two layers. The **v1 layer** is a deterministic data platform: a Databricks medallion pipeline producing 59 business metrics, a five-component priority-scoring engine, a signal engine validating leading indicators, a FastAPI backend, and a React frontend — deployed and in production. The **v2 layer** is an agentic AI operating system built *additively* on top of v1: four agents, a hybrid supervisor, a semantic layer, a retrieval stack, an evaluation framework, and guardrails.

The governing architectural principle is **additive-only**. Every line of v2 code lives in a `clubos2/` namespace. The only modification ever made to v1 code is adding route-registration lines in the API entrypoint. This means v2 can never break v1's production stability — the physical separation makes accidental regressions structurally impossible.

The second governing principle is **deterministic-first**. Any step that can be done with a database lookup, a business rule, or a SQL query is done that way. LLMs are the *last* step, invoked only when genuine reasoning is required — never as the first reflex. This is why numeric retrieval, alert detection, and query routing are all deterministic, while only explanation, briefing composition, and complex multi-step orchestration involve an LLM.

## The Four Agents

Not everything called an "agent" is one, and ClubOS is deliberate about the distinction.

### Scout — the question-answering compound system
Scout answers questions about the data. It is **not** an autonomous agent — it is a compound system with a fixed pipeline: resolve the metric deterministically via the semantic layer, retrieve the value and context, then make a single LLM call to compose a grounded answer. The LLM never chooses tools and never generates numbers. It composes prose around values that were already retrieved. This is what makes Scout's fabrication rate structurally zero.

### Watchdog — the deterministic monitor
Watchdog detects meaningful change in the Priority Board. It contains **no LLM at all**. Detection is arithmetic — did a metric enter the top ten, did its rank move by ≥5, did its score swing by ≥0.20 — and arithmetic belongs in Python, not in a prompt. Watchdog also deduplicates alerts against a long-term memory table so leadership isn't alerted twice for the same event. When it raises a critical alert, it auto-triggers Investigator in a fire-and-forget background task.

### Investigator — the true agent
Investigator is the first genuine LLM agent in the system: a LangGraph ReAct loop that, given an alert, decides step by step which tools to call — metric history, peer benchmarks, semantic-layer definitions, internal knowledge retrieval, public web search via an MCP server — observes the results, and reasons toward a cited hypothesis for *why* the change happened. Its state is checkpointed (AsyncSqliteSaver) so runs are resumable, and every step is captured in a reasoning trace that becomes the audit trail. This is the component that answers *"why"*, and it is the one you show an interviewer when they ask whether you've built agents.

### Briefer — the compound composer
Briefer composes monthly executive briefings. It reads from investigations and alerts (the primary sources) plus the agent-memory table (recurring patterns), computes aggregates deterministically (the LLM never counts), and composes a cited narrative. It maintains a `briefings` table that doubles as a **dedup cache**: a repeat request for the same period within a freshness window returns the stored briefing with zero LLM calls, keeping cost bounded.

## The Hybrid Supervisor

User queries enter through a single supervisor that routes them — but routing itself follows the deterministic-first principle.

- **A rule-based classifier runs first** (regex + semantic-layer lookup, sub-10ms, zero LLM). Roughly 80% of queries are obvious: a metric question goes straight to Scout, an alert-with-ID goes to Investigator, a "monthly summary" goes to Briefer.
- **A LangGraph supervisor handles the rest** — complex, ambiguous, or genuinely multi-step queries fall through to an LLM-based planner that composes a plan across agents (Scout → Investigator → synthesis) and executes it.

The framing: *detection is arithmetic, complex routing is reasoning.* Same principle as Watchdog-versus-Investigator, applied one layer up. Every response carries a `dispatch_path` field so it's always visible whether a query took the fast deterministic path or the LLM-orchestrated one.

## Retrieval Architecture

Naive vector-search RAG tops out around 21% accuracy on realistic retrieval tasks — unacceptable for a system a Head of Data will trust. ClubOS uses **three-tier retrieval**, ordered by determinism:

1. **The semantic layer** (Tier 1) — a SQL table with one row per metric, resolving numeric questions deterministically before any LLM or vector search is involved. Same input, same output, always.
2. **Curated skill files** (Tier 2) — human-authored narrative context (how the priority board works, known seasonality, how signals are validated), embedded and retrieved by similarity but small and curated. Every claim in a skill file is one the system is authorized to make.
3. **Vector search** (Tier 3) — broader gold-layer narrative content and history, retrieved via hybrid search (BM25 keyword + dense vector) with a cross-encoder reranker, used only when the first two tiers don't resolve.

Most questions never reach Tier 3. Numeric questions resolve at Tier 1; interpretive questions usually at Tier 2.

## The Semantic Layer

The `metric_registry` table is the heart of the system's reliability. Each of the 59+ metrics has a canonical name, a business name, a definition, unit, polarity, seasonality notes, and — critically — an explicit resolution contract:

- **`gold_lookup_strategy`** — how to find this metric in the gold layer (`exact_match`, `asset_metric_split`, or `compound_priority_id`). The resolver reads the strategy and executes it; it never *guesses* via prefix-splitting. Every resolution is registry-declared and auditable.
- **`preferred_source`** — when a metric appears in multiple gold sources, which one is authoritative. This resolves cross-source disagreements deterministically (see [Data Integrity](#data-integrity)).
- **`is_active`** — whether the metric has live gold data. Inactive metrics are documented but Scout refuses to fabricate a value for them.
- **Aliases and disambiguation** — synonyms map to canonical names ("total sales" → `net_sales`), and queries matching multiple metrics trigger a disambiguation response rather than a guess. Resolution is a curated, deterministic lookup — never LLM-based semantic matching, which would reintroduce non-determinism into the numeric path.

Adding a new metric is a registry row insert, not a code change. A CI test asserts every gold-layer metric is registered, so the registry can never silently drift from the data.

## Evaluation and Guardrails

The system is measured, not vibes-tested.

**Three-layer evaluation, ordered by determinism:**
1. **Fabrication rate** (deterministic) — every number in an answer must appear in retrieved context. Any fabricated number fails CI. Enforced value: zero.
2. **Behavioural compliance** (deterministic) — did the agent refuse when it should, cite the required sources, state assumptions on ambiguous queries, query the expected metrics.
3. **RAGAS** (LLM-judged) — faithfulness, context relevance, answer relevance, run on demand as supplementary signal.

The critical design decision: **deterministic checks gate CI; LLM-judged checks observe.** Using a probabilistic judge to gate a probabilistic system compounds fuzziness. Hard quality guarantees come from checks that produce reproducible, auditable results.

**A hand-authored golden set** (60 visible + 10 holdout) spans quantitative, narrative, mixed, ambiguous, unanswerable, supervisor-routing, and briefer-run question types. The holdout set is never used during prompt iteration — it catches overfitting at development checkpoints. Baseline behavioural pass rate is stable across three back-to-back runs at 0.0pp variance.

**Guardrails at multiple layers:** a no-fabricated-numbers guard scans every response post-LLM; a source-required guard makes it structurally impossible for a retrieval tool to return uncitable data; a prompt-injection defense scans retrieved content before it reaches the model.

**Prompt versioning** — every system prompt is versioned (Scout is at v6); the active version is pinned to the version that produced the baseline, and CI comparisons are meaningless if they diverge.

## Data Integrity

Two gold sources can carry the same metric. A full cross-source integrity audit (12 sources, 242 metrics, 63 cross-source pairs) confirmed **zero value divergences** — where sources appeared to disagree, the cause was *coverage semantics*, not conflicting numbers: the priority board is an intentionally filtered above-threshold view, while the KPI health snapshot is complete. The semantic layer now encodes source authority explicitly via `preferred_source`, so Scout deterministically reads the authoritative source, and a CI test fails if any cross-source metric lacks an authority resolution. The principle mirrors the system's canonical-source discipline: **one metric, one authoritative number, always.**

## Deployment

- **v1** runs in production on **GCP Cloud Run**, with the Databricks medallion pipeline feeding the gold layer, GitHub Actions CI/CD, and keyless authentication via Workload Identity Federation.
- **v2** is designed local-first (DuckDB, ChromaDB, local file storage — the reference implementation runs with zero cloud dependency) and deploys to **Databricks Mosaic AI** for production hosting, importing the `clubos2/` package. Local-first is a discipline, not a limitation: free-tier cloud resources expire and rate-limit, local infrastructure is stable across time, and cloud deployment is recorded proof of production capability rather than a live dependency.

## Technical Stack

**Data & AI**
- Databricks medallion architecture (Bronze → Silver → Gold), Delta Lake
- LangGraph (agent orchestration), LangSmith (tracing/observability)
- OpenAI: `gpt-4o` (Investigator, Briefer reasoning), `gpt-4o-mini` (Scout, routing, RAGAS judge), `text-embedding-3-small`
- ChromaDB (vector store), hybrid retrieval (BM25 + dense + cross-encoder rerank)
- RAGAS (supplementary eval), MCP (Model Context Protocol — web search + ClubOS-as-server)

**Backend**
- FastAPI (Python 3.11), Pydantic v2 typed contracts
- DuckDB (semantic layer, agent memory, alerts, investigations, briefings — local), Postgres-compatible schema for production
- Tenacity retry-with-backoff on all external API calls

**Frontend**
- React 18, TypeScript, Vite
- AI Assistant panels: chat, alerts, investigations (with ReAct trace visualization), briefings (rendered markdown)

**Quality**
- 600+ automated tests (unit, contract, integration, end-to-end resolution)
- Deterministic eval pipeline with CI gate
- Golden set with holdout discipline

---

# Part III — Running It

## Quick Start

For developers familiar with the toolchain.

```bash
# 1. Install
./scripts/bootstrap.sh          # creates Python venv + installs deps
cd apps/clubos-web && npm install && cd ../..

# 2. Run — Terminal 1 (backend)
cd backend/api
source ../../clubosvenv/bin/activate
PYTHONPATH=$(git rev-parse --show-toplevel) uvicorn app.main:app --reload

# 3. Run — Terminal 2 (frontend)
cd apps/clubos-web
npm run dev

# 4. Open
# http://localhost:5173  → Priority Board (landing)
# http://localhost:5173/ai/chat  → AI Assistant
```

**Environment:** Local snapshot mode is the default — no credentials needed; the backend auto-detects `data/gold_snapshots/`. The AI layer requires an OpenAI key: copy `.env.v2.example` to `.env.v2` and set `OPENAI_API_KEY`.

> **Note:** the backend must start with `PYTHONPATH` set to the repo root so the `clubos2` and `eval` packages resolve. The Quick Start command above handles this via `git rev-parse`.

## Detailed Setup

<details>
<summary><strong>First time with Git / Python / Node? Click for the full step-by-step guide.</strong></summary>

### Before You Start — Install These Three Things

**Git** (downloads the code)
```bash
git --version
```
If no version appears: Mac → https://git-scm.com/download/mac · Windows → https://git-scm.com/download/win

**Python 3.11** (runs the data engine and AI layer)
```bash
python3 --version   # need 3.11.x
```
If missing or wrong version: https://www.python.org/downloads/ (download 3.11 specifically)

**Node.js 20+** (runs the interface)
```bash
node --version   # need 20+
```
If missing: https://nodejs.org (LTS download)

### Step 1 — Download the project
Open Terminal (Mac: Cmd+Space → "Terminal") or Command Prompt (Windows: Win key → "cmd").
```bash
git clone https://github.com/divyyansh05/clubos.git
cd clubos
```

### Step 2 — Set up the backend
```bash
./scripts/bootstrap.sh
```
If that fails on Windows, run manually:
```bash
python3.11 -m venv clubosvenv
clubosvenv\Scripts\activate          # Windows
# source clubosvenv/bin/activate     # Mac/Linux
pip install -r requirements/dev.txt
```

### Step 3 — Configure the AI layer
```bash
cp .env.v2.example .env.v2
# open .env.v2 and set OPENAI_API_KEY=sk-...
```

### Step 4 — Start the backend (Terminal 1)
```bash
cd backend/api
source ../../clubosvenv/bin/activate
PYTHONPATH=$(git rev-parse --show-toplevel) uvicorn app.main:app --reload
```
Running when you see: `Uvicorn running on http://127.0.0.1:8000`
Verify: open http://localhost:8000/docs

### Step 5 — Start the frontend (Terminal 2, keep Terminal 1 open)
```bash
cd clubos/apps/clubos-web
npm install
npm run dev
```
Wait for: `Local: http://localhost:5173`

### Step 6 — Open ClubOS
Browser → **http://localhost:5173** (Priority Board) or **http://localhost:5173/ai/chat** (AI Assistant)

### Troubleshooting

| Problem | Fix |
|---------|-----|
| `pip: command not found` | Use `pip3` |
| `npm: command not found` | Node.js not installed — see above |
| `source: command not found` (Windows) | Use `clubosvenv\Scripts\activate` |
| Port 8000 in use | `lsof -i :8000` then `kill -9 <pid>` |
| Frontend blank page | Ensure backend (Step 4) is running in another terminal |
| `ModuleNotFoundError: clubos2` / `eval` | Backend not started with `PYTHONPATH` set to repo root |
| AI chat returns errors | Check `.env.v2` has a valid `OPENAI_API_KEY` |
| `ModuleNotFoundError` (other) | Re-run `pip install -r requirements/dev.txt` |

</details>

## Testing

```bash
# Everything
./scripts/run_all_tests.sh

# v2 AI layer suite
pytest tests_v2/ -q

# Deterministic eval (paced for OpenAI Tier 1)
make v2-eval

# Holdout eval (overfitting check, run at development checkpoints)
make v2-eval-holdout

# Data integrity audit (cross-source agreement)
make v2-data-integrity

# Metric registry coverage (every gold metric is registered)
make v2-metric-coverage
```

**Coverage:** 600+ tests spanning gold snapshot validation, API contracts, UI smoke tests, agent unit tests, end-to-end metric resolution (every active metric resolves through Scout), cross-source data agreement, and the deterministic eval pipeline with its CI gate.

## Repository Structure

```
.
├── clubos2/                     # v2 AI layer (additive namespace)
│   ├── agents/                  # Scout
│   ├── watchdog/                # Watchdog monitor + alerts + memory
│   ├── investigator/            # Investigator agent (LangGraph ReAct)
│   ├── briefer/                 # Briefer agent + briefings dedup cache
│   ├── supervisor/              # Hybrid classifier + LangGraph supervisor
│   ├── semantic_layer/          # metric_registry, migrations, seed, lookup
│   ├── rag/                     # chunking, embeddings, ingest, hybrid retriever
│   ├── tools/                   # gold_client, registry (Scout/Investigator tools)
│   ├── guardrails/              # no-fabrication, source-required, injection defense
│   ├── gateway/                 # LLM gateway (OpenAI, retry, prompt versioning)
│   ├── observability/           # LangSmith tracing
│   ├── mcp/                     # web-search MCP server + client
│   └── eval/                    # scorers, pipeline, reporter, CI gate
├── apps/clubos-web/             # Frontend (React + TypeScript), incl. /ai/* panels
├── backend/api/                 # FastAPI backend (v1 + v2 routers)
├── data/gold_snapshots/         # Local Gold exports (CSV)
├── databricks/notebooks/        # Data pipeline (Bronze/Silver/Gold/Analytics/Quality)
├── prompts/                     # Versioned system prompts (scout_v1..v6, investigator, briefer)
├── eval/golden/                 # Golden sets + holdout
├── tests/ tests_v2/             # v1 + v2 test suites
├── scripts/                     # Bootstrap, test runners, audits, scheduled briefing
└── docs/                        # Product, architecture, delivery, eval methodology
```

---

## Key Design Principles

- **Additive-only** — v2 never modifies v1 behaviour; production stability is structurally protected.
- **Deterministic-first** — LLMs are the last step, not the first. Detection, retrieval, and routing are deterministic; only explanation and composition use an LLM.
- **Every number cited, none fabricated** — the load-bearing trust guarantee, enforced by a hard CI gate.
- **One metric, one authoritative number** — canonical names, registry-declared resolution, explicit source authority.
- **Measured, not vibes-tested** — hand-authored golden set, deterministic CI gate, holdout discipline, zero-variance baseline.
- **Local-first** — the reference implementation runs with no cloud dependency; cloud is recorded proof, not a live crutch.

---

## Built By

**Divyansh Shrivastava**
Senior Data Engineer · MSc Sports Analytics, Universidad Europea de Madrid (Real Madrid Graduate School)

Built for Real Madrid's digital business analytics team during an AI engineering internship. AI-assisted development (Claude Code) was used as a core part of the engineering workflow — architecture, agent design, evaluation methodology, and quality validation directed by the engineer.

[LinkedIn](https://linkedin.com/in/divyyansh05) · divyyansh99@gmail.com

---

## License

Proprietary — Real Madrid Internship Project
