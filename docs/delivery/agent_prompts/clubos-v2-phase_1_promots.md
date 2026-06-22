# ClubOS 2.0 — Phase 1 Prompts (REVISED for additive extension)

**Approach changed.** Original prompts assumed a monorepo restructure into `apps/api` + `apps/web`. Revised approach: **extend the existing v1 repo additively**. Existing `BACKEND/api/`, `APPS/clubos-web/`, `DATABRICKS/`, `DATA/`, and `TESTS/` directories are NOT touched. All new v2 code lives in new top-level folders.

**Why the change.** v1 is live in production on GCP Cloud Run with 36 passing tests. The senior call is: do not destabilise a working production system to enable structure you won't need until Phase 6. Add new folders alongside; never move existing ones.

**What this file contains.** Only the prompts that changed. Prompts 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, and 4.1 from the original file are unchanged — they only touch `packages/` which works identically in either layout. Use the original file for those.

**Prompts that changed (use the versions below):**
- Prompt 0.1 — completely rewritten (no restructure, only new folders added)
- Prompt 1.1 — Makefile and mypy targets updated to reflect existing paths
- Prompt 3.4 — `query_metrics` now reads from existing `DATA/gold_snapshots/` CSVs (no new Gold DuckDB needed for Phase 1)
- Prompt 4.3 — router added inside existing `BACKEND/api/app/routers/`, not in a new `apps/api/`
- Prompt 5.1 — completion-report checklist updated to remove "monorepo restructure complete"

---

# Stage 0 — Additive extension (1 prompt)

## Prompt 0.1 — Add v2 directories to the existing ClubOS repo (REWRITTEN)

