"""Tests for TTL cache — runs without Wind Terminal."""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from wind_mcp.core.cache import WindCache


def test_cache_set_get():
    cache = WindCache()
    cache.set("test_func", {"result": 42}, "snapshot", "arg1", "arg2")
    result = cache.get("test_func", "arg1", "arg2")
    assert result == {"result": 42}


def test_cache_miss():
    cache = WindCache()
    result = cache.get("nonexistent", "arg1")
    assert result is None


def test_cache_different_args():
    cache = WindCache()
    cache.set("func", "data1", "snapshot", "a")
    cache.set("func", "data2", "snapshot", "b")
    assert cache.get("func", "a") == "data1"
    assert cache.get("func", "b") == "data2"


def test_cache_expiry():
    cache = WindCache()
    # Use a very short TTL category — override manually
    cache._store.clear()
    key = cache._make_key("func", "arg")
    from wind_mcp.core.cache import CacheEntry
    cache._store[key] = CacheEntry(data="old", timestamp=time.time() - 1000, ttl=1)
    result = cache.get("func", "arg")
    assert result is None


def test_cache_clear():
    cache = WindCache()
    cache.set("func", "data", "snapshot", "arg")
    cache.clear()
    assert cache.get("func", "arg") is None


def test_cache_stats():
    cache = WindCache()
    cache.set("func", "data", "snapshot", "arg")
    cache.get("func", "arg")  # hit
    cache.get("func", "miss")  # miss
    stats = cache.stats()
    assert stats["entries"] == 1
    assert stats["hits"] >= 1
    assert stats["misses"] >= 1
