"""
Bloomberg → Wind ticker converter.

Three-layer fallback:
  1. Format detection — if already Wind format, pass through
  2. Rule engine — deterministic markets (CH, HK, JP, etc.)
  3. Static mapping — US exchange, indices, commodities, currencies
  4. Wind API lookup — last resort (not implemented in v1)

Usage:
    from wind_mcp.core.converter import ensure_wind_codes

    # Single code
    wind_code = ensure_wind_codes("700 HK Equity")  # → "00700.HK"

    # Multiple codes (str or list)
    wind_codes = ensure_wind_codes(["AAPL US Equity", "600030.SH", "700 HK Equity"])
    # → ["AAPL.O", "600030.SH", "00700.HK"]
"""

import re
import json
import os
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Wind format detection regex
# ──────────────────────────────────────────────
WIND_FORMAT_RE = re.compile(
    r"^[A-Za-z0-9]+\.(SH|SZ|BJ|HK|O|N|A|L|T|GI|HI|WI|CSI|SI|OF|SHF|DCE|CZC|CFE|INE)$",
    re.IGNORECASE,
)

BBG_FORMAT_RE = re.compile(
    r"^(.+?)\s+(US|CH|HK|JP|LN|GR|FP|IM|SM|AV|SW|AU|CN|IN|KS|TT|SP|ID|MK|TB|PM|BZ)\s+"
    r"(Equity|Index|Comdty|Curncy|Govt|Corp|Mtge|Muni|Pfd|Fund)$",
    re.IGNORECASE,
)

BBG_INDEX_RE = re.compile(r"^(.+?)\s+Index$", re.IGNORECASE)
BBG_COMDTY_RE = re.compile(r"^(.+?)\s+Comdty$", re.IGNORECASE)
BBG_CURNCY_RE = re.compile(r"^(.+?)\s+Curncy$", re.IGNORECASE)


def ensure_wind_codes(codes: str | list[str]) -> str | list[str]:
    """
    Convert code(s) to Wind format. Accepts Bloomberg or Wind format.
    Returns same type as input (str → str, list → list).
    """
    if isinstance(codes, str):
        if "," in codes:
            parts = [c.strip() for c in codes.split(",")]
            converted = [_convert_single(c) for c in parts]
            return ",".join(converted)
        return _convert_single(codes)
    else:
        return [_convert_single(c) for c in codes]


def _convert_single(code: str) -> str:
    """Convert a single ticker to Wind format."""
    code = code.strip()

    # Layer 0: Already Wind format?
    if WIND_FORMAT_RE.match(code):
        return code.upper() if code.split(".")[-1].upper() in ("SH", "SZ", "BJ") else code

    # Layer 1: Bloomberg Equity format
    m = BBG_FORMAT_RE.match(code)
    if m:
        ticker, market, yellow_key = m.group(1), m.group(2).upper(), m.group(3).lower()
        if yellow_key == "equity":
            return _convert_equity(ticker, market)

    # Layer 2: Bloomberg Index
    m = BBG_INDEX_RE.match(code)
    if m:
        idx_ticker = m.group(1).strip()
        return _convert_index(idx_ticker)

    # Layer 3: Bloomberg Commodity
    m = BBG_COMDTY_RE.match(code)
    if m:
        comdty_ticker = m.group(1).strip()
        return _convert_commodity(comdty_ticker)

    # Layer 4: Bloomberg Currency
    m = BBG_CURNCY_RE.match(code)
    if m:
        curncy_ticker = m.group(1).strip()
        return _convert_currency(curncy_ticker)

    # Layer 5: Unrecognized — return as-is
    logger.warning(f"Could not convert ticker '{code}' — passing through as-is")
    return code


# ──────────────────────────────────────────────
# Equity conversion (Rule engine)
# ──────────────────────────────────────────────

def _convert_equity(ticker: str, market: str) -> str:
    """Convert Bloomberg equity ticker to Wind format."""
    if market == "CH":
        return _convert_china_equity(ticker)
    elif market == "HK":
        return _convert_hk_equity(ticker)
    elif market == "US":
        return _convert_us_equity(ticker)
    elif market == "JP":
        return f"{ticker}.T"
    elif market == "LN":
        return f"{ticker}.L"
    elif market in ("GR", "GY"):
        return f"{ticker}.DE"
    elif market == "FP":
        return f"{ticker}.PA"
    elif market == "TT":
        return f"{ticker}.TW"
    elif market == "AU":
        return f"{ticker}.AX"
    elif market == "KS":
        return f"{ticker}.KS"
    elif market == "SP":
        return f"{ticker}.SI"
    elif market == "IN":
        return f"{ticker}.BOM"
    else:
        logger.warning(f"Unknown market '{market}' for ticker '{ticker}'")
        return f"{ticker}.{market}"


