"""Phase 7 — a minute whose OPEN is already above the target → gap target at open."""
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


def test_gap_open_above_target_fills_at_open() -> None:
    # Bar 1 opens at 120.0 — already above the 115.0 target. A gap-through fills
    # at the OPEN (120.0), capturing the realistic gap gain.
    path = _minute_path([
        {"o": 100.0, "h": 100.5, "l": 99.8, "c": 100.0},   # fill bar
        {"o": 120.0, "h": 122.0, "l": 119.0, "c": 121.0},  # gap above target
    ])
    ev = walk_lot_exit(_lot(), path, exit_cfg={})
    assert ev is not None
    assert ev.exit_reason == "gap_target"
    assert ev.exit_price == 120.0  # filled at the open, not the 115.0 target
