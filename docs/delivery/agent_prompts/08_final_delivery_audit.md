# Session 08 Prompt - Final Delivery Audit

## Copy-Paste Prompt

```text
Read these files first:

- AGENTS.md
- REPO_STRUCTURE.md
- docs/product/clubos_product_definition_report.md
- docs/product/clubos_mvp_spec.md
- docs/product/clubos_screen_blueprint.md
- docs/architecture/clubos_databricks_schema_plan.md
- docs/architecture/gold_table_contracts.md
- docs/architecture/api_contract.md
- docs/delivery/project_execution_memory.md
- docs/demos/demo_script.md
- agents/01_delivery_orchestrator.md
- agents/07_qa_release_manager.md

Also inspect the implemented system in:

- databricks/notebooks/
- backend/api/
- apps/clubos-web/
- tests/
- artifacts/demo/

Act jointly as:

- Delivery Orchestrator
- QA Release Manager

Your task:
Run the final delivery audit for ClubOS and judge whether the project is ready for GitHub upload, demo delivery, and final submission.

Audit in these sections:

1. Product truth alignment
2. Gold logic trustworthiness
3. API completeness
4. Frontend completeness
5. Test and regression coverage
6. Demo readiness
7. Submission readiness
8. Final verdict

Required final verdict format:

- final project confidence score: X/10
- ready for GitHub upload: Yes / No
- ready for final demo: Yes / No
- ready for final submission: Yes / No
- if no, exact blockers remaining
- if yes, what advanced features can be explored later

Constraints:

- do not flatter
- do not confuse “looks finished” with “is safe to deliver”
- be strict about unsupported claims
- be strict about recurring monthly workflow viability

Required session output:

1. the full final audit
2. explicit blocker list or go-live list
3. update `docs/delivery/project_execution_memory.md`
4. finish with:
   - Passed
   - Failed
   - Fix After Delivery (if any)
```
