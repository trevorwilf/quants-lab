"""Phase 3: individual gate behavior."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from bowaka_lab.config.models import PrefilterConfig, UniverseConfig
from bowaka_lab.features.prefilter import apply_prefilter


def _features(rows):
    return pd.DataFrame(rows).set_index("symbol")


def test_price_min_gate_rejects_below():
    feats = _features(
        [
            {"symbol": "LOW", "close": 0.5, "rvol": 2, "atr_pct": 0.1, "range_expansion": 1.5, "close_location": 0.8, "ema_distance": 0.05, "ema_slope": 0.02, "avg_dollar_volume": 1e6, "gap_pct": 0.0},
            {"symbol": "OK", "close": 5.0, "rvol": 2, "atr_pct": 0.1, "range_expansion": 1.5, "close_location": 0.8, "ema_distance": 0.05, "ema_slope": 0.02, "avg_dollar_volume": 1e6, "gap_pct": 0.0},
        ]
    )
    cfg = PrefilterConfig(price_min=1.0, price_max=20.0)
    cset = apply_prefilter(feats, cfg, signal_date=date(2026, 5, 11), trade_date=date(2026, 5, 12), universe=UniverseConfig())
    assert "LOW" not in cset.candidates.index
    assert "OK" in cset.candidates.index
    low_row = cset.all_decisions.loc["LOW"]
    assert "price_min" in low_row["rejection_reasons"]


def test_price_max_gate_rejects_above():
    feats = _features(
        [
            {"symbol": "HIGH", "close": 100.0, "rvol": 2, "atr_pct": 0.1, "range_expansion": 1.5, "close_location": 0.8, "ema_distance": 0.05, "ema_slope": 0.02, "avg_dollar_volume": 1e6, "gap_pct": 0.0},
            {"symbol": "OK", "close": 5.0, "rvol": 2, "atr_pct": 0.1, "range_expansion": 1.5, "close_location": 0.8, "ema_distance": 0.05, "ema_slope": 0.02, "avg_dollar_volume": 1e6, "gap_pct": 0.0},
        ]
    )
    cfg = PrefilterConfig(price_min=1.0, price_max=20.0)
    cset = apply_prefilter(feats, cfg, signal_date=date(2026, 5, 11), trade_date=date(2026, 5, 12), universe=UniverseConfig())
    assert "HIGH" not in cset.candidates.index
    assert "price_max" in cset.all_decisions.loc["HIGH"]["rejection_reasons"]


def test_avg_dollar_volume_min_gate():
    feats = _features(
        [
            {"symbol": "THIN", "close": 5.0, "rvol": 2, "atr_pct": 0.1, "range_expansion": 1.5, "close_location": 0.8, "ema_distance": 0.05, "ema_slope": 0.02, "avg_dollar_volume": 1e4, "gap_pct": 0.0},
            {"symbol": "OK", "close": 5.0, "rvol": 2, "atr_pct": 0.1, "range_expansion": 1.5, "close_location": 0.8, "ema_distance": 0.05, "ema_slope": 0.02, "avg_dollar_volume": 1e6, "gap_pct": 0.0},
        ]
    )
    cfg = PrefilterConfig(price_min=1.0, price_max=20.0, avg_dollar_volume_min=2e5)
    cset = apply_prefilter(feats, cfg, signal_date=date(2026, 5, 11), trade_date=date(2026, 5, 12), universe=UniverseConfig())
    assert "THIN" not in cset.candidates.index
    assert "OK" in cset.candidates.index


def test_rvol_min_gate():
    feats = _features(
        [
            {"symbol": "LOWRVOL", "close": 5.0, "rvol": 0.5, "atr_pct": 0.1, "range_expansion": 1.5, "close_location": 0.8, "ema_distance": 0.05, "ema_slope": 0.02, "avg_dollar_volume": 1e6, "gap_pct": 0.0},
            {"symbol": "OK", "close": 5.0, "rvol": 2.0, "atr_pct": 0.1, "range_expansion": 1.5, "close_location": 0.8, "ema_distance": 0.05, "ema_slope": 0.02, "avg_dollar_volume": 1e6, "gap_pct": 0.0},
        ]
    )
    cfg = PrefilterConfig(price_min=1.0, price_max=20.0, rvol_min=1.5)
    cset = apply_prefilter(feats, cfg, signal_date=date(2026, 5, 11), trade_date=date(2026, 5, 12), universe=UniverseConfig())
    assert "LOWRVOL" not in cset.candidates.index


def test_close_location_min_gate():
    feats = _features(
        [
            {"symbol": "WEAK", "close": 5.0, "rvol": 2.0, "atr_pct": 0.1, "range_expansion": 1.5, "close_location": 0.3, "ema_distance": 0.05, "ema_slope": 0.02, "avg_dollar_volume": 1e6, "gap_pct": 0.0},
            {"symbol": "OK", "close": 5.0, "rvol": 2.0, "atr_pct": 0.1, "range_expansion": 1.5, "close_location": 0.8, "ema_distance": 0.05, "ema_slope": 0.02, "avg_dollar_volume": 1e6, "gap_pct": 0.0},
        ]
    )
    cfg = PrefilterConfig(price_min=1.0, price_max=20.0, close_location_min=0.6)
    cset = apply_prefilter(feats, cfg, signal_date=date(2026, 5, 11), trade_date=date(2026, 5, 12), universe=UniverseConfig())
    assert "WEAK" not in cset.candidates.index


def test_rvol_max_gate_when_set():
    feats = _features(
        [
            {"symbol": "BLOW", "close": 5.0, "rvol": 12.0, "atr_pct": 0.1, "range_expansion": 1.5, "close_location": 0.8, "ema_distance": 0.05, "ema_slope": 0.02, "avg_dollar_volume": 1e6, "gap_pct": 0.0},
            {"symbol": "OK", "close": 5.0, "rvol": 2.0, "atr_pct": 0.1, "range_expansion": 1.5, "close_location": 0.8, "ema_distance": 0.05, "ema_slope": 0.02, "avg_dollar_volume": 1e6, "gap_pct": 0.0},
        ]
    )
    cfg = PrefilterConfig(price_min=1.0, price_max=20.0, rvol_min=1.0, rvol_max=8.0)
    cset = apply_prefilter(feats, cfg, signal_date=date(2026, 5, 11), trade_date=date(2026, 5, 12), universe=UniverseConfig())
    assert "BLOW" not in cset.candidates.index
    assert "OK" in cset.candidates.index


def test_rejected_kept_with_reasons():
    feats = _features(
        [
            {"symbol": "REJECT", "close": 5.0, "rvol": 0.2, "atr_pct": 0.1, "range_expansion": 0.5, "close_location": 0.3, "ema_distance": -0.1, "ema_slope": -0.05, "avg_dollar_volume": 1e6, "gap_pct": 0.0},
        ]
    )
    cfg = PrefilterConfig(
        price_min=1.0,
        price_max=20.0,
        rvol_min=1.5,
        atr_pct_min=0.06,
        range_expansion_min=1.25,
        close_location_min=0.6,
        ema_distance_min=0.0,
        ema_slope_min=0.0,
    )
    cset = apply_prefilter(feats, cfg, signal_date=date(2026, 5, 11), trade_date=date(2026, 5, 12), universe=UniverseConfig())
    assert "REJECT" in cset.all_decisions.index
    reasons = cset.all_decisions.loc["REJECT"]["rejection_reasons"]
    assert "rvol_min" in reasons
    assert "range_expansion_min" in reasons
    assert "close_location_min" in reasons
    assert "ema_distance_min" in reasons
    assert "ema_slope_min" in reasons


def test_ranking_sorts_by_signal_strength_desc():
    feats = _features(
        [
            {"symbol": "STRONG", "close": 5.0, "rvol": 5.0, "atr_pct": 0.1, "range_expansion": 3.0, "close_location": 0.9, "ema_distance": 0.10, "ema_slope": 0.05, "avg_dollar_volume": 1e6, "gap_pct": 0.0},
            {"symbol": "MEDIUM", "close": 5.0, "rvol": 3.0, "atr_pct": 0.1, "range_expansion": 2.0, "close_location": 0.8, "ema_distance": 0.05, "ema_slope": 0.02, "avg_dollar_volume": 1e6, "gap_pct": 0.0},
            {"symbol": "WEAK", "close": 5.0, "rvol": 1.6, "atr_pct": 0.1, "range_expansion": 1.3, "close_location": 0.7, "ema_distance": 0.01, "ema_slope": 0.005, "avg_dollar_volume": 1e6, "gap_pct": 0.0},
        ]
    )
    cfg = PrefilterConfig(price_min=1.0, price_max=20.0, rvol_min=1.5)
    cset = apply_prefilter(feats, cfg, signal_date=date(2026, 5, 11), trade_date=date(2026, 5, 12), universe=UniverseConfig())
    ranks = cset.candidates.reset_index()[["symbol", "rank"]].set_index("symbol")
    assert ranks.loc["STRONG", "rank"] < ranks.loc["MEDIUM", "rank"]
    assert ranks.loc["MEDIUM", "rank"] < ranks.loc["WEAK", "rank"]
