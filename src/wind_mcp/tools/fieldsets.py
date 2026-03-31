"""
Wind-native FieldSet definitions.

Usage: Users can pass FieldSet names (e.g., "PRICE", "VALUATION") instead of
individual field names. The field_expander module resolves these to actual
Wind field mnemonics.

NOTE: Verify all field names using Wind Code Generator (CG) before deployment.
Some fields may vary by Wind subscription tier.
"""

FIELDSETS: dict[str, list[str] | None] = {
    # === Market Data ===
    "PRICE": [
        "open", "high", "low", "close", "volume", "amt",
        "pct_chg",
    ],

    "MOMENTUM": [
        "pct_chg",
        "pct_chg_5d",
        "pct_chg_1m",
        "pct_chg_3m",
        "pct_chg_6m",
        "pct_chg_1y",
        "pct_chg_ytd",
    ],

    "VOLUME_PROFILE": [
        "volume",
        "amt",
        "turn",
        "free_turn",
        "volume_ratio",
    ],

    # === Valuation ===
    "VALUATION": [
        "pe_ttm",
        "pb_lf",
        "ps_ttm",
        "pcf_ocf_ttm",
        "ev2_to_ebitda",
        "val_mv",
        "mkt_freeshares_val",
    ],

    "VALUATION_EXTENDED": [
        "pe_ttm", "pb_lf", "ps_ttm", "pcf_ocf_ttm",
        "ev2_to_ebitda", "dividendyield2",
        "pe_est_fy1",
    ],

    # === Fundamentals ===
    "PROFITABILITY": [
        "roe_ttm2",
        "roa_ttm2",
        "grossprofitmargin_ttm2",
        "operatingprofitmargin_ttm2",
        "netprofitmargin_ttm2",
        "roic_ttm",
    ],

    "GROWTH": [
        "yoy_or",
        "yoyprofit",
        "yoynetprofit",
        "yoyeps_basic",
        "qfa_yoy_or",
        "qfa_yoynetprofit",
    ],

    "BALANCE_SHEET": [
        "debttoassets",
        "assettoequity",
        "current",
        "quick",
        "cashtocurrentdebt",
    ],

    "CASH_FLOW": [
        "ocfps",
        "fcfps",
        "ocf_to_or",
        "ocf_to_profit",
    ],

    # === Technical ===
    "TECHNICAL": [
        "rsi",
        "macd_dif",
        "macd_dea",
        "macd_macd",
        "bbands_upper",
        "bbands_lower",
        "ma_5",
        "ma_20",
        "ma_60",
    ],

    # === Analyst Estimates ===
    "ANALYST": [
        "wrating_avg",
        "wrating_targetprice_avg",
        "wrating_numofbuy",
        "wrating_numofoutperform",
        "wrating_numofhold",
        "est_eps_fy1",
        "est_eps_fy2",
        "est_roe_fy1",
    ],

    "ESTIMATE_REVISIONS": [
        "est_eps_chg_1w",
        "est_eps_chg_1m",
        "est_eps_chg_3m",
        "est_or_chg_1m",
    ],

    # === Classification ===
    "SECTOR": [
        "industry_sw",
        "industry_sw_lv2",
        "industry_sw_lv3",
        "industry_gics",
        "industry_gics_lv2",
    ],

    # === A-Share Special ===
    "NORTHBOUND": [
        "share_hk_hold",
        "ratio_hk_hold",
        "share_hk_hold_chg_1d",
        "share_hk_hold_chg_5d",
    ],

    "MARGIN": [
        "margin_longbalance",
        "margin_shortbalance",
        "margin_netbalance",
    ],

    # === Risk ===
    "RISK": [
        "beta_100w",
        "stdevry_20d",
        "stdevry_60d",
        "mkt_freeshares_val",
    ],

    # === Composite ===
    "SCREENING_FULL": None,  # Special: expands to PRICE+VALUATION+PROFITABILITY+GROWTH+MOMENTUM+ANALYST+SECTOR
}


def get_screening_full() -> list[str]:
    """Expand SCREENING_FULL to all component fields."""
    full = []
    for key in ["PRICE", "VALUATION", "PROFITABILITY", "GROWTH", "MOMENTUM", "ANALYST", "SECTOR"]:
        full.extend(FIELDSETS[key])
    return list(dict.fromkeys(full))  # deduplicate preserving order
