from __future__ import annotations

import json
import logging
import os
import re
import time
from enum import Enum
from typing import Any, TypeVar

import openai
from openai import APIConnectionError, APITimeoutError, RateLimitError
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger("clubos.gateway")

T = TypeVar("T", bound=BaseModel)

_RETRYABLE = (RateLimitError, APITimeoutError, APIConnectionError)


class GatewaySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.v2", extra="ignore")

    openai_api_key: str = Field(default="")
    vertex_api_key: str | None = Field(default=None)
    vertex_project_id: str | None = Field(default=None)
    vertex_location: str | None = Field(default=None)

    default_provider: str = Field(default="openai")
    scout_model: str = Field(default="gpt-4o-mini")
    investigator_model: str = Field(default="gpt-4o")
    ragas_judge_model: str = Field(default="gpt-4o-mini")
    # Legacy aliases kept for pipeline code that reads these directly
    default_routing_model: str = Field(default="gpt-4o-mini")
    default_reasoning_model: str = Field(default="gpt-4o")
    default_temperature: float = Field(default=0.0)
    guardrail_fabrication_mode: str = "warn"  # 'warn' | 'block'
    scout_prompt_version: str = Field(
        default="v6",
        description=(
            "Active Scout prompt version. Must match the version used to generate "
            "eval/reports/baseline.json — CI gate comparisons are meaningless if "
            "these diverge. Update this default when promoting a new prompt version "
            "after baseline re-establishment."
        ),
    )


class ModelTier(Enum):
    ROUTING = "routing"
    REASONING = "reasoning"


class GatewayError(Exception):
    """Base exception for the LLM Gateway."""

    pass


class GatewayValidationError(GatewayError):
    """Exception raised when model response fails structured validation."""

    pass


# Pricing per million tokens in USD
PRICING = {
    "gpt-4o-mini": {
        "input": 0.15 / 1_000_000,
        "output": 0.60 / 1_000_000,
    },
    "gpt-4o": {
        "input": 2.50 / 1_000_000,
        "output": 10.00 / 1_000_000,
    },
}

_openai_client: openai.AsyncOpenAI | None = None


def _validate_openai_key() -> None:
    key = GatewaySettings().openai_api_key or os.environ.get("OPENAI_API_KEY", "")
    if not key or key.strip() == "":
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Check .env.v2 file exists and contains "
            "OPENAI_API_KEY=... — see .env.v2.example for reference."
        )
    if not key.startswith("sk-"):
        raise RuntimeError(
            f"OPENAI_API_KEY appears malformed (does not start with 'sk-'). "
            f"First 10 chars: {key[:10]!r}"
        )


def get_openai_client() -> openai.AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        settings = GatewaySettings()
        api_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise GatewayError(
                "OpenAI API key is missing. Set OPENAI_API_KEY in environment or .env.v2"
            )
        _openai_client = openai.AsyncOpenAI(api_key=api_key)
    return _openai_client


def clean_json_text(text: str) -> str:
    """Strips markdown code fences and whitespace from response strings."""
    text = text.strip()
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    return text


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type(_RETRYABLE),
    reraise=True,
    before_sleep=lambda rs: logger.warning(
        f"OpenAI transient error (attempt {rs.attempt_number}), retrying in {rs.next_action.sleep:.1f}s"  # type: ignore[union-attr]
    ),
)
async def _chat_with_retry(client: openai.AsyncOpenAI, **kwargs: Any) -> Any:
    return await client.chat.completions.create(**kwargs)


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type(_RETRYABLE),
    reraise=True,
    before_sleep=lambda rs: logger.warning(
        f"OpenAI embedding transient error (attempt {rs.attempt_number}), retrying in {rs.next_action.sleep:.1f}s"  # type: ignore[union-attr]
    ),
)
async def _embed_with_retry(client: openai.AsyncOpenAI, **kwargs: Any) -> Any:
    return await client.embeddings.create(**kwargs)


async def call_llm(
    messages: list[dict[str, Any]],
    tier: ModelTier = ModelTier.REASONING,
    response_model: type[T] | None = None,
    temperature: float | None = None,
    max_tokens: int = 4096,
    system: str | None = None,
) -> T | str:
    """
    Unified entrypoint for LLM requests in ClubOS 2.0.
    Handles routing, structured output enforcement, usage cost computation, and error raises.
    """
    settings = GatewaySettings()
    provider = settings.default_provider.lower()
    temp = temperature if temperature is not None else settings.default_temperature

    if tier == ModelTier.ROUTING:
        model_name = settings.default_routing_model
    else:
        model_name = settings.default_reasoning_model

    if provider == "openai":
        return await _call_openai(
            messages=messages,
            model_name=model_name,
            tier=tier,
            response_model=response_model,
            temperature=temp,
            max_tokens=max_tokens,
            system=system,
        )
    elif provider == "vertex":
        raise GatewayError(
            "Vertex AI provider is configured but not yet implemented. "
            "Please check back when Vertex AI support is fully rolled out."
        )
    else:
        raise GatewayError(f"Unsupported LLM provider: {settings.default_provider}")


async def _call_openai(
    messages: list[dict[str, Any]],
    model_name: str,
    tier: ModelTier,
    response_model: type[T] | None,
    temperature: float,
    max_tokens: int,
    system: str | None,
) -> T | str:
    openai_messages = []
    system_parts = []

    if system:
        system_parts.append(system)

    for msg in messages:
        if msg.get("role") == "system":
            system_parts.append(msg.get("content", ""))
        else:
            openai_messages.append(msg)

    if response_model:
        schema = json.dumps(response_model.model_json_schema())
        schema_instruction = (
            f"\n\nYou must respond with ONLY a valid JSON object matching this schema: {schema}. "
            "Do not include any other text, markdown, or code fences."
        )
        system_parts.append(schema_instruction)

    if system_parts:
        openai_messages.insert(0, {"role": "system", "content": "\n\n".join(system_parts)})

    api_kwargs: dict[str, Any] = {
        "model": model_name,
        "messages": openai_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if response_model:
        api_kwargs["response_format"] = {"type": "json_object"}

    start_time = time.perf_counter()
    try:
        client = get_openai_client()
        response = await _chat_with_retry(client, **api_kwargs)
    except Exception as e:
        raise GatewayError(f"OpenAI completion request failed: {str(e)}") from e

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    content = response.choices[0].message.content or ""
    prompt_tokens = response.usage.prompt_tokens if response.usage else 0
    completion_tokens = response.usage.completion_tokens if response.usage else 0

    pricing = PRICING.get(model_name, {"input": 0.0, "output": 0.0})
    try:
        cost = (prompt_tokens * pricing["input"]) + (completion_tokens * pricing["output"])
        cost_str = f"${cost:.6f}"
    except Exception:
        cost = 0.0
        cost_str = "$0.000000"

    logger.info(
        f"LLM Call (OpenAI): model={model_name}, tier={tier.value}, input_tokens={prompt_tokens}, "
        f"output_tokens={completion_tokens}, latency_ms={latency_ms}, cost_usd={cost_str}"
        + (f", response_model={response_model.__name__}" if response_model else "")
    )

    if response_model:
        cleaned_content = clean_json_text(content)
        try:
            return response_model.model_validate_json(cleaned_content)
        except Exception as e:
            logger.warning(
                f"OpenAI structured output validation failed for {response_model.__name__}: {e}"
            )
            raise GatewayValidationError(
                f"Failed to validate response against Pydantic schema {response_model.__name__}. "
                f"Raw content: {content}"
            ) from e

    return content
