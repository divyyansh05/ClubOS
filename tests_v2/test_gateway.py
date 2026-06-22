from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from clubos2.gateway.client import (
    GatewayError,
    GatewaySettings,
    GatewayValidationError,
    ModelTier,
    call_llm,
)


class SimpleResponse(BaseModel):
    greeting: str
    number: int


@pytest.mark.asyncio
async def test_call_llm_string_response():
    """Verify call_llm returns a raw string response when no response_model is provided."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello there!"
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("clubos2.gateway.client.get_openai_client", return_value=mock_client):
        res = await call_llm(
            messages=[{"role": "user", "content": "Say hello"}], tier=ModelTier.ROUTING
        )
        assert res == "Hello there!"
        mock_client.chat.completions.create.assert_called_once()
        called_kwargs = mock_client.chat.completions.create.call_args[1]
        assert called_kwargs["model"] == "gpt-4o-mini"
        assert called_kwargs["temperature"] == 0.0
        assert "response_format" not in called_kwargs


@pytest.mark.asyncio
async def test_call_llm_pydantic_response():
    """Verify call_llm parses the response into the specified Pydantic model."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    # Mock content with markdown code blocks to check stripping logic
    mock_response.choices[0].message.content = '```json\n{"greeting": "Hello", "number": 42}\n```'
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 20
    mock_response.usage.completion_tokens = 15

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("clubos2.gateway.client.get_openai_client", return_value=mock_client):
        res = await call_llm(
            messages=[{"role": "user", "content": "Get json"}],
            tier=ModelTier.REASONING,
            response_model=SimpleResponse,
        )
        assert isinstance(res, SimpleResponse)
        assert res.greeting == "Hello"
        assert res.number == 42

        called_kwargs = mock_client.chat.completions.create.call_args[1]
        assert called_kwargs["model"] == "gpt-4o"
        assert called_kwargs["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_call_llm_temperature_override():
    """Verify that temperature override is correctly passed to the completions API."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Override"
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 5
    mock_response.usage.completion_tokens = 2

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("clubos2.gateway.client.get_openai_client", return_value=mock_client):
        await call_llm(messages=[{"role": "user", "content": "test"}], temperature=0.7)
        called_kwargs = mock_client.chat.completions.create.call_args[1]
        assert called_kwargs["temperature"] == 0.7


@pytest.mark.asyncio
async def test_call_llm_validation_error():
    """Verify that GatewayValidationError is raised on invalid JSON schema."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    # greeting parameter is missing and number is a string which fails Pydantic validation
    mock_response.choices[0].message.content = '{"number": "invalid_number_type"}'
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 5
    mock_response.usage.completion_tokens = 2

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("clubos2.gateway.client.get_openai_client", return_value=mock_client):
        with pytest.raises(GatewayValidationError):
            await call_llm(
                messages=[{"role": "user", "content": "invalid json"}],
                response_model=SimpleResponse,
            )


@pytest.mark.asyncio
async def test_call_llm_anthropic_fallback():
    """Verify that Anthropic provider logic executes correctly when selected in settings."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = "Anthropic reply"
    mock_response.content = [mock_content]
    mock_response.usage = MagicMock()
    mock_response.usage.input_tokens = 12
    mock_response.usage.output_tokens = 8

    mock_client.messages.create = AsyncMock(return_value=mock_response)

    custom_settings = GatewaySettings(
        default_provider="anthropic", default_routing_model="claude-haiku-4-5"
    )

    with (
        patch("clubos2.gateway.client.GatewaySettings", return_value=custom_settings),
        patch("clubos2.gateway.client.get_anthropic_client", return_value=mock_client),
    ):
        res = await call_llm(
            messages=[{"role": "user", "content": "Ask Anthropic"}], tier=ModelTier.ROUTING
        )
        assert res == "Anthropic reply"
        mock_client.messages.create.assert_called_once()
        called_kwargs = mock_client.messages.create.call_args[1]
        assert called_kwargs["model"] == "claude-haiku-4-5"


@pytest.mark.asyncio
async def test_call_llm_vertex_error():
    """Verify that Vertex AI provider raises a not implemented exception."""
    custom_settings = GatewaySettings(default_provider="vertex")
    with patch("clubos2.gateway.client.GatewaySettings", return_value=custom_settings):
        with pytest.raises(GatewayError) as exc_info:
            await call_llm(messages=[{"role": "user", "content": "Ask Vertex"}])
        assert "Vertex AI provider is configured but not yet implemented" in str(exc_info.value)
