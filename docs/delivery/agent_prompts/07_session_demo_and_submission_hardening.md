# Session 07 Prompt - Demo And Submission Hardening

## Copy-Paste Prompt

```text
Read these files first:

- AGENTS.md
- REPO_STRUCTURE.md
- docs/product/clubos_product_definition_report.md
- docs/product/clubos_mvp_spec.md
- docs/product/clubos_screen_blueprint.md
- docs/demos/demo_script.md
- docs/delivery/project_execution_memory.md
- docs/delivery/clubos_work_plan_revised.md
- agents/01_delivery_orchestrator.md
- agents/05_frontend_product_engineer.md
- agents/07_qa_release_manager.md

Also inspect:

- apps/clubos-web/src/*
- backend/api/app/*
- artifacts/demo/*
- output/pdf/clubos_work_plan_revised.pdf

Act jointly as:

- Delivery Orchestrator
- Frontend Product Engineer
- QA Release Manager

Current audit context:

- the MVP should now largely exist
- the project needs to be made demo-safe, submission-safe, and presentation-safe

Your task:
Harden the product and delivery materials for the final presentation and submission stage.

What to do:

1. verify the demo flow is coherent and matches the MVP promise
2. tighten any weak UX text or confusing UI transitions
3. update demo docs to match the actual product
4. prepare the fallback plan if a module fails during presentation
5. ensure the repo tells a clean story for GitHub upload later

Files you may edit:

- apps/clubos-web/src/*
- docs/demos/demo_script.md
- docs/delivery/project_execution_memory.md
- README.md
- artifacts/demo/*
- relevant agent role files only if workflow expectations change materially

Constraints:

- do not add new product modules
- do not widen scope
- polish the MVP that exists
- keep every claim aligned with actual implementation

Required session output:

1. list all files changed
2. describe the final demo path
3. describe the fallback path if one module breaks
4. update `docs/delivery/project_execution_memory.md`
5. finish with:
   - Passed
   - Failed
   - Fix Before Next Prompt
   - confidence score after this session
   - whether Session 08 is safe to run
```
