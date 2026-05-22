"""Optuna preflight refuses to start a study when data-quality checks fail.

Realism remediation Phase 9, Task 3. A walk-forward study is a multi-hour job;
it must not start against a dataset whose data-quality report has a failing
*required* check.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.optuna.preflight import (
    PreflightError,
    run_preflight,
)


def _failing_dq_report() -> dict:
    """A lake-regime DQ report with a failing required check."""
    return {
        "schema_version": 2,
        "regime": "lake",
        "feed": "sip",
        "passed": 3,
        "failed": 1,
        "warned": 0,
        "checks": [
            {"name": "coverage_missing", "status": "fail", "count": 12,
             "evidence": {"detail": "12 (symbol, session) pairs missing"}},
        ],
        "required_failures": ["coverage_missing"],
    }


def _clean_dq_report() -> dict:
    return {
        "schema_version": 2,
        "regime": "lake",
        "feed": "sip",
        "passed": 5,
        "failed": 0,
        "warned": 1,
        "checks": [{"name": "coverage_missing", "status": "pass", "count": 0}],
        "required_failures": [],
    }


def test_preflight_raises_on_failing_required_dq_check() -> None:
    with pytest.raises(PreflightError) as exc:
        run_preflight(
            sim_mode="intended_realism",
            allow_smoke=False,
            dq_report=_failing_dq_report(),
            quote_coverage_pct=100.0,
        )
    assert "data-quality" in str(exc.value) or "data_quality" in str(exc.value)
    assert "coverage_missing" in str(exc.value)


def test_preflight_records_the_failing_dq_check() -> None:
    result = run_preflight(
        sim_mode="intended_realism",
        allow_smoke=False,
        dq_report=_failing_dq_report(),
        quote_coverage_pct=100.0,
        raise_on_fail=False,
    )
    assert result.passed is False
    dq_check = next(c for c in result.checks if c.name == "data_quality")
    assert dq_check.status == "fail"
    assert "coverage_missing" in dq_check.evidence["required_failures"]


def test_preflight_passes_on_a_clean_dq_report() -> None:
    result = run_preflight(
        sim_mode="intended_realism",
        allow_smoke=False,
        dq_report=_clean_dq_report(),
        quote_coverage_pct=100.0,
    )
    assert result.passed is True
    dq_check = next(c for c in result.checks if c.name == "data_quality")
    assert dq_check.status == "pass"


def test_preflight_does_not_refuse_current_code_parity_on_failing_dq() -> None:
    """current_code_parity is not DQ-gated — a failing required check warns, not fails.

    Mirrors the data_quality.py contract: only intended_realism is gated.
    """
    result = run_preflight(
        sim_mode="current_code_parity",
        allow_smoke=False,
        dq_report=_failing_dq_report(),
        quote_coverage_pct=100.0,
    )
    assert result.passed is True
    dq_check = next(c for c in result.checks if c.name == "data_quality")
    assert dq_check.status == "warn"
    assert "coverage_missing" in dq_check.evidence["required_failures"]
