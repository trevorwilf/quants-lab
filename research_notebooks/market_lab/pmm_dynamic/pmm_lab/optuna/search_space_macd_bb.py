"""
MACD-BB Optuna search space.

Defines the hyperparameter sampling for MACD+BB directional trading strategy.
"""

import optuna
from typing import Dict, Any, Optional


def suggest_macd_bb_params(
    trial: optuna.Trial,
    fixed_quote: Optional[float] = None,
) -> Dict[str, Any]:
    """Suggest MACD-BB hyperparameters for one Optuna trial.

    Parameters
    ----------
    trial : optuna.Trial
        Optuna trial object.
    fixed_quote : float, optional
        If set, total_amount_quote is fixed to this value (not optimized).

    Returns
    -------
    dict
        Raw sampled parameters for canonicalization.
    """
    # Bollinger Bands
    bb_length = trial.suggest_int("bb_length", 10, 200)
    bb_std = trial.suggest_float("bb_std", 0.5, 3.0)
    bb_long_threshold = trial.suggest_float("bb_long_threshold", -0.5, 0.5)
    bb_short_threshold = trial.suggest_float("bb_short_threshold", 0.5, 1.5)

    # MACD
    macd_slow = trial.suggest_int("macd_slow", 20, 200)
    macd_fast = trial.suggest_int("macd_fast", 5, min(49, macd_slow - 1))
    macd_signal = trial.suggest_int("macd_signal", 5, 30)

    # Execution — MVP: max_executors_per_side = 1
    max_executors_per_side = 1

    # Timing
    cooldown_time = trial.suggest_int("cooldown_time", 60, 14400)

    # Triple barrier
    stop_loss = trial.suggest_float("stop_loss", 0.01, 0.10, log=True)
    take_profit = trial.suggest_float("take_profit", 0.01, 0.15, log=True)
    time_limit = trial.suggest_int("time_limit", 3600, 259200)
    take_profit_order_type = trial.suggest_categorical(
        "take_profit_order_type", ["LIMIT", "MARKET"]
    )

    # Trailing stop
    trailing_stop_activation = trial.suggest_float("trailing_stop_activation", 0.0, 0.05)
    trailing_stop_delta = trial.suggest_float("trailing_stop_delta", 0.0, 0.03)

    # Capital
    if fixed_quote is not None:
        total_amount_quote = fixed_quote
    else:
        total_amount_quote = trial.suggest_float("total_amount_quote", 25.0, 1000.0)

    return {
        "bb_length": bb_length,
        "bb_std": bb_std,
        "bb_long_threshold": bb_long_threshold,
        "bb_short_threshold": bb_short_threshold,
        "macd_fast": macd_fast,
        "macd_slow": macd_slow,
        "macd_signal": macd_signal,
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
