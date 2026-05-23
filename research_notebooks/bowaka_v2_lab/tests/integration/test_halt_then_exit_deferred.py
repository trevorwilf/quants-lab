"""Realism Remediation 2 Phase 7 (Task 3 robustness) — when the venue reports
the symbol as ``halted`` / ``pending_review`` / ``luld_pause`` at a minute, the
bracket cannot fill at that minute. The exit walker DEFERS to the first
non-halted minute (a stop in a halted minute does not fire; the same stop in
the next active minute does).

This integration test pins the halt-defer contract via a fixture status
supplier that returns ``halted`` for one minute then ``active``.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any, Optional

import pandas as pd

from bowaka_v2_lab.sim.exits import walk_lot_exit
from bowaka_v2_lab.sim.portfolio import Position


def _path(rows: list[dict], start_clock: str = "09:30") -> pd.DataFrame:
    base = pd.Timestamp(
        f"2024-09-04 {start_clock}", tz="America/New_York"
    ).tz_convert("UTC")
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


def _status_supplier_factory(halted_minutes: set[pd.Timestamp]):
    """Fixture status supplier: ``halted`` for any minute in ``halted_minutes``,
    ``active`` everywhere else."""
    halted_set = {pd.Timestamp(t).tz_convert("UTC") for t in halted_minutes}

    def supplier(symbol: str, ts: Any) -> Optional[dict]:
        ts_utc = pd.Timestamp(ts)
        if ts_utc.tzinfo is None:
            ts_utc = ts_utc.tz_localize("UTC")
        else:
            ts_utc = ts_utc.tz_convert("UTC")
        if ts_utc in halted_set:
            return {"status": "halted"}
        return {"status": "active"}

    return supplier


def test_halt_then_exit_deferred_to_first_non_halted_minute() -> None:
    """A minute that touches the stop while HALTED defers the exit. The next
    non-halted minute that touches the stop fires the exit."""
    # Build a 3-bar path: fill bar, halted minute that touches the stop (NO
    # exit fires), then an active minute that touches the stop (exit fires).
    path = _path([
        {"o": 100.0, "h": 100.5, "l": 99.8, "c": 100.0},  # fill bar
        # 09:31 — halted; touches the 92 stop; MUST defer.
        {"o": 95.0, "h": 95.5, "l": 91.0, "c": 91.5},
        # 09:32 — active; touches the stop again; THIS minute fires the exit.
        {"o": 92.5, "h": 92.7, "l": 91.5, "c": 92.0},
    ])
    base = pd.Timestamp("2024-09-04 09:30", tz="America/New_York").tz_convert("UTC")
    halted_minute = base + pd.Timedelta(minutes=1)  # 09:31
    status_supplier = _status_supplier_factory({halted_minute})

    ev = walk_lot_exit(
        _lot(), path, exit_cfg={},
        status_supplier=status_supplier,
    )
    assert ev is not None
    # The exit fires at 09:32 (the first non-halted minute that touches the stop).
    et_ts = pd.Timestamp(ev.exit_timestamp).tz_convert("America/New_York")
    assert (et_ts.hour, et_ts.minute) == (9, 32), (
        f"halt-then-exit must fire at the next non-halted minute (09:32), "
        f"got {et_ts.isoformat()}"
    )
    # It is a regular ``stop`` (not gap_stop — the open at 92.5 is above the 92 stop).
    assert ev.exit_reason == "stop"
    assert ev.exit_price == 92.0


def test_halt_only_minute_does_not_count_as_exit() -> None:
    """If the ONLY stop touch happens during a halted minute (and the lot
    survives past it without ever touching the stop again), the lot does NOT
    exit on a stop — it rides to max_hold."""
    # Build a path where the halted minute touches the stop and the next bars
    # never touch the stop again (price recovers and holds).
    path = _path([
        {"o": 100.0, "h": 100.5, "l": 99.8, "c": 100.0},  # fill bar
        # 09:31 — halted; touches the 92 stop; defers.
        {"o": 95.0, "h": 95.5, "l": 91.0, "c": 91.5},
        # 09:32+ — active; recovers ABOVE the stop, never touches it again.
        {"o": 95.0, "h": 96.0, "l": 94.0, "c": 95.5},
        {"o": 95.5, "h": 96.5, "l": 94.5, "c": 96.0},
        {"o": 96.0, "h": 97.0, "l": 95.5, "c": 96.5},
    ])
    base = pd.Timestamp("2024-09-04 09:30", tz="America/New_York").tz_convert("UTC")
    halted_minute = base + pd.Timedelta(minutes=1)
    status_supplier = _status_supplier_factory({halted_minute})

    ev = walk_lot_exit(
        _lot(), path, exit_cfg={},
        status_supplier=status_supplier,
    )
    # The walk runs out of bars (no further stop touch, no time/max-hold horizon)
    # → the fallback closes the lot on the last bar with ``max_hold``.
    # Critically the exit_reason is NOT ``stop`` / ``gap_stop``.
    if ev is not None:
        assert ev.exit_reason not in ("stop", "gap_stop"), (
            f"a halted-only stop touch must NOT fire a stop exit; got {ev.exit_reason!r}"
        )


def test_pending_review_status_also_defers_exit() -> None:
    """``pending_review`` and ``luld_pause`` defer the exit just like ``halted``."""
    path = _path([
        {"o": 100.0, "h": 100.5, "l": 99.8, "c": 100.0},  # fill bar
        # 09:31 — pending_review; touches stop; MUST defer.
        {"o": 95.0, "h": 95.5, "l": 91.0, "c": 91.5},
        # 09:32 — active; touches stop again; fires here.
        {"o": 92.5, "h": 92.7, "l": 91.5, "c": 92.0},
    ])
    base = pd.Timestamp("2024-09-04 09:30", tz="America/New_York").tz_convert("UTC")
    review_minute = base + pd.Timedelta(minutes=1)

    def status_supplier(symbol: str, ts: Any) -> Optional[dict]:
        ts_utc = pd.Timestamp(ts)
        if ts_utc.tzinfo is None:
            ts_utc = ts_utc.tz_localize("UTC")
        else:
            ts_utc = ts_utc.tz_convert("UTC")
        if ts_utc == review_minute:
            return {"status": "pending_review"}
        return {"status": "active"}

    ev = walk_lot_exit(
        _lot(), path, exit_cfg={},
        status_supplier=status_supplier,
    )
    assert ev is not None
    et_ts = pd.Timestamp(ev.exit_timestamp).tz_convert("America/New_York")
    assert (et_ts.hour, et_ts.minute) == (9, 32)
    assert ev.exit_reason == "stop"
