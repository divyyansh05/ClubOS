"""CI protection: verify cross-source data agreement and preferred_source coverage.

Two invariants maintained:
1. Every documented cross-source divergence has preferred_source set in registry.
2. All active registry metrics have preferred_source set (registry declares authority).

Finding: zero value divergences between priority_board and kpi_health for the same
(asset, metric, period) as of the 2026-07 audit. The divergence report only contains
coverage_gap entries (periods present in one source but not the other). These are
expected and resolved by preferred_source routing.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def load_divergence_report() -> list[dict]:
    path = Path("docs/cross_source_divergence.json")
    if not path.exists():
        pytest.skip("cross_source_divergence.json not found — run scripts/compare_cross_source_values.py")
    return json.loads(path.read_text())


def test_no_unresolved_value_divergences() -> None:
    """Value divergences (same period, different value) must be zero.

    If this fails, a pipeline change introduced real disagreements between
    kpi_health and priority_board for the same (metric, period). Investigate
    the pipeline and set preferred_source before shipping.
    """
    from clubos2.semantic_layer.lookup import get_all_metrics, refresh_cache

    refresh_cache()
    findings = load_divergence_report()
    value_divergences = [f for f in findings if f.get("type") == "value_divergence"]

    if not value_divergences:
        return

    metrics_with_ps: set[str] = set()
    all_metrics = get_all_metrics()
    for m in all_metrics:
        if getattr(m, "preferred_source", None):
            metrics_with_ps.add(m.metric_name)

    unresolved = []
    for d in value_divergences:
        compound = f"{d['asset']}_{d['metric']}"
        # Check if any registry metric maps to this compound name and has preferred_source
        resolved = any(
            m.metric_name == compound or
            (m.metric_name.startswith(d["asset"] + "_") and d["metric"] in m.metric_name)
            for m in all_metrics
            if getattr(m, "preferred_source", None)
        )
        if not resolved:
            unresolved.append(d)

    if unresolved:
        pytest.fail(
            f"{len(unresolved)} value divergences lack preferred_source resolution:\n"
            + "\n".join(
                f"  {d['asset']}+{d['metric']} {d['period']}: "
                f"pb={d.get('value_a'):.6g} vs kh={d.get('value_b'):.6g} "
                f"({d.get('rel_diff_pct', 0):.2f}% diff)"
                for d in unresolved[:10]
            )
        )


def test_all_active_metrics_have_preferred_source() -> None:
    """Every active metric must declare which gold source is authoritative.

    preferred_source=None means GoldClient falls back to default order, which
    may change if fetch_metric internals are refactored. Explicit is better.
    """
    from clubos2.semantic_layer.lookup import get_all_metrics, refresh_cache

    refresh_cache()
    metrics = get_all_metrics()
    active = [m for m in metrics if getattr(m, "is_active", True)]

    missing = [
        m.metric_name
        for m in active
        if not getattr(m, "preferred_source", None)
    ]

    if missing:
        pytest.fail(
            f"{len(missing)} active metrics have no preferred_source set:\n"
            + "\n".join(f"  - {name}" for name in missing[:20])
            + "\n\nRun: python scripts/backfill_preferred_source.py"
        )


def test_coverage_gaps_are_all_kh_only() -> None:
    """Coverage gaps should only be 'kh has period but pb does not', not the reverse.

    priority_board only writes rows for metrics above the priority threshold, so gaps
    where pb has data but kh does not would indicate a kpi_health pipeline regression.
    """
    findings = load_divergence_report()
    pb_has_kh_missing = [
        f for f in findings
        if f.get("type") == "coverage_gap" and f.get("absent_from") == "gold.kpi_health"
    ]
    if pb_has_kh_missing:
        # Group by metric for readability
        by_metric: dict[str, int] = {}
        for f in pb_has_kh_missing:
            key = f"{f['asset']}+{f['metric']}"
            by_metric[key] = by_metric.get(key, 0) + 1
        pytest.fail(
            f"{len(pb_has_kh_missing)} periods in priority_board are absent from kpi_health. "
            "This suggests a kpi_health pipeline gap — investigate before shipping:\n"
            + "\n".join(f"  {k}: {v} months" for k, v in list(by_metric.items())[:10])
        )
