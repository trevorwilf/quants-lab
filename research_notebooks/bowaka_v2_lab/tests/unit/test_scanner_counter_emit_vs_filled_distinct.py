"""Realism Remediation 2 Phase 7 (audit P1-003) — the scanner's emit-counter
``signal_emits_per_symbol_today`` is DISTINCT from the portfolio's
``entries_per_symbol_today`` (PARENT_FILL count). The scanner increments
emits when it accepts a candidate from gates; the portfolio increments
entries only on a real PARENT_FILL.

This unit test pins the rename + distinct-counter contract.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any

import pandas as pd
import pytest

from bowaka_v2_lab.scanner.scan_loop import evaluate_one_scan
from bowaka_v2_lab.sim.portfolio import Portfolio, Position


_SYMBOL = "AAA"


def _cfg() -> dict[str, Any]:
    return {
        "strategy_id": "bowaka_v2",
        "scanner": {
            "max_candidates_per_scan": 10,
            "max_entries_per_scan": 10,
            "same_symbol_entries_per_day": 5,  # high cap so the test is not capped
            "symbol_cooldown_minutes": 0,      # no cooldown so re-emit on every scan
        },
        "signals": {},
        "score": {},
        "market_data": {"max_bar_age_seconds": 6_000_000},
    }


def _universe() -> dict[str, Any]:
    return {
        "universe_hash": "sha256:test_p7",
        "symbols": [{
            "symbol": _SYMBOL, "exchange": "NASDAQ", "venue_code": "XNAS",
            "instrument_class": "operating_equity",
            "eligible_for_bowaka_equity_bucket": True,
        }],
    }


def _daily_cache() -> pd.DataFrame:
    return pd.DataFrame([{
        "symbol": _SYMBOL, "prior_close": 10.0,
        "avg_dollar_volume_20d": 500_000_000,
        "prior_atr_pct": 0.02, "ema_slope_prior": 0.01,
    }])


def _emitting_bars() -> pd.DataFrame:
    """A short rising path that clears the v2 gates with default config."""
    base = pd.Timestamp("2024-09-04 09:30", tz="UTC")
    rows = [{
        "timestamp": base + pd.Timedelta(minutes=i),
        "open": 10.0 + 0.05 * i,
        "high": 10.10 + 0.05 * i,
        "low": 10.0 + 0.05 * i,
        "close": 10.05 + 0.05 * i,
        "volume": 100_000.0,
    } for i in range(15)]
    return pd.DataFrame(rows)


def _bars_supplier(bars: pd.DataFrame):
    def supplier(symbol: str, cutoff) -> pd.DataFrame:
        ts = pd.Timestamp(cutoff).tz_convert("UTC")
        return bars[bars["timestamp"] <= ts].copy()
    return supplier


def test_emit_counter_is_named_signal_emits_per_symbol_today() -> None:
    """The new emit-counter key on scanner state is
    ``signal_emits_per_symbol_today`` (renamed from ``entries_per_symbol_today``).
    """
    state: dict[str, Any] = {
        "entered_symbols_today": [],
        "in_play_pool": {},
        "symbol_last_emit_ts": {},
        "signal_emits_per_symbol_today": {},
    }
    bars = _emitting_bars()
    result = evaluate_one_scan(
        cfg=_cfg(), universe_snapshot=_universe(), daily_cache=_daily_cache(),
        volume_curve=None, state=state,
        scan_ts=pd.Timestamp("2024-09-04 13:50:00", tz="UTC"),
        bars_supplier=_bars_supplier(bars),
    )
    # State must contain the new key after the scan.
    assert "signal_emits_per_symbol_today" in state, (
        "scanner MUST expose the renamed emit counter (audit P1-003)"
    )
    if result.emitted:
        assert state["signal_emits_per_symbol_today"].get(_SYMBOL, 0) >= 1


def test_scanner_does_not_touch_entries_per_symbol_today_key() -> None:
    """The legacy ``entries_per_symbol_today`` key is now portfolio-only —
    the scanner must NOT increment it on emission. (For one-release back-compat
    the scanner accepts a pre-existing legacy dict; the test below pins that.)"""
    state: dict[str, Any] = {
        "entered_symbols_today": [],
        "in_play_pool": {},
        "symbol_last_emit_ts": {},
        # Intentionally NOT preloading the legacy key — scanner must NOT create it.
        "signal_emits_per_symbol_today": {},
    }
    bars = _emitting_bars()
    evaluate_one_scan(
        cfg=_cfg(), universe_snapshot=_universe(), daily_cache=_daily_cache(),
        volume_curve=None, state=state,
        scan_ts=pd.Timestamp("2024-09-04 13:50:00", tz="UTC"),
        bars_supplier=_bars_supplier(bars),
    )
    # The legacy key must NOT have been created by the scanner.
    assert "entries_per_symbol_today" not in state, (
        "scanner must not write to the portfolio-owned entries_per_symbol_today "
        "key (audit P1-003)"
    )


def test_legacy_entries_per_symbol_today_is_migrated_to_signal_emits() -> None:
    """For one-release back-compat: if a caller pre-loads the legacy key in
    ``state``, the scanner migrates it to the new ``signal_emits_per_symbol_today``
    key without losing counts."""
    state: dict[str, Any] = {
        "entered_symbols_today": [],
        "in_play_pool": {},
        "symbol_last_emit_ts": {},
        "entries_per_symbol_today": {_SYMBOL: 3},  # legacy pre-load
    }
    bars = _emitting_bars()
    evaluate_one_scan(
        cfg=_cfg(), universe_snapshot=_universe(), daily_cache=_daily_cache(),
        volume_curve=None, state=state,
        scan_ts=pd.Timestamp("2024-09-04 13:50:00", tz="UTC"),
        bars_supplier=_bars_supplier(bars),
    )
    # Migration carries the count over to the new key.
    assert state["signal_emits_per_symbol_today"].get(_SYMBOL, 0) >= 3


def test_portfolio_entries_per_symbol_increments_on_add_position() -> None:
    """The portfolio increments ``entries_per_symbol_today`` on each
    ``add_position`` (PARENT_FILL semantics) — distinct from the scanner.
    """
    pf = Portfolio(initial_bankroll=100_000.0)
    sd = _dt.date(2024, 9, 4)
    pf.begin_session(sd)
    # Start: no entries.
    assert pf.state is not None
    assert pf.state.entries_per_symbol_today == {}

    base = pd.Timestamp(f"{sd} 09:35", tz="UTC")
    pos = Position(
        symbol=_SYMBOL, entry_date=sd, entry_price=10.0, qty=100,
        stop_pct=0.08, target_pct=0.15, max_hold_days=3,
        entry_session=sd, entry_timestamp=base.isoformat(),
        stop_price=9.2, target_price=11.5,
        position_id="pos-1",
    )
    pf.add_position(pos)
    assert pf.state.entries_per_symbol_today.get(_SYMBOL) == 1

    # A second lot for the same symbol bumps the per-symbol count to 2.
    pos2 = Position(
        symbol=_SYMBOL, entry_date=sd, entry_price=10.5, qty=50,
        stop_pct=0.08, target_pct=0.15, max_hold_days=3,
        entry_session=sd, entry_timestamp=base.isoformat(),
        stop_price=9.66, target_price=12.075,
        position_id="pos-2",
    )
    pf.add_position(pos2)
    assert pf.state.entries_per_symbol_today.get(_SYMBOL) == 2


def test_two_counters_are_independent() -> None:
    """Scanner emits and portfolio entries are NOT linked — emitting on the
    scanner does not increment portfolio entries, and vice versa."""
    state: dict[str, Any] = {
        "entered_symbols_today": [],
        "in_play_pool": {},
        "symbol_last_emit_ts": {},
        "signal_emits_per_symbol_today": {},
    }
    pf = Portfolio(initial_bankroll=100_000.0)
    pf.begin_session(_dt.date(2024, 9, 4))

    # Run a scan that emits a candidate. No PARENT_FILL happens — portfolio
    # entry count must stay at zero.
    bars = _emitting_bars()
    result = evaluate_one_scan(
        cfg=_cfg(), universe_snapshot=_universe(), daily_cache=_daily_cache(),
        volume_curve=None, state=state,
        scan_ts=pd.Timestamp("2024-09-04 13:50:00", tz="UTC"),
        bars_supplier=_bars_supplier(bars),
    )
    if not result.emitted:
        pytest.skip("scanner emitted no candidate for this test fixture")
    assert state["signal_emits_per_symbol_today"].get(_SYMBOL, 0) >= 1
    assert pf.state is not None
    # Portfolio side untouched.
    assert pf.state.entries_per_symbol_today.get(_SYMBOL, 0) == 0
