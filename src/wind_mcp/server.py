"""
Wind MCP Server — entry point.

Exposes ~19 tools via FastMCP for AI assistant access to Wind Financial Terminal.
"""

import logging
from mcp.server.fastmcp import FastMCP
from .models.inputs import (
    SnapshotInput, HistoricalInput, MinuteBarsInput, TicksInput,
    RealtimeInput, DatasetInput, MacroInput, SectorSeriesInput,
    SectorSnapshotInput, ScreenInput, DynamicScreenInput,
    EstimatesInput, HoldersInput, StockConnectInput,
    EventCalendarInput, TradingDaysInput, DateOffsetInput, DaysCountInput,
)
from .formatters import format_response

# Import handlers
from .handlers.snapshot import handle_snapshot
from .handlers.historical import handle_historical
from .handlers.minute_bars import handle_minute_bars
from .handlers.ticks import handle_ticks
from .handlers.realtime import handle_realtime
from .handlers.dataset import handle_dataset
from .handlers.macro import handle_macro
from .handlers.sector import handle_sector_series, handle_sector_snapshot
from .handlers.screening import handle_screen, handle_dynamic_screen
from .handlers.estimates import handle_estimates
from .handlers.holders import handle_holders
from .handlers.stock_connect import handle_stock_connect
from .handlers.calendar import handle_calendar
from .handlers.dates import handle_trading_days, handle_date_offset, handle_days_count

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("wind-mcp", description="Wind Financial Terminal MCP Server")


# === Core Data Tools ===

@mcp.tool()
def wind_get_snapshot(params: SnapshotInput) -> str:
    """Get cross-sectional data for securities (WSS). Supports multiple securities and fields. Use for current/point-in-time fundamentals, valuation, price data."""
    data = handle_snapshot(params)
    return format_response(data, params.response_format.value)


@mcp.tool()
def wind_get_historical(params: HistoricalInput) -> str:
    """Get daily time series data (WSD). Price, volume, fundamentals over date range. Supports date macros like '-1M', '-1Y', 'LYR'."""
    data = handle_historical(params)
    return format_response(data, params.response_format.value)


@mcp.tool()
def wind_get_minute_bars(params: MinuteBarsInput) -> str:
    """Get minute-level K-line data (WSI). Supports 1/3/5/10/15/30/60 minute intervals."""
    data = handle_minute_bars(params)
    return format_response(data, params.response_format.value)


@mcp.tool()
def wind_get_ticks(params: TicksInput) -> str:
    """Get intraday tick data (WST). Level-2 bid/ask snapshots and trade-by-trade data."""
    data = handle_ticks(params)
    return format_response(data, params.response_format.value)


@mcp.tool()
def wind_get_realtime(params: RealtimeInput) -> str:
    """Get real-time quote snapshot (WSQ). Current price, change, volume for securities."""
    data = handle_realtime(params)
    return format_response(data, params.response_format.value)


@mcp.tool()
def wind_get_dataset(params: DatasetInput) -> str:
    """Get report/dataset data (WSET). Index constituents, sector members, IPO events, fund holdings, etc."""
    data = handle_dataset(params)
    return format_response(data, params.response_format.value)


@mcp.tool()
def wind_get_macro(params: MacroInput) -> str:
    """Get global macro economic data (EDB). China CPI, PMI, M2, global rates, commodity prices. Codes from Wind EDB browser."""
    data = handle_macro(params)
    return format_response(data, params.response_format.value)


# === Sector Tools ===

@mcp.tool()
def wind_get_sector_series(params: SectorSeriesInput) -> str:
    """Get sector-level time series data (WSES). Average PE, price, fundamentals for A-share sectors."""
    data = handle_sector_series(params)
    return format_response(data, params.response_format.value)


@mcp.tool()
def wind_get_sector_snapshot(params: SectorSnapshotInput) -> str:
    """Get sector-level snapshot data (WSEE). Cross-sectional sector averages."""
    data = handle_sector_snapshot(params)
    return format_response(data, params.response_format.value)


# === Screening Tools ===

@mcp.tool()
def wind_run_screen(params: ScreenInput) -> str:
    """Run a saved screening scheme from Wind terminal (WEQS)."""
    data = handle_screen(params)
    return format_response(data, params.response_format.value)


@mcp.tool()
def wind_dynamic_screen(params: DynamicScreenInput) -> str:
    """Custom dynamic screening: pick universe, fields (with FieldSet shortcuts), apply filters, rank, and slice top N. Most powerful tool for stock screening."""
    data = handle_dynamic_screen(params)
    return format_response(data, params.response_format.value)


# === Analysis Tools ===

@mcp.tool()
def wind_get_estimates(params: EstimatesInput) -> str:
    """Get consensus analyst estimates: EPS/Revenue FY1/FY2, estimate revisions, target price, ratings."""
    data = handle_estimates(params)
    return format_response(data, params.response_format.value)


@mcp.tool()
def wind_get_holders(params: HoldersInput) -> str:
    """Get shareholder data: top 10 holders, institutional holders, fund holders."""
    data = handle_holders(params)
    return format_response(data, params.response_format.value)


@mcp.tool()
def wind_get_stock_connect(params: StockConnectInput) -> str:
    """Get Stock Connect (沪深港通) northbound holding data. Key A-share marginal pricing signal."""
    data = handle_stock_connect(params)
    return format_response(data, params.response_format.value)


@mcp.tool()
def wind_get_calendar(params: EventCalendarInput) -> str:
    """Get event calendar: dividends, IPOs, restricted share unlocks, earnings announcements."""
    data = handle_calendar(params)
    return format_response(data, params.response_format.value)


# === Date Utility Tools ===

@mcp.tool()
def wind_get_trading_days(params: TradingDaysInput) -> str:
    """Get trading day sequence between two dates. Supports different exchanges and day types."""
    data = handle_trading_days(params)
    return format_response(data, params.response_format.value)


@mcp.tool()
def wind_get_date_offset(params: DateOffsetInput) -> str:
    """Get the date N trading/calendar days before or after a reference date."""
    data = handle_date_offset(params)
    return str(data)


@mcp.tool()
def wind_get_days_count(params: DaysCountInput) -> str:
    """Count trading/calendar days between two dates."""
    data = handle_days_count(params)
    return str(data)


# === Server Runner ===

def main():
    import sys
    if "--http" in sys.argv:
        port = 8080
        for arg in sys.argv:
            if arg.startswith("--port="):
                port = int(arg.split("=")[1])
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    elif "--sse" in sys.argv:
        port = 8080
        for arg in sys.argv:
            if arg.startswith("--port="):
                port = int(arg.split("=")[1])
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
