"""Phase 1 §3 — failing-gate dump_row is NOT allocated when collect_gate_dump=False.

Speedup report v2 §9.5 "Patch sketch": the objective-minimal path
(``collect_gate_dump=False``) is the dominant runtime path; it was building
one full ``_row(...)`` dict per failing symbol per scan and discarding it.
The Phase 1 refactor defers that allocation: when gates fail and dumps are
not collected, only ``rejection_counts[GATE_FAILED]`` is bumped.

The test is observable through two channels:
  (1) ``result.gate_dump`` is empty;
  (2) ``result.rejection_counts[GATE_FAILED]`` equals the number of failing
      symbols at the scan.
Combined with the existing parity test
``tests/parity/test_scan_loop_objective_mode_emissions_match.py`` (which
verifies emitted-candidate parity across both modes on the same fixture),
this proves the optimization is observation-equivalent.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from bowaka_v2_lab.scanner.scan_context import build_scan_session_context
from bowaka_v2_lab.scanner.scan_loop import (
    ScanSkipReason,
    evaluate_one_scan,
)
from tests.fixtures.build_minute_fixture import make_minute_bars


def _cfg_with_extreme_gate() -> dict:
    """A config whose gates force most/all symbols into GATE_FAILED."""
    return {
        "strategy_id": "bowaka_v2",
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "scanner": {
            "max_candidates_per_scan": 5,
            "max_entries_per_scan": 3,
            "min_signal_strength": 0.0,
            "signal_expiry_seconds": 600,
            "same_symbol_entries_per_day": 1,
            "symbol_cooldown_minutes": 390,
        },
        # Set an unachievable RVOL minimum so every symbol fails gates.
        "signals": {
            "rvol_so_far_min": 1000.0,
            "rvol_so_far_max": 99999.0,
        },
        "execution": {
            "max_spread_bps": 200,
            "max_quote_age_seconds": 60,
            "order_type": "marketable_limit",
        },
        "historical_features": {
            "volume_curve": {
                "bucket_edges": [250_000, 500_000, 1_000_000, 5_000_000, 20_000_000],
                "fallback_opening_15m_share": 0.08,
            },
        },
    }


def _universe(symbols: list[str]) -> dict:
    return {
        "universe_hash": "sha256:t",
        "symbols": [
            {
                "symbol": s,
                "exchange": "NASDAQ",
                "venue_code": "XNAS",
                "instrument_class": "operating_equity",
                "eligible_for_bowaka_equity_bucket": True,
            }
            for s in symbols
        ],
    }


def _daily_cache(symbols: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": s,
                "prior_close": 100.0,
                "avg_dollar_volume_20d": 5_000_000,
                "avg_volume_20d": 50_000,
                "prior_atr_pct": 0.02,
                "prior_atr_14d": 2.0,
                "ema_slope_prior": 0.01,
                "ema_10_prior": 100.0,
            }
            for s in symbols
        ]
    )


def _bars_supplier(symbols: list[str]):
    sd = dt.date(2024, 9, 4)
    bars_by_symbol = {
        s: make_minute_bars(s, sd, minutes=30, drift_per_minute=0.5, minute_volume=10_000)
        for s in symbols
    }
    return lambda sym, ts: bars_by_symbol.get(sym, pd.DataFrame())


def test_no_dump_row_built_when_collect_gate_dump_false() -> None:
    """All symbols fail gates; ``gate_dump`` stays empty; counter is correct."""
    symbols = ["AAA", "BBB", "CCC", "DDD", "EEE"]
    cfg = _cfg_with_extreme_gate()
    universe = _universe(symbols)
    daily_cache = _daily_cache(symbols)
    bars_supplier = _bars_supplier(symbols)
    scan_ts = pd.Timestamp("2024-09-04T14:00:00", tz="UTC")
    scan_times = [scan_ts]

    ctx = build_scan_session_context(
        cfg, daily_cache, universe, scan_times, collect_gate_dump=False,
    )
    result = evaluate_one_scan(
        cfg=cfg,
        universe_snapshot=universe,
        daily_cache=daily_cache,
        volume_curve=None,
        state={},
        scan_ts=scan_ts,
        bars_supplier=bars_supplier,
        scan_context=ctx,
        collect_gate_dump=False,
    )

    # No per-symbol gate-dump rows.
    assert result.gate_dump == []
    # Every symbol funneled into the GATE_FAILED bucket (no other skip applies).
    expected = len(symbols)
    assert (
        result.rejection_counts.get(ScanSkipReason.GATE_FAILED.value, 0) == expected
    )
    # No candidates emitted (all symbols failed).
    assert result.emitted == []


def test_full_mode_still_builds_gate_dump_rows() -> None:
    """The same fixture under ``collect_gate_dump=True`` builds one row per symbol."""
    symbols = ["AAA", "BBB", "CCC", "DDD", "EEE"]
    cfg = _cfg_with_extreme_gate()
    universe = _universe(symbols)
    daily_cache = _daily_cache(symbols)
    bars_supplier = _bars_supplier(symbols)
    scan_ts = pd.Timestamp("2024-09-04T14:00:00", tz="UTC")
    scan_times = [scan_ts]

    ctx = build_scan_session_context(
        cfg, daily_cache, universe, scan_times, collect_gate_dump=True,
    )
    result = evaluate_one_scan(
        cfg=cfg,
        universe_snapshot=universe,
        daily_cache=daily_cache,
        volume_curve=None,
        state={},
        scan_ts=scan_ts,
        bars_supplier=bars_supplier,
        scan_context=ctx,
        collect_gate_dump=True,
    )

    # Every symbol contributes one full gate-dump row.
    assert len(result.gate_dump) == len(symbols)
    reasons = [row.get("rejection_reason") for row in result.gate_dump]
    assert set(reasons) == {ScanSkipReason.GATE_FAILED.value}
