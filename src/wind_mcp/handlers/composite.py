"""
Composite handlers — multi-source aggregation tools.

wind_company_profile: One-stop company overview combining
snapshot, estimates, holders, and recent price data.
"""

import logging
from ..core.session import WindSession
from ..core.cache import get_cache
from ..core.parser import parse_wss, parse_wsd
from ..core.converter import ensure_wind_codes
from ..core.executor import run_wind_sync
from ..models.inputs import CompanyProfileInput

logger = logging.getLogger(__name__)

# Fields for each data section
_PROFILE_FIELDS = "sec_name,close,pct_chg,mkt_cap_ard,pe_ttm,pb_lf,ps_ttm,roe_ttm2,profit_ttm,revenue_ttm,dividendyield2"
_ESTIMATE_FIELDS = "est_eps_fy1,est_eps_fy2,est_roe_fy1,wrating_avg,wrating_targetprice_avg"
_HOLDER_FIELDS = "holder_name,holder_pct"


def handle_company_profile(params: CompanyProfileInput) -> dict:
    """
    Aggregate company profile from multiple Wind API calls.

    Returns a dict with sections: basic, estimates, price_history.
    """
    codes = ensure_wind_codes([params.codes])[0]

    session = WindSession.get()
    result = {}

    # 1. Basic snapshot (WSS)
    cache = get_cache()
    cache_key = ("company_profile", codes)
    cached = cache.get("company_profile", *cache_key)
    if cached is not None:
        return cached

    logger.info(f"Company profile: {codes}")

    try:
        wss_result = run_wind_sync(session.w.wss, codes, _PROFILE_FIELDS)
        basic = parse_wss(wss_result)
        result["basic"] = basic[0] if basic else {}
    except Exception as e:
        logger.warning(f"Failed to get basic data for {codes}: {e}")
        result["basic"] = {"code": codes, "error": str(e)}

    # 2. Consensus estimates (WSS)
    try:
        est_result = run_wind_sync(session.w.wss, codes, _ESTIMATE_FIELDS)
        estimates = parse_wss(est_result)
        result["estimates"] = estimates[0] if estimates else {}
    except Exception as e:
        logger.warning(f"Failed to get estimates for {codes}: {e}")
        result["estimates"] = {"error": str(e)}

    # 3. Recent price history (WSD, last 20 trading days)
    try:
        wsd_result = run_wind_sync(
            session.w.wsd, codes, "close,pct_chg,volume,amt", "-20TD", ""
        )
        result["price_history"] = parse_wsd(wsd_result)
    except Exception as e:
        logger.warning(f"Failed to get price history for {codes}: {e}")
        result["price_history"] = []

    cache.set("company_profile", result, "snapshot", *cache_key)
    return result
