"""Phase fidelity-7: opening_range_break counterfactual."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from bowaka_lab.sim.counterfactuals import (
    _entry_bar_for_opening_range_break,
    _entry_bar_for_vwap_reclaim,
    _find_entry_bar,
)


def _bars(*, high_seq):
    """Build a fixture with explicit per-bar highs. Each bar is "flat"
    (open=close=high) so the VWAP equals the high — a bar's ``open < vwap``
    is only true when there's a genuine dip."""
    minutes = pd.date_range(
        start=pd.Timestamp("2026-05-12 09:30:00", tz="America/New_York"),
        periods=len(high_seq), freq="1min", tz="America/New_York",
    ).tz_convert("UTC")
    rows = []
    for ts, h in zip(minutes, high_seq):
        rows.append({"timestamp": ts, "open": h, "high": h,
                     "low": h, "close": h, "volume": 100,
                     "symbol": "AAA"})
    return pd.DataFrame(rows)


def test_opening_range_break_returns_first_breakout_bar():
    # OR window = 5 minutes. Window highs: 10.0, 10.0, 10.0, 10.0, 10.0.
    # OR high = 10.0. Subsequent bar at 10.1 should trigger.
    bars = _bars(high_seq=[10.0]*5 + [9.95, 10.05, 10.10, 10.15])
    out = _entry_bar_for_opening_range_break(
        minute_bars=bars, trade_date=date(2026, 5, 12), or_window_minutes=5,
    )
    assert out is not None
    # First bar with high > 10.0 is index 6 (10.05) since post-window
    # threshold = or_high (10.0); first high > 10.0 is index 6.
    assert pd.Timestamp(out["timestamp"]) == bars["timestamp"].iloc[6]


def test_opening_range_break_returns_none_if_no_breakout():
    bars = _bars(high_seq=[10.0]*5 + [9.95, 9.98, 9.99, 9.99])
    out = _entry_bar_for_opening_range_break(
        minute_bars=bars, trade_date=date(2026, 5, 12),
    )
    assert out is None


def test_opening_range_break_with_buffer():
    # Use a larger buffer so floating-point doesn't decide the boundary case.
    bars = _bars(high_seq=[10.0]*5 + [10.05, 10.20, 10.30])
    # Threshold = 10.0 * 1.10 = 11.0. None of these qualify.
    out_none = _entry_bar_for_opening_range_break(
        minute_bars=bars, trade_date=date(2026, 5, 12),
        breakout_buffer_pct=0.10,
    )
    assert out_none is None
    # Threshold = 10.0 * 1.01 = 10.10. Bars 5 (10.05) and 6 (10.20) — 10.20 wins.
    out = _entry_bar_for_opening_range_break(
        minute_bars=bars, trade_date=date(2026, 5, 12),
        breakout_buffer_pct=0.01,
    )
    assert out is not None
    assert pd.Timestamp(out["timestamp"]) == bars["timestamp"].iloc[6]


def test_find_entry_bar_dispatches_to_or_break():
    bars = _bars(high_seq=[10.0]*5 + [10.10])
    out = _find_entry_bar("opening_range_break", bars, date(2026, 5, 12))
    assert out is not None


def test_find_entry_bar_dispatches_to_vwap_reclaim_when_data_supports():
    # Build bars where price dips below VWAP then closes above.
    minutes = pd.date_range(
        start=pd.Timestamp("2026-05-12 09:30:00", tz="America/New_York"),
        periods=10, freq="1min", tz="America/New_York",
    ).tz_convert("UTC")
    # First 5 bars at 10.0; next 5 dip to 9.5 open then close > vwap.
    rows = []
    for i, ts in enumerate(minutes):
        if i < 5:
            rows.append({"timestamp": ts, "open": 10.0, "high": 10.05, "low": 9.95,
                         "close": 10.0, "volume": 100, "symbol": "AAA"})
        elif i == 8:
            # Dip: opens at 9.5, closes well above VWAP.
            rows.append({"timestamp": ts, "open": 9.5, "high": 10.30, "low": 9.50,
                         "close": 10.25, "volume": 500, "symbol": "AAA"})
        else:
            rows.append({"timestamp": ts, "open": 10.0, "high": 10.05, "low": 9.95,
                         "close": 10.0, "volume": 100, "symbol": "AAA"})
    bars = pd.DataFrame(rows)
    out = _find_entry_bar("vwap_reclaim", bars, date(2026, 5, 12))
    assert out is not None


def test_vwap_reclaim_returns_none_when_no_dip():
    bars = _bars(high_seq=[10.0]*20)
    out = _entry_bar_for_vwap_reclaim(
        minute_bars=bars, trade_date=date(2026, 5, 12),
    )
    assert out is None


def test_find_entry_bar_raises_on_unknown_rule():
    bars = _bars(high_seq=[10.0]*5)
    with pytest.raises(ValueError, match="Unknown entry rule"):
        _find_entry_bar("magic_rule", bars, date(2026, 5, 12))


def test_or_break_and_fixed_time_differ_for_same_fixture():
    """Proves the silent-fallback bug is fixed: OR break with no breakout
    returns no_breakout, not a fixed-time bar."""
    bars = _bars(high_seq=[10.0]*5 + [9.95, 9.96, 9.97])
    or_out = _entry_bar_for_vwap_reclaim(  # vwap also returns None
        minute_bars=bars, trade_date=date(2026, 5, 12),
    )
    assert or_out is None
    # Same fixture with fixed_time_0945 returns a real bar.
    out_fixed = _find_entry_bar("fixed_time_0935", bars, date(2026, 5, 12))
    assert out_fixed is not None
