"""Phase 7 — telemetry_only signal-fade records the would-have-exited event but
does NOT close the lot."""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.exits import FadeTelemetry, walk_lot_exit
from bowaka_v2_lab.sim.portfolio import Position

# Frozen-contract signal_fade block in telemetry_only mode.
_FADE_CFG_TELEMETRY = {
    "time_stop": {"enabled": False},
    "signal_fade": {
        "enabled": True,
        "initial_mode": "telemetry_only",
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


def test_telemetry_only_records_but_does_not_close() -> None:
    # The re-scored signal at 15:45 is 0.10 — below the 0.50 hard threshold.
    # In telemetry_only mode the would-have-exited event is recorded; the lot is
    # NOT closed, so walk_lot_exit returns the (later) max-hold exit instead.
    telemetry: list[FadeTelemetry] = []
    ev = walk_lot_exit(
        _lot(), _quiet_path_to("15:50"),
        exit_cfg=_FADE_CFG_TELEMETRY,
        signal_score_fn=lambda pos, ts: 0.10,
        fade_telemetry_out=telemetry,
    )
    # A would-have-exited fade event WAS recorded.
    assert len(telemetry) == 1
    t = telemetry[0]
    assert t.would_exit_reason in ("signal_fade_hard", "signal_fade_critical")
    assert t.score == 0.10
    # ...but the lot was NOT closed by the fade — the exit (if any) is max_hold,
    # never a signal_fade reason.
    if ev is not None:
        assert not ev.exit_reason.startswith("signal_fade")


def test_telemetry_only_no_event_when_score_healthy() -> None:
    # A healthy score (0.90 >= every threshold) records nothing.
    telemetry: list[FadeTelemetry] = []
    walk_lot_exit(
        _lot(), _quiet_path_to("15:50"),
        exit_cfg=_FADE_CFG_TELEMETRY,
        signal_score_fn=lambda pos, ts: 0.90,
        fade_telemetry_out=telemetry,
    )
    assert telemetry == []
