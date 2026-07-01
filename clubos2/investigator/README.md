# Investigator Agent

The first true LLM agent in ClubOS 2.0. Uses a LangGraph linear ReAct loop
with 6 bound tools, multi-step reasoning, and SqliteSaver checkpointing.

## Architecture

```
START → agent_node → should_continue → tools → agent_node → ... → END
```

## Tools

1. `query_metrics` — verified numeric values from Gold layer
2. `search_knowledge` — internal skill files and briefings
3. `get_recent_alerts` — Watchdog alert history for a metric
4. `get_metric_definition` — semantic layer definition
5. `get_peer_benchmark` — peer comparison data
6. `web_search` — public web via MCP-backed client

## Resuming an interrupted investigation

```python
config = {"configurable": {"thread_id": investigation_id}}
result = await graph.ainvoke(state, config=config)
```

The checkpointer loads saved state from where it left off. Phase 4 does NOT expose
a resume API endpoint — interrupted investigations are marked 'failed' and a new
investigation can be triggered manually.
