"""
WSQ handler — real-time quote snapshot.

Wraps w.wsq(codes, fields). No options parameter.
Uses snapshot mode (no callback).
"""

import logging
from ..core.session import WindSession
from ..core.cache import get_cache
from ..core.parser import parse_wsq
from ..core.converter import ensure_wind_codes
from ..tools.field_expander import expand_fields
from ..models.inputs import RealtimeInput

logger = logging.getLogger(__name__)


def handle_realtime(params: RealtimeInput) -> list[dict]:
    params.codes = ensure_wind_codes(params.codes)

    fields = expand_fields(params.fields)
    fields_str = ",".join(fields)

    codes = params.codes if isinstance(params.codes, list) else [params.codes]
    codes_str = ",".join(codes)

    cache = get_cache()
    cache_key_args = (codes_str, fields_str)
    cached = cache.get("wsq", *cache_key_args)
    if cached is not None:
        return cached

    session = WindSession.get()
    logger.info(f"WSQ: codes={codes_str}, fields={fields_str}")

    # WSQ takes only codes and fields, no options
    result = session.w.wsq(codes_str, fields_str)
    parsed = parse_wsq(result)

    cache.set("wsq", parsed, "realtime", *cache_key_args)
    return parsed
