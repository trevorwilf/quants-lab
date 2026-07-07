"""range_ladder Optuna search space — the 10-param generative description.

Raw rung prices and raw weight vectors are NEVER exposed to Optuna. Every
sample is a fixed-dimension generative ladder description; the canonicalizer
turns it into a concrete (validated) ladder per fold.

`fund_quote` (the deployed fund) is NOT tuned — it comes from the notebook's
FUND_USD parameter via `fixed_quote`. Timing parameters are frozen at live
values in Phase A (`cooldown_time` 3600 s; `executor_refresh_time` is not
modeled — Phase B).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import optuna

# Frozen Phase A live timing values (seconds)
PHASE_A_COOLDOWN_SECONDS = 3600
PHASE_A_EXECUTOR_REFRESH_SECONDS = 43200

DEFAULT_FUND_QUOTE = 1000.0


def suggest_range_ladder_params(
    trial: optuna.Trial,
    fixed_quote: Optional[float] = None,
    bar_interval_seconds: int = 3600,
) -> Dict[str, Any]:
    """Sample raw range_ladder hyperparameters for one Optuna trial.

    Parameters
    ----------
    trial : optuna.Trial
    fixed_quote : float, optional
        Deployed fund in quote units (notebook FUND_USD). Not sampled.
    bar_interval_seconds : int
        Study bar interval; converts the frozen cooldown to bars.

    Returns
    -------
    dict
        Raw params for `canonicalize_range_ladder_params`.
    """
    n_buy = trial.suggest_int("n_buy", 3, 10)
    n_sell = trial.suggest_int("n_sell", 3, 10)
    buy_near_pct = trial.suggest_float("buy_near_pct", 0.005, 0.10, log=True)
    buy_far_pct = trial.suggest_float("buy_far_pct", 0.03, 0.45, log=True)
    sell_near_pct = trial.suggest_float("sell_near_pct", 0.005, 0.10, log=True)
    sell_far_pct = trial.suggest_float("sell_far_pct", 0.03, 0.45, log=True)
    buy_gamma = trial.suggest_float("buy_gamma", 0.5, 2.0)
    sell_gamma = trial.suggest_float("sell_gamma", 0.5, 2.0)
    k_buy = trial.suggest_float("k_buy", -2.0, 4.0)
    k_sell = trial.suggest_float("k_sell", -2.0, 4.0)

    fund_quote = fixed_quote if fixed_quote is not None else DEFAULT_FUND_QUOTE

    return {
        "n_buy": n_buy,
        "n_sell": n_sell,
        "buy_near_pct": buy_near_pct,
        "buy_far_pct": buy_far_pct,
        "sell_near_pct": sell_near_pct,
        "sell_far_pct": sell_far_pct,
        "buy_gamma": buy_gamma,
        "sell_gamma": sell_gamma,
        "k_buy": k_buy,
        "k_sell": k_sell,
        # Fixed (not sampled) — threaded through canonicalizer + export
        "fund_quote": fund_quote,
        "quote_frac": 0.5,
        "cooldown_time": PHASE_A_COOLDOWN_SECONDS,
        "executor_refresh_time": PHASE_A_EXECUTOR_REFRESH_SECONDS,
    }
