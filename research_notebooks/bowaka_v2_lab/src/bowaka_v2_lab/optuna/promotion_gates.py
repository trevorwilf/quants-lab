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

from typing import Any, Iterable, Mapping, Optional


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


__all__ = [
    "HARD_RISK_CONTROL_FIELDS",
    "risk_control_drift",
    "evaluate_promotion",
]
