# Session 05 Prompt - Monthly Briefing Layer

## Copy-Paste Prompt

```text
Read these files first:

- AGENTS.md
- REPO_STRUCTURE.md
- docs/product/clubos_mvp_spec.md
- docs/product/clubos_screen_blueprint.md
- docs/architecture/gold_table_contracts.md
- docs/architecture/api_contract.md
- docs/delivery/project_execution_memory.md
- agents/03_analytics_engineer.md
- agents/04_backend_api_engineer.md
- agents/05_frontend_product_engineer.md
- agents/06_ai_insights_engineer.md
- agents/07_qa_release_manager.md

Also inspect:

- databricks/notebooks/gold/03_build_monthly_brief_inputs.py
- backend/api/app/routers/briefing.py
- backend/api/app/services/briefing_service.py
- backend/api/app/schemas/briefing.py
- apps/clubos-web/src/features/monthly-briefing/MonthlyBriefingPage.tsx

Act jointly as:

- Analytics Engineer
- Backend API Engineer
- Frontend Product Engineer
- AI Insights Engineer
- QA Release Manager

Current audit context:

- Monthly Briefing is part of the MVP but must stay grounded in structured data
- AI may help with wording, but not with ranking or analytics truth

Your task:
Implement the Monthly Briefing module as a real MVP screen backed by structured Gold inputs and a real API contract.

What to do:

1. finish `gold_monthly_brief_inputs` if still incomplete
2. expose a real briefing endpoint
3. build the Monthly Briefing screen
4. keep AI support optional and guarded
5. ensure the screen still works if AI wording is unavailable

Files you may edit:

- databricks/notebooks/gold/03_build_monthly_brief_inputs.py
- backend/api/app/routers/briefing.py
- backend/api/app/services/briefing_service.py
- backend/api/app/schemas/briefing.py
- apps/clubos-web/src/features/monthly-briefing/*
- docs/architecture/gold_table_contracts.md
- docs/architecture/api_contract.md
- docs/delivery/project_execution_memory.md
- relevant agent role files only if workflow expectations change materially

Constraints:

- AI cannot invent new business logic
- the briefing must summarize structured outputs already present elsewhere
- do not add open-ended chat
- keep the module short, leadership-friendly, and monthly

Required session output:

1. list all files changed
2. explain what the briefing is now built from
3. explain where AI is used and where it is explicitly not used
4. update `docs/delivery/project_execution_memory.md`
5. finish with:
   - Passed
   - Failed
   - Fix Before Next Prompt
   - confidence score after this session
   - whether Session 06 is safe to run
```
