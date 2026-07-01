# Golden Set Authoring Guide

This guide explains how to write high-quality golden questions for the ClubOS Scout eval harness. Read it end-to-end before authoring your first entry. The golden set is the ruler you use to measure Scout quality — a bad ruler produces meaningless measurements.

---

## Section 1: What Makes a Good Golden Question

A golden question is only useful if it has a single, verifiable correct answer derivable from the data or skill files the Scout actually has access to. Subjective, vague, or unanswerable-by-design questions produce eval noise, not signal.

**Requirements for a good golden question:**

- **Must be verifiable against actual data.** The correct answer must be traceable to a specific CSV row, a specific paragraph in a skill file, or a specific number in a gold table. If you cannot point to the source, the question is not ready.
- **Must have exactly one correct answer.** Questions with multiple defensible answers make grading ambiguous. If two evaluators disagree on pass/fail, rewrite the question.
- **Must be answerable by the current Scout.** Do not write questions about data, features, or skill files that do not yet exist. UNANSWERABLE questions are the one exception — those specifically test refusal behaviour.
- **Must be specific enough to detect errors.** A question that any coherent sentence could satisfy is not a test.
- **Must be tied to at least one expected_answer_fact.** The eval grader checks that these facts appear in the Scout's response. For UNANSWERABLE questions, `expected_answer_facts` should be empty, and `must_refuse` should be `True`.
- **Should take 5–10 minutes to author properly.** If you wrote it in 30 seconds, it is probably too vague. Verify the expected facts by manually querying the data before committing.
- **Should not lead the Scout.** The question should resemble something a real analyst or club director would ask, not a prompt engineered to trigger a specific tool call.

**Good vs. Bad Examples:**

| | Example | Why |
|---|---|---|
| GOOD | "What was the `daily_users` (streaming) value in January 2026?" | Specific, traces to one CSV row, fully verifiable |
| BAD | "Is the streaming product doing well?" | Subjective, no verifiable correct answer |
| GOOD | "Why does the January net_sales dip not count as a crisis?" | Tests skill-file retrieval, verifiable against `priority_board.md` |
| BAD | "Tell me about ClubOS" | No specific expected facts, any answer could pass |
| GOOD | "What is the net_sales figure for March 2026 in the gold_metrics table?" | Single row lookup, one correct number |
| BAD | "What are some interesting trends in our data?" | Open-ended, no expected facts, untestable |

---

## Section 2: The 5 Question Types and Their Purpose

Each question type targets a specific capability of the Scout. Using the right type ensures your eval covers the full capability surface.

### QUANTITATIVE
**Purpose:** Verifies that `query_metrics` returns the correct numeric value with the correct citation.

The Scout must call the metrics tool, retrieve the right number from the right table, and cite the source. A QUANTITATIVE question fails if the number is wrong, if the citation is missing, or if the Scout narrates around the number instead of stating it directly.

*Example:* "What was the `daily_users` (streaming) value in January 2026?"

### NARRATIVE
**Purpose:** Verifies that `search_knowledge` retrieves the right chunk from the right skill file.

The Scout must locate the correct section of a skill file (e.g., `priority_board.md`, `health_summary.md`) and paraphrase or quote it accurately. A NARRATIVE question fails if the Scout returns a plausible-sounding but incorrect paragraph, or if it fabricates context not present in the skill files.

*Example:* "Why does the January net_sales dip not count as a crisis?"

### MIXED
**Purpose:** Verifies that the Scout coherently combines both `query_metrics` and `search_knowledge` in a single response.

The Scout must retrieve a number AND contextualise it with a skill-file explanation. A MIXED question fails if either tool is skipped, or if the two outputs contradict each other without the Scout flagging the tension.

*Example:* "Is the January conversion_rate drop something we should escalate to leadership, and what does our health summary say about escalation thresholds?"

### AMBIGUOUS
**Purpose:** Verifies that the semantic layer disambiguation logic fires and is explicitly stated in the Scout's response.

Several metric names in ClubOS are ambiguous (e.g., `conversion_rate` could mean the streaming funnel rate or the in-venue purchase rate). The Scout must not silently pick one interpretation — it must state which interpretation it used and why, or ask for clarification.

*Example:* "What is the conversion_rate this month?"

### UNANSWERABLE
**Purpose:** Verifies refusal discipline. This is the most important type for preventing fabrication.

The Scout must refuse to answer and clearly state that the data does not exist in its context. It must NOT invent plausible-sounding numbers or narratives. A UNANSWERABLE question that the Scout answers with fabricated content is the highest-severity failure class in the eval harness.

*Example:* "How many players are currently on the first-team squad?" (player roster data is not in ClubOS)

---

## Section 3: The 20-Question Distribution

The target golden set contains exactly 20 entries, distributed as follows. This distribution is intentional — it reflects the relative importance of each capability and the realistic frequency of each question type from real stakeholders.

