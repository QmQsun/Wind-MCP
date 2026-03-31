"""
Shareholder data handler.

Routes by holder_type:
- top10_holder / top10_tradable_holder → WSS with holder fields
- fund_holder / institutional → WSET-based
"""

import logging
from ..core.session import WindSession
from ..core.cache import get_cache
from ..core.parser import parse_wss, parse_wset
from ..core.converter import ensure_wind_codes
from ..models.inputs import HoldersInput

logger = logging.getLogger(__name__)

# WSS fields for top holder queries
_TOP_HOLDER_FIELDS = {
    "top10_holder": "holder_name,holder_quantity,holder_pct,holder_holdchange",
    "top10_tradable_holder": "holder_name,holder_quantity,holder_pct,holder_holdchange",
}


def handle_holders(params: HoldersInput) -> list[dict]:
    params.codes = ensure_wind_codes(params.codes)

    codes = params.codes if isinstance(params.codes, list) else [params.codes]
    codes_str = ",".join(codes)

    cache = get_cache()
    cache_key_args = (codes_str, params.holder_type, params.options)
    cached = cache.get("holders", *cache_key_args)
    if cached is not None:
        return cached

    session = WindSession.get()

    if params.holder_type in _TOP_HOLDER_FIELDS:
        fields_str = _TOP_HOLDER_FIELDS[params.holder_type]
        options = params.options or ""
        if params.holder_type == "top10_tradable_holder" and "holderType" not in options:
            options = f"holderType=tradable;{options}" if options else "holderType=tradable"

        logger.info(f"Holders WSS: codes={codes_str}, type={params.holder_type}")
        result = session.w.wss(codes_str, fields_str, options)
        parsed = parse_wss(result)
    elif params.holder_type == "fund_holder":
        logger.info(f"Holders WSET FundPortfolio: codes={codes_str}")
        options = f"windcode={codes_str}" if not params.options else params.options
        result = session.w.wset("FundPortfolio", options)
        parsed = parse_wset(result)
    elif params.holder_type == "institutional":
        logger.info(f"Holders WSS institutional: codes={codes_str}")
        fields_str = "holder_institutionnum,holder_institution_pct,holder_fundnum,holder_fund_pct"
        result = session.w.wss(codes_str, fields_str, params.options)
        parsed = parse_wss(result)
    else:
        raise ValueError(f"Unknown holder_type: {params.holder_type}")

    cache.set("holders", parsed, "holders", *cache_key_args)
    return parsed
