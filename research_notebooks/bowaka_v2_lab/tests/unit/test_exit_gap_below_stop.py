"""Phase 7 — a minute whose OPEN is already below the stop → gap stop at open."""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.exits import walk_lot_exit
from bowaka_v2_lab.sim.portfolio import Position


def _minute_path(rows: list[dict]) -> pd.DataFrame:
    base = pd.Timestamp("2024-09-04 09:30", tz="America/New_York").tz_convert("UTC")
    out = []
    for i, r in enumerate(rows):
        out.append({
            "symbol": "AAA",
            "timestamp": base + pd.Timedelta(minutes=i),
            "open": r["o"], "high": r["h"], "low": r["l"], "close": r["c"],
            "volume": 1000.0,
        })
    return pd.DataFrame(out)


def _lot() -> Position:
    base = pd.Timestamp("2024-09-04 09:30", tz="America/New_York").tz_convert("UTC")
    return Position(
        symbol="AAA", entry_date=_dt.date(2024, 9, 4), entry_price=100.0, qty=10,
        stop_pct=0.08, target_pct=0.15, max_hold_days=3,
        entry_session=_dt.date(2024, 9, 4),
        entry_timestamp=base.isoformat(),
        stop_price=92.0, target_price=115.0,
    )


def test_gap_open_below_stop_fills_at_open() -> None:
    # Bar 1 opens at 88.0 — already through the 92.0 stop. A gap-through fills at
    # the OPEN (88.0), NOT the stop price (the realistic gap loss).
    path = _minute_path([
        {"o": 100.0, "h": 100.5, "l": 99.8, "c": 100.0},  # fill bar
        {"o": 88.0, "h": 89.0, "l": 86.0, "c": 87.0},     # gap below stop
    ])
    ev = walk_lot_exit(_lot(), path, exit_cfg={})
    assert ev is not None
    assert ev.exit_reason == "gap_stop"
    assert ev.exit_price == 88.0  # filled at the open, not the 92.0 stop
