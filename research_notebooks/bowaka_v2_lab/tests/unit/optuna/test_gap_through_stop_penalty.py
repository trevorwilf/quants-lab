"""Phase 2 (audit 2026-05-29 §8.5) — gap-through-stop objective penalty."""
from __future__ import annotations

from bowaka_v2_lab.optuna.objective import (
    GapThroughStopMetrics,
    gap_through_stop_penalty,
)


def _m(excess: float) -> GapThroughStopMetrics:
    return GapThroughStopMetrics(
        n_gap_through_events=3,
        gap_through_loss_dollars_total=excess,
        expected_gap_through_loss_dollars=0.0,
    )


def test_penalty_caps_at_max() -> None:
    assert gap_through_stop_penalty(_m(1500.0)) == 0.5  # min(0.5, 1.5)


def test_penalty_scales_below_cap() -> None:
    assert abs(gap_through_stop_penalty(_m(200.0)) - 0.2) < 1e-9


def test_zero_excess_is_zero() -> None:
    assert gap_through_stop_penalty(_m(0.0)) == 0.0


def test_expected_loss_subtracted() -> None:
    m = GapThroughStopMetrics(
        n_gap_through_events=2,
        gap_through_loss_dollars_total=500.0,
        expected_gap_through_loss_dollars=300.0,
    )
    # excess = 200 -> 0.2
    assert abs(gap_through_stop_penalty(m) - 0.2) < 1e-9
