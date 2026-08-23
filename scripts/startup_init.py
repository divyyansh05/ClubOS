"""Idempotent bootstrap for v2 stack.

Called from Dockerfile RUN step to bake seeded state into the container image,
and optionally from the FastAPI lifespan handler as a safety belt on cold start.

Runs (in order):
  1. bootstrap_db()      — creates metric_registry, watchdog_alerts, investigations,
                            briefings tables + applies migrations
  2. run_seed()          — populates metric_registry with 76 metrics
  3. ingest_gold_to_rag  — populates clubos_rag ChromaDB collection (if empty)

Every step is idempotent — safe to run multiple times. Skips silently on any
missing optional dep (e.g. no OPENAI_API_KEY at build time skips RAG ingest).

Exit codes:
  0 — full init succeeded OR partial (RAG skipped) with core DB ready
  1 — core DB init failed (fatal, container should not deploy)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure repo root is importable so `clubos2.*` resolves regardless of CWD
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _step_bootstrap_db() -> bool:
    """Bootstrap every v2 DB subsystem's migrations.

    Each subsystem owns its own migrations dir + bootstrap function — they don't
    auto-run when the repo class is instantiated. Must be called explicitly here
    so tables exist before the first API request hits them.
    """
    ok = True

    try:
        from clubos2.semantic_layer.db import bootstrap_db as bootstrap_semantic
        bootstrap_semantic()
        print("[init] semantic_layer bootstrap OK", flush=True)
    except Exception as e:
        print(f"[init] semantic_layer bootstrap FAILED: {e}", flush=True)
        ok = False

    try:
        from clubos2.watchdog.orchestrator import bootstrap_all as bootstrap_watchdog
        bootstrap_watchdog()
        print("[init] watchdog bootstrap OK (alerts + memory + snapshots)", flush=True)
    except Exception as e:
        print(f"[init] watchdog bootstrap FAILED: {e}", flush=True)
        ok = False

    try:
        from clubos2.investigator.repo import bootstrap_investigations_db
        bootstrap_investigations_db()
        print("[init] investigations bootstrap OK", flush=True)
    except Exception as e:
        print(f"[init] investigations bootstrap FAILED: {e}", flush=True)
        ok = False

    try:
        from clubos2.briefer.repo import bootstrap_briefings_db
        bootstrap_briefings_db()
        print("[init] briefings bootstrap OK", flush=True)
    except Exception as e:
        print(f"[init] briefings bootstrap FAILED: {e}", flush=True)
        ok = False

    return ok


def _step_seed_registry() -> bool:
    try:
        from clubos2.semantic_layer.seed import run_seed
        count = run_seed()
        print(f"[init] seeded {count} metrics", flush=True)
        return True
    except Exception as e:
        print(f"[init] seed FAILED: {e}", flush=True)
        return False


def _step_ingest_rag() -> bool:
    """Populate clubos_rag ChromaDB collection with gold-layer narratives.

    Skipped silently if OPENAI_API_KEY is missing (embeddings unavailable) or
    if the collection is already populated.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        print("[init] RAG ingest skipped — OPENAI_API_KEY not set", flush=True)
        return True

    try:
        import chromadb
        persist_dir = os.environ.get("CHROMA_PERSIST_DIR", str(_REPO_ROOT / "var" / "chroma"))
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=persist_dir)
        try:
            existing = client.get_collection("clubos_rag")
            if existing.count() > 0:
                print(f"[init] clubos_rag already populated ({existing.count()} chunks) — skipping ingest", flush=True)
                return True
        except Exception:
            pass  # collection doesn't exist yet, will be created by ingest
    except Exception as e:
        print(f"[init] chroma pre-check failed (continuing): {e}", flush=True)

    try:
        import asyncio
        # Reuse the ingest script — same logic that's tested locally
        script_path = _REPO_ROOT / "scripts" / "ingest_gold_to_rag.py"
        if not script_path.exists():
            print("[init] ingest_gold_to_rag.py not found — RAG left empty", flush=True)
            return True
        # Import as module rather than subprocess to preserve error visibility
        import importlib.util
        spec = importlib.util.spec_from_file_location("_rag_ingest", script_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "ingest"):
                asyncio.run(mod.ingest())
                print("[init] RAG ingest OK", flush=True)
    except Exception as e:
        print(f"[init] RAG ingest FAILED (non-fatal): {e}", flush=True)
        # Non-fatal — deploy can proceed with empty RAG, degrades gracefully
    return True


def main() -> int:
    print("[init] starting v2 stack bootstrap", flush=True)

    if not _step_bootstrap_db():
        print("[init] FATAL: DB bootstrap failed — aborting", flush=True)
        return 1

    if not _step_seed_registry():
        print("[init] FATAL: registry seed failed — aborting", flush=True)
        return 1

    _step_ingest_rag()  # non-fatal

    print("[init] v2 stack bootstrap complete", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
