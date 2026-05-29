"""Phase 0 (audit 2026-05-29 §A.5 / Appendix E) — degraded-folds gate.

``_run_validation_folds`` appends a ``_degraded_fold`` (fold_status="degraded")
when a fold's backtest raises a non-structural exception. A degraded fold is
the swallowed-exception sentinel, not a real datapoint; any trial containing
one makes the study invalid. This gate has NO opt-out.
"""
from __future__ import annotations

from bowaka_v2_lab.optuna.errors import REASON_DEGRADED_FOLDS_PRESENT
from bowaka_v2_lab.optuna.study_validity import (
    detect_degraded_folds_present,
    evaluate_study_validity,
)


def test_any_degraded_flagged() -> None:
    statuses = [["ok", "ok"], ["ok", "degraded"], ["ok", "ok"]]
    assert detect_degraded_folds_present(statuses) is True


def test_all_ok_not_flagged() -> None:
    assert detect_degraded_folds_present([["ok", "ok"]] * 3) is False
    assert detect_degraded_folds_present([]) is False


def test_evaluate_flags_degraded() -> None:
    r = evaluate_study_validity(
        trial_values=[float(i) for i in range(12)],
        fold_metrics_per_trial=[[{"n_trades": 5}] for _ in range(12)],
        fold_status_per_trial=[["ok"]] * 11 + [["degraded"]],
        study_user_attrs={},
        cfg_optuna={},
    )
    assert r.valid is False
    assert REASON_DEGRADED_FOLDS_PRESENT in r.invalid_reasons
    assert r.detail["degraded_trial_count"] == 1


def test_degraded_gate_has_no_opt_out() -> None:
    # even with every other opt-out set, a degraded fold still fails the study
    r = evaluate_study_validity(
        trial_values=[-1.5] * 12,
        fold_metrics_per_trial=[[{"n_trades": 0}] for _ in range(12)],
        fold_status_per_trial=[["degraded"] for _ in range(12)],
        study_user_attrs={"incumbent_padded_from_search_space": {"k": 1}},
        cfg_optuna={
            "allow_constant_objective_surface": True,
            "allow_no_trade_study": True,
            "allow_padded_incumbent": True,
        },
    )
    assert r.valid is False
    assert r.invalid_reasons == (REASON_DEGRADED_FOLDS_PRESENT,)
