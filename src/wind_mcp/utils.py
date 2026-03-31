"""
Date macro helpers and code validators.
"""

from datetime import datetime


def today_str() -> str:
    """Return today's date as YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


def normalize_date(date_str: str) -> str:
    """
    Normalize date string. Wind macros (e.g., '-1M', 'LYR') are passed through.
    Converts YYYYMMDD to YYYY-MM-DD if needed.
    """
    if not date_str:
        return today_str()

    # Wind date macros — pass through
    if date_str.startswith("-") or date_str.startswith("+"):
        return date_str
    if date_str.upper() in (
        "ED", "SD", "LYR", "LQ1", "LQ2", "LQ3", "MRQ",
        "RYF", "RMF", "LME", "LYE", "IPO",
    ):
        return date_str

    # YYYYMMDD → YYYY-MM-DD
    if len(date_str) == 8 and date_str.isdigit():
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

    return date_str


def validate_wind_code(code: str) -> bool:
    """Basic validation of Wind security code format."""
    if not code or "." not in code:
        return False
    parts = code.rsplit(".", 1)
    return len(parts) == 2 and len(parts[1]) >= 1
