"""Pre-warm the on-disk numba cache for the walk-forward scan-feature kernels.

Every kernel is ``@njit(cache=True)``: the FIRST call in a process pays the JIT
compile and writes the compiled artifact to numba's on-disk cache; later calls
(and other processes) load the artifact instead of recompiling. Under a spawned
Optuna worker pool each of the N workers would otherwise pay first-call JIT.

Run this ONCE per environment, and again after any kernel change or numba
upgrade (the cache is keyed by the kernel source + numba/llvm versions, so a
stale cache is simply ignored and recompiled).

    cd research_notebooks/bowaka_v2_lab
    pip install -e .[numba]
    PYTHONPATH=src:../bowaka_common/src python scripts/warm_numba_cache.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

_LAB_ROOT = Path(__file__).resolve().parents[1]
if str(_LAB_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_LAB_ROOT / "src"))

from bowaka_v2_lab.features._numba_scan_features import (  # noqa: E402
    _NUMBA_AVAILABLE,
    _ewm_mean_series,
    _fallback_curve_fraction_nb,
    _forming_features_nb,
    build_session_columns_nb,
    compute_baselines_nb,
)


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    if not _NUMBA_AVAILABLE:
        print("numba is NOT installed — kernels run interpreted (no on-disk cache "
              "to warm). Install with: pip install -e .[numba]")
        return

    t0 = time.perf_counter()
    n = 24
    close = np.linspace(100.0, 110.0, n)
    high = close + 0.5
    low = close - 0.5
    vol = np.full(n, 1.0e5)

    _ewm_mean_series(close, 2.0 / 11.0, 0)
    _fallback_curve_fraction_nb(120, 0.08)
    _forming_features_nb(1000.0, 1.0, 101.0, 99.0, 100.5, 100.0, 0.3,
                         3.0e5, 1.2, 99.0, 100.0)
    compute_baselines_nb(close, high, low, vol, 14, 20, 10, 3)

    bar_ts = np.arange(n, dtype=np.int64) * 60_000_000_000
    scan_ts = np.array([5, 15, 23], dtype=np.int64) * 60_000_000_000
    scan_mod = np.array([5, 15, 23], dtype=np.int64)
    build_session_columns_nb(
        bar_ts, close, high, low, close, vol, scan_ts, scan_mod, True,
        3.0e5, 1.2, 99.0, 100.0, 0.08,
    )

    print(f"numba kernel cache warmed in {time.perf_counter() - t0:.2f}s "
          f"(5 kernels compiled + cached). Subsequent processes load the artifact.")


if __name__ == "__main__":
    main()
