"""Bowaka Optuna search space (per [Report §19.2]).

The space honors ``None`` choices for nullable maxes (rvol_max, range_max,
gap_pct_max) so a trial can decide to disable the cap entirely.
"""

from __future__ import annotations

from typing import Any


_NULLABLE_MAX_DEFAULTS = {
    "rvol_max": [None, 5.0, 8.0, 12.0],
    "range_expansion_max": [None, 3.0, 4.0, 5.0],
    "gap_pct_max": [None, 0.20, 0.30, 0.40],
}


def suggest_params(trial: Any) -> dict[str, Any]:
    """Suggest a Bowaka parameter set using an Optuna ``Trial`` object."""
    params: dict[str, Any] = {}

    params["rvol_min"] = trial.suggest_float("rvol_min", 1.2, 5.0)
    params["atr_pct_min"] = trial.suggest_float("atr_pct_min", 0.03, 0.15)
    params["range_expansion_min"] = trial.suggest_float("range_expansion_min", 1.0, 4.0)
    params["close_location_min"] = trial.suggest_float("close_location_min", 0.50, 0.90)
    params["ema_distance_min"] = trial.suggest_float("ema_distance_min", -0.03, 0.10)
    params["ema_slope_min"] = trial.suggest_float("ema_slope_min", -0.02, 0.05)

    for key, choices in _NULLABLE_MAX_DEFAULTS.items():
        choice_str = trial.suggest_categorical(key, [str(c) for c in choices])
        params[key] = None if choice_str == "None" else float(choice_str)

    params["entry_rule"] = trial.suggest_categorical(
        "entry_rule",
        ["fixed_time_0935", "fixed_time_0945", "fixed_time_1000", "or_breakout_15m", "vwap_reclaim"],
    )
    params["stop_pct"] = trial.suggest_float("stop_pct", 0.05, 0.12)
    params["target_pct"] = trial.suggest_float("target_pct", 0.08, 0.25)
    params["max_hold_days"] = trial.suggest_int("max_hold_days", 1, 4)

    fade_choices = ["None", "6", "7", "8", "9"]
    sf = trial.suggest_categorical("signal_fade_threshold", fade_choices)
    params["signal_fade_threshold"] = None if sf == "None" else int(sf)
    return params
