"""Audit 2026-05-29 §6.5 / Appendix D-E — Notebook 10 constant-objective regression.

The operator pasted the full Notebook 10 output of the broken run:
80 completed Optuna trials, every one scoring -1.5, with the incumbent
baseline padded from search-space midpoints. ``parse_fixture.py`` distils
it to ``summary.json``. This is the canonical failure shape the Phase 0
validity gates must reject. If this test ever passes a study with this
shape as valid, the fail-closed guarantee has regressed.
"""
from __future__ import annotations

import json
from pathlib import Path

from bowaka_v2_lab.optuna.errors import (
    REASON_CONSTANT_OBJECTIVE_SURFACE,
    REASON_INCUMBENT_MAPPING_INCOMPLETE,
    REASON_NO_TRADE_STUDY,
)
from bowaka_v2_lab.optuna.study_validity import evaluate_study_validity

_FIXTURE = (
    Path(__file__).resolve().parent.parent
    / "fixtures"
    / "notebook10_constant_objective_20260528"
    / "summary.json"
)


def _summary() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def test_fixture_summary_matches_canonical_values() -> None:
    s = _summary()
    # The audit pre-computed these from the same log. Lock them so a
    # re-parse drift is caught.
    assert s["parsed_trials"] >= 60
    assert s["unique_objective_values"] == [-1.5]
    assert s["incumbent_padded_keys"] == [
        "execution.max_quote_age_seconds",
        "execution.max_spread_bps",
    ]
    assert s["has_dynamic_categorical_error"] is False
    assert s["soft_gt_hard_count"] >= 10
    assert s["target_le_stop_count"] >= 10
    assert s["trial_0_max_quote_age_seconds"] == 60
    assert s["trial_0_max_spread_bps"] == 102


def test_regression_fixture_rejected_by_validity_gates() -> None:
    s = _summary()
    n = s["parsed_trials"]
    # Reconstruct the study-validity inputs from the canonical summary.
    trial_values = list(s["unique_objective_values"]) * n  # all -1.5
    # The broken run was a no-trade study: n_trades=0 across all folds.
    fold_metrics_per_trial = [
        [{"n_trades": 0}, {"n_trades": 0}, {"n_trades": 0}] for _ in range(n)
    ]
    fold_status_per_trial = [["ok", "ok", "ok"] for _ in range(n)]
    # The incumbent (Trial 0) was padded with search-space midpoints.
    study_user_attrs = {
        "incumbent_padded_from_search_space": {
            k: None for k in s["incumbent_padded_keys"]
        }
    }

    result = evaluate_study_validity(
        trial_values=trial_values,
        fold_metrics_per_trial=fold_metrics_per_trial,
        fold_status_per_trial=fold_status_per_trial,
        study_user_attrs=study_user_attrs,
        cfg_optuna={},
    )

    assert result.valid is False
    assert REASON_CONSTANT_OBJECTIVE_SURFACE in result.invalid_reasons
    assert REASON_INCUMBENT_MAPPING_INCOMPLETE in result.invalid_reasons
    assert REASON_NO_TRADE_STUDY in result.invalid_reasons
