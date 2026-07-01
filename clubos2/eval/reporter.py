from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from clubos2.eval.behavioural_scorer import BehaviouralScore, aggregate_behaviour
from clubos2.eval.fabrication_scorer import FabricationScore, aggregate_fabrication
from clubos2.eval.ragas_scorer import RagasScores
from clubos2.eval.runner import EvalRun
from eval.golden.schema import GoldenSet

logger = logging.getLogger("clubos.eval.reporter")


class EvalReport(BaseModel):
    run_id: str
    timestamp: str
    golden_set_version: str
    scout_prompt_version: str
    total_questions: int
    total_errors: int

    # Aggregates
    ragas_avg_faithfulness: float | None = None
    ragas_avg_context_relevance: float | None = None
    ragas_avg_answer_relevance: float | None = None
    fabrication_summary: dict
    behavioural_summary: dict

    # Per-entry details
    per_entry: list[dict]


def generate_report(
    eval_run: EvalRun,
    ragas: list[RagasScores] | None,
    fabrication: list[FabricationScore],
    behavioural: list[BehaviouralScore],
    golden_set: GoldenSet,
) -> EvalReport:
    """Combine all scores into a single report object."""
    fab_summary = aggregate_fabrication(fabrication)
    behav_summary = aggregate_behaviour(behavioural)

    # RAGAS averages (None when skipped or all entries unanswerable)
    if ragas is not None:
        faith_vals = [s.faithfulness for s in ragas if s.faithfulness is not None]
        ctx_vals = [s.context_relevance for s in ragas if s.context_relevance is not None]
        ans_vals = [s.answer_relevance for s in ragas if s.answer_relevance is not None]
        ragas_avg_faith = sum(faith_vals) / len(faith_vals) if faith_vals else None
        ragas_avg_ctx = sum(ctx_vals) / len(ctx_vals) if ctx_vals else None
        ragas_avg_ans = sum(ans_vals) / len(ans_vals) if ans_vals else None
    else:
        ragas_avg_faith = ragas_avg_ctx = ragas_avg_ans = None

    # Build per-entry details
    ragas_by_id = {s.entry_id: s for s in ragas} if ragas is not None else {}
    fab_by_id = {s.entry_id: s for s in fabrication}
    behav_by_id = {s.entry_id: s for s in behavioural}
    golden_by_id = {e.id: e for e in golden_set.entries}

    per_entry = []
    for result in eval_run.results:
        eid = result.entry_id
        r_score = ragas_by_id.get(eid)
        f_score = fab_by_id.get(eid)
        b_score = behav_by_id.get(eid)
        entry = golden_by_id.get(eid)

        overall_pass = (b_score.overall_pass if b_score else False) and (
            not (f_score.has_fabrication if f_score else False)
        )

        per_entry.append({
            "entry_id": eid,
            "question": result.question,
            "question_type": result.question_type,
            "overall_pass": overall_pass,
            "answer_preview": (result.scout_answer.answer[:200] if result.scout_answer else "[ERROR]"),
            "trace_url": result.trace_url,
            "ragas": {
                "faithfulness": r_score.faithfulness if r_score else None,
                "context_relevance": r_score.context_relevance if r_score else None,
                "answer_relevance": r_score.answer_relevance if r_score else None,
                "error": r_score.error if r_score else None,
            },
            "fabrication": {
                "has_fabrication": f_score.has_fabrication if f_score else None,
                "fabricated_numbers": f_score.fabricated_numbers if f_score else [],
                "fabricated_rate": f_score.fabricated_rate if f_score else None,
            },
            "behavioural": {
                "overall_pass": b_score.overall_pass if b_score else None,
                "failures": b_score.failures if b_score else [],
            },
            "error": result.error,
        })

    return EvalReport(
        run_id=eval_run.run_id,
        timestamp=eval_run.timestamp,
        golden_set_version=eval_run.golden_set_version,
        scout_prompt_version=eval_run.scout_prompt_version,
        total_questions=len(eval_run.results),
        total_errors=eval_run.total_errors,
        ragas_avg_faithfulness=ragas_avg_faith,
        ragas_avg_context_relevance=ragas_avg_ctx,
        ragas_avg_answer_relevance=ragas_avg_ans,
        fabrication_summary=fab_summary,
        behavioural_summary=behav_summary,
        per_entry=per_entry,
    )