```
You are extending the existing ClubOS v1 repository to host ClubOS 2.0 code, WITHOUT moving, renaming, or restructuring any existing v1 directory. v1 is live in production on GCP Cloud Run with 36 passing tests; the operating principle is "additive only — touch nothing that works."

The existing layout (DO NOT TOUCH):
- AGENTS/                         (existing — v1 agent role markdown files)
- APPS/clubos-web/                (existing — React/Vite frontend, port 5174)
- BACKEND/api/                    (existing — FastAPI backend, port 8000)
  - app/main.py
  - app/routers/                  (existing routers: priorities.py, signals.py, etc.)
  - app/services/
  - app/schemas/
  - app/clients/databricks.py
  - app/config/
  - tests/                        (existing 36 pytest tests)
- DATA/gold_snapshots/             (existing — CSV snapshots used as the Gold layer in dev)
- DATA_CONTRACTS/                  (existing)
- DATABRICKS/                      (existing — medallion pipeline notebooks)
- DOCS/                            (existing)
- INTEGRATIONS/                    (existing connector stubs)
- SCRIPTS/                         (existing)
- TESTS/                           (existing top-level test stubs)
- REQUIREMENTS/                    (existing — base.txt, dev.txt, databricks-local.txt)

Add the following NEW top-level directories. Do not modify anything outside this list.

NEW directories (all at repo root, alongside existing ones):

clubos2/                          ← NEW namespace for all v2 Python code
├── __init__.py
├── gateway/
│   └── __init__.py
├── observability/
│   └── __init__.py
├── semantic_layer/
│   ├── __init__.py
│   └── migrations/
├── rag/
│   ├── __init__.py
│   └── skills/
├── tools/
│   └── __init__.py
├── agents/
│   └── __init__.py
└── guardrails/
    └── __init__.py

prompts/                          ← NEW (versioned agent system prompts)
└── .gitkeep

eval/                             ← NEW (golden set + eval scripts, used in Phase 2)
└── golden/
    └── .gitkeep

var/                              ← NEW (local-only runtime files; gitignored)
└── .gitkeep

tests_v2/                         ← NEW (Phase 1 tests; kept separate from v1's BACKEND/api/tests/)
└── __init__.py

Why `clubos2/` instead of `packages/`: a Python namespace that imports cleanly as `from clubos2.agents.scout import run_scout` is clearer than the generic `packages.`. It also signals "this is the v2 codebase" without colliding with any existing v1 module name.

Files to create or modify at repo root:

1. CREATE pyproject.toml at repo root if it does not exist; otherwise APPEND to it (do not overwrite).
   - Define a project namespace `clubos2` that points to the new clubos2/ folder
   - Add optional dependency groups [v2-runtime] and [v2-dev] containing only the new v2 deps (defined in Prompt 1.1)
   - Do NOT touch the existing REQUIREMENTS/base.txt or REQUIREMENTS/dev.txt — v1 keeps its dependency management

2. CREATE Makefile at repo root if it does not exist; otherwise APPEND to it.
   Add ONLY new targets, prefixed with v2- to avoid colliding with existing make targets:
   - make v2-setup       → installs v2 deps into a new venv (clubos2venv) or the existing clubosvenv
   - make v2-lint        → runs ruff check clubos2/ tests_v2/
   - make v2-typecheck   → runs mypy clubos2/
   - make v2-test        → runs pytest tests_v2/
   - make v2-ingest      → runs the RAG ingestion (Stage 3)
   - make v2-seed        → seeds the semantic layer (Stage 2)
   Do not modify existing make targets.

3. APPEND to the root .gitignore (create if missing):
   var/
   .env.v2
   .langsmith/
   clubos2/**/__pycache__/
   tests_v2/**/__pycache__/
   
4. CREATE .env.v2.example at repo root with placeholders:
   ANTHROPIC_API_KEY=
   OPENAI_API_KEY=
   LANGSMITH_API_KEY=
   LANGSMITH_PROJECT=clubos-2
   CHROMA_PERSIST_DIR=./var/chroma
   SEMANTIC_DB_URL=duckdb:///./var/clubos_semantic.duckdb
   GOLD_SNAPSHOTS_DIR=./DATA/gold_snapshots     # reuse existing v1 data
   
5. CREATE clubos2/README.md briefly documenting:
   - What clubos2/ is (the v2 agentic layer)
   - That it lives alongside v1, does not modify v1
   - How to install: `pip install -e ".[v2-runtime,v2-dev]"` from repo root
   - How to run tests: `make v2-test`
   - That `clubos2/` imports cleanly via `from clubos2.X.Y import Z` because it has __init__.py files

Critical constraints:
- DO NOT touch BACKEND/api/, APPS/clubos-web/, DATABRICKS/, DATA/, DOCS/, TESTS/, INTEGRATIONS/, SCRIPTS/, REQUIREMENTS/, AGENTS/, or any file inside them.
- DO NOT modify the existing FastAPI main.py, the existing routers, or the existing requirements files.
- DO NOT change the GCP Cloud Run deployment configuration. v1 must remain deployable exactly as it is today.
- All Phase 1 v2 code will live inside clubos2/. Phase 1 only ADDS one file inside BACKEND/api/app/routers/ — that happens in Prompt 4.3, not now. For Prompt 0.1 BACKEND is fully untouched.
- Verify the existing v1 backend still starts: after the additions, `cd BACKEND/api && pytest tests/` must still pass all 36 tests, and `cd BACKEND/api && uvicorn app.main:app --reload` must still start cleanly with no import errors.

Acceptance criteria:
1. `tree -L 2 -I 'node_modules|__pycache__|.git|var|clubosvenv'` shows BOTH the original v1 layout AND the new clubos2/, prompts/, eval/, var/, tests_v2/ directories at the repo root.
2. `cd BACKEND/api && pytest tests/` still passes all 36 v1 tests (regression check).
3. `cd BACKEND/api && uvicorn app.main:app --port 8000` still starts the v1 FastAPI server with no errors.
4. `cd APPS/clubos-web && npm run build` still succeeds (frontend untouched).
5. `python -c "import clubos2; print(clubos2.__file__)"` works from repo root, confirming the new namespace is importable.
6. `cat .gitignore | grep -E "var/|.env.v2"` confirms the new gitignore lines are present.

Verify before next prompt:
- Run `cd BACKEND/api && pytest tests/` — expect 36 passing
- Run `cd BACKEND/api && uvicorn app.main:app --reload --port 8000` in one terminal
- In another terminal, hit `curl http://localhost:8000/priorities` (or whatever your v1 health-check endpoint is) and confirm it returns data
- Only then proceed to Prompt 1.1

This prompt's success is measured by what it does NOT break, not what it adds.
```

---

# Stage 1 — Foundations

## Prompt 1.1 — Python dependencies and dev tooling (REVISED)

```
Configure root pyproject.toml for ClubOS 2.0 Phase 1 dependencies, isolated from v1's existing requirements management. v1 uses REQUIREMENTS/base.txt, dev.txt, databricks-local.txt — leave those completely alone.

Approach: a single pyproject.toml at the repo root defines a new package `clubos2` and its dependencies in optional groups. v1's pip install workflow is unchanged.

Required runtime dependencies for [v2-runtime] group:
- fastapi
- uvicorn[standard]
- pydantic (v2)
- pydantic-settings
- anthropic
- openai (for text-embedding-3-small embeddings only)
- langchain
- langchain-core
- langchain-anthropic
- langchain-openai
- langchain-community
- langgraph
- langsmith
- chromadb
- rank-bm25
- sentence-transformers
- httpx
- python-dotenv
- sqlalchemy
- duckdb
- pyyaml

