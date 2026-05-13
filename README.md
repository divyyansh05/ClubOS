# ClubOS

**A monthly digital business operating system for elite football clubs.**

ClubOS turns recurring monthly digital business data into a repeatable workflow for digital and commercial teams. Instead of only showing charts, ClubOS helps clubs understand what changed, where they stand against peers, which signals matter commercially, and what deserves attention first.

---

## What This Is

ClubOS is a working MVP demonstrating:

- **Priority Board** — Ranked business issues and opportunities (hero feature)
- **Command Center** — Digital ecosystem health overview
- **Peer Benchmark** — KPI comparison against peer clubs
- **Commercial Signal Engine** — Validated leading indicators
- **Monthly Briefing** — Leadership-ready monthly summary

Every month: **new data in → same workflow → clear priorities out.**

---

## Current State

**MVP Complete** ✅

- ✅ 5 core screens functional with real data
- ✅ Databricks Gold tables (priority_board, kpi_health, peer_benchmark, signal_relationships, monthly_brief_inputs)
- ✅ Backend API (FastAPI with typed contracts)
- ✅ Frontend (React + TypeScript)
- ✅ 23 executable regression tests
- ✅ Local snapshot mode (no Databricks credentials required)

**Demo-ready:**
- Run `./scripts/run_all_tests.sh` → all tests pass
- Navigate to `http://localhost:5176` → Priority Board loads
- Click "View evidence" → score breakdown modal works
- All 6 MVP pages accessible

---

## Quick Start

### 1. Install dependencies

```bash
./scripts/bootstrap.sh
```

This creates Python venv + installs all dependencies.

**Manual install:**
```bash
# Python dependencies
python3.11 -m venv clubosvenv
source clubosvenv/bin/activate
pip install -r requirements/dev.txt

# Frontend dependencies
cd apps/clubos-web
npm install
```

### 2. Run the application

**Terminal 1 - Backend:**
```bash
cd backend/api
source ../../clubosvenv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd apps/clubos-web
npm run dev
```

**Terminal 3 - Tests:**
```bash
./scripts/run_all_tests.sh
```

### 3. Open the app

Navigate to: **http://localhost:5176**

Default landing: **Priority Board** (hero feature)

---

## Environment Configuration

**Local snapshot mode (default):**
No configuration needed. Backend auto-detects `data/gold_snapshots/` and serves local data.

**Live Databricks mode (optional):**
1. Copy `.env` template: `cp backend/api/.env.example .env`
2. Fill in Databricks credentials from `~/.databrickscfg`
3. Restart backend

**Full setup guide:** [`docs/delivery/ENV_SETUP.md`](docs/delivery/ENV_SETUP.md)

---

## Demo Flow

