"""Phase 7 — minute path triggers the stop before the target → stop exit."""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.exits import walk_lot_exit
from bowaka_v2_lab.sim.portfolio import Position


def _minute_path(rows: list[dict]) -> pd.DataFrame:
    """Build a tiny minute-bar frame anchored at 09:30 ET on 2024-09-04."""
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
    # entry_timestamp = the 09:30 fill bar; the walk starts on the NEXT bar.
    base = pd.Timestamp("2024-09-04 09:30", tz="America/New_York").tz_convert("UTC")
    return Position(
        symbol="AAA", entry_date=_dt.date(2024, 9, 4), entry_price=100.0, qty=10,
        stop_pct=0.08, target_pct=0.15, max_hold_days=3,
        entry_session=_dt.date(2024, 9, 4),
        entry_timestamp=base.isoformat(),
        stop_price=92.0, target_price=115.0,
    )


def test_minute_path_stop_before_target() -> None:
    # Bar 0 = fill bar (skipped). Bar 1 dips to 91.5 (<= stop 92.0); a later bar
    # would hit the target — but the stop fired first.
    path = _minute_path([
        {"o": 100.0, "h": 100.5, "l": 99.8, "c": 100.0},  # fill bar
        {"o": 100.0, "h": 100.2, "l": 91.5, "c": 95.0},   # stop hit
        {"o": 95.0, "h": 116.0, "l": 94.0, "c": 115.5},   # would hit target
    ])
    ev = walk_lot_exit(_lot(), path, exit_cfg={})
    assert ev is not None
    assert ev.exit_reason == "stop"
    assert ev.exit_price == 92.0
    assert ev.position_id is not None
    # The walk skipped the fill bar — the exit is on bar 1, not bar 0.
    assert ev.exit_timestamp is not None
