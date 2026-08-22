from __future__ import annotations
import httpx
from pydantic import BaseModel, Field
from clubos2.observability.tracing import traced
from clubos2.mcp.server_config import WebSearchSettings, WebSearchProvider


class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str = Field(..., description="Excerpt of the page content")
    published_date: str | None = None
    relevance_score: float | None = None
    source: str = Field(..., description="Always 'web_search:tavily' or 'web_search:brave'")


class WebSearchClient:
    """Direct Python client for web search. Used internally by the Investigator agent."""

    def __init__(self, settings: WebSearchSettings | None = None):
        self.settings = settings or WebSearchSettings()
        if self.settings.web_search_provider == WebSearchProvider.TAVILY:
            if not self.settings.tavily_api_key:
                raise ValueError("TAVILY_API_KEY required for Tavily provider")
        elif self.settings.web_search_provider == WebSearchProvider.BRAVE:
            if not self.settings.brave_search_api_key:
                raise ValueError("BRAVE_SEARCH_API_KEY required for Brave provider")

    @traced(name="mcp:web_search", run_type="tool")
    async def search(
        self,
        query: str,
        max_results: int | None = None,
        include_recent_only: bool = False,
    ) -> list[WebSearchResult]:
        """Execute a web search. Returns up to max_results items."""
        max_results = max_results or self.settings.web_search_max_results
        if self.settings.web_search_provider == WebSearchProvider.TAVILY:
            return await self._search_tavily(query, max_results, include_recent_only)
        else:
            return await self._search_brave(query, max_results, include_recent_only)

    async def _search_tavily(self, query: str, max_results: int, recent_only: bool) -> list[WebSearchResult]:
        async with httpx.AsyncClient(timeout=self.settings.web_search_timeout_seconds) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.settings.tavily_api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "basic",
                    "topic": "news" if recent_only else "general",
                },
            )
            response.raise_for_status()
            data = response.json()
            return [
                WebSearchResult(
                    title=r["title"],
                    url=r["url"],
                    snippet=r["content"],
                    published_date=r.get("published_date"),
                    relevance_score=r.get("score"),
                    source="web_search:tavily",
                )
                for r in data.get("results", [])
            ]

    async def _search_brave(self, query: str, max_results: int, recent_only: bool) -> list[WebSearchResult]:
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.settings.brave_search_api_key or "",
        }
        params: dict = {"q": query, "count": max_results}
        if recent_only:
            params["freshness"] = "pd"  # past day
        async with httpx.AsyncClient(timeout=self.settings.web_search_timeout_seconds) as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("web", {}).get("results", [])
            return [
                WebSearchResult(
                    title=r["title"],
                    url=r["url"],
                    snippet=r.get("description", ""),
                    published_date=r.get("age"),
                    relevance_score=None,
                    source="web_search:brave",
                )
                for r in results[:max_results]
            ]
