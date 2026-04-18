"""Stage 3: Phase 2 directional signal precompute — parallelism parity.

Must produce bit-exact identical signals to the serial path, preserve
identical Phase 2 selection winners, and fall back to serial cleanly when
only one unique signal key exists.

Tests use controller_compat=False so they run in a few seconds each. The
parity test is about the precompute mechanism (dispatch/pickle/dedup),
not the feature kernel.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest


# ────────────────────────────────────────────────────────────────────────────
# Fixtures & helpers
# ────────────────────────────────────────────────────────────────────────────

def _make_candles(n: int = 2000, seed: int = 1) -> np.ndarray:
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


def _make_regime(n: int = 500, seed: int = 2) -> np.ndarray:
    from tests.conftest import CANDLE_DTYPE
    rng = np.random.default_rng(seed)
    rows = []
    ts0 = 1_700_000_000
    price = 100.0
    for i in range(n):
        ch = rng.normal(0, 1.0)
        op = price
        cl = op + ch
        hi = max(op, cl) + abs(rng.normal(0, 0.5))
        lo = min(op, cl) - abs(rng.normal(0, 0.5))
        hi = max(hi, max(op, cl))
        lo = max(lo, 0.01)
        lo = min(lo, min(op, cl))
        rows.append((ts0 + i * 28800, op, hi, lo, cl, rng.uniform(0.5, 3.0), False))
        price = cl
    return np.array(rows, dtype=CANDLE_DTYPE)


def _pair_rules():
    from pmm_lab.config.params import FeeConfig, PairRules
    return PairRules(
        price_tick=0.01, amount_step=0.0001, min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


def _mr_configs(n: int = 3, distinct: bool = True):
    from pmm_lab.strategies.mean_reversion_bb_rsi import MeanReversionBBRSIStrategyConfig
    base = MeanReversionBBRSIStrategyConfig(
        bb_length=20, bb_std=2.0, bbp_entry_threshold=0.15,
        rsi_length=14, rsi_entry_threshold=35.0,
        use_trend_filter=False, trend_ema_length=50,
        min_trend_slope=0.0, atr_length=14, max_atr_pct_for_entry=0.10,
        volume_filter_window=30, min_volume_quantile=0.0,
        timestamp_mode="open", controller_compat=False,
    )
    configs = []
    for i in range(n):
        if distinct:
            configs.append(replace(base, bb_length=20 + i, rsi_length=14 + i))
        else:
            configs.append(base)
    return configs


def _ema_configs(n: int = 3, regime: np.ndarray = None, distinct: bool = True):
    from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig
    base = EMARegimeHoldStrategyConfig(
        regime_ema_fast=10, regime_ema_slow=30,
        regime_adx_length=14, regime_adx_threshold=20.0,
        volume_filter_window=30, min_volume_quantile=0.0,
        hold_mode="reentry", timestamp_mode="open", controller_compat=False,
    )
    if regime is not None:
        base = replace(base, _regime_candles=regime)
    configs = []
    for i in range(n):
        if distinct:
            configs.append(replace(base, regime_ema_fast=5 + 2 * i))
        else:
            configs.append(base)
    return configs


def _signals_equal(a, b) -> bool:
    """Compare two SignalOutput instances structurally (array equality)."""
    if set(a.data.keys()) != set(b.data.keys()):
        return False
    if a.warmup_end != b.warmup_end:
        return False
    for k in a.data:
        av, bv = a.data[k], b.data[k]
        if av.dtype != bv.dtype:
            return False
        if av.shape != bv.shape:
            return False
        if np.issubdtype(av.dtype, np.floating):
            if not np.allclose(av, bv, equal_nan=True, atol=0, rtol=0):
                return False
        else:
            if not np.array_equal(av, bv):
                return False
    return True


# ────────────────────────────────────────────────────────────────────────────
# Tests
# ────────────────────────────────────────────────────────────────────────────

def test_phase2_precompute_directional_mr_serial_matches_inline():
    from pmm_lab.objective.phase2_parallel_directional import (
        precompute_unique_directional_signals,
    )
    from pmm_lab.objective.signal_cache import SharedSignalCache, signal_cache_key

    candles = _make_candles(2000)
    pair_rules = _pair_rules()
    configs = _mr_configs(3, distinct=True)
    top = [{"config": c} for c in configs]

    # Inline baseline
    inline_cache = SharedSignalCache()
    for cfg in configs:
        inline_cache.get_or_compute(cfg, "dev", candles, pair_rules)

    # Serial dispatch
    new_cache = precompute_unique_directional_signals(
        top_candidates=top, candles=candles, pair_rules=pair_rules,
        dataset_key="dev", max_workers=1,
    )

    for cfg in configs:
        sig_inline = inline_cache.get_for_config(cfg, "dev")
        sig_new = new_cache.get_for_config(cfg, "dev")
        assert sig_inline is not None and sig_new is not None
        assert _signals_equal(sig_inline, sig_new)


def test_phase2_precompute_directional_ema_serial_matches_inline():
    from pmm_lab.objective.phase2_parallel_directional import (
        precompute_unique_directional_signals,
    )
    from pmm_lab.objective.signal_cache import SharedSignalCache

    candles = _make_candles(2000)
    regime = _make_regime(500)
    pair_rules = _pair_rules()
    configs = _ema_configs(3, regime=regime, distinct=True)
    top = [{"config": c} for c in configs]

    inline_cache = SharedSignalCache()
    for cfg in configs:
        inline_cache.get_or_compute(cfg, "dev", candles, pair_rules, regime_candles=regime)

    new_cache = precompute_unique_directional_signals(
        top_candidates=top, candles=candles, pair_rules=pair_rules,
        regime_candles=regime, dataset_key="dev", max_workers=1,
    )

    for cfg in configs:
        sig_inline = inline_cache.get_for_config(cfg, "dev", regime_candles=regime)
        sig_new = new_cache.get_for_config(cfg, "dev", regime_candles=regime)
        assert sig_inline is not None and sig_new is not None
        assert _signals_equal(sig_inline, sig_new)


def test_phase2_precompute_directional_dedupes_signal_keys():
    """Candidates with identical signal_cache_key share one computation."""
    from pmm_lab.objective.phase2_parallel_directional import (
        precompute_unique_directional_signals,
    )
    from pmm_lab.objective.signal_cache import signal_cache_key

    candles = _make_candles(1500)
    pair_rules = _pair_rules()
    # Two duplicate signal-keys (cand 0 == cand 2) among 4 candidates
    base, alt = _mr_configs(2, distinct=True)
    configs = [base, alt, base, replace(alt, bb_length=alt.bb_length + 5)]
    top = [{"config": c} for c in configs]

    cache = precompute_unique_directional_signals(
        top_candidates=top, candles=candles, pair_rules=pair_rules,
        dataset_key="dev", max_workers=1,
    )

    unique_keys = {signal_cache_key(c) for c in configs}
    assert len(unique_keys) == 3  # distinct signal keys
    # Cache entries: one per unique key
    mr_entries = [k for k in cache._store if k[0][0] == "mr_bb_rsi"]
    assert len(mr_entries) == 3, f"expected 3 unique entries, got {len(mr_entries)}"

    # Identity check: cand 0 and cand 2 share signals object
    sig0 = cache.get_for_config(configs[0], "dev")
    sig2 = cache.get_for_config(configs[2], "dev")
    assert sig0 is sig2


def test_phase2_precompute_directional_parallel_matches_serial_mr():
    from pmm_lab.objective.phase2_parallel_directional import (
        precompute_unique_directional_signals,
    )

    candles = _make_candles(2000)
    pair_rules = _pair_rules()
    configs = _mr_configs(4, distinct=True)
    top = [{"config": c} for c in configs]

    serial = precompute_unique_directional_signals(
        top_candidates=top, candles=candles, pair_rules=pair_rules,
        dataset_key="dev", max_workers=1,
    )
    parallel = precompute_unique_directional_signals(
        top_candidates=top, candles=candles, pair_rules=pair_rules,
        dataset_key="dev", max_workers=2,
    )

    for cfg in configs:
        s = serial.get_for_config(cfg, "dev")
        p = parallel.get_for_config(cfg, "dev")
        assert s is not None and p is not None
        assert _signals_equal(s, p)


def test_phase2_precompute_directional_parallel_matches_serial_ema():
    from pmm_lab.objective.phase2_parallel_directional import (
        precompute_unique_directional_signals,
    )

    candles = _make_candles(2000)
    regime = _make_regime(500)
    pair_rules = _pair_rules()
    configs = _ema_configs(4, regime=regime, distinct=True)
    top = [{"config": c} for c in configs]

    serial = precompute_unique_directional_signals(
        top_candidates=top, candles=candles, pair_rules=pair_rules,
        regime_candles=regime, dataset_key="dev", max_workers=1,
    )
    parallel = precompute_unique_directional_signals(
        top_candidates=top, candles=candles, pair_rules=pair_rules,
        regime_candles=regime, dataset_key="dev", max_workers=2,
    )

    for cfg in configs:
        s = serial.get_for_config(cfg, "dev", regime_candles=regime)
        p = parallel.get_for_config(cfg, "dev", regime_candles=regime)
        assert s is not None and p is not None
        assert _signals_equal(s, p)


def test_phase2_precompute_directional_prewarmed_cache_no_recompute():
    """A pre-warmed cache must skip candidates whose signals are already cached."""
    from pmm_lab.objective.phase2_parallel_directional import (
        precompute_unique_directional_signals,
    )
    from pmm_lab.objective.signal_cache import SharedSignalCache

    candles = _make_candles(1500)
    pair_rules = _pair_rules()
    configs = _mr_configs(2, distinct=True)
    cfg_a, cfg_b = configs

    cache = SharedSignalCache()
    # Pre-warm with cfg_a only
    signals_a_initial = cache.get_or_compute(cfg_a, "dev", candles, pair_rules)

    top = [{"config": cfg_a}, {"config": cfg_b}]
    precompute_unique_directional_signals(
        top_candidates=top, candles=candles, pair_rules=pair_rules,
        dataset_key="dev", max_workers=1,
        shared_signal_cache=cache,
    )

    # cfg_a's cached signals must be the SAME object (not recomputed)
    signals_a_after = cache.get_for_config(cfg_a, "dev")
    assert signals_a_after is signals_a_initial, (
        "Pre-warmed signals must not be recomputed — expected same object identity"
    )
    # cfg_b's signals must now also be cached
    assert cache.get_for_config(cfg_b, "dev") is not None


def test_phase2_precompute_directional_end_to_end_selection_winner_unchanged_mr():
    """Winner, robust score, and diagnostics must match across inline vs new precompute."""
    from pmm_lab.objective.phase2_parallel_directional import (
        precompute_unique_directional_signals,
    )
    from pmm_lab.objective.signal_cache import SharedSignalCache
    from pmm_lab.objective.stress_selection import select_best_stressed_candidate
    from pmm_lab.sim.engine_config import EngineConfig

    candles = _make_candles(2000)
    pair_rules = _pair_rules()
    configs = _mr_configs(5, distinct=True)

    def _build_top():
        return [
            {
                "config": c, "trial_number": i, "phase1_score": 0.1 * i,
                "engine_config": EngineConfig(
                    total_amount_quote=100.0 + i * 10,
                    stop_loss=0.02, take_profit=0.03,
                    time_limit=3600, latency_bars=1, slippage_bps=5.0,
                ),
            }
            for i, c in enumerate(configs)
        ]

    # Pipeline A: inline loop (pre-change behavior)
    cache_a = SharedSignalCache()
    for c in configs:
        cache_a.get_or_compute(c, "dev", candles, pair_rules)
    best_a, diag_a = select_best_stressed_candidate(
        top_candidates=_build_top(), candles=candles, pair_rules=pair_rules,
        bar_interval_seconds=300, scenarios=[],
        objective_version=2, shared_signal_cache=cache_a, dataset_key="dev",
    )

    # Pipeline B: new precompute
    cache_b = precompute_unique_directional_signals(
        top_candidates=_build_top(), candles=candles, pair_rules=pair_rules,
        dataset_key="dev", max_workers=1,
    )
    best_b, diag_b = select_best_stressed_candidate(
        top_candidates=_build_top(), candles=candles, pair_rules=pair_rules,
        bar_interval_seconds=300, scenarios=[],
        objective_version=2, shared_signal_cache=cache_b, dataset_key="dev",
    )

    assert (best_a is None) == (best_b is None)
    if best_a is not None:
        assert best_a["trial_number"] == best_b["trial_number"]
        assert best_a["robust_score"] == pytest.approx(best_b["robust_score"], abs=0, rel=0)
        assert best_a["baseline_score"] == pytest.approx(best_b["baseline_score"], abs=0, rel=0)
        assert best_a["worst_score"] == pytest.approx(best_b["worst_score"], abs=0, rel=0)

    assert diag_a["candidates_evaluated"] == diag_b["candidates_evaluated"]
    assert diag_a["candidates_pruned"] == diag_b["candidates_pruned"]


def test_phase2_precompute_directional_end_to_end_selection_winner_unchanged_ema():
    from pmm_lab.objective.phase2_parallel_directional import (
        precompute_unique_directional_signals,
    )
    from pmm_lab.objective.signal_cache import SharedSignalCache
    from pmm_lab.objective.stress_selection import select_best_stressed_candidate
    from pmm_lab.sim.engine_config import EngineConfig

    candles = _make_candles(2000)
    regime = _make_regime(500)
    pair_rules = _pair_rules()
    configs = _ema_configs(5, regime=regime, distinct=True)

    def _build_top():
        return [
            {
                "config": c, "trial_number": i, "phase1_score": 0.1 * i,
                "engine_config": EngineConfig(
                    total_amount_quote=100.0 + i * 10,
                    stop_loss=0.02, take_profit=0.03,
                    time_limit=3600, latency_bars=1, slippage_bps=5.0,
                ),
            }
            for i, c in enumerate(configs)
        ]

    cache_a = SharedSignalCache()
    for c in configs:
        cache_a.get_or_compute(c, "dev", candles, pair_rules, regime_candles=regime)
    best_a, diag_a = select_best_stressed_candidate(
        top_candidates=_build_top(), candles=candles, pair_rules=pair_rules,
        bar_interval_seconds=300, scenarios=[],
        objective_version=2, shared_signal_cache=cache_a, dataset_key="dev",
        regime_candles=regime,
    )

    cache_b = precompute_unique_directional_signals(
        top_candidates=_build_top(), candles=candles, pair_rules=pair_rules,
        regime_candles=regime, dataset_key="dev", max_workers=1,
    )
    best_b, diag_b = select_best_stressed_candidate(
        top_candidates=_build_top(), candles=candles, pair_rules=pair_rules,
        bar_interval_seconds=300, scenarios=[],
        objective_version=2, shared_signal_cache=cache_b, dataset_key="dev",
        regime_candles=regime,
    )

    assert (best_a is None) == (best_b is None)
    if best_a is not None:
        assert best_a["trial_number"] == best_b["trial_number"]
        assert best_a["robust_score"] == pytest.approx(best_b["robust_score"], abs=0, rel=0)
    assert diag_a["candidates_evaluated"] == diag_b["candidates_evaluated"]


def test_phase2_precompute_directional_worker_error_raises():
    """Force a real worker failure and assert it propagates.

    An EMA config evaluated WITHOUT regime_candles raises ValueError inside
    get_or_compute — this naturally produces a worker-process exception that
    should surface to the caller rather than being silently swallowed.
    """
    from pmm_lab.objective import phase2_parallel_directional as mod

    candles = _make_candles(800)
    pair_rules = _pair_rules()
    # EMA configs but pass regime_candles=None → worker ValueError
    configs = _ema_configs(2, regime=None, distinct=True)
    top = [{"config": c} for c in configs]

    with pytest.raises((ValueError, Exception)) as excinfo:
        mod.precompute_unique_directional_signals(
            top_candidates=top, candles=candles, pair_rules=pair_rules,
            regime_candles=None, dataset_key="dev", max_workers=2,
        )
    # The worker ValueError about missing regime_candles must surface
    assert "regime_candles" in str(excinfo.value).lower() or \
           "unsupported config type" in str(excinfo.value).lower() or \
           "EMA regime-hold" in str(excinfo.value)