def _convert_china_equity(ticker: str) -> str:
    """
    Convert China A-share Bloomberg ticker to Wind.
    6XXXXX → .SH, 0XXXXX → .SZ, 3XXXXX → .SZ, 68XXXX → .SH,
    8XXXXX/4XXXXX → .BJ, 9XXXXX → .SH (B-share), 2XXXXX → .SZ (B-share)
    """
    ticker = ticker.zfill(6)
    first = ticker[0]
    first_two = ticker[:2]

    if first_two == "68":
        return f"{ticker}.SH"
    elif first == "6":
        return f"{ticker}.SH"
    elif first == "0":
        return f"{ticker}.SZ"
    elif first == "3":
        return f"{ticker}.SZ"
    elif first in ("8", "4"):
        return f"{ticker}.BJ"
    elif first == "9":
        return f"{ticker}.SH"
    elif first == "2":
        return f"{ticker}.SZ"
    else:
        logger.warning(f"Unknown China A-share pattern: {ticker}")
        return f"{ticker}.SH"


def _convert_hk_equity(ticker: str) -> str:
    """Convert HK ticker to Wind. Zero-pad to 5 digits + .HK."""
    ticker_num = ticker.lstrip("0") or "0"
    return f"{ticker_num.zfill(5)}.HK"


def _convert_us_equity(ticker: str) -> str:
    """Convert US equity ticker to Wind using static mapping."""
    mapping = _load_us_exchange_map()
    upper = ticker.upper()
    if upper in mapping:
        exchange = mapping[upper]
        return f"{upper}.{exchange}"
    logger.info(f"US ticker '{ticker}' not in mapping, defaulting to .O (NASDAQ)")
    return f"{upper}.O"


# ──────────────────────────────────────────────
# Index / Commodity / Currency conversion
# ──────────────────────────────────────────────

def _convert_index(ticker: str) -> str:
    mapping = _load_index_map()
    upper = ticker.upper().strip()
    if upper in mapping:
        return mapping[upper]
    logger.warning(f"Index '{ticker}' not in mapping")
    return f"{upper}.GI"


def _convert_commodity(ticker: str) -> str:
    mapping = _load_commodity_map()
    upper = ticker.upper().strip()
    if upper in mapping:
        return mapping[upper]
    logger.warning(f"Commodity '{ticker}' not in mapping")
    return ticker


def _convert_currency(ticker: str) -> str:
    mapping = _load_currency_map()
    upper = ticker.upper().strip()
    if upper in mapping:
        return mapping[upper]
    logger.warning(f"Currency '{ticker}' not in mapping")
    return ticker


# ──────────────────────────────────────────────
# Static mapping loaders (cached)
# ──────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_us_exchange_map() -> dict[str, str]:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "us_exchange_map.json")
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("us_exchange_map.json not found, using built-in defaults")
        return _BUILTIN_US_MAP


@lru_cache(maxsize=1)
def _load_index_map() -> dict[str, str]:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "index_map.json")
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return _BUILTIN_INDEX_MAP


@lru_cache(maxsize=1)
def _load_commodity_map() -> dict[str, str]:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "commodity_map.json")
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return _BUILTIN_COMMODITY_MAP


@lru_cache(maxsize=1)
def _load_currency_map() -> dict[str, str]:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "currency_map.json")
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return _BUILTIN_CURRENCY_MAP


# ──────────────────────────────────────────────
# Built-in mapping tables (fallback if JSON missing)
# ──────────────────────────────────────────────

