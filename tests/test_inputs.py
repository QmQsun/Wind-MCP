"""Tests for input model validation (Pydantic model_validators)."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pydantic import ValidationError
from wind_mcp.models.inputs import (
    HistoricalInput,
    SectorSeriesInput,
    SectorSnapshotInput,
    DynamicScreenInput,
)


# --- HistoricalInput date range validation ---

def test_historical_input_valid():
    inp = HistoricalInput(
        codes="600030.SH", fields="close", begin_date="2024-01-01", end_date="2025-01-01"
    )
    assert inp.begin_date == "2024-01-01"


def test_historical_input_macro_dates():
    inp = HistoricalInput(codes="600030.SH", fields="close", begin_date="-1M")
    assert inp.begin_date == "-1M"


def test_historical_input_reversed_dates():
    with pytest.raises(ValidationError, match="after"):
        HistoricalInput(
            codes="600030.SH", fields="close",
            begin_date="2025-12-31", end_date="2025-01-01"
        )


# --- SectorSeriesInput single field + date range ---

def test_sector_series_single_field():
    inp = SectorSeriesInput(codes="a001010100", fields="pe_ttm")
    assert inp.fields == "pe_ttm"


def test_sector_series_multi_field_rejected():
    with pytest.raises(ValidationError, match="single indicator"):
        SectorSeriesInput(codes="a001010100", fields="pe_ttm,roe_ttm")


# --- SectorSnapshotInput single field ---

def test_sector_snapshot_single_field():
    inp = SectorSnapshotInput(codes="a001010100", fields="pe_ttm")
    assert inp.fields == "pe_ttm"


def test_sector_snapshot_multi_field_rejected():
    with pytest.raises(ValidationError, match="single indicator"):
        SectorSnapshotInput(codes="a001010100", fields="pe_ttm,roe_ttm")


# --- DynamicScreenInput universe validation ---

def test_dynamic_screen_valid_universe():
    inp = DynamicScreenInput(
        universe="index:000300.SH", fields=["close", "pe_ttm"]
    )
    assert inp.universe == "index:000300.SH"


def test_dynamic_screen_invalid_universe():
    with pytest.raises(ValidationError, match="Unknown universe"):
        DynamicScreenInput(universe="blah:something", fields=["close"])


def test_dynamic_screen_empty_universe_value():
    with pytest.raises(ValidationError, match="Empty universe"):
        DynamicScreenInput(universe="index:", fields=["close"])
