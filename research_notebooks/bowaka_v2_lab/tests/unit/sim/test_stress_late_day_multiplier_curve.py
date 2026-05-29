"""Phase 2 (audit 2026-05-29 §8.5) — late-day liquidity multiplier curve."""
from __future__ import annotations

from bowaka_v2_lab.sim.fills import late_day_multiplier


def test_curve_conservative() -> None:
    assert late_day_multiplier(45, "conservative") == 1.0
    assert late_day_multiplier(30, "conservative") == 1.0
    assert abs(late_day_multiplier(15, "conservative") - 1.25) < 1e-9
    assert abs(late_day_multiplier(0, "conservative") - 1.5) < 1e-9


def test_base_is_always_unity() -> None:
    assert late_day_multiplier(0, "base") == 1.0
    assert late_day_multiplier(15, "base") == 1.0


def test_severe_peaks_higher() -> None:
    assert abs(late_day_multiplier(0, "severe") - 2.5) < 1e-9
