"""
EDB handler — macro economic data.

Wraps w.edb(codes, begin_date, end_date, options).
Codes are EDB indicator IDs, not security codes — no ticker conversion.
"""

import logging
from ..core.session import WindSession
from ..core.cache import get_cache
from ..core.parser import parse_edb
from ..models.inputs import MacroInput

logger = logging.getLogger(__name__)


def handle_macro(params: MacroInput) -> list[dict]:
    codes = params.codes if isinstance(params.codes, list) else [params.codes]
    codes_str = ",".join(codes)

    cache = get_cache()
    cache_key_args = (codes_str, params.begin_date, params.end_date, params.options)
    cached = cache.get("edb", *cache_key_args)
    if cached is not None:
        return cached

    session = WindSession.get()
    logger.info(f"EDB: codes={codes_str}, begin={params.begin_date}, end={params.end_date}")

    result = session.w.edb(codes_str, params.begin_date, params.end_date, params.options)
    parsed = parse_edb(result)

    cache.set("edb", parsed, "macro", *cache_key_args)
    return parsed
