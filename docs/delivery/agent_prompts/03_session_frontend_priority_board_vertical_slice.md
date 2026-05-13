# Session 03 Prompt - Frontend Priority Board Vertical Slice

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
- agents/07_qa_release_manager.md

Also inspect:

- apps/clubos-web/src/app/App.tsx
- apps/clubos-web/src/components/ui/PageShell.tsx
- apps/clubos-web/src/features/priority-board/PriorityBoardPage.tsx
- apps/clubos-web/src/lib/api.ts
- apps/clubos-web/src/types/clubos.ts
- backend/api/app/routers/priorities.py
- backend/api/app/schemas/priorities.py

Act jointly as:

- Frontend Product Engineer
- QA Release Manager

Current audit context:

- Priority Board is the hero module
- backend should now expose real priority endpoints
- frontend is still placeholder-only and must become the first true product slice

Your task:
Build the first real end-to-end vertical slice for ClubOS: the Priority Board screen and its evidence-aware detail flow.

What to build:

1. Real API integration for latest priorities
2. Real Priority Board page rendering:
   - summary strip
   - top ranked cards
   - score/category display
   - why-it-matters text
   - evidence/context preview
3. Priority detail view or drawer showing:
   - score breakdown
   - supporting evidence payload
   - peer context if present
   - next investigation text
4. Real loading / empty / error states

Files you may edit:

- apps/clubos-web/src/app/App.tsx
- apps/clubos-web/src/components/ui/PageShell.tsx
- apps/clubos-web/src/features/priority-board/*
- apps/clubos-web/src/lib/api.ts
- apps/clubos-web/src/types/clubos.ts
- apps/clubos-web/src/styles/global.css
- docs/delivery/project_execution_memory.md
- relevant agent role files only if workflow expectations change materially

Constraints:

- do not build every screen in this session
- Priority Board must be the default landing page
- do not use fake data if the API contract is now real
- avoid decorative dashboard cards with weak meaning
- every displayed score must have a visible breakdown path

Required session output:

1. list all files changed
2. describe the real Priority Board flow now working
3. explain how the evidence chain appears in the UI
4. note any API contract gaps exposed by the frontend
5. update `docs/delivery/project_execution_memory.md`
6. finish with:
   - Passed
   - Failed
   - Fix Before Next Prompt
   - confidence score after this session
   - whether Session 04 is safe to run
```
