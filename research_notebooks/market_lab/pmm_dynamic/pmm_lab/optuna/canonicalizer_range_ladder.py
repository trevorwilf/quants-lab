"""range_ladder parameter canonicalization.

Raw generative params → validated `RangeLadderConfig` in a CandidateBundle.

Signals invalidity exactly like the other canonicalizers: returns
(None, reason). The objective wrapper translates a rejected config into
`optuna.TrialPruned` (per the Phase A spec — hard constraints prune rather
than score REJECT).

All fee-dependent floors are read from the connector's exchange rules
(`pair_rules.fees.maker_fee`) — NEVER a hardcoded 0.002 — so the same
constraints scale across connectors (nonkyc fee 0.002 → dead-zone floor
0.008; kraken fee 0.0025 → 0.010).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from pmm_lab.config.params import PairRules
from pmm_lab.optuna.candidate import CandidateBundle
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.strategies.range_ladder import RangeLadderConfig
from pmm_lab.strategies.range_ladder_gen import build_rungs, validate_rungs

logger = logging.getLogger(__name__)


def effective_min_order_quote(pair_rules: PairRules, reference_price: float) -> float:
    """Min viable rung notional for the pair.

    The binding constraint is the larger of the exchange's min notional and
    its min base order size valued at the reference price (Kraken's
    `ordermin` is usually the binding one; NonKYC's is the 1 USDT notional).
    """
    floor = float(pair_rules.min_notional_quote)
    if pair_rules.min_order_size_base > 0 and reference_price > 0:
        floor = max(floor, pair_rules.min_order_size_base * reference_price)
    return floor


def canonicalize_range_ladder_params(
    raw_params: Dict[str, Any],
    pair_rules: PairRules,
    reference_price: float,
    bar_interval_seconds: int = 3600,
) -> Tuple[Optional[CandidateBundle], Optional[str]]:
    """Validate raw range_ladder params and build a CandidateBundle.

    The hard constraints (§0 of the Phase A spec) are checked on a ladder
    built at `reference_price`. Per-fold rebuilds re-validate at each fold's
    train anchor; a fold-level failure counts as a gate violation there.

    Returns
    -------
    (CandidateBundle, None) on success
    (None, rejection_reason) on failure
    """
    if reference_price <= 0:
        return None, f"reference_price must be positive; got {reference_price}"

    fee = float(pair_rules.fees.maker_fee)
    fund_quote = float(raw_params.get("fund_quote", 1000.0))
    quote_frac = float(raw_params.get("quote_frac", 0.5))
    cooldown_time = int(raw_params.get("cooldown_time", 3600))
    cooldown_bars = max(0, round(cooldown_time / bar_interval_seconds))

    try:
        config = RangeLadderConfig(
            n_buy=int(raw_params["n_buy"]),
            n_sell=int(raw_params["n_sell"]),
            buy_near_pct=float(raw_params["buy_near_pct"]),
            buy_far_pct=float(raw_params["buy_far_pct"]),
            sell_near_pct=float(raw_params["sell_near_pct"]),
            sell_far_pct=float(raw_params["sell_far_pct"]),
            buy_gamma=float(raw_params["buy_gamma"]),
            sell_gamma=float(raw_params["sell_gamma"]),
            k_buy=float(raw_params["k_buy"]),
            k_sell=float(raw_params["k_sell"]),
            fund_quote=fund_quote,
            quote_frac=quote_frac,
            fee=fee,
            cooldown_bars=int(cooldown_bars),
        )
    except (KeyError, ValueError) as e:
        return None, f"invalid range_ladder params: {e}"

    # Strict band ordering must hold before any ladder can be built.
    if not (config.buy_far_pct > config.buy_near_pct):
        return None, (
            f"buy_far_pct ({config.buy_far_pct:.6f}) must be > "
            f"buy_near_pct ({config.buy_near_pct:.6f})"
        )
    if not (config.sell_far_pct > config.sell_near_pct):
        return None, (
            f"sell_far_pct ({config.sell_far_pct:.6f}) must be > "
            f"sell_near_pct ({config.sell_near_pct:.6f})"
        )

    min_order_quote = effective_min_order_quote(pair_rules, reference_price)
    try:
        rungs = build_rungs(reference_price, config, pair_rules.price_tick)
    except ValueError as e:
        return None, f"rung construction failed at reference price: {e}"

    ok, reason = validate_rungs(
        rungs,
        anchor=reference_price,
        fee=fee,
        price_tick=pair_rules.price_tick,
        min_order_quote=min_order_quote,
        fund=fund_quote,
        quote_frac=quote_frac,
        buy_near_pct=config.buy_near_pct,
        buy_far_pct=config.buy_far_pct,
        sell_near_pct=config.sell_near_pct,
        sell_far_pct=config.sell_far_pct,
    )
    if not ok:
        return None, reason

    engine_config = EngineConfig(
        total_amount_quote=fund_quote,
        executor_refresh_time=float(raw_params.get("executor_refresh_time", 43200)),
        cooldown_time=float(cooldown_time),
    )

    bundle = CandidateBundle(
        strategy_name="range_ladder",
        strategy_config=config,
        engine_config=engine_config,
        export_meta={
            "controller_name": "range_inventory_ladder",
            "controller_type": "market_making",
        },
    )
    return bundle, None
