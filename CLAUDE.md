# Wind MCP — Claude Code Instructions

## Project Overview
MCP server exposing Wind Financial Terminal data via 24 tools + 1 resource.

## Key Architecture
- `src/wind_mcp/server.py` — FastMCP entry, 24 tools + wind://health resource, lifespan hooks, metrics instrumentation
- `src/wind_mcp/handlers/` — One module per tool group (snapshot, historical, minute_bars, ticks, realtime, dataset, macro, sector, screening, estimates, holders, stock_connect, calendar, dates, composite, portfolio)
- `src/wind_mcp/core/session.py` — WindPy singleton with reconnect + health check
- `src/wind_mcp/core/executor.py` — Single-thread executor for serialized Wind API calls + in-flight dedup
- `src/wind_mcp/core/cache.py` — TTL cache with maxsize limit + LRU eviction
- `src/wind_mcp/core/parser.py` — WindData → dict parsers
- `src/wind_mcp/core/converter.py` — Bloomberg → Wind ticker converter
- `src/wind_mcp/core/validators.py` — Input validation (codes, dates, single-field guard for WSES/WSEE)
- `src/wind_mcp/core/resilience.py` — Timeout, retry, stale-cache fallback
- `src/wind_mcp/core/config.py` — Centralized config (env > toml > defaults)
- `src/wind_mcp/core/metrics.py` — Counters + histograms for tool/API call tracking
- `src/wind_mcp/core/universe.py` — Universe resolution (index/sector/codes → security list)
- `src/wind_mcp/core/filters.py` — In-memory data filtering (gt/lt/between/in/isnull/contains)

## Concurrency Model
FastMCP is async, WindPy is synchronous and NOT thread-safe. All Wind API calls go through `core/executor.py` which uses a single-thread `ThreadPoolExecutor` to serialize access. Handlers use `run_wind_sync()` to submit calls.

## WindPy API Patterns
All WindPy calls are synchronous:
```python
from WindPy import w
w.start()
result = w.wss("600030.SH", "close,pe_ttm")
# result.ErrorCode, result.Data (column-major!), result.Fields, result.Codes
```

## Critical: Data Layout
WindData.Data is COLUMN-MAJOR: `[[field1_vals], [field2_vals]]`
Parser functions transpose to row-major dicts.

## Ticker Formats
Accepts both Bloomberg format ("AAPL US Equity", "700 HK Equity") and Wind format ("AAPL.O", "00700.HK"). Auto-converted via core/converter.py.

## Running
```bash
# stdio (Claude Code)
python -m wind_mcp.server

# HTTP
python -m wind_mcp.server --http --port=8080
```

## Testing
Tests in `tests/` can run without Wind Terminal (mock WindData objects).
