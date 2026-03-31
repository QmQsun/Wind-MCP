"""Tests for output formatters — runs without Wind Terminal."""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from wind_mcp.formatters import format_response


def test_format_json():
    data = [{"code": "600030.SH", "close": 25.6}]
    result = format_response(data, "json")
    parsed = json.loads(result)
    assert parsed[0]["code"] == "600030.SH"


def test_format_markdown_table():
    data = [
        {"code": "600030.SH", "close": 25.6, "pe_ttm": 18.5},
        {"code": "000001.SZ", "close": 30.1, "pe_ttm": 22.3},
    ]
    result = format_response(data, "markdown")
    assert "| code |" in result
    assert "600030.SH" in result
    assert "000001.SZ" in result
    assert "---" in result


def test_format_markdown_none():
    data = [{"code": "600030.SH", "value": None}]
    result = format_response(data, "markdown")
    assert "—" in result


def test_format_markdown_large_numbers():
    data = [{"value": 1_500_000_000.0}]
    result = format_response(data, "markdown")
    assert "1.50B" in result


def test_format_markdown_millions():
    data = [{"value": 2_500_000.0}]
    result = format_response(data, "markdown")
    assert "2.50M" in result


def test_format_empty_list():
    data = []
    result = format_response(data, "markdown")
    assert result == ""


def test_format_string_list():
    data = ["2025-01-01", "2025-01-02", "2025-01-03"]
    result = format_response(data, "markdown")
    assert "2025-01-01" in result


def test_format_dict():
    data = {"key1": "value1", "key2": 42}
    result = format_response(data, "markdown")
    assert "| Key | Value |" in result
    assert "key1" in result
