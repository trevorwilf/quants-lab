"""Realism Remediation 2 Phase 7 (Task 3 robustness) — when a single minute
touches BOTH the stop and the target, the tie-breaking policy decides which
fires. Default (``exits.same_minute_tie: stop_first``) → STOP WINS;
``target_first`` → target wins.

This integration test pins the per-exit-config tie-breaker contract.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.exits import walk_lot_exit
from bowaka_v2_lab.sim.portfolio import Position


def _path(rows: list[dict]) -> pd.DataFrame:
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


def _same_minute_path() -> pd.DataFrame:
    return _path([
        {"o": 100.0, "h": 100.5, "l": 99.8, "c": 100.0},  # fill bar
        # Same minute touches BOTH the 92.0 stop AND the 115.0 target.
        {"o": 100.0, "h": 116.0, "l": 91.0, "c": 100.0},
    ])


def test_same_minute_tie_default_stop_first_wins() -> None:
    """Default (no explicit tie config) → stop wins (conservative policy)."""
    ev = walk_lot_exit(_lot(), _same_minute_path(), exit_cfg={})
    assert ev is not None
    assert ev.exit_reason == "stop", (
        f"default same_minute tie MUST be stop_first → stop wins, got {ev.exit_reason!r}"
    )
    assert ev.exit_price == 92.0
    assert ev.ambiguous_bar_resolved is True


def test_same_minute_tie_explicit_stop_first_wins() -> None:
    """Explicit ``exits.same_minute_tie: stop_first`` → stop wins."""
    ev = walk_lot_exit(
        _lot(), _same_minute_path(),
        exit_cfg={"same_minute_tie": "stop_first"},
    )
    assert ev is not None
    assert ev.exit_reason == "stop"
    assert ev.exit_price == 92.0
    assert ev.ambiguous_bar_resolved is True


def test_same_minute_tie_target_first_makes_target_win() -> None:
    """Alternative ``exits.same_minute_tie: target_first`` → target wins."""
    ev = walk_lot_exit(
        _lot(), _same_minute_path(),
        exit_cfg={"same_minute_tie": "target_first"},
    )
    assert ev is not None
    assert ev.exit_reason == "target", (
        f"same_minute_tie: target_first MUST make target win, got {ev.exit_reason!r}"
    )
    assert ev.exit_price == 115.0
    assert ev.ambiguous_bar_resolved is True


def test_exits_tie_overrides_simulation_resolution() -> None:
    """When both ``exits.same_minute_tie`` AND ``simulation.same_minute_resolution``
    are provided, the exit-config-level setting wins (it is the more specific
    lever)."""
    # simulation says "optimistic" (= target_first), but the exits tie says
    # "stop_first" → stop wins.
    ev = walk_lot_exit(
        _lot(), _same_minute_path(),
        exit_cfg={"same_minute_tie": "stop_first"},
        same_minute_resolution="optimistic",
    )
    assert ev is not None
    assert ev.exit_reason == "stop"
