"""Phase 10 — decision-reason comparator surfaces mismatched reasons."""
from __future__ import annotations

from bowaka_v2_lab.reconcile.comparators import compare_decision_reason
from bowaka_v2_lab.reconcile.schemas import LabDecision, PaperDecision


def _paper(decision: str, reason: str) -> PaperDecision:
    return PaperDecision(symbol="AAA", decision=decision, reason=reason)


def _lab(decision: str, reason: str) -> LabDecision:
    return LabDecision(symbol="AAA", decision=decision, reason=reason)


def test_matching_decision_and_reason() -> None:
    cmp = compare_decision_reason(
        "c:AAA", _paper("accepted", "all_gates_passed"), _lab("accepted", "all_gates_passed")
    )
    assert cmp.match is True


def test_mismatched_reason_surfaced() -> None:
    """Same decision, different reason -> mismatch, both reasons retained."""
    cmp = compare_decision_reason(
        "c:AAA", _paper("rejected", "spread_too_wide"), _lab("rejected", "daily_entry_cap")
    )
    assert cmp.match is False
    assert cmp.paper_reason == "spread_too_wide"
    assert cmp.lab_reason == "daily_entry_cap"


def test_mismatched_decision_surfaced() -> None:
    """Paper accepted, lab rejected -> mismatch."""
    cmp = compare_decision_reason(
        "c:AAA", _paper("accepted", "all_gates_passed"), _lab("rejected", "spread_too_wide")
    )
    assert cmp.match is False
    assert cmp.paper_decision == "accepted"
    assert cmp.lab_decision == "rejected"


def test_missing_lab_decision_not_comparable() -> None:
    cmp = compare_decision_reason("c:AAA", _paper("accepted", "all_gates_passed"), None)
    assert cmp.match is None
    assert cmp.paper_decision == "accepted"
    assert cmp.lab_decision is None


def test_missing_paper_decision_not_comparable() -> None:
    cmp = compare_decision_reason("c:AAA", None, _lab("accepted", "all_gates_passed"))
    assert cmp.match is None
    assert cmp.lab_decision == "accepted"
    assert cmp.paper_decision is None


def test_both_missing_not_comparable() -> None:
    cmp = compare_decision_reason("c:AAA", None, None)
    assert cmp.match is None
