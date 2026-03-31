"""
Dynamic screening example.

Screen CSI 300 constituents for:
- PE (TTM) between 5 and 30
- ROE (TTM) > 15%
- Rank by ROE descending
- Top 20

Requires Wind Terminal running and logged in.
"""

from wind_mcp.models.inputs import DynamicScreenInput
from wind_mcp.models.enums import ResponseFormat
from wind_mcp.handlers.screening import handle_dynamic_screen
from wind_mcp.formatters import format_response


def screen_csi300_value():
    params = DynamicScreenInput(
        universe="index:000300.SH",
        fields=["PRICE", "VALUATION", "PROFITABILITY", "SECTOR"],
        filters=[
            {"field": "pe_ttm", "op": "between", "value": [5, 30]},
            {"field": "roe_ttm2", "op": "gt", "value": 15},
        ],
        rank_by="roe_ttm2",
        rank_descending=True,
        top_n=20,
        response_format=ResponseFormat.MARKDOWN,
    )
    data = handle_dynamic_screen(params)
    print(f"Found {len(data)} stocks matching criteria:\n")
    print(format_response(data, "markdown"))


def screen_sector_momentum():
    """Screen 全部A股 for high momentum + reasonable valuation."""
    params = DynamicScreenInput(
        universe="sector:a001010100",
        fields=["close", "pct_chg_1m", "pct_chg_3m", "pe_ttm", "industry_sw"],
        filters=[
            {"field": "pct_chg_1m", "op": "gt", "value": 10},
            {"field": "pe_ttm", "op": "between", "value": [10, 50]},
        ],
        rank_by="pct_chg_3m",
        rank_descending=True,
        top_n=30,
        response_format=ResponseFormat.MARKDOWN,
    )
    data = handle_dynamic_screen(params)
    print(f"Found {len(data)} high-momentum stocks:\n")
    print(format_response(data, "markdown"))


if __name__ == "__main__":
    print("=== CSI 300 Value Screen ===")
    screen_csi300_value()
    print("\n=== Sector Momentum Screen ===")
    screen_sector_momentum()
