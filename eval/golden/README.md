# eval/golden — Golden Question Set

The golden set is 20 hand-authored question-and-answer pairs used to measure ClubOS Scout quality. Each entry specifies a question, the key facts that must appear in the answer, and the expected behaviour (tool calls, citations, refusal).

## File Structure

| File | Purpose |
|---|---|
| `schema.py` | Pydantic v2 models: `GoldenEntry`, `GoldenSet`, `QuestionType`, `ExpectedConfidence` |
| `authoring_guide.md` | How to write good golden questions — read before adding entries |
| `golden_set_v1.yaml` | The 20 hand-authored entries *(coming in Prompt 2.1.2)* |
| `loader.py` | Loads and validates `golden_set_v1.yaml` against the schema *(coming in Prompt 2.1.3)* |

## Workflow

1. **Author** — follow `authoring_guide.md` to write entries in `golden_set_v1.yaml`
2. **Run eval** — execute the harness against the current Scout
3. **See scores** — review pass/fail per entry and per question type
4. **Improve Scout** — fix prompts, tools, or skill files based on failures
5. **Re-run** — repeat until all 20 pass

## Adding New Questions

Read `authoring_guide.md` fully before adding questions. New entries go into `golden_set_v2.yaml` once `golden_set_v1.yaml` has been used for at least one eval run.

## Version Policy

`golden_set_v1.yaml` is **immutable** once the first eval run is recorded. Changing entries retroactively invalidates historical score comparisons. New or revised questions belong in a new versioned file (`golden_set_v2.yaml`, etc.).
