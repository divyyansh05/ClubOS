# ClubOS Repository Structure

## Purpose

This document defines the repository layout for ClubOS so the project can be developed systematically by AI agents and human contributors.

The structure separates:

- product app code
- backend APIs
- Databricks pipeline assets
- contracts and documentation
- tests
- demo artifacts

## Canonical Structure

```text
.
├── .github/
├── CLAUDE.md
├── AGENTS.md
├── README.md
├── REPO_STRUCTURE.md
├── agents/
│   ├── 01_delivery_orchestrator.md
│   ├── 02_data_platform_engineer.md
│   ├── 03_analytics_engineer.md
│   ├── 04_backend_api_engineer.md
│   ├── 05_frontend_product_engineer.md
│   ├── 06_ai_insights_engineer.md
│   └── 07_qa_release_manager.md
├── apps/
│   ├── clubos-web/
│   │   ├── src/
│   │   │   ├── app/
│   │   │   ├── components/
│   │   │   ├── features/
│   │   │   ├── lib/
│   │   │   ├── styles/
│   │   │   └── types/
│   │   └── public/
│   └── tableau/
├── backend/
│   └── api/
│       ├── app/
│       │   ├── routers/
│       │   ├── schemas/
│       │   ├── services/
│       │   ├── clients/
│       │   └── config/
│       └── tests/
├── data/
│   └── source/
├── databricks/
│   ├── notebooks/
│   │   ├── bronze/
│   │   ├── silver/
│   │   ├── gold/
│   │   ├── analytics/
│   │   └── quality/
│   ├── sql/
│   ├── jobs/
│   └── seeds/
├── data_contracts/
├── docs/
│   ├── product/
│   ├── architecture/
│   ├── delivery/
│   ├── demos/
│   └── research/
├── tests/
│   ├── data/
│   ├── api/
│   └── ui/
└── artifacts/
    └── demo/
```

## Folder Responsibilities

### `agents/`

Contains the role definitions and operating instructions for AI agents.

### `apps/clubos-web/`

Contains the primary SaaS product frontend.

Recommended responsibility:

- app shell
- pages
- feature modules
- shared components
- styling
- client-side state

### `apps/tableau/`

Contains Tableau-related materials, connection instructions, extracts, or support assets.

This is a secondary delivery layer, not the hero product.

### `backend/api/`

Contains the backend service that exposes Gold outputs to the frontend.

Recommended responsibility:

- API routers
- response schemas
- business-facing service logic
- Databricks or warehouse clients
- configuration

### `databricks/notebooks/`

Contains Databricks-side notebooks grouped by medallion stage and analysis function.

Subfolders:

- `bronze/` for ingestion notebooks
- `silver/` for cleaning and normalization notebooks
- `gold/` for app-ready output generation
- `analytics/` for signal logic, scoring, and benchmark calculations
- `quality/` for checks and validation runs

### `databricks/sql/`

Contains SQL scripts for warehouse objects, views, and lightweight transformations where SQL is preferable.

### `databricks/jobs/`

Contains job definitions, run order notes, or deployment metadata for scheduled or manual execution.

### `databricks/seeds/`

Contains seed datasets such as curated event annotations or sample input files.

### `data_contracts/`

Contains schema contracts and refresh assumptions.

Recommended files:

- `internal_metrics_contract.md`
- `benchmark_contract.md`
- `event_annotations_contract.md`
- `refresh_runbook.md`

### `docs/product/`

Contains product-facing reference material.

Recommended content:

- feature notes
- module specs
- priority logic explanation

### `docs/architecture/`

Contains architecture documents and technical diagrams.

Recommended content:

- system diagrams
- API contracts
- table relationship docs

### `docs/delivery/`

Contains execution plans, sprint notes, risks, and handoff logs.

### `docs/demos/`

Contains demo scripts, live walkthrough notes, and final presentation support material.

### `tests/data/`

Contains tests for schema validation, metric sanity, and refresh behavior.

### `tests/api/`

Contains backend API tests.

### `tests/ui/`

Contains UI regression or interaction tests.

### `artifacts/demo/`

Contains screenshots, exports, and demo-specific generated assets.

### `docs/research/`

Contains imported brainstorm, challenge, and research material used to define the product direction.

### `data/source/`

Contains raw source datasets and original project pack files provided for the internship brief.

## Ownership Summary

- `agents/` -> delivery orchestrator
- `databricks/` -> data platform engineer
- `data_contracts/` -> data platform engineer with analytics engineer
- `backend/` -> backend API engineer
- `apps/clubos-web/` -> frontend product engineer
- `docs/product/` -> product/frontend shared
- `docs/architecture/` -> data platform and backend shared
- `tests/` -> QA release manager with contributing engineers

## File Placement Rules

- Raw-source-specific logic belongs in `databricks/notebooks/bronze/` or `silver/`
- reusable scoring logic belongs in `databricks/notebooks/analytics/`
- app-ready table creation belongs in `databricks/notebooks/gold/`
- frontend should not contain analytics logic that belongs in Databricks
- backend should not recalculate data science logic that should already exist in Gold
- docs should reflect implementation reality, not intended future state only

## Build Order Mapping

Recommended build path by folder:

1. `data_contracts/`
2. `databricks/notebooks/bronze/`
3. `databricks/notebooks/silver/`
4. `databricks/notebooks/gold/`
5. `databricks/notebooks/analytics/`
6. `backend/api/`
7. `apps/clubos-web/`
8. `tests/`
9. `apps/tableau/`
10. `docs/demos/`

## Final Structure Principle

The repository should make one thing obvious:

**data enters once, gets standardized once, and then powers the same recurring product workflow every month.**
