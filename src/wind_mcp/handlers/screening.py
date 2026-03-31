"""
Screening handlers.

1. handle_screen — run a saved WEQS screening scheme
2. handle_dynamic_screen — custom WSS+WSET composite screening
"""

import logging
from datetime import datetime
from ..core.session import WindSession
from ..core.cache import get_cache
from ..core.parser import parse_wset, parse_wss
from ..core.converter import ensure_wind_codes
from ..tools.field_expander import expand_fields
from ..models.inputs import ScreenInput, DynamicScreenInput

logger = logging.getLogger(__name__)


def handle_screen(params: ScreenInput) -> list[dict]:
    """Run a saved screening scheme from Wind terminal (WEQS)."""
    cache = get_cache()
    cache_key_args = (params.filter_name,)
    cached = cache.get("weqs", *cache_key_args)
    if cached is not None:
        return cached

    session = WindSession.get()
    logger.info(f"WEQS: filter_name={params.filter_name}")

    result = session.w.weqs(params.filter_name)
    parsed = parse_wset(result)

    cache.set("weqs", parsed, "screening", *cache_key_args)
    return parsed


def handle_dynamic_screen(params: DynamicScreenInput) -> list[dict]:
    """
    Custom dynamic screening.

    Workflow:
    1. Resolve universe → list of security codes
    2. Expand FieldSet shortcuts → flat field list
    3. WSS batch query all codes × all fields
    4. Apply filters in-memory
    5. Rank and slice top_n
    6. Return results
    """
    session = WindSession.get()
    today = datetime.now().strftime("%Y-%m-%d")

    # Step 1: Resolve universe
    if params.universe.startswith("index:"):
        index_code = params.universe.split(":", 1)[1]
        result = session.w.wset("IndexConstituent", f"date={today};windcode={index_code}")
        constituents = parse_wset(result)
        codes = [row.get("wind_code", row.get("code", "")) for row in constituents]
    elif params.universe.startswith("sector:"):
        sector_code = params.universe.split(":", 1)[1]
        result = session.w.wset("SectorConstituent", f"date={today};sectorId={sector_code}")
        constituents = parse_wset(result)
        codes = [row.get("wind_code", row.get("code", "")) for row in constituents]
    elif params.universe.startswith("codes:"):
        raw_codes = [c.strip() for c in params.universe.split(":", 1)[1].split(",")]
        codes = ensure_wind_codes(raw_codes)
    else:
        raise ValueError(f"Unknown universe format: {params.universe}")

    if not codes:
        return []

    # Step 2: Expand fields
    fields = expand_fields(params.fields)

    # Step 3: WSS batch query
    codes_str = ",".join(codes)
    fields_str = ",".join(fields)
    logger.info(f"Dynamic screen: {len(codes)} codes × {len(fields)} fields")

    result = session.w.wss(codes_str, fields_str)
    data = parse_wss(result)

    # Step 4: Apply filters
    if params.filters:
        data = _apply_filters(data, params.filters)

    # Step 5: Rank and slice
    if params.rank_by:
        data = sorted(
            data,
            key=lambda row: row.get(params.rank_by.lower(), 0) or 0,
            reverse=params.rank_descending,
        )

    if params.top_n:
        data = data[: params.top_n]

    return data


def _apply_filters(data: list[dict], filters: list[dict]) -> list[dict]:
    """Apply filter conditions to data rows."""
    result = data
    for f in filters:
        field = f["field"].lower()
        op = f["op"]
        value = f["value"]

        if op == "gt":
            result = [r for r in result if (r.get(field) is not None and r[field] > value)]
        elif op == "gte":
            result = [r for r in result if (r.get(field) is not None and r[field] >= value)]
        elif op == "lt":
            result = [r for r in result if (r.get(field) is not None and r[field] < value)]
        elif op == "lte":
            result = [r for r in result if (r.get(field) is not None and r[field] <= value)]
        elif op == "eq":
            result = [r for r in result if r.get(field) == value]
        elif op == "neq":
            result = [r for r in result if r.get(field) != value]
        elif op == "between":
            lo, hi = value[0], value[1]
            result = [
                r for r in result if (r.get(field) is not None and lo <= r[field] <= hi)
            ]
        elif op == "in":
            result = [r for r in result if r.get(field) in value]

    return result
