"""lake_has_bars must detect daily bars under the backfilled adjustment.

The backfill writes daily bars under ``split_adjusted`` (the bowaka_v2 default),
NOT the legacy ``raw``. A raw-only probe made a fresh SIP backfill invisible, so
``feed='auto'`` would never cut over to SIP even with SIP bars + quotes present.
This pins the fix + the full intended_realism cutover.
"""
from __future__ import annotations

import pandas as pd

from bowaka_common.marketdata import layout
from bowaka_v2_lab.optuna.autoconfig import (
    detect_best_feed,
    lake_has_bars,
    lake_has_quotes,
)


def _write(path, df) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _daily(sym):
    return pd.DataFrame({
        "symbol": [sym], "timestamp": [pd.Timestamp("2025-05-01", tz="UTC")],
        "open": [10.0], "high": [10.5], "low": [9.5], "close": [10.0], "volume": [1000],
    })


def _quotes(sym):
    return pd.DataFrame({
        "symbol": [sym], "timestamp": [pd.Timestamp("2025-05-01 14:00", tz="UTC")],
        "bid": [9.99], "ask": [10.01], "bid_size": [100.0], "ask_size": [100.0],
        "conditions": ["R"],
    })


def test_lake_has_bars_detects_split_adjusted_only(tmp_path) -> None:
    # SIP daily bars written ONLY under split_adjusted (no legacy raw partition).
    _write(layout.daily_bars_path(tmp_path, "AAA", feed="sip", adjustment="split_adjusted"),
           _daily("AAA"))
    assert lake_has_bars(tmp_path, "sip") is True  # the fix (was False on raw-only probe)
    assert lake_has_bars(tmp_path, "iex") is False  # other feeds unaffected


def test_sip_bars_plus_quotes_cuts_over_to_intended_realism(tmp_path) -> None:
    _write(layout.daily_bars_path(tmp_path, "AAA", feed="sip", adjustment="split_adjusted"),
           _daily("AAA"))
    # Bars only -> current_code_parity (no quotes yet).
    feed, mode, _ = detect_best_feed(tmp_path)
    assert (feed, mode) == ("sip", "current_code_parity")
    # Add SIP quotes -> full intended_realism.
    _write(layout.quotes_path(tmp_path, "AAA", 2025, 5, feed="sip"), _quotes("AAA"))
    assert lake_has_quotes(tmp_path, "sip") is True
    feed, mode, _ = detect_best_feed(tmp_path)
    assert (feed, mode) == ("sip", "intended_realism")