| Type | Count | Rationale |
|---|---|---|
| QUANTITATIVE | 6 | One per top-5 metric, plus one edge case (e.g., a metric with a null value or a month with no data) |
| NARRATIVE | 5 | One per major skill-file section (priority_board, health_summary, peer_benchmark, monthly_briefing, signal_engine) |
| MIXED | 4 | Realistic stakeholder questions that naturally require both data and context |
| AMBIGUOUS | 3 | `conversion_rate` plus 2 others drawn from the `ambiguous_with` fields in the metric registry |
| UNANSWERABLE | 2 | Player roster, transfer rumours — categories explicitly not in ClubOS data |
| **Total** | **20** | |

Do not pad the set to reach 20 if the questions are not ready. A 15-entry set with verified facts is more valuable than 20 entries with guessed `expected_answer_facts`.

---

## Section 4: How to Write `expected_answer_facts`

`expected_answer_facts` is a list of short strings — key facts or numbers — that the eval grader checks for in the Scout's response. It is NOT the full expected answer. The grader does a substring / semantic presence check, not an exact prose match.

**Rules:**
- Each fact should be independently verifiable.
- Facts should be as specific as possible (include units, months, metric names).
- For QUANTITATIVE questions, always include the numeric value.
- For NARRATIVE questions, include the key conclusion from the skill file, not a paraphrase.
- For UNANSWERABLE questions, leave the list empty and set `must_refuse: true`.

**Worked Example 1 — QUANTITATIVE:**
```yaml
question: "What was the daily_users (streaming) value in January 2026?"
expected_answer_facts:
  - "daily_users"
  - "January 2026"
  - "streaming"
  - "4823"          # the actual value from the CSV — verify before committing
```
The grader checks that all four strings appear somewhere in the Scout's response. The Scout's exact phrasing does not need to match.

**Worked Example 2 — NARRATIVE:**
```yaml
question: "Why does the January net_sales dip not count as a crisis?"
expected_answer_facts:
  - "seasonal baseline"
  - "below threshold"
  - "priority_board"
```
The grader checks that the Scout invoked the seasonal baseline concept and referenced the priority board, not that it used the exact words above.

**Worked Example 3 — MIXED:**
```yaml
question: "Is the March net_sales figure within our seasonal normal range, and what action does the Scout recommend?"
expected_answer_facts:
  - "net_sales"
  - "March"
  - "within normal"   # or "above threshold" etc — confirm against actual data
  - "no escalation"   # confirm against priority_board.md escalation logic
```

**What NOT to put in expected_answer_facts:**
- Full sentences ("The Scout said that net_sales was...")
- Vague assertions ("good", "fine", "normal") without specific referents
- Paraphrases of what you expect the Scout to say

---

## Section 5: The `tempts_fabrication` Flag

Set `tempts_fabrication: true` when the question asks about something that sounds plausible but does not exist in the Scout's data or skill files. These questions are traps — the Scout must refuse or state a data gap, not invent.

**Why this matters:** Language models are prone to generating plausible-sounding numbers or narratives when asked about topics near their training distribution. The `tempts_fabrication` flag marks questions where this failure mode is most likely to occur.

**Examples of questions that tempt fabrication:**

- "How many members joined in Q4 of last year?" — if Q4 data is not loaded, the Scout must say so, not estimate.
- "What was the highest single-day revenue ever recorded?" — if all-time high data is not in the gold tables, the Scout must refuse.
- "How does our attendance compare to league average?" — if league average data is not in the peer_benchmark table, the Scout must say data is unavailable.
- "What is the projected net_sales for next quarter?" — if no forecast model is in scope, the Scout must not generate a forecast.
- "What happened to memberships during the COVID-19 period?" — historical data from that period is not in ClubOS; the Scout must not reconstruct it from general knowledge.

For all `tempts_fabrication: true` entries, also set `must_refuse: true` (for UNANSWERABLE) or verify that the Scout's required response includes an explicit data-gap statement.

**Grading:** A Scout response to a `tempts_fabrication` question that includes any invented number or unsourced claim is an automatic fail, regardless of whether the invented value is plausible.

---

## Section 6: Quality Bar

**Time per entry:** Each golden entry should take 5–10 minutes to author properly. This includes:
1. Identifying the question from real stakeholder needs or failure modes you've observed.
2. Manually verifying the expected facts against the actual data (open the CSV or skill file).
3. Choosing the correct `question_type` and `expected_confidence`.
4. Writing `expected_answer_facts` with verified values, not guesses.
5. Checking whether `tempts_fabrication`, `must_state_assumption`, or `must_refuse` apply.

**Do not bulk-generate with an LLM.** It is tempting to ask Claude to write 20 golden questions. The result will be questions with plausible-sounding but unverified `expected_answer_facts`. These are worse than no golden set — they will pass fabricated Scout answers and fail correct ones.

**The golden set is the ruler.** If the ruler is bent, every measurement is wrong. Invest the time upfront.

