"""
Search space definition for PMM Dynamic Optuna optimization.

Uses geometric spread ladders (base + ratio) instead of 10 independent
variables per side, giving the TPE sampler a smoother landscape.

v2: Widened ranges for thorough 3000-trial exploration.
"""

import optuna
from typing import Dict, Any


def suggest_params(trial: optuna.Trial) -> Dict[str, Any]:
    """Suggest a full set of PMM Dynamic parameters from an Optuna trial.

    Returns a flat dict of raw parameter values. These must be passed through
    canonicalize_params() before constructing a SimConfig.
    """
    # Indicator parameters
    macd_fast = trial.suggest_int("macd_fast", 5, 50)
    #macd_slow = trial.suggest_int("macd_slow", macd_fast + 5, 100)
    macd_slow = trial.suggest_int("macd_slow", 20, 100)
    macd_signal = trial.suggest_int("macd_signal", 5, 30)
    natr_length = trial.suggest_int("natr_length", 7, 50)

    # Level counts
    buy_n_levels = trial.suggest_int("buy_n_levels", 2, 10)
    sell_n_levels = trial.suggest_int("sell_n_levels", 2, 10)

    # Spread ladders (geometric)
    buy_spread_base = trial.suggest_float("buy_spread_base", 0.2, 6.0)
    buy_spread_ratio = trial.suggest_float("buy_spread_ratio", 1.2, 3.0)
    
    sell_spread_base = trial.suggest_float("sell_spread_base", 0.2, 6.0)     # was 70.0
    sell_spread_ratio = trial.suggest_float("sell_spread_ratio", 1.2, 3.0)   # was 30.0

    # Amount allocation
    buy_side_weight = trial.suggest_float("buy_side_weight", 0.2, 0.8)
    amount_skew = trial.suggest_float("amount_skew", 1.0, 4.0)

    # Capital allocation — optimized
    total_amount_quote = trial.suggest_float("total_amount_quote", 25.0, 1000.0)

    # Timing — widened
    executor_refresh_time = trial.suggest_float("executor_refresh_time", 300.0, 14400.0)
    cooldown_time = trial.suggest_float("cooldown_time", 60.0, 7200.0)

    # Triple barrier — widened
    stop_loss = trial.suggest_float("stop_loss", 0.01, 0.25)
    take_profit = trial.suggest_float("take_profit", 0.005, 0.15)
    time_limit = trial.suggest_int("time_limit", 3600, 172800)
    trailing_stop_activation = trial.suggest_float("trailing_stop_activation", 0.0, 0.10)
    trailing_stop_delta = trial.suggest_float("trailing_stop_delta", 0.001, 0.05)

    return {
        "macd_fast": macd_fast,
        "macd_slow": macd_slow,
        "macd_signal": macd_signal,
        "natr_length": natr_length,
        "buy_n_levels": buy_n_levels,
        "sell_n_levels": sell_n_levels,
        "buy_spread_base": buy_spread_base,
        "buy_spread_ratio": buy_spread_ratio,
        "sell_spread_base": sell_spread_base,
        "sell_spread_ratio": sell_spread_ratio,
        "buy_side_weight": buy_side_weight,
        "amount_skew": amount_skew,
        "total_amount_quote": total_amount_quote,
        "executor_refresh_time": executor_refresh_time,
        "cooldown_time": cooldown_time,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "time_limit": time_limit,
        "trailing_stop_activation": trailing_stop_activation,
        "trailing_stop_delta": trailing_stop_delta,
    }
