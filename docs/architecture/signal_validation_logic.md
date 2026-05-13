# Signal Validation Logic

This document formalizes how ClubOS detects and publishes internal commercial signals.

## 1. Objective
Identify 1–3 month lagged correlations between top-of-funnel or engagement indicators (candidate features) and trailing revenue, conversion, or subscription milestones. The goal is business actionability, not black-box prediction.

## 2. Constraints & Exclusions
- **No Same-Month Correlations**: Correlating `visits` against `sales` in the exact same month is descriptive, not predictive. Signals must lead the target by 1, 2, or 3 months.
- **Explainability Bound**: Only theoretically sound business connections are tested. (e.g., app engagement trailing into eCommerce purchasing makes sense). Opaque statistical anomalies are blocked and never make it to the Gold layer.
- **Top 3 Limit**: The `gold_signal_relationships` table enforces a maximum capacity of 3 signals. Exceeding this introduces noise and contradicts the "focus" premise of the Priority Board.

## 3. Mathematical Pipeline (`01_validate_signals.py`)

### Target Commercial Metrics
The MVP focuses strictly on identifying precursors to three defined targets:
1. `ecommerce.net_sales`
2. `ecommerce.conversion_rate`
3. `streaming.subscriptions`

### Validation Methodology
1. **Pivoted Asset Construction**: The PySpark pipeline joins `silver_internal_asset_metrics` sideways into a wide monthly vector dataframe.
2. **Windowed Timeshift**: Target commercial metrics are evaluated using `F.lead(..., lag)` to align future targets onto present-day precursors month-by-month.
3. **Threshold Check**: A Pearson correlation is evaluated against the non-null intersections.
4. **Acceptance Threshold**: The absolute correlation coefficient (`strength_score`) must safely exceed `|0.65|`. 
5. **Business Interpretation Merge**: The script marries successful thresholds to pre-written, plain-English interpretation templates.
6. **No Fabricated Fallback**: If zero signals pass the mathematical threshold, the table remains empty for that run. The pipeline does not inject synthetic or manually-curated rows into `gold_signal_relationships`.

## 4. Output Contract
The resulting table `gold_signal_relationships` serves the Commercial Signal Engine screen.
**Key Columns**:
- `source_asset`, `source_metric`
- `target_asset`, `target_metric`
- `lag_months` (1, 2, or 3)
- `relationship_direction` (`positive` or `negative`)
- `strength_score` (float bounded between -1 and +1)
- `validation_status` (`active` or `curated_hypothesis`)
- `business_interpretation` (String designed for front-end rendering)
- `last_validated_month` (Dynamic month tied to the latest month evaluated in the run context)

## 5. Scoring Guardrail
- Priority scoring only consumes rows where `validation_status = 'active'`.
- Curated hypothesis rows may exist in future flows, but are excluded from core scoring by design.
- Monthly Briefing inputs only consume `active` signal rows and may legally store an empty signal list when no relationships pass validation.
