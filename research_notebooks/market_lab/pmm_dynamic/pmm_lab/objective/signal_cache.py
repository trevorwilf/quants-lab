"""
Shared signal cache utilities.

Extracted from pmm_lab/optuna/sensitivity.py for reuse across the
stress-testing pipeline, notebook sweeps, and sensitivity analysis.

SharedSignalCache provides a cross-step cache keyed by
(signal_cache_key, dataset_key) so that signal computations can be
reused across pipeline steps (walk-forward, holdout, stress, sensitivity,
recent-window) without recomputation.

Dispatch by config type is used to support multiple strategy families:
PMM Dynamic (SimConfig), MACD-BB (SimConfig), MR BB+RSI, EMA regime-hold.
New strategies are added by extending `signal_cache_key` and
`SharedSignalCache.get_or_compute` with a new branch.
"""

import importlib.util
import logging
from typing import Any, Optional, Tuple

logger = logging.getLogger(__name__)


def _module_is_installable(module_name: str) -> bool:
    """Return True if the module's top-level package is findable.

    Returns False ONLY when the module itself is missing — NOT when the module
    is present but raises ImportError due to a transitive dependency. This lets
    us distinguish "feature absent" (legitimate skip) from "feature broken"
    (re-raise so the operator sees the real problem).
    """
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except (ImportError, ValueError):
        return False


def signal_cache_key(cfg: Any) -> tuple:
    """Cache key covering all feature-affecting config fields.

    Dispatches by config type. Execution parameters (spreads, stop-loss,
    fill model, etc.) do NOT affect signal computation, so they are
    excluded from the key. A type-tag string is the first tuple element
    so keys from different strategies never collide.
    """
    from pmm_lab.sim.executor_model import SimConfig

    if isinstance(cfg, SimConfig):
        # Existing PMM / MACD-BB branch — do NOT modify (backward-compat)
        return (
            cfg.macd_fast,
            cfg.macd_slow,
            cfg.macd_signal,
            cfg.natr_length,
            cfg.controller_compat,
            cfg.timestamp_mode,
        )

    if _module_is_installable("pmm_lab.strategies.mean_reversion_bb_rsi"):
        try:
            from pmm_lab.strategies.mean_reversion_bb_rsi import MeanReversionBBRSIStrategyConfig
        except ImportError as e:
            raise ImportError(
                f"Directional MR module failed to import transitively: {e}"
            ) from e
        if isinstance(cfg, MeanReversionBBRSIStrategyConfig):
            return (
                "mr_bb_rsi",
                cfg.bb_length, cfg.bb_std, cfg.bbp_entry_threshold,
                cfg.rsi_length, cfg.rsi_entry_threshold,
                cfg.use_trend_filter, cfg.trend_ema_length, cfg.min_trend_slope,
                cfg.atr_length, cfg.max_atr_pct_for_entry,
                cfg.volume_filter_window, cfg.min_volume_quantile,
                cfg.timestamp_mode, cfg.controller_compat,
            )

    if _module_is_installable("pmm_lab.strategies.ema_regime_hold"):
        try:
            from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig
        except ImportError as e:
            raise ImportError(
                f"Directional EMA module failed to import transitively: {e}"
            ) from e
        if isinstance(cfg, EMARegimeHoldStrategyConfig):
            return (
                "ema_regime_hold",
                cfg.regime_ema_fast, cfg.regime_ema_slow,
                cfg.regime_adx_length, cfg.regime_adx_threshold,
                cfg.volume_filter_window, cfg.min_volume_quantile,
                cfg.hold_mode,
                cfg.timestamp_mode, cfg.controller_compat,
            )

    raise TypeError(
        f"signal_cache_key: unsupported config type {type(cfg).__name__}. "
        f"Add a branch for this type."
    )


# Fields that compose the signal cache key for SimConfig — useful for tests
SIGNAL_AFFECTING_FIELDS = (
    "macd_fast", "macd_slow", "macd_signal",
    "natr_length", "controller_compat", "timestamp_mode",
)


