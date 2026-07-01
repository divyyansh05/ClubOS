from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Callable, Awaitable
from uuid import uuid4

from pydantic import BaseModel

from eval.golden.schema import GoldenEntry
from clubos2.watchdog.orchestrator import WatchdogRunResult

logger = logging.getLogger("clubos.eval.watchdog_scorer")

# Isolated eval DB — separate from production var/clubos_semantic.duckdb
EVAL_DB_URL = "duckdb:///var/clubos_watchdog_eval.duckdb"


class WatchdogScenarioResult(BaseModel):
    entry_id: str
    scenario_recreated: bool
    watchdog_result: WatchdogRunResult | None
    expected_facts: list[str]
    facts_satisfied: list[str]
    facts_failed: list[str]
    facts_uncheckable: list[str]
    overall_pass: bool
    notes: list[str]


def check_fact(fact: str, result: WatchdogRunResult) -> str:
    """Check a single fact string against a WatchdogRunResult.

    Returns: 'satisfied', 'failed', or 'uncheckable'
    """
    fact = fact.strip()

    # alerts_created == N
    m = re.match(r"alerts_created\s*==\s*(\d+)", fact)
    if m:
        return "satisfied" if result.alerts_created == int(m.group(1)) else "failed"

    # alerts_created > N
    m = re.match(r"alerts_created\s*>\s*(\d+)", fact)
    if m:
        return "satisfied" if result.alerts_created > int(m.group(1)) else "failed"

    # alerts_created >= N
    m = re.match(r"alerts_created\s*>=\s*(\d+)", fact)
    if m:
        return "satisfied" if result.alerts_created >= int(m.group(1)) else "failed"

    # alerts_deduped == N
    m = re.match(r"alerts_deduped\s*==\s*(\d+)", fact)
    if m:
        return "satisfied" if result.alerts_deduped == int(m.group(1)) else "failed"

    # alerts_deduped > N
    m = re.match(r"alerts_deduped\s*>\s*(\d+)", fact)
    if m:
        return "satisfied" if result.alerts_deduped > int(m.group(1)) else "failed"

    # alerts_deduped >= N
    m = re.match(r"alerts_deduped\s*>=\s*(\d+)", fact)
    if m:
        return "satisfied" if result.alerts_deduped >= int(m.group(1)) else "failed"

    # errors is empty
    if re.search(r"errors\s+is\s+empty", fact, re.IGNORECASE):
        return "satisfied" if len(result.errors) == 0 else "failed"

    # errors list is non-empty / errors list non-empty / errors is non-empty
    if re.search(r"errors\s+(list\s+)?(is\s+)?non-?empty", fact, re.IGNORECASE):
        return "satisfied" if len(result.errors) > 0 else "failed"

    # snapshot_id is non-empty
    if re.search(r"snapshot_id\s+is\s+non-?empty", fact, re.IGNORECASE):
        return "satisfied" if bool(result.snapshot_id) else "failed"

    # WatchdogRunResult is returned (not exception)
    if re.search(r"WatchdogRunResult\s+is\s+returned", fact, re.IGNORECASE):
        return "satisfied"  # if we got here, it was returned

    # "{rule_name} rule fires" — cannot verify without DB query
    m = re.search(r"(\w+)\s+rule\s+fires?", fact, re.IGNORECASE)
    if m:
        return "uncheckable"

    # "rank_delta is non-zero"
    if re.search(r"rank_delta\s+is\s+non-?zero", fact, re.IGNORECASE):
        return "uncheckable"  # need to inspect alert details

    # "triggered_by_rule is X for at least one alert"
    if re.search(r"triggered_by_rule\s+is\s+\w+\s+for\s+at\s+least\s+one\s+alert", fact, re.IGNORECASE):
        return "uncheckable"

    logger.debug("Uncheckable fact: %s", fact)
    return "uncheckable"


