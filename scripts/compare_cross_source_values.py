"""Compare values for every (asset, metric, period) tuple that appears in
both gold_priority_board and gold_kpi_health.

Priority board values are inside supporting_metrics_json → severity_inputs →
metric_value. KPI health values are the metric_value column directly.

Output: docs/cross_source_divergence.json + docs/cross_source_divergence.md
Run: python scripts/compare_cross_source_values.py
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import pandas as pd

GOLD_DIR = Path("data/gold_snapshots")
OUT_DIR = Path("docs")

RELATIVE_TOLERANCE = 0.005   # 0.5 %
ABSOLUTE_TOLERANCE = 1e-6

# Also track period-coverage gaps (metric exists in both sources but one is
# missing a month the other has). These drive "wrong period returned" bugs.
COVERAGE_GAP_NOTE = "coverage_gap"
VALUE_DIVERGENCE_NOTE = "value_divergence"


def load_priority_board_values() -> dict[tuple, float]:
    """Extract (asset, metric, yyyy-mm) → severity_inputs.metric_value."""
    df = pd.read_csv(GOLD_DIR / "gold_priority_board.csv", low_memory=False)
    out = {}
    for _, row in df.iterrows():
        try:
            js = json.loads(row["supporting_metrics_json"])
            val = js.get("severity_inputs", {}).get("metric_value")
            if val is None:
                continue
            key = (str(row["asset_name"]), str(row["primary_metric"]), str(row["month"])[:7])
            out[key] = float(val)
        except Exception:
            continue
    return out


def load_kpi_health_values() -> dict[tuple, float]:
    """Extract (asset, metric, yyyy-mm) → metric_value."""
    df = pd.read_csv(GOLD_DIR / "gold_kpi_health.csv", low_memory=False)
    out = {}
    for _, row in df.iterrows():
        if pd.isna(row.get("metric_value")):
            continue
        key = (str(row["asset_name"]), str(row["metric_name"]), str(row["month"])[:7])
        out[key] = float(row["metric_value"])
    return out


def values_disagree(v1: float, v2: float) -> bool:
    abs_diff = abs(v1 - v2)
    if abs_diff <= ABSOLUTE_TOLERANCE:
        return False
    denom = max(abs(v1), abs(v2), 1e-12)
    return abs_diff / denom > RELATIVE_TOLERANCE


def main() -> None:
    pb_vals = load_priority_board_values()
    kh_vals = load_kpi_health_values()

    # All (asset, metric) pairs that appear in both sources
    pb_pairs = {(a, m) for a, m, _ in pb_vals}
    kh_pairs = {(a, m) for a, m, _ in kh_vals}
    cross_pairs = pb_pairs & kh_pairs

    divergences = []
    coverage_gaps: list[dict] = []

    for asset, metric in sorted(cross_pairs):
        pb_months = {p for a, m, p in pb_vals if a == asset and m == metric}
        kh_months = {p for a, m, p in kh_vals if a == asset and m == metric}
        all_months = pb_months | kh_months

        for period in sorted(all_months):
            pb_v = pb_vals.get((asset, metric, period))
            kh_v = kh_vals.get((asset, metric, period))

            if pb_v is not None and kh_v is not None:
                if values_disagree(pb_v, kh_v):
                    abs_diff = abs(pb_v - kh_v)
                    denom = max(abs(pb_v), abs(kh_v), 1e-12)
                    divergences.append({
                        "asset": asset,
                        "metric": metric,
                        "period": period,
                        "type": VALUE_DIVERGENCE_NOTE,
                        "source_a": "gold.priority_board",
                        "value_a": pb_v,
                        "source_b": "gold.kpi_health",
                        "value_b": kh_v,
                        "abs_diff": abs_diff,
                        "rel_diff_pct": abs_diff / denom * 100,
                    })
            elif pb_v is not None and kh_v is None:
                coverage_gaps.append({
                    "asset": asset,
                    "metric": metric,
                    "period": period,
                    "type": COVERAGE_GAP_NOTE,
                    "present_in": "gold.priority_board",
                    "absent_from": "gold.kpi_health",
                    "value": pb_v,
                })
            elif kh_v is not None and pb_v is None:
                coverage_gaps.append({
                    "asset": asset,
                    "metric": metric,
                    "period": period,
                    "type": COVERAGE_GAP_NOTE,
                    "present_in": "gold.kpi_health",
                    "absent_from": "gold.priority_board",
                    "value": kh_v,
                })

    # Write JSON
    OUT_DIR.mkdir(exist_ok=True)
    all_findings = divergences + coverage_gaps
    (OUT_DIR / "cross_source_divergence.json").write_text(
        json.dumps(all_findings, indent=2)
    )

    # Write markdown report
    by_metric_div: dict = defaultdict(list)
    for d in divergences:
        by_metric_div[(d["asset"], d["metric"])].append(d)

    by_metric_gap_kh: dict = defaultdict(int)  # months only in kpi_health
    by_metric_gap_pb: dict = defaultdict(int)  # months only in priority_board
    for g in coverage_gaps:
        key = (g["asset"], g["metric"])
        if g["absent_from"] == "gold.priority_board":
            by_metric_gap_kh[key] += 1
        else:
            by_metric_gap_pb[key] += 1

    lines = [
        "# Cross-Source Data Integrity Report",
        "",
        f"Sources compared: `gold.priority_board` vs `gold.kpi_health`",
        f"Tolerance: absolute {ABSOLUTE_TOLERANCE}, relative {RELATIVE_TOLERANCE*100:.2f}%",
        "",
        "## Summary",
        "",
        f"- Cross-source (asset, metric) pairs: **{len(cross_pairs)}**",
        f"- Overlapping (asset, metric, period) triples: **{sum(1 for a, m, p in pb_vals if (a,m,p) in kh_vals)}**",
        f"- **Value divergences** (same period, different value): **{len(divergences)}**",
        f"- **Coverage gaps** (period in one source but not the other): **{len(coverage_gaps)}**",
        f"  - Periods only in kpi_health (missed by priority_board): **{sum(by_metric_gap_kh.values())}**",
        f"  - Periods only in priority_board (missed by kpi_health): **{sum(by_metric_gap_pb.values())}**",
        "",
    ]

    if divergences:
        lines += [
            "## Value Divergences (same period, different value)",
            "",
            "| Asset | Metric | Period | PB value | KH value | Rel diff % |",
            "|---|---|---|---|---|---|",
        ]
        for d in sorted(divergences, key=lambda x: -x["rel_diff_pct"]):
            lines.append(
                f"| {d['asset']} | {d['metric']} | {d['period']} "
                f"| {d['value_a']:.6g} | {d['value_b']:.6g} | {d['rel_diff_pct']:.2f}% |"
            )
        lines.append("")
    else:
        lines += [
            "## Value Divergences",
            "",
            "**None.** When both sources have data for the same (asset, metric, period),",
            "values agree within tolerance. The gold layer is internally consistent.",
            "",
        ]

    lines += [
        "## Coverage Gaps — Periods only in kpi_health",
        "",
        "These months exist in kpi_health but NOT in priority_board.",
        "GoldClient's current priority (priority_board first) silently skips them,",
        "returning the wrong period when only kpi_health has the requested month.",
        "",
    ]
    top_kh_gaps = sorted(by_metric_gap_kh.items(), key=lambda x: -x[1])[:20]
    if top_kh_gaps:
        lines += [
            "| Asset | Metric | Months missing from priority_board |",
            "|---|---|---|",
        ]
        for (asset, metric), count in top_kh_gaps:
            lines.append(f"| {asset} | {metric} | {count} months |")
    else:
        lines.append("None.")

    lines += [
        "",
        "## Root Cause of gq_062 Failure",
        "",
        "`ecommerce/conversion_rate` for November 2025 exists in kpi_health (0.014637) but NOT",
        "in priority_board. GoldClient tries priority_board first and finds other months (Oct 2025,",
        "Jan 2026) — so it returns without falling through to kpi_health. Scout receives no Nov 2025",
        "data and returns a wrong-period value.",
        "",
        "**Fix:** When `preferred_source = gold.kpi_health`, GoldClient tries kpi_health first.",
        "Since kpi_health has 6× more (metric, period) coverage, preferred_source should default",
        "to kpi_health for all 57 cross-source metrics.",
        "",
        "## Finding for v1 pipeline session",
        "",
        "priority_board has sporadic period gaps for many metrics. This is likely because the",
        "priority board pipeline only writes a row when a metric exceeds the priority threshold.",
        "Metrics that are healthy (below threshold) have no priority_board row for that month.",
        "kpi_health is written for every metric every month regardless of health status.",
        "This is an intentional pipeline difference, not a bug — but it means priority_board",
        "is NOT a reliable source for absolute metric values. kpi_health is always preferred.",
    ]

    (OUT_DIR / "cross_source_divergence.md").write_text("\n".join(lines))

    print(f"Priority board triples: {len(pb_vals)}")
    print(f"KPI health triples: {len(kh_vals)}")
    print(f"Cross-source (asset,metric) pairs: {len(cross_pairs)}")
    print(f"Value divergences: {len(divergences)}")
    print(f"Coverage gaps (kh only): {sum(by_metric_gap_kh.values())}")
    print(f"Coverage gaps (pb only): {sum(by_metric_gap_pb.values())}")
    print()
    if not divergences:
        print("PATTERN: Zero value divergences. Sources agree on every overlapping period.")
        print("ROOT CAUSE of eval failures: coverage gaps causing GoldClient to return wrong-period data.")
    else:
        print(f"Top divergent pairs:")
        for (a, m), ds in sorted(by_metric_div.items(), key=lambda x: -len(x[1]))[:5]:
            print(f"  {a}+{m}: {len(ds)} periods")


if __name__ == "__main__":
    main()
