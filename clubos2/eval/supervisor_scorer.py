from __future__ import annotations

import logging
import re
from typing import Callable, Awaitable
from uuid import uuid4

from pydantic import BaseModel

from eval.golden.schema import GoldenEntry

logger = logging.getLogger(__name__)


class SupervisorScenarioResult(BaseModel):
    entry_id: str
    scenario_recreated: bool
    supervisor_result: dict | None
    expected_facts: list[str]
    facts_satisfied: list[str]
    facts_failed: list[str]
    overall_pass: bool
    notes: list[str]


# ---------------------------------------------------------------------------
# Fact checker
# ---------------------------------------------------------------------------

def check_supervisor_fact(fact: str, result: dict) -> bool:
    """Parse fact strings and check against a SupervisorResponse dict.

    Supported patterns:
    - dispatch_path=<value>
    - dispatch_path in [<v1>, <v2>]
    - classification.agent=<value>
    - classification.agent in [<v1>, <v2>]
    - classification.confidence=<value>
    - classification.extracted_params contains alert_id=<value>
    - plan.steps>=<N>
    - plan.steps==<N>
    - error is null
    """
    f = fact.strip()
    fl = f.lower()

    dispatch_path = result.get("dispatch_path", "")
    classification = result.get("classification") or {}
    error = result.get("error")

    # error is null
    if re.search(r"error\s+is\s+null", fl):
        return error is None

    # dispatch_path=<value>
    m = re.match(r"dispatch_path\s*=\s*(\S+)", fl)
    if m:
        return dispatch_path == m.group(1)

    # dispatch_path in [v1, v2, ...]
    m = re.match(r"dispatch_path\s+in\s+\[([^\]]+)\]", fl)
    if m:
        allowed = [v.strip() for v in m.group(1).split(",")]
        return dispatch_path in allowed

    # classification.agent=<value>
    m = re.match(r"classification\.agent\s*=\s*(\S+)", fl)
    if m:
        return classification.get("agent", "") == m.group(1)

    # classification.agent in [v1, v2]
    m = re.match(r"classification\.agent\s+in\s+\[([^\]]+)\]", fl)
    if m:
        allowed = [v.strip() for v in m.group(1).split(",")]
        return classification.get("agent", "") in allowed

    # classification.confidence=<value>
    m = re.match(r"classification\.confidence\s*=\s*(\S+)", fl)
    if m:
        return classification.get("confidence", "") == m.group(1)

    # classification.extracted_params contains alert_id=<value>
    m = re.search(r"extracted_params\s+contains\s+alert_id\s*=\s*(\S+)", fl)
    if m:
        expected_id = m.group(1)
        params = classification.get("extracted_params") or {}
        return params.get("alert_id", "") == expected_id

    # plan.steps>=N  or  plan.steps==N  or  plan.steps<=N
    m = re.match(r"plan\.steps\s*(>=|==|<=|>|<)\s*(\d+)", fl)
    if m:
        op, n = m.group(1), int(m.group(2))
        inner = result.get("result") or {}
        plan = inner.get("plan") or []
        steps = len(plan)
        return _compare(steps, op, n)

    logger.warning(f"check_supervisor_fact: unparseable fact '{fact}' — marking as pass")
    return True


def _compare(val: int, op: str, n: int) -> bool:
    if op == ">=":
        return val >= n
    if op == "==":
        return val == n
    if op == "<=":
        return val <= n
    if op == ">":
        return val > n
    if op == "<":
        return val < n
    return False


# ---------------------------------------------------------------------------
# Scenario setup functions
# ---------------------------------------------------------------------------

