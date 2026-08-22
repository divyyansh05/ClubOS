from __future__ import annotations
from enum import Enum
from pydantic_settings import BaseSettings


class WebSearchProvider(str, Enum):
    TAVILY = "tavily"
    BRAVE = "brave"


class WebSearchSettings(BaseSettings):
    web_search_provider: WebSearchProvider = WebSearchProvider.TAVILY
    tavily_api_key: str | None = None
    brave_search_api_key: str | None = None
    web_search_max_results: int = 5
    web_search_timeout_seconds: int = 10

    model_config = {"env_file": ".env.v2", "extra": "ignore"}
