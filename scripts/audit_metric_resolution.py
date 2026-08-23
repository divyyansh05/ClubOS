"""Full audit of metric resolution across all registry entries.

Tests every metric in metric_registry against GoldClient.fetch_metric() and
classifies each as RESOLVES_CLEAN, RESOLVES_VIA_ASSET_PREFIX,
RESOLVES_VIA_ASSET_SUFFIX, RESOLVES_DIRECT, or FAILS_MISSING_ROW.

Output: docs/metric_resolution_audit.md + docs/metric_resolution_audit.json

Run with backend stopped (DuckDB lock):
    pkill -f "uvicorn app.main" || true
    python scripts/audit_metric_resolution.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clubos2.tools.gold_client import GoldClient, GoldClientSettings, MetricNotInGoldError
from clubos2.semantic_layer.lookup import get_all_metrics


def classify_resolution_path(metric_name: str, gc: GoldClient) -> str:
    asset, raw = gc._split_metric_name(metric_name)
    if asset is None:
        return "direct"
    # Determine if asset was matched as prefix or suffix
    for known_asset in sorted(gc.KNOWN_ASSETS, key=len, reverse=True):
        if metric_name.startswith(known_asset + "_"):
            return "asset_prefix"
    for known_asset in sorted(gc.KNOWN_ASSETS, key=len, reverse=True):
        if metric_name.endswith("_" + known_asset):
            return "asset_suffix"
    return "alias"


async def audit_all_metrics() -> list[dict]:
    gc = GoldClient(GoldClientSettings(gold_snapshots_dir="./data/gold_snapshots"))
    metrics = get_all_metrics()

    results = []
    for m in sorted(metrics, key=lambda x: x.metric_name):
        entry: dict = {
            "metric_name": m.metric_name,
            "business_name": m.business_name,
            "platform": m.platform,
        }

        asset, raw = gc._split_metric_name(m.metric_name)
        entry["gold_asset"] = asset
        entry["gold_raw"] = raw

        try:
            rows = await gc.fetch_metric(m.metric_name)
            res_path = classify_resolution_path(m.metric_name, gc)
            if res_path == "asset_prefix":
                entry["status"] = "RESOLVES_VIA_ASSET_PREFIX"
            elif res_path == "asset_suffix":
                entry["status"] = "RESOLVES_VIA_ASSET_SUFFIX"
            else:
                entry["status"] = "RESOLVES_DIRECT"
            entry["rows_returned"] = len(rows)
            entry["source"] = rows[0].get("source") if rows else None
        except MetricNotInGoldError:
            entry["status"] = "FAILS_MISSING_ROW"
            entry["reason"] = "No gold row matches via any resolution path"
        except Exception as e:
            entry["status"] = "FAILS_OTHER"
            entry["reason"] = str(e)

        results.append(entry)

    return results


def write_report(results: list[dict]) -> None:
    by_status: dict[str, list] = {}
    for r in results:
        by_status.setdefault(r["status"], []).append(r)

    total = len(results)
    now = datetime.now(UTC).isoformat()
    lines = [
        f"# Metric Resolution Audit — {now}",
        "",
        f"Total metrics tested: **{total}**",
        "",
        "## Summary",
        "",
    ]

    status_order = [
        "RESOLVES_VIA_ASSET_PREFIX",
        "RESOLVES_VIA_ASSET_SUFFIX",
        "RESOLVES_DIRECT",
        "FAILS_MISSING_ROW",
        "FAILS_OTHER",
    ]
    for status in status_order:
        count = len(by_status.get(status, []))
        pct = 100 * count / total if total else 0
        lines.append(f"- **{status}**: {count} ({pct:.1f}%)")

    resolves_total = sum(
        len(by_status.get(s, []))
        for s in ["RESOLVES_VIA_ASSET_PREFIX", "RESOLVES_VIA_ASSET_SUFFIX", "RESOLVES_DIRECT"]
    )
    lines += [
        "",
        f"**Total resolving**: {resolves_total}/{total}  ",
        f"**Total failing**: {total - resolves_total}/{total}",
        "",
    ]

    for status in status_order:
        entries = by_status.get(status, [])
        if not entries:
            continue
        lines.append(f"## {status} ({len(entries)})")
        lines.append("")
        for e in entries:
            lines.append(
                f"- `{e['metric_name']}` — {e['business_name']} (platform: {e['platform']})"
            )
            if e.get("gold_asset"):
                lines.append(f"  - gold path: asset=`{e['gold_asset']}`, raw=`{e['gold_raw']}`")
            if e.get("source"):
                lines.append(f"  - source: `{e['source']}`")
            if e.get("reason"):
                lines.append(f"  - reason: {e['reason']}")
        lines.append("")

    Path("docs/metric_resolution_audit.md").write_text("\n".join(lines))
    Path("docs/metric_resolution_audit.json").write_text(json.dumps(results, indent=2))

    print(f"Report written. ({total} metrics audited)")
    for status in status_order:
        count = len(by_status.get(status, []))
        print(f"  {status}: {count}")


if __name__ == "__main__":
    results = asyncio.run(audit_all_metrics())
    write_report(results)