def _dataset_key_for(config, dataset_key: str, regime_candles) -> str:
    """Compose a dataset key that includes regime identity for EMA configs.

    For EMA, signals depend on BOTH the signal-timeframe candles AND the
    regime-timeframe candles. A `dataset_key` of "dev" alone would collide
    across runs with different regime data. This helper adds a short regime
    hash suffix so the cache distinguishes them.

    Non-EMA configs (SimConfig, MR) pass through unchanged.
    """
    if _module_is_installable("pmm_lab.strategies.ema_regime_hold"):
        try:
            from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig
        except ImportError as e:
            raise ImportError(
                f"Directional EMA module failed to import transitively: {e}"
            ) from e
        if isinstance(config, EMARegimeHoldStrategyConfig) and regime_candles is not None:
            from pmm_lab.data.hashing import hash_candles as _hc
            return f"{dataset_key}#regime={_hc(regime_candles)[:16]}"
    return dataset_key


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

    def get_or_compute(
        self,
        config: Any,
        dataset_key: str,
        candles,
        pair_rules,
        regime_candles=None,
    ) -> object:
        """Get cached signals or compute and cache them.

        Parameters
        ----------
        config : SimConfig | MeanReversionBBRSIStrategyConfig | EMARegimeHoldStrategyConfig
            Strategy configuration (used to derive the signal key and dispatch
            signal computation).
        dataset_key : str
            Identifier for the candle dataset (e.g., "dev", "full").
        candles : np.ndarray
            Candle data to compute signals on (if not cached).
        pair_rules : PairRules
            Exchange rules. Used by PMM/MACD-BB runner; ignored for MR/EMA.
        regime_candles : np.ndarray, optional
            Required when config is EMARegimeHoldStrategyConfig. Ignored otherwise.

        Returns
        -------
        signals
            The computed or cached signals (SignalOutput or equivalent).
        """
        # Regime-aware dataset key (ML-DIR-002): EMA configs get a key that
        # distinguishes different regime candles. Non-EMA passes through.
        effective_key = _dataset_key_for(config, dataset_key, regime_candles)
        sig_key = signal_cache_key(config)
        cached = self.get(sig_key, effective_key)
        if cached is not None:
            logger.debug("  Signal cache hit: %s / %s", sig_key, effective_key)
            return cached
        logger.debug("  Signal cache miss: %s / %s — computing", sig_key, effective_key)

        from pmm_lab.sim.executor_model import SimConfig
        if isinstance(config, SimConfig):
            from pmm_lab.sim.runner import CandleSimRunner
            runner = CandleSimRunner(config, pair_rules)
            signals = runner.compute_signals(candles)
            self.put(sig_key, effective_key, signals)
            return signals

        if _module_is_installable("pmm_lab.strategies.mean_reversion_bb_rsi"):
            try:
                from pmm_lab.strategies.mean_reversion_bb_rsi import MeanReversionBBRSIStrategyConfig
            except ImportError as e:
                raise ImportError(
                    f"Directional MR module failed to import transitively: {e}"
                ) from e
            if isinstance(config, MeanReversionBBRSIStrategyConfig):
                from pmm_lab.features.mean_reversion_bb_rsi_features import (
                    compute_mr_bb_rsi_features,
                    MRBBRSIFeatureConfig,
                )
                feature_cfg = MRBBRSIFeatureConfig(
                    bb_length=config.bb_length,
                    bb_std=config.bb_std,
                    bbp_entry_threshold=config.bbp_entry_threshold,
                    rsi_length=config.rsi_length,
                    rsi_entry_threshold=config.rsi_entry_threshold,
                    use_trend_filter=config.use_trend_filter,
                    trend_ema_length=config.trend_ema_length,
                    min_trend_slope=config.min_trend_slope,
                    atr_length=config.atr_length,
                    max_atr_pct_for_entry=config.max_atr_pct_for_entry,
                    volume_filter_window=config.volume_filter_window,
                    min_volume_quantile=config.min_volume_quantile,
                    timestamp_mode=config.timestamp_mode,
                    controller_compat=config.controller_compat,
                )
                signals = compute_mr_bb_rsi_features(candles, feature_cfg)
                self.put(sig_key, effective_key, signals)
                return signals

        if _module_is_installable("pmm_lab.strategies.ema_regime_hold"):
            try:
                from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig
            except ImportError as e:
                raise ImportError(
                    f"Directional EMA module failed to import transitively: {e}"
                ) from e
            if isinstance(config, EMARegimeHoldStrategyConfig):
                if regime_candles is None:
                    raise ValueError(
                        "EMA regime-hold config requires regime_candles "
                        "to be passed to get_or_compute()."
                    )
                from pmm_lab.features.ema_regime_hold_features import (
                    compute_ema_regime_hold_features,
                    EMARegimeHoldFeatureConfig,
                )
                feature_cfg = EMARegimeHoldFeatureConfig(
                    regime_ema_fast=config.regime_ema_fast,
                    regime_ema_slow=config.regime_ema_slow,
                    regime_adx_length=config.regime_adx_length,
                    regime_adx_threshold=config.regime_adx_threshold,
                    volume_filter_window=config.volume_filter_window,
                    min_volume_quantile=config.min_volume_quantile,
                    hold_mode=config.hold_mode,
                    timestamp_mode=config.timestamp_mode,
                    controller_compat=config.controller_compat,
                )
                signals = compute_ema_regime_hold_features(
                    candles, regime_candles, feature_cfg,
                )
                self.put(sig_key, effective_key, signals)
                return signals

        raise TypeError(
            f"SharedSignalCache.get_or_compute: unsupported config type "
            f"{type(config).__name__}"
        )

    def __len__(self):
        return len(self._store)

    def clear(self):
        self._store.clear()
