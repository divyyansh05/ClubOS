from __future__ import annotations
import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


def get_checkpointer(path: str | None = None) -> SqliteSaver:
    """Returns a configured SqliteSaver for the Investigator graph.

    Args:
        path: Override default path. None = ./var/clubos_investigator_checkpoints.sqlite.

    The checkpointer persists graph state at every node transition. If an investigation
    is interrupted, the next call with the same thread_id resumes from last checkpoint.
    """
    if path is None:
        path = "./var/clubos_investigator_checkpoints.sqlite"
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path, check_same_thread=False)
    return SqliteSaver(conn)
