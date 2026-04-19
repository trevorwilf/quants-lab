"""
Process-parallel signal precomputation for Phase 2.

Computes unique signal keys in worker processes, populating a signal cache
before the serial stress-selection loop. This preserves the exact current
Phase 2 scoring and pruning logic while attacking the true bottleneck.
"""

import os
import logging
from typing import Dict, List
from concurrent.futures import ProcessPoolExecutor

from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.objective.signal_cache import signal_cache_key

logger = logging.getLogger(__name__)


def _pin_blas_threads():
    """Force single-threaded BLAS inside each worker."""
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                "BLIS_NUM_THREADS"):
        os.environ[var] = "1"


def _compute_signals_worker(config_dict: dict, candles_bytes: bytes,
                             candles_dtype_str: str,
                             pair_rules_dict: dict) -> tuple:
    """Top-level worker function for signal computation.

    Accepts serializable data, returns (signal_key, signals).
    Must be at module top level for pickling.
    """
    _pin_blas_threads()

    import numpy as np
    from pmm_lab.sim.executor_model import SimConfig
    from pmm_lab.config.params import PairRules
    from pmm_lab.sim.runner import CandleSimRunner
    from pmm_lab.objective.signal_cache import signal_cache_key

    config = SimConfig(**config_dict)
    pair_rules = PairRules(**pair_rules_dict)
    candles = np.frombuffer(candles_bytes, dtype=np.dtype(eval(candles_dtype_str))).copy()

    key = signal_cache_key(config)
    runner = CandleSimRunner(config, pair_rules)
    signals = runner.compute_signals(candles)
    return (key, signals)


def precompute_unique_signals(
    top_candidates: List[dict],
    candles,
    pair_rules,
    max_workers: int = 1,
) -> dict:
    """Precompute unique signal keys for Phase 2 candidates.

    Parameters
    ----------
    top_candidates : list of dict
        Each dict has a "config" key with a SimConfig.
    candles : np.ndarray
        Candle data array.
    pair_rules : PairRules
        Exchange pair rules.
    max_workers : int
        Number of worker processes. Default 1 (serial, for debugging).

    Returns
    -------
    dict
        Mapping from signal_cache_key to computed signals.
    """
    # Deduplicate by signal key
    unique_configs = {}
    for cand in top_candidates:
        cfg = cand["config"]
        key = signal_cache_key(cfg)
        if key not in unique_configs:
            unique_configs[key] = cfg

    logger.info("Phase 2 signal precompute: %d unique keys from %d candidates",
                len(unique_configs), len(top_candidates))

    if max_workers <= 1 or len(unique_configs) <= 1:
        # Serial fallback
        from pmm_lab.sim.runner import CandleSimRunner
        cache = {}
        for key, cfg in unique_configs.items():
            runner = CandleSimRunner(cfg, pair_rules)
            cache[key] = runner.compute_signals(candles)
        return cache

    # Serialize data for workers
    from dataclasses import asdict
    candles_bytes = candles.tobytes()
    candles_dtype_str = repr(candles.dtype.descr)
    pair_rules_dict = asdict(pair_rules)

    cache = {}
    with ProcessPoolExecutor(max_workers=min(max_workers, len(unique_configs))) as pool:
        futures = {}
        for key, cfg in unique_configs.items():
            cfg_dict = asdict(cfg)
            future = pool.submit(_compute_signals_worker, cfg_dict,
                                 candles_bytes, candles_dtype_str,
                                 pair_rules_dict)
            futures[future] = key

        for future in futures:
            try:
                result_key, signals = future.result()
                cache[result_key] = signals
            except Exception as e:
                logger.error("Signal worker failed for key %s: %s",
                             futures[future], e)
                raise

    logger.info("Phase 2 signal precompute complete: %d signals cached",
                len(cache))
    return cache
