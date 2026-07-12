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

    def _strip_fences(text: str) -> str:
        if "```" in text:
            parts = text.split("```")
            if len(parts) >= 2:
                inner = parts[1]
                if inner.startswith("json"):
                    inner = inner[4:].strip()
                return inner.split("```")[0].strip()
        return text

    def _extract_json_object(text: str) -> str:
        """Find the first {...} block in text (handles prose + JSON mixed output)."""
        start = text.find("{")
        if start == -1:
            return text
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        return text[start:]

    async def _synthesis_call(context_messages: list, tools_used: list[str]) -> str:
        """Call the LLM without tools to force a structured JSON finding output."""
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage
        from clubos2.gateway.client import GatewaySettings as _GS
        s = _GS()
        llm = ChatOpenAI(model=s.investigator_model, temperature=0, max_tokens=1024, api_key=s.openai_api_key or None)
        tool_ctx = ("Tools used: " + ", ".join(tools_used)) if tools_used else "No tools called."
        msgs = context_messages + [HumanMessage(content=(
            f"{tool_ctx}\n\n"
            f"Summarise your investigation findings as a single raw JSON object.\n"
            f"Output ONLY the JSON — no markdown, no explanation, no fences.\n"
            f"Keys required:\n"
            f"  cause_hypothesis: one sentence explaining the likely cause\n"
            f"  confidence: one of low, medium, high\n"
            f"  evidence_summary: 2-3 sentences of supporting evidence from your tool results\n"
            f"  alert_id: \"{input.alert_id}\"\n"
            f"  metric_name: \"{input.metric_name}\"\n"
            f"  citations: [] (empty list is fine)\n"
            f"  data_gaps: [] (empty list is fine)\n"
            f"Example: {{\"cause_hypothesis\": \"...\", \"confidence\": \"medium\", "
            f"\"evidence_summary\": \"...\", \"alert_id\": \"...\", \"metric_name\": \"...\", "
            f"\"citations\": [], \"data_gaps\": []}}"
        ))]
        resp = await llm.ainvoke(msgs)
        return resp.content if isinstance(resp.content, str) else ""

    content = last_message.content if isinstance(last_message.content, str) else ""
    content = _strip_fences(content)

    try:
        # If the model produced prose or empty content, extract the JSON block if present
        json_content = _extract_json_object(content)
        parsed = json.loads(json_content)
    except Exception:
        # Model didn't produce JSON — force a synthesis call with the full conversation
        logger.warning("Non-JSON final message for %s — running synthesis", investigation_id)
        try:
            synth_content = await _synthesis_call(
                list(final_state["messages"]),
                final_state.get("tools_called", []),
            )
            synth_content = _strip_fences(synth_content)
            json_content = _extract_json_object(synth_content)
            parsed = json.loads(json_content)
        except Exception as synth_err:
            parse_error = f"Synthesis failed: {synth_err}"
            logger.warning(parse_error)
            parsed = None

    if parsed is not None:
        try:
            parsed.setdefault("alert_id", input.alert_id)
            parsed.setdefault("metric_name", input.metric_name)
            parsed.setdefault("citations", [])
            parsed.setdefault("data_gaps", [])
            parsed["reasoning_trace"] = final_state.get("reasoning_trace", [])
            parsed["tools_called"] = final_state.get("tools_called", [])
            parsed["total_steps"] = final_state.get("step_count", 0)
            finding = InvestigatorFinding.model_validate(parsed)
        except Exception as e:
            parse_error = f"Failed to validate finding: {e}"
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
