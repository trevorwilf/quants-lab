"""Optuna refuses an intended_realism study when the lake cannot support it.

Realism remediation 2 Phase 8 (audit §P0-011). intended_realism is only
admissible when:

1. ``market_data.require_adjusted_daily_bars`` is True (the contract value);
2. the dataset's DQ report has no failing required checks;
3. real historical quote coverage is at or above the configured threshold
   (default 95%).
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.optuna.walkforward_runner import (
    IntendedRealismDataInsufficient,
    assert_intended_realism_data_prerequisites,
)


def _intended_realism_cfg(**md_overrides) -> dict:
    """A minimal intended_realism config with overridable market_data fields."""
    md = {"feed": "sip", "require_adjusted_daily_bars": True}
    md.update(md_overrides)
    return {"simulation": {"mode": "intended_realism"}, "market_data": md}


def test_refuses_when_require_adjusted_daily_bars_is_false() -> None:
    """The realism gate raises when the config does not require adjusted bars."""
    cfg = _intended_realism_cfg(require_adjusted_daily_bars=False)
    with pytest.raises(IntendedRealismDataInsufficient, match="require_adjusted_daily_bars"):
        assert_intended_realism_data_prerequisites(
            cfg, dq_report=None, quote_coverage_pct=99.0,
            min_quote_coverage_pct=95.0,
        )


def test_refuses_when_required_dq_check_fails() -> None:
    """The realism gate raises when the DQ report has a failing required check."""
    cfg = _intended_realism_cfg()
    dq = {
        "regime": "lake", "feed": "sip", "failed": 2, "passed": 5,
        "required_failures": ["coverage_missing_late_session"],
        "checks": [],
    }
    with pytest.raises(IntendedRealismDataInsufficient, match="coverage_missing_late_session"):
        assert_intended_realism_data_prerequisites(
            cfg, dq_report=dq, quote_coverage_pct=99.0,
            min_quote_coverage_pct=95.0,
        )


def test_refuses_when_quote_coverage_is_below_threshold() -> None:
    """The realism gate raises when real quote coverage is below the threshold."""
    cfg = _intended_realism_cfg()
    with pytest.raises(IntendedRealismDataInsufficient, match="quote coverage"):
        assert_intended_realism_data_prerequisites(
            cfg, dq_report=None, quote_coverage_pct=42.0,
            min_quote_coverage_pct=95.0,
        )


def test_admits_when_all_prereqs_pass() -> None:
    """A real intended_realism config + a clean lake clears the gate."""
    cfg = _intended_realism_cfg()
    dq = {
        "regime": "lake", "feed": "sip", "failed": 0, "passed": 5,
        "required_failures": [], "checks": [],
    }
    # No raise.
    assert_intended_realism_data_prerequisites(
        cfg, dq_report=dq, quote_coverage_pct=99.0,
        min_quote_coverage_pct=95.0,
    )


def test_admits_when_metrics_unknown() -> None:
    """A ``None`` DQ report / quote-coverage measurement does NOT fail the gate.

    The cheaper preflight already records ``skipped`` and the new per-fold
    preflight gates the actual data. This gate is the explicit early-fail when
    we *have* measured the lake and it is insufficient.
    """
    cfg = _intended_realism_cfg()
    # No raise — None inputs skip the gate.
    assert_intended_realism_data_prerequisites(
        cfg, dq_report=None, quote_coverage_pct=None,
        min_quote_coverage_pct=95.0,
    )


def test_does_not_apply_to_current_code_parity_or_smoke() -> None:
    """The gate is a no-op for non-intended_realism modes."""
    for mode in ("current_code_parity", "smoke_fixture"):
        cfg = {"simulation": {"mode": mode}, "market_data": {"feed": "iex"}}
        # No raise; gate is intended_realism-only.
        assert_intended_realism_data_prerequisites(
            cfg, dq_report={"required_failures": ["whatever"]},
            quote_coverage_pct=0.0, min_quote_coverage_pct=95.0,
        )
