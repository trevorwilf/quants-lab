"""
Shared signal cache utilities.

Extracted from pmm_lab/optuna/sensitivity.py for reuse across the
stress-testing pipeline, notebook sweeps, and sensitivity analysis.

SharedSignalCache provides a cross-step cache keyed by
(signal_cache_key, dataset_key) so that signal computations can be
reused across pipeline steps (walk-forward, holdout, stress, sensitivity,
recent-window) without recomputation.
"""

import logging
from typing import Optional, Tuple

from pmm_lab.sim.executor_model import SimConfig

logger = logging.getLogger(__name__)


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


class SharedSignalCache:
    """Cross-step signal cache keyed by (signal_key, dataset_key).

    The dataset_key distinguishes different candle arrays (e.g., dev vs full)
    so that signals computed on one dataset are not incorrectly reused for
    another dataset with different length or content.

    Usage::

        cache = SharedSignalCache()
        sig_key = signal_cache_key(config)
        signals = cache.get(sig_key, "dev")
        if signals is None:
            signals = runner.compute_signals(dev_candles)
            cache.put(sig_key, "dev", signals)
    """

    def __init__(self):
        self._store: dict = {}

    def get(self, sig_key: tuple, dataset_key: str):
        """Retrieve cached signals, or None if not cached."""
        return self._store.get((sig_key, dataset_key))

    def put(self, sig_key: tuple, dataset_key: str, signals):
        """Store signals in the cache."""
        self._store[(sig_key, dataset_key)] = signals

    def get_or_compute(self, config: SimConfig, dataset_key: str,
                       candles, pair_rules) -> object:
        """Get cached signals or compute and cache them.

        Parameters
        ----------
        config : SimConfig
            Strategy configuration (used to derive the signal key).
        dataset_key : str
            Identifier for the candle dataset (e.g., "dev", "full").
        candles : np.ndarray
            Candle data to compute signals on (if not cached).
        pair_rules : PairRules
            Exchange rules for the runner.

        Returns
        -------
        signals
            The computed or cached signals array.
        """
        from pmm_lab.sim.runner import CandleSimRunner
        sig_key = signal_cache_key(config)
        cached = self.get(sig_key, dataset_key)
        if cached is not None:
            logger.debug("  Signal cache hit: %s / %s", sig_key, dataset_key)
            return cached
        logger.debug("  Signal cache miss: %s / %s — computing", sig_key, dataset_key)
        runner = CandleSimRunner(config, pair_rules)
        signals = runner.compute_signals(candles)
        self.put(sig_key, dataset_key, signals)
        return signals

    def __len__(self):
        return len(self._store)

    def clear(self):
        self._store.clear()
