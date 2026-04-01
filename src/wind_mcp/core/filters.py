"""
In-memory data filters for screening results.

Supports: gt, gte, lt, lte, eq, neq, between, in, contains, isnull, notnull.
All comparisons are null-safe and type-tolerant.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _safe_compare(val: Any, op: str, target: Any) -> bool:
    """Null-safe comparison. Returns False if value is None."""
    if val is None:
        return False
    try:
        if op == "gt":
            return val > target
        elif op == "gte":
            return val >= target
        elif op == "lt":
            return val < target
        elif op == "lte":
            return val <= target
        elif op == "eq":
            return val == target
        elif op == "neq":
            return val != target
        elif op == "between":
            return target[0] <= val <= target[1]
        elif op == "in":
            return val in target
        elif op == "contains":
            return str(target).lower() in str(val).lower()
    except (TypeError, IndexError):
        return False
    return False


def apply_filters(data: list[dict], filters: list[dict]) -> list[dict]:
    """
    Apply filter conditions to data rows.

    Each filter dict: {'field': str, 'op': str, 'value': any}
    Operators: gt, gte, lt, lte, eq, neq, between, in, contains, isnull, notnull

    Returns filtered list.
    """
    result = data
    for f in filters:
        field = f["field"].lower()
        op = f["op"]
        value = f.get("value")

        if op == "isnull":
            result = [r for r in result if r.get(field) is None]
        elif op == "notnull":
            result = [r for r in result if r.get(field) is not None]
        else:
            result = [r for r in result if _safe_compare(r.get(field), op, value)]

    return result
