# Holdout Set Protocol

The holdout set is the integrity check on prompt iteration. Without it, every prompt
change is at risk of overfitting to the 40 visible golden questions.

## Hard rules
1. Holdout questions live in eval/golden/holdout_set_v1.yaml — never in the main set.
2. The default `make v2-eval` does NOT include holdout questions.
3. The holdout is run ONLY via `make v2-eval-holdout`, manually, at phase boundaries.
4. Holdout questions are NEVER edited based on observed Scout/Investigator behaviour.
   If a holdout question is bad, REPLACE it with a new one drawn from the same
   conceptual area — do not "fix" it to make scores look better.
5. The holdout report includes a comparison: holdout-vs-visible score deltas per metric.
   A gap of > 0.10 on any RAGAS metric indicates overfitting.

## Workflow at phase boundaries
1. Run `make v2-eval` against the visible set — produces the standard phase report
2. Run `make v2-eval-holdout` — produces the holdout report
3. Compare: holdout_faithfulness vs visible_faithfulness. Delta < 0.05 is healthy.
4. If holdout regresses while visible improves, the last 2-3 prompt iterations are
   likely overfitting. Revert and try a different approach.

## When to expand the holdout
The holdout grows when the visible set grows. When the visible set reaches 80, expand
holdout to 20 (25%). When visible reaches 150, holdout reaches 50.

Phase 4 baseline: 40 visible + 10 holdout = 50 total.
