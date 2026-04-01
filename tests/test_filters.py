"""Tests for in-memory filters."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from wind_mcp.core.filters import apply_filters


SAMPLE_DATA = [
    {"code": "A", "pe_ttm": 10, "roe_ttm2": 20, "name": "Alpha"},
    {"code": "B", "pe_ttm": 25, "roe_ttm2": 8, "name": "Beta"},
    {"code": "C", "pe_ttm": None, "roe_ttm2": 15, "name": "Charlie"},
    {"code": "D", "pe_ttm": 50, "roe_ttm2": 30, "name": "Delta"},
]


def test_filter_gt():
    result = apply_filters(SAMPLE_DATA, [{"field": "pe_ttm", "op": "gt", "value": 20}])
    codes = [r["code"] for r in result]
    assert codes == ["B", "D"]


def test_filter_between():
    result = apply_filters(SAMPLE_DATA, [{"field": "pe_ttm", "op": "between", "value": [5, 30]}])
    codes = [r["code"] for r in result]
    assert codes == ["A", "B"]


def test_filter_in():
    result = apply_filters(SAMPLE_DATA, [{"field": "code", "op": "in", "value": ["A", "C"]}])
    codes = [r["code"] for r in result]
    assert codes == ["A", "C"]


def test_filter_isnull():
    result = apply_filters(SAMPLE_DATA, [{"field": "pe_ttm", "op": "isnull"}])
    codes = [r["code"] for r in result]
    assert codes == ["C"]


def test_filter_notnull():
    result = apply_filters(SAMPLE_DATA, [{"field": "pe_ttm", "op": "notnull"}])
    assert len(result) == 3


def test_filter_contains():
    result = apply_filters(SAMPLE_DATA, [{"field": "name", "op": "contains", "value": "lph"}])
    assert result[0]["code"] == "A"


def test_filter_chained():
    result = apply_filters(SAMPLE_DATA, [
        {"field": "pe_ttm", "op": "notnull"},
        {"field": "pe_ttm", "op": "lte", "value": 30},
        {"field": "roe_ttm2", "op": "gte", "value": 10},
    ])
    codes = [r["code"] for r in result]
    assert codes == ["A"]


def test_filter_null_safe():
    """Filters should skip None values without crashing."""
    result = apply_filters(SAMPLE_DATA, [{"field": "pe_ttm", "op": "lt", "value": 100}])
    # C has pe_ttm=None, should be excluded
    assert "C" not in [r["code"] for r in result]
