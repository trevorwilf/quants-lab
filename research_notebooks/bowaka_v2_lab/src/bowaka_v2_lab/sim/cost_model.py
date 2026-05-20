"""Execution cost model — base / conservative / severe stress levels.

Port of ``bowaka_v2_cost_model.py``'s 3-level structure (lines 1-12).
"""
from __future__ import annotations

from dataclasses import dataclass


COST_STRESS_LEVELS = ("base", "conservative", "severe")


@dataclass(frozen=True)
class CostParameters:
    half_spread_bps: float  # half-spread added on top of mid
    commission_bps: float   # per-share commission expressed in bps of notional
    impact_bps_per_pct_adv: float  # market-impact slippage per 1% of ADV participation


_PARAMS: dict[str, CostParameters] = {
    "base":         CostParameters(half_spread_bps=2.0, commission_bps=0.5, impact_bps_per_pct_adv=2.0),
    "conservative": CostParameters(half_spread_bps=5.0, commission_bps=1.0, impact_bps_per_pct_adv=5.0),
    "severe":       CostParameters(half_spread_bps=15.0, commission_bps=2.0, impact_bps_per_pct_adv=12.0),
}


def get_params(stress_level: str) -> CostParameters:
    if stress_level not in _PARAMS:
        raise ValueError(f"unknown stress_level {stress_level!r}; allowed: {COST_STRESS_LEVELS}")
    return _PARAMS[stress_level]


def slippage_bps(
    *,
    stress_level: str,
    adv_participation_frac: float,
) -> float:
    """Total per-fill slippage in basis points (half-spread + commission + impact)."""
    p = get_params(stress_level)
    impact = p.impact_bps_per_pct_adv * (adv_participation_frac * 100.0)
    return p.half_spread_bps + p.commission_bps + impact
