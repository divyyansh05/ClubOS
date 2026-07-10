"""
Compare Gold-layer discovered metrics vs metric_registry contents.

Also tests which registry metrics actually resolve to Gold data via GoldClient,
since the registry uses different naming conventions than Gold CSVs.

Prints:
- Metrics in Gold but not in registry (compound-name match)
- Metrics in registry that fail to resolve to Gold data
- Metrics in registry with no Gold data (forward-looking / planned)
"""
import asyncio
import json
import sys
from pathlib import Path

import duckdb


def main():
    inventory_path = Path("docs/gold_metrics_inventory.json")
    if not inventory_path.exists():
        print("docs/gold_metrics_inventory.json not found.", file=sys.stderr)
        print("Run: python scripts/discover_gold_metrics.py > docs/gold_metrics_inventory.json", file=sys.stderr)
        sys.exit(1)

    gold = set(json.loads(inventory_path.read_text()))

    conn = duckdb.connect("var/clubos_semantic.duckdb", read_only=True)
    registry_rows = conn.execute("SELECT metric_name FROM metric_registry ORDER BY metric_name").fetchall()
    conn.close()
    registry = {row[0] for row in registry_rows}

    # Compound-name diff (Gold uses compound names, registry uses short names)
    missing_from_registry = sorted(gold - registry)
    in_registry_not_gold = sorted(registry - gold)

    print(f"Gold layer metrics (compound names): {len(gold)}")
    print(f"Registry metrics: {len(registry)}")

    print(f"\nIn Gold but not in registry as compound name ({len(missing_from_registry)}):")
    for m in missing_from_registry:
        print(f"  - {m}")

    # Resolution test: which registry metrics actually fetch Gold data?
    from clubos2.tools.gold_client import GoldClient, MetricNotInGoldError
    gc = GoldClient()

    resolves = []
    fails_resolution = []
    for m in sorted(registry):
        try:
            result = asyncio.run(gc.fetch_metric(m))
            if result:
                resolves.append(m)
            else:
                fails_resolution.append((m, "empty result"))
        except MetricNotInGoldError as e:
            fails_resolution.append((m, str(e)[:80]))
        except Exception as e:
            fails_resolution.append((m, f"ERROR: {str(e)[:80]}"))

    print(f"\nRegistry metrics that resolve to Gold data: {len(resolves)}/{len(registry)}")
    print(f"\nRegistry metrics that FAIL to resolve ({len(fails_resolution)}):")
    for m, reason in fails_resolution:
        print(f"  - {m}: {reason}")

    # Save gap analysis
    gap = {
        "gold_compound_metrics": sorted(gold),
        "registry_metrics": sorted(registry),
        "in_gold_not_registry_compound": missing_from_registry,
        "registry_resolves_to_gold": resolves,
        "registry_fails_resolution": [{"metric": m, "reason": r} for m, r in fails_resolution],
    }
    Path("docs/registry_gap_analysis.json").write_text(json.dumps(gap, indent=2))
    print(f"\nWrote docs/registry_gap_analysis.json")


if __name__ == "__main__":
    main()
