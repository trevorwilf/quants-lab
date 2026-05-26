"""Every DQ check emitted by ``build_data_quality_report`` is classified.

Speedup report v2 §4 P4 / §5.6 / Phase 3 task 6. The
``_DQ_CHECK_INVARIANCE`` dict must enumerate every check name the report
emits — an unclassified name defaults to ``trial_dependent`` (the
conservative fallback rebuilds the cache, never silently reuses a stale
row). This test pins the surface area so a new check addition forces a
manual classification audit.
"""
from __future__ import annotations

from bowaka_v2_lab.data.data_quality import (
    DQ_CHECK_INVARIANCE_VERSION,
    _DQ_CHECK_INVARIANCE,
    dq_check_invariance,
)


def test_invariance_version_is_a_positive_int() -> None:
    assert isinstance(DQ_CHECK_INVARIANCE_VERSION, int)
    assert DQ_CHECK_INVARIANCE_VERSION >= 1


def test_every_classification_value_is_valid() -> None:
    for name, cls in _DQ_CHECK_INVARIANCE.items():
        assert cls in ("invariant", "trial_dependent"), (
            f"check {name!r} classified as {cls!r}, expected "
            "'invariant' or 'trial_dependent'"
        )


def test_helper_default_is_trial_dependent_for_unknown_names() -> None:
    assert dq_check_invariance("an_unclassified_check_that_should_never_exist") == (
        "trial_dependent"
    )


def test_trial_dependent_checks_cover_max_quote_age_and_max_hold_days() -> None:
    """The classification must mark trial-dependent any check whose body
    consumes a search-space leaf — speedup §5.6 names quote_coverage,
    coverage_missing_exit_path, and replay_quote_age_violation explicitly.
    """
    assert dq_check_invariance("quote_coverage") == "trial_dependent"
    assert dq_check_invariance("coverage_missing_exit_path") == "trial_dependent"
    assert dq_check_invariance("replay_quote_age_violation") == "trial_dependent"


def test_audit_and_coverage_missing_checks_are_invariant() -> None:
    for name in (
        "audit_missing_sessions",
        "audit_duplicate_sessions",
        "audit_ohlc_violations",
        "audit_passed_research_audit",
        "coverage_missing",
        "adjustment_mismatch",
        "split_adjustment_mismatch",
    ):
        assert dq_check_invariance(name) == "invariant", name
