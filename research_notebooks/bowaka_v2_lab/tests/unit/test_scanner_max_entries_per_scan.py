"""max_entries_per_scan caps emitted candidates (Report §15.2 P1)."""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.scanner.scan_loop import ScanSkipReason, evaluate_one_scan
from tests.fixtures.build_minute_fixture import make_minute_bars


def _setup_symbols(n: int):
    sd = _dt.date(2024, 9, 4)
    universe = {
        "universe_hash": "sha256:test",
        "symbols": [
            {"symbol": f"S{i:02d}", "exchange": "NASDAQ", "venue_code": "XNAS",
             "instrument_class": "operating_equity",
             "eligible_for_bowaka_equity_bucket": True}
            for i in range(n)
        ],
    }
    daily_cache = pd.DataFrame([
        {"symbol": f"S{i:02d}", "prior_close": 100.0,
         "avg_dollar_volume_20d": 5_000_000, "prior_atr_pct": 0.02,
         "ema_slope_prior": 0.01}
        for i in range(n)
    ])
    bars_by_sym = {f"S{i:02d}": make_minute_bars(f"S{i:02d}", sd, minutes=30,
                                                   drift_per_minute=0.5 + i * 0.01)
                    for i in range(n)}
    return universe, daily_cache, bars_by_sym


def test_max_entries_caps_below_max_candidates() -> None:
    universe, daily_cache, bars = _setup_symbols(8)
    cfg = {
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "scanner": {"max_candidates_per_scan": 10, "max_entries_per_scan": 3},
        "signals": {},
        "historical_features": {},
    }
    scan_ts = pd.Timestamp("2024-09-04 14:00:00", tz="UTC")
    result = evaluate_one_scan(
        cfg=cfg, universe_snapshot=universe, daily_cache=daily_cache,
        volume_curve=None, state={},
        scan_ts=scan_ts, bars_supplier=lambda sym, ts: bars[sym],
    )
    assert len(result.emitted) <= 3
    capped = [d for d in result.gate_dump if d.get("skipped") == ScanSkipReason.MAX_ENTRIES_CAP.value]
    if len(result.emitted) == 3:
        # 8 symbols passed gates, 3 emitted, 5 capped.
        assert len(capped) >= 1


def test_no_cap_when_under_limit() -> None:
    universe, daily_cache, bars = _setup_symbols(2)
    cfg = {
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "scanner": {"max_candidates_per_scan": 10, "max_entries_per_scan": 5},
        "signals": {},
        "historical_features": {},
    }
    scan_ts = pd.Timestamp("2024-09-04 14:00:00", tz="UTC")
    result = evaluate_one_scan(
        cfg=cfg, universe_snapshot=universe, daily_cache=daily_cache,
        volume_curve=None, state={},
        scan_ts=scan_ts, bars_supplier=lambda sym, ts: bars[sym],
    )
    capped = [d for d in result.gate_dump if d.get("skipped") == ScanSkipReason.MAX_ENTRIES_CAP.value]
    assert capped == []
