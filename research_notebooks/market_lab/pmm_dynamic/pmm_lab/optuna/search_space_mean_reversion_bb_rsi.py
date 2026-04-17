"""MR BB+RSI Optuna search space.

Per D17: `min_trend_slope` is fixed at 0.0 and NOT sampled. The canonicalizer
still threads it through the YAML export.

Per D3: `max_trades_per_day` is a live-safety cap, NOT tuned. Held at the
YAML default (6) during optimization.

Per D2: `max_spread_pct` is live-only; not enforced in backtest but exported
at the controller's default (0.006).

`cooldown_time` lower bound is `max(bar_interval_seconds * 2, 300)` to avoid
multi-trade-per-bar drift (MACD-BB bug avoided per Appendix C).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import optuna


def suggest_mr_bb_rsi_params(
    trial: optuna.Trial,
    fixed_quote: Optional[float] = None,
    bar_interval_seconds: int = 300,
) -> Dict[str, Any]:
    """Sample raw MR BB+RSI hyperparameters for one Optuna trial.

    Parameters
    ----------
    trial : optuna.Trial
    fixed_quote : float, optional
        If set, `total_amount_quote` is fixed (not sampled).
    bar_interval_seconds : int
        Used to set the `cooldown_time` lower bound.

    Returns
    -------
    dict
        Raw params suitable for `canonicalize_mr_bb_rsi_params`.
    """
    bb_length = trial.suggest_int("bb_length", 20, 200)
    bb_std = trial.suggest_float("bb_std", 1.0, 3.0)
    bbp_entry_threshold = trial.suggest_float("bbp_entry_threshold", 0.05, 0.40)
    rsi_length = trial.suggest_int("rsi_length", 7, 30)
    rsi_entry_threshold = trial.suggest_float("rsi_entry_threshold", 20.0, 50.0)
    use_trend_filter = trial.suggest_categorical("use_trend_filter", [True, False])
    trend_ema_length = trial.suggest_int("trend_ema_length", 50, 400)
    atr_length = trial.suggest_int("atr_length", 7, 30)
    max_atr_pct_for_entry = trial.suggest_float(
        "max_atr_pct_for_entry", 0.005, 0.10, log=True
    )
    volume_filter_window = trial.suggest_int("volume_filter_window", 48, 576)
    min_volume_quantile = trial.suggest_float("min_volume_quantile", 0.0, 0.6)

    cooldown_lower = max(bar_interval_seconds * 2, 300)
    cooldown_time = trial.suggest_int("cooldown_time", cooldown_lower, 86400)

    stop_loss = trial.suggest_float("stop_loss", 0.015, 0.08, log=True)
    take_profit = trial.suggest_float("take_profit", 0.005, 0.06, log=True)
    time_limit = trial.suggest_int("time_limit", 3600, 345600)
    take_profit_order_type = trial.suggest_categorical(
        "take_profit_order_type", ["LIMIT", "MARKET"]
    )

    trailing_stop_activation = trial.suggest_float("trailing_stop_activation", 0.0, 0.04)
    trailing_stop_delta = trial.suggest_float("trailing_stop_delta", 0.0, 0.02)

    if fixed_quote is not None:
        total_amount_quote = fixed_quote
    else:
        total_amount_quote = trial.suggest_float("total_amount_quote", 25.0, 1000.0)

    # Fixed per design decisions — still returned for canonicalizer + export
    min_trend_slope = 0.0      # D17
    max_spread_pct = 0.006     # D2
    max_trades_per_day = 6     # D3
    max_executors_per_side = 1

    return {
        "bb_length": bb_length,
        "bb_std": bb_std,
        "bbp_entry_threshold": bbp_entry_threshold,
        "rsi_length": rsi_length,
        "rsi_entry_threshold": rsi_entry_threshold,
        "use_trend_filter": use_trend_filter,
        "trend_ema_length": trend_ema_length,
        "min_trend_slope": min_trend_slope,
        "atr_length": atr_length,
        "max_atr_pct_for_entry": max_atr_pct_for_entry,
        "volume_filter_window": volume_filter_window,
        "min_volume_quantile": min_volume_quantile,
        "max_spread_pct": max_spread_pct,
        "max_trades_per_day": max_trades_per_day,
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
