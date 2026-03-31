"""
WSI handler — minute-level K-line data.

Wraps w.wsi(codes, fields, begin_time, end_time, options).
"""

import logging
from ..core.session import WindSession
from ..core.cache import get_cache
from ..core.parser import parse_wsi
from ..core.converter import ensure_wind_codes
from ..tools.field_expander import expand_fields
from ..models.inputs import MinuteBarsInput

logger = logging.getLogger(__name__)


def handle_minute_bars(params: MinuteBarsInput) -> list[dict]:
    params.codes = ensure_wind_codes(params.codes)

    fields = expand_fields(params.fields)
    fields_str = ",".join(fields)

    codes = params.codes if isinstance(params.codes, list) else [params.codes]
    codes_str = ",".join(codes)

    cache = get_cache()
    cache_key_args = (codes_str, fields_str, params.begin_time, params.end_time, params.options)
    cached = cache.get("wsi", *cache_key_args)
    if cached is not None:
        return cached

    session = WindSession.get()
    logger.info(f"WSI: codes={codes_str}, fields={fields_str}, begin={params.begin_time}")

    result = session.w.wsi(codes_str, fields_str, params.begin_time, params.end_time, params.options)
    parsed = parse_wsi(result)

    cache.set("wsi", parsed, "minute_bars", *cache_key_args)
    return parsed
