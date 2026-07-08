from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from eval.golden.loader import load_golden_set
from eval.golden.schema import QuestionType

logger = logging.getLogger("clubos.eval.pipeline")


async def run_full_eval(
    golden_version: str = "v1",
    scout_prompt_version: str | None = None,
    output_dir: str = "eval/reports",
    skip_ragas: bool = False,
    inter_question_sleep_seconds: float = 2.0,
) -> Path:
    """Orchestrate: runner -> (RAGAS) -> fabrication -> behavioural -> reporter."""
    from clubos2.gateway.client import GatewaySettings
    if scout_prompt_version is None:
        scout_prompt_version = GatewaySettings().scout_prompt_version
    logger.info(f"Eval pipeline using scout_prompt_version={scout_prompt_version}")

    from clubos2.eval.runner import run_eval
    from clubos2.eval.ragas_scorer import score_with_ragas
    from clubos2.eval.fabrication_scorer import score_fabrication_batch
    from clubos2.eval.behavioural_scorer import score_behaviour_batch
    from clubos2.eval.reporter import generate_report, render_markdown

    logger.info(f"Starting full eval: golden={golden_version}, prompt={scout_prompt_version}, skip_ragas={skip_ragas}")

    # Step 1: Run the golden set through Scout
    eval_run = await run_eval(
        golden_version,
        scout_prompt_version,
        inter_question_sleep_seconds=inter_question_sleep_seconds,
    )
    logger.info(f"Scout run complete: {eval_run.run_id}, {eval_run.total_errors} errors")

    # Step 2: Score in parallel where possible
    gs = load_golden_set(golden_version)

    fab_task = asyncio.to_thread(score_fabrication_batch, eval_run)
    behav_task = asyncio.to_thread(score_behaviour_batch, eval_run, gs)
    fabrication, behavioural = await asyncio.gather(fab_task, behav_task)

    ragas = None
    if not skip_ragas:
        try:
            ragas = await score_with_ragas(eval_run)
        except Exception as e:
            logger.warning(f"RAGAS scoring failed: {e}. Continuing without RAGAS scores.")
            ragas = None

    logger.info("Scoring complete")

    # Step 2b: Run investigation scenarios for INVESTIGATION entries
    investigation_entries = [e for e in gs.entries if e.question_type == QuestionType.INVESTIGATION]
    investigation_results = []
    for entry in investigation_entries:
        from clubos2.eval.investigator_scorer import run_investigation_scenario
        result = await run_investigation_scenario(entry)
        investigation_results.append(result)

    if investigation_results:
        logger.info(
            f"Investigation scenarios complete: {sum(1 for r in investigation_results if r.overall_pass)}"
            f"/{len(investigation_results)} passed"
        )

    # Step 3: Generate report
    report = generate_report(eval_run, ragas, fabrication, behavioural, gs)
    output_path = Path(output_dir) / f"{eval_run.run_id}.md"
    render_markdown(report, output_path)

    # Also save the report as JSON alongside the markdown
    json_path = output_path.with_suffix(".json")
    json_path.write_text(report.model_dump_json(indent=2))
    logger.info(f"Report written: {output_path}")

    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run full ClubOS 2.0 eval pipeline")
    parser.add_argument("--golden", default="v1")
    parser.add_argument("--prompt-version", default=None)
    parser.add_argument("--output-dir", default="eval/reports")
    parser.add_argument("--skip-ragas", action="store_true", default=False,
                        help="Skip RAGAS LLM-judged scoring (deterministic layers only)")
    parser.add_argument(
        "--inter-question-sleep",
        type=float,
        default=2.0,
        help="Seconds to sleep between eval questions (throttle for OpenAI Tier 1 TPM). Default 2.0. Set to 0 to disable.",
    )
    args = parser.parse_args()

    path = asyncio.run(
        run_full_eval(
            args.golden,
            args.prompt_version,
            args.output_dir,
            args.skip_ragas,
            inter_question_sleep_seconds=args.inter_question_sleep,
        )
    )
    print(f"Report written to: {path}")
