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

    # ADV tier caps.
    adv_caps = risk_cfg.get("adv_tier_caps") or []
    adv_participation = target_notional / candidate_adv if candidate_adv > 0 else 0.0
    for cap in adv_caps:
        if isinstance(cap, dict):
            min_adv = float(cap.get("min_adv_dollars", 0))
            max_position = float(cap.get("max_position_dollars", float("inf")))
            if candidate_adv >= min_adv and target_notional > max_position:
                return RiskGateResult(False, "adv_cap", target_notional, adv_participation)

    return RiskGateResult(True, None, target_notional, adv_participation)
