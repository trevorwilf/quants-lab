"""Preflight fails CLOSED on adjustment-gating DQ failures in ``current_code_parity``.

Speedup report §4 P0-A / §5.1 / Phase 0 task 3. The pre-remediation
``_check_data_quality`` surfaced any ``current_code_parity`` DQ failure as a
``warn`` — including ``adjustment_mismatch`` / ``split_adjustment_mismatch``,
which silently allow a study to run against a raw lake when the live contract
requires adjusted daily bars. The unified path now consults
``evaluate_startup_dq``: parity mode is gated only on the adjustment-enforcement
checks (matching the backtester's own gate), but those failures DO refuse the
study.
"""
from __future__ import annotations

from bowaka_v2_lab.optuna.preflight import _check_data_quality


def _adj_failing_report() -> dict:
    """A lake-regime DQ report with adjustment_mismatch + split_adjustment_mismatch."""
    return {
        "schema_version": 2,
        "regime": "lake",
        "feed": "iex",
        "passed": 1,
        "failed": 2,
        "warned": 0,
        "checks": [
            {
                "name": "adjustment_mismatch",
                "status": "fail",
                "count": 1,
                "evidence": {"detail": "lake declares adjustment=raw"},
            },
            {
                "name": "split_adjustment_mismatch",
                "status": "fail",
                "count": 1,
                "evidence": {"detail": "lake has not applied split adjustments"},
            },
            {"name": "coverage_missing", "status": "pass", "count": 0},
        ],
        "required_failures": ["adjustment_mismatch", "split_adjustment_mismatch"],
        "adjustment_gating_failures": [
            "adjustment_mismatch", "split_adjustment_mismatch",
        ],
    }


def _non_adjustment_failing_report() -> dict:
    """A lake-regime DQ report with a non-adjustment required failure (coverage)."""
    return {
        "schema_version": 2,
        "regime": "lake",
        "feed": "iex",
        "passed": 1,
        "failed": 1,
        "warned": 0,
        "checks": [
            {
                "name": "coverage_missing",
                "status": "fail",
                "count": 12,
                "evidence": {"detail": "12 (symbol, session) pairs missing"},
            },
        ],
        "required_failures": ["coverage_missing"],
        "adjustment_gating_failures": [],
    }


def _clean_report() -> dict:
    return {
        "schema_version": 2,
        "regime": "lake",
        "feed": "iex",
        "passed": 4,
        "failed": 0,
        "warned": 0,
        "checks": [
            {"name": "adjustment_mismatch", "status": "pass", "count": 0},
            {"name": "split_adjustment_mismatch", "status": "pass", "count": 0},
            {"name": "coverage_missing", "status": "pass", "count": 0},
        ],
        "required_failures": [],
        "adjustment_gating_failures": [],
    }


def test_current_code_parity_fails_closed_on_adjustment_gating_failures() -> None:
    check = _check_data_quality(
        _adj_failing_report(),
        sim_mode="current_code_parity",
        allow_smoke=False,
    )
    assert check.status == "fail"
    assert "adjustment_mismatch" in check.detail
    assert "split_adjustment_mismatch" in check.detail


def test_current_code_parity_still_warns_on_non_adjustment_failures() -> None:
    """``coverage_missing`` is required but not adjustment-gating: parity still permits."""
    check = _check_data_quality(
        _non_adjustment_failing_report(),
        sim_mode="current_code_parity",
        allow_smoke=False,
    )
    assert check.status == "warn"
    assert "coverage_missing" in check.evidence["required_failures"]


def test_intended_realism_fails_closed_on_adjustment_gating_failures() -> None:
    check = _check_data_quality(
        _adj_failing_report(),
        sim_mode="intended_realism",
        allow_smoke=False,
    )
    assert check.status == "fail"
    assert "adjustment_mismatch" in check.detail


def test_smoke_fixture_with_allow_smoke_skips_dq() -> None:
    """``smoke_fixture`` with ``allow_smoke=True`` is plumbing — DQ gating not applicable."""
    check = _check_data_quality(
        _clean_report(),
        sim_mode="smoke_fixture",
        allow_smoke=True,
    )
    assert check.status in ("pass", "skipped")


def test_clean_report_passes_current_code_parity() -> None:
    check = _check_data_quality(
        _clean_report(),
        sim_mode="current_code_parity",
        allow_smoke=False,
    )
    assert check.status == "pass"
