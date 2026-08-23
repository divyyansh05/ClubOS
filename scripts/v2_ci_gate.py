#!/usr/bin/env python3
"""
CI gate for ClubOS 2.0. Runs the eval, compares against a baseline,
fails the build if any regression is detected.

Usage:
    python scripts/v2_ci_gate.py --baseline eval/reports/baseline.json

Exit codes:
    0 = pass (no regressions)
    1 = regression detected
    2 = baseline missing or corrupted
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path


REGRESSION_THRESHOLDS = {
    "fabrication_incidence_rate": 0.0,       # strict: any increase fails
    "behavioural_pass_rate_drop_max": 0.05,  # 5pp drop tolerance
    "ragas_metric_drop_max": 0.05,           # 5pp drop tolerance
}


async def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="ClubOS 2.0 CI gate")
    parser.add_argument("--baseline", default="eval/reports/baseline.json")
    parser.add_argument("--golden", default="v1")
    parser.add_argument("--prompt-version", default=None)
    parser.add_argument("--skip-ragas", action="store_true", default=False,
                        help="Skip RAGAS scoring (null RAGAS values skip regression checks)")
    args = parser.parse_args()

    prompt_version = args.prompt_version
    if prompt_version is None:
        from clubos2.gateway.client import GatewaySettings
        prompt_version = GatewaySettings().scout_prompt_version
    print(f"CI gate running against scout_prompt_version={prompt_version}")

    baseline_path = Path(args.baseline)
    if not baseline_path.exists():
        print(f"ERROR: Baseline not found at {baseline_path}", file=sys.stderr)
        print(
            "Create one with:\n"
            "  make v2-eval\n"
            "  cp eval/reports/eval_*.json eval/reports/baseline.json"
        )
        sys.exit(2)

    try:
        baseline = json.loads(baseline_path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: Baseline corrupted: {e}", file=sys.stderr)
        sys.exit(2)

    print(f"Baseline loaded from {baseline_path}")
    print("Running eval...")

    from clubos2.eval.pipeline import run_full_eval

    report_path = await run_full_eval(
        golden_version=args.golden,
        scout_prompt_version=prompt_version,
        skip_ragas=args.skip_ragas,
    )
    current_json_path = report_path.with_suffix(".json")
    current = json.loads(current_json_path.read_text())

    regressions: list[str] = []

    # Fabrication check (strict — any increase fails)
    baseline_fab = baseline.get("fabrication_summary", {}).get("entries_with_fabrication", 0)
    current_fab = current.get("fabrication_summary", {}).get("entries_with_fabrication", 0)
    if current_fab > baseline_fab:
        regressions.append(
            f"FABRICATION REGRESSION: {baseline_fab} → {current_fab} entries with fabrication"
        )

    # Behavioural pass rate check
    baseline_behav = baseline.get("behavioural_summary", {}).get("overall_pass_rate", 0.0)
    current_behav = current.get("behavioural_summary", {}).get("overall_pass_rate", 0.0)
    behav_drop = baseline_behav - current_behav
    if behav_drop > REGRESSION_THRESHOLDS["behavioural_pass_rate_drop_max"]:
        regressions.append(
            f"BEHAVIOURAL REGRESSION: pass rate dropped {behav_drop:.1%} "
            f"({baseline_behav:.1%} → {current_behav:.1%})"
        )

    # RAGAS metric checks
    for field in ("ragas_avg_faithfulness", "ragas_avg_context_relevance", "ragas_avg_answer_relevance"):
        b_val = baseline.get(field)
        c_val = current.get(field)
        if b_val is not None and c_val is not None:
            drop = b_val - c_val
            if drop > REGRESSION_THRESHOLDS["ragas_metric_drop_max"]:
                regressions.append(
                    f"{field.upper()} REGRESSION: dropped {drop:.2f} ({b_val:.2f} → {c_val:.2f})"
                )

    if regressions:
        print("\n=== REGRESSIONS DETECTED ===")
        for r in regressions:
            print(f"  ✗ {r}")
        print(f"\nReport: {report_path}")
        sys.exit(1)

    print("\n=== ALL CHECKS PASSED ===")
    print(f"  Fabrication incidence: {current_fab}/{current.get('total_questions', 20)}")
    print(f"  Behavioural pass rate: {current_behav:.1%}")
    if current.get("ragas_avg_faithfulness") is not None:
        print(f"  RAGAS faithfulness:    {current['ragas_avg_faithfulness']:.2f}")
    print(f"\nReport: {report_path}")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
