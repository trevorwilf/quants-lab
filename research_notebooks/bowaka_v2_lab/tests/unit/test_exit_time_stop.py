"""Phase 7 — a lot still open at the 15:45 ET time-stop exits at the next bid."""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.exits import walk_lot_exit
from bowaka_v2_lab.sim.portfolio import Position

#: The frozen-contract exits.time_stop block.
_TIME_STOP_CFG = {"time_stop": {"enabled": True, "exit_time": "15:45"}}


def _lot() -> Position:
    base = pd.Timestamp("2024-09-04 09:30", tz="America/New_York").tz_convert("UTC")
    return Position(
        symbol="AAA", entry_date=_dt.date(2024, 9, 4), entry_price=100.0, qty=10,
        stop_pct=0.08, target_pct=0.15, max_hold_days=3,
        entry_session=_dt.date(2024, 9, 4),
        entry_timestamp=base.isoformat(),
        stop_price=92.0, target_price=115.0,
    )


def _quiet_path_to(end_clock: str) -> pd.DataFrame:
    """A minute path from 09:31 ET to ``end_clock`` ET that never trips a
    bracket (flat at 100) so only the time-stop can fire."""
    start = pd.Timestamp("2024-09-04 09:31", tz="America/New_York")
    end = pd.Timestamp(f"2024-09-04 {end_clock}", tz="America/New_York")
    rows = []
    ts = start
    while ts <= end:
        rows.append({
            "symbol": "AAA",
            "timestamp": ts.tz_convert("UTC"),
            "open": 100.0, "high": 100.3, "low": 99.7, "close": 100.0,
            "volume": 1000.0,
        })
        ts = ts + pd.Timedelta(minutes=1)
    return pd.DataFrame(rows)


def test_time_stop_fires_at_1545_minute_close() -> None:
    # No quote_supplier → the time-stop exits at the minute close (smoke path).
    path = _quiet_path_to("15:50")
    ev = walk_lot_exit(_lot(), path, exit_cfg=_TIME_STOP_CFG)
    assert ev is not None
    assert ev.exit_reason == "time_stop"
    assert ev.exit_price == 100.0
    # The exit minute is 15:45 ET (the first bar at/after the time-stop clock).
    et = pd.Timestamp(ev.exit_timestamp).tz_convert("America/New_York")
    assert (et.hour, et.minute) == (15, 45)


def test_time_stop_exits_at_bid_when_quote_aware() -> None:
    # A quote_supplier returning a bid → the time-stop exits at the bid.
    path = _quiet_path_to("15:50")

    def quote_supplier(symbol, ts, max_age_seconds=None):
        return {"bid": 99.5, "ask": 100.5}

    ev = walk_lot_exit(_lot(), path, exit_cfg=_TIME_STOP_CFG, quote_supplier=quote_supplier)
    assert ev is not None
    assert ev.exit_reason == "time_stop"
    assert ev.exit_price == 99.5  # the bid, not the 100.0 minute close
