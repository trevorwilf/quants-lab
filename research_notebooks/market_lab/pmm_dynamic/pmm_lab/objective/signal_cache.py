"""
Shared signal cache utilities.

Extracted from pmm_lab/optuna/sensitivity.py for reuse across the
stress-testing pipeline, notebook sweeps, and sensitivity analysis.
"""

from pmm_lab.sim.executor_model import SimConfig


def signal_cache_key(cfg: SimConfig) -> tuple:
    """Cache key covering all feature-affecting config fields.

    Trade execution parameters (spreads, stop-loss, fill model, etc.)
    do NOT affect signal computation, so they are excluded from the key.
    """
    return (
        cfg.macd_fast,
        cfg.macd_slow,
        cfg.macd_signal,
        cfg.natr_length,
        cfg.controller_compat,
        cfg.timestamp_mode,
    )


# Fields that compose the signal cache key — useful for tests
SIGNAL_AFFECTING_FIELDS = (
    "macd_fast", "macd_slow", "macd_signal",
    "natr_length", "controller_compat", "timestamp_mode",
)
