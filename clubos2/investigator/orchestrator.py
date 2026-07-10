from __future__ import annotations
import json
import logging
import time
from datetime import timedelta
from uuid import uuid4

from pydantic import BaseModel

from clubos2.investigator.agent_schemas import (
    InvestigationConfidence,
    InvestigatorFinding,
    InvestigatorInput,
)
from clubos2.investigator.checkpointer import get_checkpointer
from clubos2.investigator.graph import build_graph
from clubos2.investigator.repo import InvestigationRepository
from clubos2.investigator.state import InvestigatorState
from clubos2.observability.tracing import traced, get_current_langsmith_trace_url
from clubos2.watchdog.alerts_repo import AlertsRepository
from clubos2.watchdog.memory_repo import AgentMemoryRepository

logger = logging.getLogger(__name__)


class InvestigationRunResult(BaseModel):
    investigation_id: str
    alert_id: str
    metric_name: str
    status: str  # 'completed' | 'failed' | 'timeout'
    finding: InvestigatorFinding | None
    latency_seconds: float
    total_tokens: int | None = None
    cost_usd: float | None = None
    trace_url: str | None = None
    error: str | None = None


@traced(name="investigator:run", run_type="chain")
async def run_investigation(input: InvestigatorInput) -> InvestigationRunResult:
    """Run one investigation end-to-end.

    Pipeline:
    1. Verify the alert exists
    2. Create investigations row with status='running'
    3. Build LangGraph with SqliteSaver checkpointer
    4. Run the graph
    5. Parse the final finding
    6. Persist to investigations table and LTM memory
    7. Return InvestigationRunResult
    """
    started_at = time.perf_counter()

    investigations_repo = InvestigationRepository()
    memory_repo = AgentMemoryRepository()

    # 1. Verify alert exists
    alerts_repo = AlertsRepository()
    alert = None
    try:
        alert = await alerts_repo.get_by_id(input.alert_id)
    except Exception as e:
        logger.warning(f"Could not fetch alert {input.alert_id}: {e}")

    if alert is None:
        return InvestigationRunResult(
            investigation_id=f"inv_{uuid4().hex[:16]}",
            alert_id=input.alert_id,
            metric_name=input.metric_name,
            status="failed",
            finding=None,
            latency_seconds=0.0,
            error=f"Alert {input.alert_id} not found",
        )

    # 2. Start the investigation row
    investigation = await investigations_repo.start(
        alert_id=input.alert_id,
        metric_name=input.metric_name,
        triggered_by=input.triggered_by,
    )
    investigation_id = investigation.investigation_id

    # 3–4. Build graph with async checkpointer and run
    initial_state: InvestigatorState = {
        "alert_id": input.alert_id,
        "metric_name": input.metric_name,
        "triggered_by": input.triggered_by,
        "max_steps": input.max_steps,
        "messages": [],
        "step_count": 0,
        "tools_called": [],
        "reasoning_trace": [],
        "finding": None,
        "finished": False,
    }
    config = {"configurable": {"thread_id": investigation_id}}

    try:
        async with get_checkpointer() as checkpointer:
            graph = build_graph(checkpointer=checkpointer)
            final_state = await graph.ainvoke(initial_state, config=config)
    except Exception as e:
        latency = time.perf_counter() - started_at
        logger.exception(f"Investigation {investigation_id} crashed")
        await investigations_repo.fail(
            investigation_id=investigation_id,
            error_message=str(e),
            latency_seconds=latency,
        )
        return InvestigationRunResult(
            investigation_id=investigation_id,
            alert_id=input.alert_id,
            metric_name=input.metric_name,
            status="failed",
            finding=None,
            latency_seconds=latency,
            error=str(e),
        )

    latency = time.perf_counter() - started_at

    # 5. Parse the final finding from the last AIMessage
    last_message = final_state["messages"][-1] if final_state["messages"] else None
    if not last_message:
        await investigations_repo.fail(
            investigation_id=investigation_id,
            error_message="No final message from agent",
            latency_seconds=latency,
            partial_reasoning_trace=final_state.get("reasoning_trace", []),
        )
        return InvestigationRunResult(
            investigation_id=investigation_id,
            alert_id=input.alert_id,
            metric_name=input.metric_name,
            status="failed",
            finding=None,
            latency_seconds=latency,
            error="No final message",
        )

    finding: InvestigatorFinding | None = None
    parse_error: str | None = None
    try:
        content = last_message.content if isinstance(last_message.content, str) else ""
        # Strip markdown fences if the LLM added them despite instructions
        if "```" in content:
            parts = content.split("```")
            if len(parts) >= 2:
                content = parts[1]
                if content.startswith("json"):
                    content = content[4:].strip()
                content = content.split("```")[0].strip()

        parsed = json.loads(content)
        parsed.setdefault("alert_id", input.alert_id)
        parsed.setdefault("metric_name", input.metric_name)
        # Inject reasoning_trace and tools_called from graph state
        parsed["reasoning_trace"] = final_state.get("reasoning_trace", [])
        parsed["tools_called"] = final_state.get("tools_called", [])
        parsed["total_steps"] = final_state.get("step_count", 0)

        finding = InvestigatorFinding.model_validate(parsed)
    except Exception as e:
        parse_error = f"Failed to parse final finding: {e}"
        logger.warning(parse_error)

    if finding is None:
        status = "timeout" if final_state.get("step_count", 0) >= input.max_steps else "failed"
        await investigations_repo.fail(
            investigation_id=investigation_id,
            error_message=parse_error or "Unknown failure",
            latency_seconds=latency,
            partial_reasoning_trace=final_state.get("reasoning_trace", []),
        )
        return InvestigationRunResult(
            investigation_id=investigation_id,
            alert_id=input.alert_id,
            metric_name=input.metric_name,
            status=status,
            finding=None,
            latency_seconds=latency,
            error=parse_error,
        )

    # 6. Persist the finding
    trace_url = get_current_langsmith_trace_url()
    await investigations_repo.complete(
        investigation_id=investigation_id,
        cause_hypothesis=finding.cause_hypothesis,
        confidence=finding.confidence.value,
        evidence_summary=finding.evidence_summary,
        citations=finding.citations,
        reasoning_trace=[
            step.model_dump() if hasattr(step, "model_dump") else step
            for step in finding.reasoning_trace
        ],
        tools_called=finding.tools_called,
        total_steps=finding.total_steps,
        total_tokens=None,
        cost_usd=None,
        latency_seconds=latency,
        trace_url=trace_url,
    )

    # 7. Record LTM memory for Phase 5 Briefer
    try:
        await memory_repo.remember(
            agent_name="investigator",
            memory_type="investigation_concluded",
            subject_key=f"{input.metric_name}::{input.alert_id}",
            subject_metadata={
                "investigation_id": investigation_id,
                "cause_hypothesis": finding.cause_hypothesis,
                "confidence": finding.confidence.value,
                "is_seasonal_or_expected": finding.is_seasonal_or_expected,
            },
            ttl=timedelta(days=90),
            confidence=1.0 if finding.confidence == InvestigationConfidence.HIGH else (
                0.7 if finding.confidence == InvestigationConfidence.MEDIUM else 0.4
            ),
        )
    except Exception as e:
        logger.warning(f"Failed to record LTM memory: {e}")

    return InvestigationRunResult(
        investigation_id=investigation_id,
        alert_id=input.alert_id,
        metric_name=input.metric_name,
        status="completed",
        finding=finding,
        latency_seconds=latency,
        trace_url=trace_url,
    )
