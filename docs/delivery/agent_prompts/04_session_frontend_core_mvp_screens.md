# Session 04 Prompt - Frontend Core MVP Screens

## Copy-Paste Prompt

```text
Read these files first:

- AGENTS.md
- REPO_STRUCTURE.md
- docs/product/clubos_mvp_spec.md
- docs/product/clubos_screen_blueprint.md
- docs/architecture/api_contract.md
- docs/delivery/project_execution_memory.md
- agents/05_frontend_product_engineer.md
- agents/04_backend_api_engineer.md
- agents/07_qa_release_manager.md

Also inspect:

- apps/clubos-web/src/features/command-center/CommandCenterPage.tsx
- apps/clubos-web/src/features/peer-benchmark/PeerBenchmarkPage.tsx
- apps/clubos-web/src/features/signal-engine/SignalEnginePage.tsx
- apps/clubos-web/src/features/priority-board/*
- backend/api/app/routers/health.py
- backend/api/app/routers/benchmark.py
- backend/api/app/routers/signals.py
- backend/api/app/schemas/benchmark.py
- backend/api/app/schemas/signals.py

Act jointly as:

- Frontend Product Engineer
- Backend API Engineer
- QA Release Manager

Current audit context:

- the first vertical slice should now exist or nearly exist
- the next step is to connect the supporting MVP screens around the hero workflow
- Event Intelligence is still out of scope for this session

Your task:
Build the remaining core MVP screens needed for a usable demo:

1. Command Center
2. Peer Benchmark
3. Commercial Signal Engine

What to do:

- ensure the backend contracts needed for these screens are real and stable
- bind each screen to live API responses
- make each screen answer a clear business question
- keep layout operational, not decorative

Files you may edit:

- backend/api/app/routers/health.py
- backend/api/app/routers/benchmark.py
- backend/api/app/routers/signals.py
- backend/api/app/services/*.py
- backend/api/app/schemas/*.py
- apps/clubos-web/src/features/command-center/*
- apps/clubos-web/src/features/peer-benchmark/*
- apps/clubos-web/src/features/signal-engine/*
- apps/clubos-web/src/lib/api.ts
- apps/clubos-web/src/types/clubos.ts
- apps/clubos-web/src/styles/global.css
- docs/delivery/project_execution_memory.md
- relevant agent role files only if workflow expectations change materially

Constraints:

- do not touch Monthly Briefing yet unless absolutely necessary for contract consistency
- do not add Event Intelligence
- do not add speculative metrics or unsupported benchmark comparisons
- keep each screen narrowly aligned to the MVP spec

Required session output:

1. list all files changed
2. explain what is now real on each of the three screens
3. explain any contract assumptions the frontend depends on
4. update `docs/delivery/project_execution_memory.md`
5. finish with:
   - Passed
   - Failed
   - Fix Before Next Prompt
   - confidence score after this session
   - whether Session 05 is safe to run
```