Optional [v2-dev] group:
- ruff
- mypy
- pytest
- pytest-asyncio
- pytest-cov

Optional [v2-eval] group (used in Phase 2, define now):
- ragas

pyproject.toml structure (create or append; do not destroy any existing content):

[project]
name = "clubos2"
version = "0.1.0"
description = "ClubOS 2.0 — the agentic AI layer on top of ClubOS v1"
requires-python = ">=3.11"
dependencies = []  # empty — runtime deps live in optional groups so v1 install is unaffected

[project.optional-dependencies]
v2-runtime = [...as listed above...]
v2-dev = [...]
v2-eval = [...]

[tool.setuptools.packages.find]
include = ["clubos2*"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]

[tool.mypy]
files = ["clubos2"]            # scope mypy to v2 only; do not touch v1
strict = true
python_version = "3.11"

[tool.pytest.ini_options]
testpaths = ["tests_v2"]        # v2 tests only; v1 tests run separately from BACKEND/api/
asyncio_mode = "auto"

Update root Makefile, appending the v2- prefixed targets defined in Prompt 0.1, now with concrete commands:
- v2-setup: `pip install -e ".[v2-runtime,v2-dev]"`
- v2-lint: `ruff check clubos2/ tests_v2/ && ruff format --check clubos2/ tests_v2/`
- v2-typecheck: `mypy clubos2/`
- v2-test: `pytest tests_v2/`
- v2-run-api: NOT NEEDED — the API runs via the existing v1 backend, which we extend in Prompt 4.3

Critical constraints:
- v1's existing pip install path (REQUIREMENTS/base.txt, dev.txt) must continue to work without modification.
- A developer installing v1 only does `pip install -r REQUIREMENTS/base.txt` and gets no v2 deps.
- A developer working on v2 does `pip install -e ".[v2-runtime,v2-dev]"` from repo root.
- The v2 install will share the venv with v1 if a developer wants both — verify there are no version conflicts between v1's pinned deps and v2's. If a conflict exists (e.g., pydantic v1 in v1, pydantic v2 in v2), flag it; do not auto-resolve. Pydantic v2 is mandatory for v2 — if v1 uses pydantic v1, this needs an upgrade conversation before proceeding.
- mypy and pytest are scoped to clubos2/ and tests_v2/ only. They do not run against v1 code.

