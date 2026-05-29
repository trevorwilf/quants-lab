"""Risk-control promotion gate (audit 2026-05-23 §P1-004).

The user explicitly chose to leave risk-control parameters in the Optuna search
space (rather than freezing them). The mitigation is a hard promotion-gate
refusal when the winning trial's risk-control parameters materially differ from
the incumbent: the run is labeled ``risk_policy_experiment`` and the effective
tier is capped at ``research_only`` regardless of the requested tier.

This sits ALONGSIDE the existing IEX partial-tape cap (which already pins IEX
studies at ``research_only``) — the two gates are independent and any one of
them caps the tier.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional, Sequence


#: Risk-control fields the promotion gate watches. Any drift beyond the
#: per-field epsilon flips ``risk_policy_experiment: true`` and caps the tier.
HARD_RISK_CONTROL_FIELDS: tuple[str, ...] = (
    "risk.daily_loss_pct",
    "risk.max_gross_exposure_pct",
    "risk.max_total_entries_per_day",
    "risk.max_lots_per_symbol",
    "risk.max_stopouts_per_day",
    "risk.stop_trading_after_consecutive_stopouts",
)

#: Tolerance per field — tight enough that any non-trivial move trips the gate.
#: Integer fields use 0 (any change is material); fractional fields use 1e-4.
_EPSILON_BY_FIELD: dict[str, float] = {
    "risk.daily_loss_pct": 1e-4,
    "risk.max_gross_exposure_pct": 1e-4,
    "risk.max_total_entries_per_day": 0,
    "risk.max_lots_per_symbol": 0,
    "risk.max_stopouts_per_day": 0,
    "risk.stop_trading_after_consecutive_stopouts": 0,
}


def _lookup(params: Mapping[str, Any], dotted: str) -> Any:
    """Look up ``dotted`` in a flat dotted-key params dict OR a nested dict.

    Optuna search params arrive as a flat ``{"risk.daily_loss_pct": 0.03}``
    mapping; the contract's incumbent baseline arrives the same way. Nested
    dicts are tolerated for callers that pass the full config.
    """
    if dotted in params:
        return params[dotted]
    parts = dotted.split(".")
    node: Any = params
    for p in parts:
        if isinstance(node, Mapping) and p in node:
            node = node[p]
        else:
            return None
    return node


def risk_control_drift(
    incumbent: Mapping[str, Any],
    candidate: Mapping[str, Any],
    *,
    fields: Iterable[str] = HARD_RISK_CONTROL_FIELDS,
    eps_by_field: Mapping[str, float] = _EPSILON_BY_FIELD,
) -> list[dict[str, Any]]:
    """Return the list of risk-control fields whose candidate moved past eps.

    Each entry: ``{"field": dotted_name, "incumbent": v, "candidate": v,
    "delta": float, "eps": float}``. A field that is absent in either side is
    silently skipped (the optimizer may not have sampled it).
    """
    out: list[dict[str, Any]] = []
    for field in fields:
        inc = _lookup(incumbent, field)
        cand = _lookup(candidate, field)
        if inc is None or cand is None:
            continue
        try:
            inc_f = float(inc)
            cand_f = float(cand)
        except (TypeError, ValueError):
            # Non-numeric — drift iff equality fails.
            if inc != cand:
                out.append({
                    "field": field, "incumbent": inc, "candidate": cand,
                    "delta": None, "eps": None,
                })
            continue
        delta = cand_f - inc_f
        eps = float(eps_by_field.get(field, 0.0))
        if abs(delta) > eps:
            out.append({
                "field": field, "incumbent": inc, "candidate": cand,
                "delta": delta, "eps": eps,
            })
    return out


#: Tiers that may be requested. Order is monotone (research_only < ... < live_candidate).
_TIER_ORDER: tuple[str, ...] = (
    "research_only", "backtesting_only", "paper_candidate", "live_candidate",
)


def _tier_rank(tier: str) -> int:
    try:
        return _TIER_ORDER.index(tier)
    except ValueError:
        return -1


def evaluate_promotion(
    *,
    incumbent_params: Mapping[str, Any],
    candidate_params: Mapping[str, Any],
    requested_tier: str,
    feed: Optional[str] = None,
) -> dict[str, Any]:
    """Compute the promotion-gate decision for a (incumbent, candidate, requested) tuple.

    Returns::

        {
            "promotable": bool,
            "effective_tier": "research_only" | "backtesting_only" | ...,
            "requested_tier": str,
            "refusal_reasons": [str],
            "risk_policy_experiment": bool,
            "risk_drift": [{...}, ...],
            "feed_cap_applied": bool,
        }

    Caps:
    - IEX feed always caps at ``research_only`` (existing partial-tape rule).
    - Any risk-control drift beyond epsilon flips
      ``risk_policy_experiment: true`` and caps the tier at ``research_only``.
    - ``promotable`` is ``True`` only when the requested tier survives every
      cap. A request *at or below* the cap is promotable; a request *above* is
      refused with a ``refusal_reasons`` entry listing the cap source.
    """
    refusal_reasons: list[str] = []
    drift = risk_control_drift(incumbent_params, candidate_params)
    is_risk_policy_experiment = bool(drift)
    effective_tier = requested_tier
    feed_cap_applied = False

    if is_risk_policy_experiment:
        # Any risk drift caps at research_only.
        if _tier_rank(requested_tier) > _tier_rank("research_only"):
            refusal_reasons.append(
                "risk_policy_experiment: risk-control parameter drifted beyond "
                "epsilon from incumbent; "
                + ", ".join(
                    f"{d['field']} ({d['incumbent']} -> {d['candidate']})"
                    for d in drift
                )
            )
        effective_tier = "research_only"

    if feed is not None and str(feed).lower() == "iex":
        feed_cap_applied = True
        if _tier_rank(requested_tier) > _tier_rank("research_only"):
            refusal_reasons.append(
                "iex_feed_cap: IEX is partial-tape; any IEX study caps at "
                "research_only regardless of requested tier"
            )
        if _tier_rank(effective_tier) > _tier_rank("research_only"):
            effective_tier = "research_only"

    promotable = (
        _tier_rank(requested_tier) >= 0
        and _tier_rank(requested_tier) <= _tier_rank(effective_tier)
    )

    return {
        "promotable": promotable,
        "effective_tier": effective_tier,
        "requested_tier": requested_tier,
        "refusal_reasons": refusal_reasons,
        "risk_policy_experiment": is_risk_policy_experiment,
        "risk_drift": drift,
        "feed_cap_applied": feed_cap_applied,
    }


# --------------------------------------------------------------------------
# Structured promotion evidence (audit 2026-05-29 §6.8 / §10.4 / Appendix E.6).
#
# The single ``promotable`` bool conflated "the study ran", "the study is
# valid", "the result is reviewable", and "the result is a parameter
# recommendation". A completed-but-invalid study and a valid IEX research run
# could both surface ``promotable: true`` to a reviewer who did not read the
# partial-tape cap. These separate booleans make each question explicit.
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class PromotionEvidence:
    study_execution_completed: bool
    study_valid: bool
    invalid_reasons: tuple[str, ...]
    reviewable_for_research: bool
    parameter_recommendation_allowed: bool
    promotable_to_paper: bool
    promotable_to_live: bool
    best_params: dict | None
    effective_tier: str       # research_only | backtesting_only | paper_candidate | live_candidate
    requested_tier: str
    caps_applied: tuple[str, ...]   # IEX_PARTIAL_TAPE, RISK_POLICY_EXPERIMENT, ...


def passes_stress_matrix_floor(
    stress_results: Sequence[Any],
    *,
    conservative_floor_score_min: float = 0.0,
    robust_to_severe: bool = False,
) -> tuple[bool, str]:
    """The finalist must remain in-the-black at the conservative floor
    (slippage_bps_offset=50, spread_multiplier=2.0, cost_stress=conservative).

    Audit 2026-05-29 §8.5 / Phase 4a. Severe-tier robustness is optional and
    reported but does not block paper-candidate promotion under this contract.
    ``stress_results`` is duck-typed: each item exposes ``.point`` (with
    ``slippage_bps_offset`` / ``spread_multiplier`` / ``cost_stress``) and
    ``.score``.
    """
    cf = next((r for r in stress_results
               if r.point.slippage_bps_offset == 50
               and r.point.spread_multiplier == 2.0
               and r.point.cost_stress == "conservative"), None)
    if cf is None:
        return False, "missing_conservative_floor_result"
    if cf.score < conservative_floor_score_min:
        return (False,
                f"conservative_floor_score={cf.score:.4f} < "
                f"min={conservative_floor_score_min:.4f}")
    return True, "ok"


#: Phase 4b envelope dimensions (mirror of stress_matrix.ENVELOPE_DIMENSIONS;
#: duplicated here to avoid importing stress_matrix into the gate).
_ENVELOPE_DIMENSIONS: tuple[str, ...] = (
    "conservative_slippage",
    "conservative_spread",
    "conservative_partial_fill",
    "no_fill_policy",
    "adverse_selection",
    "late_day_liquidity",
)


def passes_stress_envelope(
    stress_results: Sequence[Any],
    *,
    min_score_per_dim: float = 0.0,
) -> tuple[bool, list[str]]:
    """The finalist must score positive at the conservative version of EACH
    stress dimension separately (audit 2026-05-29 §8.5 / Phase 4b).

    Backward-compatible: when the results carry no per-dimension labels (the
    Phase-1 conservative-floor-only shape), this falls back to
    :func:`passes_stress_matrix_floor`. ``stress_results`` is duck-typed; each
    item exposes ``.point.label`` and ``.score``.
    """
    labeled = {
        getattr(r.point, "label", ""): r
        for r in stress_results if getattr(r.point, "label", "")
    }
    if not any(d in labeled for d in _ENVELOPE_DIMENSIONS):
        ok, _reason = passes_stress_matrix_floor(
            stress_results, conservative_floor_score_min=min_score_per_dim,
        )
        return ok, ([] if ok else ["conservative_floor"])
    failed = [
        d for d in _ENVELOPE_DIMENSIONS
        if (labeled.get(d) is None or labeled[d].score < min_score_per_dim)
    ]
    return (not failed, failed)


def _rr_get(reconcile_report: Any, attr: str, default: Any = None) -> Any:
    """Duck-typed accessor for a ReconcileReport (dataclass or mapping)."""
    if reconcile_report is None:
        return default
    if hasattr(reconcile_report, attr):
        return getattr(reconcile_report, attr)
    if isinstance(reconcile_report, Mapping):
        return reconcile_report.get(attr, default)
    return default


def evaluate_promotion_evidence(
    *,
    study_valid: bool,
    invalid_reasons: Sequence[str],
    feed: str,                 # "iex" | "sip"
    simulation_mode: str,      # "current_code_parity" | "intended_realism" | "smoke_fixture"
    risk_control_drift: bool,
    paper_reconciliation_artifact_present: bool,
    best_params: Mapping[str, Any] | None,
    requested_tier: str,
    stress_results: Optional[Sequence[Any]] = None,
    reconcile_report: Optional[Any] = None,
) -> PromotionEvidence:
    """Compute structured promotion evidence. Rules (audit §10.4):

    - Invalid study -> every promotion bool False; ``best_params`` None;
      ``effective_tier`` research_only.
    - IEX feed -> caps at research_only: reviewable_for_research True but
      parameter_recommendation_allowed / promotable_* all False.
    - SIP + intended_realism + valid + no risk drift -> parameter
      recommendation allowed.
    - paper requires the paper-reconciliation artifact; live requires paper
      eligibility AND no risk drift.
    - ``effective_tier`` is the highest supported tier, capped by
      ``requested_tier`` (never raised above the request).
    """
    reasons = tuple(invalid_reasons or ())
    if not study_valid:
        return PromotionEvidence(
            study_execution_completed=True,
            study_valid=False,
            invalid_reasons=reasons,
            reviewable_for_research=False,
            parameter_recommendation_allowed=False,
            promotable_to_paper=False,
            promotable_to_live=False,
            best_params=None,
            effective_tier="research_only",
            requested_tier=requested_tier,
            caps_applied=(),
        )

    is_iex = str(feed).lower() == "iex"
    is_realism = simulation_mode == "intended_realism"
    caps: list[str] = []
    if is_iex:
        caps.append("IEX_PARTIAL_TAPE")
    if risk_control_drift:
        caps.append("RISK_POLICY_EXPERIMENT")

    reviewable_for_research = True
    parameter_recommendation_allowed = (
        is_realism and not is_iex and not risk_control_drift
    )
    promotable_to_paper = (
        parameter_recommendation_allowed and bool(paper_reconciliation_artifact_present)
    )
    promotable_to_live = promotable_to_paper and not risk_control_drift

    # Audit 2026-05-29 §8.5 / Phase 4a — the finalist robustness gate. When a
    # stress matrix is supplied and the candidate is otherwise paper-eligible,
    # it must hold the conservative floor; otherwise paper/live are refused.
    if stress_results is not None and promotable_to_paper:
        env_ok, failed_dims = passes_stress_envelope(stress_results)
        if not env_ok:
            promotable_to_paper = False
            promotable_to_live = False
            caps.append("STRESS_MATRIX_FLOOR_FAILED")
            for _d in failed_dims:
                caps.append(f"stress_dim:{_d}")

    # Audit 2026-05-29 §8.7 / Phase 6 — paper / live promotion REQUIRES a
    # passing multi-session paper-reconciliation report. The reconcile gate
    # only engages for the paper / live tiers, so research_only / backtesting
    # callers are unaffected.
    if requested_tier in ("paper_candidate", "live_candidate"):
        paper_ok_pre = promotable_to_paper
        promotable_to_paper = False
        if reconcile_report is None:
            caps.append("RECONCILE_MISSING")
        else:
            rr_status = _rr_get(reconcile_report, "status", "ok")
            if rr_status == "REAL_LOGS_DEFERRED":
                caps.append("REAL_LOGS_DEFERRED")
            elif rr_status == "BELOW_MIN_SESSIONS":
                caps.append(
                    f"BELOW_MIN_SESSIONS ({_rr_get(reconcile_report, 'n_sessions', 0)} sessions)"
                )
            elif not _rr_get(reconcile_report, "passes_all_thresholds", False):
                failing = list(_rr_get(reconcile_report, "failing_metrics", []) or [])
                caps.append(f"RECONCILE_THRESHOLDS_FAILED: {failing}")
            else:
                promotable_to_paper = paper_ok_pre
        promotable_to_live = promotable_to_paper and not risk_control_drift

    supported = "research_only"
    if parameter_recommendation_allowed:
        supported = "backtesting_only"
    if promotable_to_paper:
        supported = "paper_candidate"
    if promotable_to_live:
        supported = "live_candidate"
    # Cap to the requested tier (never raise above the request).
    if _tier_rank(requested_tier) >= 0 and _tier_rank(supported) > _tier_rank(requested_tier):
        effective_tier = requested_tier
    else:
        effective_tier = supported

    return PromotionEvidence(
        study_execution_completed=True,
        study_valid=True,
        invalid_reasons=reasons,
        reviewable_for_research=reviewable_for_research,
        parameter_recommendation_allowed=parameter_recommendation_allowed,
        promotable_to_paper=promotable_to_paper,
        promotable_to_live=promotable_to_live,
        best_params=dict(best_params) if best_params is not None else None,
        effective_tier=effective_tier,
        requested_tier=requested_tier,
        caps_applied=tuple(caps),
    )


__all__ = [
    "HARD_RISK_CONTROL_FIELDS",
    "risk_control_drift",
    "evaluate_promotion",
    "PromotionEvidence",
    "evaluate_promotion_evidence",
    "passes_stress_matrix_floor",
    "passes_stress_envelope",
]
