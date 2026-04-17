"""EMA regime-hold parameter canonicalization.

Guards:
 - D4: hold_mode='hold' -> reject.
 - regime_ema_fast < regime_ema_slow (strict) or reject.
 - D19 slow-buffer: reject if max(regime_ema_slow, regime_adx_length) + 50 > 2950
   (the live controller hardcodes max_records=3000 for the slow feed).
 - D19 fast-buffer: reject if volume_filter_window + 50 > 5950
   (max_records=6000 for the fast feed).
 - regime_candles must be provided; if None, reject.
 - Trailing stop soft constraints.
 - Min notional at reference_price.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, Optional, Tuple

import numpy as np

from pmm_lab.config.exchange_rules import check_min_notional, round_amount
from pmm_lab.config.params import PairRules
from pmm_lab.optuna.candidate import CandidateBundle
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig


SLOW_BUFFER_MAX_RECORDS = 3000
FAST_BUFFER_MAX_RECORDS = 6000


def canonicalize_ema_regime_hold_params(
    raw_params: Dict[str, Any],
    pair_rules: PairRules,
    reference_price: float,
    signal_interval_seconds: int,
    regime_candles: Optional[np.ndarray] = None,
) -> Tuple[Optional[CandidateBundle], Optional[str]]:
    """Validate raw EMA params and build a CandidateBundle.

    Returns
    -------
    (CandidateBundle, None) on success
    (None, rejection_reason) on failure
    """
    if regime_candles is None:
        return None, "EMA canonicalizer requires regime_candles"

    regime_ema_fast = int(raw_params["regime_ema_fast"])
    regime_ema_slow = int(raw_params["regime_ema_slow"])
    regime_adx_length = int(raw_params["regime_adx_length"])
    regime_adx_threshold = float(raw_params["regime_adx_threshold"])
    volume_filter_window = int(raw_params["volume_filter_window"])
    min_volume_quantile = float(raw_params["min_volume_quantile"])
    hold_mode = str(raw_params.get("hold_mode", "reentry"))
    max_executors_per_side = int(raw_params.get("max_executors_per_side", 1))
    cooldown_time = int(raw_params["cooldown_time"])
    stop_loss = float(raw_params["stop_loss"])
    take_profit = float(raw_params["take_profit"])
    time_limit = int(raw_params["time_limit"])
    take_profit_order_type = str(raw_params["take_profit_order_type"])
    trailing_stop_activation = float(raw_params["trailing_stop_activation"])
    trailing_stop_delta = float(raw_params["trailing_stop_delta"])
    total_amount_quote = float(raw_params["total_amount_quote"])

    # --- Hard constraints ---
    if hold_mode != "reentry":
        return None, "hold_mode='hold' not supported in backtest (see D4)"
    if regime_ema_fast >= regime_ema_slow:
        return None, (
            f"regime_ema_fast ({regime_ema_fast}) >= regime_ema_slow ({regime_ema_slow})"
        )

    # --- D19: slow-buffer guard ---
    slow_need = max(regime_ema_slow, regime_adx_length) + 50
    if slow_need > SLOW_BUFFER_MAX_RECORDS - 50:
        return None, (
            f"regime_ema_slow ({regime_ema_slow}) + safety margin exceeds "
            f"controller's slow buffer ({SLOW_BUFFER_MAX_RECORDS})"
        )

    # --- D19: fast-buffer guard ---
    if volume_filter_window + 50 > FAST_BUFFER_MAX_RECORDS - 50:
        return None, (
            f"volume_filter_window ({volume_filter_window}) + safety margin exceeds "
            f"controller's fast buffer ({FAST_BUFFER_MAX_RECORDS})"
        )

    # --- Trailing stop ---
    if trailing_stop_activation == 0.0:
        trailing_stop_delta = 0.0
    elif trailing_stop_delta >= trailing_stop_activation:
        trailing_stop_delta = trailing_stop_activation * 0.5

    # --- Min notional ---
    capital_per_entry = total_amount_quote / max(1, max_executors_per_side)
    if reference_price > 0:
        base_amount = capital_per_entry / reference_price
        base_amount = round_amount(base_amount, pair_rules)
        if not check_min_notional(reference_price, base_amount, pair_rules):
            return None, (
                f"Min notional check failed: {reference_price:.6f} * {base_amount:.6f} = "
                f"{reference_price * base_amount:.6f} < {pair_rules.min_notional_quote}"
            )

    # --- Build configs ---
    base_strategy_cfg = EMARegimeHoldStrategyConfig(
        regime_ema_fast=regime_ema_fast,
        regime_ema_slow=regime_ema_slow,
        regime_adx_length=regime_adx_length,
        regime_adx_threshold=regime_adx_threshold,
        volume_filter_window=volume_filter_window,
        min_volume_quantile=min_volume_quantile,
        hold_mode=hold_mode,
        max_executors_per_side=max_executors_per_side,
    )
    # Wire the regime candles via dataclasses.replace
    strategy_config = replace(base_strategy_cfg, _regime_candles=regime_candles)

    engine_config = EngineConfig(
        total_amount_quote=total_amount_quote,
        executor_refresh_time=float(signal_interval_seconds),  # D7
        cooldown_time=float(cooldown_time),
        stop_loss=stop_loss,
        take_profit=take_profit,
        time_limit=time_limit,
        take_profit_order_type=take_profit_order_type,
        trailing_stop_activation=trailing_stop_activation,
        trailing_stop_delta=trailing_stop_delta,
        latency_bars=1,  # D6
    )

    bundle = CandidateBundle(
        strategy_name="ema_regime_hold",
        strategy_config=strategy_config,
        engine_config=engine_config,
        export_meta={
            "controller_name": "ema_regime_hold_v1",
            "controller_type": "directional_trading",
        },
    )
    return bundle, None
