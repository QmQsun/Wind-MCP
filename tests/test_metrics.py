"""Tests for metrics collection."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from wind_mcp.core.metrics import Counter, Histogram, MetricsRegistry


def test_counter_basic():
    c = Counter()
    assert c.value == 0
    c.inc()
    assert c.value == 1
    c.inc(5)
    assert c.value == 6


def test_histogram_empty():
    h = Histogram()
    s = h.summary()
    assert s["count"] == 0


def test_histogram_observe():
    h = Histogram()
    for v in [10, 20, 30, 40, 50]:
        h.observe(v)
    s = h.summary()
    assert s["count"] == 5
    assert s["min"] == 10
    assert s["max"] == 50
    assert s["avg"] == 30.0
    assert s["p50"] == 30


def test_histogram_max_samples():
    h = Histogram(max_samples=10)
    for i in range(100):
        h.observe(float(i))
    s = h.summary()
    assert s["count"] == 10  # Capped


def test_registry_snapshot():
    r = MetricsRegistry()
    r.record_tool_call("snapshot", 150.0)
    r.record_tool_call("historical", 200.0)
    r.record_tool_call("snapshot", 100.0, error=True)
    r.record_wind_api_call(80.0)
    r.record_wind_api_call(90.0, error=True)

    snap = r.snapshot()
    assert snap["tool_calls"]["total"] == 3
    assert snap["tool_calls"]["errors"] == 1
    assert snap["tool_calls"]["per_tool"]["snapshot"] == 2
    assert snap["tool_calls"]["per_tool"]["historical"] == 1
    assert snap["wind_api"]["total"] == 2
    assert snap["wind_api"]["errors"] == 1
    assert "uptime" in snap