_BUILTIN_US_MAP: dict[str, str] = {
    # Mega-cap Tech / AI Infra
    "AAPL": "O", "MSFT": "O", "GOOGL": "O", "GOOG": "O", "AMZN": "O",
    "META": "O", "NVDA": "O", "TSLA": "O", "AVGO": "O", "ORCL": "N",
    "CRM": "N", "AMD": "O", "INTC": "O", "QCOM": "O", "CSCO": "O",
    "SAP": "N", "IBM": "N", "ADBE": "O", "TXN": "O", "MU": "O",
    "AMAT": "O", "LRCX": "O", "KLAC": "O", "MRVL": "O", "SNPS": "O",
    "CDNS": "O", "PANW": "O", "CRWD": "O", "NET": "N", "ZS": "O",
    # Energy — Generation
    "CEG": "O", "VST": "N", "NRG": "N", "SO": "N", "DUK": "N",
    "NEE": "N", "AEP": "O", "D": "N", "EXC": "O", "SRE": "N",
    "XEL": "O", "ED": "N", "PCG": "N", "EIX": "N", "FE": "N",
    "ETR": "N", "PPL": "N", "WEC": "N", "ES": "N", "AES": "N",
    "OKE": "N", "WMB": "N", "KMI": "N", "EPD": "N", "ET": "N",
    "LNG": "A", "FSLR": "O", "ENPH": "O", "RUN": "O", "SEDG": "O",
    "PLUG": "O", "BE": "N",
    # Energy — Oil & Gas
    "XOM": "N", "CVX": "N", "COP": "N", "EOG": "N", "PXD": "N",
    "DVN": "N", "MPC": "N", "PSX": "N", "VLO": "N", "HES": "N",
    "OXY": "N", "HAL": "N", "SLB": "N", "BKR": "O",
    # Materials — Gold
    "NEM": "N", "GOLD": "N", "AEM": "N", "WPM": "N", "FNV": "N",
    "RGLD": "O", "KGC": "N", "AU": "N", "GFI": "N", "AGI": "N",
    "EGO": "N", "BTG": "N", "CDE": "N", "HL": "N", "PAAS": "O",
    # Materials — Copper
    "FCX": "N", "SCCO": "N", "TECK": "N", "HBM": "N", "IVN": "N",
    # Materials — Lithium
    "ALB": "N", "SQM": "N", "LTHM": "N", "LAC": "N", "PLL": "O",
    # Materials — Uranium
    "CCJ": "N", "UEC": "A", "DNN": "A", "NXE": "N", "LEU": "A",
    "UUUU": "A", "URA": "N", "URNM": "A",
    # Materials — Other
    "NUE": "N", "STLD": "O", "CLF": "N", "RS": "N", "AA": "N",
    "CENX": "N", "MP": "N", "LYB": "N", "DD": "N", "APD": "N",
    "LIN": "O", "ECL": "N", "SHW": "N", "VMC": "N", "MLM": "N",
    # Defense & Aerospace
    "LMT": "N", "RTX": "N", "NOC": "N", "GD": "N", "BA": "N",
    "LHX": "N", "HII": "N",
    # Financials
    "JPM": "N", "BAC": "N", "GS": "N", "MS": "N", "WFC": "N",
    "C": "N", "BLK": "N", "SCHW": "N", "BK": "N",
    # Healthcare
    "UNH": "N", "JNJ": "N", "LLY": "N", "PFE": "N", "ABT": "N",
    "TMO": "N", "ABBV": "N", "MRK": "N", "ISRG": "O", "DXCM": "O",
    "VEEV": "N", "TDOC": "N",
    # Major ETFs
    "SPY": "N", "QQQ": "O", "IWM": "N", "DIA": "N", "XLF": "N",
    "XLE": "N", "XLU": "N", "XLK": "N", "XLB": "N", "XLI": "N",
    "XLV": "N", "XLP": "N", "XLY": "N", "XLRE": "N",
    "GDX": "N", "GDXJ": "N", "SLV": "N", "GLD": "N", "USO": "N",
    "TLT": "O", "HYG": "N", "LQD": "N", "EEM": "N", "EFA": "N",
    "VTI": "N", "VEA": "N", "VWO": "N", "ARKK": "N",
    "SMH": "O", "SOXX": "O", "XBI": "N", "IBB": "O",
    # Auto / EV
    "GM": "N", "F": "N", "RIVN": "O", "LCID": "O", "NIO": "N",
    "XPEV": "N", "LI": "O",
    # Digital Ads
    "PINS": "N", "SNAP": "N", "TTD": "O", "RBLX": "N",
    # Misc
    "BRK/B": "N", "V": "N", "MA": "N", "COST": "O", "WMT": "N",
    "HD": "N", "DIS": "N", "NFLX": "O", "ABNB": "O", "UBER": "N",
    "LYFT": "O", "SQ": "N", "PYPL": "O", "SHOP": "N", "SE": "N",
    "BABA": "N", "JD": "O", "PDD": "O", "BIDU": "O",
}

