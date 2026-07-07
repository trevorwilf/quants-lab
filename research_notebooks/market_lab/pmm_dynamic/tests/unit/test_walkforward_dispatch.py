"""Smoke tests for strategy-dispatched walk-forward."""
import numpy as np
import pytest


def _make_dummy_candles(n: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    bars = np.zeros(n, dtype=[
        ("timestamp", "i8"), ("open", "f8"), ("high", "f8"),
        ("low", "f8"), ("close", "f8"), ("volume", "f8"),
        ("is_forward_fill", "bool"),
    ])
    bars["timestamp"] = np.arange(n) * 60
    price = 100.0 + np.cumsum(rng.normal(0, 0.5, n))
    bars["open"] = price
    bars["close"] = price + rng.normal(0, 0.2, n)
    bars["high"] = np.maximum(bars["open"], bars["close"]) + 0.3
    bars["low"] = np.minimum(bars["open"], bars["close"]) - 0.3
    bars["volume"] = rng.uniform(1000, 5000, n)
    return bars


def _pair_rules():
    from pmm_lab.config.params import FeeConfig, PairRules
    return PairRules(
        price_tick=0.01, amount_step=0.0001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


def test_dispatch_pmm_config():
    """run_walk_forward_dispatch must work for PMM SimConfig (backwards compat)."""
    from pmm_lab.objective.walkforward_dispatch import run_walk_forward_dispatch
    from pmm_lab.sim.executor_model import SimConfig

    candles = _make_dummy_candles(3000)
    config = SimConfig(
        buy_spreads=[0.002], sell_spreads=[0.002],
        buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
        controller_compat=False,
    )
    result = run_walk_forward_dispatch(
        candles=candles, config=config, pair_rules=_pair_rules(),
        bar_interval_seconds=60, dataset_hash="deadbeef",
        train_days=1.0, test_days=0.5, step_days=0.5,
        objective_version=1,
    )
    assert len(result.folds) >= 1, "must produce at least 1 fold"
    assert result.dataset_hash == "deadbeef"


def test_dispatch_mr_config():
    """run_walk_forward_dispatch must work for MR BB+RSI config."""
    from pmm_lab.objective.walkforward_dispatch import run_walk_forward_dispatch
    from pmm_lab.optuna.canonicalizer_mean_reversion_bb_rsi import (
        canonicalize_mr_bb_rsi_params,
    )

    candles = _make_dummy_candles(6000)
    pair_rules = _pair_rules()
    raw_params = {
        "bb_length": 20, "bb_std": 2.0, "bbp_entry_threshold": 0.15,
        "rsi_length": 14, "rsi_entry_threshold": 35.0,
        "use_trend_filter": False, "trend_ema_length": 100,
        "atr_length": 14, "max_atr_pct_for_entry": 0.05,
        "volume_filter_window": 50, "min_volume_quantile": 0.0,
        "cooldown_time": 600, "stop_loss": 0.04, "take_profit": 0.02,
        "time_limit": 86400, "take_profit_order_type": "LIMIT",
        "trailing_stop_activation": 0.0, "trailing_stop_delta": 0.0,
        "max_spread_pct": 0.006, "max_trades_per_day": 6,
        "max_executors_per_side": 1, "total_amount_quote": 300.0,
        "min_trend_slope": 0.0,
    }
    bundle, reject = canonicalize_mr_bb_rsi_params(
        raw_params, pair_rules, 100.0, bar_interval_seconds=60,
    )
    assert bundle is not None, f"canonicalize rejected params: {reject}"

    result = run_walk_forward_dispatch(
        candles=candles, config=bundle.strategy_config,
        engine_config=bundle.engine_config,
        pair_rules=pair_rules,
        bar_interval_seconds=60, dataset_hash="mr_test",
        train_days=1.0, test_days=0.5, step_days=0.5,
        objective_version=1,
    )
    assert len(result.folds) >= 1


def test_dispatch_mr_without_engine_config_raises():
    """Directional config without engine_config must raise ValueError, NOT return None."""
    from pmm_lab.objective.walkforward_dispatch import run_walk_forward_dispatch
    try:
        from pmm_lab.strategies.mean_reversion_bb_rsi import MeanReversionBBRSIStrategyConfig
    except ImportError:
        pytest.skip("MR imports unavailable in this env")

    config = MeanReversionBBRSIStrategyConfig()
    candles = _make_dummy_candles(3000)
    with pytest.raises(ValueError, match="engine_config is required"):
        run_walk_forward_dispatch(
            candles=candles, config=config, pair_rules=_pair_rules(),
            bar_interval_seconds=60, dataset_hash="x",
            train_days=1.0, test_days=0.5, step_days=0.5,
        )


def _range_ladder_bundle(bar_interval_seconds=60):
    from pmm_lab.optuna.canonicalizer_range_ladder import canonicalize_range_ladder_params
    raw_params = {
        "n_buy": 4, "n_sell": 4,
        "buy_near_pct": 0.02, "buy_far_pct": 0.15,
        "sell_near_pct": 0.02, "sell_far_pct": 0.15,
        "buy_gamma": 1.0, "sell_gamma": 1.0,
        "k_buy": 0.5, "k_sell": 0.5,
        "fund_quote": 1000.0, "quote_frac": 0.5,
        "cooldown_time": 3600,
    }
    bundle, reject = canonicalize_range_ladder_params(
        raw_params, _pair_rules(), 100.0, bar_interval_seconds=bar_interval_seconds,
    )
    assert bundle is not None, f"canonicalize rejected params: {reject}"
    return bundle


def test_dispatch_range_ladder_config():
    """run_walk_forward_dispatch must work for the (signal-less) range_ladder."""
    from pmm_lab.objective.walkforward_dispatch import run_walk_forward_dispatch

    candles = _make_dummy_candles(6000)
    bundle = _range_ladder_bundle()
    result = run_walk_forward_dispatch(
        candles=candles, config=bundle.strategy_config,
        engine_config=bundle.engine_config,
        pair_rules=_pair_rules(),
        bar_interval_seconds=60, dataset_hash="rl_test",
        train_days=1.0, test_days=0.5, step_days=0.5,
        objective_version=1,
    )
    assert len(result.folds) >= 1
    assert result.dataset_hash == "rl_test"


def test_dispatch_range_ladder_without_engine_config_raises():
    from pmm_lab.objective.walkforward_dispatch import run_walk_forward_dispatch
    from pmm_lab.strategies.range_ladder import RangeLadderConfig

    candles = _make_dummy_candles(3000)
    with pytest.raises(ValueError, match="engine_config is required"):
        run_walk_forward_dispatch(
            candles=candles, config=RangeLadderConfig(), pair_rules=_pair_rules(),
            bar_interval_seconds=60, dataset_hash="x",
            train_days=1.0, test_days=0.5, step_days=0.5,
        )