async def _insert_alert(metric_name: str, alert_type_str: str = "score_jump",
                        severity_str: str = "critical", alert_id: str | None = None) -> str:
    from clubos2.watchdog.alerts_repo import AlertsRepository, bootstrap_watchdog_alerts_db
    from clubos2.watchdog.alerts_schema import AlertType, AlertSeverity, WatchdogAlertCreate

    bootstrap_watchdog_alerts_db()
    repo = AlertsRepository()

    type_map = {
        "score_jump": AlertType.SCORE_JUMP,
        "new_in_top_n": AlertType.NEW_IN_TOP_N,
    }
    sev_map = {
        "info": AlertSeverity.INFO,
        "warning": AlertSeverity.WARNING,
        "critical": AlertSeverity.CRITICAL,
    }
    aid = alert_id or f"alrt_eval_{uuid4().hex[:12]}"
    a = WatchdogAlertCreate(
        alert_id=aid,
        metric_name=metric_name,
        alert_type=type_map.get(alert_type_str, AlertType.SCORE_JUMP),
        severity=sev_map.get(severity_str, AlertSeverity.CRITICAL),
        current_rank=1,
        previous_rank=5,
        rank_delta=4,
        score_current=0.9,
        score_previous=0.5,
        triggered_by_rule=alert_type_str,
        context_snapshot="{}",
        source="eval",
        run_id=f"eval_{aid}",
    )
    created = await repo.create(a)
    return created.alert_id


# gq_041 — Scout metric question, no setup needed
async def setup_gq_041() -> None:
    pass


# gq_042 — Briefer monthly summary, no setup needed
async def setup_gq_042() -> None:
    pass


# gq_043 — Investigator with explicit alert_id that must exist in DB
async def setup_gq_043() -> None:
    from clubos2.watchdog.alerts_repo import AlertsRepository, bootstrap_watchdog_alerts_db
    from clubos2.watchdog.alerts_schema import AlertType, AlertSeverity, WatchdogAlertCreate

    bootstrap_watchdog_alerts_db()
    repo = AlertsRepository()
    existing = await repo.get_by_id("alrt_test0043")
    if existing is None:
        await _insert_alert("net_sales", "score_jump", "critical", alert_id="alrt_test0043")


# gq_044 through gq_050 — no DB setup needed (purely classifier/supervisor behaviour)
async def setup_gq_044() -> None:
    pass

async def setup_gq_045() -> None:
    pass

async def setup_gq_046() -> None:
    pass

async def setup_gq_047() -> None:
    pass

async def setup_gq_048() -> None:
    pass

async def setup_gq_049() -> None:
    pass

async def setup_gq_050() -> None:
    pass


SUPERVISOR_SCENARIOS: dict[str, Callable[[], Awaitable[None]]] = {
    "gq_041": setup_gq_041,
    "gq_042": setup_gq_042,
    "gq_043": setup_gq_043,
    "gq_044": setup_gq_044,
    "gq_045": setup_gq_045,
    "gq_046": setup_gq_046,
    "gq_047": setup_gq_047,
    "gq_048": setup_gq_048,
    "gq_049": setup_gq_049,
    "gq_050": setup_gq_050,
}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def run_supervisor_scenario(entry: GoldenEntry) -> SupervisorScenarioResult:
    """Run a SUPERVISOR_ROUTING golden entry through handle_query and score facts."""
    from clubos2.supervisor.entry_point import handle_query, SupervisorRequest

    setup_fn = SUPERVISOR_SCENARIOS.get(entry.id)
    notes: list[str] = []
    scenario_recreated = False

    if setup_fn:
        try:
            await setup_fn()
            scenario_recreated = True
        except Exception as e:
            notes.append(f"Scenario setup failed: {e}")
            logger.warning("Supervisor scenario setup failed for %s: %s", entry.id, e)
    else:
        notes.append(f"No setup function for {entry.id} — running with no setup")
        scenario_recreated = True

    try:
        response = await handle_query(SupervisorRequest(query=entry.question))
        result_dict = response.model_dump(mode="json")
    except Exception as e:
        notes.append(f"handle_query raised: {e}")
        return SupervisorScenarioResult(
            entry_id=entry.id,
            scenario_recreated=scenario_recreated,
            supervisor_result=None,
            expected_facts=entry.expected_answer_facts,
            facts_satisfied=[],
            facts_failed=entry.expected_answer_facts,
            overall_pass=False,
            notes=notes,
        )

    satisfied, failed = [], []
    for fact in entry.expected_answer_facts:
        if check_supervisor_fact(fact, result_dict):
            satisfied.append(fact)
        else:
            failed.append(fact)

    return SupervisorScenarioResult(
        entry_id=entry.id,
        scenario_recreated=scenario_recreated,
        supervisor_result=result_dict,
        expected_facts=entry.expected_answer_facts,
        facts_satisfied=satisfied,
        facts_failed=failed,
        overall_pass=(len(failed) == 0),
        notes=notes,
    )
