"""Risk-control promotion gate (audit 2026-05-23 §P1-004).

The user chose to keep risk-control parameters in the Optuna search space
rather than freeze them. The mitigation is the promotion gate: any drift past
epsilon caps the effective tier at ``research_only`` and labels the run
``risk_policy_experiment``. The IEX partial-tape cap is independent.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.optuna.promotion_gates import (
    HARD_RISK_CONTROL_FIELDS,
    evaluate_promotion,
    risk_control_drift,
)


_BASELINE = {
    "risk.daily_loss_pct": 0.03,
    "risk.max_gross_exposure_pct": 0.50,
    "risk.max_total_entries_per_day": 12,
    "risk.max_lots_per_symbol": 1,
    "risk.max_stopouts_per_day": 4,
    "risk.stop_trading_after_consecutive_stopouts": 3,
}


# --------------------------------------------------------------------------
# risk_control_drift
# --------------------------------------------------------------------------
def test_drift_empty_for_identical_params():
    assert risk_control_drift(_BASELINE, dict(_BASELINE)) == []


def test_drift_lists_changed_fractional_field():
    candidate = dict(_BASELINE)
    candidate["risk.daily_loss_pct"] = 0.05
    drift = risk_control_drift(_BASELINE, candidate)
    assert len(drift) == 1
    assert drift[0]["field"] == "risk.daily_loss_pct"
    assert drift[0]["incumbent"] == 0.03
    assert drift[0]["candidate"] == 0.05
    assert drift[0]["delta"] == pytest.approx(0.02)


def test_drift_lists_integer_field_one_step_change():
    candidate = dict(_BASELINE)
    candidate["risk.max_total_entries_per_day"] = 13  # +1 — past eps=0
    drift = risk_control_drift(_BASELINE, candidate)
    assert any(d["field"] == "risk.max_total_entries_per_day" for d in drift)


def test_drift_ignores_tiny_fractional_movements_inside_eps():
    """A 1e-5 change in daily_loss_pct is within the 1e-4 tolerance."""
    candidate = dict(_BASELINE)
    candidate["risk.daily_loss_pct"] = 0.030001
    drift = risk_control_drift(_BASELINE, candidate)
    assert drift == []


def test_drift_skips_fields_absent_in_candidate():
    candidate = {k: v for k, v in _BASELINE.items() if k != "risk.daily_loss_pct"}
    drift = risk_control_drift(_BASELINE, candidate)
    assert drift == []


# --------------------------------------------------------------------------
# evaluate_promotion
# --------------------------------------------------------------------------
def test_no_drift_permits_requested_tier():
    ev = evaluate_promotion(
        incumbent_params=_BASELINE,
        candidate_params=dict(_BASELINE),
        requested_tier="paper_candidate",
        feed="sip",
    )
    assert ev["promotable"] is True
    assert ev["effective_tier"] == "paper_candidate"
    assert ev["risk_policy_experiment"] is False
    assert ev["refusal_reasons"] == []


def test_daily_loss_pct_drift_caps_tier():
    candidate = dict(_BASELINE)
    candidate["risk.daily_loss_pct"] = 0.05
    ev = evaluate_promotion(
        incumbent_params=_BASELINE, candidate_params=candidate,
        requested_tier="paper_candidate", feed="sip",
    )
    assert ev["promotable"] is False
    assert ev["effective_tier"] == "research_only"
    assert ev["risk_policy_experiment"] is True
    assert any("daily_loss_pct" in r for r in ev["refusal_reasons"])


def test_integer_drift_in_max_lots_caps_tier():
    candidate = dict(_BASELINE)
    candidate["risk.max_lots_per_symbol"] = 2  # +1
    ev = evaluate_promotion(
        incumbent_params=_BASELINE, candidate_params=candidate,
        requested_tier="live_candidate", feed="sip",
    )
    assert ev["promotable"] is False
    assert ev["effective_tier"] == "research_only"
    assert ev["risk_policy_experiment"] is True


def test_research_only_request_always_promotable():
    """research_only is the floor — any input combination is promotable to it."""
    candidate = dict(_BASELINE)
    candidate["risk.daily_loss_pct"] = 0.50  # huge drift
    ev = evaluate_promotion(
        incumbent_params=_BASELINE, candidate_params=candidate,
        requested_tier="research_only", feed="iex",
    )
    assert ev["promotable"] is True
    assert ev["effective_tier"] == "research_only"
    # Drift still recorded for forensic value.
    assert ev["risk_policy_experiment"] is True


def test_iex_feed_caps_at_research_only_even_without_risk_drift():
    """IEX partial-tape cap fires independently of the risk gate."""
    ev = evaluate_promotion(
        incumbent_params=_BASELINE, candidate_params=dict(_BASELINE),
        requested_tier="paper_candidate", feed="iex",
    )
    assert ev["promotable"] is False
    assert ev["effective_tier"] == "research_only"
    assert ev["feed_cap_applied"] is True
    assert ev["risk_policy_experiment"] is False
    assert any("iex" in r.lower() for r in ev["refusal_reasons"])


def test_sip_feed_unaffected_by_iex_cap():
    """SIP studies are NOT capped by the IEX rule."""
    ev = evaluate_promotion(
        incumbent_params=_BASELINE, candidate_params=dict(_BASELINE),
        requested_tier="paper_candidate", feed="sip",
    )
    assert ev["promotable"] is True
    assert ev["feed_cap_applied"] is False


def test_hard_risk_control_fields_match_audit_list():
    """The set of audited fields is exactly the prompt's HARD_RISK_CONTROL_FIELDS."""
    assert HARD_RISK_CONTROL_FIELDS == (
        "risk.daily_loss_pct",
        "risk.max_gross_exposure_pct",
        "risk.max_total_entries_per_day",
        "risk.max_lots_per_symbol",
        "risk.max_stopouts_per_day",
        "risk.stop_trading_after_consecutive_stopouts",
    )


def test_nested_params_dict_also_works():
    """A nested ``{"risk": {"daily_loss_pct": ...}}`` config is tolerated."""
    incumbent = {"risk": {"daily_loss_pct": 0.03, "max_lots_per_symbol": 1}}
    candidate = {"risk": {"daily_loss_pct": 0.05, "max_lots_per_symbol": 1}}
    drift = risk_control_drift(incumbent, candidate)
    assert len(drift) == 1
    assert drift[0]["field"] == "risk.daily_loss_pct"
