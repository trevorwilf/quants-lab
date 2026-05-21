"""Realism Phase 4 (Task 5) — a stale last minute bar rejects the symbol.

If the last minute bar's timestamp is older than ``max_bar_age_seconds`` from
the scan timestamp, the symbol is rejected; the gate-dump row carries
``rejection_reason == 'stale_bar'`` and no candidate is emitted. This hardens
the §15.1 P0 behaviour with the Phase-4 ``rejection_reason`` column.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.scanner.scan_loop import ScanSkipReason, evaluate_one_scan
from tests.fixtures.build_minute_fixture import make_minute_bars


def _universe():
    return {
        "universe_hash": "sha256:test",
        "symbols": [{
            "symbol": "AAA", "exchange": "NASDAQ", "venue_code": "XNAS",
            "instrument_class": "operating_equity",
            "eligible_for_bowaka_equity_bucket": True,
        }],
    }


def _daily_cache():
    return pd.DataFrame([{
        "symbol": "AAA", "prior_close": 100.0,
        "avg_dollar_volume_20d": 5_000_000, "prior_atr_pct": 0.02,
        "ema_slope_prior": 0.01,
    }])


def _fresh_state():
    return {
        "entered_symbols_today": [],
        "in_play_pool": {},
        "symbol_last_emit_ts": {},
        "entries_per_symbol_today": {},
    }


def test_stale_bar_rejected_with_reason() -> None:
    sd = _dt.date(2024, 9, 4)
    # 30 bars from 09:30 ET → last bar 09:59 ET = 13:59 UTC.
    bars = make_minute_bars("AAA", sd, minutes=30)
    # Scan 30 minutes after the last bar — well past max_bar_age_seconds=60.
    scan_ts = pd.Timestamp("2024-09-04 14:29:00", tz="UTC")
    cfg = {
        "market_data": {"feed": "iex", "max_bar_age_seconds": 60},
        "scanner": {"max_candidates_per_scan": 10, "max_entries_per_scan": 10},
        "signals": {},
        "historical_features": {},
    }
    result = evaluate_one_scan(
        cfg=cfg, universe_snapshot=_universe(), daily_cache=_daily_cache(),
        volume_curve=None, state=_fresh_state(),
        scan_ts=scan_ts, bars_supplier=lambda sym, ts: bars,
    )
    assert result.emitted == []
    rows = [r for r in result.gate_dump if r["symbol"] == "AAA"]
    assert len(rows) == 1
    row = rows[0]
    assert row["rejection_reason"] == ScanSkipReason.STALE_BAR.value == "stale_bar"
    assert row["candidate_emitted"] is False
    assert row["bar_age_seconds"] > 60


def test_fresh_bar_not_rejected_as_stale() -> None:
    sd = _dt.date(2024, 9, 4)
    bars = make_minute_bars("AAA", sd, minutes=30, drift_per_minute=0.5)
    # Last bar 09:59 ET = 13:59 UTC; scan one minute later — within max_bar_age.
    scan_ts = pd.Timestamp("2024-09-04 14:00:00", tz="UTC")
    cfg = {
        "market_data": {"feed": "iex", "max_bar_age_seconds": 90},
        "scanner": {"max_candidates_per_scan": 10, "max_entries_per_scan": 10},
        "signals": {},
        "historical_features": {},
    }
    result = evaluate_one_scan(
        cfg=cfg, universe_snapshot=_universe(), daily_cache=_daily_cache(),
        volume_curve=None, state=_fresh_state(),
        scan_ts=scan_ts, bars_supplier=lambda sym, ts: bars,
    )
    stale = [r for r in result.gate_dump if r.get("rejection_reason") == "stale_bar"]
    assert stale == []


def test_stale_threshold_is_exclusive_boundary() -> None:
    # age exactly == max_bar_age_seconds is NOT stale (reject only when older).
    sd = _dt.date(2024, 9, 4)
    bars = make_minute_bars("AAA", sd, minutes=30, drift_per_minute=0.5)
    # Last bar at 13:59 UTC; scan at 13:59 + 90s with max_bar_age 90 → boundary.
    scan_ts = pd.Timestamp("2024-09-04 13:59:00", tz="UTC") + pd.Timedelta(seconds=90)
    cfg = {
        "market_data": {"feed": "iex", "max_bar_age_seconds": 90},
        "scanner": {"max_candidates_per_scan": 10, "max_entries_per_scan": 10},
        "signals": {},
        "historical_features": {},
    }
    result = evaluate_one_scan(
        cfg=cfg, universe_snapshot=_universe(), daily_cache=_daily_cache(),
        volume_curve=None, state=_fresh_state(),
        scan_ts=scan_ts, bars_supplier=lambda sym, ts: bars,
    )
    stale = [r for r in result.gate_dump if r.get("rejection_reason") == "stale_bar"]
    assert stale == [], "age == max_bar_age_seconds must not be stale"