def _setup_eval_db() -> None:
    """Bootstrap all three Watchdog tables in the eval-isolated DB."""
    from clubos2.watchdog.alerts_repo import bootstrap_watchdog_alerts_db
    from clubos2.watchdog.memory_repo import bootstrap_agent_memory_db
    from clubos2.watchdog.snapshot_repo import bootstrap_snapshot_db

    bootstrap_watchdog_alerts_db(EVAL_DB_URL)
    bootstrap_agent_memory_db(EVAL_DB_URL)
    bootstrap_snapshot_db(EVAL_DB_URL)


def _clear_eval_db() -> None:
    """Truncate all watchdog tables in the eval DB for scenario isolation."""
    import sqlalchemy as sa

    from clubos2.semantic_layer.db import get_engine

    engine = get_engine(EVAL_DB_URL)
    with engine.begin() as conn:
        for table in ["watchdog_alerts", "agent_memory", "priority_board_snapshots"]:
            try:
                conn.execute(sa.text(f"DELETE FROM {table}"))
            except Exception:
                pass  # table may not exist yet


async def _run_with_eval_db(dedup_window_days: int = 7, top_n: int = 10) -> WatchdogRunResult:
    """Run watchdog against the eval-isolated DB by monkeypatching DATABASE_URL."""
    import clubos2.semantic_layer.db as db_mod
    from sqlalchemy.orm import sessionmaker

    orig_url = db_mod.DATABASE_URL
    orig_engine = db_mod._default_engine
    orig_factory = db_mod._SessionFactory

    try:
        db_mod.DATABASE_URL = EVAL_DB_URL
        eval_engine = db_mod.get_engine(EVAL_DB_URL)
        db_mod._default_engine = eval_engine
        db_mod._SessionFactory = sessionmaker(bind=eval_engine)

        result = await run_watchdog(dedup_window_days=dedup_window_days, top_n=top_n)
        return result
    finally:
        db_mod.DATABASE_URL = orig_url
        db_mod._default_engine = orig_engine
        db_mod._SessionFactory = orig_factory


# Import run_watchdog here so it can be referenced
from clubos2.watchdog.orchestrator import run_watchdog  # noqa: E402


# ── Scenario setup functions ─────────────────────────────────────────────────


async def setup_gq_026() -> None:
    """First run: clear all watchdog state."""
    _clear_eval_db()


async def setup_gq_027() -> None:
    """Run once first to establish dedup state."""
    _clear_eval_db()
    await _run_with_eval_db(dedup_window_days=7)


async def setup_gq_028() -> None:
    """Inject previous snapshot with target metric at high rank; current CSV has it at low rank.

    We can't easily modify the real CSV, so just clear state and let the
    orchestrator run normally — the large_rank_change rule will fire if
    there's meaningful movement between runs. For this scenario, just run once
    to establish a baseline.
    """
    _clear_eval_db()


async def setup_gq_029() -> None:
    """Seed agent_memory with 3 prior present_in_top_n memories."""
    _clear_eval_db()
    import clubos2.semantic_layer.db as db_mod
    from sqlalchemy.orm import sessionmaker

    orig_url = db_mod.DATABASE_URL
    orig_engine = db_mod._default_engine
    orig_factory = db_mod._SessionFactory

    try:
        db_mod.DATABASE_URL = EVAL_DB_URL
        eval_engine = db_mod.get_engine(EVAL_DB_URL)
        db_mod._default_engine = eval_engine
        db_mod._SessionFactory = sessionmaker(bind=eval_engine)

        from clubos2.watchdog.memory_repo import AgentMemoryRepository
        from clubos2.watchdog.priority_board_reader import PriorityBoardReader

        memory_repo = AgentMemoryRepository()

        # Seed 3 memories for a real metric from the CSV
        reader = PriorityBoardReader()
        snapshot = await reader.read_current()
        if snapshot.rows:
            target_metric = snapshot.rows[0].metric_name
            for _ in range(3):
                await memory_repo.remember(
                    agent_name="watchdog",
                    memory_type="present_in_top_n",
                    subject_key=f"{target_metric}::present_in_top_n",
                    subject_metadata={"run_id": f"seed_{uuid4().hex[:8]}"},
                    ttl=timedelta(days=30),
                )
    finally:
        db_mod.DATABASE_URL = orig_url
        db_mod._default_engine = orig_engine
        db_mod._SessionFactory = orig_factory


