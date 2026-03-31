"""
Pydantic input models for all Wind MCP tools.

Every tool has a corresponding input model that validates parameters
and provides clear descriptions for the MCP tool schema.
"""

from pydantic import BaseModel, Field
from .enums import ResponseFormat, Periodicity, BarInterval, DayType, TradingCalendar


class SnapshotInput(BaseModel):
    """Input for wind_get_snapshot (WSS)."""

    codes: str | list[str] = Field(
        ...,
        description="Security codes. e.g. '600030.SH' or ['600030.SH','000001.SZ']. Also accepts Bloomberg format like 'AAPL US Equity'.",
    )
    fields: str | list[str] = Field(
        ...,
        description="Wind field names or FieldSet shortcuts. e.g. 'close,pe_ttm' or ['PRICE','VALUATION'] or 'close,MOMENTUM'",
    )
    options: str = Field(
        default="",
        description="Optional Wind parameters. e.g. 'tradeDate=20250101;priceAdj=F'",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class HistoricalInput(BaseModel):
    """Input for wind_get_historical (WSD)."""

    codes: str | list[str] = Field(
        ...,
        description="Security codes. Supports multi-code single-field OR single-code multi-field.",
    )
    fields: str | list[str] = Field(
        ..., description="Field names or FieldSet shortcuts."
    )
    begin_date: str = Field(
        ...,
        description="Start date. Supports: '2024-01-01', '20240101', '-5D', '-1M', 'LYR', etc.",
    )
    end_date: str = Field(
        default="", description="End date. Empty string = today. Supports date macros."
    )
    options: str = Field(
        default="", description="e.g. 'Period=W;PriceAdj=F;Fill=Previous'"
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class MinuteBarsInput(BaseModel):
    """Input for wind_get_minute_bars (WSI)."""

    codes: str | list[str] = Field(..., description="Security codes.")
    fields: str | list[str] = Field(
        default="open,high,low,close,volume",
        description="Field names for minute bars.",
    )
    begin_time: str = Field(
        ..., description="Start datetime. e.g. '2025-03-01 09:30:00'"
    )
    end_time: str = Field(default="", description="End datetime. Empty = now.")
    options: str = Field(
        default="", description="e.g. 'BarSize=5' for 5-min bars. Default is 1-min."
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class TicksInput(BaseModel):
    """Input for wind_get_ticks (WST)."""

    codes: str = Field(..., description="Single security code. e.g. '600030.SH'")
    fields: str | list[str] = Field(
        default="last,volume,amt", description="Tick data fields."
    )
    begin_time: str = Field(..., description="Start datetime.")
    end_time: str = Field(default="", description="End datetime.")
    options: str = Field(default="")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class RealtimeInput(BaseModel):
    """Input for wind_get_realtime (WSQ)."""

    codes: str | list[str] = Field(..., description="Security codes.")
    fields: str | list[str] = Field(
        default="rt_last,rt_chg,rt_pct_chg,rt_vol,rt_amt",
        description="Realtime field names. Wind RT fields start with 'rt_'.",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class DatasetInput(BaseModel):
    """Input for wind_get_dataset (WSET)."""

    table_name: str = Field(
        ...,
        description=(
            "WSET report name. Common values: "
            "'SectorConstituent' (板块成分), 'IndexConstituent' (指数成分+权重), "
            "'StockConnect' (沪深港通), 'MarginTrade' (融资融券), "
            "'BlockTrade' (大宗交易), 'RestrictedStock' (限售解禁), "
            "'IPOEvent' (IPO), 'FundPortfolio' (基金持仓)"
        ),
    )
    options: str = Field(
        default="",
        description=(
            "Report parameters. e.g. "
            "'date=2025-03-31;sectorId=a001010100' or "
            "'date=2025-03-31;windcode=000300.SH'"
        ),
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class MacroInput(BaseModel):
    """Input for wind_get_macro (EDB)."""

    codes: str | list[str] = Field(
        ...,
        description=(
            "EDB macro indicator codes. e.g. 'M5567877' (China CPI YoY). "
            "Use Wind terminal's EDB browser or code generator to find codes."
        ),
    )
    begin_date: str = Field(default="-1Y", description="Start date. Supports date macros.")
    end_date: str = Field(default="", description="End date.")
    options: str = Field(default="")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class SectorSeriesInput(BaseModel):
    """Input for wind_get_sector_series (WSES)."""

    codes: str | list[str] = Field(
        ..., description="Sector codes. e.g. 'a001010100' (全部A股)"
    )
    fields: str = Field(..., description="Single field only. e.g. 'sec_close_avg'")
    begin_date: str = Field(default="-1M")
    end_date: str = Field(default="")
    options: str = Field(default="")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class SectorSnapshotInput(BaseModel):
    """Input for wind_get_sector_snapshot (WSEE)."""

    codes: str | list[str] = Field(..., description="Sector codes.")
    fields: str = Field(..., description="Single field only.")
    options: str = Field(default="")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class ScreenInput(BaseModel):
    """Input for wind_run_screen (WEQS)."""

    filter_name: str = Field(
        ..., description="Name of saved screening scheme in Wind terminal."
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class DynamicScreenInput(BaseModel):
    """Input for wind_dynamic_screen (WSS+WSET composite)."""

    universe: str = Field(
        ...,
        description=(
            "Universe source. Formats: "
            "'index:000300.SH' (沪深300成分), "
            "'index:000905.SH' (中证500), "
            "'sector:a001010100' (全部A股), "
            "'codes:600030.SH,000001.SZ,...' (custom list)"
        ),
    )
    fields: list[str] = Field(
        ...,
        description=(
            "Fields or FieldSet shortcuts. e.g. ['PRICE','VALUATION','pe_ttm','roe_ttm2']. "
            "FieldSet names are expanded automatically."
        ),
    )
    filters: list[dict] | None = Field(
        default=None,
        description=(
            "Filter conditions. Each dict: {'field': str, 'op': str, 'value': any}. "
            "Operators: gt, gte, lt, lte, eq, neq, between, in. "
            "Example: [{'field':'pe_ttm','op':'between','value':[5,30]}, "
            "{'field':'roe_ttm2','op':'gt','value':15}]"
        ),
    )
    rank_by: str | None = Field(default=None, description="Field to rank by.")
    rank_descending: bool = Field(
        default=True, description="Rank descending (True) or ascending (False)."
    )
    top_n: int | None = Field(
        default=None, description="Return only top N results after ranking."
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class EstimatesInput(BaseModel):
    """Input for wind_get_estimates."""

    codes: str | list[str] = Field(..., description="Security codes.")
    metrics: list[str] = Field(
        default=[
            "est_eps_fy1", "est_eps_fy2", "est_roe_fy1",
            "wrating_avg", "wrating_targetprice_avg",
            "est_eps_chg_1w", "est_eps_chg_1m", "est_eps_chg_3m",
        ],
        description="Estimate fields.",
    )
    options: str = Field(default="")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class HoldersInput(BaseModel):
    """Input for wind_get_holders."""

    codes: str | list[str] = Field(..., description="Security codes.")
    holder_type: str = Field(
        default="top10_holder",
        description="Type: 'top10_holder', 'top10_tradable_holder', 'fund_holder', 'institutional'",
    )
    options: str = Field(default="")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class StockConnectInput(BaseModel):
    """Input for wind_get_stock_connect."""

    codes: str | list[str] | None = Field(
        default=None, description="Security codes. None = full northbound summary."
    )
    begin_date: str = Field(default="-1M")
    end_date: str = Field(default="")
    options: str = Field(default="")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class EventCalendarInput(BaseModel):
    """Input for wind_get_calendar."""

    event_type: str = Field(
        ...,
        description=(
            "Event type: 'dividend' (分红派息), 'ipo' (新股), "
            "'restricted' (限售解禁), 'earnings' (业绩预告/快报)"
        ),
    )
    begin_date: str = Field(default="", description="Start date.")
    end_date: str = Field(default="", description="End date.")
    options: str = Field(default="")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class TradingDaysInput(BaseModel):
    """Input for wind_get_trading_days (tdays)."""

    begin_date: str = Field(..., description="Start date. Supports date macros.")
    end_date: str = Field(default="", description="End date.")
    day_type: DayType = Field(default=DayType.TRADING)
    period: Periodicity = Field(default=Periodicity.DAILY)
    calendar: TradingCalendar = Field(default=TradingCalendar.SSE)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class DateOffsetInput(BaseModel):
    """Input for wind_get_date_offset (tdaysoffset)."""

    offset: int = Field(..., description="Offset value. >0 forward, <0 backward.")
    begin_date: str = Field(default="", description="Reference date. Empty = today.")
    day_type: DayType = Field(default=DayType.TRADING)
    period: Periodicity = Field(default=Periodicity.DAILY)
    calendar: TradingCalendar = Field(default=TradingCalendar.SSE)


class DaysCountInput(BaseModel):
    """Input for wind_get_days_count (tdayscount)."""

    begin_date: str = Field(..., description="Start date.")
    end_date: str = Field(default="", description="End date.")
    day_type: DayType = Field(default=DayType.TRADING)
    calendar: TradingCalendar = Field(default=TradingCalendar.SSE)