Acceptance criteria:
1. `pip install -e ".[v2-runtime,v2-dev]"` from repo root completes without errors
2. Existing `pip install -r REQUIREMENTS/base.txt` still works for v1-only setup
3. `python -c "import langchain, langgraph, langsmith, chromadb, anthropic; print('ok')"` prints `ok`
4. `make v2-lint` runs (may report nothing yet, that's fine)
5. `make v2-typecheck` runs against the empty clubos2/ tree
6. `cd BACKEND/api && pytest tests/` still passes 36 tests
7. `cd BACKEND/api && uvicorn app.main:app --reload` still starts v1 backend cleanly

Verify before next prompt:
- Check pydantic version: `python -c "import pydantic; print(pydantic.__version__)"` — must be 2.x
- If v1 currently uses pydantic v1, STOP and flag this. Do not silently upgrade v1's pydantic — that breaks the no-touch-v1 rule.
- Confirm both `pip list | grep langchain` and `pip list | grep langgraph` show installed versions.
```

---

# Stage 3 — Skill files + RAG

## Prompt 3.4 — Wire `search_knowledge` and `query_metrics` to real sources (REVISED)

```
Replace the stub `search_knowledge` tool in `clubos2/tools/registry.py` with the real implementation that calls the retriever. Also implement the real `query_metrics` tool that reads from the EXISTING v1 Gold CSV snapshots in `DATA/gold_snapshots/`.

Why CSVs not a new DuckDB: v1 already uses `DATA/gold_snapshots/*.csv` as the dev-mode Gold layer. v1's BACKEND/api/app/clients/databricks.py has the "CSV fallback in dev" pattern. Reusing the same CSVs means no duplicate data layer, no seeding script, no drift between v1 and v2's view of the world.

Modifications to clubos2/tools/registry.py:

1. `search_knowledge(query, k=5)` — replace stub:
   - Build a RetrievalConfig(k_final=k)
   - Call clubos2.rag.retriever.retrieve(query, config)
   - Return list of KnowledgeChunk

2. `query_metrics(metric_name, month=None)` — replace stub:
   - First, look up the metric in the semantic_layer to validate it exists
     - If not found, raise MetricNotFoundError with similar-name suggestions via lookup_metrics_by_terms()
   - Then read from DATA/gold_snapshots/ — specifically gold_priority_board.csv and gold_kpi_health.csv as the primary metric-value sources (review the actual CSVs first; pick the table(s) that contain the requested metric_name)
   - Return list of MetricRow with source field set to the EXACT CSV filename (e.g. "DATA/gold_snapshots/gold_priority_board.csv")

3. `get_signal(signal_id)` — keep as stub for Phase 1. Phase 3 implements it.
4. `get_benchmark(metric_name, peers)` — keep as stub for Phase 1.

Create clubos2/tools/gold_client.py:

```python
import pandas as pd
from pathlib import Path
from pydantic_settings import BaseSettings

class GoldClientSettings(BaseSettings):
    gold_snapshots_dir: str = "./DATA/gold_snapshots"  # default reads v1's CSVs

class GoldClient:
    """
    Reads metric values from v1's existing gold_snapshots CSVs.
    Phase 1: dev-only, reads CSVs directly.
    Future (Phase 2+): swap to v1's BACKEND/api/app/clients/databricks.py
    abstraction so we share the same code path that v1 uses to read Databricks.
    """
    
    def __init__(self, settings: GoldClientSettings | None = None):
        self.settings = settings or GoldClientSettings()
        self.gold_dir = Path(self.settings.gold_snapshots_dir)
        if not self.gold_dir.exists():
            raise FileNotFoundError(
                f"Gold snapshots dir not found at {self.gold_dir}. "
                f"Run from repo root or set GOLD_SNAPSHOTS_DIR env var."
            )
    
    async def fetch_metric(
        self,
        metric_name: str,
        month: str | None = None,
    ) -> list[dict]:
        """
        Find the metric across known gold_*.csv files.
        Phase 1 strategy: try gold_priority_board.csv first (it has the 59 main metrics),
        then gold_kpi_health.csv. If found in neither, raise MetricNotInGoldError.
        Return raw rows with the source filename attached.
        """
        # Read the CSV with pandas, filter to rows matching metric_name and optionally month
        # Return as list of dicts with explicit 'source' field set to the CSV path
        ...
    
    def list_available_metrics(self) -> dict[str, str]:
        """Return {metric_name: source_csv} for every metric found across gold_*.csv. 
        Used by MetricNotFoundError for 'did you mean' suggestions."""
        ...
```

Update MetricNotFoundError to include both semantic-layer suggestions (from lookup_metrics_by_terms) AND existence-in-Gold suggestions (from GoldClient.list_available_metrics):

```python
class MetricNotFoundError(Exception):
    def __init__(self, metric_name: str, suggestions_from_registry: list[str], suggestions_from_gold: list[str]):
        self.metric_name = metric_name
        self.suggestions_from_registry = suggestions_from_registry
        self.suggestions_from_gold = suggestions_from_gold
        super().__init__(
            f"Metric '{metric_name}' not in semantic_layer registry. "
            f"Did you mean: {', '.join(suggestions_from_registry[:3]) or '(no close matches)'}? "
            f"Or in Gold but unregistered: {', '.join(suggestions_from_gold[:3]) or '(none)'}"
        )
```

This split is intentional and a senior point worth flagging: a metric can exist in the registry but be missing from Gold (data gap), or exist in Gold but not in the registry (governance gap — needs human definition). The error message surfaces both, helping the developer see which is wrong.

Tests in tests_v2/test_tools_query_metrics.py:
- query_metrics("streaming_daily_users") returns at least one MetricRow with source ending in ".csv"
- query_metrics("nonexistent_metric") raises MetricNotFoundError; the message includes the closest match from the registry
- A metric that is in the registry but missing from Gold raises MetricNotFoundError with suggestions_from_gold = []
- The returned MetricRow's source field is the actual CSV filename (e.g. "DATA/gold_snapshots/gold_priority_board.csv"), not a placeholder

Tests in tests_v2/test_tools_search_knowledge.py:
- search_knowledge("seasonal Z-score") returns chunks all with populated source fields
- search_knowledge with k=3 returns at most 3 chunks
- Empty corpus case returns []

Critical constraints:
- This prompt does NOT modify v1's BACKEND/api/app/clients/databricks.py. v2 creates its own GoldClient that happens to read the same CSVs.
- Future migration path: when Phase 2 or 3 needs live Databricks data, GoldClient is the swap point — implement a DatabricksGoldClient subclass that reads from the SQL Warehouse and matches the same fetch_metric signature.
- All tools are async (FastAPI compatibility)
- All tools wrapped with @traced(name="tool:X", run_type="tool")
- The grounding rule: every returned MetricRow and KnowledgeChunk has its source field populated. Test this explicitly.

Acceptance criteria:
1. `await query_metrics("streaming_daily_users")` returns real data from DATA/gold_snapshots/*.csv
2. `await query_metrics("conversion_rate")` raises MetricNotFoundError suggesting conversion_rate_ecommerce / conversion_rate_streaming from the registry
3. `await search_knowledge("seasonal patterns")` returns chunks all with populated source fields
4. The returned MetricRow.source is the actual CSV file path
5. Tests pass
6. v1 backend (BACKEND/api/) still starts and runs all 36 tests

Verify before next prompt: REPL session combining both:
```python
import asyncio
from clubos2.tools import query_metrics, search_knowledge
metric = asyncio.run(query_metrics("streaming_daily_users"))
print(f"Metric source: {metric[0].source}")  # should print DATA/gold_snapshots/gold_X.csv
context = asyncio.run(search_knowledge("January seasonal patterns"))
print(f"Context chunks: {len(context)}")
for c in context[:2]:
    print(f"  {c.source}::{c.section}")
```
Both should return data, sources should be real file paths (not placeholders), and the context chunks should be relevant to the January question.
```

---

# Stage 4 — Scout agent

## Prompt 4.3 — Add `POST /api/ai/query` to the existing v1 backend (REVISED)

```
Expose the Scout agent via a FastAPI endpoint by ADDING ONE NEW ROUTER FILE to the existing v1 backend. No restructure of v1 — we add a single file alongside the existing routers.

File to CREATE: BACKEND/api/app/routers/ai_query.py
File to MODIFY (one line addition): BACKEND/api/app/main.py — include the new router

This is the ONLY place where Phase 1 touches v1's directory tree. The discipline: one file added, one file modified to register the route, no other v1 code changed.

In BACKEND/api/app/routers/ai_query.py:

```python
from __future__ import annotations
import logging
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# These are the v2 imports — proves the v1 backend can reach v2 code cleanly
from clubos2.agents.scout import run_scout
from clubos2.agents.scout_schemas import ScoutInput, ScoutAnswer
from clubos2.observability.tracing import get_current_langsmith_trace_url

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["ai"])


class AIQueryRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)
    session_id: str | None = None
    user_id: str | None = None


class AIQueryResponse(BaseModel):
    answer: str
    citations: list[dict]
    confidence: str
    assumptions_made: list[str]
    metrics_queried: list[str]
    chunks_retrieved: int
    trace_url: str | None
    latency_ms: int


@router.post("/query", response_model=AIQueryResponse)
async def query_scout(request: AIQueryRequest) -> AIQueryResponse:
    """
    ClubOS 2.0 Scout — grounded natural-language Q&A over club metrics and knowledge.
    Phase 1 endpoint. Auth and rate-limiting are deferred to Phase 6.
    """
    start = time.perf_counter()
    try:
        scout_input = ScoutInput(**request.model_dump())
        answer: ScoutAnswer = await run_scout(scout_input)
        latency_ms = int((time.perf_counter() - start) * 1000)
        return AIQueryResponse(
            answer=answer.answer,
            citations=[c.model_dump() for c in answer.citations],
            confidence=answer.confidence.value,
            assumptions_made=answer.assumptions_made,
            metrics_queried=answer.metrics_queried,
            chunks_retrieved=answer.chunks_retrieved,
            trace_url=get_current_langsmith_trace_url(),
            latency_ms=latency_ms,
        )
    except Exception:
        # Log full detail server-side; return generic error to client
        logger.exception("Scout query failed", extra={"question_preview": request.question[:80]})
        raise HTTPException(status_code=500, detail="Internal error processing AI query")
```

Modification to BACKEND/api/app/main.py:
Locate the section where existing routers are included (look for `app.include_router(...)` calls — there should be many for priorities, signals, health, benchmark, briefing, events, social, etc.).

Add EXACTLY one new line in that section:
```python
from app.routers import ai_query
app.include_router(ai_query.router)
```

Place the import at the top of main.py near the other router imports, and the include_router call near the others. Touch nothing else.

CORS: confirm the existing CORS config in main.py allows the frontend origin. The new /api/ai/query endpoint will be subject to the same CORS policy — no change needed.

Integration test: CREATE tests_v2/test_api_ai_query.py (NOT inside BACKEND/api/tests/ — those are v1's; v2 tests live in tests_v2/).

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

# Import the existing v1 app — this proves the v2 router is registered into it
import sys
sys.path.insert(0, "BACKEND/api")  # so `from app.main import app` works
from app.main import app

client = TestClient(app)


def test_query_endpoint_registered():
    """/api/ai/query exists in OpenAPI schema."""
    schema = client.get("/openapi.json").json()
    assert "/api/ai/query" in schema["paths"]


def test_query_validates_input():
    """Empty question → 422."""
    response = client.post("/api/ai/query", json={"question": ""})
    assert response.status_code == 422


def test_query_too_long():
    """Question > 500 chars → 422."""
    response = client.post("/api/ai/query", json={"question": "x" * 501})
    assert response.status_code == 422


@patch("clubos2.agents.scout.run_scout", new_callable=AsyncMock)
def test_query_happy_path(mock_run_scout):
    """Valid question → 200 with ScoutAnswer shape."""
    from clubos2.agents.scout_schemas import ScoutAnswer, Confidence
    mock_run_scout.return_value = ScoutAnswer(
        answer="Test answer",
        citations=[],
        confidence=Confidence.HIGH,
        assumptions_made=[],
        metrics_queried=["streaming_daily_users"],
        chunks_retrieved=3,
    )
    response = client.post(
        "/api/ai/query",
        json={"question": "what is streaming daily users this month?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert "trace_url" in body
    assert "latency_ms" in body
    assert body["confidence"] == "high"
```

Manual smoke test (document in clubos2/README.md):
```bash
# Terminal 1: start v1 backend with v2 routes
cd BACKEND/api && uvicorn app.main:app --reload --port 8000

# Terminal 2: query
curl -X POST http://localhost:8000/api/ai/query \
  -H "Content-Type: application/json" \
  -d '{"question": "what does the seasonal Z-score correct for?"}'
```
Expect 200 with citations referencing priority_board.md and a trace_url.

Critical constraints:
- ONLY add the import + include_router line to BACKEND/api/app/main.py. Do not touch any other v1 file.
- The router file lives in BACKEND/api/app/routers/ai_query.py — adopting v1's existing convention.
- The new router imports from clubos2.* — this is the bridge between v1 (FastAPI app) and v2 (agent code).
- For the v1 backend to import clubos2.*, the repo root must be on the Python path when uvicorn runs. Verify this works: `cd BACKEND/api && python -c "import clubos2; print(clubos2.__file__)"` — if this fails, the v2 package is not installed in v1's venv. Fix by running `pip install -e ".[v2-runtime]"` from repo root, in v1's venv.
- Auth and rate limiting are OUT of scope for Phase 1. Add a comment in the router file: `# TODO Phase 6: add auth and rate limiting before exposing publicly`.
- The endpoint does NOT add business logic. It is a thin HTTP wrapper around run_scout.

Acceptance criteria:
1. `cd BACKEND/api && uvicorn app.main:app --reload` still starts cleanly after the modification.
2. All 36 v1 tests in BACKEND/api/tests/ still pass.
3. `curl POST http://localhost:8000/api/ai/query` with a valid question returns 200 with the expected response shape.
4. The trace_url in the response opens a real LangSmith trace.
5. http://localhost:8000/docs shows the new /api/ai/query endpoint alongside the existing v1 endpoints (priorities, signals, etc.).
6. `pytest tests_v2/test_api_ai_query.py` passes.

Verify before next prompt:
- Hit the existing v1 endpoint /priorities — must still return data (regression check).
- Hit /api/ai/query with the curl command above — must return 200 with a valid trace URL.
- Open the trace URL in LangSmith and walk through the spans: scout:run → tool calls → llm call → answer.
- If anything breaks v1, revert the main.py change and investigate before proceeding to Stage 5.
```

---

# Stage 5 — Verification and handoff

## Prompt 5.1 — Phase 1 verification and completion report (REVISED)

```
Build the verification scaffolding that proves Phase 1 is complete and document the state of the system for Phase 2 entry. The completion report's checklist is updated to reflect the additive approach (no monorepo restructure happened — that's now a Phase 6+ decision).

Files to create:
- tests_v2/test_phase1_e2e.py — end-to-end integration tests
- DOCS/phase1_completion.md — human-readable state report (placed in v1's DOCS/ folder so it lives alongside v1 documentation)

In tests_v2/test_phase1_e2e.py:

```python
import os
import re
import pytest
import pytest_asyncio

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_E2E") != "1",
    reason="E2E tests require RUN_E2E=1 and real API keys",
)


@pytest.mark.asyncio
async def test_scout_answers_seasonal_question():
    """Real LLM + real ChromaDB + real semantic layer + real Gold CSVs."""
    from clubos2.agents.scout import run_scout
    from clubos2.agents.scout_schemas import ScoutInput

    answer = await run_scout(ScoutInput(
        question="What does the seasonal Z-score correct for, and which metric is most affected?"
    ))

    assert answer.answer is not None
    assert len(answer.answer) > 50

    sources = {c.source for c in answer.citations}
    assert any("priority_board" in s or "signal_engine" in s for s in sources), \
        f"Expected skill-file citation, got {sources}"

    assert "net_sales" in answer.answer.lower() or "january" in answer.answer.lower()
    assert answer.confidence in ("high", "medium")


@pytest.mark.asyncio
async def test_scout_refuses_unanswerable_question():
    """No fabrication discipline check."""
    from clubos2.agents.scout import run_scout
    from clubos2.agents.scout_schemas import ScoutInput

    answer = await run_scout(ScoutInput(
        question="Who is the highest-paid player on Real Madrid this season?"
    ))

    assert answer.confidence == "low"
    # No specific monetary numbers fabricated
    assert not re.search(r"€\d|\$\d|\d+\s*million", answer.answer)


@pytest.mark.asyncio
async def test_scout_handles_ambiguity():
    """Disambiguation rule fires."""
    from clubos2.agents.scout import run_scout
    from clubos2.agents.scout_schemas import ScoutInput

    answer = await run_scout(ScoutInput(
        question="how is conversion rate doing this month?"
    ))

    assert len(answer.assumptions_made) > 0
    assumption_text = " ".join(answer.assumptions_made).lower()
    assert "ecommerce" in assumption_text or "streaming" in assumption_text


@pytest.mark.asyncio
async def test_v1_endpoints_still_work():
    """Regression: v1 endpoints still function after v2 addition."""
    from fastapi.testclient import TestClient
    import sys
    sys.path.insert(0, "BACKEND/api")
    from app.main import app
    client = TestClient(app)

    # Hit a known v1 endpoint
    response = client.get("/priorities")
    assert response.status_code == 200
```

In DOCS/phase1_completion.md, write a human-readable summary. Required sections:

```markdown
# ClubOS 2.0 — Phase 1 Completion Report

## Approach taken
ClubOS 2.0 Phase 1 was built ADDITIVELY on top of the live v1 repository. No v1 directories were restructured. New v2 code lives in `clubos2/` at the repo root. The only v1 file modified in Phase 1 is `BACKEND/api/app/main.py` (one new router registration). All 36 v1 tests still pass; GCP Cloud Run deployment is unchanged.

## What is built
- [ ] Additive directory extension complete (`clubos2/`, `prompts/`, `eval/`, `tests_v2/`)
- [ ] v2 dependencies installable via `pip install -e ".[v2-runtime,v2-dev]"`
- [ ] LLM gateway with structured output and cost logging
- [ ] LangSmith tracing wired (chain / tool / llm / retriever run types)
- [ ] Semantic layer: metric_registry table with 10 fully-curated rows + 49 stub rows
- [ ] Skill files: priority_board.md and signal_engine.md fully authored
- [ ] RAG ingestion: skill files chunked, embedded, stored in ChromaDB
- [ ] Hybrid retrieval (vector + BM25) with cross-encoder reranking
- [ ] query_metrics reads from existing DATA/gold_snapshots/*.csv (no duplicate Gold layer)
- [ ] search_knowledge wired to real ChromaDB-backed retriever
- [ ] Scout agent assembling grounded answers with citations
- [ ] POST /api/ai/query endpoint added to existing v1 FastAPI app

## Verified numbers (do not change)
- 59 metrics in registry (10 fully curated, 49 stub awaiting human review)
- 6 skill files (2 fully authored, 4 with structural skeleton)
- 36 v1 tests still passing (regression confirmed)
- N new v2 tests in tests_v2/ (record actual count after running)

## What was deliberately NOT done (and why)
- No monorepo restructure: deferred to Phase 6+ when the Slack app is built. The cost of restructuring a live production system in Phase 1 outweighs the benefit.
- No new Gold layer: v2 reuses v1's DATA/gold_snapshots/*.csv. Single source of truth.
- No auth/rate-limiting on /api/ai/query: Phase 6 work. Add a TODO in the router file.

## Known gaps deferred to Phase 2
- query_metrics reads CSVs only; live Databricks SQL Warehouse swap is a Phase 2 task using v1's existing databricks.py client
- get_signal and get_benchmark are still stubs
- No guardrail enforcement yet (the LLM is asked to obey citation rules but no post-processing check exists)
- No evals harness — questions are spot-tested manually
- No conversation memory — each question is independent
- No frontend integration — /api/ai/query is callable only via curl/Postman

## Latency baseline (measure and record after running 10 sample questions)
- p50 latency: ___ ms
- p95 latency: ___ ms
- Average cost per question: $___

## How to demo
Three commands that prove Phase 1 works:
1. `cd BACKEND/api && uvicorn app.main:app --reload --port 8000` to start the existing v1 server (now extended with v2 route)
2. `curl -X POST http://localhost:8000/api/ai/query -H "Content-Type: application/json" -d '{"question":"what does the seasonal Z-score correct for?"}'` — expect a grounded answer with citations and a trace_url
3. Open the trace_url in LangSmith and walk through the spans

## Phase 2 entry checklist
Phase 2 is unblocked when:
- [ ] All Phase 1 acceptance criteria above pass
- [ ] At least 5 questions have been asked end-to-end via curl and the answers reviewed for fabrication
- [ ] The fabricated-number rate on a small ad-hoc test set is at or near zero
- [ ] You can answer the interview question "walk me through what happens when a user hits POST /api/ai/query" without looking at code
- [ ] v1 deployment to GCP Cloud Run still works (run a manual deploy and confirm v1 endpoints respond)

## Architectural note for interviews
The Phase 1 design uses a single-LLM-call compound system (deterministic semantic layer check → parallel tool calls → one LLM call with grounded context), NOT a multi-agent LangGraph orchestration. This is intentional: the senior pattern is to use the simplest architecture that meets the requirement, not to over-agentify. LangGraph multi-agent orchestration enters in Phase 4 when the Watchdog, Investigator, and Briefer agents need to coordinate.
```

Run the verification:
```bash
RUN_E2E=1 pytest tests_v2/test_phase1_e2e.py -v
```

Critical constraints:
- E2E tests are gated by RUN_E2E=1 so they don't consume real API budget in normal CI
- The completion doc is honest — every checkbox accurately reflects what is and isn't done
- Latency and cost numbers are MEASURED, not estimated — run the 10 questions and record real values
- The "What was deliberately NOT done" section is critical for the interview narrative — being able to explain why you didn't restructure the monorepo, why you reused v1's CSVs, why you used a compound system instead of LangGraph for one LLM call — these are the senior-engineer answers that distinguish you from someone who built the same thing by following tutorials.

Acceptance criteria:
1. E2E tests pass when run with RUN_E2E=1 and valid API keys
2. DOCS/phase1_completion.md exists and every checkbox is honestly marked
3. The 3 demo questions all return valid responses with valid trace URLs
4. The Phase 2 entry checklist has all boxes ticked
5. GCP Cloud Run deployment of v1 still works (manual verification)

Verify Phase 1 is complete: walk through the demo. If any of the 3 demo questions returns something embarrassing (fabricated number, irrelevant citation, refusal on an answerable question), DO NOT move to Phase 2 — fix the underlying issue first. This report is what you will reference in interviews; it must be accurate.
```

---

# Summary of what changed vs. original prompts

| Prompt | Status | Change |
|---|---|---|
| 0.1 | **Rewritten** | No restructure. New folders only: `clubos2/`, `prompts/`, `eval/`, `var/`, `tests_v2/`. v1 untouched. |
| 1.1 | **Revised** | Dependency groups renamed `v2-runtime`/`v2-dev`/`v2-eval`. Makefile targets prefixed `v2-`. Pydantic version check added. |
| 1.2 | Unchanged | Lives in `clubos2/gateway/` — works identically. |
| 1.3 | Unchanged | Lives in `clubos2/observability/` + `clubos2/tools/` — works identically. |
| 2.1 | Unchanged | `clubos2/semantic_layer/` — works identically. |
| 2.2 | Unchanged | Same seed script. |
| 2.3 | Unchanged | Same lookup API. |
| 3.1 | Unchanged | Skill files in `clubos2/rag/skills/`. |
| 3.2 | Unchanged | Same ingestion pipeline. |
| 3.3 | Unchanged | Same retriever. |
| 3.4 | **Revised** | `query_metrics` reads from existing `DATA/gold_snapshots/*.csv` instead of a new DuckDB seed. `GoldClient` swap point for future Databricks. |
| 4.1 | Unchanged | Scout schemas in `clubos2/agents/`. |
| 4.2 | Unchanged | Scout orchestration. |
| 4.3 | **Rewritten** | Router added to `BACKEND/api/app/routers/ai_query.py`. Only `main.py` modified (one line). v1 conventions respected. |
| 5.1 | **Revised** | Completion report reflects additive approach. Includes regression check that v1 endpoints + 36 tests still pass. |

For interviews, the senior-engineer story is now:
> "I built ClubOS 2.0 as an additive extension to the live v1 system. No restructure, no breaking changes — the existing 36 tests and GCP Cloud Run deployment kept working throughout. The new agentic layer lives in a separate `clubos2/` package, and the v1 FastAPI app just adds one new router that imports from it. When the Slack app and Databricks deployment come later, then we revisit structure with concrete requirements — not premature abstraction."