def render_markdown(report: EvalReport, output_path: Path) -> None:
    """Write a markdown report readable by a stakeholder."""

    def _fmt(val: float | None) -> str:
        return f"{val:.2f}" if val is not None else "N/A"

    def _pass_icon(passed: bool) -> str:
        return "PASS" if passed else "FAIL"

    lines = [
        "# ClubOS 2.0 — Eval Report",
        f"**Run:** {report.run_id}  ",
        f"**Date:** {report.timestamp}  ",
        f"**Golden set:** {report.golden_set_version} ({report.total_questions} questions)  ",
        f"**Scout prompt:** {report.scout_prompt_version}  ",
        "",
        "## Headline metrics",
        "",
        "| Metric | Value | Target |",
        "|---|---|---|",
        f"| Fabrication incidence | {report.fabrication_summary.get('entries_with_fabrication', 'N/A')} / {report.total_questions} | 0 / {report.total_questions} |",
        f"| Behavioural pass rate | {report.behavioural_summary.get('overall_pass_rate', 0):.1%} | 95%+ |",
        f"| RAGAS faithfulness (avg) | {_fmt(report.ragas_avg_faithfulness) if report.ragas_avg_faithfulness is not None else 'N/A (not run — see DOCS/eval_methodology.md)'} | >0.85 |",
        f"| RAGAS context relevance (avg) | {_fmt(report.ragas_avg_context_relevance) if report.ragas_avg_context_relevance is not None else 'N/A (not run — see DOCS/eval_methodology.md)'} | >0.75 |",
        f"| RAGAS answer relevance (avg) | {_fmt(report.ragas_avg_answer_relevance) if report.ragas_avg_answer_relevance is not None else 'N/A (not run — see DOCS/eval_methodology.md)'} | >0.80 |",
        f"| Total errors | {report.total_errors} | 0 |",
        "",
        "## Headline verdict",
        "",
    ]

    # Auto-generate verdict
    fab_count = report.fabrication_summary.get('entries_with_fabrication', 0)
    behav_rate = report.behavioural_summary.get('overall_pass_rate', 0)
    errors = report.total_errors

    ragas_skipped = (
        report.ragas_avg_faithfulness is None
        and report.ragas_avg_context_relevance is None
        and report.ragas_avg_answer_relevance is None
    )
    ragas_note = (
        "RAGAS layer was skipped for this run. Deterministic layers are the gate. "
        "See DOCS/eval_methodology.md."
        if ragas_skipped else ""
    )

    if fab_count == 0 and behav_rate >= 0.95 and errors == 0:
        verdict = (
            f"Phase 2 baseline established. Scout achieves zero fabrication on "
            f"{report.total_questions}/{report.total_questions} questions. "
            f"Behavioural compliance is {behav_rate:.0%}. "
            + (ragas_note if ragas_skipped else "RAGAS scores are within target.")
            + " Safe to proceed to Phase 3."
        )
    elif fab_count == 0:
        verdict = (
            f"Zero fabrication across all {report.total_questions} questions — the hard guarantee holds. "
            f"Behavioural pass rate is {behav_rate:.0%} "
            f"({'above' if behav_rate >= 0.95 else 'below'} 95% target). "
            f"{errors} errors. "
            + (ragas_note + " " if ragas_skipped else "")
            + "Review per-question failures before promoting to Phase 3."
        )
    else:
        verdict = (
            f"Fabrication detected in {fab_count}/{report.total_questions} entries — "
            "do NOT proceed to Phase 3 until all fabrication cases are investigated and resolved. "
            f"Behavioural pass rate: {behav_rate:.0%}. Errors: {errors}. "
            + (ragas_note + " " if ragas_skipped else "")
            + "Check per-question breakdown for details."
        )

    lines.append(verdict)
    lines.append("")
    lines.append("## Per-question breakdown")
    lines.append("")

    # Sort by question_type then by entry_id
    sorted_entries = sorted(report.per_entry, key=lambda e: (e["question_type"], e["entry_id"]))

    for e in sorted_entries:
        pass_label = _pass_icon(e["overall_pass"])
        qt = e["question_type"].upper()
        lines += [
            f"### {e['entry_id']} — {qt} — {pass_label}",
            f"**Question:** {e['question']}",
            f"**Scout answer:** {e['answer_preview']}{'...' if len(e.get('answer_preview', '')) == 200 else ''}",
            "**Scores:**",
            f"- Fabrication: {len(e['fabrication']['fabricated_numbers'])} fabricated numbers"
            + (f": {e['fabrication']['fabricated_numbers']}" if e['fabrication']['fabricated_numbers'] else ""),
            f"- Behavioural: {'passed' if e['behavioural']['overall_pass'] else 'failed — ' + '; '.join(e['behavioural']['failures'])}",
        ]
        ragas = e["ragas"]
        if ragas["faithfulness"] is not None:
            lines.append(
                f"- RAGAS: faithfulness={_fmt(ragas['faithfulness'])}, "
                f"context_relevance={_fmt(ragas['context_relevance'])}, "
                f"answer_relevance={_fmt(ragas['answer_relevance'])}"
            )
        else:
            lines.append("- RAGAS: N/A (UNANSWERABLE or error)")
        if e["trace_url"]:
            lines.append(f"**Trace:** {e['trace_url']}")
        if e["error"]:
            lines.append(f"**Error:** {e['error']}")
        lines.append("")

    # Failure summary
    failures = [e for e in report.per_entry if not e["overall_pass"]]
    lines += ["## Failure summary", ""]
    if failures:
        for f in failures:
            reasons = f["behavioural"]["failures"] + (
                [f"Fabrication: {f['fabrication']['fabricated_numbers']}"] if f["fabrication"]["has_fabrication"] else []
            )
            lines.append(f"- **{f['entry_id']}**: {'; '.join(reasons) or 'Unknown failure'}")
    else:
        lines.append("No failures.")
    lines.append("")

    # Recommendations
    lines += ["## Recommendations", ""]
    if fab_count > 0:
        lines.append(f"- **Fix fabrication ({fab_count} entries):** Investigate each flagged number before Phase 3.")
    mixed_fails = [e for e in report.per_entry if e["question_type"] == "mixed" and not e["overall_pass"]]
    if mixed_fails:
        lines.append(f"- **MIXED question citation gap ({len(mixed_fails)} entries):** Scout may not be combining metric + skill citations.")
    if behav_rate < 0.95:
        lines.append(f"- **Behavioural pass rate {behav_rate:.0%} below 95% target:** Review citation and refusal compliance.")
    if errors > 0:
        lines.append(f"- **{errors} runner errors:** Investigate Scout failures in the run JSON.")
    if not any([fab_count > 0, mixed_fails, behav_rate < 0.95, errors > 0]):
        lines.append("All metrics on target. Proceed to Phase 3.")

    lines += [
        "",
        "---",
        f"*Generated {report.timestamp}. Eval methodology: deterministic fabricated-number rate + behavioural compliance"
        + (" (RAGAS skipped — see DOCS/eval_methodology.md)." if ragas_skipped else " + RAGAS faithfulness/context-relevance/answer-relevance.")
        + "*",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"Report written to {output_path}")


if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="Generate ClubOS 2.0 eval report from a run JSON")
    parser.add_argument("--run-id", required=True, help="Run ID (filename without .json in eval/runs/)")
    args = parser.parse_args()

    run_path = Path(f"eval/runs/{args.run_id}.json")
    if not run_path.exists():
        raise FileNotFoundError(f"Run not found: {run_path}")

    eval_run = EvalRun.model_validate_json(run_path.read_text())
    print(f"Loaded run: {eval_run.run_id}, {len(eval_run.results)} results")
