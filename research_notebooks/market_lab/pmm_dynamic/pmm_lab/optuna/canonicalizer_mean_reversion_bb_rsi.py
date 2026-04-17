"""MR BB+RSI parameter canonicalization.

Validates raw params and produces a CandidateBundle.

Guards:
 - D17: clamp `min_trend_slope` to 0.0 (log a warning if non-zero was passed).
 - D18: reject if `volume_filter_window + 50 > required_records`. The live
   controller's `required_records` omits `volume_filter_window`; a config
   where the rolling quantile cannot warm up inside the controller's candle
   buffer would silently always pass `volume_ok=True` at live runtime.
 - Trailing: zero-activation → zero delta; delta >= activation → clamp to half.
 - Min notional at reference_price.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from pmm_lab.config.exchange_rules import check_min_notional, round_amount
from pmm_lab.config.params import PairRules
from pmm_lab.optuna.candidate import CandidateBundle
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.strategies.mean_reversion_bb_rsi import MeanReversionBBRSIStrategyConfig

logger = logging.getLogger(__name__)


def canonicalize_mr_bb_rsi_params(
    raw_params: Dict[str, Any],
    pair_rules: PairRules,
    reference_price: float,
    bar_interval_seconds: int = 300,
) -> Tuple[Optional[CandidateBundle], Optional[str]]:
    """Validate raw MR params and build a CandidateBundle.

    Returns
    -------
    (CandidateBundle, None) on success
    (None, rejection_reason) on failure
    """
    bb_length = raw_params["bb_length"]
    bb_std = raw_params["bb_std"]
    bbp_entry_threshold = raw_params["bbp_entry_threshold"]
    rsi_length = raw_params["rsi_length"]
    rsi_entry_threshold = raw_params["rsi_entry_threshold"]
    use_trend_filter = raw_params["use_trend_filter"]
    trend_ema_length = raw_params["trend_ema_length"]
    raw_min_slope = raw_params.get("min_trend_slope", 0.0)
    atr_length = raw_params["atr_length"]
    max_atr_pct_for_entry = raw_params["max_atr_pct_for_entry"]
    volume_filter_window = raw_params["volume_filter_window"]
    min_volume_quantile = raw_params["min_volume_quantile"]
    max_spread_pct = raw_params.get("max_spread_pct", 0.006)
    max_trades_per_day = raw_params.get("max_trades_per_day", 6)
    max_executors_per_side = raw_params.get("max_executors_per_side", 1)
    cooldown_time = int(raw_params["cooldown_time"])
    stop_loss = raw_params["stop_loss"]
    take_profit = raw_params["take_profit"]
    time_limit = int(raw_params["time_limit"])
    take_profit_order_type = raw_params["take_profit_order_type"]
    trailing_stop_activation = raw_params["trailing_stop_activation"]
    trailing_stop_delta = raw_params["trailing_stop_delta"]
    total_amount_quote = raw_params["total_amount_quote"]

    # --- D17: clamp min_trend_slope to 0.0 with warning ---
    if raw_min_slope != 0.0:
        logger.warning(
            "MR canonicalizer: min_trend_slope=%.6f clamped to 0.0 (D17 — raw "
            "slope is in price units and isn't portable across pairs)",
            float(raw_min_slope),
        )
    min_trend_slope = 0.0

    # --- D18: volume_filter_window warmup guard ---
    required_records = max(bb_length, trend_ema_length, rsi_length, atr_length) + 500
    if volume_filter_window + 50 > required_records:
        return None, (
            f"volume_filter_window ({volume_filter_window}) exceeds controller's "
            f"required_records buffer ({required_records}) — rolling quantile would "
            f"never warm up at live runtime"
        )

    # --- Trailing stop soft constraints ---
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
    strategy_config = MeanReversionBBRSIStrategyConfig(
        bb_length=int(bb_length),
        bb_std=float(bb_std),
        bbp_entry_threshold=float(bbp_entry_threshold),
        rsi_length=int(rsi_length),
        rsi_entry_threshold=float(rsi_entry_threshold),
        use_trend_filter=bool(use_trend_filter),
        trend_ema_length=int(trend_ema_length),
        min_trend_slope=float(min_trend_slope),
        atr_length=int(atr_length),
        max_atr_pct_for_entry=float(max_atr_pct_for_entry),
        volume_filter_window=int(volume_filter_window),
        min_volume_quantile=float(min_volume_quantile),
        max_spread_pct=float(max_spread_pct),
        max_trades_per_day=int(max_trades_per_day),
        max_executors_per_side=int(max_executors_per_side),
    )

    engine_config = EngineConfig(
        total_amount_quote=float(total_amount_quote),
        executor_refresh_time=float(bar_interval_seconds),  # D7
        cooldown_time=float(cooldown_time),
        stop_loss=float(stop_loss),
        take_profit=float(take_profit),
        time_limit=int(time_limit),
        take_profit_order_type=str(take_profit_order_type),
        trailing_stop_activation=float(trailing_stop_activation),
        trailing_stop_delta=float(trailing_stop_delta),
        latency_bars=1,  # D6
    )

    bundle = CandidateBundle(
        strategy_name="mean_reversion_bb_rsi",
        strategy_config=strategy_config,
        engine_config=engine_config,
        export_meta={
            "controller_name": "mean_reversion_bb_rsi_v1",
            "controller_type": "directional_trading",
        },
    )
    return bundle, None
