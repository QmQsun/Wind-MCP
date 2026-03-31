"""
WST handler — intraday tick data.

Wraps w.wst(codes, fields, begin_time, end_time, options).
Single security only.
"""

import logging
from ..core.session import WindSession
from ..core.cache import get_cache
from ..core.parser import parse_wst
from ..core.converter import ensure_wind_codes
from ..tools.field_expander import expand_fields
from ..models.inputs import TicksInput

logger = logging.getLogger(__name__)


def handle_ticks(params: TicksInput) -> list[dict]:
    params.codes = ensure_wind_codes(params.codes)

    fields = expand_fields(params.fields)
    fields_str = ",".join(fields)

    cache = get_cache()
    cache_key_args = (params.codes, fields_str, params.begin_time, params.end_time, params.options)
    cached = cache.get("wst", *cache_key_args)
    if cached is not None:
        return cached

    session = WindSession.get()
    logger.info(f"WST: code={params.codes}, fields={fields_str}, begin={params.begin_time}")

    result = session.w.wst(params.codes, fields_str, params.begin_time, params.end_time, params.options)
    parsed = parse_wst(result)

    cache.set("wst", parsed, "ticks", *cache_key_args)
    return parsed
