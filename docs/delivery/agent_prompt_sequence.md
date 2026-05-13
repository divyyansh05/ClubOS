# ClubOS Agent Prompt Sequence

Use these prompts in order.

Do not skip ahead unless the prior prompt explicitly concludes that the next phase is safe.

## Sequence

1. `docs/delivery/agent_prompts/01_session_gold_trust_closure.md`
2. `docs/delivery/agent_prompts/02_session_backend_core_contracts.md`
3. `docs/delivery/agent_prompts/03_session_frontend_priority_board_vertical_slice.md`
4. `docs/delivery/agent_prompts/04_session_frontend_core_mvp_screens.md`
5. `docs/delivery/agent_prompts/05_session_monthly_briefing_layer.md`
6. `docs/delivery/agent_prompts/06_session_quality_and_regression.md`
7. `docs/delivery/agent_prompts/07_session_demo_and_submission_hardening.md`
8. `docs/delivery/agent_prompts/08_final_delivery_audit.md`

## Global Rule

Every session must:

- read `AGENTS.md`
- read `REPO_STRUCTURE.md`
- read `docs/delivery/project_execution_memory.md`
- update `docs/delivery/project_execution_memory.md` before finishing
- update a relevant agent role file only if the session materially changes responsibilities, dependencies, or workflow expectations
- end with a hard self-audit:
  - `Passed`
  - `Failed`
  - `Fix Before Next Prompt`

## Stop Condition

If a prompt cannot be completed because of a genuine blocker, the agent must:

- stop immediately
- explain the blocker clearly
- say exactly what the user must do
- update `docs/delivery/project_execution_memory.md`
- not pretend the session is complete
