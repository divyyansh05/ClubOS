from __future__ import annotations

import logging
import os
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any, Literal

from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree
from langsmith.run_trees import RunTree

logger = logging.getLogger("clubos.observability")


def setup_tracing() -> None:
    """Initialize LangSmith tracing configuration from env vars."""
    api_key = os.environ.get("LANGSMITH_API_KEY") or os.environ.get("LANGCHAIN_API_KEY")
    project = os.environ.get("LANGSMITH_PROJECT") or os.environ.get("LANGCHAIN_PROJECT", "clubos-2")

    if not api_key:
        logger.warning("LANGSMITH_API_KEY is missing. Tracing will be disabled (no-op).")
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGCHAIN_PROJECT"] = project
        logger.info(f"LangSmith tracing configured for project: {project}")


def traced(
    name: str,
    run_type: Literal[
        "chain", "tool", "llm", "retriever", "embedding", "prompt", "parser"
    ] = "chain",
) -> Callable[..., Any]:
    """Decorator to trace a sync or async function using LangSmith."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return traceable(run_type=run_type, name=name)(func)

    return decorator


@contextmanager
def traced_span(
    name: str,
    run_type: Literal[
        "chain", "tool", "llm", "retriever", "embedding", "prompt", "parser"
    ] = "chain",
    inputs: dict[str, Any] | None = None,
) -> Generator[RunTree | None, None, None]:
    """Context manager to trace a block of code as a LangSmith span."""
    parent_tree = get_current_run_tree()
    if parent_tree:
        child_run = parent_tree.create_child(
            name=name,
            run_type=run_type,
            inputs=inputs or {},
        )
        child_run.post()
        try:
            yield child_run
        except Exception as e:
            child_run.end(error=str(e))
            child_run.patch()
            raise
        else:
            child_run.end(outputs={})
            child_run.patch()
    else:
        # Check if tracing is enabled and key exists to start a root trace
        api_key = os.environ.get("LANGSMITH_API_KEY") or os.environ.get("LANGCHAIN_API_KEY")
        if api_key:
            project = os.environ.get("LANGSMITH_PROJECT") or os.environ.get(
                "LANGCHAIN_PROJECT", "clubos-2"
            )
            root_run = RunTree(
                name=name,
                run_type=run_type,
                inputs=inputs or {},
                project_name=project,
            )
            root_run.post()
            try:
                yield root_run
            except Exception as e:
                root_run.end(error=str(e))
                root_run.patch()
                raise
            else:
                root_run.end(outputs={})
                root_run.patch()
        else:
            yield None


def get_current_langsmith_trace_url() -> str | None:
    """Retrieve the URL of the current active LangSmith trace."""
    try:
        run_tree = get_current_run_tree()
        if run_tree:
            if hasattr(run_tree, "get_url"):
                url = run_tree.get_url()
                return str(url) if url else None
            elif hasattr(run_tree, "url"):
                url = run_tree.url
                return str(url) if url else None
    except Exception:
        pass
    return None
