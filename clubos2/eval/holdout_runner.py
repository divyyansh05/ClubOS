from __future__ import annotations
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


async def run_holdout_eval(scout_prompt_version: str | None = None) -> Path:
    """Run all holdout questions through the same scoring pipeline as the visible set.

    Output is written to eval/reports/holdout/holdout_{timestamp}.md and a JSON sidecar.

    CRITICAL: this function is NOT called by `make v2-eval`. Run ONLY at phase boundaries
    via `make v2-eval-holdout`.
    """
    from eval.golden.loader import load_holdout_set
    from clubos2.eval.pipeline import run_full_eval

    if scout_prompt_version is None:
        from clubos2.gateway.client import GatewaySettings
        scout_prompt_version = GatewaySettings().scout_prompt_version
        logger.info(f"Eval pipeline using scout_prompt_version={scout_prompt_version}")

    holdout = load_holdout_set()
    logger.info(f"Running holdout eval on {len(holdout.entries)} questions")

    # Run the same pipeline but pass the holdout set
    # The pipeline accepts a golden_version argument; we use a temporary approach:
    # write holdout entries as a temp golden set file for the pipeline
    # OR refactor pipeline to accept a GoldenSet directly.
    # Here we use the simpler approach: run entry by entry.

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("eval/reports/holdout")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"holdout_{timestamp}.md"
    json_path = output_dir / f"holdout_{timestamp}.json"

    results = {
        "timestamp": timestamp,
        "total": len(holdout.entries),
        "entries": [],
    }

    for entry in holdout.entries:
        try:
            result = await _score_holdout_entry(entry, scout_prompt_version)
            results["entries"].append(result)
        except Exception as e:
            logger.error(f"Error scoring holdout entry {entry.id}: {e}")
            results["entries"].append({"id": entry.id, "error": str(e)})

    json_path.write_text(json.dumps(results, indent=2, default=str))

    # Write markdown report
    lines = [
        f"# Holdout Eval Report — {timestamp}",
        f"\nTotal: {len(holdout.entries)} questions",
        "\n## Results by entry\n",
    ]
    for r in results["entries"]:
        if "error" in r:
            lines.append(f"- **{r['id']}**: ERROR — {r['error']}")
        else:
            lines.append(f"- **{r['id']}** ({r.get('type', '?')}): {r.get('status', '?')}")

    output_path.write_text("\n".join(lines))
    logger.info(f"Holdout report: {output_path}")
    return output_path


async def _score_holdout_entry(entry, scout_prompt_version: str) -> dict:
    """Score a single holdout entry based on its type."""
    from eval.golden.schema import QuestionType

    if entry.question_type == QuestionType.INVESTIGATION:
        from clubos2.eval.investigator_scorer import run_investigation_scenario
        result = await run_investigation_scenario(entry)
        return {
            "id": entry.id,
            "type": "investigation",
            "status": "pass" if result.overall_pass else "fail",
            "facts_satisfied": result.facts_satisfied,
            "facts_failed": result.facts_failed,
        }
    else:
        # Non-investigation: run Scout and do basic checking
        try:
            from clubos2.agents.scout import run_scout
            from clubos2.agents.scout_schemas import ScoutInput
            answer = await run_scout(ScoutInput(question=entry.question))
            return {
                "id": entry.id,
                "type": entry.question_type.value,
                "status": "answered",
                "answer_length": len(answer.answer),
                "num_citations": len(answer.citations),
            }
        except Exception as e:
            return {"id": entry.id, "type": entry.question_type.value, "status": "error", "error": str(e)}


def compare_visible_vs_holdout(
    visible_report_json: dict,
    holdout_report_json: dict,
) -> dict:
    """Compare key metrics between visible and holdout runs.

    Returns delta dict. Positive delta = visible scored better than holdout (watch for overfitting).
    """
    vis_total = visible_report_json.get("total", 0)
    hold_total = holdout_report_json.get("total", 0)

    vis_pass = sum(1 for e in visible_report_json.get("entries", []) if e.get("status") == "pass")
    hold_pass = sum(1 for e in holdout_report_json.get("entries", []) if e.get("status") == "pass")

    vis_pass_rate = vis_pass / vis_total if vis_total else 0
    hold_pass_rate = hold_pass / hold_total if hold_total else 0
    delta = vis_pass_rate - hold_pass_rate

    warnings = []
    if delta > 0.10:
        warnings.append(
            f"Overfitting signal: visible pass rate {vis_pass_rate:.2f} vs holdout "
            f"{hold_pass_rate:.2f} (delta={delta:.2f} > 0.10)"
        )

    return {
        "visible_pass_rate": vis_pass_rate,
        "holdout_pass_rate": hold_pass_rate,
        "delta": delta,
        "warnings": warnings,
    }
