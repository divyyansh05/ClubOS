# ClubOS Mid-Phase Audit Prompt

Use this prompt after the following are implemented:

- strict metric allowlists in Silver
- metric polarity-aware KPI health logic
- signal validation pipeline
- priority board scoring pipeline

Use this audit before backend API and frontend product work expands beyond skeleton level.

## Copy-Paste Prompt

```text
Read these files first:

- AGENTS.md
- REPO_STRUCTURE.md
- docs/product/clubos_product_definition_report.md
- docs/product/clubos_mvp_spec.md
- docs/product/clubos_screen_blueprint.md
- docs/architecture/clubos_databricks_schema_plan.md
- docs/architecture/source_data_audit.md
- docs/architecture/bronze_silver_logic.md
- docs/architecture/gold_table_contracts.md
- docs/architecture/signal_validation_logic.md
- docs/architecture/priority_board_logic.md
- data_contracts/internal_metrics_contract.md
- data_contracts/benchmark_contract.md
- data_contracts/event_annotations_contract.md
- data_contracts/refresh_runbook.md
- data_contracts/metric_inventory.md
- docs/research/real_madrid_project_brief.md
- agents/01_delivery_orchestrator.md
- agents/02_data_platform_engineer.md
- agents/03_analytics_engineer.md
- agents/04_backend_api_engineer.md
- agents/05_frontend_product_engineer.md
- agents/07_qa_release_manager.md

Also inspect the current implementation in these folders:

- databricks/notebooks/bronze/
- databricks/notebooks/silver/
- databricks/notebooks/gold/
- databricks/notebooks/analytics/
- databricks/notebooks/quality/
- backend/api/
- apps/clubos-web/
- tests/data/
- tests/api/
- tests/ui/

Act as a combined reviewer using the mindset of:

- Delivery Orchestrator
- Data Platform Engineer
- Analytics Engineer
- Backend API Engineer
- Frontend Product Engineer
- QA Release Manager

Your task:
Audit the current state of ClubOS at the mid-phase checkpoint, after core data and scoring logic exist but before backend/frontend work expands materially.

What I need from you:
1. Tell me exactly what is now real versus still skeleton-only.
2. Tell me whether the project is genuinely ready for API and UI expansion.
3. Identify what is solid, what is weak, and what is still risky.
4. Challenge the implementation against the actual product docs and monthly data constraints.
5. Tell me what must be fixed before the UI and API are allowed to grow.

Audit this in 7 sections:

## 1. Mid-Phase Status
- What core systems now exist?
- Which parts are implemented versus placeholder-only?
- Is the repo materially progressing toward a SaaS product, or still mostly scaffolding?

## 2. Data Layer Readiness
- Are data contracts accurate and stable?
- Are Bronze and Silver reusable for future monthly uploads?
- Are metric allowlists and column controls strong enough?
- Are there any recurring refresh risks still unresolved?

## 3. Gold / Analytics Readiness
- Are `gold_kpi_health`, `gold_peer_benchmark`, `gold_signal_relationships`, and `gold_priority_board` implemented at a credible level?
- Are signal relationships selective, stable, and business-meaningful?
- Is priority scoring deterministic and inspectable?
- Are there any analytics shortcuts that would break trust in the product?

## 4. API Readiness
- Based on the current Gold outputs, is the backend ready to expose stable app-facing contracts?
- Are the API schemas and service boundaries clear enough?
- What backend work can safely begin now, and what should still wait?

## 5. Frontend Readiness
- Is the data model stable enough for the frontend team to build real screens?
- Which screens are safe to build now?
- Which screens should not be built yet because logic is still too weak or too unstable?
- Does the product now feel operational enough to support UI expansion?

## 6. Risks Before Expansion
- What are the top technical or product risks if the team starts building API/UI too early?
- What must be fixed first?
- What can safely wait until later?
- What should be cut or simplified if the project is still overreaching?

## 7. Final Verdict
Give a hard verdict in this exact format:

- Mid-phase confidence score: X/10
- Ready for API expansion: Yes / No
- Ready for frontend expansion: Yes / No
- If no: exact blocking items
- If yes: the next 5 build priorities in order

Important constraints:
- Do not flatter
- Do not assume work is good just because files exist
- Be strict about recurring monthly workflow
- Be strict about benchmark limitations
- Be strict about unsupported claims
- Be strict about anything still pretending to be product logic when it is really placeholder behavior
- Prefer harsh but useful truth over positivity

At the end, include:
- a short bullet list called `Passed`
- a short bullet list called `Failed`
- a short bullet list called `Fix Before API/UI Expansion`
```

## Purpose Of This Audit

This audit exists to answer one question:

**Do we now have enough real logic to let backend and frontend work expand, or are we still dressing up weak foundations?**

If the answer is no, fix the blocking logic first.
