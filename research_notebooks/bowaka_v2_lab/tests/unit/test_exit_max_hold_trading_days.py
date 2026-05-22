"""Phase 7 — max_hold counts XNYS trading days: entry Mon, max_hold 3 → EOD Wed.

``max_hold_exit_session`` returns the close-of-session N where
N = entry_session + (max_hold_days - 1) trading days, so a Monday entry with
max_hold_days=3 must exit at the close of that Wednesday.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.exits import max_hold_exit_session, walk_lot_exit
from bowaka_v2_lab.sim.portfolio import Position

# time_stop disabled so the walk runs to the max-hold horizon, not 15:45.
_NO_TIME_STOP = {"time_stop": {"enabled": False}}


def test_max_hold_exit_session_mon_plus_three_is_wed() -> None:
    # Mon 2024-09-09 + 3 trading days → Wed 2024-09-11 (Mon+0, Tue+1, Wed+2).
    assert max_hold_exit_session(_dt.date(2024, 9, 9), 3) == _dt.date(2024, 9, 11)


def _multi_day_path(days: list[_dt.date]) -> pd.DataFrame:
    """A quiet minute path (flat at 100) over several sessions — 09:31..16:00 ET
    each day — that never trips a bracket."""
    rows = []
    for d in days:
        ts = pd.Timestamp(f"{d} 09:31", tz="America/New_York")
        end = pd.Timestamp(f"{d} 16:00", tz="America/New_York")
        while ts <= end:
            rows.append({
                "symbol": "AAA",
                "timestamp": ts.tz_convert("UTC"),
                "open": 100.0, "high": 100.3, "low": 99.7, "close": 100.0,
                "volume": 1000.0,
            })
            ts = ts + pd.Timedelta(minutes=1)
    return pd.DataFrame(rows)


def test_max_hold_exit_by_eod_wednesday() -> None:
    # Entry Monday 2024-09-09; max_hold_days=3 → exit by EOD Wed 2024-09-11.
    entry = _dt.date(2024, 9, 9)
    base = pd.Timestamp(f"{entry} 09:30", tz="America/New_York").tz_convert("UTC")
    lot = Position(
        symbol="AAA", entry_date=entry, entry_price=100.0, qty=10,
        stop_pct=0.30, target_pct=0.30, max_hold_days=3,
        entry_session=entry, entry_timestamp=base.isoformat(),
        stop_price=70.0, target_price=130.0,
    )
    # Supply Mon/Tue/Wed/Thu — the walk must stop at Wednesday's close.
    days = [_dt.date(2024, 9, 9), _dt.date(2024, 9, 10),
            _dt.date(2024, 9, 11), _dt.date(2024, 9, 12)]
    ev = walk_lot_exit(lot, _multi_day_path(days), exit_cfg=_NO_TIME_STOP)
    assert ev is not None
    assert ev.exit_reason == "max_hold"
    assert ev.exit_date == _dt.date(2024, 9, 11)
