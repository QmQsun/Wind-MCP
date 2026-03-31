"""
Consensus estimates handler.

Thin wrapper around WSS with estimate-specific fields.
"""

import logging
from ..core.session import WindSession
from ..core.cache import get_cache
from ..core.parser import parse_wss
from ..core.converter import ensure_wind_codes
from ..models.inputs import EstimatesInput

logger = logging.getLogger(__name__)


def handle_estimates(params: EstimatesInput) -> list[dict]:
    params.codes = ensure_wind_codes(params.codes)

    codes = params.codes if isinstance(params.codes, list) else [params.codes]
    codes_str = ",".join(codes)
    fields_str = ",".join(params.metrics)

    cache = get_cache()
    cache_key_args = (codes_str, fields_str, params.options)
    cached = cache.get("estimates", *cache_key_args)
    if cached is not None:
        return cached

    session = WindSession.get()
    logger.info(f"Estimates WSS: codes={codes_str}, fields={fields_str}")

    result = session.w.wss(codes_str, fields_str, params.options)
    parsed = parse_wss(result)

    cache.set("estimates", parsed, "estimates", *cache_key_args)
    return parsed
