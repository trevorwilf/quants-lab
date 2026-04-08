"""Tests for the shared signal cache utility."""

import numpy as np
import pytest
from dataclasses import replace

from pmm_lab.objective.signal_cache import signal_cache_key, SIGNAL_AFFECTING_FIELDS
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.sim.runner import CandleSimRunner


@pytest.fixture
def base_config():
    return SimConfig(
        buy_spreads=[1.0], sell_spreads=[1.0],
        buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
        controller_compat=False,
    )


class TestSignalCacheKey:
    """Verify the cache key covers all signal-affecting fields."""

    def test_key_covers_all_signal_fields(self, base_config):
        """Key tuple has exactly len(SIGNAL_AFFECTING_FIELDS) elements."""
        key = signal_cache_key(base_config)
        assert len(key) == len(SIGNAL_AFFECTING_FIELDS)

    def test_different_macd_fast_different_key(self, base_config):
        alt = replace(base_config, macd_fast=12)
        assert signal_cache_key(base_config) != signal_cache_key(alt)

    def test_different_macd_slow_different_key(self, base_config):
        alt = replace(base_config, macd_slow=100)
        assert signal_cache_key(base_config) != signal_cache_key(alt)

    def test_different_macd_signal_different_key(self, base_config):
        alt = replace(base_config, macd_signal=5)
        assert signal_cache_key(base_config) != signal_cache_key(alt)

    def test_different_natr_length_different_key(self, base_config):
        alt = replace(base_config, natr_length=20)
        assert signal_cache_key(base_config) != signal_cache_key(alt)

    def test_different_controller_compat_different_key(self, base_config):
        alt = replace(base_config, controller_compat=True)
        assert signal_cache_key(base_config) != signal_cache_key(alt)

    def test_different_timestamp_mode_different_key(self, base_config):
        alt = replace(base_config, timestamp_mode="close")
        assert signal_cache_key(base_config) != signal_cache_key(alt)

    def test_trade_params_same_key(self, base_config):
        """Changing trade-execution params does NOT change the cache key."""
        alt = replace(
            base_config,
            buy_spreads=[2.0, 4.0],
            sell_spreads=[2.0, 4.0],
            buy_amounts_pct=[0.5, 0.5],
            sell_amounts_pct=[0.5, 0.5],
            stop_loss=0.05,
            take_profit=0.03,
            fill_participation_rate=0.5,
            slippage_bps=10.0,
            latency_bars=3,
        )
        assert signal_cache_key(base_config) == signal_cache_key(alt)

    def test_cached_signals_produce_same_result(self, base_config, sample_candles_500, default_pair_rules):
        """Using cached signals produces identical simulation results."""
        runner = CandleSimRunner(base_config, default_pair_rules)
        signals = runner.compute_signals(sample_candles_500)

        # Run with fresh signals
        result1 = runner.run(sample_candles_500)

        # Run with cached signals
        result2 = runner.run_with_signals(sample_candles_500, signals)

        np.testing.assert_array_equal(result1.equity_curve, result2.equity_curve)


class TestSharedSignalCache:
    """Tests for SharedSignalCache cross-step reuse."""

    def test_shared_cache_avoids_recomputation(self, base_config, sample_candles_500, default_pair_rules):
        """Second get_or_compute with same key+dataset must return cached result."""
        from pmm_lab.objective.signal_cache import SharedSignalCache
        cache = SharedSignalCache()

        sig1 = cache.get_or_compute(base_config, "dev", sample_candles_500, default_pair_rules)
        assert len(cache) == 1

        sig2 = cache.get_or_compute(base_config, "dev", sample_candles_500, default_pair_rules)
        assert len(cache) == 1  # no new entry
        assert sig1 is sig2  # same object (cache hit, not recomputation)

    def test_shared_cache_different_dataset_keys(self, base_config, sample_candles_500, default_pair_rules):
        """Different dataset_key should produce separate cache entries."""
        from pmm_lab.objective.signal_cache import SharedSignalCache
        cache = SharedSignalCache()

        sig_dev = cache.get_or_compute(base_config, "dev", sample_candles_500, default_pair_rules)
        sig_full = cache.get_or_compute(base_config, "full", sample_candles_500, default_pair_rules)
        assert len(cache) == 2
        assert sig_dev is not sig_full
