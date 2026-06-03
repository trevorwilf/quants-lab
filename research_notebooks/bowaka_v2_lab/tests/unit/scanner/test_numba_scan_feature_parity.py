"""Phase 1 (walk-forward numba) — kernel vs committed pure-Python fixtures.

Loads the seeded fixtures under ``tests/fixtures/numba_scan_features/`` (whose
expected arrays were produced by the PURE-PYTHON ``forming_bar`` path) and runs
the compiled kernels: booleans/ints bit-exact, floats ``atol<=1e-10`` with NaN
positions compared separately (market_lab pattern). When numba is not installed
the kernels run interpreted with identical semantics, so this still validates the
math. Regenerate with ``scripts/generate_numba_scan_feature_fixtures.py``.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from bowaka_v2_lab.features._numba_scan_features import (
    _NUMBA_AVAILABLE,
    build_session_columns_nb,
    compute_baselines_nb,
)

_FIX = Path(__file__).resolve().parents[2] / "fixtures" / "numba_scan_features"
_SIZES = ["small", "medium", "large"]


def _load(size: str):
    npz = np.load(str(_FIX / f"scan_features_{size}.npz"), allow_pickle=False)
    meta = json.loads((_FIX / f"scan_features_{size}.json").read_text(encoding="utf-8"))
    return npz, meta


def _cmp_float(actual: np.ndarray, expected: np.ndarray, *, atol: float, rtol: float) -> None:
    assert actual.shape == expected.shape
    nan_a = np.isnan(actual)
    nan_e = np.isnan(expected)
    assert np.array_equal(nan_a, nan_e), "NaN positions differ"
    mask = ~nan_e
    if mask.any():
        np.testing.assert_allclose(actual[mask], expected[mask], atol=atol, rtol=rtol)


def test_numba_availability_flag_is_bool() -> None:
    # Informational: parity holds whether numba is installed (compiled) or not
    # (interpreted via the njit no-op).
    assert _NUMBA_AVAILABLE in (True, False)


@pytest.mark.parametrize("size", _SIZES)
def test_baselines_kernel_matches_pure_python(size: str) -> None:
    npz, meta = _load(size)
    out = compute_baselines_nb(
        npz["daily_close"], npz["daily_high"], npz["daily_low"], npz["daily_volume"],
        int(meta["atr_n"]), int(meta["lookback"]), int(meta["ema_n"]),
        int(meta["ema_slope_lookback"]),
    )
    exp = npz["base_expected"]
    # rtol covers the ~1e-16 relative drift on the large-magnitude
    # avg_dollar_volume_20d sum (sequential vs numpy pairwise); the recursive EMA
    # baselines are bit-exact.
    _cmp_float(np.asarray(out, dtype=np.float64), exp, atol=1e-10, rtol=1e-9)


@pytest.mark.parametrize("size", _SIZES)
def test_build_columns_kernel_matches_pure_python(size: str) -> None:
    npz, meta = _load(size)
    res = build_session_columns_nb(
        npz["bar_ts_ns"], npz["bar_open"], npz["bar_high"], npz["bar_low"],
        npz["bar_close"], npz["bar_volume"],
        npz["scan_ts_ns"], npz["scan_minute_of_day"], True,
        float(npz["avg_volume_20d"]), float(npz["prior_atr_14d"]),
        float(npz["prior_close"]), float(npz["ema_10_prior"]),
        float(meta["fallback_share"]),
    )
    (hb, hv, hbl, tsn, so, sh, sl, sla, sv, sr, ba,
     vcf, expv, rvol, proj, rexp, cloc, edist, cret, gap) = res

    # Bools / ints: bit-exact.
    np.testing.assert_array_equal(np.asarray(hb), npz["has_bar"])
    np.testing.assert_array_equal(np.asarray(hv), npz["has_valid_ts"])
    np.testing.assert_array_equal(np.asarray(hbl), npz["has_baseline"])
    np.testing.assert_array_equal(np.asarray(tsn), npz["last_bar_ts_ns"])

    # Floats: atol<=1e-10 (session_volume's sequential sum drifts ~1e-13).
    for arr, key in [
        (so, "s_open"), (sh, "s_high"), (sl, "s_low"), (sla, "s_last"),
        (sv, "s_vol"), (sr, "s_range"), (ba, "bar_age"), (vcf, "vcf"),
        (expv, "expv"), (rvol, "rvol"), (proj, "proj"), (rexp, "rexp"),
        (cloc, "cloc"), (edist, "edist"), (cret, "cret"), (gap, "gap"),
    ]:
        _cmp_float(np.asarray(arr, dtype=np.float64), npz[key], atol=1e-10, rtol=1e-10)
