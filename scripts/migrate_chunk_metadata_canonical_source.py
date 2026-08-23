"""
Rewrites all clubos_skills chunk metadata to have exactly one 'source' field
in canonical form. Removes ambiguous fields like 'file_path' when present.

Idempotent: safe to run multiple times.

Canonical form:
  Skill files  → skills.<basename>   (e.g. skills.priority_board)
  Gold data    → gold.<table>        (e.g. gold.priority_board)
  (Gold data is not stored in ChromaDB — this script only handles skill chunks.)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import chromadb
import os

CANONICAL_MAP = {
    # Raw basename → canonical alias (handles legacy chunks stored with just filename)
    "priority_board.md": "skills.priority_board",
    "signal_engine.md": "skills.signal_engine",
    "command_center.md": "skills.command_center",
    "monthly_briefing.md": "skills.monthly_briefing",
    "peer_benchmark.md": "skills.peer_benchmark",
    "social_intelligence.md": "skills.social_intelligence",
}


def canonicalize(raw: str) -> str:
    """Return canonical source for a raw source string. Raises if unmapped."""
    if raw in CANONICAL_MAP:
        return CANONICAL_MAP[raw]
    # Already canonical
    if raw.startswith(("skills.", "gold.", "metric_registry", "watchdog_alerts", "investigations", "web_search:")):
        return raw
    # Strip section suffix, canonicalize base, restore suffix
    if "::" in raw:
        base, section = raw.split("::", 1)
        return f"{canonicalize(base)}::{section}"
    raise ValueError(f"No canonical mapping for source: {raw!r}")


def main() -> None:
    chroma_dir = os.environ.get("CHROMA_PERSIST_DIR", "./var/chroma")
    client = chromadb.PersistentClient(path=chroma_dir)
    col = client.get_collection("clubos_skills")

    all_chunks = col.get(include=["metadatas", "documents"])
    ids = all_chunks["ids"]
    metas = all_chunks["metadatas"]

    updates = 0
    errors = []

    for chunk_id, meta in zip(ids, metas):
        new_meta = dict(meta)
        changed = False

        raw_source = new_meta.get("source", "")
        try:
            canonical = canonicalize(raw_source)
        except ValueError as e:
            errors.append(f"Chunk {chunk_id}: {e}")
            continue

        if canonical != raw_source:
            new_meta["source"] = canonical
            changed = True

        # Remove any stale ambiguous fields
        for stale_field in ("file_path", "origin", "canonical_source", "raw_path"):
            if stale_field in new_meta:
                del new_meta[stale_field]
                changed = True

        if changed:
            col.update(ids=[chunk_id], metadatas=[new_meta])
            updates += 1

    print(f"Scanned {len(ids)} chunks. Rewrote {updates}. Errors: {len(errors)}.")
    for e in errors:
        print(f"  ERROR: {e}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
