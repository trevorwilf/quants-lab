"""Post-study validity gates (audit 2026-05-29 §6.5 / Appendix E).

A study can be operationally complete (Optuna finished trials, RDB has
rows) but scientifically invalid: every trial returns the same penalty,
no trial generated trades, every trial had degraded folds, or the
incumbent baseline was silently padded with search-space midpoints
instead of the actual lab config.

This module owns the detection. ``walkforward_runner._finalize_study``
calls ``evaluate_study_validity(...)`` after the optimization loop
completes and before any artifact is written. An invalid result writes
``status: "failed"`` instead of ``status: "ok"``, suppresses
``best_params``, and surfaces a list of ``invalid_reasons``.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence
from .errors import (
    REASON_CONSTANT_OBJECTIVE_SURFACE,
    REASON_DEGRADED_FOLDS_PRESENT,
    REASON_HOLDOUT_GUARD_NOT_ACTIVE,
    REASON_INCUMBENT_MAPPING_INCOMPLETE,
    REASON_LOW_FOLD_ACTIVITY,
    REASON_NO_TRADE_STUDY,
)


@dataclass(frozen=True)
class StudyValidityResult:
    valid: bool
    invalid_reasons: tuple[str, ...] = ()
    detail: Mapping[str, Any] = field(default_factory=dict)


def detect_constant_objective_surface(
    trial_values: Sequence[float],
    *,
    epsilon: float = 1e-6,
    min_trials: int = 10,
) -> bool:
    """True if every value in ``trial_values`` lies within ``epsilon`` of
    the first finite value, and there are at least ``min_trials`` finite
    values to judge from."""
    finite = [v for v in trial_values if v is not None and v == v
              and v not in (float("inf"), float("-inf"))]
    if len(finite) < min_trials:
        return False
    v0 = finite[0]
    return all(abs(v - v0) <= epsilon for v in finite)


def detect_no_trade_study(
    fold_metrics_per_trial: Sequence[Sequence[Mapping[str, Any]]],
    *,
    min_total_trades: int = 1,
) -> bool:
    """True if at least one fold was recorded and EVERY recorded fold of EVERY
    trial has zero trades.

    A trial that recorded no fold metrics at all (empty inner list) contributes
    no evidence — that is the §P0-001 "missing fold metrics" shape, not a
    no-trade study — so an all-empty input returns ``False`` (no evidence). A
    real no-trade study has populated fold rows whose every ``n_trades`` is 0.
    """
    if not fold_metrics_per_trial:
        return False
    saw_any_fold = False
    for fold_metrics in fold_metrics_per_trial:
        for fm in fold_metrics:
            saw_any_fold = True
            if int(fm.get("n_trades", 0) or 0) >= min_total_trades:
                return False
    return saw_any_fold


def detect_padded_incumbent(
    study_user_attrs: Mapping[str, Any],
) -> tuple[bool, dict[str, Any]]:
    padded = study_user_attrs.get("incumbent_padded_from_search_space") or {}
    return (bool(padded), {"padded_keys": sorted(padded.keys())})


def detect_degraded_folds_present(
    fold_status_per_trial: Sequence[Sequence[str]],
) -> bool:
    for fold_statuses in fold_status_per_trial:
        if any(s != "ok" for s in fold_statuses):
            return True
    return False


def detect_holdout_guard_not_active(study_user_attrs: Mapping[str, Any]) -> bool:
    """True iff the study EXPLICITLY recorded ``holdout_guard_active: False``.

    Absent (legacy / not recorded) is treated as no evidence — only an explicit
    False from a worker that ran without the tuning-phase holdout lock flags the
    study (audit 2026-05-29 §9 Phase 5 task 6).
    """
    if "holdout_guard_active" not in study_user_attrs:
        return False
    return not bool(study_user_attrs.get("holdout_guard_active"))


def detect_low_fold_activity(
    fold_metrics_per_trial: Sequence[Sequence[Mapping[str, Any]]],
    *,
    min_trades_per_fold: int = 5,
    min_active_days_per_fold: int = 3,
) -> bool:
    """True iff EVERY fold that recorded ``n_active_days`` is below the activity
    floor (and at least one such fold exists).

    Only folds carrying ``n_active_days`` are judged, so a legacy fold-metric
    payload (no such key) contributes no evidence — this keeps the gate from
    firing on inputs built before Phase 5.
    """
    judged = False
    for trial in fold_metrics_per_trial:
        for fm in trial:
            if "n_active_days" not in fm:
                continue
            judged = True
            if (int(fm.get("n_trades", 0) or 0) >= min_trades_per_fold
                    and int(fm.get("n_active_days", 0) or 0) >= min_active_days_per_fold):
                return False
    return judged


def evaluate_study_validity(
    *,
    trial_values: Sequence[float],
    fold_metrics_per_trial: Sequence[Sequence[Mapping[str, Any]]],
    fold_status_per_trial: Sequence[Sequence[str]],
    study_user_attrs: Mapping[str, Any],
    cfg_optuna: Mapping[str, Any],
) -> StudyValidityResult:
    """Run all gates. ``cfg_optuna`` supplies opt-outs for diagnostic runs:
    ``allow_constant_objective_surface``, ``allow_no_trade_study``,
    ``allow_padded_incumbent`` — defaults are all False."""
    reasons: list[str] = []
    detail: dict[str, Any] = {}

    padded, padded_detail = detect_padded_incumbent(study_user_attrs)
    if padded and not cfg_optuna.get("allow_padded_incumbent", False):
        reasons.append(REASON_INCUMBENT_MAPPING_INCOMPLETE)
        detail["padded_incumbent"] = padded_detail

    if detect_constant_objective_surface(trial_values) and \
       not cfg_optuna.get("allow_constant_objective_surface", False):
        reasons.append(REASON_CONSTANT_OBJECTIVE_SURFACE)
        detail["unique_values"] = sorted(set(trial_values))

    if detect_no_trade_study(fold_metrics_per_trial) and \
       not cfg_optuna.get("allow_no_trade_study", False):
        reasons.append(REASON_NO_TRADE_STUDY)
        detail["fold_trade_counts"] = [
            [int(fm.get("n_trades", 0) or 0) for fm in trial]
            for trial in fold_metrics_per_trial
        ][:5]

    if detect_degraded_folds_present(fold_status_per_trial):
        reasons.append(REASON_DEGRADED_FOLDS_PRESENT)
        detail["degraded_trial_count"] = sum(
            1 for fs in fold_status_per_trial
            if any(s != "ok" for s in fs)
        )

    # Audit 2026-05-29 §9 Phase 5 — the tuning-phase holdout guard must have
    # been active; an explicit False (any worker) flags the study.
    if detect_holdout_guard_not_active(study_user_attrs):
        reasons.append(REASON_HOLDOUT_GUARD_NOT_ACTIVE)
        detail["holdout_guard_active"] = study_user_attrs.get("holdout_guard_active")

    # Fold-activity floor is OPT-IN (default off) so existing studies / fixtures
    # with naturally-sparse folds are unaffected.
    if cfg_optuna.get("enforce_fold_activity_floor", False) and detect_low_fold_activity(
        fold_metrics_per_trial,
        min_trades_per_fold=int(cfg_optuna.get("min_trades_per_fold", 5)),
        min_active_days_per_fold=int(cfg_optuna.get("min_active_days_per_fold", 3)),
    ):
        reasons.append(REASON_LOW_FOLD_ACTIVITY)

    return StudyValidityResult(
        valid=not reasons,
        invalid_reasons=tuple(reasons),
        detail=detail,
    )


__all__ = [
    "StudyValidityResult",
    "detect_constant_objective_surface",
    "detect_no_trade_study",
    "detect_padded_incumbent",
    "detect_degraded_folds_present",
    "detect_holdout_guard_not_active",
    "detect_low_fold_activity",
    "evaluate_study_validity",
]
