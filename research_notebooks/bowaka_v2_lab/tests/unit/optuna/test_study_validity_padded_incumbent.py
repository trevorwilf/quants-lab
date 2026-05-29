"""Phase 0 (audit 2026-05-29 §6.5 / Appendix E) — padded-incumbent gate.

When the incumbent (Trial 0) baseline is silently padded with search-space
midpoints (because the search-space keys were absent from the contract
lookup), the incumbent comparison is meaningless. The study records
``incumbent_padded_from_search_space``; the gate must reject on it.
"""
from __future__ import annotations

from bowaka_v2_lab.optuna.errors import REASON_INCUMBENT_MAPPING_INCOMPLETE
from bowaka_v2_lab.optuna.study_validity import (
    detect_padded_incumbent,
    evaluate_study_validity,
)


def test_padded_flagged_with_detail() -> None:
    attrs = {
        "incumbent_padded_from_search_space": {
            "execution.max_quote_age_seconds": 60,
        }
    }
    flagged, detail = detect_padded_incumbent(attrs)
    assert flagged is True
    assert detail["padded_keys"] == ["execution.max_quote_age_seconds"]

    r = evaluate_study_validity(
        trial_values=[float(i) for i in range(12)],
        fold_metrics_per_trial=[[{"n_trades": 5}] for _ in range(12)],
        fold_status_per_trial=[["ok"] for _ in range(12)],
        study_user_attrs=attrs,
        cfg_optuna={},
    )
    assert r.valid is False
    assert REASON_INCUMBENT_MAPPING_INCOMPLETE in r.invalid_reasons
    assert r.detail["padded_incumbent"]["padded_keys"] == [
        "execution.max_quote_age_seconds"
    ]


def test_empty_padded_not_flagged() -> None:
    flagged, _ = detect_padded_incumbent(
        {"incumbent_padded_from_search_space": {}}
    )
    assert flagged is False
    flagged2, _ = detect_padded_incumbent({})
    assert flagged2 is False


def test_opt_out_not_flagged() -> None:
    attrs = {"incumbent_padded_from_search_space": {"k": 1}}
    r = evaluate_study_validity(
        trial_values=[float(i) for i in range(12)],
        fold_metrics_per_trial=[[{"n_trades": 5}] for _ in range(12)],
        fold_status_per_trial=[["ok"] for _ in range(12)],
        study_user_attrs=attrs,
        cfg_optuna={"allow_padded_incumbent": True},
    )
    assert REASON_INCUMBENT_MAPPING_INCOMPLETE not in r.invalid_reasons
    assert r.valid is True
