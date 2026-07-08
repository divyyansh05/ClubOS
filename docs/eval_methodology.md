# ClubOS 2.0 — Eval Methodology

## The three-layer eval architecture

ClubOS 2.0 evaluates Scout outputs across three layers, deliberately ordered by determinism:

### Layer 1 — Fabrication-rate (deterministic)

Custom check. Extracts every number from a Scout answer and from the retrieved
context. A number in the answer that does NOT appear in retrieved context is
classified as fabricated. Year numbers and date-separator false positives are
filtered. Rounding tolerance applied.

This is the HARDEST quality guarantee in the system. The rule is: every
numeric claim in any Scout answer must trace to a retrieved source. The CI
gate enforces `fabrication_incidence_rate=0` as a strict threshold — any
regression here fails the build.

This metric was built specifically for ClubOS because the system is
stakeholder-facing — Real Madrid leadership cannot see invented numbers.
RAGAS faithfulness is a fuzzy signal; fabrication-rate is a binary, auditable
check. We trust binary checks more than fuzzy ones.

### Layer 2 — Behavioural compliance (deterministic)

Custom check. For each golden question, verifies the Scout's structured
output behaviour:
- UNANSWERABLE questions: did the Scout refuse?
- AMBIGUOUS questions: did the Scout state its assumption?
- QUANTITATIVE/NARRATIVE/MIXED: did the Scout cite the expected sources?
- QUANTITATIVE/MIXED: did the Scout query the expected metrics?

Deterministic set operations on the Scout's structured ScoutAnswer schema.
No LLM calls. Sub-second per entry.

The CI gate tolerates a 5-percentage-point drop in `behavioural_pass_rate`.

### Layer 3 — RAGAS LLM-judged metrics (probabilistic)

Standard RAG eval library. Three sub-metrics: faithfulness, context_relevance,
answer_relevance. Each is scored by an LLM-as-judge on each Scout answer.

This layer is METHODOLOGY-COMPLETE: integration code, scorer, report
formatting, CI gate handling are all built and tested. It is INTENTIONALLY
DEFERRED in normal CI runs because:

1. It requires either a paid OpenAI tier (for embeddings) or extended runtime
   on free tier with rate-limit backoff
2. The signal it provides is fuzzy and supplementary, not contract-grade
3. The deterministic layers already provide the hard quality guarantees

RAGAS is run on demand when establishing major baselines (phase boundaries,
significant prompt iterations) where the supplementary signal pays for the
cost. Run with:

    python -m clubos2.eval.pipeline --golden v1 --prompt-version vX
    # (no --skip-ragas flag; uses paid tier credentials from env)

The CI gate skips RAGAS comparisons when the metric is null (not run for
this baseline).

## Why this ordering matters

Deterministic checks gate the build. LLM-judged checks observe quality but
do not gate it. This is a deliberate inversion of the standard RAG eval
pattern, which typically treats RAGAS as the primary quality signal.

The reasoning: LLM-judged scores are themselves probabilistic. Using one
probabilistic system (RAGAS) to gate another probabilistic system (Scout)
introduces compounding fuzziness. Deterministic checks — when they can be
designed for the specific domain — produce hard, auditable, reproducible
guarantees that are much more defensible in production and in interviews.

The fabrication-rate check is a good example of when deterministic beats
fuzzy: a 0.87 RAGAS faithfulness score still tolerates roughly one
hallucinated claim per 7 answers. For stakeholder-facing Real Madrid data,
that is unacceptable. The fabrication-rate check produces zero or non-zero.
Zero is shippable; non-zero is not.

## Baseline and CI flow

- `eval/reports/baseline.json` — the canonical reference point. Updated
  manually at phase boundaries.
- `make v2-eval` — runs the deterministic baseline. Fast, free, run on every
  prompt change.
- `make v2-ci-gate` — runs `scripts/v2_ci_gate.py` comparing current eval
  output against baseline.json. Fails on:
  - Any increase in fabrication_incidence_rate
  - >5pp drop in behavioural_pass_rate
  - >0.05 drop in any RAGAS metric (only when both baseline and current
    have non-null RAGAS scores)
- Prompt iteration workflow lives in `docs/prompt_versioning.md`.

## When to run full RAGAS

- Phase boundaries (establish new baseline with full signal)
- Investigating a behavioural regression that deterministic scorers cannot
  explain
- Before publishing eval results externally (paper, blog, interview material)
- After a significant prompt architecture change (not just wording tweaks)

For routine prompt iteration, deterministic-only is sufficient.

## Baseline stability threshold

Behavioural pass rate is measured as median-of-3 back-to-back deterministic
runs. Individual run variance up to 2pp is treated as sampling noise from
LLM tie-breaking on greedy decode. The CI gate compares median-vs-median,
with regression tolerance of 5pp.

Reproducibility requires:
1. OpenAI-only stack (OPENAI_API_KEY validated at startup via `_validate_openai_key()`)
2. Retry-with-backoff on all external API calls (tenacity, 4 attempts, 2-30s exponential)
3. All golden set metrics present in metric_registry (cross-check via seed.py)
4. Canonical source form enforced at emission (see commit e5b419c)

A residual TPM rate-limit error (gpt-4o, 30k tokens/min tier) may cause 1
question to error out in a run even after all 4 retries. This is treated as
acceptable if: (a) variance across the 3 runs remains ≤ 2pp, (b) the erroring
question was already a behavioral failure in error-free runs, and (c) the
fabrication count remains 0/20. Upgrade to a higher TPM tier or add inter-run
sleep to eliminate this residual.
