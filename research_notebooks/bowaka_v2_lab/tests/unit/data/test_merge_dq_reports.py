"""``merge_dq_reports`` concatenates checks + rebuilds top-level summaries.

Speedup report v2 §4 P4 / §5.6 / Phase 3 task 3. The merge helper is the
backbone of the cached DQ flow: invariant half (cached) ⊕ trial-dependent
half (fresh) → full report indistinguishable from the un-cached path.
"""
from __future__ import annotations

from bowaka_v2_lab.data.data_quality import merge_dq_reports


def test_merge_concatenates_unique_checks() -> None:
    a = {
        "schema_version": 2, "regime": "lake", "feed": "iex",
        "checks": [
            {"name": "audit_missing_sessions", "status": "pass", "count": 0},
            {"name": "coverage_missing", "status": "fail", "count": 1},
        ],
        "passed": 1, "failed": 1, "warned": 0,
        "required_failures": ["coverage_missing"],
        "adjustment_gating_failures": [],
    }
    b = {
        "checks": [
            {"name": "quote_coverage", "status": "warn", "count": 5},
        ],
        "passed": 0, "failed": 0, "warned": 1,
        "required_failures": [],
        "adjustment_gating_failures": [],
    }
    merged = merge_dq_reports(a, b)
    names = [c["name"] for c in merged["checks"]]
    assert sorted(names) == [
        "audit_missing_sessions", "coverage_missing", "quote_coverage",
    ]
    assert merged["passed"] == 1
    assert merged["failed"] == 1
    assert merged["warned"] == 1
    assert merged["required_failures"] == ["coverage_missing"]
    assert merged["schema_version"] == 2
    assert merged["feed"] == "iex"


def test_merge_handles_empty_b() -> None:
    a = {
        "schema_version": 2, "regime": "lake", "feed": "iex",
        "checks": [
            {"name": "audit_missing_sessions", "status": "pass", "count": 0},
        ],
        "passed": 1, "failed": 0, "warned": 0,
        "required_failures": [], "adjustment_gating_failures": [],
    }
    merged = merge_dq_reports(a, {"checks": []})
    assert [c["name"] for c in merged["checks"]] == ["audit_missing_sessions"]


def test_merge_collision_picks_b_value() -> None:
    """Both halves carry the same check name — the trial-dependent half wins.

    Should not happen for a clean split (the classification dict partitions
    names cleanly) but is the conservative fallback to keep the merge
    well-defined.
    """
    a = {
        "checks": [{"name": "quote_coverage", "status": "pass", "count": 0}],
        "passed": 1, "failed": 0, "warned": 0,
        "required_failures": [], "adjustment_gating_failures": [],
    }
    b = {
        "checks": [{"name": "quote_coverage", "status": "fail", "count": 99}],
        "passed": 0, "failed": 1, "warned": 0,
        "required_failures": ["quote_coverage"],
        "adjustment_gating_failures": [],
    }
    merged = merge_dq_reports(a, b)
    assert merged["checks"][0]["status"] == "fail"
    assert merged["checks"][0]["count"] == 99
    assert merged["required_failures"] == ["quote_coverage"]


def test_merge_recomputes_required_failures_from_merged_checks() -> None:
    """``adjustment_mismatch`` in either half lands as an adjustment-gating fail."""
    a = {
        "checks": [
            {"name": "adjustment_mismatch", "status": "fail", "count": 1},
        ],
        "passed": 0, "failed": 1, "warned": 0,
        "required_failures": ["adjustment_mismatch"],
        "adjustment_gating_failures": ["adjustment_mismatch"],
    }
    b = {"checks": []}
    merged = merge_dq_reports(a, b)
    assert merged["adjustment_gating_failures"] == ["adjustment_mismatch"]
    assert merged["required_failures"] == ["adjustment_mismatch"]
