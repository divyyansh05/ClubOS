from __future__ import annotations

import logging
import os
from typing import Any

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger("clubos.rag.embeddings")

_RETRYABLE = (RateLimitError, APITimeoutError, APIConnectionError)


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type(_RETRYABLE),
    reraise=True,
    before_sleep=lambda rs: logger.warning(
        f"OpenAI embedding transient error (attempt {rs.attempt_number}), retrying"
    ),
)
async def _embed_with_retry(client: AsyncOpenAI, **kwargs: Any) -> Any:
    return await client.embeddings.create(**kwargs)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-embed via OpenAI text-embedding-3-small (1536 dimensions).

    Handles the 8192-token-per-input limit by truncating with a warning log.
    Batch size 100 max per API call.
    """
    if not texts:
        return []

    from clubos2.gateway.client import GatewaySettings
    _settings = GatewaySettings()
    api_key = _settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")

    client = AsyncOpenAI(api_key=api_key)
    batch_size = 100
    all_embeddings: list[list[float]] = []

    for idx in range(0, len(texts), batch_size):
        batch = texts[idx : idx + batch_size]
        clean_batch = []

        for text in batch:
            # Safe character-based truncation to avoid exceeding 8192 tokens (~32,000 characters)
            if len(text) > 32000:
                logger.warning(
                    f"Text length ({len(text)} chars) exceeds safe limits. "
                    "Truncating text to prevent OpenAI token overflow error."
                )
                text = text[:32000]
            clean_batch.append(text)

        response = await _embed_with_retry(
            client,
            input=clean_batch,
            model="text-embedding-3-small",
        )

        batch_embeddings = [data.embedding for data in response.data]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings
