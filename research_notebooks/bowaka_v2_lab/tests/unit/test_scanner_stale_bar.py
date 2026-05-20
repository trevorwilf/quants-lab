"""Stale-bar enforcement happens before feature compute (Report §15.1 P0)."""
from __future__ import annotations

import datetime as _dt

import pandas as pd
import pytest

from bowaka_v2_lab.scanner.scan_loop import ScanSkipReason, evaluate_one_scan
from tests.fixtures.build_minute_fixture import make_minute_bars


def test_stale_bar_skipped_before_feature_compute() -> None:
    # scan_ts is 10 minutes after the last bar — max_bar_age=60 → stale.
    sd = _dt.date(2024, 9, 4)
    bars = make_minute_bars("AAA", sd, minutes=30)
    scan_ts = pd.Timestamp("2024-09-04 14:10:00", tz="UTC")  # last bar at 14:00 UTC = 10:00 ET
    cfg = {
        "market_data": {"feed": "iex", "max_bar_age_seconds": 60},
        "scanner": {"max_candidates_per_scan": 10, "max_entries_per_scan": 10},
        "signals": {},
        "historical_features": {},
    }
    universe = {
        "universe_hash": "sha256:test",
        "symbols": [{
            "symbol": "AAA", "exchange": "NASDAQ", "venue_code": "XNAS",
            "instrument_class": "operating_equity",
            "eligible_for_bowaka_equity_bucket": True,
        }],
    }
    daily_cache = pd.DataFrame([{
        "symbol": "AAA", "prior_close": 100.0,
        "avg_dollar_volume_20d": 5_000_000, "prior_atr_pct": 0.02,
        "ema_slope_prior": 0.01,
    }])
    result = evaluate_one_scan(
        cfg=cfg, universe_snapshot=universe, daily_cache=daily_cache,
        volume_curve=None, state={},
        scan_ts=scan_ts,
        bars_supplier=lambda sym, ts: bars,
    )
    # No candidates emitted; gate_dump shows stale_bar skip.
    assert result.emitted == []
    stale_entries = [d for d in result.gate_dump if d.get("skipped") == ScanSkipReason.STALE_BAR.value]
    assert len(stale_entries) >= 1


def test_fresh_bar_proceeds_through_evaluation() -> None:
    sd = _dt.date(2024, 9, 4)
    bars = make_minute_bars("AAA", sd, minutes=30, drift_per_minute=0.5)
    # scan_ts within max_bar_age of last bar (last bar = 09:30+29 = 09:59 ET = 13:59 UTC)
    scan_ts = pd.Timestamp("2024-09-04 14:00:00", tz="UTC")
    cfg = {
        "market_data": {"feed": "iex", "max_bar_age_seconds": 90},
        "scanner": {"max_candidates_per_scan": 10, "max_entries_per_scan": 10},
        "signals": {},
        "historical_features": {},
    }
    universe = {
        "universe_hash": "sha256:test",
        "symbols": [{
            "symbol": "AAA", "exchange": "NASDAQ", "venue_code": "XNAS",
            "instrument_class": "operating_equity",
            "eligible_for_bowaka_equity_bucket": True,
        }],
    }
    daily_cache = pd.DataFrame([{
        "symbol": "AAA", "prior_close": 100.0,
        "avg_dollar_volume_20d": 5_000_000, "prior_atr_pct": 0.02,
        "ema_slope_prior": 0.01,
    }])
    result = evaluate_one_scan(
        cfg=cfg, universe_snapshot=universe, daily_cache=daily_cache,
        volume_curve=None, state={},
        scan_ts=scan_ts, bars_supplier=lambda sym, ts: bars,
    )
    stale_entries = [d for d in result.gate_dump if d.get("skipped") == ScanSkipReason.STALE_BAR.value]
    assert len(stale_entries) == 0
