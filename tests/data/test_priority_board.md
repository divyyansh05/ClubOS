# Priority Board Test Coverage

These tests guarantee that the core logic generating the hero interface safely prioritizes internal actions without overclaiming peer limits or fabricating data.

## 1. Boundary & Limit Checks
- **Output Record Limit**: The `gold_priority_board` cannot output more than 10 rows per month (assert `row_number() <= 10`). Generating endless queues contradicts the core premise of focus.
- **Score Max Boundaries**: Calculate total priority weights (e.g. 0.3 + 0.2 + 0.2 + 0.2 + 0.1). Assert that `priority_score` max == 1.0.
- **Peer Score Consistency**: `peer_gap_score` must be derived from polarity-aware `rm_rank` semantics from `gold_peer_benchmark`, not raw value ordering.

## 2. Text Validity
- **Structural Integrity**: Ensure `priority_title`, `summary_text`, `why_it_matters`, and `suggested_next_investigation` never evaluate to `null`. Without them, the React application completely falls over and crashes. 
- **AI Exclusión Guarantee**: The generated text values must explicitly adhere to the logic switches mapped directly from underlying data dimensions (e.g., if category like 'conversion', then print the funnel drop-off text string). No dynamic hallucinated logic should be passed into these rows to satisfy the SaaS scale requirements.

## 3. Evidence Audit Constraint
- **Payload Viability**: Validate `supporting_metrics_json` as an object (not `[]`) and assert required keys exist: `score_components`, `severity_inputs`, `persistence_inputs`, `linked_signal_references`, `supporting_metric_rows`.
- **Peer Context Nullability**: `peer_context` may be null for non-benchmarked metrics, but when present it must include `peer_rank`, `peer_club_count`, `peer_median`, `peer_leader_value`, `gap_to_peer_median`, and `gap_to_leader`.
- **Supporting Rows Integrity**: `supporting_metric_rows` should list additional non-stable metrics from the same `month + asset_name` context and must not duplicate `primary_metric`.
