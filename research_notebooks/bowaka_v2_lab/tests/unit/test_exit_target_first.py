"""Phase 7 — minute path triggers the target before the stop → target exit."""
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


def test_minute_path_target_before_stop() -> None:
    # Bar 1 climbs to 115.5 (>= target 115.0); a later bar would hit the stop.
    path = _minute_path([
        {"o": 100.0, "h": 100.5, "l": 99.8, "c": 100.0},  # fill bar
        {"o": 100.0, "h": 115.5, "l": 99.5, "c": 114.0},  # target hit
        {"o": 114.0, "h": 114.5, "l": 91.0, "c": 92.0},   # would hit stop
    ])
    ev = walk_lot_exit(_lot(), path, exit_cfg={})
    assert ev is not None
    assert ev.exit_reason == "target"
    assert ev.exit_price == 115.0
    assert ev.mfe_pct > 0.0  # the path reached above entry