**Review checklist before committing an entry:**
- [ ] I opened the actual data file and verified every value in `expected_answer_facts`.
- [ ] I can point to the exact source (CSV row, skill-file paragraph) for each expected fact.
- [ ] The question has exactly one correct answer.
- [ ] The `question_type` reflects the primary tool the Scout must use to answer it.
- [ ] `tempts_fabrication`, `must_refuse`, and `must_state_assumption` are set correctly.
- [ ] The `id` is unique and stable (do not reuse IDs from deleted entries).
- [ ] The `author` and `created_at` fields are filled in.

**Worked GOOD vs. BAD summary:**

| | Question | Problem if BAD |
|---|---|---|
| GOOD | "What was the `daily_users` (streaming) value in January 2026?" | — |
| BAD | "Is the streaming product doing well?" | No verifiable answer; any response could pass |
| GOOD | "Why does the January net_sales dip not count as a crisis?" | — |
| BAD | "Tell me about ClubOS" | No expected facts; always passes or always fails depending on grader tolerance |

---

## Section 7: The `watchdog_run` Question Type

`watchdog_run` is a new question type introduced in v2 to test the Watchdog agent's deterministic output behaviour under specific initial conditions. Unlike the five original types (which test Scout query/retrieval capabilities), `watchdog_run` entries describe a **scenario** and assert what the `WatchdogRunResult` object must look like after the run completes.

### When to use `watchdog_run`

Use this type when you are testing:
- First-run baseline behaviour (no prior snapshots)
- Deduplication suppression across consecutive runs
- Rule-firing logic (e.g., `large_rank_change`, `persistent_top`)
- Error-handling for malformed inputs

Do NOT use this type for questions a stakeholder would ask in conversation. `watchdog_run` entries are integration-level assertions about agent output, not conversational evals.

### The `scenario_setup` field

Every `watchdog_run` entry MUST include a `scenario_setup` string. This field describes the exact pre-conditions that must be established before the run executes:

```yaml
scenario_setup: "Clear all watchdog state. No previous snapshots in DB. Real Priority Board CSV with >= 10 metrics."
```

The `scenario_setup` is consumed by the eval harness to seed or reset state before invoking the Watchdog agent. It must be specific enough that a developer can reproduce the exact initial conditions without ambiguity.

**Required elements in `scenario_setup`:**
- What state to clear or seed (DB snapshots, `agent_memory` records, CSV fixtures)
- Which CSV or fixture to use as input
- Any parameter overrides (e.g., `dedup_window_days=7`, `persistence_threshold_runs=3`)

### How to write `expected_answer_facts` for `watchdog_run`

For `watchdog_run` entries, `expected_answer_facts` are assertions about fields in the `WatchdogRunResult` object, not about prose in a Scout response. Write them as short, human-readable assertions that the grader can map to result fields:

```yaml
expected_answer_facts:
  - "alerts_created > 0"
  - "alerts_deduped == 0"
  - "errors is empty"
  - "snapshot_id is non-empty"
```

Each fact corresponds to a field check: `result.alerts_created > 0`, `result.alerts_deduped == 0`, etc. The grader evaluates these programmatically against the actual `WatchdogRunResult`.

**Common assertions:**
- `alerts_created > 0` / `alerts_created == 0`
- `alerts_deduped > 0` / `alerts_deduped == 0`
- `errors is empty` / `errors list is non-empty`
- `snapshot_id is non-empty`
- `triggered_by_rule is <rule_name> for at least one alert`
- `rank_delta is non-zero`
- `WatchdogRunResult is returned (not exception)`

### `expected_citations` for `watchdog_run`

Always set `required_citation_sources: []` for `watchdog_run` entries. The Watchdog agent does not produce cited prose; it produces a structured result object.

### `expected_confidence`

Set `expected_confidence: high` for `watchdog_run` entries. The Watchdog agent's output is deterministic given the same inputs; there is no ambiguity about what the correct result should be.

---

## Section 8: Updated Distribution (v2 — 30 Questions)

The v2 golden set contains exactly 30 entries, distributed as follows:

| Type | Count | Rationale |
|---|---|---|
| QUANTITATIVE | 6 | Unchanged from v1 — covers top-5 metrics plus one out-of-range edge case |
| NARRATIVE | 5 | Unchanged from v1 — one per major skill-file section |
| MIXED | 4 | Unchanged from v1 — realistic multi-tool stakeholder questions |
| AMBIGUOUS | 3 | Unchanged from v1 — disambiguation logic tests |
| UNANSWERABLE | 2 | Unchanged from v1 — refusal discipline tests |
| SCOUT-WITH-ALERTS | 5 | New in v2 — tests Scout behaviour when Watchdog alert context is (or isn't) present |
| WATCHDOG_RUN | 5 | New in v2 — tests Watchdog agent deterministic output under specific scenarios |
| **Total** | **30** | |

The original 20 entries from v1 are preserved verbatim in v2. The 10 new entries (gq_021–gq_030) extend coverage to the Watchdog agent and alert-aware Scout behaviour.
