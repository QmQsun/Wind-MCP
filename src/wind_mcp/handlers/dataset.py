"""
WSET handler — dataset/report data.

Wraps w.wset(table_name, options). No field expansion.
"""

import logging
from ..core.session import WindSession
from ..core.cache import get_cache
from ..core.parser import parse_wset
from ..models.inputs import DatasetInput

logger = logging.getLogger(__name__)


def handle_dataset(params: DatasetInput) -> list[dict]:
    cache = get_cache()
    cache_key_args = (params.table_name, params.options)
    cached = cache.get("wset", *cache_key_args)
    if cached is not None:
        return cached

    session = WindSession.get()
    logger.info(f"WSET: table={params.table_name}, options={params.options}")

    result = session.w.wset(params.table_name, params.options)
    parsed = parse_wset(result)

    cache.set("wset", parsed, "dataset", *cache_key_args)
    return parsed
