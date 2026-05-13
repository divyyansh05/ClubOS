# Session 01 Prompt - Gold Trust Closure

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
- docs/architecture/priority_board_logic.md
- docs/architecture/signal_validation_logic.md
- docs/architecture/source_data_audit.md
- docs/delivery/project_execution_memory.md
- data_contracts/internal_metrics_contract.md
- data_contracts/benchmark_contract.md
- data_contracts/metric_inventory.md
- agents/02_data_platform_engineer.md
- agents/03_analytics_engineer.md
- agents/07_qa_release_manager.md

Also inspect these implementation files:

- databricks/notebooks/gold/01_build_kpi_health.py
- databricks/notebooks/gold/02_build_peer_benchmark.py
- databricks/notebooks/gold/03_build_monthly_brief_inputs.py
- databricks/notebooks/gold/04_build_priority_board.py
- databricks/notebooks/analytics/01_validate_signals.py
- databricks/notebooks/analytics/02_compute_priority_inputs.py
- databricks/notebooks/quality/01_run_data_quality_checks.py
- tests/data/test_gold_contracts.md
- tests/data/test_signal_validation.md
- tests/data/test_priority_board.md

Act jointly as:

- Data Platform Engineer
- Analytics Engineer
- QA Release Manager

Current audit context:

- Mid-phase confidence is 6.5/10
- API/UI expansion is not yet safe
- The remaining Gold-layer blockers are:
  1. polarity-aware peer benchmark ranking and leader/gap semantics
  2. `gold_monthly_brief_inputs` implementation
  3. hard data-quality gate checks with run-failure behavior

Your task:
Close the remaining Gold-layer trust gaps so the project is genuinely ready for backend contract work.

What to do:

1. Fix `gold_peer_benchmark` so inverse-polarity metrics are ranked and compared correctly.
2. Implement `gold_monthly_brief_inputs` so the Monthly Briefing MVP module has a real Gold input table.
3. Upgrade the quality checks so they can fail-stop when required checks fail.
4. Update Gold/quality architecture docs and markdown test specs to match the new behavior.

Files you may edit:

- databricks/notebooks/gold/02_build_peer_benchmark.py
- databricks/notebooks/gold/03_build_monthly_brief_inputs.py
- databricks/notebooks/quality/01_run_data_quality_checks.py
- docs/architecture/gold_table_contracts.md
- docs/architecture/priority_board_logic.md
- docs/architecture/signal_validation_logic.md
- tests/data/test_gold_contracts.md
- tests/data/test_signal_validation.md
- tests/data/test_priority_board.md
- docs/delivery/project_execution_memory.md
- relevant agent role files only if workflow expectations change materially

Constraints:

- do not touch backend yet
- do not touch frontend yet
- keep everything monthly, deterministic, and inspectable
- do not overclaim signal confidence
- do not add Event Intelligence work in this session

Required session output:

1. list all files changed
2. explain the benchmark polarity correction
3. explain what `gold_monthly_brief_inputs` now contains
4. explain what quality checks can now fail the run
5. update `docs/delivery/project_execution_memory.md`
6. finish with:
   - Passed
   - Failed
   - Fix Before Next Prompt
   - confidence score after this session
   - whether Session 02 is safe to run
```
