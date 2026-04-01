"""
Lightweight metrics collection for Wind MCP.

Pure Python counters and histograms — no external dependencies.
Exposed via wind_metrics tool.
"""

import time
import threading
import logging
from typing import Any

logger = logging.getLogger(__name__)


class Counter:
    """Thread-safe monotonic counter."""

    def __init__(self):
        self._value: int = 0
        self._lock = threading.Lock()

    def inc(self, n: int = 1) -> None:
        with self._lock:
            self._value += n

    @property
    def value(self) -> int:
        return self._value


class Histogram:
    """Thread-safe histogram tracking min/max/avg/count/p50/p95."""

    def __init__(self, max_samples: int = 1000):
        self._samples: list[float] = []
        self._lock = threading.Lock()
        self._max_samples = max_samples

    def observe(self, value: float) -> None:
        with self._lock:
            self._samples.append(value)
            if len(self._samples) > self._max_samples:
                self._samples = self._samples[-self._max_samples:]

    def summary(self) -> dict[str, Any]:
        with self._lock:
            if not self._samples:
                return {"count": 0, "min": 0, "max": 0, "avg": 0, "p50": 0, "p95": 0}
            s = sorted(self._samples)
            n = len(s)
            return {
                "count": n,
                "min": round(s[0], 3),
                "max": round(s[-1], 3),
                "avg": round(sum(s) / n, 3),
                "p50": round(s[n // 2], 3),
                "p95": round(s[int(n * 0.95)], 3),
            }


class MetricsRegistry:
    """Central metrics store."""

    def __init__(self):
        self.tool_calls = Counter()
        self.tool_errors = Counter()
        self.wind_api_calls = Counter()
        self.wind_api_errors = Counter()
        self.tool_latency = Histogram()
        self.wind_api_latency = Histogram()
        self._tool_call_counts: dict[str, int] = {}
        self._lock = threading.Lock()
        self._start_time = time.time()

    def record_tool_call(self, tool_name: str, latency_ms: float, error: bool = False) -> None:
        """Record a tool invocation."""
        self.tool_calls.inc()
        self.tool_latency.observe(latency_ms)
        if error:
            self.tool_errors.inc()
        with self._lock:
            self._tool_call_counts[tool_name] = self._tool_call_counts.get(tool_name, 0) + 1

    def record_wind_api_call(self, latency_ms: float, error: bool = False) -> None:
        """Record a Wind API call."""
        self.wind_api_calls.inc()
        self.wind_api_latency.observe(latency_ms)
        if error:
            self.wind_api_errors.inc()

    def snapshot(self) -> dict[str, Any]:
        """Return a complete metrics snapshot."""
        uptime = time.time() - self._start_time
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)

        with self._lock:
            per_tool = dict(self._tool_call_counts)

        return {
            "uptime": f"{hours}h {minutes}m",
            "tool_calls": {
                "total": self.tool_calls.value,
                "errors": self.tool_errors.value,
                "latency_ms": self.tool_latency.summary(),
                "per_tool": per_tool,
            },
            "wind_api": {
                "total": self.wind_api_calls.value,
                "errors": self.wind_api_errors.value,
                "latency_ms": self.wind_api_latency.summary(),
            },
        }


# Global singleton
_metrics: MetricsRegistry | None = None


def get_metrics() -> MetricsRegistry:
    global _metrics
    if _metrics is None:
        _metrics = MetricsRegistry()
    return _metrics
