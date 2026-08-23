# ClubOS Web Search MCP Server

Exposes web search as an MCP tool for Claude Desktop and other MCP-aware clients.

## Provider
Configured via `WEB_SEARCH_PROVIDER` env var (default: `tavily`).
Free tier limits: Tavily 1000/month, Brave 2000/month.

## Starting the server

```bash
python -m clubos2.mcp.web_search_server
```

## Claude Desktop configuration

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "clubos-web-search": {
      "command": "python",
      "args": ["-m", "clubos2.mcp.web_search_server"],
      "cwd": "/path/to/clubos/repo"
    }
  }
}
```

## Manual smoke test
Run the server, then in Claude Desktop: "use clubos-web-search to find recent news about Real Madrid".
