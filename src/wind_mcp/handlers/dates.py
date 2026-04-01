"""
Trading date utilities handler.

Three sub-functions:
- tdays: get trading day sequence
- tdaysoffset: get date N days before/after
- tdayscount: count trading days between dates
"""

import logging
from ..core.session import WindSession
from ..core.cache import get_cache
from ..core.parser import parse_tdays, parse_tdaysoffset, parse_tdayscount
from ..core.executor import run_wind_sync
from ..models.inputs import TradingDaysInput, DateOffsetInput, DaysCountInput
from ..utils import today_str

logger = logging.getLogger(__name__)


def handle_trading_days(params: TradingDaysInput) -> list[str]:
    end_date = params.end_date or today_str()

    options = f"Days={params.day_type.value};Period={params.period.value};TradingCalendar={params.calendar.value}"

    cache = get_cache()
    cache_key_args = (params.begin_date, end_date, options)
    cached = cache.get("tdays", *cache_key_args)
    if cached is not None:
        return cached

    session = WindSession.get()
    logger.info(f"tdays: begin={params.begin_date}, end={end_date}")

    result = run_wind_sync(session.w.tdays, params.begin_date, end_date, options)
    parsed = parse_tdays(result)

    cache.set("tdays", parsed, "dates", *cache_key_args)
    return parsed


def handle_date_offset(params: DateOffsetInput) -> str:
    begin_date = params.begin_date or today_str()

    options = f"Days={params.day_type.value};Period={params.period.value};TradingCalendar={params.calendar.value}"

    cache = get_cache()
    cache_key_args = (params.offset, begin_date, options)
    cached = cache.get("tdaysoffset", *cache_key_args)
    if cached is not None:
        return cached

    session = WindSession.get()
    logger.info(f"tdaysoffset: offset={params.offset}, begin={begin_date}")

    result = run_wind_sync(session.w.tdaysoffset, params.offset, begin_date, options)
    parsed = parse_tdaysoffset(result)

    cache.set("tdaysoffset", parsed, "dates", *cache_key_args)
    return parsed


def handle_days_count(params: DaysCountInput) -> int:
    end_date = params.end_date or today_str()

    options = f"Days={params.day_type.value};TradingCalendar={params.calendar.value}"

    cache = get_cache()
    cache_key_args = (params.begin_date, end_date, options)
    cached = cache.get("tdayscount", *cache_key_args)
    if cached is not None:
        return cached

    session = WindSession.get()
    logger.info(f"tdayscount: begin={params.begin_date}, end={end_date}")

    result = run_wind_sync(session.w.tdayscount, params.begin_date, end_date, options)
    parsed = parse_tdayscount(result)

    cache.set("tdayscount", parsed, "dates", *cache_key_args)
    return parsed
