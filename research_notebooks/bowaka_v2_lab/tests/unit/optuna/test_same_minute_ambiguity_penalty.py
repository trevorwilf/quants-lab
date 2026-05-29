"""Phase 2 (audit 2026-05-29 §8.5) — same-minute stop/target ambiguity penalty."""
from __future__ import annotations

from bowaka_v2_lab.optuna.objective import (
    SameMinuteAmbiguityMetrics,
    same_minute_ambiguity_penalty,
)


def test_caps_at_max() -> None:
    m = SameMinuteAmbiguityMetrics(n_ambiguous_bars=50, n_resolved_as_stop=50)
    assert same_minute_ambiguity_penalty(m) == 0.2  # min(0.2, 0.25)


def test_scales_below_cap() -> None:
    m = SameMinuteAmbiguityMetrics(n_ambiguous_bars=5, n_resolved_as_stop=5)
    assert abs(same_minute_ambiguity_penalty(m) - 0.025) < 1e-9


def test_zero_is_zero() -> None:
    m = SameMinuteAmbiguityMetrics(n_ambiguous_bars=0, n_resolved_as_stop=0)
    assert same_minute_ambiguity_penalty(m) == 0.0
