"""
TTL-based cache with data-type-aware expiration.

Cache keys are built from: (function_name, args_tuple, frozen_options)
"""

import time
import hashlib
import json
from typing import Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# TTL in seconds, by data category
CACHE_TTL = {
    "realtime": 30,        # WSQ — near real-time
    "snapshot": 300,       # WSS — 5 minutes
    "historical": 43200,   # WSD — 12 hours (EOD data stable)
    "minute_bars": 300,    # WSI — 5 minutes
    "ticks": 60,           # WST — 1 minute
    "dataset": 86400,      # WSET — 24 hours
    "macro": 86400,        # EDB — 24 hours
    "sector": 86400,       # WSES/WSEE — 24 hours
    "screening": 600,      # WEQS — 10 minutes
    "estimates": 14400,    # Consensus — 4 hours
    "holders": 86400,      # Shareholder data — 24 hours
    "dates": 86400,        # Trading calendar — 24 hours
    "static": 86400,       # Rarely changes — 24 hours
}


@dataclass
class CacheEntry:
    data: Any
    timestamp: float
    ttl: float


class WindCache:
    """Simple in-memory TTL cache."""

    def __init__(self):
        self._store: dict[str, CacheEntry] = {}
        self._hits: int = 0
        self._misses: int = 0

    def _make_key(self, func_name: str, *args, **kwargs) -> str:
        raw = json.dumps(
            {"func": func_name, "args": args, "kwargs": kwargs},
            sort_keys=True,
            default=str,
        )
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, func_name: str, *args, **kwargs) -> Any | None:
        key = self._make_key(func_name, *args, **kwargs)
        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            return None
        if time.time() - entry.timestamp > entry.ttl:
            del self._store[key]
            self._misses += 1
            return None
        self._hits += 1
        return entry.data

    def set(
        self, func_name: str, data: Any, category: str, *args, **kwargs
    ) -> None:
        key = self._make_key(func_name, *args, **kwargs)
        ttl = CACHE_TTL.get(category, 300)
        self._store[key] = CacheEntry(data=data, timestamp=time.time(), ttl=ttl)

    def clear(self) -> None:
        self._store.clear()

    def stats(self) -> dict:
        return {
            "entries": len(self._store),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": (
                f"{self._hits / (self._hits + self._misses) * 100:.1f}%"
                if (self._hits + self._misses) > 0
                else "N/A"
            ),
        }


# Global singleton
_cache = WindCache()


def get_cache() -> WindCache:
    return _cache
