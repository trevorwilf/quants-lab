"""Phase 5 — stop-ship checklist gate.

Speedup report v2 §11 task 8. Each failure condition is tripped
individually and asserted; a clean report passes with no failures.
"""
from __future__ import annotations

from bowaka_v2_lab.optuna.stop_ship_checklist import evaluate_stop_ship


def _clean_report() -> dict:
    return {
        "feed": "sip",
        "finalists": [
            {"trial_number": 1, "holdout": {"objective": 1.0},
             "validation": {"objective": 1.1},
             "trade_diagnostics": {"total_trades": 80, "max_symbol_share": 0.10}},
        ],
        "incumbent": {"trial_number": 0, "holdout": {"objective": 1.0}},
        "finalist_evaluation": {
            "fold_local_stress_matrix": {"worst_case_objective": 0.2},
            "top_k_clustering": {"unstable_fraction": 0.1, "cv_threshold": 0.15},
            "trade_diagnostics": {"exported": {"total_trades": 80, "max_symbol_share": 0.10}},
            "data_quality": {"any_gate_failed": False, "partial_tape_caveat": False},
        },
    }


def test_clean_report_passes() -> None:
    decision = evaluate_stop_ship(_clean_report())
    assert decision.passed is True
    assert decision.failures == []


def test_holdout_regression_fails() -> None:
    r = _clean_report()
    # exported holdout 0.5 vs incumbent 1.0 -> 50% worse, > 10% limit.
    r["finalists"][0]["holdout"]["objective"] = 0.5
    decision = evaluate_stop_ship(r)
    assert decision.passed is False
    assert any("holdout regression" in f for f in decision.failures)


def test_stress_collapse_fails() -> None:
    r = _clean_report()
    r["finalist_evaluation"]["fold_local_stress_matrix"]["worst_case_objective"] = -0.01
    decision = evaluate_stop_ship(r)
    assert decision.passed is False
    assert any("stress collapse" in f for f in decision.failures)


def test_non_clustered_top_k_fails() -> None:
    r = _clean_report()
    r["finalist_evaluation"]["top_k_clustering"]["unstable_fraction"] = 0.75
    decision = evaluate_stop_ship(r)
    assert decision.passed is False
    assert any("not clustered" in f for f in decision.failures)


def test_too_few_trades_fails() -> None:
    r = _clean_report()
    r["finalist_evaluation"]["trade_diagnostics"]["exported"]["total_trades"] = 10
    decision = evaluate_stop_ship(r)
    assert decision.passed is False
    assert any("too few trades" in f for f in decision.failures)


def test_symbol_concentration_fails() -> None:
    r = _clean_report()
    r["finalist_evaluation"]["trade_diagnostics"]["exported"]["max_symbol_share"] = 0.30
    decision = evaluate_stop_ship(r)
    assert decision.passed is False
    assert any("symbol concentration" in f for f in decision.failures)


def test_dq_gate_failure_fails() -> None:
    r = _clean_report()
    r["finalist_evaluation"]["data_quality"]["any_gate_failed"] = True
    decision = evaluate_stop_ship(r)
    assert decision.passed is False
    assert any("data-quality gate failed" in f for f in decision.failures)


def test_iex_partial_tape_caveat_fails() -> None:
    r = _clean_report()
    r["feed"] = "iex"
    r["finalist_evaluation"]["data_quality"]["partial_tape_caveat"] = True
    decision = evaluate_stop_ship(r)
    assert decision.passed is False
    assert any("partial-tape" in f for f in decision.failures)


def test_warnings_when_sections_absent() -> None:
    """A skeletal report yields warnings (missing data) but no spurious failures
    beyond what is actually checkable."""
    decision = evaluate_stop_ship({"finalists": [], "incumbent": None,
                                   "finalist_evaluation": {}})
    # No data -> no hard failures, but warnings present.
    assert decision.passed is True
    assert decision.warnings
