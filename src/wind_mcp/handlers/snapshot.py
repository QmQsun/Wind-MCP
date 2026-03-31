"""
WSS handler — cross-sectional snapshot data.

Wraps w.wss(codes, fields, options) for point-in-time multi-security multi-field queries.
"""

import logging
from ..core.session import WindSession
from ..core.cache import get_cache
from ..core.parser import parse_wss
from ..core.converter import ensure_wind_codes
from ..tools.field_expander import expand_fields
from ..models.inputs import SnapshotInput

logger = logging.getLogger(__name__)


def handle_snapshot(params: SnapshotInput) -> list[dict]:
    """
    Execute WSS query and return parsed results.

    Args:
        params: Validated SnapshotInput

    Returns:
        List of dicts, one per security, with code + field values.
    """
    # Auto-convert Bloomberg → Wind codes
    params.codes = ensure_wind_codes(params.codes)

    # Expand FieldSet shortcuts
    fields = expand_fields(params.fields)
    fields_str = ",".join(fields)

    # Normalize codes
    codes = params.codes if isinstance(params.codes, list) else [params.codes]
    codes_str = ",".join(codes)

    # Check cache
    cache = get_cache()
    cache_key_args = (codes_str, fields_str, params.options)
    cached = cache.get("wss", *cache_key_args)
    if cached is not None:
        logger.debug("Cache hit for WSS query")
        return cached

    # Call Wind API
    session = WindSession.get()
    logger.info(f"WSS: codes={codes_str}, fields={fields_str}, options={params.options}")

    result = session.w.wss(codes_str, fields_str, params.options)
    parsed = parse_wss(result)

    # Store in cache
    cache.set("wss", parsed, "snapshot", *cache_key_args)

    return parsed
