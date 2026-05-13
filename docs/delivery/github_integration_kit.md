# GitHub Integration Kit for ClubOS

## Purpose

This document is the copy-paste-ready GitHub setup pack for the ClubOS project.

Use it when creating the GitHub repository, configuring project settings, and preparing the public or private repo structure in a professional way.

It includes:

- recommended repository name
- repository description
- GitHub topics
- copy-paste-ready `README.md`
- recommended repository settings
- recommended labels
- suggested issue and PR structure
- initial project board structure

---

## 1. Recommended Repository Name

Use one of these:

- `clubos`
- `clubos-realmadrid-digital-os`
- `clubos-digital-business-os`

Recommended:

**`clubos`**

If you want a more descriptive public name:

**`clubos-digital-business-os`**

---

## 2. Repository Description

Use this as the GitHub repository description:

**ClubOS is a monthly digital business operating system for elite football clubs, built on Databricks to unify KPI health, peer benchmarking, leading signals, and ranked business priorities.**

---

## 3. Suggested GitHub Topics

Use these GitHub topics:

- databricks
- delta-lake
- pyspark
- react
- fastapi
- analytics
- saas
- sports-analytics
- business-intelligence
- dashboard
- football
- ecommerce
- benchmarking
- ai
- data-engineering

---

## 4. Copy-Paste README.md

Copy the content below into the project `README.md`.

```md
# ClubOS

ClubOS is a monthly digital business operating system for elite football clubs.

It is designed to turn recurring monthly digital business datasets into a repeatable decision workflow for club business teams. Instead of just showing charts, ClubOS helps leadership understand what changed, where the club stands against peers, which internal signals matter commercially, and what deserves attention next.

## What ClubOS Does

ClubOS is built around five core capabilities:

- **Priority Board**: ranks the most important business issues and opportunities for the latest month
- **Command Center**: shows the health of the four digital businesses in one place
- **Peer Benchmark Engine**: compares Real Madrid against selected competitor clubs on supported KPIs
- **Commercial Signal Engine**: highlights which digital signals tend to precede stronger or weaker commercial outcomes
- **Monthly Briefing**: generates a leadership-ready summary after each data refresh

## Why This Project Exists

The project started from a Real Madrid / Universidad Europea internship brief focused on historical digital business data. The base assignment asked for:

- a reproducible Databricks pipeline
- a visualization layer
- optional AI-generated insights

ClubOS expands that brief into a SaaS-style internal product:

- recurring monthly data refresh
- reusable benchmark and KPI logic
- ranked business priorities
- operational decision support

## Product Thesis

ClubOS is not a one-off dashboard.

It is a recurring monthly operating system designed to answer:

- what changed this month that matters
- where the club is ahead or behind peers
- which signals may affect commercial performance next
- what the team should investigate first

## Core Product Principles

- monthly recurring workflow, not one-time analysis
- deterministic logic before AI polish
- benchmark only what the data truly supports
- evidence-backed priorities instead of disconnected charts
- same app, same workflow, new data in, new business answers out

## Data Scope

The current project uses:

- internal monthly data across four digital assets:
  - main website
  - eCommerce
  - streaming
  - fan app
- benchmark monthly data for five peer clubs on selected metrics

The data is treated as the first recurring delivery of a monthly operating feed.

## High-Level Architecture

### Data Platform

- Databricks Free Edition
- Delta Lake
- Unity Catalog
- Python / PySpark

### Product Layer

- React web application
- FastAPI backend
- optional Tableau support layer

### Data Flow

1. monthly source files are uploaded
2. raw data is stored in Bronze
3. cleaned and standardized data is created in Silver
4. app-facing Gold outputs are generated
5. backend exposes the outputs
6. frontend updates the same recurring business workflow

## Repository Structure

```text
.
├── AGENTS.md
├── REPO_STRUCTURE.md
├── agents/
├── apps/
│   ├── clubos-web/
│   └── tableau/
├── backend/
│   └── api/
├── databricks/
│   ├── notebooks/
│   ├── sql/
│   ├── jobs/
│   └── seeds/
├── data_contracts/
├── docs/
├── tests/
└── artifacts/
```

## Source Of Truth Documents

The main product and engineering decisions are documented in:

- `docs/product/clubos_product_definition_report.md`
- `docs/product/clubos_mvp_spec.md`
- `docs/product/clubos_screen_blueprint.md`
- `docs/architecture/clubos_databricks_schema_plan.md`
- `AGENTS.md`
- `REPO_STRUCTURE.md`

## Current MVP Scope

The strict MVP includes:

- recurring monthly ingestion pipeline
- benchmark engine on supported KPIs
- 2–3 validated leading indicators
- operational Priority Board
- Command Center
- Monthly Briefing
- backend API and React product shell

It does not depend on:

- open-ended AI chat
- unsupported benchmark claims
- daily precision from monthly data
- a large scenario simulator

## Getting Started

### 1. Read the source of truth

Before making changes, read:

- `AGENTS.md`
- `REPO_STRUCTURE.md`
- `docs/product/clubos_product_definition_report.md`
- `docs/product/clubos_mvp_spec.md`

### 2. Follow the build sequence

The expected build order is:

1. data contracts
2. Bronze ingestion
3. Silver normalization
4. Gold KPI and benchmark outputs
5. signal validation
6. priority scoring
7. backend API
8. frontend product
9. AI summaries

### 3. Work by role

This repository is structured for role-based development:

- delivery orchestration
- data platform engineering
- analytics engineering
- backend API engineering
- frontend product engineering
- AI insights engineering
- QA and release management

Role files are in the `agents/` folder.

## Definition of Success

ClubOS is successful if:

- the next monthly data delivery can run through the same system
- the product recalculates the same outputs automatically
- business users can see priorities, benchmark position, and signal-based context quickly
- the product feels operational rather than exploratory

## Status

This repository currently contains:

- product strategy and MVP definition
- screen blueprint
- Databricks table and schema plan
- AI-agent build constraints
- implementation repo structure

The next phase is the actual build of the data contracts, Databricks pipeline, backend API, and React product.

## License

Choose a license based on whether the repository is public or private.

For a public portfolio version, MIT is the simplest default.

For an internship or proprietary working version, keep the repository private unless explicitly approved.
```

