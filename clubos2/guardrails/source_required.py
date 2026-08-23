from __future__ import annotations

import functools
import logging
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

logger = logging.getLogger("clubos.guardrails.source_required")

T = TypeVar("T")


class SourceMissingError(Exception):
    """A tool returned a row/chunk without a populated source field."""


def requires_source(
    tool_func: Callable[..., Coroutine[Any, Any, T]],
) -> Callable[..., Coroutine[Any, Any, T]]:
    """
    Decorator that validates every returned row/chunk has source populated.
    Raises SourceMissingError if any item is missing source.
    Applied INSIDE @traced so that tracing wraps validation failures too.
    """

    @functools.wraps(tool_func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        result = await tool_func(*args, **kwargs)

        items = result if isinstance(result, list) else [result]
        for i, item in enumerate(items):
            if hasattr(item, "source"):
                if not item.source or not isinstance(item.source, str):
                    raise SourceMissingError(
                        f"Tool '{tool_func.__name__}' returned item[{i}] "
                        f"without populated source field: {item!r}"
                    )

        return result

    return wrapper
