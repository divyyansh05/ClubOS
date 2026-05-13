# Session 06 Prompt - Quality And Regression

## Copy-Paste Prompt

```text
Read these files first:

- AGENTS.md
- REPO_STRUCTURE.md
- docs/product/clubos_mvp_spec.md
- docs/architecture/api_contract.md
- docs/architecture/gold_table_contracts.md
- docs/delivery/project_execution_memory.md
- agents/07_qa_release_manager.md
- agents/02_data_platform_engineer.md
- agents/04_backend_api_engineer.md
- agents/05_frontend_product_engineer.md

Also inspect:

- tests/data/*
- tests/api/*
- tests/ui/*
- databricks/notebooks/quality/01_run_data_quality_checks.py
- backend/api/app/*
- apps/clubos-web/src/*

Act jointly as:

- QA Release Manager
- Data Platform Engineer
- Backend API Engineer
- Frontend Product Engineer

Current audit context:

- docs and markdown test plans exist, but executable regression protection is still weak
- the product is moving from concept to usable MVP, so regressions now matter

Your task:
Add the minimum executable quality layer needed to trust the recurring monthly workflow.

What to do:

1. convert the most important data checks into executable tests or runnable validation scripts
2. add API contract tests for core endpoints
3. add UI smoke coverage for the main MVP flow
4. ensure the recurring monthly refresh workflow has a real validation gate story

Files you may edit:

- tests/data/*
- tests/api/*
- tests/ui/*
- backend/api/tests/*
- databricks/notebooks/quality/01_run_data_quality_checks.py
- docs/delivery/project_execution_memory.md
- relevant agent role files only if workflow expectations change materially

Constraints:

- focus on the minimum useful regression set
- do not chase perfect coverage
- prioritize recurring refresh safety, Priority Board integrity, and API contract stability

Required session output:

1. list all files changed
2. explain what is now executable versus still documentation-only
3. list the core regressions now protected
4. update `docs/delivery/project_execution_memory.md`
5. finish with:
   - Passed
   - Failed
   - Fix Before Next Prompt
   - confidence score after this session
   - whether Session 07 is safe to run
```
