"""Tests for SharedSignalCache dataset-scoped keying."""

import pytest
from unittest.mock import MagicMock

from pmm_lab.objective.signal_cache import SharedSignalCache, signal_cache_key


class TestSharedSignalCache:
    """SharedSignalCache must scope by both signal key and dataset key."""

    def test_same_key_different_dataset_no_collision(self):
        """Same signal key with different dataset keys must not collide."""
        cache = SharedSignalCache()
        sig_key = (12, 26, 9, 14, True, "open")

        cache.put(sig_key, "dev", "signals_dev")
        cache.put(sig_key, "full", "signals_full")

        assert cache.get(sig_key, "dev") == "signals_dev"
        assert cache.get(sig_key, "full") == "signals_full"
        assert len(cache) == 2

    def test_miss_returns_none(self):
        """Cache miss must return None."""
        cache = SharedSignalCache()
        assert cache.get((1, 2, 3), "dev") is None

    def test_clear_empties_cache(self):
        """clear() must remove all entries."""
        cache = SharedSignalCache()
        cache.put((1,), "dev", "x")
        cache.put((2,), "full", "y")
        cache.clear()
        assert len(cache) == 0

    def test_different_signal_keys_same_dataset(self):
        """Different signal keys with same dataset key must not collide."""
        cache = SharedSignalCache()
        cache.put((12, 26, 9, 14, True, "open"), "dev", "signals_a")
        cache.put((12, 26, 9, 21, True, "open"), "dev", "signals_b")

        assert cache.get((12, 26, 9, 14, True, "open"), "dev") == "signals_a"
        assert cache.get((12, 26, 9, 21, True, "open"), "dev") == "signals_b"

    def test_get_or_compute_caches_result(self):
        """get_or_compute must cache the computed result.

        Uses a real SimConfig (signal_cache dispatch now uses isinstance).
        """
        from pmm_lab.sim.executor_model import SimConfig

        cache = SharedSignalCache()
        config = SimConfig(
            buy_spreads=[1.0], sell_spreads=[1.0],
            buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
            controller_compat=False,
        )

        import numpy as np
        candles = np.zeros(10, dtype=[("close", "f8"), ("timestamp", "i8")])
        pair_rules = MagicMock()

        # Patch CandleSimRunner where it's looked up inside get_or_compute
        from unittest.mock import patch
        mock_runner = MagicMock()
        mock_runner.compute_signals.return_value = "computed_signals"

        with patch("pmm_lab.sim.runner.CandleSimRunner", return_value=mock_runner):
            result1 = cache.get_or_compute(config, "dev", candles, pair_rules)
            assert result1 == "computed_signals"
            assert len(cache) == 1

            # Second call should hit cache (no new computation)
            result2 = cache.get_or_compute(config, "dev", candles, pair_rules)
            assert result2 == "computed_signals"
            assert mock_runner.compute_signals.call_count == 1
