"""End-to-end mini-sweep parity test — flag-on vs flag-off.

Runs a minimal Phase-2 style pipeline for both MR and EMA with
`use_numba_kernel=True` and `use_numba_kernel=False`, and asserts:
  1. The same candidate wins.
  2. Boolean signal arrays are bit-exact.
  3. Float arrays within per-indicator tolerances from Stage 1.
  4. `best["robust_score"]` matches within rtol=1e-6.

Skipped in normal unit runs (integration marker). Run explicitly:
    pytest tests/integration/test_numba_flag_end_to_end_parity.py -v
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

pytestmark = pytest.mark.integration


def _make_candles(n: int = 3000, seed: int = 1) -> np.ndarray:
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


def _make_regime(n: int = 300, seed: int = 2) -> np.ndarray:
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
        rows.append((ts0 + i * 3000, op, hi, lo, cl, rng.uniform(0.5, 3.0), False))
        price = cl
    return np.array(rows, dtype=CANDLE_DTYPE)


def _pair_rules():
    from pmm_lab.config.params import FeeConfig, PairRules
    return PairRules(
        price_tick=0.01, amount_step=0.0001, min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


def _build_engine(total_quote: float = 100.0):
    from pmm_lab.sim.engine_config import EngineConfig
    return EngineConfig(
        total_amount_quote=total_quote,
        stop_loss=0.02, take_profit=0.03,
        time_limit=3600, latency_bars=1, slippage_bps=5.0,
    )


def _assert_signals_parity(s_off, s_on, *, name: str, float_tol_by_field: dict):
    assert s_off.warmup_end == s_on.warmup_end, f"{name}: warmup_end differs"
    assert set(s_off.data.keys()) == set(s_on.data.keys()), (
        f"{name}: signal-output key set differs"
    )
    for k in s_off.data:
        a_off = np.asarray(s_off.data[k])
        a_on = np.asarray(s_on.data[k])
        assert a_off.shape == a_on.shape, f"{name}[{k}]: shape differs"
        if k in ("signal", "volume_ok", "trend_on", "vol_ok"):
            # Booleans-as-float must be bit-exact
            np.testing.assert_array_equal(
                a_off, a_on, err_msg=f"{name}[{k}]: boolean not bit-exact",
            )
        else:
            atol = float_tol_by_field.get(k, 1e-12)
            nan_off = np.isnan(a_off)
            nan_on = np.isnan(a_on)
            assert np.array_equal(nan_off, nan_on), f"{name}[{k}]: NaN positions differ"
            mask = ~nan_off
            if mask.any():
                np.testing.assert_allclose(
                    a_off[mask], a_on[mask], atol=atol, rtol=atol,
                    err_msg=f"{name}[{k}]: float mismatch at atol={atol}",
                )


# ────────────────────────────────────────────────────────────────────────────

def test_mini_sweep_mr_numba_on_matches_numba_off_signals():
    """MR: Phase-2 mini-sweep with 5 candidates, flag on vs flag off.

    Verifies: same winner, bit-exact boolean signals, float signals within
    Stage 1 per-indicator tolerances.
    """
    from pmm_lab.objective.signal_cache import SharedSignalCache
    from pmm_lab.objective.stress_selection import select_best_stressed_candidate
    from pmm_lab.strategies.mean_reversion_bb_rsi import MeanReversionBBRSIStrategyConfig

    candles = _make_candles(3000, seed=1)
    pair_rules = _pair_rules()
    base = MeanReversionBBRSIStrategyConfig(
        bb_length=20, bb_std=2.0, bbp_entry_threshold=0.15,
        rsi_length=14, rsi_entry_threshold=35.0,
        use_trend_filter=False, trend_ema_length=50,
        atr_length=14, max_atr_pct_for_entry=0.10,
        volume_filter_window=30, min_volume_quantile=0.0,
        controller_compat=True, timestamp_mode="open",
    )
    cfg_off = [replace(base, bb_length=20 + i, use_numba_kernel=False) for i in range(5)]
    cfg_on = [replace(c, use_numba_kernel=True) for c in cfg_off]

    def _build_top(configs):
        return [
            {"config": c, "engine_config": _build_engine(100.0 + i * 10),
             "trial_number": i, "phase1_score": 0.0}
            for i, c in enumerate(configs)
        ]

    # OFF
    cache_off = SharedSignalCache()
    for c in cfg_off:
        cache_off.get_or_compute(c, "dev", candles, pair_rules)
    best_off, diag_off = select_best_stressed_candidate(
        top_candidates=_build_top(cfg_off), candles=candles, pair_rules=pair_rules,
        bar_interval_seconds=300, scenarios=[], objective_version=2,
        shared_signal_cache=cache_off, dataset_key="dev",
    )

    # ON
    cache_on = SharedSignalCache()
    for c in cfg_on:
        cache_on.get_or_compute(c, "dev", candles, pair_rules)
    best_on, diag_on = select_best_stressed_candidate(
        top_candidates=_build_top(cfg_on), candles=candles, pair_rules=pair_rules,
        bar_interval_seconds=300, scenarios=[], objective_version=2,
        shared_signal_cache=cache_on, dataset_key="dev",
    )

    # Same winner
    assert (best_off is None) == (best_on is None)
    if best_off is not None:
        assert best_off["trial_number"] == best_on["trial_number"], (
            f"Different winners: off={best_off['trial_number']} on={best_on['trial_number']}"
        )
        # Robust score within rtol=1e-6
        rs_off = best_off["robust_score"]
        rs_on = best_on["robust_score"]
        assert rs_off == pytest.approx(rs_on, rel=1e-6, abs=1e-9), (
            f"robust_score off={rs_off} != on={rs_on}"
        )

    # Signal arrays: bit-exact booleans; relaxed bbp tol
    for c_off, c_on in zip(cfg_off, cfg_on):
        s_off = cache_off.get_for_config(c_off, "dev")
        s_on = cache_on.get_for_config(c_on, "dev")
        _assert_signals_parity(
            s_off, s_on, name="MR",
            float_tol_by_field={"bbp": 1e-10},
        )


def test_mini_sweep_ema_numba_on_matches_numba_off_signals():
    """EMA: Phase-2 mini-sweep with 5 candidates, flag on vs flag off."""
    from pmm_lab.objective.signal_cache import SharedSignalCache
    from pmm_lab.objective.stress_selection import select_best_stressed_candidate
    from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig

    candles = _make_candles(3000, seed=1)
    regime = _make_regime(300, seed=2)
    pair_rules = _pair_rules()
    base = EMARegimeHoldStrategyConfig(
        regime_ema_fast=10, regime_ema_slow=30,
        regime_adx_length=14, regime_adx_threshold=20.0,
        volume_filter_window=30, min_volume_quantile=0.0,
        hold_mode="reentry", timestamp_mode="open",
        controller_compat=True,
    )
    base = replace(base, _regime_candles=regime)
    cfg_off = [
        replace(base, regime_ema_fast=10 + i, use_numba_kernel=False)
        for i in range(5)
    ]
    cfg_on = [replace(c, use_numba_kernel=True) for c in cfg_off]

    def _build_top(configs):
        return [
            {"config": c, "engine_config": _build_engine(100.0 + i * 10),
             "trial_number": i, "phase1_score": 0.0}
            for i, c in enumerate(configs)
        ]

    cache_off = SharedSignalCache()
    for c in cfg_off:
        cache_off.get_or_compute(c, "dev", candles, pair_rules, regime_candles=regime)
    best_off, diag_off = select_best_stressed_candidate(
        top_candidates=_build_top(cfg_off), candles=candles, pair_rules=pair_rules,
        bar_interval_seconds=300, scenarios=[], objective_version=2,
        shared_signal_cache=cache_off, dataset_key="dev",
        regime_candles=regime,
    )

    cache_on = SharedSignalCache()
    for c in cfg_on:
        cache_on.get_or_compute(c, "dev", candles, pair_rules, regime_candles=regime)
    best_on, diag_on = select_best_stressed_candidate(
        top_candidates=_build_top(cfg_on), candles=candles, pair_rules=pair_rules,
        bar_interval_seconds=300, scenarios=[], objective_version=2,
        shared_signal_cache=cache_on, dataset_key="dev",
        regime_candles=regime,
    )

    assert (best_off is None) == (best_on is None)
    if best_off is not None:
        assert best_off["trial_number"] == best_on["trial_number"]
        rs_off = best_off["robust_score"]
        rs_on = best_on["robust_score"]
        assert rs_off == pytest.approx(rs_on, rel=1e-6, abs=1e-9)

    for c_off, c_on in zip(cfg_off, cfg_on):
        s_off = cache_off.get_for_config(c_off, "dev", regime_candles=regime)
        s_on = cache_on.get_for_config(c_on, "dev", regime_candles=regime)
        _assert_signals_parity(
            s_off, s_on, name="EMA", float_tol_by_field={},
        )
