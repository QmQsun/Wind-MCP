"""Tests for FieldSet expansion — runs without Wind Terminal."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from wind_mcp.tools.field_expander import expand_fields
from wind_mcp.tools.fieldsets import FIELDSETS, get_screening_full


def test_expand_single_fieldset():
    result = expand_fields("PRICE")
    assert "open" in result
    assert "close" in result
    assert "volume" in result
    assert "pct_chg" in result


def test_expand_mixed():
    result = expand_fields("PRICE,pe_ttm,roe_ttm2")
    assert "open" in result
    assert "pe_ttm" in result
    assert "roe_ttm2" in result


def test_expand_list_input():
    result = expand_fields(["PRICE", "VALUATION"])
    assert "open" in result
    assert "pe_ttm" in result
    assert "pb_lf" in result


def test_expand_dedup():
    result = expand_fields(["PRICE", "close"])
    # "close" is in PRICE, should not be duplicated
    assert result.count("close") == 1


def test_expand_screening_full():
    result = expand_fields(["SCREENING_FULL"])
    assert len(result) > 20
    # Should contain fields from all component FieldSets
    assert "close" in result
    assert "pe_ttm" in result
    assert "roe_ttm2" in result
    assert "yoy_or" in result


def test_expand_passthrough():
    result = expand_fields("my_custom_field")
    assert result == ["my_custom_field"]


def test_expand_case_insensitive_fieldset():
    result = expand_fields("price")
    assert "open" in result


def test_screening_full_no_duplicates():
    result = get_screening_full()
    assert len(result) == len(set(f.lower() for f in result))
