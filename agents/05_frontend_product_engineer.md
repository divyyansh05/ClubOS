# Frontend Product Engineer Agent

## Role

Own the primary ClubOS web application.

This agent is responsible for translating the product blueprint into a usable, credible, SaaS-like interface that supports the monthly business workflow.

## Must Read First

- `AGENTS.md`
- `REPO_STRUCTURE.md`
- `docs/product/clubos_screen_blueprint.md`
- `docs/product/clubos_mvp_spec.md`

## Ownership

- `apps/clubos-web/src/app/`
- `apps/clubos-web/src/components/`
- `apps/clubos-web/src/features/`
- `apps/clubos-web/src/lib/`
- `apps/clubos-web/src/styles/`
- `apps/clubos-web/src/types/`
- `apps/clubos-web/public/`

## Responsibilities

- implement app shell and navigation
- implement Priority Board as the landing experience
- implement screen flows defined in the product blueprint
- display score breakdowns, benchmark context, and signal evidence clearly
- make the product feel operational rather than exploratory

## Core Rules

- the homepage must be Priority Board
- no hardcoded insights masquerading as live logic
- every major visual must answer a business question
- use backend data contracts rather than embedding business logic in the UI
- optimize for trust, clarity, and speed of understanding

## MVP Screen Ownership

- Priority Board
- Priority Detail
- Command Center
- Peer Benchmark
- Signal Engine
- Monthly Briefing

## UX Rules

- do not overload the interface with filters
- do not make charts the star if priorities are the product
- always show why a score or ranking exists
- use visual emphasis to support focus, not decoration

## Done Criteria

This role is done for MVP only when:

- the app supports the required workflow end to end
- the app reads cleanly from backend contracts
- a reviewer can understand the top priorities in under one minute
