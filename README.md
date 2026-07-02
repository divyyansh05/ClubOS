# ClubOS

A recurring monthly digital business operating system for elite football clubs. Ingests monthly KPI files, runs deterministic scoring and benchmark logic, surfaces ranked priorities, and layers AI-powered investigation and briefing on top of structured data.

**This is not a dashboard. It is a monthly operating system.**

---

## Project state (as of 2026-07-02)

| Layer | Status |
|---|---|
| V1 product (Priority Board, Benchmarks, Signal Engine, Briefing) | ✅ Complete |
| V2 Phase 1 — Semantic layer + RAG + Scout agent | ✅ Complete |
| V2 Phase 2 — Evals + Guardrails + Observability | ✅ Complete |
| V2 Phase 3 — Watchdog + LTM memory | ✅ Complete |
| V2 Phase 4 — Investigator + MCP web search | ✅ Complete |
| V2 Phase 5 — Briefer + LangGraph supervisor | 🔜 Next |

Tests: **461 passing** (167 v1 + 294 v2), 7 skipped (E2E gated). Run from project root: `pytest`

---

## Agent entry points

Every agent must read these before doing any work:

| Document | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Build constraints, ownership rules, non-negotiables, definition of done |
| [`CLAUDE.md`](CLAUDE.md) | Current session state — branch, test count, last milestone, key files |
| [`REPO_STRUCTURE.md`](REPO_STRUCTURE.md) | Canonical folder layout and ownership map |
| [`docs/eval_methodology.md`](docs/eval_methodology.md) | How AI outputs are evaluated — three-layer deterministic-first strategy |
| [`docs/phase4_completion.md`](docs/phase4_completion.md) | What Phase 4 built, verified facts, Phase 5 entry checklist |

---

## Codebase layout

```
clubos2/          # V2 AI layer — agents, eval, RAG, tools, watchdog, investigator
backend/api/      # V1 FastAPI backend — serves Gold tables + V2 AI endpoints
apps/clubos-web/  # V1 React frontend
data/             # Gold CSV snapshots (source of truth for V1 scoring)
eval/             # Golden sets, holdout set, eval reports
prompts/          # Versioned agent prompts (scout_v1–v4, investigator_v1)
tests_v2/         # All V2 unit + integration tests
docs/             # Architecture, methodology, completion reports
var/              # Local runtime state — DuckDB, ChromaDB, SQLite (gitignored)
```

---

## Key commands

```bash
# Run all tests (v1 + v2) from project root
pytest

# Run only v2 tests
pytest tests_v2/

# Seed semantic layer + ingest RAG
make v2-seed && make v2-ingest

# Run eval against golden set (skip RAGAS for speed)
make v2-eval

# Run holdout eval
make v2-eval-holdout

# Run CI gate vs baseline
make v2-ci-gate

# Start backend (port 8000)
cd backend/api && uvicorn app.main:app --reload --port 8000
```

---

## Rules every agent must follow

These are load-bearing constraints, not suggestions. Full rationale is in [`AGENTS.md`](AGENTS.md).

- **Never modify v1 code** to serve a v2 feature. V2 extends V1 additively. V1 must stay independently deployable.
- **AI is a support layer.** Scoring, ranking, and KPI logic are deterministic Python. LLMs explain; they do not score.
- **Eval discipline is mandatory.** Every prompt change must be re-evaluated against the golden set and compared to `eval/reports/baseline.json`. Run `make v2-eval` before claiming a prompt improvement.
- **Run tests from project root.** `pytest` uses `pyproject.toml` testpaths and picks up both v1 and v2 suites correctly.
- **Do not commit secrets.** `.env.v2` is gitignored. Use `.env.v2.example` (tracked, empty keys) as the template.
- **Priority Board is the hero feature.** Every new screen and AI output must be traceable to it.

---

## V2 API endpoints (Phase 1–4)

| Endpoint | Phase | Purpose |
|---|---|---|
| `POST /api/ai/query` | 1 | Scout — answers questions from RAG + semantic layer |
| `POST /api/ai/watchdog/run` | 3 | Trigger Watchdog — detects rank-change anomalies |
| `GET /api/ai/watchdog/alerts` | 3 | Query alerts with filters |
| `POST /api/ai/watchdog/alerts/{id}/acknowledge` | 3 | Acknowledge an alert |
| `POST /api/ai/investigator/run/{alert_id}` | 4 | Trigger Investigator on a Watchdog alert |
| `GET /api/ai/investigator` | 4 | List past investigations |
| `GET /api/ai/investigator/{id}` | 4 | Get a single investigation |
