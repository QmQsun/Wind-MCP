# Wind MCP

A Model Context Protocol server that gives AI assistants direct access to Wind Financial Terminal data.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)

---

Wind MCP bridges the Wind Financial Terminal (万得) with AI assistants via the [Model Context Protocol](https://modelcontextprotocol.io). It exposes **19 tools** covering market data, fundamentals, macro economics, screening, estimates, and date utilities — all accessible through natural language.

> Companion project to [Bloomberg-MCP](https://github.com/QmQsun/Bloomberg-MCP). Same architecture, same philosophy — but for Wind (万得).

```
You: "拉一下贵州茅台过去20天的量价数据"

Claude: runs wind_historical with codes=600519.SH, fields=close,volume
        → Returns structured price/volume time series

You: "Find me A-share stocks with PE < 15 and ROE > 20%"

Claude: runs wind_dynamic_screen with universe=A-shares, filters, rank
        → Returns filtered and ranked stock list
```

## Architecture

```mermaid
graph TB
    subgraph Clients
        CC[Claude Code]
        WC[Web Client]
        CA[Custom App]
    end

    subgraph "Wind MCP Server"
        direction TB
        MCP["FastMCP Server<br/><i>19 tools exposed</i>"]

        subgraph Handlers["Handler Layer"]
            direction LR
            SNAP[Snapshot & Historical]
            INTRA[Minute Bars & Ticks]
            MACRO[Macro & Sector]
            SCREEN[Screening]
            EST[Estimates & Holders]
            CAL[Calendar & Dates]
        end

        subgraph Core["Core Layer"]
            direction LR
            SESSION["WindSession<br/><i>Singleton + atexit</i>"]
            CACHE["WindCache<br/><i>TTL-based</i>"]
            PARSER["Parser<br/><i>12 parsers</i>"]
            CONV["Converter<br/><i>BBG → Wind</i>"]
        end
    end

    WIND["Wind Terminal<br/><i>WindPy (w.start)</i>"]

    CC -- stdio --> MCP
    WC -- HTTP/SSE --> MCP
    CA -- HTTP/SSE --> MCP
    MCP --> Handlers
    Handlers --> Core
    SESSION <--> WIND

    style MCP fill:#1a73e8,stroke:#1557b0,color:#fff
    style WIND fill:#e65100,stroke:#bf360c,color:#fff
    style SESSION fill:#2e7d32,stroke:#1b5e20,color:#fff
    style CACHE fill:#2e7d32,stroke:#1b5e20,color:#fff
```

## Tools Overview (19 tools)

```mermaid
graph LR
    subgraph "Market Data (5)"
        T1["wind_snapshot<br/><i>WSS current data</i>"]
        T2["wind_historical<br/><i>WSD time series</i>"]
        T3["wind_minute_bars<br/><i>WSI candles</i>"]
        T4["wind_ticks<br/><i>WST raw ticks</i>"]
        T5["wind_realtime<br/><i>WSQ live quotes</i>"]
    end

    subgraph "Fundamentals & Screening (5)"
        T6["wind_dataset<br/><i>WSET tables</i>"]
        T7["wind_screen<br/><i>WEQS screens</i>"]
        T8["wind_dynamic_screen<br/><i>Custom filter + rank</i>"]
        T9["wind_estimates<br/><i>Consensus</i>"]
        T10["wind_holders<br/><i>Shareholding</i>"]
    end

    subgraph "Macro & Sector (3)"
        T11["wind_macro<br/><i>EDB series</i>"]
        T12["wind_sector_series<br/><i>WSES time series</i>"]
        T13["wind_sector_snapshot<br/><i>WSEE snapshot</i>"]
    end

    subgraph "Connect & Calendar (3)"
        T14["wind_stock_connect<br/><i>Northbound flows</i>"]
        T15["wind_event_calendar<br/><i>IPO, earnings...</i>"]
        T16["wind_list_fieldsets<br/><i>Available FieldSets</i>"]
    end

    subgraph "Date Utilities (3)"
        T17["wind_trading_days<br/><i>TDAYS</i>"]
        T18["wind_date_offset<br/><i>TDAYSOFFSET</i>"]
        T19["wind_days_count<br/><i>TDAYSCOUNT</i>"]
    end

    style T6 fill:#1a73e8,stroke:#1557b0,color:#fff
    style T7 fill:#1a73e8,stroke:#1557b0,color:#fff
    style T8 fill:#1a73e8,stroke:#1557b0,color:#fff
    style T11 fill:#7b1fa2,stroke:#6a1b9a,color:#fff
    style T12 fill:#7b1fa2,stroke:#6a1b9a,color:#fff
    style T13 fill:#7b1fa2,stroke:#6a1b9a,color:#fff
```

## Key Features

- **Bloomberg → Wind Ticker Converter** — Accepts Bloomberg-style identifiers (`AAPL US Equity`, `700 HK Equity`, `601012 CH Equity`) and auto-converts to Wind codes (`AAPL.O`, `00700.HK`, `601012.SH`). Covers US, HK, JP, LN, CH equities, indices, commodities, and currencies.
- **Modular architecture** — server.py is a thin entry point. Handlers, models, formatters, parsers, and converters cleanly separated.
- **16 FieldSet shortcuts** — Pre-defined field collections (PRICE, VALUATION, PROFITABILITY, etc.) that expand to Wind field mnemonics.
- **Cache layer** — TTL-based in-memory cache with data-type-aware expiration (30s for realtime, 24h for static).
- **12 WindPy parsers** — Handle WSS, WSD, WSI, WST, WSQ, WSET, EDB, WSES, WSEE, TDAYS, TDAYSOFFSET, TDAYSCOUNT with NaN→None cleanup and column-to-row transposition.
- **Dynamic Screening** — Custom filtering with operators (gt, lt, between, in, eq) + ranking + slicing, without knowing Wind mnemonics.

## Data Flow

```mermaid
sequenceDiagram
    participant Client as AI Assistant
    participant MCP as MCP Server
    participant Conv as Ticker Converter
    participant Expand as Field Expander
    participant Cache as Cache Layer
    participant Session as WindSession
    participant Wind as Wind Terminal

    Client->>MCP: Tool call (JSON)
    MCP->>Conv: Convert BBG → Wind codes
    Conv-->>MCP: Wind codes

    alt FieldSet shortcuts used
        MCP->>Expand: Expand FieldSet shortcuts
        Expand-->>MCP: Resolved field list
    end

    MCP->>Cache: Check cache
    alt Cache hit
        Cache-->>MCP: Cached result
    else Cache miss
        MCP->>Session: Call WindPy API
        Session->>Wind: w.wsd() / w.wss() / ...
        Wind-->>Session: WindData response
        Session-->>MCP: Parsed dicts
        MCP->>Cache: Store with TTL
    end

    alt Markdown format
        MCP-->>Client: Formatted table
    else JSON format
        MCP-->>Client: Structured JSON
    end
```

## Tool Reference

### Market Data

| Tool | WindPy API | Description | Key Parameters |
|------|-----------|-------------|----------------|
| `wind_snapshot` | WSS | Current field values for any security | `codes`, `fields`, `trade_date` |
| `wind_historical` | WSD | Time series with configurable periodicity | `codes`, `fields`, `begin_date`, `end_date` |
| `wind_minute_bars` | WSI | OHLCV intraday candles (1/3/5/15/30/60 min) | `codes`, `fields`, `begin_time`, `end_time`, `bar_size` |
| `wind_ticks` | WST | Raw tick-level trade data | `codes`, `fields`, `begin_time`, `end_time` |
| `wind_realtime` | WSQ | Live streaming quotes | `codes`, `fields` |

### Fundamentals & Screening

| Tool | WindPy API | Description | Key Parameters |
|------|-----------|-------------|----------------|
| `wind_dataset` | WSET | Structured datasets (index members, IPOs, etc.) | `table_name`, `options` |
| `wind_screen` | WEQS | Execute saved Wind stock screens | `screen_name`, `options` |
| `wind_dynamic_screen` | WSS | Custom filter + rank + slice | `universe`, `fields`, `filters`, `rank_by`, `top_n` |
| `wind_estimates` | WSS | Consensus estimates and target prices | `codes`, `metrics`, `year` |
| `wind_holders` | WSS/WSET | Top holders, institutional, fund holdings | `codes`, `holder_type`, `date` |

### Macro & Sector

| Tool | WindPy API | Description | Key Parameters |
|------|-----------|-------------|----------------|
| `wind_macro` | EDB | Macroeconomic indicator time series | `codes`, `begin_date`, `end_date` |
| `wind_sector_series` | WSES | Sector-level time series | `codes`, `fields`, `begin_date`, `end_date` |
| `wind_sector_snapshot` | WSEE | Sector-level current snapshot | `codes`, `fields`, `trade_date` |

### Stock Connect & Calendar

| Tool | WindPy API | Description | Key Parameters |
|------|-----------|-------------|----------------|
| `wind_stock_connect` | WSET/WSS | Northbound/Southbound flow data | `codes`, `direction`, `date` |
| `wind_event_calendar` | WSET | IPO, earnings, dividend calendars | `event_type`, `begin_date`, `end_date` |
| `wind_list_fieldsets` | — | List all available FieldSet shortcuts | — |

### Date Utilities

| Tool | WindPy API | Description | Key Parameters |
|------|-----------|-------------|----------------|
| `wind_trading_days` | TDAYS | List trading days in a range | `begin_date`, `end_date`, `calendar` |
| `wind_date_offset` | TDAYSOFFSET | Offset a date by N trading days | `date`, `offset`, `calendar` |
| `wind_days_count` | TDAYSCOUNT | Count trading days between two dates | `begin_date`, `end_date`, `calendar` |

All tools support `response_format`: `"markdown"` (default) or `"json"`.

## FieldSet Shortcuts

Instead of remembering Wind field mnemonics, use shorthand names that expand to multiple fields.

| FieldSet | Fields | Key Wind Mnemonics |
|----------|--------|-------------------|
| `PRICE` | 5 | close, open, high, low, pct_chg |
| `MOMENTUM` | 4 | pct_chg, pct_chg_5d, pct_chg_1m, pct_chg_ytd |
| `VOLUME_PROFILE` | 4 | volume, amt, turn, free_turn |
| `VALUATION` | 5 | pe_ttm, pb_lf, ps_ttm, pcf_ocf_ttm, ev2_to_ebitda |
| `VALUATION_EXTENDED` | 9 | + pe_est, dividend_yield, total_mkt_cap, ev |
| `PROFITABILITY` | 6 | roe_ttm, roa_ttm, grossprofitmargin, netprofitmargin, operatingprofitmargin, roic |
| `GROWTH` | 4 | yoyprofit, yoyrevenue, yoyocf, qfa_yoygr |
| `BALANCE_SHEET` | 6 | debttoassets, current_ratio, quick_ratio, cashflow_to_debt, longdebttodebt, equity_ratio |
| `CASH_FLOW` | 5 | ocfps, fcf, cf_from_ops, capex, dividendps |
| `TECHNICAL` | 5 | rsi, macd, vol_20d, beta_100w, atr_14d |
| `ANALYST` | 4 | rating_avg, est_target_price, est_eps_fy1, est_net_profit_fy1 |
| `ESTIMATE_REVISIONS` | 4 | est_eps_chg_4w, est_eps_chg_13w, est_num_up, est_num_down |
| `SECTOR` | 2 | industry_sw, industry_sw_lv2 |
| `NORTHBOUND` | 4 | sh_hk_share_pct, sh_hk_share_chg, sh_hk_share_amt, sh_hk_share_rank |
| `MARGIN` | 3 | margin_buy_bal, margin_sell_bal, margin_net_bal |
| `RISK` | 5 | beta_100w, volatility_20d, volatility_60d, sharpe_20d, max_drawdown_1y |
| `SCREENING_FULL` | 50+ | All of the above combined |

## Bloomberg → Wind Ticker Conversion

Wind MCP automatically converts Bloomberg-style identifiers to Wind codes:

| Bloomberg Format | Wind Code | Market |
|-----------------|-----------|--------|
| `AAPL US Equity` | `AAPL.O` | US (NASDAQ) |
| `JPM US Equity` | `JPM.N` | US (NYSE) |
| `700 HK Equity` | `00700.HK` | Hong Kong |
| `7203 JP Equity` | `7203.T` | Japan |
| `VOD LN Equity` | `VOD.L` | London |
| `601012 CH Equity` | `601012.SH` | A-share (Shanghai) |
| `000001 CH Equity` | `000001.SZ` | A-share (Shenzhen) |
| `300750 CH Equity` | `300750.SZ` | A-share (ChiNext) |
| `SPX Index` | `SPX.GI` | Index |
| `HSI Index` | `HSI.HI` | Index |
| `CL1 Comdty` | `CL.NYM` | Commodity |
| `EURUSD Curncy` | `EURUSD.FX` | Currency |
| `600519.SH` | `600519.SH` | Passthrough (already Wind) |

## Dynamic Screening

Build custom screens with pre-validated field sets, filters, and ranking — no need to know Wind field mnemonics.

```mermaid
flowchart LR
    A["Universe<br/><i>index, sector,<br/>or ticker list</i>"] --> B["Field Expansion<br/><i>FieldSet shortcuts<br/>→ Wind fields</i>"]
    B --> C["Wind API<br/><i>WSS request</i>"]
    C --> D["Filter<br/><i>gt, lt, between,<br/>in, eq, ...</i>"]
    D --> E["Rank & Slice<br/><i>rank_by + top_n</i>"]
    E --> F["Response<br/><i>Markdown table<br/>or JSON</i>"]

    style A fill:#e8f5e9,stroke:#2e7d32
    style C fill:#fff3e0,stroke:#ff6f00
    style F fill:#e3f2fd,stroke:#1a73e8
```

### Filter Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `gt` / `gte` | Greater than (or equal) | `{"field": "roe_ttm", "op": "gt", "value": 20}` |
| `lt` / `lte` | Less than (or equal) | `{"field": "pe_ttm", "op": "lt", "value": 15}` |
| `eq` / `neq` | Equals / not equals | `{"field": "industry_sw", "op": "eq", "value": "电子"}` |
| `between` | Range (inclusive) | `{"field": "pe_ttm", "op": "between", "value": [10, 25]}` |
| `in` | Value in list | `{"field": "industry_sw", "op": "in", "value": ["电子", "计算机"]}` |

### Example: Find Undervalued High-ROE A-shares

```json
{
  "universe": "sector:全部A股",
  "fields": ["PRICE", "VALUATION", "PROFITABILITY"],
  "filters": [
    {"field": "pe_ttm", "op": "lt", "value": 15},
    {"field": "roe_ttm", "op": "gt", "value": 20}
  ],
  "rank_by": "roe_ttm",
  "rank_descending": true,
  "top_n": 20
}
```

## Cache Layer

Built-in cache reduces Wind API load with data-type-aware TTLs:

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Realtime quotes (WSQ) | 30 seconds | Near real-time |
| Historical (WSD) | 12 hours | End-of-day data stable |
| Snapshot (WSS) | 5 minutes | Moderate refresh |
| Static reference | 24 hours | Rarely changes |
| Macro data (EDB) | 6 hours | Periodic updates |
| Dataset (WSET) | 1 hour | Moderate refresh |

## Project Structure

```
wind-mcp/
├── pyproject.toml
├── README.md
├── LICENSE
├── CLAUDE.md
├── run_server.bat / run_server.ps1
├── src/wind_mcp/
│   ├── __init__.py
│   ├── __main__.py
│   ├── server.py                  # FastMCP entry point, 19 tools
│   ├── formatters.py              # Markdown table & JSON output
│   ├── utils.py                   # Date normalization, validation
│   ├── core/
│   │   ├── session.py             # WindSession singleton + atexit
│   │   ├── cache.py               # TTL cache with hit/miss stats
│   │   ├── parser.py              # 12 WindData parsers
│   │   └── converter.py           # Bloomberg → Wind ticker converter
│   ├── models/
│   │   ├── enums.py               # ResponseFormat, Periodicity, etc.
│   │   └── inputs.py              # 18 Pydantic input models
│   ├── tools/
│   │   ├── fieldsets.py           # 16 FieldSet definitions
│   │   └── field_expander.py      # FieldSet → field list resolver
│   ├── handlers/                  # 12 handler modules
│   │   ├── snapshot.py            # WSS
│   │   ├── historical.py          # WSD
│   │   ├── minute_bars.py         # WSI
│   │   ├── ticks.py               # WST
│   │   ├── realtime.py            # WSQ
│   │   ├── dataset.py             # WSET
│   │   ├── macro.py               # EDB
│   │   ├── sector.py              # WSES / WSEE
│   │   ├── screening.py           # WEQS + dynamic screen
│   │   ├── estimates.py           # Consensus estimates
│   │   ├── holders.py             # Holder analysis
│   │   ├── stock_connect.py       # Northbound/Southbound
│   │   ├── calendar.py            # Event calendar
│   │   └── dates.py               # TDAYS / TDAYSOFFSET / TDAYSCOUNT
│   └── data/                      # Static mapping files
│       ├── us_exchange_map.json   # ~200 US tickers → exchange
│       ├── index_map.json         # BBG → Wind index mapping
│       ├── commodity_map.json     # BBG → Wind commodity mapping
│       └── currency_map.json      # BBG → Wind currency mapping
├── tests/                         # 42 unit tests (no Wind needed)
│   ├── test_parser.py
│   ├── test_fieldsets.py
│   ├── test_cache.py
│   ├── test_formatters.py
│   └── test_converter.py
└── examples/
    ├── basic_usage.py
    └── screening_example.py
```

## Installation

### Prerequisites

- Python 3.10+
- **Wind Financial Terminal (万得) running and logged in**
- WindPy installed (`pip install WindPy` or repair via Wind Terminal)

### Setup

```bash
# Clone the repository
git clone https://github.com/QmQsun/Wind-MCP.git
cd Wind-MCP

# Install
pip install .            # standard install
# or: pip install -e .   # editable mode (for development)
```

### Configure Claude Code

Add to your Claude Code MCP settings (`.mcp.json`):

```json
{
  "mcpServers": {
    "wind-mcp": {
      "command": "python",
      "args": ["-m", "wind_mcp.server"],
      "cwd": "/path/to/Wind-MCP/src"
    }
  }
}
```

### Install from PyPI

```bash
pip install wind-mcp
```

## Quick Start

### As an MCP Server

```bash
# stdio (default — for Claude Code)
python -m wind_mcp.server

# HTTP transport (for web clients)
python -m wind_mcp.server --transport http --port 8080

# SSE transport (for streaming clients)
python -m wind_mcp.server --transport sse --port 8080
```

### Windows

```bash
# Command Prompt
run_server.bat

# PowerShell
.\run_server.ps1
```

## Wind API Coverage

```mermaid
graph LR
    subgraph "Wind Terminal (WindPy)"
        WSS["WSS<br/><i>Snapshot</i>"]
        WSD["WSD<br/><i>Historical</i>"]
        WSI["WSI<br/><i>Minute bars</i>"]
        WST["WST<br/><i>Tick data</i>"]
        WSQ["WSQ<br/><i>Realtime</i>"]
        WSET["WSET<br/><i>Datasets</i>"]
        EDB["EDB<br/><i>Macro</i>"]
        WSES["WSES<br/><i>Sector series</i>"]
        WSEE["WSEE<br/><i>Sector snapshot</i>"]
        WEQS["WEQS<br/><i>Stock screener</i>"]
        TDAYS["TDAYS<br/><i>Trading days</i>"]
    end

    WSS --- T1[Snapshot + Estimates + Holders + Screen]
    WSD --- T2[Historical Time Series]
    WSI --- T3[Intraday Bars]
    WST --- T4[Tick Data]
    WSQ --- T5[Realtime Quotes]
    WSET --- T6[Datasets + Connect + Calendar]
    EDB --- T7[Macro Indicators]
    WSES --- T8[Sector Time Series]
    WSEE --- T9[Sector Snapshot]
    WEQS --- T10[Saved Screens]
    TDAYS --- T11[Date Utilities]

    style WSS fill:#1a73e8,stroke:#1557b0,color:#fff
    style WSD fill:#1a73e8,stroke:#1557b0,color:#fff
    style EDB fill:#7b1fa2,stroke:#6a1b9a,color:#fff
    style WEQS fill:#e65100,stroke:#bf360c,color:#fff
```

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

```bash
pip install -e ".[dev]"
pytest                    # Unit tests (no Wind Terminal needed)
black src/ tests/
ruff check src/ tests/
```

## Contributors

| | Contributor | Role |
|---|---|---|
| 1 | [QmQsun](https://github.com/QmQsun) | Architecture, spec design, code review |
| 2 | Claude (Anthropic) | Implementation, code generation, testing |

## Related Projects

- [Bloomberg-MCP](https://github.com/QmQsun/Bloomberg-MCP) — Same architecture for Bloomberg Terminal

## License

MIT — see [LICENSE](LICENSE) for details.
