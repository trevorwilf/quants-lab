"""EMA regime-hold Optuna search space.

Per D4: `hold_mode` is fixed at `"reentry"` — the `"hold"` variant requires a
regime-close engine hook that's out of scope for this MVP.

`cooldown_time` lower bound uses the SIGNAL interval, not the regime interval.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import optuna


def suggest_ema_regime_hold_params(
    trial: optuna.Trial,
    fixed_quote: Optional[float] = None,
    signal_interval_seconds: int = 300,
    regime_interval_seconds: int = 14400,
) -> Dict[str, Any]:
    """Sample raw EMA regime-hold hyperparameters for one Optuna trial.

    Parameters
    ----------
    trial : optuna.Trial
    fixed_quote : float, optional
    signal_interval_seconds : int
        Signal (fast) timeframe in seconds. Used for cooldown lower bound.
    regime_interval_seconds : int
        Regime (slow) timeframe in seconds. Currently informational only.
    """
    regime_ema_fast = trial.suggest_int("regime_ema_fast", 10, 100)
    regime_ema_slow = trial.suggest_int(
        "regime_ema_slow", max(50, regime_ema_fast + 1), 500
    )
    regime_adx_length = trial.suggest_int("regime_adx_length", 7, 30)
    regime_adx_threshold = trial.suggest_float("regime_adx_threshold", 10.0, 35.0)

    volume_filter_window = trial.suggest_int("volume_filter_window", 48, 576)
    min_volume_quantile = trial.suggest_float("min_volume_quantile", 0.0, 0.6)

    cooldown_lower = max(signal_interval_seconds * 2, 300)
    cooldown_time = trial.suggest_int("cooldown_time", cooldown_lower, 86400)

    stop_loss = trial.suggest_float("stop_loss", 0.02, 0.10, log=True)
    take_profit = trial.suggest_float("take_profit", 0.01, 0.10, log=True)
    time_limit = trial.suggest_int("time_limit", 3600, 604800)
    take_profit_order_type = trial.suggest_categorical(
        "take_profit_order_type", ["LIMIT", "MARKET"]
    )

    trailing_stop_activation = trial.suggest_float("trailing_stop_activation", 0.0, 0.05)
    trailing_stop_delta = trial.suggest_float("trailing_stop_delta", 0.0, 0.025)

    if fixed_quote is not None:
        total_amount_quote = fixed_quote
    else:
        total_amount_quote = trial.suggest_float("total_amount_quote", 25.0, 1000.0)

    # Fixed
    hold_mode = "reentry"  # D4
    max_executors_per_side = 1

    return {
        "regime_ema_fast": regime_ema_fast,
        "regime_ema_slow": regime_ema_slow,
        "regime_adx_length": regime_adx_length,
        "regime_adx_threshold": regime_adx_threshold,
        "volume_filter_window": volume_filter_window,
        "min_volume_quantile": min_volume_quantile,
        "hold_mode": hold_mode,
        "max_executors_per_side": max_executors_per_side,
        "cooldown_time": cooldown_time,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "time_limit": time_limit,
        "take_profit_order_type": take_profit_order_type,
        "trailing_stop_activation": trailing_stop_activation,
        "trailing_stop_delta": trailing_stop_delta,
        "total_amount_quote": total_amount_quote,
    }