---

## 5. Recommended GitHub Repository Settings

### Visibility

Recommended for current working version:

- **Private**

Reason:

- the project is based on internship work
- the datasets and product direction are tied to a real club context
- keep it private until you decide what can safely be made public

Later:

- create a sanitized portfolio version if needed

### Features To Enable

- Issues: **On**
- Projects: **On**
- Discussions: **Off** for now
- Wiki: **Off**

### Default Branch

- `main`

### Branch Strategy

Recommended branches:

- `main` -> stable branch
- `develop` -> optional integration branch
- feature branches prefixed like:
  - `feature/data-contracts`
  - `feature/gold-priority-board`
  - `feature/frontend-priority-board`
  - `feature/backend-api`

If you want a simpler solo workflow:

- use `main` plus short-lived feature branches only

### Branch Protection For `main`

Recommended rules:

- require pull request before merge
- require at least 1 approval if you are collaborating
- require status checks if CI exists later
- restrict force pushes

If you are working mostly solo, keep protection light but still use PRs for clean history.

---

## 6. Recommended Labels

Create these GitHub labels:

### Product

- `product`
- `mvp`
- `stretch`
- `demo`

### Engineering

- `data-platform`
- `analytics`
- `backend`
- `frontend`
- `ai`
- `qa`

### Priority

- `priority:high`
- `priority:medium`
- `priority:low`

### Status

- `blocked`
- `needs-review`
- `in-progress`
- `ready`

---

## 7. Suggested Milestones

Create these milestones:

### Milestone 1 — Data Foundation

- contracts
- Bronze ingestion
- Silver normalization

### Milestone 2 — Gold Outputs

- KPI health
- benchmark layer
- signal outputs
- priority inputs

### Milestone 3 — Product Core

- backend API
- Priority Board
- Command Center
- Benchmark screen

### Milestone 4 — Product Completion

- Monthly Briefing
- AI summaries
- event layer
- demo readiness

---

## 8. Suggested GitHub Project Board Columns

Recommended columns:

- Backlog
- Ready
- In Progress
- Review
- Blocked
- Done

If you want a cleaner solo workflow:

- Backlog
- Doing
- Done

---

## 9. Suggested Issue Template Structure

Use this structure for GitHub issues:

### Issue Title Format

- `[Data] Build bronze ingestion for internal workbook`
- `[Analytics] Define priority scoring logic`
- `[Frontend] Implement Priority Board cards`
- `[Backend] Add benchmark endpoint`

### Issue Body Template

```md
## Objective

Describe the goal clearly.

## Why It Matters

Explain the value to ClubOS.

## Scope

- item
- item
- item

## Out of Scope

- item

## Files / Folders

- path
- path

## Acceptance Criteria

- [ ] criterion
- [ ] criterion
- [ ] criterion

## Notes

Assumptions, risks, or dependencies.
```

---

## 10. Suggested Pull Request Template

Create `.github/pull_request_template.md` later using this:

```md
## Summary

What does this PR change?

## Why

Why is this needed?

## Files Changed

- path
- path

## Validation

- [ ] tested locally
- [ ] aligned with AGENTS.md
- [ ] respects REPO_STRUCTURE.md
- [ ] no unsupported product claims introduced

## Risks / Notes

List any assumptions or follow-up items.
```

---

## 11. Suggested First GitHub Issues

Create these first:

1. Create data contracts for internal and benchmark workbooks
2. Build Bronze ingestion notebooks for both source files
3. Build Silver normalization notebooks and validation checks
4. Build `gold_kpi_health`
5. Build `gold_peer_benchmark`
6. Validate 2-3 leading commercial signals
7. Build `gold_priority_inputs` and `gold_priority_board`
8. Create backend API skeleton and MVP endpoints
9. Create React app shell and Priority Board screen
10. Build Monthly Briefing view

---

## 12. Recommended Git Ignore Areas

Make sure the repo ignores:

- local environment files
- notebook outputs if noisy
- generated caches
- build artifacts
- temporary exports
- raw data copies if needed for privacy

Suggested items:

```gitignore
.DS_Store
.env
.env.*
node_modules/
dist/
build/
__pycache__/
.pytest_cache/
.venv/
venv/
.idea/
.vscode/
*.log
artifacts/demo/*.png
artifacts/demo/*.pdf
```

If the real data files should not be committed publicly, keep them out of the public repo.

---

## 13. Recommended License Guidance

For the active working repo:

- keep private unless you are sure the project content is safe to publish

For a future sanitized public version:

- MIT License is the simplest default

Do not publish real or sensitive internship materials without permission.

---

## 14. Recommended First Commit Structure

Suggested first clean repository setup:

1. add strategy docs
2. add AI agent docs
3. add repo structure scaffold
4. add README
5. add `.gitignore`

Then move into:

6. data contracts
7. Databricks notebooks
8. backend
9. frontend

---

## 15. Final GitHub Principle

The GitHub repo should make one thing obvious to any reviewer:

**This is not a class dashboard. This is a structured, role-driven, recurring product build for a SaaS-grade internal platform.**
