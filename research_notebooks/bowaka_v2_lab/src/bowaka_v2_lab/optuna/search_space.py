"""Optuna search space.

Per [Report §14.2] verbatim. The ranges are **research priors** — they have not
been validated against out-of-sample data; broadening or narrowing them
without methodology evidence is reasonable.
"""
from __future__ import annotations

from typing import Any


# Authoritative spec used by both the suggestion routine and the priors test.
SEARCH_SPACE_SPEC: dict[str, tuple] = {
    # (suggest_kind, args...)
    "signals.rvol_so_far_min":            ("uniform", 1.0, 5.0),
    "signals.projected_full_day_rvol_min": ("uniform", 1.0, 5.0),
    "signals.range_expansion_so_far_min": ("uniform", 1.0, 3.5),
    "signals.close_location_so_far_min":  ("uniform", 0.3, 0.95),
    "signals.ema_distance_min":           ("uniform", -0.05, 0.30),
    "signals.ema_slope_min":              ("uniform", -0.02, 0.10),
    "signals.gap_pct_max":                ("uniform", 0.02, 0.50),
    "signals.rvol_so_far_max":            ("uniform", 5.0, 20.0),
    "signals.range_expansion_so_far_max": ("uniform", 3.0, 10.0),
    "exits.stop_loss_pct":                ("uniform", 0.005, 0.05),
    "exits.take_profit_pct":              ("uniform", 0.02, 0.20),
    "exits.max_hold_days":                ("int",     1, 10),
    "sizing.dollars_per_position":        ("int",     500, 10_000),
}


def suggest_params(trial: "object") -> dict[str, Any]:
    """Use the Optuna trial API to suggest a parameter set per ``SEARCH_SPACE_SPEC``."""
    out: dict[str, Any] = {}
    for name, spec in SEARCH_SPACE_SPEC.items():
        kind = spec[0]
        if kind == "uniform":
            out[name] = trial.suggest_float(name, spec[1], spec[2])
        elif kind == "int":
            out[name] = trial.suggest_int(name, spec[1], spec[2])
        elif kind == "log_uniform":
            out[name] = trial.suggest_float(name, spec[1], spec[2], log=True)
        else:
            raise ValueError(f"unknown suggest kind {kind!r}")
    return out
