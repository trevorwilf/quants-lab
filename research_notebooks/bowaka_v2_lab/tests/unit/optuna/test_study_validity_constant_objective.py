"""Phase 0 (audit 2026-05-29 §6.5 / Appendix E) — constant-objective gate.

The pasted Notebook 10 run completed 80 trials, every one scoring -1.5
(``low_trade_count_penalty(1.0) + fill_rate_penalty(0.5)``). TPE had no
signal, yet the study reported a "best trial". The constant-surface gate
must reject that shape and fail closed.
"""
from __future__ import annotations

from bowaka_v2_lab.optuna.errors import REASON_CONSTANT_OBJECTIVE_SURFACE
from bowaka_v2_lab.optuna.study_validity import (
    detect_constant_objective_surface,
    evaluate_study_validity,
)


def _folds(n_trials: int, n_folds: int = 3):
    return [[{"n_trades": 5} for _ in range(n_folds)] for _ in range(n_trials)]


def _ok(n_trials: int, n_folds: int = 3):
    return [["ok"] * n_folds for _ in range(n_trials)]


def test_all_equal_values_flagged() -> None:
    vals = [-1.5] * 12
    r = evaluate_study_validity(
        trial_values=vals,
        fold_metrics_per_trial=_folds(12),
        fold_status_per_trial=_ok(12),
        study_user_attrs={},
        cfg_optuna={},
    )
    assert r.valid is False
    assert REASON_CONSTANT_OBJECTIVE_SURFACE in r.invalid_reasons
    assert r.detail["unique_values"] == [-1.5]


def test_tiny_spread_within_epsilon_still_flagged() -> None:
    # spread ~1e-9, well within the default 1e-6 epsilon
    vals = [-1.5 + i * 1e-9 for i in range(12)]
    assert detect_constant_objective_surface(vals) is True


def test_mixed_values_not_flagged() -> None:
    # prompt's explicit small case
    assert detect_constant_objective_surface([-1.5, -1.5, -0.8]) is False
    # and a genuinely varied set of >= 10 values
    assert detect_constant_objective_surface([-1.5, -0.8] * 6) is False


def test_fewer_than_min_trials_not_flagged() -> None:
    # only 9 finite values — insufficient evidence to call it constant
    assert detect_constant_objective_surface([-1.5] * 9) is False


def test_opt_out_returns_valid() -> None:
    vals = [-1.5] * 12
    r = evaluate_study_validity(
        trial_values=vals,
        fold_metrics_per_trial=_folds(12),
        fold_status_per_trial=_ok(12),
        study_user_attrs={},
        cfg_optuna={"allow_constant_objective_surface": True},
    )
    assert REASON_CONSTANT_OBJECTIVE_SURFACE not in r.invalid_reasons
    assert r.valid is True
