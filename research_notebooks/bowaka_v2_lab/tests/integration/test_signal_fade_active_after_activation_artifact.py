"""Realism Remediation 2 Phase 7 (audit P0-008) — dropping a validation
activation artifact at ``<dir>/signal_fade_activation_<feed>.json`` flips
``telemetry_then_active_after_validation`` from telemetry to active. The lot
then closes via a ``signal_fade_*`` exit instead of recording telemetry.

This is an INTEGRATION test (it touches the filesystem and runs the full minute
walk on top of the activation artifact handshake) — it pins the activation
contract end-to-end.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import pandas as pd

from bowaka_v2_lab.sim.exits import FadeTelemetry, walk_lot_exit
from bowaka_v2_lab.sim.portfolio import Position


_FADE_CFG_AFTER_VALIDATION = {
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


def _write_activation_artifact(target: Path, *, feed: str) -> None:
    """Drop a documented activation artifact for ``feed``."""
    target.mkdir(parents=True, exist_ok=True)
    body = {
        "feed": feed,
        "timestamp": "2026-05-22T15:00:00Z",
        "dataset_hash": "sha256:deadbeef0123456789abcdef0123456789abcdef0123",
        "code_hash": "sha256:cafef00d0123456789abcdef0123456789abcdef0123",
        "operator_signature": "operator:trevor.j.wilford@gmail.com",
        "promotion_run_id": "phase-7-activation-test",
    }
    (target / f"signal_fade_activation_{feed}.json").write_text(
        json.dumps(body, indent=2), encoding="utf-8"
    )


def test_activation_artifact_flips_after_validation_mode_to_active(
    tmp_path: Path,
) -> None:
    """Before the artifact lands, telemetry mode emits no fade exit.
    After the artifact lands, fade exits FIRE for the same config."""
    promo_dir = tmp_path / "promotion"
    promo_dir.mkdir(parents=True, exist_ok=True)

    # Run #1 — no artifact → telemetry; would-have-exited recorded, no fade exit.
    pre_telemetry: list[FadeTelemetry] = []
    ev_pre = walk_lot_exit(
        _lot(), _quiet_path_to("15:50"),
        exit_cfg=_FADE_CFG_AFTER_VALIDATION,
        signal_score_fn=lambda pos, ts: 0.10,
        fade_telemetry_out=pre_telemetry,
        feed="iex",
        activation_artifact_dir=promo_dir,
    )
    assert len(pre_telemetry) == 1, (
        "before the artifact lands, telemetry MUST be recorded "
        "(audit P0-008 contract)"
    )
    if ev_pre is not None:
        assert not ev_pre.exit_reason.startswith("signal_fade"), (
            "before the artifact lands, no signal_fade exit may fire"
        )

    # Drop the activation artifact.
    _write_activation_artifact(promo_dir, feed="iex")

    # Run #2 — artifact present → active; the same path now closes the lot
    # via a signal_fade_* exit at 15:45 ET.
    post_telemetry: list[FadeTelemetry] = []
    ev_post = walk_lot_exit(
        _lot(), _quiet_path_to("15:50"),
        exit_cfg=_FADE_CFG_AFTER_VALIDATION,
        signal_score_fn=lambda pos, ts: 0.10,
        fade_telemetry_out=post_telemetry,
        feed="iex",
        activation_artifact_dir=promo_dir,
    )
    assert ev_post is not None
    assert ev_post.exit_reason.startswith("signal_fade"), (
        f"after the artifact lands, the lot MUST close via signal_fade; "
        f"got exit_reason={ev_post.exit_reason!r}"
    )
    # Fired at 15:45 ET (the eval_time bar).
    et = pd.Timestamp(ev_post.exit_timestamp).tz_convert("America/New_York")
    assert (et.hour, et.minute) == (15, 45)


def test_activation_artifact_for_different_feed_does_not_activate_iex(
    tmp_path: Path,
) -> None:
    """The artifact is keyed by feed — dropping ``signal_fade_activation_sip.json``
    must NOT activate an IEX run."""
    promo_dir = tmp_path / "promotion"
    _write_activation_artifact(promo_dir, feed="sip")

    telemetry: list[FadeTelemetry] = []
    ev = walk_lot_exit(
        _lot(), _quiet_path_to("15:50"),
        exit_cfg=_FADE_CFG_AFTER_VALIDATION,
        signal_score_fn=lambda pos, ts: 0.10,
        fade_telemetry_out=telemetry,
        feed="iex",  # different feed
        activation_artifact_dir=promo_dir,
    )
    # IEX is still in telemetry — the SIP artifact does NOT activate IEX.
    assert len(telemetry) == 1
    if ev is not None:
        assert not ev.exit_reason.startswith("signal_fade")


def test_corrupt_activation_artifact_leaves_telemetry_mode_in_place(
    tmp_path: Path,
) -> None:
    """A malformed JSON artifact is NOT a valid activation handshake — the
    safety default is "stay in telemetry until the artifact is a parseable
    JSON object" (refuse to promote on bad inputs)."""
    promo_dir = tmp_path / "promotion"
    promo_dir.mkdir(parents=True, exist_ok=True)
    (promo_dir / "signal_fade_activation_iex.json").write_text(
        "not valid json {{{", encoding="utf-8"
    )

    telemetry: list[FadeTelemetry] = []
    ev = walk_lot_exit(
        _lot(), _quiet_path_to("15:50"),
        exit_cfg=_FADE_CFG_AFTER_VALIDATION,
        signal_score_fn=lambda pos, ts: 0.10,
        fade_telemetry_out=telemetry,
        feed="iex",
        activation_artifact_dir=promo_dir,
    )
    # A corrupt artifact is treated as no artifact — telemetry stays on.
    assert len(telemetry) == 1
    if ev is not None:
        assert not ev.exit_reason.startswith("signal_fade")
