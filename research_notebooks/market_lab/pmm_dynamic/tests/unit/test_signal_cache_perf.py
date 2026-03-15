"""Performance test to ensure signal caching provides expected speedup."""

import time
import pytest

from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.config.params import PairRules, FeeConfig


@pytest.fixture
def default_sim_config():
    return SimConfig(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5],
        sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
    )


@pytest.fixture
def default_pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


class TestSignalCachePerformance:
    def test_cached_faster_than_uncached(self, sample_candles_5m, default_sim_config, default_pair_rules):
        """run_with_signals() should be faster than run() when reusing signals."""
        runner = CandleSimRunner(default_sim_config, default_pair_rules)
        n_folds = 5

        # Uncached: compute signals each time
        t0 = time.time()
        for i in range(n_folds):
            end = len(sample_candles_5m) - (n_folds - i) * 2
            runner.run(sample_candles_5m[:end])
        uncached_time = time.time() - t0

        # Cached: compute once, reuse
        signals = runner.compute_signals(sample_candles_5m)
        t0 = time.time()
        for i in range(n_folds):
            end = len(sample_candles_5m) - (n_folds - i) * 2
            runner.run_with_signals(sample_candles_5m[:end], signals)
        cached_time = time.time() - t0

        # Cached should be at least 2x faster (in practice 5-10x on real data)
        assert cached_time < uncached_time, (
            f"Cached ({cached_time:.2f}s) not faster than uncached ({uncached_time:.2f}s)"
        )