_BUILTIN_INDEX_MAP: dict[str, str] = {
    # US
    "SPX": "SPX.GI", "INDU": "DJIA.GI", "NDX": "NDX.GI",
    "CCMP": "IXIC.GI", "RTY": "RUT.GI", "VIX": "VIX.GI",
    # China
    "SHCOMP": "000001.SH", "SZCOMP": "399001.SZ", "CSI300": "000300.SH",
    "CSI500": "000905.SH", "CSI1000": "000852.SH", "CHINEXT": "399006.SZ",
    "STAR50": "000688.SH", "SSE50": "000016.SH",
    # Hong Kong
    "HSI": "HSI.HI", "HSCEI": "HSCEI.HI", "HSTECH": "HSTECH.HI",
    # Japan
    "NKY": "N225.GI", "TPX": "TPX.GI",
    # Europe
    "SX5E": "SX5E.GI", "DAX": "DAX.GI", "UKX": "FTSE.GI", "CAC": "CAC.GI",
    # Asia ex-Japan
    "TWSE": "TWII.GI", "KOSPI": "KOSPI.GI", "AS51": "AS51.GI",
    "STI": "STI.GI", "SENSEX": "SENSEX.GI", "NIFTY": "NIFTY.GI",
    # Commodity indices
    "CRY": "CRB.GI", "BCOM": "BCOM.GI",
}

_BUILTIN_COMMODITY_MAP: dict[str, str] = {
    # Energy
    "CL1": "CL.NYM", "CO1": "B.IPE", "NG1": "NG.NYM",
    "HO1": "HO.NYM", "XB1": "RB.NYM",
    # Metals — Precious
    "GC1": "GC.CMX", "SI1": "SI.CMX", "PL1": "PL.NYM", "PA1": "PA.NYM",
    # Metals — Base (LME)
    "LMCADS03": "CA.LME", "LMAHDS03": "AH.LME", "LMZSDS03": "ZS.LME",
    "LMNIDS03": "NI.LME", "LMPBDS03": "PB.LME", "LMSNDS03": "SN.LME",
    # Ags
    "C 1": "C.CBT", "S 1": "S.CBT", "W 1": "W.CBT",
    "CT1": "CT.NYB", "KC1": "KC.NYB", "SB1": "SB.NYB",
    # China futures
    "SCF1": "SC.INE", "CUF1": "CU.SHF", "AUF1": "AU.SHF",
    "RBF1": "RB.SHF", "IF1": "IF.CFE",
}

_BUILTIN_CURRENCY_MAP: dict[str, str] = {
    "EUR": "EURUSD.FX", "GBP": "GBPUSD.FX", "JPY": "USDJPY.FX",
    "CNY": "USDCNY.FX", "CNH": "USDCNH.FX", "HKD": "USDHKD.FX",
    "AUD": "AUDUSD.FX", "CHF": "USDCHF.FX", "CAD": "USDCAD.FX",
    "KRW": "USDKRW.FX", "TWD": "USDTWD.FX", "SGD": "USDSGD.FX",
    "INR": "USDINR.FX", "BRL": "USDBRL.FX", "MXN": "USDMXN.FX",
    "DXY": "DXY.GI",
}


# ──────────────────────────────────────────────
# Reverse converter: Wind → Bloomberg
# ──────────────────────────────────────────────

def wind_to_bbg(code: str) -> str:
    """Best-effort Wind → Bloomberg conversion."""
    code = code.strip()
    if "." not in code:
        return code

    ticker, suffix = code.rsplit(".", 1)
    suffix = suffix.upper()

    if suffix in ("SH", "SZ", "BJ"):
        return f"{ticker} CH Equity"
    elif suffix == "HK":
        ticker_clean = ticker.lstrip("0") or "0"
        return f"{ticker_clean} HK Equity"
    elif suffix in ("O", "N", "A"):
        return f"{ticker} US Equity"
    elif suffix == "T":
        return f"{ticker} JP Equity"
    elif suffix == "L":
        return f"{ticker} LN Equity"
    else:
        return code
