# Wind MCP — Claude Code Instructions

## Project Overview
MCP server exposing Wind Financial Terminal data via 19 tools.

## Key Architecture
- `src/wind_mcp/server.py` — FastMCP entry, tool registration (~100 lines, thin)
- `src/wind_mcp/handlers/` — One module per tool group
- `src/wind_mcp/core/session.py` — WindPy singleton
- `src/wind_mcp/core/cache.py` — TTL cache
- `src/wind_mcp/core/parser.py` — WindData → dict parsers
- `src/wind_mcp/core/converter.py` — Bloomberg → Wind ticker converter

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
