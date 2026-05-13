# Session 02 Prompt - Backend Core Contracts

## Copy-Paste Prompt

```text
Read these files first:

- AGENTS.md
- REPO_STRUCTURE.md
- docs/product/clubos_mvp_spec.md
- docs/product/clubos_screen_blueprint.md
- docs/architecture/api_contract.md
- docs/architecture/gold_table_contracts.md
- docs/delivery/project_execution_memory.md
- agents/04_backend_api_engineer.md
- agents/07_qa_release_manager.md

Also inspect these implementation files:

- backend/api/app/main.py
- backend/api/app/routers/priorities.py
- backend/api/app/routers/health.py
- backend/api/app/routers/benchmark.py
- backend/api/app/routers/signals.py
- backend/api/app/routers/briefing.py
- backend/api/app/services/priority_service.py
- backend/api/app/services/benchmark_service.py
- backend/api/app/services/signal_service.py
- backend/api/app/services/briefing_service.py
- backend/api/app/clients/databricks.py
- backend/api/app/schemas/priorities.py
- backend/api/app/schemas/benchmark.py
- backend/api/app/schemas/signals.py
- backend/api/app/schemas/briefing.py

Act jointly as:

- Backend API Engineer
- QA Release Manager

Current audit context:

- Gold logic should be substantially trustworthy after Session 01
- backend is still placeholder-only
- next goal is not “smart backend”; it is a thin, typed, Gold-backed product layer

Your task:
Replace backend placeholders with real typed read-only contracts over the Gold layer.

What to build:

1. Real client/service flow for Gold-backed reads
2. Typed response schemas for:
   - latest priorities
   - priority detail
   - latest health
   - benchmark view
   - latest signals
   - latest briefing
3. Real routers returning shaped responses instead of placeholder strings
4. API contract documentation updates

Files you may edit:

- backend/api/app/main.py
- backend/api/app/clients/databricks.py
- backend/api/app/routers/priorities.py
- backend/api/app/routers/health.py
- backend/api/app/routers/benchmark.py
- backend/api/app/routers/signals.py
- backend/api/app/routers/briefing.py
- backend/api/app/services/*.py
- backend/api/app/schemas/*.py
- docs/architecture/api_contract.md
- docs/delivery/project_execution_memory.md
- relevant agent role files only if workflow expectations change materially

Constraints:

- do not duplicate business logic already present in Gold
- keep the backend read-only and thin
- do not touch frontend in this session
- do not add AI logic in the backend

Required session output:

1. list all files changed
2. list the real endpoints now implemented
3. explain the service boundary between Gold tables and API
4. note any blockers around Databricks connectivity assumptions
5. update `docs/delivery/project_execution_memory.md`
6. finish with:
   - Passed
   - Failed
   - Fix Before Next Prompt
   - confidence score after this session
   - whether Session 03 is safe to run
```
