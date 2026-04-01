"""
WSD handler — daily time series data.

Wraps w.wsd(codes, fields, begin_date, end_date, options).
"""

import logging
from ..core.session import WindSession
from ..core.cache import get_cache
from ..core.parser import parse_wsd
from ..core.converter import ensure_wind_codes
from ..core.executor import run_wind_sync
from ..tools.field_expander import expand_fields
from ..models.inputs import HistoricalInput

logger = logging.getLogger(__name__)


def handle_historical(params: HistoricalInput) -> list[dict]:
    # Auto-convert Bloomberg → Wind codes
    params.codes = ensure_wind_codes(params.codes)

    fields = expand_fields(params.fields)
    fields_str = ",".join(fields)

    codes = params.codes if isinstance(params.codes, list) else [params.codes]
    codes_str = ",".join(codes)

    cache = get_cache()
    cache_key_args = (codes_str, fields_str, params.begin_date, params.end_date, params.options)
    cached = cache.get("wsd", *cache_key_args)
    if cached is not None:
        return cached

    session = WindSession.get()
    logger.info(
        f"WSD: codes={codes_str}, fields={fields_str}, "
        f"begin={params.begin_date}, end={params.end_date}"
    )

    result = run_wind_sync(session.w.wsd, codes_str, fields_str, params.begin_date, params.end_date, params.options)
    parsed = parse_wsd(result)

    cache.set("wsd", parsed, "historical", *cache_key_args)
    return parsed
