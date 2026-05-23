"""Phase 7 — active signal-fade closes the lot when the re-scored signal is
below the hard threshold at eval_time."""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.exits import walk_lot_exit
from bowaka_v2_lab.sim.portfolio import Position

# Frozen-contract signal_fade block — the live initial_mode is
# "telemetry_then_active_after_validation". Realism remediation 2 Phase 7
# (audit P0-008) requires an explicit activation handshake before fade fires
# real exits; this fixture sets ``activation_state: active`` to model the
# post-validation state used by these tests.
_FADE_CFG_ACTIVE = {
    "time_stop": {"enabled": False},
    "signal_fade": {
        "enabled": True,
        "initial_mode": "telemetry_then_active_after_validation",
        "activation_state": "active",
        "eval_time": "15:45",
        "score_thresholds": {"soft": 0.34, "hard": 0.50, "critical": 0.67},
        "exit_on": ["hard", "critical"],
    },
}


def _lot() -> Position:
    base = pd.Timestamp("2024-09-04 09:30", tz="America/New_York").tz_convert("UTC")
    return Position(
        symbol="AAA", entry_date=_dt.date(2024, 9, 4), entry_price=100.0, qty=10,
        stop_pct=0.30, target_pct=0.30, max_hold_days=3,
        entry_session=_dt.date(2024, 9, 4),
        entry_timestamp=base.isoformat(),
        stop_price=70.0, target_price=130.0,
    )


def _quiet_path_to(end_clock: str) -> pd.DataFrame:
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


def test_active_fade_closes_lot_below_hard_threshold() -> None:
    # Re-scored signal 0.40 < 0.50 hard (but >= 0.34 soft) → a hard fade exit.
    ev = walk_lot_exit(
        _lot(), _quiet_path_to("15:50"),
        exit_cfg=_FADE_CFG_ACTIVE,
        signal_score_fn=lambda pos, ts: 0.40,
    )
    assert ev is not None
    assert ev.exit_reason == "signal_fade_hard"
    # Fired at 15:45 ET (the eval_time bar).
    et = pd.Timestamp(ev.exit_timestamp).tz_convert("America/New_York")
    assert (et.hour, et.minute) == (15, 45)


def test_active_fade_critical_reason_between_hard_and_critical() -> None:
    # Re-scored signal 0.60 clears the 0.50 hard line but is still below the
    # 0.67 critical line → a critical fade exit. (Per Task 5 the rule is
    # score < threshold; the band is the tightest exit_on threshold the score
    # is below — here only `critical`.)
    ev = walk_lot_exit(
        _lot(), _quiet_path_to("15:50"),
        exit_cfg=_FADE_CFG_ACTIVE,
        signal_score_fn=lambda pos, ts: 0.60,
    )
    assert ev is not None
    assert ev.exit_reason == "signal_fade_critical"


def test_active_fade_hard_reason_when_far_below_hard() -> None:
    # A very weak signal (0.10) is below the hard line → hard fade (the
    # tightest exit_on threshold it is below).
    ev = walk_lot_exit(
        _lot(), _quiet_path_to("15:50"),
        exit_cfg=_FADE_CFG_ACTIVE,
        signal_score_fn=lambda pos, ts: 0.10,
    )
    assert ev is not None
    assert ev.exit_reason == "signal_fade_hard"


def test_active_fade_no_exit_when_score_healthy() -> None:
    # A healthy score (0.80) does not trip any exit_on threshold → no fade exit
    # (the lot exits later via max_hold instead).
    ev = walk_lot_exit(
        _lot(), _quiet_path_to("15:50"),
        exit_cfg=_FADE_CFG_ACTIVE,
        signal_score_fn=lambda pos, ts: 0.80,
    )
    if ev is not None:
        assert not ev.exit_reason.startswith("signal_fade")
