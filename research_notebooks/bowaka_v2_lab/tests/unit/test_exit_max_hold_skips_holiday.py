"""Phase 7 — a market holiday inside the max-hold window does NOT count.

Entry Tue 2024-12-24 with max_hold_days=3. Wed 2024-12-25 is Christmas (XNYS
closed). Trading days on/after the entry: 12-24 (+0), 12-26 (+1), 12-27 (+2) —
so the lot must exit on Fri 2024-12-27, not Thu 2024-12-26. A naive calendar-day
or bdate_range count would mis-fire a day early.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.exits import max_hold_exit_session, walk_lot_exit
from bowaka_v2_lab.sim.portfolio import Position

_NO_TIME_STOP = {"time_stop": {"enabled": False}}


def test_max_hold_exit_session_skips_christmas() -> None:
    # Tue 12-24 + 3 trading days (12-25 Christmas closed) → Fri 12-27.
    assert max_hold_exit_session(_dt.date(2024, 12, 24), 3) == _dt.date(2024, 12, 27)


def _multi_day_path(days: list[_dt.date]) -> pd.DataFrame:
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


def test_max_hold_walk_skips_holiday() -> None:
    entry = _dt.date(2024, 12, 24)
    base = pd.Timestamp(f"{entry} 09:30", tz="America/New_York").tz_convert("UTC")
    lot = Position(
        symbol="AAA", entry_date=entry, entry_price=100.0, qty=10,
        stop_pct=0.30, target_pct=0.30, max_hold_days=3,
        entry_session=entry, entry_timestamp=base.isoformat(),
        stop_price=70.0, target_price=130.0,
    )
    # Supply the actual trading days (12-25 Christmas is absent — the market is
    # closed, so there are no minute bars for it).
    days = [_dt.date(2024, 12, 24), _dt.date(2024, 12, 26),
            _dt.date(2024, 12, 27), _dt.date(2024, 12, 30)]
    ev = walk_lot_exit(lot, _multi_day_path(days), exit_cfg=_NO_TIME_STOP)
    assert ev is not None
    assert ev.exit_reason == "max_hold"
    # Exits Fri 12-27 — the holiday did not consume a hold day.
    assert ev.exit_date == _dt.date(2024, 12, 27)
