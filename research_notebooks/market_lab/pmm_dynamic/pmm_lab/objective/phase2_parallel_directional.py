"""
Process-parallel signal precomputation for Phase 2 — directional strategies.

Computes unique directional signal keys in worker processes, populating a
SharedSignalCache before the serial stress-selection loop. Preserves exact
Phase 2 scoring and pruning semantics.

Sibling to phase2_parallel.py (which handles PMM/SimConfig). This module is
specialized for MeanReversionBBRSIStrategyConfig and EMARegimeHoldStrategyConfig.
"""

from __future__ import annotations

import logging
import os
import pickle
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from pmm_lab.objective.signal_cache import (
    SharedSignalCache,
    _dataset_key_for,
    signal_cache_key,
)

logger = logging.getLogger(__name__)


def _pin_blas_threads() -> None:
    """Force single-threaded BLAS inside each worker."""
    for var in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "BLIS_NUM_THREADS",
    ):
        os.environ[var] = "1"


def _compute_directional_signals_worker(
    config_pickle: bytes,
    candles_pickle: bytes,
    pair_rules_pickle: bytes,
    regime_candles_pickle: Optional[bytes],
    dataset_key: str,
) -> tuple:
    """Top-level worker function — must be picklable.

    Accepts pickled arguments to avoid any dtype-descriptor reconstruction
    (no `eval(...)` involved). Returns (sig_key, effective_dataset_key, signals).
    """
    _pin_blas_threads()

    import pickle as _pickle
    from pmm_lab.objective.signal_cache import (
        SharedSignalCache,
        _dataset_key_for,
        signal_cache_key,
    )

    config = _pickle.loads(config_pickle)
    candles = _pickle.loads(candles_pickle)
    pair_rules = _pickle.loads(pair_rules_pickle)
    regime_candles = (
        _pickle.loads(regime_candles_pickle)
        if regime_candles_pickle is not None
        else None
    )

    # Use a fresh SharedSignalCache inside the worker to delegate to the
    # canonical compute-and-store path. Then extract the single computed
    # signals object and return it along with its keys.
    local_cache = SharedSignalCache()
    signals = local_cache.get_or_compute(
        config, dataset_key, candles, pair_rules,
        regime_candles=regime_candles,
    )
    sig_key = signal_cache_key(config)
    effective_key = _dataset_key_for(config, dataset_key, regime_candles)
    return (sig_key, effective_key, signals)


def precompute_unique_directional_signals(
    top_candidates: List[dict],
    candles: Any,
    pair_rules: Any,
    regime_candles: Optional[Any] = None,
    dataset_key: str = "dev",
    max_workers: int = 1,
    shared_signal_cache: Optional[SharedSignalCache] = None,
) -> SharedSignalCache:
    """Precompute unique directional signals into a SharedSignalCache.

    Parameters
    ----------
    top_candidates : list of dict
        Each dict must have a "config" key. The config must be a
        MeanReversionBBRSIStrategyConfig or EMARegimeHoldStrategyConfig.
    candles : np.ndarray
        Signal-timeframe candle array.
    pair_rules : PairRules
        Exchange pair rules.
    regime_candles : np.ndarray, optional
        Regime-timeframe candles for EMA strategies. Ignored for MR.
    dataset_key : str
        Dataset identity (typically "dev" or "full").
    max_workers : int
        Number of worker processes. 1 or below means serial fallback.
    shared_signal_cache : SharedSignalCache, optional
        If provided, results are stored into this cache. If None, a fresh
        SharedSignalCache is created and returned.

    Returns
    -------
    SharedSignalCache
        The populated cache. All unique signal keys from top_candidates have
        entries under their effective dataset keys.
    """
    cache = shared_signal_cache if shared_signal_cache is not None else SharedSignalCache()

    # Deduplicate by signal_cache_key, preserving first-occurrence order for
    # deterministic debugging (worker completion order is independent).
    seen_keys: Dict[tuple, Any] = {}
    unique_in_order: List[Any] = []
    for cand in top_candidates:
        cfg = cand["config"]
        k = signal_cache_key(cfg)
        if k not in seen_keys:
            seen_keys[k] = cfg
            unique_in_order.append(cfg)

    logger.info(
        "Phase 2 directional signal precompute: %d unique signal keys from %d candidates",
        len(unique_in_order), len(top_candidates),
    )

    # Filter out configs whose signals are already cached to avoid redundant work.
    configs_to_compute = []
    for cfg in unique_in_order:
        cached = cache.get_for_config(cfg, dataset_key, regime_candles=regime_candles)
        if cached is None:
            configs_to_compute.append(cfg)

    if not configs_to_compute:
        logger.info(
            "Phase 2 directional signal precompute: all %d unique signals already cached",
            len(unique_in_order),
        )
        return cache

    if max_workers <= 1 or len(configs_to_compute) <= 1:
        # Serial fallback: identical to the pre-change notebook loop.
        for cfg in configs_to_compute:
            cache.get_or_compute(
                cfg, dataset_key, candles, pair_rules,
                regime_candles=regime_candles,
            )
        logger.info(
            "Phase 2 directional signal precompute (serial): %d signals cached",
            len(configs_to_compute),
        )
        return cache

    # Parallel path.
    candles_pickle = pickle.dumps(candles, protocol=pickle.HIGHEST_PROTOCOL)
    pair_rules_pickle = pickle.dumps(pair_rules, protocol=pickle.HIGHEST_PROTOCOL)
    regime_candles_pickle = (
        pickle.dumps(regime_candles, protocol=pickle.HIGHEST_PROTOCOL)
        if regime_candles is not None
        else None
    )

    n_workers = min(max_workers, len(configs_to_compute))

    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        futures = {}
        for cfg in configs_to_compute:
            cfg_pickle = pickle.dumps(cfg, protocol=pickle.HIGHEST_PROTOCOL)
            fut = pool.submit(
                _compute_directional_signals_worker,
                cfg_pickle,
                candles_pickle,
                pair_rules_pickle,
                regime_candles_pickle,
                dataset_key,
            )
            futures[fut] = cfg

        for fut in as_completed(futures):
            cfg = futures[fut]
            try:
                sig_key, effective_key, signals = fut.result()
            except Exception as e:
                logger.error(
                    "Phase 2 signal worker failed for signal_key=%s: %s",
                    signal_cache_key(cfg), e,
                )
                raise
            cache.put(sig_key, effective_key, signals)

    logger.info(
        "Phase 2 directional signal precompute (parallel, %d workers): %d signals cached",
        n_workers, len(configs_to_compute),
    )
    return cache
