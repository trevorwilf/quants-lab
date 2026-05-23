"""Realism Remediation 2 Phase 7 (audit P0-008) — the live frozen-contract
``signal_fade.initial_mode: telemetry_then_active_after_validation`` MUST
resolve to ``fade_active == False`` until an activation handshake (explicit
``activation_state: active`` OR a validation activation artifact) is present.

Pre-Phase-7 code treated ``telemetry_then_active_after_validation`` as active
immediately — that is wrong (the phrase ITSELF says ``after_validation``).
This test pins the new correct behavior end-to-end:

* with the actual-contract config, ``resolve_signal_fade_active`` returns
  ``(False, "telemetry_then_active_after_validation", "telemetry")``,
* ``walk_lot_exit`` emits telemetry would-have-exited events but does NOT close
  the lot via a ``signal_fade_*`` exit reason,
* a healthy score path emits no telemetry and no fade exit.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pandas as pd

from bowaka_v2_lab.sim.exits import (
    FadeTelemetry,
    resolve_signal_fade_active,
    walk_lot_exit,
)
from bowaka_v2_lab.sim.portfolio import Position


# Frozen-contract signal_fade block — copy of the actual_bowaka_v2_contract
# initial_mode. No ``activation_state`` field, no artifact dropped → must
# resolve to telemetry per Phase 7.
_FADE_CFG_DEFAULT = {
    "time_stop": {"enabled": False},
    "signal_fade": {
        "enabled": True,
        "initial_mode": "telemetry_then_active_after_validation",
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


def test_resolve_signal_fade_active_defaults_to_telemetry_for_after_validation_mode() -> None:
    """The pure resolver must NEVER report fade_active=True for the
    after-validation mode unless an activation handshake exists."""
    active, mode, state = resolve_signal_fade_active(
        _FADE_CFG_DEFAULT["signal_fade"],
        feed="iex",
        artifact_dir=Path("/this/path/does/not/exist/and/must/not"),
    )
    assert active is False, (
        "telemetry_then_active_after_validation MUST resolve to fade_active=False "
        "until an activation artifact lands (audit P0-008)"
    )
    assert mode == "telemetry_then_active_after_validation"
    assert state == "telemetry"


def test_resolve_active_when_explicit_activation_state() -> None:
    """Explicit ``activation_state: active`` flips the mode without an artifact."""
    fade_cfg = dict(_FADE_CFG_DEFAULT["signal_fade"])
    fade_cfg["activation_state"] = "active"
    active, mode, state = resolve_signal_fade_active(
        fade_cfg,
        feed="iex",
        artifact_dir=Path("/this/path/does/not/exist/and/must/not"),
    )
    assert active is True
    assert mode == "telemetry_then_active_after_validation"
    assert state == "active"


def test_resolve_active_for_pure_active_mode() -> None:
    """``initial_mode: active`` is always active — no handshake needed."""
    active, mode, _ = resolve_signal_fade_active({
        "enabled": True,
        "initial_mode": "active",
    })
    assert active is True
    assert mode == "active"


def test_resolve_telemetry_for_telemetry_only_mode() -> None:
    """``initial_mode: telemetry_only`` is always telemetry."""
    active, mode, _ = resolve_signal_fade_active({
        "enabled": True,
        "initial_mode": "telemetry_only",
    })
    assert active is False
    assert mode == "telemetry_only"


def test_default_after_validation_mode_records_telemetry_but_no_fade_exit(
    tmp_path: Path,
) -> None:
    """End-to-end: walk_lot_exit must record a fade telemetry event but MUST
    NOT close the lot via signal_fade_* under the contract default."""
    fade_cfg = dict(_FADE_CFG_DEFAULT)
    # Point at an empty artifact dir so no activation artifact exists.
    fade_cfg["signal_fade"] = dict(fade_cfg["signal_fade"])

    telemetry: list[FadeTelemetry] = []
    ev = walk_lot_exit(
        _lot(), _quiet_path_to("15:50"),
        exit_cfg=fade_cfg,
        signal_score_fn=lambda pos, ts: 0.10,  # well below hard
        fade_telemetry_out=telemetry,
        feed="iex",
        activation_artifact_dir=tmp_path / "promotion_empty",
    )
    # Telemetry event WAS recorded (would-have-exited).
    assert len(telemetry) == 1, (
        "telemetry_then_active_after_validation default MUST emit telemetry"
    )
    assert telemetry[0].would_exit_reason in ("signal_fade_hard", "signal_fade_critical")
    # But the lot was NOT closed via a signal_fade_* reason.
    if ev is not None:
        assert not ev.exit_reason.startswith("signal_fade"), (
            f"telemetry mode MUST NOT close the lot via signal_fade; "
            f"got exit_reason={ev.exit_reason!r}"
        )


def test_default_after_validation_mode_no_telemetry_when_score_healthy(
    tmp_path: Path,
) -> None:
    """A healthy score (above critical) records nothing AND fires no exit."""
    telemetry: list[FadeTelemetry] = []
    ev = walk_lot_exit(
        _lot(), _quiet_path_to("15:50"),
        exit_cfg=_FADE_CFG_DEFAULT,
        signal_score_fn=lambda pos, ts: 0.90,
        fade_telemetry_out=telemetry,
        feed="iex",
        activation_artifact_dir=tmp_path / "promotion_empty",
    )
    assert telemetry == []
    # The exit (if any) is max_hold / time_stop, NEVER signal_fade.
    if ev is not None:
        assert not ev.exit_reason.startswith("signal_fade")
