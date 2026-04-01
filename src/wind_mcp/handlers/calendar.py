"""
Event calendar handler (WSET-based).

Routes WSET table by event_type:
- dividend → DividendHistory
- ipo → IPOEvent
- restricted → RestrictedStock
- earnings → earnings-related WSET table
"""

import logging
from ..core.session import WindSession
from ..core.cache import get_cache
from ..core.parser import parse_wset
from ..core.executor import run_wind_sync
from ..models.inputs import EventCalendarInput
from ..utils import today_str

logger = logging.getLogger(__name__)

_EVENT_TABLE_MAP = {
    "dividend": "DividendHistory",
    "ipo": "IPOEvent",
    "restricted": "RestrictedStock",
    "earnings": "EarningsReport",
}


def handle_calendar(params: EventCalendarInput) -> list[dict]:
    table_name = _EVENT_TABLE_MAP.get(params.event_type)
    if not table_name:
        raise ValueError(
            f"Unknown event_type: {params.event_type}. "
            f"Supported: {list(_EVENT_TABLE_MAP.keys())}"
        )

    # Build options
    options = params.options
    if not options:
        begin = params.begin_date or today_str()
        end = params.end_date or today_str()
        options = f"startdate={begin};enddate={end}"

    cache = get_cache()
    cache_key_args = (table_name, options)
    cached = cache.get("calendar_wset", *cache_key_args)
    if cached is not None:
        return cached

    session = WindSession.get()
    logger.info(f"Calendar WSET: table={table_name}, options={options}")

    result = run_wind_sync(session.w.wset, table_name, options)
    parsed = parse_wset(result)

    cache.set("calendar_wset", parsed, "dataset", *cache_key_args)
    return parsed