1. **Priority Board** — Top-ranked issues (e.g., #1: Conversion Weakness in Ecommerce, score 0.96)
2. **View evidence** — Click "View evidence" → see score breakdown (severity, persistence, peer_gap, commercial_weight, supporting_evidence)
3. **Peer Benchmark** — Select "eCommerce - Conversion Rate" → Real Madrid rank #4/5, gap to median visible
4. **Signal Engine** — See validated signals (e.g., website traffic → ecommerce sales, 1mo lag, 70% strength)
5. **Monthly Briefing** — Leadership summary (top 3 priorities, anomalies, benchmark/health summaries)

**Full demo script:** [`docs/demos/demo_script.md`](docs/demos/demo_script.md)

---

## Technical Stack

**Data layer:**
- Databricks medallion architecture (Bronze → Silver → Gold)
- Python 3.11 notebooks
- Delta Lake tables

**Backend:**
- FastAPI (Python 3.11)
- Pydantic schemas
- Snapshot mode + optional live Databricks SQL

**Frontend:**
- React 18
- TypeScript
- Vite (dev server)

**Quality:**
- 23 executable regression tests
- Gold snapshot validation
- API contract tests
- UI smoke tests

---

## Repository Structure

```
.
├── AGENTS.md                    # AI agent build constraints
├── REPO_STRUCTURE.md            # Folder ownership
├── agents/                      # Role definitions
├── apps/clubos-web/            # Frontend (React + TypeScript)
├── backend/api/                 # Backend API (FastAPI)
├── data/gold_snapshots/         # Local Gold table exports (CSV)
├── databricks/notebooks/        # Data pipeline (Bronze/Silver/Gold/Analytics/Quality)
├── docs/                        # Product, architecture, delivery docs
├── scripts/                     # Bootstrap, test runners
└── tests/                       # Executable regression tests
```

---

## Testing

**Run all tests:**
```bash
./scripts/run_all_tests.sh
```

**Individual test suites:**
```bash
# Gold snapshot validation
python tests/data/validate_gold_snapshots.py

# API contract tests
pytest backend/api/tests/test_api_contracts.py -v

# UI smoke tests
./tests/ui/smoke_test.sh
```

**Test coverage:**
- ✅ 5 Gold tables validated (structure, columns, data types)
- ✅ 7 API endpoints tested (schema contracts)
- ✅ 6 MVP pages tested (HTTP 200, title validation)

---

## Source Of Truth Documents

**Product:**
- [`docs/product/clubos_product_definition_report.md`](docs/product/clubos_product_definition_report.md) — Product vision
- [`docs/product/clubos_mvp_spec.md`](docs/product/clubos_mvp_spec.md) — MVP scope
- [`docs/product/clubos_screen_blueprint.md`](docs/product/clubos_screen_blueprint.md) — Screen-level UX

**Architecture:**
- [`docs/architecture/clubos_databricks_schema_plan.md`](docs/architecture/clubos_databricks_schema_plan.md) — Data pipeline design
- [`docs/architecture/gold_table_contracts.md`](docs/architecture/gold_table_contracts.md) — Gold table schemas
- [`docs/architecture/api_contract.md`](docs/architecture/api_contract.md) — Backend API contracts

**Delivery:**
- [`docs/delivery/project_execution_memory.md`](docs/delivery/project_execution_memory.md) — Build session log
- [`docs/demos/demo_script.md`](docs/demos/demo_script.md) — Demo walkthrough

---

## Runtime Versions

- **Python:** 3.11.9 (`.python-version`)
- **Node.js:** 20.16.0 (`.nvmrc`)
- **npm:** 10.8.1 (`package.json`)

All pinned for reproducibility.

---

## Key Design Principles

**Recurring monthly workflow:**
- ClubOS is not a one-off dashboard
- Designed for same process every month
- New data in → same logic → updated priorities

**Deterministic logic:**
- Priority scores from weighted formula (not AI black box)
- Benchmark gaps polarity-aware (bounce_rate = lower is better)
- Signals statistically validated (not random correlations)

**Traceable evidence:**
- Every score has breakdown
- Supporting metrics visible
- Peer context included
- Gold table → API → UI chain inspectable

**Hero feature:**
- **Priority Board** is landing page (not Command Center)
- Ranked business attention first, exploration second

---

## Important Constraints

**Monthly data only:**
- ClubOS does NOT support day-level precision
- All timing is month-grain

**AI role:**
- AI can enhance wording later (optional)
- AI does NOT rank priorities or determine signals
- Core logic is deterministic
- If AI fails, product still works

**Benchmark scope:**
- Only 8 metrics benchmarked (across 4 assets)
- Unsupported metrics hidden in benchmark view
- Peer group: 5 elite clubs

---

## Next Steps (Post-MVP)

**Production hardening:**
- Add authentication/authorization
- Deploy to cloud (AWS/Azure/GCP)
- Add monitoring/logging
- Harden Databricks orchestration

**Feature expansion:**
- Event Intelligence module
- Scenario simulator
- PDF export for Monthly Briefing
- Tableau integration layer
- AI-enhanced wording (optional)

**Data expansion:**
- Add more peer clubs
- Support additional KPIs
- Day-level data streams (if available)

---

## Working Principle

> **New data in. Same workflow. Clear priorities out.**

ClubOS is a monthly operating system, not a static dashboard.

---

## License

Proprietary - Real Madrid Internship Project

---

## Contact

For questions about this repository:
- Check [`docs/delivery/project_execution_memory.md`](docs/delivery/project_execution_memory.md) for build history
- Review [`AGENTS.md`](AGENTS.md) for AI agent constraints
- See [`docs/demos/demo_script.md`](docs/demos/demo_script.md) for demo walkthrough
