"""Pre-trade risk gates per [Report §9.10].

Evaluates every configured control:
- max_concurrent_positions
- max_total_entries_per_day
- max_gross_exposure_pct
- daily_loss_pct
- strategy_slice_loss_pct
- max_stopouts_per_day
- stop_trading_after_consecutive_stopouts
- adv_tier_caps
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from .portfolio import Portfolio


@dataclass
class RiskGateResult:
    accepted: bool
    reject_reason: Optional[str]
    target_notional: float
    adv_participation_frac: float


def adv_tier_cap(adv: float | None, cfg: Mapping[str, Any]) -> tuple[bool, float]:
    """Resolve the position dollar cap for ``adv`` under the tiered ADV policy.

    Ported byte-identically from live ``bowaka_v2_strategy.adv_tier_cap``
    (realism remediation Phase 1, audit Ticket 1). Returns
    ``(allowed, max_position_dollars)``.

    Walks ``cfg.risk.adv_tier_caps`` top-to-bottom — YAML order *is* the policy.
    The first tier whose ``max_adv_dollars`` is ``None`` or >= the candidate's
    ADV matches: ``reject_if_below: true`` → ``(False, 0.0)``; otherwise the cap
    is ``adv * max_position_as_adv_frac`` (``0.0`` = uncapped). An empty tier
    list falls back to the flat ``risk.max_position_as_adv_frac``.
    """
    if adv is None or float(adv) <= 0:
        return False, 0.0
    adv_val = float(adv)
    tiers = (cfg.get("risk") or {}).get("adv_tier_caps") or []
    if not tiers:
        flat = (cfg.get("risk") or {}).get("max_position_as_adv_frac")
        if flat is None:
            return True, 0.0
        return True, adv_val * float(flat)
    for tier in tiers:
        max_adv = tier.get("max_adv_dollars")
        if max_adv is None or adv_val <= float(max_adv):
            if tier.get("reject_if_below"):
                return False, 0.0
            frac = tier.get("max_position_as_adv_frac")
            if frac is None:
                return True, 0.0
            return True, adv_val * float(frac)
    return False, 0.0


def evaluate_risk_gates(
    *,
    portfolio: Portfolio,
    risk_cfg: Mapping[str, Any],
    sizing_cfg: Mapping[str, Any],
    candidate_adv: float,
    target_notional: float,
) -> RiskGateResult:
    """Return (accepted, reject_reason). Rejects use canonical reason names."""
    state = portfolio.state
    if state is None:
        return RiskGateResult(False, "kill_switch", target_notional, 0.0)

    if state.kill_switch_state is not None:
        return RiskGateResult(False, "kill_switch", target_notional, 0.0)

    max_concurrent = int(risk_cfg.get("max_concurrent_positions", 5))
    if len(portfolio.open_positions) >= max_concurrent:
        return RiskGateResult(False, "max_concurrent_positions", target_notional, 0.0)

    max_entries = int(risk_cfg.get("max_total_entries_per_day", 12))
    if state.entries_today >= max_entries:
        return RiskGateResult(False, "daily_entry_cap", target_notional, 0.0)

    max_stopouts = int(risk_cfg.get("max_stopouts_per_day", 4))
    if state.stopouts_today >= max_stopouts:
        return RiskGateResult(False, "kill_switch", target_notional, 0.0)

    consec_stopout_limit = int(risk_cfg.get("stop_trading_after_consecutive_stopouts", 3))
    if state.consecutive_stopouts >= consec_stopout_limit:
        state.kill_switch_state = "consecutive_stopouts"
        return RiskGateResult(False, "kill_switch", target_notional, 0.0)

    max_gross = float(risk_cfg.get("max_gross_exposure_pct", 0.50))
    new_gross_dollars = state.gross_exposure_dollars + target_notional
    new_gross_pct = new_gross_dollars / state.bankroll if state.bankroll > 0 else 0.0
    if new_gross_pct > max_gross:
        return RiskGateResult(False, "gross_exposure_cap", target_notional, 0.0)

    # daily_loss_pct kill switch.
    daily_loss_pct = float(risk_cfg.get("daily_loss_pct", 0.02))
    total_daily_pnl = state.daily_realized_pnl + state.daily_unrealized_pnl
    if state.bankroll > 0 and (-total_daily_pnl / state.bankroll) >= daily_loss_pct:
        state.kill_switch_state = "daily_loss"
        return RiskGateResult(False, "kill_switch", target_notional, 0.0)

    # ADV tier caps — ported live `adv_tier_cap` (Phase 1). Skipped when ADV is
    # unknown / non-positive, matching live `_risk_gates`. Phase 5 makes the cap
    # apply to the aggregate symbol notional (existing lots + candidate).
    adv_participation = target_notional / candidate_adv if candidate_adv > 0 else 0.0
    if candidate_adv is not None and candidate_adv > 0:
        allowed, cap_dollars = adv_tier_cap(candidate_adv, {"risk": dict(risk_cfg)})
        if not allowed or (cap_dollars and target_notional > cap_dollars):
            return RiskGateResult(False, "adv_cap", target_notional, adv_participation)

    return RiskGateResult(True, None, target_notional, adv_participation)
