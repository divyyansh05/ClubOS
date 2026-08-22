from __future__ import annotations


def get_tool_overview() -> str:
    """Returns a markdown summary of all Investigator tools for debugging."""
    from clubos2.investigator.tools import INVESTIGATOR_TOOLS
    lines = ["# Investigator Tools\n"]
    for t in INVESTIGATOR_TOOLS:
        lines.append(f"## {t.name}")
        lines.append(f"{t.description}\n")
    return "\n".join(lines)
