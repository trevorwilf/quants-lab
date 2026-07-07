"""Signal cache must distinguish configs from different strategies and
must dispatch signal computation to the right feature module."""

import numpy as np
import pytest

from pmm_lab.objective.signal_cache import signal_cache_key, SharedSignalCache
from pmm_lab.strategies.mean_reversion_bb_rsi import MeanReversionBBRSIStrategyConfig
from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig
from pmm_lab.sim.executor_model import SimConfig


def _make_regime_candles(n: int = 200, interval: int = 28800) -> np.ndarray:
    """Build a synthetic candle array at regime (8h) cadence."""
    from tests.conftest import CANDLE_DTYPE
    rng = np.random.default_rng(seed=77)
    start_ts = 1_700_000_000
    price = 100.0
    rows = []
    for i in range(n):
        ts = start_ts + i * interval
        change = rng.normal(0, 0.5)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.3))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.3))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = rng.uniform(0.5, 3.0)
        rows.append((ts, open_p, high_p, low_p, close_p, vol, False))
        price = close_p
    return np.array(rows, dtype=CANDLE_DTYPE)


def test_signal_cache_key_differs_across_strategy_types():
    mr_cfg = MeanReversionBBRSIStrategyConfig()
    ema_cfg = EMARegimeHoldStrategyConfig()
    assert signal_cache_key(mr_cfg) != signal_cache_key(ema_cfg)


def test_signal_cache_key_pmm_branch_unchanged():
    """Regression: PMM SimConfig's cache key format has not changed.
    This keeps PMM Dynamic + MACD-BB backward-compatible."""
    cfg = SimConfig(
        buy_spreads=[1.0], sell_spreads=[1.0],
        buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
        controller_compat=False,
    )
    key = signal_cache_key(cfg)
    # PMM branch: (macd_fast, macd_slow, macd_signal, natr_length, controller_compat, timestamp_mode)
    assert len(key) == 6
    assert key == (
        cfg.macd_fast, cfg.macd_slow, cfg.macd_signal,
        cfg.natr_length, cfg.controller_compat, cfg.timestamp_mode,
    )


def test_signal_cache_key_mr_has_type_tag():
    mr_cfg = MeanReversionBBRSIStrategyConfig()
    key = signal_cache_key(mr_cfg)
    assert key[0] == "mr_bb_rsi"


def test_signal_cache_key_ema_has_type_tag():
    ema_cfg = EMARegimeHoldStrategyConfig()
    key = signal_cache_key(ema_cfg)
    assert key[0] == "ema_regime_hold"


def test_signal_cache_get_or_compute_mr(sample_candles_500, default_pair_rules):
    """Verify MR dispatch: computes signals, caches them, hits on second call."""
    cache = SharedSignalCache()
    mr_cfg = MeanReversionBBRSIStrategyConfig()
    assert len(cache) == 0
    signals_a = cache.get_or_compute(mr_cfg, "test", sample_candles_500, default_pair_rules)
    assert signals_a is not None
    assert len(cache) == 1
    # Second call — cache hit. Same object, cache size unchanged.
    signals_b = cache.get_or_compute(mr_cfg, "test", sample_candles_500, default_pair_rules)
    assert signals_b is signals_a
    assert len(cache) == 1


def test_signal_cache_get_or_compute_ema_requires_regime_candles(
    sample_candles_500, default_pair_rules,
):
    cache = SharedSignalCache()
    ema_cfg = EMARegimeHoldStrategyConfig()
    with pytest.raises(ValueError, match="regime_candles"):
        cache.get_or_compute(ema_cfg, "test", sample_candles_500, default_pair_rules)

    regime = _make_regime_candles(n=300)
    signals = cache.get_or_compute(
        ema_cfg, "test", sample_candles_500, default_pair_rules,
        regime_candles=regime,
    )
    assert signals is not None
    assert len(cache) == 1


def test_signal_cache_key_unknown_type_raises():
    class UnknownConfig:
        pass
    with pytest.raises(TypeError, match="unsupported config type"):
        signal_cache_key(UnknownConfig())


def test_signal_cache_key_range_ladder_type_tag():
    """range_ladder is signal-less: its key is just the type tag."""
    from pmm_lab.strategies.range_ladder import RangeLadderConfig
    cfg = RangeLadderConfig()
    key = signal_cache_key(cfg)
    assert key == ("range_ladder",)
    assert key != signal_cache_key(MeanReversionBBRSIStrategyConfig())
    assert key != signal_cache_key(EMARegimeHoldStrategyConfig())


def test_signal_cache_get_or_compute_range_ladder(sample_candles_500, default_pair_rules):
    """Signal-less strategy: passthrough entry is cached like any other."""
    from pmm_lab.strategies.range_ladder import RangeLadderConfig
    cache = SharedSignalCache()
    cfg = RangeLadderConfig()
    signals_a = cache.get_or_compute(cfg, "dev", sample_candles_500, default_pair_rules)
    assert len(cache) == 1
    assert signals_a.warmup_end == 0
    assert np.array_equal(signals_a.data["close_price"], sample_candles_500["close"])
    signals_b = cache.get_or_compute(cfg, "dev", sample_candles_500, default_pair_rules)
    assert signals_b is signals_a, "second call must be a cache hit"
    assert len(cache) == 1
    # a different ladder config maps to the SAME key (no signal-affecting fields)
    cfg2 = RangeLadderConfig(k_buy=2.0)
    assert signal_cache_key(cfg2) == signal_cache_key(cfg)
