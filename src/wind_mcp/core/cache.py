"""
TTL-based cache with data-type-aware expiration and LRU eviction.

Cache keys are built from: (function_name, args_tuple, frozen_options)
"""

import time
import hashlib
import json
from typing import Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

# TTL in seconds, by data category (defaults — overridden by config)
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
    "portfolio": 300,      # WPF/WPS/WPD — 5 minutes
    "static": 86400,       # Rarely changes — 24 hours
}


@dataclass
class CacheEntry:
    data: Any
    timestamp: float
    ttl: float
    last_access: float = 0.0

    def __post_init__(self):
        if self.last_access == 0.0:
            self.last_access = self.timestamp


class WindCache:
    """In-memory TTL cache with maxsize and LRU eviction."""

    def __init__(self, maxsize: int = 2000):
        self._store: dict[str, CacheEntry] = {}
        self._hits: int = 0
        self._misses: int = 0
        self._evictions: int = 0
        self._maxsize: int = maxsize

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
        entry.last_access = time.time()
        return entry.data

    def stale_get(self, func_name: str, *args, **kwargs) -> Any | None:
        """
        Return data even if expired (stale-while-error fallback).
        Does NOT delete the entry or update hit/miss counters.
        """
        key = self._make_key(func_name, *args, **kwargs)
        entry = self._store.get(key)
        if entry is not None:
            return entry.data
        return None

    def set(
        self, func_name: str, data: Any, category: str, *args, **kwargs
    ) -> None:
        key = self._make_key(func_name, *args, **kwargs)
        ttl = CACHE_TTL.get(category, 300)
        self._store[key] = CacheEntry(data=data, timestamp=time.time(), ttl=ttl)
        self._evict_if_needed()

    def _evict_if_needed(self) -> None:
        """Evict oldest 20% of entries when cache exceeds maxsize."""
        if len(self._store) <= self._maxsize:
            return
        # Sort by last_access, evict oldest 20%
        evict_count = max(1, len(self._store) // 5)
        sorted_keys = sorted(
            self._store, key=lambda k: self._store[k].last_access
        )
        for key in sorted_keys[:evict_count]:
            del self._store[key]
            self._evictions += 1
        logger.debug(f"Cache eviction: removed {evict_count} entries, {len(self._store)} remaining")

    def clear(self) -> None:
        self._store.clear()

    def stats(self) -> dict:
        return {
            "entries": len(self._store),
            "maxsize": self._maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate": (
                f"{self._hits / (self._hits + self._misses) * 100:.1f}%"
                if (self._hits + self._misses) > 0
                else "N/A"
            ),
        }


# Global singleton (lazy init with config)
_cache: WindCache | None = None


def get_cache() -> WindCache:
    global _cache
    if _cache is None:
        try:
            from .config import get_config
            cfg = get_config()
            _cache = WindCache(maxsize=cfg.cache_maxsize)
            # Apply config TTLs
            ttl_map = cfg.get_cache_ttl_map()
            CACHE_TTL.update(ttl_map)
        except Exception:
            _cache = WindCache()
    return _cache
