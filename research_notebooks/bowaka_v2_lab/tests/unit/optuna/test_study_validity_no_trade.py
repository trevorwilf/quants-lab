"""Phase 0 (audit 2026-05-29 §6.5 / Appendix E) — no-trade-study gate.

A study where every trial generated zero trades in every fold has no
optimization signal. The gate must reject it (unless opted out for a
diagnostic run).
"""
from __future__ import annotations

from bowaka_v2_lab.optuna.errors import REASON_NO_TRADE_STUDY
from bowaka_v2_lab.optuna.study_validity import (
    detect_no_trade_study,
    evaluate_study_validity,
)


def test_all_zero_trades_flagged() -> None:
    fm = [[{"n_trades": 0}, {"n_trades": 0}] for _ in range(5)]
    assert detect_no_trade_study(fm) is True


def test_one_fold_with_trades_not_flagged() -> None:
    fm = [[{"n_trades": 0}, {"n_trades": 0}] for _ in range(5)]
    fm[2][0] = {"n_trades": 3}
    assert detect_no_trade_study(fm) is False


def test_empty_fold_list_not_flagged() -> None:
    # no trials at all -> no evidence
    assert detect_no_trade_study([]) is False


def test_trials_with_no_recorded_folds_not_flagged() -> None:
    # trials present but each recorded zero fold rows (the §P0-001
    # "missing fold metrics" shape, e.g. the objective caught an exception
    # before writing fold_metrics) -> no evidence, not a no-trade study.
    assert detect_no_trade_study([[], []]) is False


def test_evaluate_flags_no_trade() -> None:
    r = evaluate_study_validity(
        # varied values so the constant-surface gate does not also fire
        trial_values=[float(i) for i in range(12)],
        fold_metrics_per_trial=[[{"n_trades": 0}] for _ in range(12)],
        fold_status_per_trial=[["ok"] for _ in range(12)],
        study_user_attrs={},
        cfg_optuna={},
    )
    assert r.valid is False
    assert REASON_NO_TRADE_STUDY in r.invalid_reasons


def test_opt_out_not_flagged() -> None:
    r = evaluate_study_validity(
        trial_values=[float(i) for i in range(12)],
        fold_metrics_per_trial=[[{"n_trades": 0}] for _ in range(12)],
        fold_status_per_trial=[["ok"] for _ in range(12)],
        study_user_attrs={},
        cfg_optuna={"allow_no_trade_study": True},
    )
    assert REASON_NO_TRADE_STUDY not in r.invalid_reasons
    assert r.valid is True
