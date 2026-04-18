"""Benchmark MR and EMA Numba kernels vs pandas replay path.

Measures wall time on 16000-bar candles for:
  - pandas path (use_numba_kernel=False)
  - numba first call (JIT compile included)
  - numba warm call (JIT cached)

Expected: warm-call speedup >= 20x for both MR and EMA.
"""

from __future__ import annotations

import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np


CANDLE_DTYPE = np.dtype([
    ("timestamp", "int64"),
    ("open", "float64"),
    ("high", "float64"),
    ("low", "float64"),
    ("close", "float64"),
    ("volume", "float64"),
    ("is_forward_fill", "bool"),
])


def _make_candles(n: int, seed: int, dt: int) -> np.ndarray:
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
        rows.append((ts0 + i * dt, op, hi, lo, cl, rng.uniform(0.5, 3.0), False))
        price = cl
    return np.array(rows, dtype=CANDLE_DTYPE)


def _timed(fn):
    t0 = time.perf_counter()
    out = fn()
    return out, time.perf_counter() - t0


def bench_mr(n_bars: int = 16000):
    from pmm_lab.features.mean_reversion_bb_rsi_features import (
        MRBBRSIFeatureConfig, compute_mr_bb_rsi_features,
    )
    print(f"\n== MR (controller_compat, {n_bars} bars) ==")
    candles = _make_candles(n_bars, seed=42, dt=300)
    cfg_pd = MRBBRSIFeatureConfig(
        bb_length=80, bb_std=2.0, bbp_entry_threshold=0.20,
        rsi_length=14, rsi_entry_threshold=40.0,
        use_trend_filter=True, trend_ema_length=200,
        atr_length=14, max_atr_pct_for_entry=0.10,
        volume_filter_window=288, min_volume_quantile=0.30,
        timestamp_mode="open", controller_compat=True, use_numba_kernel=False,
    )
    cfg_nb = replace(cfg_pd, use_numba_kernel=True)

    _, t_pd = _timed(lambda: compute_mr_bb_rsi_features(candles, cfg_pd))
    _, t_nb_cold = _timed(lambda: compute_mr_bb_rsi_features(candles, cfg_nb))
    _, t_nb_warm = _timed(lambda: compute_mr_bb_rsi_features(candles, cfg_nb))

    print(f"  pandas path       : {t_pd:>8.3f} s")
    print(f"  numba (first call): {t_nb_cold:>8.3f} s  (incl. JIT)")
    print(f"  numba (warm call) : {t_nb_warm:>8.3f} s")
    print(f"  speedup warm      : {t_pd / max(t_nb_warm, 1e-9):>8.1f}x")
    return t_pd, t_nb_cold, t_nb_warm


def bench_ema(n_bars: int = 16000):
    from pmm_lab.features.ema_regime_hold_features import (
        EMARegimeHoldFeatureConfig, compute_ema_regime_hold_features,
    )
    print(f"\n== EMA (controller_compat, {n_bars} fast bars) ==")
    fast = _make_candles(n_bars, seed=42, dt=300)
    regime = _make_candles(n_bars // 48, seed=142, dt=300 * 48)  # 4h regime
    cfg_pd = EMARegimeHoldFeatureConfig(
        regime_ema_fast=50, regime_ema_slow=200,
        regime_adx_length=14, regime_adx_threshold=20.0,
        volume_filter_window=288, min_volume_quantile=0.30,
        hold_mode="reentry", timestamp_mode="open",
        controller_compat=True, use_numba_kernel=False,
    )
    cfg_nb = replace(cfg_pd, use_numba_kernel=True)

    _, t_pd = _timed(lambda: compute_ema_regime_hold_features(fast, regime, cfg_pd))
    _, t_nb_cold = _timed(lambda: compute_ema_regime_hold_features(fast, regime, cfg_nb))
    _, t_nb_warm = _timed(lambda: compute_ema_regime_hold_features(fast, regime, cfg_nb))

    print(f"  pandas path       : {t_pd:>8.3f} s")
    print(f"  numba (first call): {t_nb_cold:>8.3f} s  (incl. JIT)")
    print(f"  numba (warm call) : {t_nb_warm:>8.3f} s")
    print(f"  speedup warm      : {t_pd / max(t_nb_warm, 1e-9):>8.1f}x")
    return t_pd, t_nb_cold, t_nb_warm


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    # Use the requested 16000-bar size; pandas MR/EMA at 16000 can take tens of minutes,
    # so allow a smaller --n-bars override for smoke runs.
    n_bars = 16000
    if len(sys.argv) > 1:
        try:
            n_bars = int(sys.argv[1])
        except ValueError:
            pass
    print(f"Benchmarking controller-compat kernels at n_bars={n_bars} ...")
    bench_mr(n_bars)
    bench_ema(n_bars)


if __name__ == "__main__":
    main()
