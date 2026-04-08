"""Tests for parallel Phase 2 signal precomputation."""

import numpy as np
from dataclasses import replace

from pmm_lab.objective.phase2_parallel import precompute_unique_signals
from pmm_lab.objective.signal_cache import signal_cache_key
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.config.params import PairRules, FeeConfig


def _make_test_candles(n=100):
    """Create a small test candle array."""
    from pmm_lab.data.mongo import CANDLE_DTYPE
    rng = np.random.default_rng(seed=42)
    start_ts = 1756833000
    interval = 300
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 0.5)
        open_p = price
        close_p = max(open_p + change, 1.0)
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.2))
        low_p = max(min(open_p, close_p) - abs(rng.normal(0, 0.2)), 0.01)
        vol = rng.uniform(0.05, 2.0)
        rows.append((start_ts + i * interval, open_p, high_p, low_p, close_p, vol, False))
        price = close_p
    return np.array(rows, dtype=CANDLE_DTYPE)


def _make_pair_rules():
    return PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=5.0,
        fees=FeeConfig(0.001, 0.002),
    )


def _make_config(**overrides):
    defaults = dict(
        buy_spreads=[1.0], sell_spreads=[1.0],
        buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
    )
    defaults.update(overrides)
    return SimConfig(**defaults)


def test_precompute_serial_matches_inline():
    """Serial precompute must produce identical signals to inline computation."""
    candles = _make_test_candles()
    pair_rules = _make_pair_rules()
    config = _make_config()
    candidates = [{"config": config}]

    # Precomputed (serial)
    cache = precompute_unique_signals(candidates, candles, pair_rules, max_workers=1)
    key = signal_cache_key(config)
    assert key in cache

    # Inline
    runner = CandleSimRunner(config, pair_rules)
    inline_signals = runner.compute_signals(candles)

    # Compare signal arrays — SignalOutput has warmup_end and data dict
    cached_signals = cache[key]
    assert cached_signals.warmup_end == inline_signals.warmup_end
    for field_name, arr in inline_signals.data.items():
        assert field_name in cached_signals.data
        np.testing.assert_array_equal(cached_signals.data[field_name], arr)


def test_precompute_deduplicates_signal_keys():
    """Candidates with identical signal keys should only compute once."""
    candles = _make_test_candles()
    pair_rules = _make_pair_rules()

    # Two configs that differ only in non-signal fields (stop_loss)
    c1 = _make_config(stop_loss=0.03)
    c2 = _make_config(stop_loss=0.05)
    assert signal_cache_key(c1) == signal_cache_key(c2)

    candidates = [{"config": c1}, {"config": c2}]
    cache = precompute_unique_signals(candidates, candles, pair_rules, max_workers=1)
    assert len(cache) == 1  # deduplicated


def test_precompute_multiple_unique_keys():
    """Candidates with different signal keys produce multiple cache entries."""
    candles = _make_test_candles()
    pair_rules = _make_pair_rules()

    c1 = _make_config(macd_fast=12, macd_slow=26)
    c2 = _make_config(macd_fast=21, macd_slow=42)
    assert signal_cache_key(c1) != signal_cache_key(c2)

    candidates = [{"config": c1}, {"config": c2}]
    cache = precompute_unique_signals(candidates, candles, pair_rules, max_workers=1)
    assert len(cache) == 2
