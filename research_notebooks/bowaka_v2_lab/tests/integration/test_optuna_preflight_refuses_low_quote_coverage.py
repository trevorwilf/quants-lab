"""Optuna preflight refuses to start a study when quote coverage is too low.

Realism remediation Phase 9, Task 3. Realistic fills need historical quotes; a
study against a lake with insufficient quote coverage would optimize against
the synthetic-quote fallback, not real execution.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.optuna.preflight import (
    PreflightError,
    probe_quote_coverage,
    run_preflight,
)


def _clean_dq() -> dict:
    return {"regime": "lake", "feed": "sip", "failed": 0, "required_failures": [],
            "checks": []}


def test_preflight_raises_below_the_coverage_threshold() -> None:
    with pytest.raises(PreflightError) as exc:
        run_preflight(
            sim_mode="intended_realism",
            allow_smoke=False,
            dq_report=_clean_dq(),
            quote_coverage_pct=40.0,
            min_quote_coverage_pct=95.0,
        )
    assert "quote coverage" in str(exc.value).lower()


def test_preflight_passes_at_or_above_the_threshold() -> None:
    result = run_preflight(
        sim_mode="intended_realism",
        allow_smoke=False,
        dq_report=_clean_dq(),
        quote_coverage_pct=96.0,
        min_quote_coverage_pct=95.0,
    )
    assert result.passed is True
    cov = next(c for c in result.checks if c.name == "quote_coverage")
    assert cov.status == "pass"


def test_preflight_quote_check_records_the_measured_coverage() -> None:
    result = run_preflight(
        sim_mode="intended_realism",
        allow_smoke=False,
        dq_report=_clean_dq(),
        quote_coverage_pct=12.5,
        min_quote_coverage_pct=95.0,
        raise_on_fail=False,
    )
    cov = next(c for c in result.checks if c.name == "quote_coverage")
    assert cov.status == "fail"
    assert cov.evidence["historical_quote_coverage_pct"] == 12.5
    assert cov.evidence["min_quote_coverage_pct"] == 95.0


def test_probe_quote_coverage_with_no_quotes_returns_zero_then_refuses() -> None:
    """A quote supplier that always returns None -> 0% coverage -> study refused."""
    import datetime as dt

    def empty_quote_supplier(symbol, ts, max_age_seconds=None):  # noqa: ARG001
        return None

    coverage = probe_quote_coverage(
        symbols=["AAA", "BBB"],
        sessions=[dt.date(2024, 1, 2), dt.date(2024, 1, 3)],
        quote_supplier=empty_quote_supplier,
        scan_times_per_session=lambda d: ["09:45", "10:00", "10:15"],
    )
    assert coverage == 0.0
    with pytest.raises(PreflightError):
        run_preflight(
            sim_mode="intended_realism",
            allow_smoke=False,
            dq_report=_clean_dq(),
            quote_coverage_pct=coverage,
            min_quote_coverage_pct=95.0,
        )


def test_probe_quote_coverage_none_supplier_returns_none() -> None:
    """No quote supplier -> None coverage -> intended_realism fails CLOSED.

    Audit 2026-05-23 §P0-003 reversed the prior fail-open behavior. Under
    ``intended_realism`` a missing quote-coverage probe is no longer ``skipped``
    — the realism simulator would otherwise silently fall back to the
    zero-spread quote model. ``current_code_parity`` / ``smoke_fixture``
    continue to ``skipped``.
    """
    import datetime as dt

    coverage = probe_quote_coverage(
        symbols=["AAA"],
        sessions=[dt.date(2024, 1, 2)],
        quote_supplier=None,
        scan_times_per_session=lambda d: ["09:45"],
    )
    assert coverage is None
    # intended_realism — must fail closed.
    with pytest.raises(PreflightError):
        run_preflight(
            sim_mode="intended_realism",
            allow_smoke=False,
            dq_report=_clean_dq(),
            quote_coverage_pct=coverage,
        )
    # current_code_parity — still skipped (parity uses the quote fallback).
    result = run_preflight(
        sim_mode="current_code_parity",
        allow_smoke=False,
        dq_report=_clean_dq(),
        quote_coverage_pct=coverage,
        raise_on_fail=False,
    )
    cov = next(c for c in result.checks if c.name == "quote_coverage")
    assert cov.status == "skipped"


def test_preflight_does_not_refuse_current_code_parity_on_low_coverage() -> None:
    """current_code_parity uses the zero-spread quote fallback — low historical
    quote coverage is a surfaced warning, not a refusal."""
    result = run_preflight(
        sim_mode="current_code_parity",
        allow_smoke=False,
        dq_report=_clean_dq(),
        quote_coverage_pct=10.0,
        min_quote_coverage_pct=95.0,
    )
    assert result.passed is True
    cov = next(c for c in result.checks if c.name == "quote_coverage")
    assert cov.status == "warn"
