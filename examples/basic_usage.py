"""
Basic usage examples for Wind MCP tools.

These examples show how to call the handlers directly (outside MCP context).
Requires Wind Terminal running and logged in.
"""

from wind_mcp.models.inputs import (
    SnapshotInput, HistoricalInput, RealtimeInput, MacroInput,
    TradingDaysInput, DateOffsetInput,
)
from wind_mcp.models.enums import ResponseFormat
from wind_mcp.handlers.snapshot import handle_snapshot
from wind_mcp.handlers.historical import handle_historical
from wind_mcp.handlers.realtime import handle_realtime
from wind_mcp.handlers.macro import handle_macro
from wind_mcp.handlers.dates import handle_trading_days, handle_date_offset
from wind_mcp.formatters import format_response


def example_snapshot():
    """Get current price and valuation for multiple A-shares."""
    params = SnapshotInput(
        codes=["600030.SH", "000001.SZ", "300750.SZ"],
        fields=["PRICE", "VALUATION"],
        response_format=ResponseFormat.MARKDOWN,
    )
    data = handle_snapshot(params)
    print(format_response(data, "markdown"))


def example_snapshot_bbg():
    """Same query using Bloomberg-style tickers."""
    params = SnapshotInput(
        codes=["AAPL US Equity", "700 HK Equity"],
        fields="close,pe_ttm,pb_lf",
        response_format=ResponseFormat.MARKDOWN,
    )
    data = handle_snapshot(params)
    print(format_response(data, "markdown"))


def example_historical():
    """Get 1-month daily price history."""
    params = HistoricalInput(
        codes="600030.SH",
        fields="close,volume",
        begin_date="-1M",
        response_format=ResponseFormat.JSON,
    )
    data = handle_historical(params)
    print(format_response(data, "json"))


def example_macro():
    """Get China CPI YoY for the past year."""
    params = MacroInput(
        codes="M5567877",
        begin_date="-1Y",
        response_format=ResponseFormat.MARKDOWN,
    )
    data = handle_macro(params)
    print(format_response(data, "markdown"))


def example_trading_days():
    """Get trading days for the current month."""
    params = TradingDaysInput(
        begin_date="RMF",
        response_format=ResponseFormat.MARKDOWN,
    )
    data = handle_trading_days(params)
    print(format_response(data, "markdown"))


if __name__ == "__main__":
    print("=== Snapshot ===")
    example_snapshot()
    print("\n=== Historical ===")
    example_historical()
    print("\n=== Macro ===")
    example_macro()
    print("\n=== Trading Days ===")
    example_trading_days()
