"""
MACD-BB parameter canonicalization.

Validates raw sampled parameters and produces a CandidateBundle
for the MACD-BB directional trading strategy.
"""

from typing import Dict, Any, Tuple, Optional

from pmm_lab.config.params import PairRules
from pmm_lab.config.exchange_rules import round_amount, check_min_notional
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.strategies.macd_bb import MACDBBStrategyConfig
from pmm_lab.optuna.candidate import CandidateBundle


def canonicalize_macd_bb_params(
    raw_params: Dict[str, Any],
    pair_rules: PairRules,
    reference_price: float,
    bar_interval_seconds: int = 300,
) -> Tuple[Optional[CandidateBundle], Optional[str]]:
    """Validate and canonicalize raw MACD-BB params into a CandidateBundle.

    Parameters
    ----------
    raw_params : dict
        Raw params from suggest_macd_bb_params().
    pair_rules : PairRules
        Exchange rules for the target pair.
    reference_price : float
        Current reference price for notional checks.
    bar_interval_seconds : int
        Candle bar interval in seconds. Used to set executor_refresh_time
        so the engine evaluates every bar (directional signals are ephemeral).

    Returns
    -------
    (CandidateBundle, None) on success
    (None, rejection_reason) on failure
    """
    macd_fast = raw_params["macd_fast"]
    macd_slow = raw_params["macd_slow"]
    macd_signal = raw_params["macd_signal"]
    bb_length = raw_params["bb_length"]
    bb_std = raw_params["bb_std"]
    bb_long_threshold = raw_params["bb_long_threshold"]
    bb_short_threshold = raw_params["bb_short_threshold"]
    max_executors_per_side = raw_params.get("max_executors_per_side", 1)
    cooldown_time = raw_params["cooldown_time"]
    stop_loss = raw_params["stop_loss"]
    take_profit = raw_params["take_profit"]
    time_limit = raw_params["time_limit"]
    take_profit_order_type = raw_params["take_profit_order_type"]
    trailing_stop_activation = raw_params["trailing_stop_activation"]
    trailing_stop_delta = raw_params["trailing_stop_delta"]
    total_amount_quote = raw_params["total_amount_quote"]

    # --- Hard constraints ---

    # macd_fast must be < macd_slow
    if macd_fast >= macd_slow:
        return None, f"macd_fast ({macd_fast}) >= macd_slow ({macd_slow})"

    # bb_long_threshold must be < bb_short_threshold
    if bb_long_threshold >= bb_short_threshold:
        return None, (
            f"bb_long_threshold ({bb_long_threshold}) >= "
            f"bb_short_threshold ({bb_short_threshold})"
        )

    # --- Trailing stop constraints ---
    if trailing_stop_activation == 0.0:
        trailing_stop_delta = 0.0
    elif trailing_stop_delta >= trailing_stop_activation:
        trailing_stop_delta = trailing_stop_activation * 0.5

    # --- Min notional check ---
    capital_per_entry = total_amount_quote / max_executors_per_side
    if reference_price > 0:
        base_amount = capital_per_entry / reference_price
        base_amount = round_amount(base_amount, pair_rules)
        if not check_min_notional(reference_price, base_amount, pair_rules):
            return None, (
                f"Min notional check failed: "
                f"{reference_price} * {base_amount} = {reference_price * base_amount} "
                f"< {pair_rules.min_notional_quote}"
            )

    # --- Build configs ---
    strategy_config = MACDBBStrategyConfig(
        bb_length=bb_length,
        bb_std=bb_std,
        bb_long_threshold=bb_long_threshold,
        bb_short_threshold=bb_short_threshold,
        macd_fast=macd_fast,
        macd_slow=macd_slow,
        macd_signal=macd_signal,
        max_executors_per_side=max_executors_per_side,
    )

    engine_config = EngineConfig(
        total_amount_quote=total_amount_quote,
        executor_refresh_time=float(bar_interval_seconds),  # directional: check every bar
        cooldown_time=float(cooldown_time),
        stop_loss=stop_loss,
        take_profit=take_profit,
        time_limit=time_limit,
        take_profit_order_type=take_profit_order_type,
        trailing_stop_activation=trailing_stop_activation,
        trailing_stop_delta=trailing_stop_delta,
    )

    bundle = CandidateBundle(
        strategy_name="macd_bb",
        strategy_config=strategy_config,
        engine_config=engine_config,
        export_meta={
            "controller_name": "macd_bb_v1",
            "controller_type": "directional_trading",
        },
    )

    return bundle, None
