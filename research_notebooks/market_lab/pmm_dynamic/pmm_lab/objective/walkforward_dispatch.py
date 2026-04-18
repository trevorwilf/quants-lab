"""Strategy-dispatched walk-forward evaluation.

Unlike `pmm_lab.objective.walkforward.run_walk_forward` (which is typed around PMM
`SimConfig` and uses `CandleSimRunner`), this dispatcher accepts any supported strategy
config type (SimConfig, MeanReversionBBRSIStrategyConfig, EMARegimeHoldStrategyConfig)
and routes execution through `pmm_lab.sim.runner_dispatch.run_simulation`.

This is the single entrypoint directional notebooks should use for walk-forward.
The PMM-only `run_walk_forward` is retained for backwards compatibility with the
PMM pipeline but is deprecated for directional use.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

import numpy as np

from pmm_lab.config.params import PairRules
from pmm_lab.metrics.metrics import compute_metrics
from pmm_lab.objective.objective import (
    objective_v1, objective_v2, ObjectiveWeights, ObjectiveWeightsV2,
)
from pmm_lab.objective.robustness import robust_aggregate
from pmm_lab.objective.signal_cache import SharedSignalCache
from pmm_lab.objective.walkforward import (
    FoldResult, TimeSeriesCV, WalkForwardResult,
)
from pmm_lab.sim.executor_model import SimConfig, SimResult
from pmm_lab.sim.runner_dispatch import run_simulation

logger = logging.getLogger(__name__)


def _warmup_bars_for_config(config: Any) -> int:
    """Compute warmup bar requirement based on strategy type.

    PMM SimConfig: max(macd_slow, natr_length) + small buffer (same as the
    default used by TimeSeriesCV for PMM).
    MR BB+RSI:    max(bb_length, rsi_length, trend_ema_length, atr_length,
                       volume_filter_window) + buffer
    EMA regime:   max(regime_ema_slow, regime_adx_length,
                       volume_filter_window) + buffer
    """
    if isinstance(config, SimConfig):
        return max(int(config.macd_slow), int(config.natr_length)) + 10

    try:
        from pmm_lab.strategies.mean_reversion_bb_rsi import MeanReversionBBRSIStrategyConfig
        if isinstance(config, MeanReversionBBRSIStrategyConfig):
            trend = int(config.trend_ema_length) if config.use_trend_filter else 0
            return max(
                int(config.bb_length),
                int(config.rsi_length),
                trend,
                int(config.atr_length),
                int(config.volume_filter_window),
            ) + 50
    except ImportError as e:
        logger.warning("MR config import failed in warmup calc: %s", e)

    try:
        from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig
        if isinstance(config, EMARegimeHoldStrategyConfig):
            return max(
                int(config.regime_ema_slow),
                int(config.regime_adx_length),
                int(config.volume_filter_window),
            ) + 100
    except ImportError as e:
        logger.warning("EMA config import failed in warmup calc: %s", e)

    return 200


def _total_amount_quote(config, engine_config) -> float:
    """Resolve the initial equity from config (PMM) or engine_config (MR/EMA)."""
    if isinstance(config, SimConfig):
        return float(config.total_amount_quote)
    if engine_config is not None and hasattr(engine_config, "total_amount_quote"):
        return float(engine_config.total_amount_quote)
    return 100.0


def run_walk_forward_dispatch(
    *,
    candles: np.ndarray,
    config: Any,
    pair_rules: PairRules,
    bar_interval_seconds: int,
    dataset_hash: str,
    train_days: float = 42.0,
    test_days: float = 14.0,
    step_days: float = 14.0,
    embargo_bars: Optional[int] = None,
    objective_weights: Optional[Any] = None,
    objective_version: int = 1,
    engine_config: Optional[Any] = None,
    regime_candles: Optional[np.ndarray] = None,
    shared_signal_cache: Optional[SharedSignalCache] = None,
    dataset_key: str = "dev",
    precomputed_signals: Optional[Any] = None,
) -> WalkForwardResult:
    """Run walk-forward evaluation for any supported strategy config type.

    Parameters match `run_walk_forward` plus:
    - `engine_config`: required for MR/EMA (separates strategy params from engine).
    - `regime_candles`: required for EMA.
    - `shared_signal_cache`: optional; used for signal precomputation reuse.

    Raises
    ------
    ValueError
        - MR/EMA without engine_config

    Returns
    -------
    WalkForwardResult
        Same shape as the PMM run_walk_forward — `folds`, `fold_definitions`,
        `aggregate_score`, `per_fold_scores`, `config_used`, `dataset_hash`.
    """
    # 1. Validate inputs per config type
    if not isinstance(config, SimConfig):
        if engine_config is None:
            raise ValueError(
                f"run_walk_forward_dispatch: engine_config is required for "
                f"{type(config).__name__} (directional configs separate strategy from engine)."
            )

    # 2. Build fold layout. Use config-aware warmup for TimeSeriesCV.
    warmup = _warmup_bars_for_config(config)
    n_bars = len(candles)

    cv = TimeSeriesCV(
        n_bars=n_bars,
        bar_interval_seconds=bar_interval_seconds,
        train_days=train_days,
        test_days=test_days,
        step_days=step_days,
        embargo_bars=embargo_bars,
        macd_slow=warmup,
        natr_length=warmup,
    )
    fold_defs = cv.get_folds()

    # 3. Precompute signals once for the full candle array via the dispatched cache.
    if precomputed_signals is not None:
        full_signals = precomputed_signals
    elif shared_signal_cache is not None:
        full_signals = shared_signal_cache.get_or_compute(
            config, f"{dataset_key}:full", candles, pair_rules,
            regime_candles=regime_candles,
        )
    else:
        _cache = SharedSignalCache()
        full_signals = _cache.get_or_compute(
            config, f"{dataset_key}:full", candles, pair_rules,
            regime_candles=regime_candles,
        )

    # 4. Run per-fold simulations via the dispatcher.
    initial_equity = _total_amount_quote(config, engine_config)

    # Select objective
    if objective_version == 2:
        _weights = objective_weights if isinstance(objective_weights, ObjectiveWeightsV2) else ObjectiveWeightsV2()
        obj_fn = lambda m: objective_v2(m, _weights)
    else:
        _weights = objective_weights if isinstance(objective_weights, ObjectiveWeights) else ObjectiveWeights()
        obj_fn = lambda m: objective_v1(m, _weights)

    fold_results: List[FoldResult] = []
    per_fold_scores: List[float] = []

    for fold_def in fold_defs:
        candle_slice = candles[: fold_def.test_end_idx]

        sim_result = run_simulation(
            config=config,
            pair_rules=pair_rules,
            candles=candle_slice,
            precomputed_signals=full_signals,
            engine_config=engine_config,
            sim_start_idx=fold_def.test_start_idx,
            bar_index_offset=0,
            regime_candles=regime_candles,
        )

        test_eq = sim_result.equity_curve[fold_def.test_start_idx:fold_def.test_end_idx]
        test_pos = sim_result.position_history[fold_def.test_start_idx:fold_def.test_end_idx]
        test_candles = candles[fold_def.test_start_idx:fold_def.test_end_idx]
        test_trades = [t for t in sim_result.trades if t.entry_bar >= fold_def.test_start_idx]

        test_sim_result = SimResult(
            trades=test_trades,
            equity_curve=test_eq,
            position_history=test_pos,
            n_orders_placed=sim_result.n_orders_placed,
            n_orders_filled=sim_result.n_orders_filled,
            n_orders_rejected=sim_result.n_orders_rejected,
            n_market_exits=sim_result.n_market_exits,
            final_base_balance=sim_result.final_base_balance,
            final_quote_balance=sim_result.final_quote_balance,
        )

        test_metrics = compute_metrics(
            test_sim_result, initial_equity, test_candles, bar_interval_seconds,
        )
        test_obj = obj_fn(test_metrics)

        fold_results.append(FoldResult(
            fold_index=fold_def.fold_index,
            train_metrics=None,  # test-only; include_train_metrics omitted for dispatch
            test_metrics=test_metrics,
            test_objective=test_obj,
            train_trade_count=None,
            test_trade_count=test_metrics.trade_count,
        ))
        per_fold_scores.append(test_obj.raw_score)

    aggregate = robust_aggregate(per_fold_scores) if per_fold_scores else float("nan")

    return WalkForwardResult(
        folds=fold_results,
        fold_definitions=fold_defs,
        aggregate_score=aggregate,
        per_fold_scores=per_fold_scores,
        config_used=config,
        dataset_hash=dataset_hash,
    )
