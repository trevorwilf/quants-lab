"""Stage 2 cache-key semantics tests.

Covers:
- SharedSignalCache.get_for_config (config-aware probe that honors EMA regime key)
- stress_selection EMA diagnostic hit-rate via config-aware probe
- sensitivity no bare-key alias write
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest


def _make_candles(n: int = 500, seed: int = 1) -> np.ndarray:
    from tests.conftest import CANDLE_DTYPE
    rng = np.random.default_rng(seed)
    rows = []
    ts0 = 1_700_000_000
    price = 100.0
    for i in range(n):
        ch = rng.normal(0, 0.5)
        op = price
        cl = op + ch
        hi = max(op, cl) + abs(rng.normal(0, 0.2))
        lo = min(op, cl) - abs(rng.normal(0, 0.2))
        hi = max(hi, max(op, cl))
        lo = max(lo, 0.01)
        lo = min(lo, min(op, cl))
        rows.append((ts0 + i * 300, op, hi, lo, cl, rng.uniform(0.5, 3.0), False))
        price = cl
    return np.array(rows, dtype=CANDLE_DTYPE)


def _make_regime(n: int = 200, seed: int = 2) -> np.ndarray:
    return _make_candles(n=n, seed=seed)


def _pair_rules():
    from pmm_lab.config.params import FeeConfig, PairRules
    return PairRules(
        price_tick=0.01, amount_step=0.0001, min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


# ────────────────────────────────────────────────────────────────────────────

def test_shared_signal_cache_get_for_config_sim_config():
    """For a SimConfig, get_for_config reduces to get(sig_key, dataset_key)."""
    from pmm_lab.objective.signal_cache import SharedSignalCache, signal_cache_key
    from pmm_lab.sim.executor_model import SimConfig

    cache = SharedSignalCache()
    cfg = SimConfig(
        buy_spreads=[0.002], sell_spreads=[0.002],
        buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
        controller_compat=False,
    )
    cache.put(signal_cache_key(cfg), "dev", "fake_signals")
    assert cache.get_for_config(cfg, "dev") == "fake_signals"


def test_shared_signal_cache_get_for_config_ema_regime_aware():
    """For EMA, get_for_config must hit the regime-hashed effective key after
    get_or_compute warmed the cache."""
    from pmm_lab.objective.signal_cache import SharedSignalCache
    from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig

    cache = SharedSignalCache()
    cfg = EMARegimeHoldStrategyConfig(
        regime_ema_fast=10, regime_ema_slow=30,
        regime_adx_length=14, regime_adx_threshold=20.0,
        volume_filter_window=30, min_volume_quantile=0.0,
        hold_mode="reentry", timestamp_mode="open", controller_compat=False,
    )
    candles = _make_candles(500, seed=1)
    regime = _make_regime(100, seed=2)

    cfg_with_regime = replace(cfg, _regime_candles=regime)
    signals = cache.get_or_compute(
        cfg_with_regime, "dev", candles, _pair_rules(), regime_candles=regime,
    )
    # Now probe with the same regime via get_for_config — must be a HIT
    hit = cache.get_for_config(cfg_with_regime, "dev", regime_candles=regime)
    assert hit is signals, "get_for_config must return the cached signals"


def test_shared_signal_cache_get_for_config_ema_regime_miss_with_different_regime():
    """Different regime candles produce a different effective key → cache miss."""
    from pmm_lab.objective.signal_cache import SharedSignalCache
    from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig

    cache = SharedSignalCache()
    cfg = EMARegimeHoldStrategyConfig(
        regime_ema_fast=10, regime_ema_slow=30,
        regime_adx_length=14, regime_adx_threshold=20.0,
        volume_filter_window=30, min_volume_quantile=0.0,
        hold_mode="reentry", timestamp_mode="open", controller_compat=False,
    )
    candles = _make_candles(500, seed=1)
    regime_a = _make_regime(100, seed=2)
    regime_b = _make_regime(100, seed=3)

    cache.get_or_compute(
        replace(cfg, _regime_candles=regime_a),
        "dev", candles, _pair_rules(), regime_candles=regime_a,
    )
    # Probe with regime_b — different hash → miss
    miss = cache.get_for_config(
        replace(cfg, _regime_candles=regime_b),
        "dev", regime_candles=regime_b,
    )
    assert miss is None


def test_stress_selection_ema_diagnostics_hit_rate():
    """Pre-warming the cache with get_or_compute must yield hits (not misses)
    when stress_selection probes via the new config-aware path."""
    from pmm_lab.objective.signal_cache import SharedSignalCache
    from pmm_lab.objective.stress_selection import select_best_stressed_candidate
    from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig
    from pmm_lab.sim.engine_config import EngineConfig

    candles = _make_candles(800, seed=1)
    regime = _make_regime(200, seed=2)
    pair_rules = _pair_rules()

    # Three candidates with the SAME feature-affecting params (same signal_cache_key)
    # but different execution-only fields.
    base_strategy = EMARegimeHoldStrategyConfig(
        regime_ema_fast=10, regime_ema_slow=30,
        regime_adx_length=14, regime_adx_threshold=20.0,
        volume_filter_window=30, min_volume_quantile=0.0,
        hold_mode="reentry", timestamp_mode="open", controller_compat=False,
    )
    strategy_with_regime = replace(base_strategy, _regime_candles=regime)

    cache = SharedSignalCache()
    # Pre-warm
    cache.get_or_compute(
        strategy_with_regime, "dev", candles, pair_rules, regime_candles=regime,
    )

    # All three candidates share the same signal_cache_key so they should all
    # hit the pre-warmed entry.
    engine_configs = [
        EngineConfig(total_amount_quote=100.0, stop_loss=0.02, take_profit=0.03,
                      time_limit=3600, latency_bars=1, slippage_bps=5.0),
        EngineConfig(total_amount_quote=200.0, stop_loss=0.03, take_profit=0.04,
                      time_limit=3600, latency_bars=1, slippage_bps=5.0),
        EngineConfig(total_amount_quote=300.0, stop_loss=0.04, take_profit=0.05,
                      time_limit=3600, latency_bars=1, slippage_bps=5.0),
    ]
    top = [
        {"config": strategy_with_regime, "engine_config": ec,
         "trial_number": i, "phase1_score": 0.0}
        for i, ec in enumerate(engine_configs)
    ]

    # Use no scenarios so the run stays fast and predictable
    best, diag = select_best_stressed_candidate(
        top_candidates=top, candles=candles, pair_rules=pair_rules,
        bar_interval_seconds=300, scenarios=[],
        objective_version=2,
        shared_signal_cache=cache, dataset_key="dev",
        regime_candles=regime,
    )

    # Every candidate probes the shared cache with the SAME signal_cache_key
    # and regime → the shared cache is hit on each iteration.
    # Note: the local signal_cache dict also hits after iteration 1, so we
    # expect at least 1 hit from shared and up to 3 total.
    assert diag["candidates_evaluated"] == 3
    assert diag["signal_cache_misses"] == 0, (
        f"Pre-warmed cache must yield zero misses; got diag={diag}"
    )
    assert diag["signal_cache_hits"] >= 1, (
        f"Expected at least one shared cache hit; got diag={diag}"
    )


def test_sensitivity_no_bare_key_alias_written():
    """After an EMA sensitivity round that invokes _get_or_compute_signals,
    the SharedSignalCache must NOT contain a bare-key alias (the old bug
    double-wrote under both bare and effective keys)."""
    from pmm_lab.objective.signal_cache import SharedSignalCache, signal_cache_key
    from pmm_lab.optuna.canonicalizer_ema_regime_hold import canonicalize_ema_regime_hold_params
    from pmm_lab.optuna.sensitivity import compute_sensitivity, EMA_PERTURBABLE_PARAMS

    candles = _make_candles(1200, seed=1)
    regime = _make_regime(300, seed=2)
    pair_rules = _pair_rules()
    shared_cache = SharedSignalCache()

    # Build an EMA canonicalizer adapter that the sensitivity call can use
    def _ema_canon(params, pair_rules_arg, ref_price_arg, **kwargs):
        raw = dict(params)
        raw.setdefault("hold_mode", "reentry")
        raw.setdefault("max_executors_per_side", 1)
        raw.setdefault("total_amount_quote", 300.0)
        return canonicalize_ema_regime_hold_params(
            raw, pair_rules_arg, ref_price_arg,
            signal_interval_seconds=300, regime_candles=regime,
        )

    params = {
        "regime_ema_fast": 10, "regime_ema_slow": 30,
        "regime_adx_length": 14, "regime_adx_threshold": 20.0,
        "volume_filter_window": 30, "min_volume_quantile": 0.0,
        "cooldown_time": 300, "stop_loss": 0.04, "take_profit": 0.02,
        "time_limit": 86400, "take_profit_order_type": "LIMIT",
        "trailing_stop_activation": 0.0, "trailing_stop_delta": 0.0,
        "max_executors_per_side": 1, "total_amount_quote": 300.0,
    }
    # Perturb only execution-only fields to keep test fast
    compute_sensitivity(
        params=params, candles=candles, pair_rules=pair_rules,
        bar_interval_seconds=300, reference_price=100.0,
        objective_version=2,
        shared_signal_cache=shared_cache,
        canonicalize_fn=_ema_canon,
        regime_candles=regime,
        perturb_params=["total_amount_quote"],
        delta_pct=0.10,
    )

    # Inspect internal store: no entry should be keyed on the bare "dev" dataset_key
    # for an EMA signal key (first element of the tuple == "ema_regime_hold").
    bare_aliases = [
        k for k in shared_cache._store
        if k[0][0] == "ema_regime_hold" and k[1] == "dev"
    ]
    assert not bare_aliases, (
        f"Bare-key alias(es) found in cache for EMA: {bare_aliases}. "
        f"Entries should only be keyed on the effective 'dev#regime=<hash>' form."
    )
    # Positive check: the effective (regime-hashed) entry DOES exist
    effective = [
        k for k in shared_cache._store
        if k[0][0] == "ema_regime_hold" and k[1].startswith("dev#regime=")
    ]
    assert effective, (
        f"Expected at least one regime-hashed entry; cache store: {list(shared_cache._store)}"
    )
