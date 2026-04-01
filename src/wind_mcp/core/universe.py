"""
Universe resolution — extract security lists from index/sector/codes specs.

Extracted from handlers/screening.py for reuse by composite tools.
"""

import logging
from datetime import datetime

from .session import WindSession
from .parser import parse_wset
from .converter import ensure_wind_codes
from .executor import run_wind_sync

logger = logging.getLogger(__name__)


def resolve_universe(spec: str, date: str | None = None) -> list[str]:
    """
    Resolve a universe specification to a list of Wind security codes.

    Formats:
        'index:000300.SH'  → CSI 300 constituents
        'sector:a001010100' → all A-shares
        'codes:600030.SH,000001.SZ' → explicit list

    Args:
        spec: Universe specification string.
        date: Reference date (default: today).

    Returns:
        List of Wind security codes.
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    session = WindSession.get()

    if spec.startswith("index:"):
        index_code = spec.split(":", 1)[1].strip()
        result = run_wind_sync(
            session.w.wset, "IndexConstituent",
            f"date={date};windcode={index_code}"
        )
        constituents = parse_wset(result)
        return [row.get("wind_code", row.get("code", "")) for row in constituents]

    elif spec.startswith("sector:"):
        sector_code = spec.split(":", 1)[1].strip()
        result = run_wind_sync(
            session.w.wset, "SectorConstituent",
            f"date={date};sectorId={sector_code}"
        )
        constituents = parse_wset(result)
        return [row.get("wind_code", row.get("code", "")) for row in constituents]

    elif spec.startswith("codes:"):
        raw_codes = [c.strip() for c in spec.split(":", 1)[1].split(",") if c.strip()]
        return ensure_wind_codes(raw_codes)

    else:
        raise ValueError(f"Unknown universe format: {spec}")
