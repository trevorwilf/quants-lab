"""Phase fidelity-2: ``aggregate_prefilter_funnel`` returns a per-class breakdown."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from bowaka_lab.config.models import PrefilterConfig, UniverseConfig
from bowaka_lab.features.prefilter import (
    aggregate_prefilter_funnel,
    apply_prefilter,
)
from bowaka_lab.reports.tables import instrument_class_breakdown


def _build_cset():
    features = pd.DataFrame(
        [
            {"symbol": "AAPL",  "close": 10.0, "avg_dollar_volume": 5_000_000, "rvol": 2.0,
             "atr_pct": 0.10, "range_expansion": 1.5, "close_location": 0.8,
             "ema_distance": 0.05, "ema_slope": 0.02, "gap_pct": 0.0},
            {"symbol": "TSLL",  "close": 10.0, "avg_dollar_volume": 5_000_000, "rvol": 2.0,
             "atr_pct": 0.10, "range_expansion": 1.5, "close_location": 0.8,
             "ema_distance": 0.05, "ema_slope": 0.02, "gap_pct": 0.0},
            {"symbol": "ETN1",  "close": 10.0, "avg_dollar_volume": 5_000_000, "rvol": 2.0,
             "atr_pct": 0.10, "range_expansion": 1.5, "close_location": 0.8,
             "ema_distance": 0.05, "ema_slope": 0.02, "gap_pct": 0.0},
        ]
    ).set_index("symbol")
    snapshot = pd.DataFrame(
        [
            {"symbol": "AAPL", "name": "APPLE INC",                     "asset_class": "us_equity"},
            {"symbol": "TSLL", "name": "DIREXION DAILY TSLA BULL 1.5X", "asset_class": "us_equity"},
            {"symbol": "ETN1", "name": "IPATH BLOOMBERG COMMODITY ETN", "asset_class": "us_equity"},
        ]
    )
    cfg = PrefilterConfig(price_min=1.0, price_max=20.0)
    universe = UniverseConfig(ticker_blocklist=["TSLL", "CONL", "SMCX"])
    cset = apply_prefilter(
        features, cfg,
        signal_date=date(2026, 1, 1), trade_date=date(2026, 1, 2),
        asset_snapshot=snapshot, universe=universe,
    )
    return cset


def test_funnel_carries_per_instrument_class_block():
    cset = _build_cset()
    funnel = aggregate_prefilter_funnel({date(2026, 1, 1): cset})
    assert "by_instrument_class" in funnel
    by_class = funnel["by_instrument_class"]
    assert "operating_equity" in by_class
    assert "leveraged_etp" in by_class
    assert "etn" in by_class
    # AAPL passes; TSLL and ETN do not.
    assert by_class["operating_equity"]["n_rows"] == 1
    assert by_class["operating_equity"]["n_passed_prefilter"] == 1
    assert by_class["leveraged_etp"]["n_passed_prefilter"] == 0
    assert by_class["etn"]["n_passed_prefilter"] == 0


def test_instrument_class_breakdown_renders_tidy():
    cset = _build_cset()
    funnel = aggregate_prefilter_funnel({date(2026, 1, 1): cset})
    out = instrument_class_breakdown(funnel["by_instrument_class"])
    assert {"instrument_class", "n_rows", "n_passed_prefilter", "n_eligible_equity_bucket"}.issubset(out.columns)
    assert out["n_rows"].sum() == 3


def test_instrument_class_breakdown_empty_input():
    out = instrument_class_breakdown({})
    assert out.empty
    assert "instrument_class" in out.columns


def test_funnel_no_decisions_still_returns_block():
    funnel = aggregate_prefilter_funnel({})
    assert "by_instrument_class" in funnel
    assert funnel["by_instrument_class"] == {}
