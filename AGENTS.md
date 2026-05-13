# ClubOS AI Development Constraints

## Mission

Build **ClubOS** as a recurring monthly digital business operating system for elite football clubs.

This repository is not for a one-off dashboard. It is for a reusable SaaS-style product that ingests recurring monthly files, recalculates benchmark and signal logic, and updates the same business workflow every month.

## Source Of Truth

All agents must read these documents before planning or implementing work:

1. `docs/product/clubos_product_definition_report.md`
2. `docs/product/clubos_mvp_spec.md`
3. `docs/product/clubos_screen_blueprint.md`
4. `docs/architecture/clubos_databricks_schema_plan.md`
5. `docs/research/real_madrid_project_brief.md`

If these documents conflict:

- the narrower document overrides the broader document
- implementation constraints override conceptual ambition
- the real data shape overrides earlier brainstorm assumptions

## Non-Negotiables

- Build for **recurring monthly data refresh**, not one-off analysis.
- The data is **monthly**, so the product must not claim day-level timing or precision.
- Python runtime standard is **3.11.x** across the project. Do not introduce 3.9-only or 3.10+only assumptions without explicit compatibility checks.
- The **Priority Board** is the hero feature.
- Benchmark only the metrics actually supported by the benchmark file.
- AI is supportive for summaries and explanations. AI is not the source of core scoring logic.
- Frontend reads from backend APIs or Gold tables only. No UI should depend on raw or Silver data.
- Build proof before polish.
- Do not overclaim novelty with statements like "no club has ever done this" unless the claim is narrow and defensible.
- Do not hardcode findings into the product as if they were computed logic.

## Product Truths

ClubOS must behave like:

- a monthly operating system
- a decision-support product
- a reusable internal SaaS tool

It must not behave like:

- a static pitch deck in app form
- a generic dashboard with better colors
- a fake AI product that invents insights without evidence

## Build Sequence

Agents must follow this order unless the orchestrator explicitly changes it:

1. data contract and metric inventory
2. Bronze ingestion
3. Silver normalization and validation
4. Gold benchmark and KPI health outputs
5. signal validation
6. priority scoring logic
7. backend API
8. frontend product shell
9. AI summaries
10. Tableau support layer

## Repo Structure

The canonical repo structure is documented in:

- `REPO_STRUCTURE.md`

Agents should place their work only in the folders they own or in agreed shared folders.

## Required Agents

The required agent role files live in:

- `agents/01_delivery_orchestrator.md`
- `agents/02_data_platform_engineer.md`
- `agents/03_analytics_engineer.md`
- `agents/04_backend_api_engineer.md`
- `agents/05_frontend_product_engineer.md`
- `agents/06_ai_insights_engineer.md`
- `agents/07_qa_release_manager.md`

Optional later:

- Tableau specialist
- demo/presentation specialist

## Ownership Boundaries

### Delivery Orchestrator

- owns sequencing, milestones, handoffs, risk control, and scope decisions

### Data Platform Engineer

- owns ingestion, validation, medallion architecture, and table generation

### Analytics Engineer

- owns KPI logic, benchmark logic, signal testing, event logic, and priority scoring

### Backend API Engineer

- owns app-facing services, response schemas, and API contracts over Gold tables

### Frontend Product Engineer

- owns app structure, feature implementation, UI state, and screen behavior

### AI Insights Engineer

- owns briefing templates, explanation generation, and guarded AI augmentation

### QA Release Manager

- owns data validation checks, testing strategy, regression checks, demo readiness, and acceptance verification

## Shared Engineering Rules

- Prefer deterministic logic over cleverness.
- Keep all scoring logic inspectable.
- Store intermediate calculations for trust and debugging.
- Use stable schema names and canonical metric names.
- Use typed contracts between layers whenever possible.
- Every recommendation in the UI must be traceable to stored evidence.
- When a metric or relationship is weak, hide it rather than forcing it into the product.

## Data Rules

- Treat each monthly upload as a new version of the same recurring feed.
- Preserve raw uploads in Bronze.
- Normalize names and fix source inconsistencies in Silver.
- Publish only app-safe outputs in Gold.
- Maintain refresh metadata and lineage.
- Validate required columns, date coverage, duplicates, and rate ranges on every run.

## Frontend Rules

- The app must open on Priority Board.
- The workflow must feel operational, not exploratory.
- Every major visual must answer a clear business question.
- Every score must have a breakdown.
- Avoid decorative dashboards with weak business meaning.

## AI Rules

- AI can summarize, explain, and draft briefings.
- AI cannot be the source of truth for scoring, ranking, or analytics validity.
- AI outputs must be grounded in structured data inputs.
- If the AI layer fails, the product must still function.

## Handoff Protocol

When one agent finishes work, the handoff must include:

- what was changed
- which files were touched
- what assumptions were made
- what is ready for the next agent
- what remains risky or unresolved

No agent should leave hidden assumptions.

## Execution Memory

All substantial build sessions must update:

- `docs/delivery/project_execution_memory.md`

This file is the shared execution memory for the project.

Agents should update it with:

- current session goal
- what became real
- what remains placeholder-only
- blockers
- confidence after the session
- whether the next prompt in sequence is safe to run

Agents should update a role file under `agents/` only if the session materially changes role scope, workflow expectations, or dependencies.

## Definition Of Done

Work is done only when:

- it is aligned to the source-of-truth docs
- it fits the repo structure
- it respects ownership boundaries
- it includes basic validation
- it does not introduce unsupported product claims
- it helps the product behave the same way on the next monthly upload

## What To Avoid

- building too many views before the core logic exists
- adding unsupported benchmark comparisons
- using AI to cover up weak product logic
- building a scenario simulator as the hero with monthly data
- equating a nice UI with a buyable product

## Final Principle

The product should always answer this:

**New data in. Same workflow. Clear priorities out.**

### Files never to push for this project
- .env and all *.env files (credentials)
- data/source/ (raw client data)
- agents/ directory (internal AI agent config)
- docs/product/ (internal product specs)
- docs/research/ (internal research docs)
- docs/architecture/ (internal architecture docs)
- docs/delivery/ (internal execution memory)
- AGENTS.md itself
- ~/claude-skills/ (never in repo anyway)
