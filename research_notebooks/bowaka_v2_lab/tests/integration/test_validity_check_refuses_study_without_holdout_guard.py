"""Phase 3 (audit 2026-05-29 §9 Phase 5) — validity gate refuses a study that
reports the holdout guard was not active.
"""
from __future__ import annotations

from bowaka_v2_lab.optuna.errors import REASON_HOLDOUT_GUARD_NOT_ACTIVE
from bowaka_v2_lab.optuna.study_validity import evaluate_study_validity


def _varied_values():
    return [0.05, 0.06, 0.07, 0.08] * 3  # 12 distinct-ish values (no constant surface)


def test_explicit_false_flags_study() -> None:
    r = evaluate_study_validity(
        trial_values=_varied_values(),
        fold_metrics_per_trial=[[{"n_trades": 5}] for _ in range(12)],
        fold_status_per_trial=[["ok"] for _ in range(12)],
        study_user_attrs={"holdout_guard_active": False},
        cfg_optuna={},
    )
    assert not r.valid
    assert REASON_HOLDOUT_GUARD_NOT_ACTIVE in r.invalid_reasons


def test_active_guard_does_not_flag() -> None:
    r = evaluate_study_validity(
        trial_values=_varied_values(),
        fold_metrics_per_trial=[[{"n_trades": 5}] for _ in range(12)],
        fold_status_per_trial=[["ok"] for _ in range(12)],
        study_user_attrs={"holdout_guard_active": True},
        cfg_optuna={},
    )
    assert REASON_HOLDOUT_GUARD_NOT_ACTIVE not in r.invalid_reasons


def test_absent_key_is_no_evidence() -> None:
    # Legacy studies that never recorded the flag are NOT penalised.
    r = evaluate_study_validity(
        trial_values=_varied_values(),
        fold_metrics_per_trial=[[{"n_trades": 5}] for _ in range(12)],
        fold_status_per_trial=[["ok"] for _ in range(12)],
        study_user_attrs={},
        cfg_optuna={},
    )
    assert REASON_HOLDOUT_GUARD_NOT_ACTIVE not in r.invalid_reasons
