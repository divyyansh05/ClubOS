"""
ClubOS 2.0 — Web Search MCP Server

Exposes the web_search tool over the Model Context Protocol so external
AI clients (Claude Desktop, other MCP-aware agents) can use it.

Run with: python -m clubos2.mcp.web_search_server
"""
from __future__ import annotations
from mcp.server.fastmcp import FastMCP
from clubos2.mcp.web_search_client import WebSearchClient

mcp = FastMCP("clubos-web-search")
client = WebSearchClient()


@mcp.tool()
async def web_search(query: str, max_results: int = 5, recent_only: bool = False) -> list[dict]:
    """Search the web for current information.

    Use this when the Investigator needs external context that isn't in the
    ClubOS data layer — e.g., news about a competitor, current platform outages,
    industry trends affecting a metric.

    Args:
        query: Natural-language search query. Be specific.
        max_results: How many results to return (1-10).
        recent_only: If True, prefer results from the last 30 days.

    Returns:
        List of search results, each with title, url, snippet, source.
    """
    results = await client.search(query, max_results=max_results, include_recent_only=recent_only)
    return [r.model_dump() for r in results]


if __name__ == "__main__":
    mcp.run()
