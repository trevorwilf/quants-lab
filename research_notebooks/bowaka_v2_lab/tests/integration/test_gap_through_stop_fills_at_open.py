"""Realism Remediation 2 Phase 7 (Task 3 robustness) — a gap-through stop
fills at the bar's OPEN, NOT at the stop price.

When a minute opens already below the stop (the prior session's close was
above, today's open is well below), the bracket cannot fill at the stop price
— the realistic fill is the bar's open, taking the gap loss. The
``exit_reason`` is ``gap_stop`` (not ``stop``), and ``exit_slippage_bps`` is
reported against the stop reference price.

This integration test pins the gap-through contract across multiple gap
magnitudes and shapes (clean opens vs intra-bar lows below the open).
"""
from __future__ import annotations

import datetime as _dt
from typing import Any

import pandas as pd
import pytest

from bowaka_v2_lab.sim.exits import walk_lot_exit
from bowaka_v2_lab.sim.portfolio import Position


_SYMBOL = "AAA"


def _path(rows: list[dict]) -> pd.DataFrame:
    base = pd.Timestamp("2024-09-05 09:30", tz="America/New_York").tz_convert("UTC")
    out = []
    for i, r in enumerate(rows):
        out.append({
            "symbol": _SYMBOL,
            "timestamp": base + pd.Timedelta(minutes=i),
            "open": r["o"], "high": r["h"], "low": r["l"], "close": r["c"],
            "volume": r.get("v", 1_000.0),
        })
    return pd.DataFrame(out)


def _lot(entry_price: float = 100.0, stop_price: float = 92.0) -> Position:
    base = pd.Timestamp("2024-09-04 09:30", tz="America/New_York").tz_convert("UTC")
    return Position(
        symbol=_SYMBOL, entry_date=_dt.date(2024, 9, 4),
        entry_price=entry_price, qty=10,
        stop_pct=0.08, target_pct=0.15, max_hold_days=3,
        entry_session=_dt.date(2024, 9, 4),
        entry_timestamp=base.isoformat(),
        stop_price=stop_price, target_price=entry_price * 1.15,
    )


@pytest.mark.parametrize("gap_open,gap_high,gap_low,gap_close", [
    (88.0, 89.0, 86.0, 87.0),   # small gap below stop
    (80.0, 81.0, 78.0, 79.0),   # mid gap
    (70.0, 71.0, 65.0, 66.0),   # large gap
])
def test_gap_through_stop_fills_at_open_various_magnitudes(
    gap_open: float, gap_high: float, gap_low: float, gap_close: float,
) -> None:
    """A minute that OPENS below the stop fills at the OPEN, not the stop.
    The reason is ``gap_stop`` and the slippage is measured against the stop
    reference (the actual loss the trader bears)."""
    path = _path([
        {"o": 100.0, "h": 100.5, "l": 99.8, "c": 100.0},  # fill bar
        {"o": gap_open, "h": gap_high, "l": gap_low, "c": gap_close},
    ])
    ev = walk_lot_exit(_lot(), path, exit_cfg={})
    assert ev is not None
    assert ev.exit_reason == "gap_stop", (
        f"a minute that opens below the stop must fire gap_stop, got {ev.exit_reason!r}"
    )
    assert ev.exit_price == gap_open, (
        f"a gap-through fills at the OPEN ({gap_open}), not the stop (92.0); "
        f"got exit_price={ev.exit_price}"
    )
    # Slippage measured vs the 92.0 stop reference (a worse-than-bracket fill
    # produces a NEGATIVE slippage_bps for a long).
    expected_slip_bps = (gap_open - 92.0) / 92.0 * 10_000.0
    assert abs(ev.exit_slippage_bps - expected_slip_bps) < 1e-6


def test_gap_stop_takes_priority_over_intraday_recovery() -> None:
    """A minute that gaps below the stop fires `gap_stop` even if the bar's
    HIGH later recovers above the stop — at the open the bracket would have
    been hit."""
    path = _path([
        {"o": 100.0, "h": 100.5, "l": 99.8, "c": 100.0},  # fill bar
        # Opens at 85 (well below the 92 stop), recovers intra-bar to 95 close —
        # the OPEN is the realistic gap-stop fill.
        {"o": 85.0, "h": 95.0, "l": 84.5, "c": 95.0},
    ])
    ev = walk_lot_exit(_lot(), path, exit_cfg={})
    assert ev is not None
    assert ev.exit_reason == "gap_stop"
    assert ev.exit_price == 85.0


def test_no_gap_when_open_above_stop_even_if_low_dips_below() -> None:
    """A minute whose OPEN is ABOVE the stop, but whose LOW dips below, is
    a regular ``stop`` (NOT ``gap_stop``) — the bracket fills at the stop
    price as it sweeps the price down through it."""
    path = _path([
        {"o": 100.0, "h": 100.5, "l": 99.8, "c": 100.0},  # fill bar
        # Opens at 95 (above the 92 stop) — low drops below 92 intra-bar.
        {"o": 95.0, "h": 95.5, "l": 91.0, "c": 91.5},
    ])
    ev = walk_lot_exit(_lot(), path, exit_cfg={})
    assert ev is not None
    assert ev.exit_reason == "stop", (
        f"an open-above-stop with intra-bar low-through-stop is a regular stop, "
        f"got {ev.exit_reason!r}"
    )
    assert ev.exit_price == 92.0  # filled at the stop price
