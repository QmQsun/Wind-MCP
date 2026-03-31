"""
WSES + WSEE handler — sector-level data.

WSES: sector time series (e.g., average PE over time)
WSEE: sector cross-sectional snapshot
"""

import logging
from ..core.session import WindSession
from ..core.cache import get_cache
from ..core.parser import parse_wses, parse_wsee
from ..models.inputs import SectorSeriesInput, SectorSnapshotInput

logger = logging.getLogger(__name__)


def handle_sector_series(params: SectorSeriesInput) -> list[dict]:
    codes = params.codes if isinstance(params.codes, list) else [params.codes]
    codes_str = ",".join(codes)

    cache = get_cache()
    cache_key_args = (codes_str, params.fields, params.begin_date, params.end_date, params.options)
    cached = cache.get("wses", *cache_key_args)
    if cached is not None:
        return cached

    session = WindSession.get()
    logger.info(f"WSES: codes={codes_str}, field={params.fields}, begin={params.begin_date}")

    result = session.w.wses(codes_str, params.fields, params.begin_date, params.end_date, params.options)
    parsed = parse_wses(result)

    cache.set("wses", parsed, "sector", *cache_key_args)
    return parsed


def handle_sector_snapshot(params: SectorSnapshotInput) -> list[dict]:
    codes = params.codes if isinstance(params.codes, list) else [params.codes]
    codes_str = ",".join(codes)

    cache = get_cache()
    cache_key_args = (codes_str, params.fields, params.options)
    cached = cache.get("wsee", *cache_key_args)
    if cached is not None:
        return cached

    session = WindSession.get()
    logger.info(f"WSEE: codes={codes_str}, field={params.fields}")

    result = session.w.wsee(codes_str, params.fields, params.options)
    parsed = parse_wsee(result)

    cache.set("wsee", parsed, "sector", *cache_key_args)
    return parsed
