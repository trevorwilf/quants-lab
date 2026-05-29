"""Phase 2 (audit 2026-05-29 §6.8) — SEARCH_SPACE_VERSION bumped to 3."""
from __future__ import annotations

from bowaka_v2_lab.optuna.search_space import SEARCH_SPACE_SPEC, SEARCH_SPACE_VERSION


def test_version_is_3() -> None:
    assert SEARCH_SPACE_VERSION == 3


def test_v3_uses_gap_ratio_keys_not_absolute() -> None:
    assert "exits.reward_risk_ratio" in SEARCH_SPACE_SPEC
    assert "exits.signal_fade.score_thresholds.hard_gap" in SEARCH_SPACE_SPEC
    assert "exits.signal_fade.score_thresholds.critical_gap" in SEARCH_SPACE_SPEC
    # the absolute keys are derived, not sampled
    assert "exits.target_pct" not in SEARCH_SPACE_SPEC
    assert "exits.signal_fade.score_thresholds.hard" not in SEARCH_SPACE_SPEC
    assert "exits.signal_fade.score_thresholds.critical" not in SEARCH_SPACE_SPEC
