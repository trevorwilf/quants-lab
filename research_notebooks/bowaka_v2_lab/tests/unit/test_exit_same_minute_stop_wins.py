"""Phase 7 — a minute touching BOTH brackets resolves to the stop under the
conservative ``same_minute_resolution`` axis (the realism default)."""
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


def test_same_minute_conservative_stop_wins() -> None:
    # Bar 1: low 91.0 (<= stop 92) AND high 116.0 (>= target 115). Open 100 is
    # inside the brackets so it is not a gap-through — genuine same-minute.
    path = _minute_path([
        {"o": 100.0, "h": 100.5, "l": 99.8, "c": 100.0},  # fill bar
        {"o": 100.0, "h": 116.0, "l": 91.0, "c": 100.0},  # both brackets touched
    ])
    ev = walk_lot_exit(_lot(), path, exit_cfg={}, same_minute_resolution="conservative")
    assert ev is not None
    assert ev.exit_reason == "stop"
    assert ev.exit_price == 92.0
    assert ev.ambiguous_bar_resolved is True


def test_same_minute_optimistic_target_wins() -> None:
    path = _minute_path([
        {"o": 100.0, "h": 100.5, "l": 99.8, "c": 100.0},
        {"o": 100.0, "h": 116.0, "l": 91.0, "c": 100.0},
    ])
    ev = walk_lot_exit(_lot(), path, exit_cfg={}, same_minute_resolution="optimistic")
    assert ev is not None
    assert ev.exit_reason == "target"
    assert ev.exit_price == 115.0
    assert ev.ambiguous_bar_resolved is True
