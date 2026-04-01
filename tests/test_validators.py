"""Tests for input validators — runs without Wind Terminal."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from wind_mcp.core.validators import (
    validate_wind_codes,
    validate_edb_codes,
    validate_sector_codes,
    validate_date_range,
    validate_single_field,
    validate_universe_format,
    is_valid_date,
)


# --- Wind code validation ---

def test_validate_wind_codes_valid():
    result = validate_wind_codes("600030.SH,000001.SZ")
    assert result == ["600030.SH", "000001.SZ"]


def test_validate_wind_codes_list():
    result = validate_wind_codes(["AAPL.O", "00700.HK"])
    assert result == ["AAPL.O", "00700.HK"]


def test_validate_wind_codes_filters_invalid():
    result = validate_wind_codes(["600030.SH", "INVALID", "000001.SZ"])
    assert result == ["600030.SH", "000001.SZ"]


def test_validate_wind_codes_all_invalid():
    with pytest.raises(ValueError, match="No valid Wind codes"):
        validate_wind_codes(["not-a-code", "also bad"])


def test_validate_wind_codes_bloomberg_rejected():
    """Bloomberg format should be rejected — must be pre-converted."""
    with pytest.raises(ValueError):
        validate_wind_codes("AAPL US Equity")


# --- EDB code validation ---

def test_validate_edb_codes_valid():
    result = validate_edb_codes("M5567877,M0000272")
    assert result == ["M5567877", "M0000272"]


def test_validate_edb_codes_invalid():
    with pytest.raises(ValueError, match="No valid EDB codes"):
        validate_edb_codes("600030.SH")


# --- Sector code validation ---

def test_validate_sector_codes_valid():
    assert validate_sector_codes("a001010100") == ["a001010100"]


def test_validate_sector_codes_invalid():
    with pytest.raises(ValueError, match="No valid sector codes"):
        validate_sector_codes("600030.SH")


# --- Date validation ---

def test_is_valid_date_absolute():
    assert is_valid_date("2025-01-01")
    assert is_valid_date("20250101")


def test_is_valid_date_macros():
    assert is_valid_date("-1M")
    assert is_valid_date("-5D")
    assert is_valid_date("-10TD")
    assert is_valid_date("-1Y")


def test_is_valid_date_special_macros():
    assert is_valid_date("ED")
    assert is_valid_date("LYR")
    assert is_valid_date("MRQ")
    assert is_valid_date("IPO")


def test_is_valid_date_macro_arithmetic():
    assert is_valid_date("ED-10d")
    assert is_valid_date("LYR+1M")


def test_is_valid_date_empty():
    assert is_valid_date("")
    assert is_valid_date("  ")


def test_is_valid_date_invalid():
    assert not is_valid_date("hello")
    assert not is_valid_date("2025/01/01")


def test_validate_date_range_valid():
    validate_date_range("2024-01-01", "2025-01-01")  # No error
    validate_date_range("-1M", "")  # Macro + empty is fine
    validate_date_range("ED", "")  # Special macro


def test_validate_date_range_reversed():
    with pytest.raises(ValueError, match="after"):
        validate_date_range("2025-12-31", "2025-01-01")


def test_validate_date_range_invalid_format():
    with pytest.raises(ValueError, match="Invalid begin_date"):
        validate_date_range("not-a-date", "2025-01-01")


# --- Single field validation (WSES/WSEE) ---

def test_validate_single_field_ok():
    assert validate_single_field("pe_ttm", "WSES") == "pe_ttm"


def test_validate_single_field_list_single():
    assert validate_single_field(["pe_ttm"], "WSES") == "pe_ttm"


def test_validate_single_field_multiple_string():
    with pytest.raises(ValueError, match="single indicator"):
        validate_single_field("pe_ttm,roe_ttm", "WSES")


def test_validate_single_field_multiple_list():
    with pytest.raises(ValueError, match="single indicator"):
        validate_single_field(["pe_ttm", "roe_ttm"], "WSEE")


# --- Universe format validation ---

def test_validate_universe_format_valid():
    validate_universe_format("index:000300.SH")
    validate_universe_format("sector:a001010100")
    validate_universe_format("codes:600030.SH,000001.SZ")


def test_validate_universe_format_unknown():
    with pytest.raises(ValueError, match="Unknown universe"):
        validate_universe_format("unknown:something")


def test_validate_universe_format_empty_value():
    with pytest.raises(ValueError, match="Empty universe"):
        validate_universe_format("index:")
