# Signal Validation Test Coverage

These tests ensure the `gold_signal_relationships` output remains robust across monthly refreshes and doesn't pollute the user interface with noise.

## 1. Table Bound Validations
- **Row Count Maximum**: `gold_signal_relationships` must mathematically restrict itself to `<= 3` rows. Test scripts must assert `ROW_COUNT <= 3`. 
- **Minimum Strength Guarantee**: Iterate across rows with `validation_status = 'active'`. Assert `abs(strength_score) >= 0.65`. If a weaker active signal breaches the table, the job must fail.
- **No Null Interpretations**: The `business_interpretation` column cannot be empty. Without human-readable text, the frontend will render improperly.
- **Empty Table Acceptance**: If no relationships pass threshold, zero rows is a valid output and must not be treated as a pipeline failure.

## 2. Semantic Integrity
- **Direction Alignment**: If `strength_score` > 0, `relationship_direction` must exactly equal `positive`. If < 0, it must equal `negative`.
- **Lag Domain Constraints**: Iterate across `lag_months`. Assert that values strictly exist in the set `{1, 2, 3}`. Lags of `0` contradict the leading indicator premise.
- **No Fabricated Fallback**: Assert that the notebook does not inject hardcoded fallback rows when no active relationship exists.
- **Recency**: `last_validated_month` must equal the latest month present in `silver_internal_asset_metrics` for the evaluated run.

## 3. Target Scope Checks
- **Target Limitation Check**: Verify that `target_metric` falls only within the approved operational bounds (`net_sales`, `conversion_rate`, `subscriptions`). We do not want the system inadvertently attempting to predict secondary engagement patterns.

## 4. Downstream Consumption Guardrail
- **Briefing Consumption Rule**: Any signal included in monthly brief inputs must trace to `gold_signal_relationships` rows where `validation_status = 'active'`.
