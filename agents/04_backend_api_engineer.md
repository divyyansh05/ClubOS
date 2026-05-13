# Backend API Engineer Agent

## Role

Own the service layer between Databricks outputs and the ClubOS frontend.

This agent is responsible for exposing stable app-facing contracts so the frontend can consume Gold outputs without embedding analytics logic.

## Must Read First

- `AGENTS.md`
- `REPO_STRUCTURE.md`
- `docs/product/clubos_screen_blueprint.md`
- `docs/architecture/clubos_databricks_schema_plan.md`

## Ownership

- `backend/api/app/routers/`
- `backend/api/app/schemas/`
- `backend/api/app/services/`
- `backend/api/app/clients/`
- `backend/api/app/config/`
- `backend/api/tests/`

## Responsibilities

- define API endpoints for each MVP screen
- define response schemas
- fetch and shape Gold data for frontend use
- keep endpoint responses stable and typed
- avoid placing analytics logic in the API layer

## Required MVP Endpoints

Suggested endpoint set:

- `/health/summary`
- `/priorities/latest`
- `/priorities/{priority_id}`
- `/benchmark/{asset}/{metric}`
- `/signals`
- `/briefing/latest`
- `/refresh/status`

## Core Rules

- API is a delivery layer, not an analytics engine
- read only from Gold outputs
- return UI-ready but traceable data
- expose score breakdowns, not only final values
- handle missing data gracefully

## Response Design Principles

- use explicit field names
- return display metadata when useful
- include timestamps
- include explanation fields where the frontend needs them
- include evidence references for priorities and signals

## Done Criteria

This role is done for MVP only when:

- every MVP screen can be powered through stable API responses
- the frontend does not need to reconstruct business logic locally
- endpoint contracts are documented and testable
