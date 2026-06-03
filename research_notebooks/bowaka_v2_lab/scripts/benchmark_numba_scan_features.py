"""Benchmark the Phase 1 numba scan-feature kernels vs the pure-Python build loop.

Times the per-(scan, symbol) aggregate + features for a realistic per-session
symbol batch three ways: pure-Python (the current build loop), numba-first
(cold/JIT), numba-warm (cached). Reports the per-session feature-compute delta
and the projected build-time delta. Target warm speedup >= 10x.

    cd research_notebooks/bowaka_v2_lab
    PYTHONPATH=src:../bowaka_common/src python scripts/benchmark_numba_scan_features.py [n_symbols] [n_scans]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

_LAB_ROOT = Path(__file__).resolve().parents[1]
if str(_LAB_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_LAB_ROOT / "src"))

from bowaka_v2_lab.features._numba_scan_features import (  # noqa: E402
    _NUMBA_AVAILABLE,
    build_session_columns_nb,
)
from bowaka_v2_lab.features.forming_bar import (  # noqa: E402
    _et_minute_of_day,
    aggregate_forming_session_bar,
    compute_forming_session_features,
    compute_prior_daily_baselines,
    compute_volume_curve_fraction,
)

_FALLBACK = 0.08


def _timed(fn):
    t0 = time.perf_counter()
    out = fn()
    return out, time.perf_counter() - t0


def _make_symbol(seed: int, n_min: int):
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2024-05-01 09:30", tz="America/New_York").tz_convert("UTC")
    ts = [start + pd.Timedelta(minutes=i) for i in range(n_min)]
    price = 100.0
    o_, h_, l_, c_, v_ = [], [], [], [], []
    for _ in range(n_min):
        o = price
        c = o + rng.normal(0.0, 0.2)
        h = max(o, c) + abs(rng.normal(0.0, 0.1))
        lo = max(min(o, c) - abs(rng.normal(0.0, 0.1)), 0.01)
        o_.append(o); h_.append(h); l_.append(lo); c_.append(c); v_.append(float(rng.uniform(0.5, 3.0)))
        price = c
    mdf = pd.DataFrame({"timestamp": ts, "open": o_, "high": h_, "low": l_, "close": c_, "volume": v_})
    drng = np.random.default_rng(seed + 5000)
    dp = 100.0
    drows = []
    for _ in range(40):
        do = dp; dc = do + drng.normal(0, 1); dh = max(do, dc) + abs(drng.normal(0, 0.5))
        dl = max(min(do, dc) - abs(drng.normal(0, 0.5)), 0.01)
        drows.append((do, dh, dl, dc, float(drng.uniform(1e5, 5e5)))); dp = dc
    ddf = pd.DataFrame(drows, columns=["open", "high", "low", "close", "volume"])
    base = compute_prior_daily_baselines(ddf)
    return mdf, base


def _pure(mdf, base, scan_times, fallback):
    out = []
    for s in scan_times:
        sc = pd.Timestamp(s).tz_convert("UTC")
        bt = mdf[mdf["timestamp"] <= sc]
        sess = aggregate_forming_session_bar(bt)
        vcf = compute_volume_curve_fraction(None, sc, "x", fallback_opening_15m_share=fallback)
        out.append(compute_forming_session_features(sess, base, vcf))
    return out


def _numba_one(mdf, base, scan_ts_ns, scan_mod, fallback):
    return build_session_columns_nb(
        mdf["timestamp"].astype("int64").to_numpy(),
        mdf["open"].to_numpy(np.float64), mdf["high"].to_numpy(np.float64),
        mdf["low"].to_numpy(np.float64), mdf["close"].to_numpy(np.float64),
        mdf["volume"].to_numpy(np.float64),
        scan_ts_ns, scan_mod, True,
        float(base["avg_volume_20d"]), float(base["prior_atr_14d"]),
        float(base["prior_close"]), float(base["ema_10_prior"]), fallback,
    )


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    n_symbols = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    n_scans = int(sys.argv[2]) if len(sys.argv) > 2 else 78
    n_min = 390
    print(f"numba available: {_NUMBA_AVAILABLE}")
    print(f"batch: {n_symbols} symbols x {n_scans} scans x {n_min} minute bars")

    syms = [_make_symbol(i, n_min) for i in range(n_symbols)]
    start = syms[0][0]["timestamp"].iloc[0]
    step = max(1, (n_min + 30) // n_scans)
    scan_times = [start + pd.Timedelta(minutes=step * i) for i in range(n_scans)]
    scan_ts_ns = np.array([pd.Timestamp(s).tz_convert("UTC").value for s in scan_times], np.int64)
    scan_mod = np.array([_et_minute_of_day(pd.Timestamp(s)) for s in scan_times], np.int64)

    _, t_pure = _timed(lambda: [_pure(m, b, scan_times, _FALLBACK) for m, b in syms])
    # cold (JIT compile on first call)
    _, t_cold = _timed(lambda: [_numba_one(m, b, scan_ts_ns, scan_mod, _FALLBACK) for m, b in syms])
    # warm (cached)
    _, t_warm = _timed(lambda: [_numba_one(m, b, scan_ts_ns, scan_mod, _FALLBACK) for m, b in syms])

    speedup = t_pure / max(t_warm, 1e-9)
    print(f"pure-Python : {t_pure:8.4f} s")
    print(f"numba first : {t_cold:8.4f} s  (includes JIT)")
    print(f"numba warm  : {t_warm:8.4f} s")
    print(f"warm speedup: {speedup:6.1f}x  (target >= 10x)")
    per_session_pure = t_pure
    print(f"per-session feature-compute delta: {per_session_pure - t_warm:.4f} s saved "
          f"({n_symbols} symbols)")


if __name__ == "__main__":
    main()
