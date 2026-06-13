"""Pre-trade risk gates per [Report §9.10].

Evaluates every configured control:
- max_concurrent_positions     (read from ``sizing`` — see Phase 5 below)
- max_total_entries_per_day
- max_gross_exposure_pct
- daily_loss_pct
- strategy_slice_loss_pct
- max_stopouts_per_day
- stop_trading_after_consecutive_stopouts
- adv_tier_caps                 (applied to the AGGREGATE symbol notional)

Realism remediation Phase 5 — live-parity fixes:

- ``max_concurrent_positions`` is read from ``sizing_cfg``, NOT ``risk_cfg``.
  This matches the live strategy verbatim (``bowaka_v2_strategy.py:444-446``):
  the live ``_risk_gates`` does ``int(sizing_cfg.get("max_concurrent_positions",
  18))``. ``risk.max_concurrent_positions`` is a tolerated legacy fallback.
- The ADV-tier cap binds the AGGREGATE position in the symbol — the dollar
  notional already open in the symbol plus the candidate's target notional —
  per live ``bowaka_v2_strategy.py:474-488`` (``_symbol_open_notional(state,
  symbol) + target_notional``). Stacking lots across days therefore cannot
  blow through the symbol's liquidity limit.
- ``strategy_slice_loss_pct`` is enforced against ``bankroll *
  strategy_slice_loss_pct`` — see ``docs/current_code_vs_intended_realism.md``
  §"Strategy-slice loss gate" for how this relates to the live code.
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
    symbol: str = "",
) -> RiskGateResult:
    """Return (accepted, reject_reason). Rejects use canonical reason names.

    ``symbol`` is required for the aggregate-symbol ADV cap (Phase 5): the cap
    binds existing open lots in the symbol plus the candidate. It defaults to
    ``""`` so legacy callers that omit it still resolve the cap against the
    candidate notional alone (no existing lots match the empty symbol).
    """
    state = portfolio.state
    if state is None:
        return RiskGateResult(False, "kill_switch", target_notional, 0.0)

    if state.kill_switch_state is not None:
        return RiskGateResult(False, "kill_switch", target_notional, 0.0)

    # Realism remediation 2 Phase 6 (audit P0-007) — refuse the candidate when
    # the protection state machine has set ``state.entries_blocked = True`` on
    # an open lot in :attr:`ProtectionState.UNPROTECTED_VIOLATION` /
    # ENTRIES_BLOCKED. The block clears the moment the violating lot reaches
    # PROTECTED again or closes flat (see Portfolio._refresh_entries_blocked).
    if getattr(state, "entries_blocked", False):
        try:
            portfolio.protection_metrics.entries_blocked_by_protection_count += 1
        except Exception:  # noqa: BLE001 — guarded for legacy Portfolio shims
            pass
        return RiskGateResult(
            False, "entries_blocked_by_protection", target_notional, 0.0
        )

    # max_concurrent_positions — Phase 5: read from `sizing`, not `risk`, per
    # live `bowaka_v2_strategy.py:444-446`. `risk.max_concurrent_positions` is
    # honored only as a legacy fallback when sizing omits it.
    max_concurrent = sizing_cfg.get("max_concurrent_positions")
    if max_concurrent is None:
        max_concurrent = risk_cfg.get("max_concurrent_positions", 18)
    max_concurrent = int(max_concurrent)
    if len(portfolio.open_positions) >= max_concurrent:
        return RiskGateResult(False, "max_concurrent_positions", target_notional, 0.0)

    max_entries = int(risk_cfg.get("max_total_entries_per_day", 12))
    if state.entries_today >= max_entries:
        return RiskGateResult(False, "daily_entry_cap", target_notional, 0.0)

    # L15: live `_risk_gates` enforces NEITHER stopout cap — they only ever fired in
    # the sim because of the hard-coded 4/3 defaults (a config that OMITS the key
    # still got capped, diverging from live). Gate both behind KEY PRESENCE (like
    # strategy_slice_loss_pct below) so an absent key = no gate, matching live; a
    # config that genuinely wants a cap still sets it explicitly.
    if "max_stopouts_per_day" in risk_cfg:
        max_stopouts = int(risk_cfg["max_stopouts_per_day"])
        if state.stopouts_today >= max_stopouts:
            return RiskGateResult(False, "kill_switch", target_notional, 0.0)

    if "stop_trading_after_consecutive_stopouts" in risk_cfg:
        consec_stopout_limit = int(risk_cfg["stop_trading_after_consecutive_stopouts"])
        if state.consecutive_stopouts >= consec_stopout_limit:
            state.kill_switch_state = "consecutive_stopouts"
            return RiskGateResult(False, "kill_switch", target_notional, 0.0)

    max_gross = float(risk_cfg.get("max_gross_exposure_pct", 0.50))
    new_gross_dollars = state.gross_exposure_dollars + target_notional
    new_gross_pct = new_gross_dollars / state.bankroll if state.bankroll > 0 else 0.0
    if new_gross_pct > max_gross:
        return RiskGateResult(False, "gross_exposure_cap", target_notional, 0.0)

    # daily_loss_pct kill switch — §sim_core.md:57 reconcile. Live `_risk_gates`
    # refuses new entries on the daily REALIZED loss only (no mid-day flatten, no
    # unrealized term). The sim previously summed daily_unrealized_pnl, which is
    # refreshed only at EOD / update_mtm -> stale (often 0) on an intraday SCAN, so
    # the kill diverged from live. Use realized-only to match live; the sim still
    # only refuses new entries here (no mid-day flatten), as live does.
    # strategy_slice_loss_pct below keeps its own realized+unrealized basis.
    daily_loss_pct = float(risk_cfg.get("daily_loss_pct", 0.02))
    total_daily_pnl = state.daily_realized_pnl + state.daily_unrealized_pnl
    if state.bankroll > 0 and (-state.daily_realized_pnl / state.bankroll) >= daily_loss_pct:
        state.kill_switch_state = "daily_loss"
        return RiskGateResult(False, "kill_switch", target_notional, 0.0)

    # strategy_slice_loss_pct kill switch — Phase 5. Enforced against
    # `bankroll * strategy_slice_loss_pct`. See docs/current_code_vs_intended_
    # realism.md: the live `_risk_gates` enforces only `daily_loss_pct` against
    # the per-strategy realized PnL; the lab keeps `strategy_slice_loss_pct` as
    # a distinct, stricter (or looser) per-slice cap so the intended-realism
    # contract can carry it without disturbing parity.
    if "strategy_slice_loss_pct" in risk_cfg:
        slice_loss_pct = float(risk_cfg["strategy_slice_loss_pct"])
        if state.bankroll > 0 and (-total_daily_pnl / state.bankroll) >= slice_loss_pct:
            state.kill_switch_state = "strategy_loss"
            return RiskGateResult(False, "kill_switch", target_notional, 0.0)

    # ADV tier caps — ported live `adv_tier_cap` (Phase 1). Skipped when ADV is
    # unknown / non-positive, matching live `_risk_gates`. Phase 5: the cap
    # binds the AGGREGATE symbol notional — the dollars already open in this
    # symbol across all its lots plus the candidate — per live
    # `bowaka_v2_strategy.py:474-488`.
    adv_participation = target_notional / candidate_adv if candidate_adv > 0 else 0.0
    if candidate_adv is not None and candidate_adv > 0:
        allowed, cap_dollars = adv_tier_cap(candidate_adv, {"risk": dict(risk_cfg)})
        projected_notional = portfolio.symbol_open_notional(symbol) + target_notional
        if not allowed or (cap_dollars and projected_notional > cap_dollars):
            return RiskGateResult(False, "adv_cap", target_notional, adv_participation)

    return RiskGateResult(True, None, target_notional, adv_participation)
