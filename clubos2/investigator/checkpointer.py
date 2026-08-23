from __future__ import annotations
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


@asynccontextmanager
async def get_checkpointer(path: str | None = None) -> AsyncIterator[AsyncSqliteSaver]:
    """Async context manager yielding an AsyncSqliteSaver for the Investigator graph.

    Usage:
        async with get_checkpointer() as checkpointer:
            graph = build_graph(checkpointer=checkpointer)
            ...
    """
    if path is None:
        path = "./var/clubos_investigator_checkpoints.sqlite"
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    async with AsyncSqliteSaver.from_conn_string(path) as saver:
        yield saver
