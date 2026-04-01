"""
Input validation for Wind MCP.

Fail-fast on invalid codes, date ranges, and API constraints
before hitting the Wind API.
"""

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Wind code pattern: digits or letters + dot + exchange suffix
# Examples: 600030.SH, 000001.SZ, AAPL.O, 00700.HK, SPX.GI, GC.CMX
_WIND_CODE_RE = re.compile(r"^[A-Za-z0-9]+\.[A-Z]{1,4}$")

# EDB macro indicator pattern: M + digits
_EDB_CODE_RE = re.compile(r"^M\d+$")

# Sector code pattern: a + digits (Wind sector IDs)
_SECTOR_CODE_RE = re.compile(r"^[a-z]\d+$")

# Absolute date patterns
_DATE_ABSOLUTE_RE = re.compile(r"^\d{4}-?\d{2}-?\d{2}$")

# Wind date macros — relative offsets
_DATE_MACRO_RE = re.compile(
    r"^-?\d+(D|TD|W|M|Q|S|Y)$", re.IGNORECASE
)

# Wind special date macros
_SPECIAL_MACROS = {
    "ED", "SD", "LYR", "MRQ", "RYF", "LYE", "IPO",
    "LQ1", "LQ2", "LQ3", "RQ1", "RQ2", "RQ3",
    "RMF", "LME", "LHYE", "RHYF", "LWE", "RWF",
}

# Wind macro with arithmetic: e.g. ED-10d, LYR+1M
_MACRO_ARITHMETIC_RE = re.compile(
    r"^(" + "|".join(_SPECIAL_MACROS) + r")[+-]\d+[dDwWmMqQsSTY]+$"
)


def validate_wind_codes(codes: str | list[str]) -> list[str]:
    """
    Validate and normalize Wind security codes.

    Filters out invalid codes and logs warnings.
    Returns list of valid codes. Raises ValueError if all codes are invalid.
    """
    if isinstance(codes, str):
        codes = [c.strip() for c in codes.split(",") if c.strip()]

    valid = []
    invalid = []
    for code in codes:
        code = code.strip()
        if _WIND_CODE_RE.match(code):
            valid.append(code)
        else:
            invalid.append(code)

    if invalid:
        logger.warning(f"Invalid Wind codes filtered out: {invalid}")

    if not valid:
        raise ValueError(
            f"No valid Wind codes provided. Invalid: {invalid}. "
            f"Expected format: TICKER.EXCHANGE (e.g. 600030.SH, AAPL.O)"
        )
    return valid


def validate_edb_codes(codes: str | list[str]) -> list[str]:
    """Validate EDB macro indicator codes (M + digits)."""
    if isinstance(codes, str):
        codes = [c.strip() for c in codes.split(",") if c.strip()]

    valid = []
    invalid = []
    for code in codes:
        code = code.strip()
        if _EDB_CODE_RE.match(code):
            valid.append(code)
        else:
            invalid.append(code)

    if invalid:
        logger.warning(f"Invalid EDB codes filtered out: {invalid}")

    if not valid:
        raise ValueError(
            f"No valid EDB codes provided. Invalid: {invalid}. "
            f"Expected format: M followed by digits (e.g. M5567877)"
        )
    return valid


def validate_sector_codes(codes: str | list[str]) -> list[str]:
    """Validate sector codes (e.g. a001010100)."""
    if isinstance(codes, str):
        codes = [c.strip() for c in codes.split(",") if c.strip()]

    valid = []
    invalid = []
    for code in codes:
        code = code.strip()
        if _SECTOR_CODE_RE.match(code):
            valid.append(code)
        else:
            invalid.append(code)

    if invalid:
        logger.warning(f"Invalid sector codes filtered out: {invalid}")

    if not valid:
        raise ValueError(
            f"No valid sector codes provided. Invalid: {invalid}. "
            f"Expected format: lowercase letter + digits (e.g. a001010100)"
        )
    return valid


def is_valid_date(date_str: str) -> bool:
    """Check if a string is a valid Wind date (absolute, macro, or empty)."""
    if not date_str or date_str.strip() == "":
        return True  # Empty means "today"
    s = date_str.strip()
    if _DATE_ABSOLUTE_RE.match(s):
        return True
    if _DATE_MACRO_RE.match(s):
        return True
    if s.upper() in _SPECIAL_MACROS:
        return True
    if _MACRO_ARITHMETIC_RE.match(s):
        return True
    return False


def validate_date_range(begin_date: str, end_date: str) -> None:
    """
    Validate a date range.

    - Both dates must be valid Wind date formats.
    - If both are absolute dates, begin <= end.
    """
    if not is_valid_date(begin_date):
        raise ValueError(f"Invalid begin_date format: '{begin_date}'")
    if not is_valid_date(end_date):
        raise ValueError(f"Invalid end_date format: '{end_date}'")

    # Only check ordering for absolute dates
    begin_abs = _DATE_ABSOLUTE_RE.match(begin_date.strip()) if begin_date else None
    end_abs = _DATE_ABSOLUTE_RE.match(end_date.strip()) if end_date else None

    if begin_abs and end_abs:
        b = begin_date.strip().replace("-", "")
        e = end_date.strip().replace("-", "")
        if b > e:
            raise ValueError(
                f"begin_date ({begin_date}) is after end_date ({end_date})"
            )


def validate_single_field(fields: str, api_name: str) -> str:
    """
    Validate that only a single field is provided (for WSES/WSEE).

    Args:
        fields: The fields string from user input.
        api_name: API name for error message (e.g. "WSES", "WSEE").

    Returns:
        The single field string.

    Raises:
        ValueError: If multiple fields are provided.
    """
    if isinstance(fields, list):
        if len(fields) > 1:
            raise ValueError(
                f"{api_name} only supports a single indicator per call. "
                f"Got {len(fields)} fields: {fields}. "
                f"Please make separate calls for each field."
            )
        return fields[0] if fields else ""

    # Check for comma-separated multiple fields
    parts = [f.strip() for f in fields.split(",") if f.strip()]
    if len(parts) > 1:
        raise ValueError(
            f"{api_name} only supports a single indicator per call. "
            f"Got {len(parts)} fields: {parts}. "
            f"Please make separate calls for each field."
        )
    return fields.strip()


def validate_universe_format(universe: str) -> None:
    """Validate dynamic screen universe format."""
    valid_prefixes = ("index:", "sector:", "codes:")
    if not any(universe.startswith(p) for p in valid_prefixes):
        raise ValueError(
            f"Unknown universe format: '{universe}'. "
            f"Expected: 'index:CODE', 'sector:CODE', or 'codes:CODE1,CODE2,...'"
        )

    # Check that the value after prefix is non-empty
    _, _, value = universe.partition(":")
    if not value.strip():
        raise ValueError(
            f"Empty universe value in '{universe}'. "
            f"Provide codes after the prefix."
        )
