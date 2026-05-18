"""Phase fidelity-2: ``CandidateSet.all_decisions`` carries every row + reasons.

The replay must retain rejected candidates so notebooks 05/06/07 can build
rejected-candidate counterfactuals. This test feeds a small fixture and
asserts every input row appears in ``all_decisions`` with rejection_reasons,
instrument_class, and the lineage columns.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from bowaka_lab.config.models import PrefilterConfig, UniverseConfig
from bowaka_lab.features.daily_features import compute_daily_features
from bowaka_lab.features.prefilter import apply_prefilter


@pytest.fixture
def feature_frame():
    """A minimal pre-computed features DataFrame indexed by symbol."""
    rows = [
        {"symbol": "AAPL", "close": 10.0, "avg_dollar_volume": 5_000_000, "rvol": 2.0,
         "atr_pct": 0.10, "range_expansion": 1.5, "close_location": 0.8,
         "ema_distance": 0.05, "ema_slope": 0.02, "gap_pct": 0.0},
        {"symbol": "PENNY", "close": 0.5, "avg_dollar_volume": 5_000_000, "rvol": 2.0,
         "atr_pct": 0.10, "range_expansion": 1.5, "close_location": 0.8,
         "ema_distance": 0.05, "ema_slope": 0.02, "gap_pct": 0.0},
        {"symbol": "QUIET", "close": 10.0, "avg_dollar_volume": 5_000_000, "rvol": 0.5,
         "atr_pct": 0.10, "range_expansion": 1.5, "close_location": 0.8,
         "ema_distance": 0.05, "ema_slope": 0.02, "gap_pct": 0.0},
        {"symbol": "TSLL", "close": 10.0, "avg_dollar_volume": 5_000_000, "rvol": 2.0,
         "atr_pct": 0.10, "range_expansion": 1.5, "close_location": 0.8,
         "ema_distance": 0.05, "ema_slope": 0.02, "gap_pct": 0.0},  # blocklisted
    ]
    return pd.DataFrame(rows).set_index("symbol")


@pytest.fixture
def asset_snapshot():
    return pd.DataFrame(
        [
            {"symbol": "AAPL",  "name": "APPLE INC",                          "asset_class": "us_equity"},
            {"symbol": "PENNY", "name": "PENNY STOCK INC",                    "asset_class": "us_equity"},
            {"symbol": "QUIET", "name": "QUIET STOCK INC",                    "asset_class": "us_equity"},
            {"symbol": "TSLL",  "name": "DIREXION DAILY TSLA BULL 1.5X",      "asset_class": "us_equity"},
        ]
    )


def test_all_decisions_is_superset_of_candidates(feature_frame, asset_snapshot):
    cfg = PrefilterConfig(price_min=1.0, price_max=20.0)
    universe = UniverseConfig(ticker_blocklist=["TSLL", "CONL", "SMCX"])
    cset = apply_prefilter(
        feature_frame, cfg,
        signal_date=date(2026, 1, 1), trade_date=date(2026, 1, 2),
        asset_snapshot=asset_snapshot, universe=universe,
    )
    # all_decisions includes EVERY input symbol
    all_syms = set(cset.all_decisions.index.tolist())
    assert all_syms == {"AAPL", "PENNY", "QUIET", "TSLL"}
    cand_syms = set(cset.candidates.index.tolist())
    assert cand_syms.issubset(all_syms)
    # AAPL passes; the others should not.
    assert "AAPL" in cand_syms
    assert "PENNY" not in cand_syms  # price_min
    assert "QUIET" not in cand_syms  # rvol_min
    assert "TSLL" not in cand_syms  # blocklist


def test_all_decisions_carries_rejection_reasons(feature_frame, asset_snapshot):
    cfg = PrefilterConfig(price_min=1.0, price_max=20.0, rvol_min=1.5)
    universe = UniverseConfig(ticker_blocklist=["TSLL", "CONL", "SMCX"])
    cset = apply_prefilter(
        feature_frame, cfg,
        signal_date=date(2026, 1, 1), trade_date=date(2026, 1, 2),
        asset_snapshot=asset_snapshot, universe=universe,
    )
    decisions = cset.all_decisions
    assert "rejection_reasons" in decisions.columns
    assert "instrument_class" in decisions.columns
    assert "classification_reason" in decisions.columns
    # AAPL has no rejection reasons; PENNY rejects on price_min; TSLL on instrument_class.
    assert decisions.loc["AAPL", "rejection_reasons"] == []
    assert "price_min" in decisions.loc["PENNY", "rejection_reasons"]
    assert "instrument_class" in decisions.loc["TSLL", "rejection_reasons"]
    assert decisions.loc["TSLL", "instrument_class"] == "leveraged_etp"
    assert decisions.loc["TSLL", "classification_reason"] == "ticker_blocklist"


def test_all_decisions_final_decision_column(feature_frame, asset_snapshot):
    cfg = PrefilterConfig(price_min=1.0, price_max=20.0)
    universe = UniverseConfig(ticker_blocklist=["TSLL", "CONL", "SMCX"])
    cset = apply_prefilter(
        feature_frame, cfg,
        signal_date=date(2026, 1, 1), trade_date=date(2026, 1, 2),
        asset_snapshot=asset_snapshot, universe=universe,
    )
    fd = cset.all_decisions["final_decision"]
    assert set(fd.unique()).issubset({"candidate", "rejected"})
    assert fd.loc["AAPL"] == "candidate"
    assert fd.loc["TSLL"] == "rejected"
