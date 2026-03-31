"""Tests for Bloomberg → Wind ticker converter — runs without Wind Terminal."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from wind_mcp.core.converter import ensure_wind_codes, wind_to_bbg


def test_china_a_shares():
    assert ensure_wind_codes("600030 CH Equity") == "600030.SH"
    assert ensure_wind_codes("000001 CH Equity") == "000001.SZ"
    assert ensure_wind_codes("300750 CH Equity") == "300750.SZ"
    assert ensure_wind_codes("688981 CH Equity") == "688981.SH"
    assert ensure_wind_codes("830799 CH Equity") == "830799.BJ"


def test_hk():
    assert ensure_wind_codes("700 HK Equity") == "00700.HK"
    assert ensure_wind_codes("1133 HK Equity") == "01133.HK"
    assert ensure_wind_codes("9988 HK Equity") == "09988.HK"


def test_us():
    assert ensure_wind_codes("AAPL US Equity") == "AAPL.O"
    assert ensure_wind_codes("JPM US Equity") == "JPM.N"
    assert ensure_wind_codes("CEG US Equity") == "CEG.O"


def test_indices():
    assert ensure_wind_codes("SPX Index") == "SPX.GI"
    assert ensure_wind_codes("HSI Index") == "HSI.HI"
    assert ensure_wind_codes("CSI300 Index") == "000300.SH"


def test_passthrough():
    assert ensure_wind_codes("600030.SH") == "600030.SH"
    assert ensure_wind_codes("00700.HK") == "00700.HK"
    assert ensure_wind_codes("AAPL.O") == "AAPL.O"


def test_multiple():
    result = ensure_wind_codes(["AAPL US Equity", "600030.SH", "700 HK Equity"])
    assert result == ["AAPL.O", "600030.SH", "00700.HK"]


def test_reverse():
    assert wind_to_bbg("600030.SH") == "600030 CH Equity"
    assert wind_to_bbg("00700.HK") == "700 HK Equity"
    assert wind_to_bbg("AAPL.O") == "AAPL US Equity"


def test_japan():
    assert ensure_wind_codes("7203 JP Equity") == "7203.T"


def test_london():
    assert ensure_wind_codes("SHEL LN Equity") == "SHEL.L"


def test_commodity():
    assert ensure_wind_codes("GC1 Comdty") == "GC.CMX"
    assert ensure_wind_codes("CL1 Comdty") == "CL.NYM"


def test_currency():
    assert ensure_wind_codes("EUR Curncy") == "EURUSD.FX"
    assert ensure_wind_codes("JPY Curncy") == "USDJPY.FX"
