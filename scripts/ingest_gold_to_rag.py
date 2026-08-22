"""Populate clubos_rag ChromaDB collection with gold-layer metric narratives.

Generates one narrative chunk per metric row in gold_priority_board.csv and
gold_kpi_health.csv, enabling RAG fallback when the tool path fails silently.

Every chunk carries canonical source tag gold.<snapshot_name>.

Run with backend stopped (DuckDB lock not needed for this script):
    python scripts/ingest_gold_to_rag.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chromadb

from clubos2.rag.embeddings import embed_texts

GOLD_DIR = Path("data/gold_snapshots")
CHROMA_PATH = "var/chroma"
COLLECTION_NAME = "clubos_rag"

# Batch size for embedding calls
EMBED_BATCH = 32


def format_priority_board_row(row: pd.Series) -> str | None:
    """One narrative sentence per priority_board row."""
    asset = row.get("asset_name")
    metric = row.get("primary_metric")
    month = row.get("month")
    if pd.isna(asset) or pd.isna(metric):
        return None

    parts = [f"In the priority_board snapshot for {month}, {asset} {metric}"]

    try:
        js = json.loads(row["supporting_metrics_json"])
        sev = js.get("severity_inputs", {})
        if "metric_value" in sev:
            parts.append(f"had a value of {sev['metric_value']:.4g}")
        if "trend_direction" in sev:
            parts.append(f"with trend {sev['trend_direction']}")
        if "health_status" in sev:
            parts.append(f"and health status {sev['health_status']}")
        peer = js.get("peer_context", {})
        if peer.get("peer_rank"):
            parts.append(f"ranking #{peer['peer_rank']} among {peer.get('peer_club_count', '?')} clubs")
        score = row.get("priority_score")
        if pd.notna(score):
            parts.append(f"priority score {float(score):.3f}")
    except Exception:
        pass

    return ". ".join(parts) + "."


def format_kpi_health_row(row: pd.Series) -> str | None:
    """One narrative sentence per kpi_health row."""
    asset = row.get("asset_name")
    metric = row.get("metric_name")
    month = row.get("month")
    if pd.isna(asset) or pd.isna(metric):
        return None

    parts = [f"In the kpi_health snapshot for {month}, {asset} {metric}"]
    val = row.get("metric_value")
    if pd.notna(val):
        parts.append(f"had a value of {float(val):.4g}")
    trend = row.get("trend_direction")
    if pd.notna(trend):
        parts.append(f"with trend {trend}")
    health = row.get("health_status")
    if pd.notna(health):
        parts.append(f"and health status {health}")
    dev = row.get("deviation_from_rolling_avg")
    if pd.notna(dev):
        parts.append(f"deviation from rolling avg {float(dev):.3f}")

    return ". ".join(parts) + "."


def format_peer_benchmark_row(row: pd.Series) -> str | None:
    """One narrative sentence per peer_benchmark row."""
    asset = row.get("asset_name")
    metric = row.get("metric_name")
    month = row.get("month")
    if pd.isna(asset) or pd.isna(metric):
        return None

    parts = [f"In the peer_benchmark snapshot for {month}, {asset} {metric}"]
    val = row.get("rm_value")
    if pd.notna(val):
        parts.append(f"had a value of {float(val):.4g}")
    rank = row.get("rm_rank")
    if pd.notna(rank):
        parts.append(f"ranked #{int(rank)}")
    clubs = row.get("club_count")
    if pd.notna(clubs):
        parts.append(f"among {int(clubs)} clubs")
    gap = row.get("gap_to_peer_median")
    if pd.notna(gap):
        parts.append(f"gap to peer median {float(gap):.4g}")

    return ". ".join(parts) + "."


async def ingest() -> None:
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing {COLLECTION_NAME} collection for clean rebuild.")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    all_items: list[dict] = []

    # Source 1: gold_priority_board.csv
    pb_path = GOLD_DIR / "gold_priority_board.csv"
    pb_df = pd.read_csv(str(pb_path), low_memory=False)
    for idx, row in pb_df.iterrows():
        text = format_priority_board_row(row)
        if not text:
            continue
        row_id = str(row.get("priority_id", f"pb_{idx}"))
        all_items.append({
            "id": f"priority_board__{row_id}",
            "text": text,
            "metadata": {
                "source": "gold.priority_board",
                "asset_name": str(row.get("asset_name", "")),
                "metric_name": str(row.get("primary_metric", "")),
                "month": str(row.get("month", "")),
            },
        })

    # Source 2: gold_kpi_health.csv (recent months only to avoid huge collection)
    kh_path = GOLD_DIR / "gold_kpi_health.csv"
    kh_df = pd.read_csv(str(kh_path), low_memory=False)
    recent_months = sorted(kh_df["month"].unique(), reverse=True)[:12]
    kh_recent = kh_df[kh_df["month"].isin(recent_months)]
    for idx, row in kh_recent.iterrows():
        text = format_kpi_health_row(row)
        if not text:
            continue
        asset = str(row.get("asset_name", ""))
        metric = str(row.get("metric_name", ""))
        month = str(row.get("month", ""))
        chunk_id = f"kpi_health__{asset}__{metric}__{month}"
        all_items.append({
            "id": chunk_id,
            "text": text,
            "metadata": {
                "source": "gold.kpi_health",
                "asset_name": asset,
                "metric_name": metric,
                "month": month,
            },
        })

    # Source 3: gold_peer_benchmark.csv
    peer_path = GOLD_DIR / "gold_peer_benchmark.csv"
    peer_df = pd.read_csv(str(peer_path), low_memory=False)
    recent_peer_months = sorted(peer_df["month"].unique(), reverse=True)[:12]
    peer_recent = peer_df[peer_df["month"].isin(recent_peer_months)]
    for idx, row in peer_recent.iterrows():
        text = format_peer_benchmark_row(row)
        if not text:
            continue
        asset = str(row.get("asset_name", ""))
        metric = str(row.get("metric_name", ""))
        month = str(row.get("month", ""))
        chunk_id = f"peer_benchmark__{asset}__{metric}__{month}"
        all_items.append({
            "id": chunk_id,
            "text": text,
            "metadata": {
                "source": "gold.peer_benchmark",
                "asset_name": asset,
                "metric_name": metric,
                "month": month,
            },
        })

    print(f"Prepared {len(all_items)} narrative chunks.")

    # Embed and write in batches
    inserted = 0
    for i in range(0, len(all_items), EMBED_BATCH):
        batch = all_items[i : i + EMBED_BATCH]
        texts = [item["text"] for item in batch]

        embeddings = await embed_texts(texts)

        collection.add(
            ids=[item["id"] for item in batch],
            documents=texts,
            embeddings=embeddings,
            metadatas=[item["metadata"] for item in batch],
        )
        inserted += len(batch)
        print(f"  Ingested {inserted}/{len(all_items)}")

    final_count = collection.count()
    print(f"\nclubos_rag total chunks: {final_count}")

    # Smoke-test (must use OpenAI embeddings to match collection dimension)
    test_embs = await embed_texts(["streaming daily users trend"])
    sample = collection.query(query_embeddings=test_embs, n_results=3)
    print("\nSample retrieval for 'streaming daily users trend':")
    for doc in sample["documents"][0]:
        print(f"  - {doc[:120]}")


if __name__ == "__main__":
    asyncio.run(ingest())