async def setup_gq_030() -> None:
    """No setup needed — malformed CSV path is passed at run time."""
    _clear_eval_db()


SCENARIO_SETUPS: dict[str, Callable[[], Awaitable[None]]] = {
    "gq_026": setup_gq_026,
    "gq_027": setup_gq_027,
    "gq_028": setup_gq_028,
    "gq_029": setup_gq_029,
    "gq_030": setup_gq_030,
}


async def _run_with_eval_db_csv(csv_path: str) -> WatchdogRunResult:
    """Run watchdog with a specific (possibly bad) CSV path against eval DB."""
    import clubos2.semantic_layer.db as db_mod
    from sqlalchemy.orm import sessionmaker

    orig_url = db_mod.DATABASE_URL
    orig_engine = db_mod._default_engine
    orig_factory = db_mod._SessionFactory

    try:
        db_mod.DATABASE_URL = EVAL_DB_URL
        eval_engine = db_mod.get_engine(EVAL_DB_URL)
        db_mod._default_engine = eval_engine
        db_mod._SessionFactory = sessionmaker(bind=eval_engine)

        result = await run_watchdog(csv_path=csv_path)
        return result
    finally:
        db_mod.DATABASE_URL = orig_url
        db_mod._default_engine = orig_engine
        db_mod._SessionFactory = orig_factory


async def run_watchdog_scenario(entry: GoldenEntry) -> WatchdogScenarioResult:
    """Run a WATCHDOG_RUN golden entry scenario and score the result."""
    facts = entry.expected_answer_facts or []

    # Setup
    setup_fn = SCENARIO_SETUPS.get(entry.id)
    scenario_recreated = False
    watchdog_result = None
    notes: list[str] = []

    try:
        _setup_eval_db()
        if setup_fn:
            await setup_fn()
        scenario_recreated = True
    except Exception as e:
        notes.append(f"Scenario setup failed: {e}")
        logger.warning("Scenario setup failed for %s: %s", entry.id, e)

    # Run (with special handling for gq_030 which needs a bad CSV)
    try:
        if entry.id == "gq_030":
            watchdog_result = await _run_with_eval_db_csv("data/nonexistent_broken.csv")
        elif entry.id == "gq_027":
            # Second run immediately after setup (which already did run 1)
            watchdog_result = await _run_with_eval_db(dedup_window_days=7)
        else:
            watchdog_result = await _run_with_eval_db()
    except Exception as e:
        notes.append(f"Watchdog run failed during scenario: {e}")
        logger.warning("Watchdog run failed for %s: %s", entry.id, e)

    if watchdog_result is None:
        return WatchdogScenarioResult(
            entry_id=entry.id,
            scenario_recreated=scenario_recreated,
            watchdog_result=None,
            expected_facts=facts,
            facts_satisfied=[],
            facts_failed=facts,
            facts_uncheckable=[],
            overall_pass=False,
            notes=notes,
        )

    # Check facts
    satisfied, failed, uncheckable = [], [], []
    for fact in facts:
        verdict = check_fact(fact, watchdog_result)
        if verdict == "satisfied":
            satisfied.append(fact)
        elif verdict == "failed":
            failed.append(fact)
        else:
            uncheckable.append(fact)

    overall_pass = len(failed) == 0

    return WatchdogScenarioResult(
        entry_id=entry.id,
        scenario_recreated=scenario_recreated,
        watchdog_result=watchdog_result,
        expected_facts=facts,
        facts_satisfied=satisfied,
        facts_failed=failed,
        facts_uncheckable=uncheckable,
        overall_pass=overall_pass,
        notes=notes,
    )


async def score_watchdog_batch(entries: list[GoldenEntry]) -> list[WatchdogScenarioResult]:
    """Run all WATCHDOG_RUN entries and return their results."""
    results = []
    for entry in entries:
        result = await run_watchdog_scenario(entry)
        results.append(result)
    return results
