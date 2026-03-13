"""
Deterministic parameter canonicalization.

Takes raw trial params (flat dict) and produces either a valid SimConfig
or a rejection reason. This function is pure — no side effects, no randomness.
"""

from typing import Tuple, Optional, List, Dict, Any
import numpy as np

from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.config.params import PairRules
from pmm_lab.config.exchange_rules import round_price, round_amount, check_min_notional


def generate_geometric_ladder(base: float, ratio: float, n_levels: int) -> List[float]:
    """Generate a geometric spread ladder.

    spread[i] = base * ratio^i  for i in 0..n_levels-1
    """
    return [base * (ratio ** i) for i in range(n_levels)]


def generate_amount_weights(n_levels: int, skew: float = 1.0) -> List[float]:
    """Generate per-level amount percentages that sum to 1.0.

    Uses geometric weighting: weight[i] = skew^i, then normalize.
    When skew == 1.0, all levels get equal weight.
    When skew > 1.0, outer levels (wider spreads) get more capital.
    """
    if n_levels == 0:
        return []
    raw = [skew ** i for i in range(n_levels)]
    total = sum(raw)
    return [w / total for w in raw]


def _check_side_feasibility(
    n_levels: int,
    side_capital: float,
    weights: List[float],
    reference_price: float,
    pair_rules: PairRules,
    amount_skew: float = 1.0,
) -> int:
    """Check how many levels pass min_notional, reducing from n_levels down.

    Returns the maximum feasible number of levels (may be 0).
    """
    for n in range(n_levels, 0, -1):
        w = generate_amount_weights(n, skew=amount_skew)  # use actual skew
        all_ok = True
        for i in range(n):
            order_quote = side_capital * w[i]
            order_base = order_quote / reference_price if reference_price > 0 else 0.0
            order_base_rounded = round_amount(order_base, pair_rules)
            if not check_min_notional(reference_price, order_base_rounded, pair_rules):
                all_ok = False
                break
        if all_ok:
            return n
    return 0


def canonicalize_params(
    raw_params: Dict[str, Any],
    pair_rules: PairRules,
    reference_price: float,
) -> Tuple[Optional[SimConfig], Optional[str]]:
    """Convert raw trial params into a valid SimConfig, or return a rejection reason.

    Returns (config, None) on success or (None, reason) on rejection.
    """

    if raw_params["macd_fast"] >= raw_params["macd_slow"]:
        return None, f"macd_fast ({raw_params['macd_fast']}) must be < macd_slow ({raw_params['macd_slow']})"
    
    # Extract params
    buy_n_levels = raw_params["buy_n_levels"]
    sell_n_levels = raw_params["sell_n_levels"]
    total_amount_quote = raw_params["total_amount_quote"]
    buy_side_weight = raw_params["buy_side_weight"]
    amount_skew = raw_params["amount_skew"]

    # Assert macd constraint
    if raw_params["macd_fast"] >= raw_params["macd_slow"]:
        return None, f"macd_fast ({raw_params['macd_fast']}) >= macd_slow ({raw_params['macd_slow']})"

    # Generate spread ladders
    buy_spreads = generate_geometric_ladder(
        raw_params["buy_spread_base"], raw_params["buy_spread_ratio"], buy_n_levels
    )
    sell_spreads = generate_geometric_ladder(
        raw_params["sell_spread_base"], raw_params["sell_spread_ratio"], sell_n_levels
    )

    # Verify spreads are positive and monotonically increasing
    for spreads, name in [(buy_spreads, "buy"), (sell_spreads, "sell")]:
        for i, s in enumerate(spreads):
            if s <= 0:
                return None, f"{name}_spread[{i}] = {s} is not positive"
        for i in range(1, len(spreads)):
            if spreads[i] <= spreads[i - 1]:
                return None, f"{name}_spreads not monotonically increasing at index {i}"

    # Check min_notional feasibility and reduce levels if needed
    buy_capital = buy_side_weight * total_amount_quote
    sell_capital = (1.0 - buy_side_weight) * total_amount_quote

    buy_weights = generate_amount_weights(buy_n_levels, amount_skew)
    sell_weights = generate_amount_weights(sell_n_levels, amount_skew)

    # Check feasibility for buy side
    feasible_buy = _check_side_feasibility(
        buy_n_levels, buy_capital, buy_weights, reference_price, pair_rules,
        amount_skew=amount_skew,
    )
    # Check feasibility for sell side
    feasible_sell = _check_side_feasibility(
        sell_n_levels, sell_capital, sell_weights, reference_price, pair_rules,
        amount_skew=amount_skew,
    )

    if feasible_buy == 0 and feasible_sell == 0:
        return None, (
            f"Both sides fail min_notional at reference_price={reference_price}, "
            f"total_amount_quote={total_amount_quote}"
        )

    # Trim to feasible levels
    if feasible_buy < buy_n_levels:
        buy_n_levels = feasible_buy
        buy_spreads = generate_geometric_ladder(
            raw_params["buy_spread_base"], raw_params["buy_spread_ratio"], buy_n_levels
        )
    if feasible_sell < sell_n_levels:
        sell_n_levels = feasible_sell
        sell_spreads = generate_geometric_ladder(
            raw_params["sell_spread_base"], raw_params["sell_spread_ratio"], sell_n_levels
        )

    # Regenerate amount weights for final level counts
    buy_amounts = generate_amount_weights(buy_n_levels, amount_skew)
    sell_amounts = generate_amount_weights(sell_n_levels, amount_skew)

    # Handle trailing stop: if activation == 0, disable delta too
    trailing_activation = raw_params["trailing_stop_activation"]
    trailing_delta = raw_params["trailing_stop_delta"]
    if trailing_activation == 0.0:
        trailing_delta = 0.0

    # Check for NaN in any float param
    float_fields = [
        total_amount_quote, buy_side_weight, amount_skew,
        raw_params["executor_refresh_time"], raw_params["cooldown_time"],
        raw_params["stop_loss"], raw_params["take_profit"],
        trailing_activation, trailing_delta,
        raw_params["buy_spread_base"], raw_params["sell_spread_base"],
    ]
    for val in float_fields + buy_spreads + sell_spreads + buy_amounts + sell_amounts:
        if np.isnan(val):
            return None, "NaN detected in parameters"

    config = SimConfig(
        buy_spreads=buy_spreads,
        sell_spreads=sell_spreads,
        buy_amounts_pct=buy_amounts,
        sell_amounts_pct=sell_amounts,
        buy_side_weight=buy_side_weight,
        total_amount_quote=total_amount_quote,
        executor_refresh_time=raw_params["executor_refresh_time"],
        cooldown_time=raw_params["cooldown_time"],
        stop_loss=raw_params["stop_loss"],
        take_profit=raw_params["take_profit"],
        time_limit=raw_params["time_limit"],
        take_profit_order_type="LIMIT",
        trailing_stop_activation=trailing_activation,
        trailing_stop_delta=trailing_delta,
        fill_participation_rate=0.1,
        latency_bars=1,
        slippage_bps=5.0,
        macd_fast=raw_params["macd_fast"],
        macd_slow=raw_params["macd_slow"],
        macd_signal=raw_params["macd_signal"],
        natr_length=raw_params["natr_length"],
        timestamp_mode="open",
    )

    return config, None
