# ClubOS Agent Operator Guide

## Purpose

This is the short operator guide for running the ClubOS build through Claude/Codex session prompts.

Use this file when you are the human coordinator and need to:

- know exactly what to paste into the AI
- verify whether a session is genuinely complete
- decide whether to continue to the next prompt or stop and fix blockers

This guide should be used together with:

- `docs/delivery/agent_prompt_sequence.md`
- `docs/delivery/project_execution_memory.md`

## 1. What To Paste Into Claude/Codex Each Time

For every session, do the same thing:

1. Open the next prompt file in sequence
2. Copy the full prompt content
3. Paste it into Claude/Codex
4. Let the agent work only on that session

Do not rewrite the prompt casually unless you need to add a small clarifying note.

### Recommended Paste Format

When you send the prompt, use this short wrapper above it:

```text
Run this session exactly as written.
Follow the file constraints strictly.
Do not skip the required self-audit.
Do not skip updating `docs/delivery/project_execution_memory.md`.

[then paste the full session prompt]
```

That is enough.

You do not need to add extra explanation unless:

- the previous session was blocked
- you manually changed files in between
- the agent explicitly asked for something from you

## 2. Exact Session Order

Run prompts in this order only:

1. `docs/delivery/agent_prompts/01_session_gold_trust_closure.md`
2. `docs/delivery/agent_prompts/02_session_backend_core_contracts.md`
3. `docs/delivery/agent_prompts/03_session_frontend_priority_board_vertical_slice.md`
4. `docs/delivery/agent_prompts/04_session_frontend_core_mvp_screens.md`
5. `docs/delivery/agent_prompts/05_session_monthly_briefing_layer.md`
6. `docs/delivery/agent_prompts/06_session_quality_and_regression.md`
7. `docs/delivery/agent_prompts/07_session_demo_and_submission_hardening.md`
8. `docs/delivery/agent_prompts/08_final_delivery_audit.md`

Do not skip ahead unless the previous session explicitly says the next one is safe.

## 3. What To Check After Every Session

When the agent finishes a session, check these 5 things:

### A. Did it update the shared memory file?

Open:

- `docs/delivery/project_execution_memory.md`

The session is not really complete unless this file was updated with:

- what changed
- what is now real
- what is still placeholder-only
- blockers
- confidence score
- whether the next session is safe

### B. Did it give the required self-audit?

Every session should end with:

- `Passed`
- `Failed`
- `Fix Before Next Prompt`
- confidence score
- whether the next session is safe to run

If this is missing, the session is incomplete.

### C. Did it actually edit the files the session was supposed to change?

Do not trust summary language alone.

Check whether the expected files were really touched.

Examples:

- Session 01 should change Databricks Gold / quality files
- Session 02 should change backend routers / services / schemas
- Session 03 should change frontend Priority Board files

If the right files were not changed, the session probably drifted.

### D. Did it leave placeholders behind in the area it claimed to complete?

Look for obvious signs like:

- `TODO`
- `placeholder`
- `"skeleton"`
- mocked static return values
- empty arrays being used as fake evidence

If the session claims completion but still leaves these in the target area, stop and correct it.

### E. Did it create real logic, or just nicer scaffolding?

Ask yourself:

- is this now actually usable by the next layer?
- or does it only look more complete?

This matters a lot in ClubOS because the risk is dressing up weak logic.

## 4. When To Continue To The Next Prompt

Continue only if all of these are true:

- the session updated `project_execution_memory.md`
- the self-audit is present
- the expected files were actually changed
- the session says the next prompt is safe
- you do not see an obvious contradiction between what it claims and what exists in the repo

If all five are true, move to the next prompt.

## 5. When To Stop And Not Continue

Stop if any of these happens:

- the agent says there is a blocker
- the self-audit says the next session is not safe
- the target files are still mostly placeholders
- the logic is still clearly wrong or unsupported
- the agent worked in the wrong folders
- the agent widened scope instead of finishing the assigned session

If this happens, do not move on.

Either:

1. ask the same agent to correct the session, or
2. use a corrective prompt before continuing

## 6. What To Do If The Agent Asks You For Something

Sometimes the agent may need:

- a manual file check
- a Databricks assumption confirmed
- a dependency installed
- a command run in your local environment

If that happens:

1. do the requested step
2. tell the agent exactly what you did
3. ask it to resume the same session

Do not jump to the next prompt until the same session is properly closed.

## 7. Practical Rule For This Project

The project should always move in this order:

**trustworthy Gold logic -> real backend contracts -> real frontend screens -> testing -> demo hardening**

If you ever feel the work is drifting into:

- too much polish
- too many screens
- too much AI
- too much speculative logic

pause and return to the current session goal.

## 8. Fast Checklist Before Running The Next Prompt

Before moving on, ask:

1. Is the session genuinely complete?
2. Is the shared memory updated?
3. Is the next session explicitly marked safe?
4. Are the target files actually real now?
5. Are we still aligned with the MVP, not drifting into extras?

If the answer is yes to all five, continue.

If not, stop and fix.

## 9. Short Operator Script

If you want the shortest possible workflow, use this:

### Before a session

- open `agent_prompt_sequence.md`
- open `project_execution_memory.md`
- copy the next prompt
- paste it into Claude/Codex with the standard wrapper

### After a session

- read the self-audit
- inspect the changed files
- inspect `project_execution_memory.md`
- decide: continue or stop

## 10. Final Principle

Do not reward motion.

Reward only this:

**more trusted logic, more real product behavior, fewer placeholders, clearer readiness for the next layer**
