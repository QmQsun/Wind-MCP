"""
Output formatters: Markdown table or JSON.
"""

import json
from typing import Any


def format_response(data: Any, fmt: str = "markdown") -> str:
    """Format parsed data for MCP response."""
    if fmt == "json":
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    if isinstance(data, list) and data and isinstance(data[0], dict):
        return _dict_list_to_markdown(data)
    elif isinstance(data, list):
        return "\n".join(str(item) for item in data)
    elif isinstance(data, dict):
        return _dict_to_markdown(data)
    else:
        return str(data)


def _dict_list_to_markdown(rows: list[dict]) -> str:
    """Convert list of dicts to Markdown table."""
    if not rows:
        return "*No data*"

    headers = list(rows[0].keys())
    lines = []

    # Header row
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    # Data rows
    for row in rows:
        cells = [_format_cell(row.get(h, "")) for h in headers]
        lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(lines)


def _dict_to_markdown(d: dict) -> str:
    """Single dict → key-value table."""
    lines = ["| Key | Value |", "| --- | --- |"]
    for k, v in d.items():
        lines.append(f"| {k} | {_format_cell(v)} |")
    return "\n".join(lines)


def _format_cell(val: Any) -> str:
    """Format a single cell value for display."""
    if val is None:
        return "—"
    if isinstance(val, float):
        if abs(val) >= 1e9:
            return f"{val/1e9:.2f}B"
        if abs(val) >= 1e6:
            return f"{val/1e6:.2f}M"
        if abs(val) < 0.01 and val != 0:
            return f"{val:.4f}"
        return f"{val:.2f}"
    return str(val)
