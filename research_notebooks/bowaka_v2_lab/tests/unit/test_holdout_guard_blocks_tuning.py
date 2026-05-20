"""Any read of final-holdout data outside the final-eval step raises."""
from __future__ import annotations

import datetime as _dt

import pytest

from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard, HoldoutGuardError


def test_tuning_read_into_holdout_raises() -> None:
    g = HoldoutGuard(_dt.date(2024, 11, 1), _dt.date(2024, 12, 31))
    # tuning phase + read inside the holdout window
    with pytest.raises(HoldoutGuardError):
        g.assert_can_read(_dt.date(2024, 11, 15), _dt.date(2024, 11, 20))


def test_tuning_read_before_holdout_passes() -> None:
    g = HoldoutGuard(_dt.date(2024, 11, 1), _dt.date(2024, 12, 31))
    g.assert_can_read(_dt.date(2024, 5, 1), _dt.date(2024, 10, 31))


def test_final_eval_phase_allows_holdout_read() -> None:
    g = HoldoutGuard(_dt.date(2024, 11, 1), _dt.date(2024, 12, 31))
    g.enter_final_eval()
    g.assert_can_read(_dt.date(2024, 11, 15), _dt.date(2024, 11, 20))
    g.exit_final_eval()
    with pytest.raises(HoldoutGuardError):
        g.assert_can_read(_dt.date(2024, 11, 15), _dt.date(2024, 11, 20))
