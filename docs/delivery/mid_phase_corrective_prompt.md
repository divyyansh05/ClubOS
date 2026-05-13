# ClubOS Mid-Phase Corrective Prompt

Use this prompt when the mid-phase audit shows that the data layer is stronger, but the product logic is still not trustworthy enough for backend and frontend expansion.

This corrective step exists to fix the three blockers that matter most:

- peer benchmark logic must compare Real Madrid internal metrics against competitor benchmark distributions correctly
- signal validation must not fabricate "active" signals when the data does not support them
- priority board outputs must include a real evidence chain instead of placeholder support fields

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
- docs/architecture/signal_validation_logic.md
- docs/architecture/priority_board_logic.md
- docs/architecture/source_data_audit.md
- data_contracts/internal_metrics_contract.md
- data_contracts/benchmark_contract.md
- data_contracts/metric_inventory.md
- agents/02_data_platform_engineer.md
- agents/03_analytics_engineer.md
- agents/07_qa_release_manager.md

Also inspect these implementation files:

- databricks/notebooks/gold/01_build_kpi_health.py
- databricks/notebooks/gold/02_build_peer_benchmark.py
- databricks/notebooks/analytics/01_validate_signals.py
- databricks/notebooks/analytics/02_compute_priority_inputs.py
- databricks/notebooks/gold/04_build_priority_board.py
- tests/data/test_signal_validation.md
- tests/data/test_priority_board.md

Act jointly as:

- Data Platform Engineer
- Analytics Engineer
- QA Release Manager

Your task:
Correct the remaining mid-phase blockers so ClubOS is genuinely ready for backend API and frontend product expansion.

There are 3 required corrections:

## Correction 1: Fix the peer benchmark logic
The current benchmark logic is not acceptable if it treats a competitor row as the Real Madrid client row.

What to do:
1. Rebuild `gold_peer_benchmark` so the client-side metric value comes from Real Madrid internal data, not from a benchmark club row.
2. Use the benchmark file only to construct peer distributions, peer medians, peer leaders, ranks, and gap context for benchmark-supported metrics.
3. Document clearly how the client metric is aligned to the peer comparison layer by month, asset, and metric.
4. If a metric is not benchmark-supported, it must not appear as benchmarked in Gold.

Files you may edit:
- databricks/notebooks/gold/02_build_peer_benchmark.py
- docs/architecture/gold_table_contracts.md
- docs/architecture/bronze_silver_logic.md
- tests/data/test_gold_contracts.md
- tests/data/test_priority_board.md

## Correction 2: Remove fabricated validated signals
The signal engine must not publish fake "active" signals when the math does not support them.

What to do:
1. Remove the fallback block that writes manually curated signals as if they were mathematically validated.
2. If no signal passes the required threshold, the output table should either:
   - be empty, or
   - contain rows explicitly marked as `validation_status = "curated_hypothesis"` and excluded from core scoring logic.
3. Make `last_validated_month` dynamic and tied to the actual run context.
4. Update signal docs and tests so they explicitly enforce the new behavior.

Files you may edit:
- databricks/notebooks/analytics/01_validate_signals.py
- docs/architecture/signal_validation_logic.md
- tests/data/test_signal_validation.md

## Correction 3: Add a real evidence chain to the Priority Board
The hero feature is not complete until every card can show its stored evidence.

What to do:
1. Replace the mocked `supporting_metrics_json = '[]'` behavior.
2. Build a deterministic evidence payload for each priority card containing at minimum:
   - severity inputs
   - persistence inputs
   - peer context if available
   - linked signal references if applicable
   - any additional supporting metric rows used to justify the rank
3. Ensure every priority row remains fully usable without AI.
4. Update docs and tests to verify that priority evidence exists and is inspectable.

Files you may edit:
- databricks/notebooks/analytics/02_compute_priority_inputs.py
- databricks/notebooks/gold/04_build_priority_board.py
- docs/architecture/priority_board_logic.md
- tests/data/test_priority_board.md

Required output expectations:
- the logic must remain deterministic
- the logic must remain monthly, not daily
- the benchmark layer must remain narrow and honest
- the product must not overclaim what the data proves
- the fixes must make the data layer safer for API/UI expansion, not just produce nicer docs

Constraints:
- do not touch frontend yet
- do not touch backend yet
- do not add AI-generated logic into scoring or ranking
- do not preserve broken behavior just to keep outputs non-empty
- do not hardcode Real Madrid findings into the Gold layer

Final deliverable:
At the end, provide:
1. every file changed
2. the exact peer benchmark correction made
3. the exact signal fallback behavior now enforced
4. the exact evidence structure now present on each priority row
5. a hard verdict:
   - mid-phase confidence score: X/10
   - ready for API expansion: Yes / No
   - ready for frontend expansion: Yes / No
   - if no, exact blockers remaining
```

## Purpose Of This Corrective Step

This prompt is meant to close the trust gap before the product surface expands.

The goal is not to make the repo look more complete.
The goal is to make the core business logic strong enough that API and UI work can safely depend on it.
