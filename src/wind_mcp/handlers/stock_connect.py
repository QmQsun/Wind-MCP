"""
Stock Connect (沪深港通) handler.

- When codes is None: WSET "StockConnect" for full northbound summary
- When codes provided: WSS with northbound holding fields
"""

import logging
from ..core.session import WindSession
from ..core.cache import get_cache
from ..core.parser import parse_wss, parse_wset
from ..core.converter import ensure_wind_codes
from ..core.executor import run_wind_sync
from ..models.inputs import StockConnectInput
from ..utils import today_str

logger = logging.getLogger(__name__)


def handle_stock_connect(params: StockConnectInput) -> list[dict]:
    cache = get_cache()

    if params.codes is None:
        # Full northbound summary via WSET
        options = params.options or f"date={today_str()}"
        cache_key_args = ("StockConnect", options)
        cached = cache.get("stock_connect_wset", *cache_key_args)
        if cached is not None:
            return cached

        session = WindSession.get()
        logger.info(f"StockConnect WSET: options={options}")
        result = run_wind_sync(session.w.wset, "StockConnect", options)
        parsed = parse_wset(result)

        cache.set("stock_connect_wset", parsed, "dataset", *cache_key_args)
        return parsed
    else:
        # Individual stock northbound holdings via WSS
        params.codes = ensure_wind_codes(params.codes)
        codes = params.codes if isinstance(params.codes, list) else [params.codes]
        codes_str = ",".join(codes)

        fields_str = "share_hk_hold,ratio_hk_hold,share_hk_hold_chg_1d,share_hk_hold_chg_5d"

        cache_key_args = (codes_str, fields_str, params.options)
        cached = cache.get("stock_connect_wss", *cache_key_args)
        if cached is not None:
            return cached

        session = WindSession.get()
        logger.info(f"StockConnect WSS: codes={codes_str}")
        result = run_wind_sync(session.w.wss, codes_str, fields_str, params.options)
        parsed = parse_wss(result)

        cache.set("stock_connect_wss", parsed, "snapshot", *cache_key_args)
        return parsed
