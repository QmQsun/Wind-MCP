"""
Portfolio management handlers — WPF, WPS, WPD.

WPF: Portfolio report data (performance, market, attribution)
WPS: Portfolio snapshot (NAV, holdings, basic info)
WPD: Portfolio time series (NAV, return, drawdown over time)
"""

import logging
from ..core.session import WindSession
from ..core.cache import get_cache
from ..core.parser import parse_wset, parse_wss, parse_wsd
from ..core.executor import run_wind_sync
from ..models.inputs import (
    PortfolioReportInput, PortfolioSnapshotInput, PortfolioSeriesInput,
)

logger = logging.getLogger(__name__)


def handle_portfolio_report(params: PortfolioReportInput) -> list[dict]:
    """
    Get portfolio report data (WPF).

    w.wpf(productname, tablename, options)
    Returns tabular report data (same structure as WSET).
    """
    cache = get_cache()
    cache_key_args = (params.product_name, params.table_name, params.options)
    cached = cache.get("wpf", *cache_key_args)
    if cached is not None:
        return cached

    session = WindSession.get()
    logger.info(f"WPF: product={params.product_name}, table={params.table_name}")

    result = run_wind_sync(
        session.w.wpf, params.product_name, params.table_name, params.options
    )
    parsed = parse_wset(result)

    cache.set("wpf", parsed, "portfolio", *cache_key_args)
    return parsed


def handle_portfolio_snapshot(params: PortfolioSnapshotInput) -> list[dict]:
    """
    Get portfolio snapshot data (WPS).

    w.wps(PortfolioName, fields, options)
    Returns cross-sectional data (same structure as WSS).
    """
    cache = get_cache()
    cache_key_args = (params.portfolio_name, params.fields, params.options)
    cached = cache.get("wps", *cache_key_args)
    if cached is not None:
        return cached

    session = WindSession.get()
    logger.info(f"WPS: portfolio={params.portfolio_name}, fields={params.fields}")

    result = run_wind_sync(
        session.w.wps, params.portfolio_name, params.fields, params.options
    )
    parsed = parse_wss(result)

    cache.set("wps", parsed, "portfolio", *cache_key_args)
    return parsed


def handle_portfolio_series(params: PortfolioSeriesInput) -> list[dict]:
    """
    Get portfolio time series data (WPD).

    w.wpd(PortfolioName, fields, beginTime, endTime, options)
    Returns time series data (same structure as WSD).
    """
    cache = get_cache()
    cache_key_args = (
        params.portfolio_name, params.fields,
        params.begin_date, params.end_date, params.options,
    )
    cached = cache.get("wpd", *cache_key_args)
    if cached is not None:
        return cached

    session = WindSession.get()
    logger.info(
        f"WPD: portfolio={params.portfolio_name}, fields={params.fields}, "
        f"begin={params.begin_date}"
    )

    result = run_wind_sync(
        session.w.wpd, params.portfolio_name, params.fields,
        params.begin_date, params.end_date, params.options,
    )
    parsed = parse_wsd(result)

    cache.set("wpd", parsed, "portfolio", *cache_key_args)
    return parsed
