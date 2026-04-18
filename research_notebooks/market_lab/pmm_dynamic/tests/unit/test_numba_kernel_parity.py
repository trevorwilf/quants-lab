"""Numba kernel parity tests — Stage 1 of the efficiency/Numba work.

For MR and EMA, each size (small/medium/large), each config: compute features
twice — once with use_numba_kernel=False (pandas replay path) and once with
use_numba_kernel=True (the compiled kernel). Output arrays must match
bit-exactly for booleans and within atol=1e-12 for floats.

Per §2.7 of the prompt, a small pandas reduction-order drift on Bollinger %B
(rolling_std(ddof=0)) may exceed 1e-12 at the 14th decimal. We document and
relax that specific indicator to 1e-10 below. Boolean signal arrays remain
bit-exact.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest


FIX_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "numba_parity"


def _load_mr_fixture(name: str):
    npz = np.load(str(FIX_DIR / f"{name}.npz"), allow_pickle=False)
    cfg_path = FIX_DIR / f"{name}.json"
    with open(cfg_path, encoding="utf-8") as f:
        meta = json.load(f)
    return npz, meta


def _load_ema_fixture(name: str):
    return _load_mr_fixture(name)


def _compare_float(actual: np.ndarray, expected: np.ndarray, atol: float, name: str):
    a = np.asarray(actual, dtype=np.float64)
    e = np.asarray(expected, dtype=np.float64)
    assert a.shape == e.shape, f"{name}: shape mismatch"
    # NaN positions must match
    nan_a = np.isnan(a)
    nan_e = np.isnan(e)
    assert np.array_equal(nan_a, nan_e), f"{name}: NaN positions diverge"
    mask = ~nan_a
    if mask.any():
        np.testing.assert_allclose(
            a[mask], e[mask], atol=atol, rtol=atol,
            err_msg=f"{name}: float mismatch at atol={atol}",
        )


def _compare_bool_via_float(actual: np.ndarray, expected: np.ndarray, name: str):
    """volume_ok / signal / trend_on / vol_ok are stored as float but represent bool.
    Must match bit-exactly."""
    a = np.asarray(actual, dtype=np.float64)
    e = np.asarray(expected, dtype=np.float64)
    assert a.shape == e.shape, f"{name}: shape mismatch"
    np.testing.assert_array_equal(a, e, err_msg=f"{name}: boolean-as-float mismatch")


def _run_mr(fx_name: str):
    from pmm_lab.features.mean_reversion_bb_rsi_features import (
        MRBBRSIFeatureConfig, compute_mr_bb_rsi_features,
    )
    npz, meta = _load_mr_fixture(fx_name)
    cfg = MRBBRSIFeatureConfig(**meta["config"], use_numba_kernel=True)
    out = compute_mr_bb_rsi_features(npz["candles"], cfg)
    return out, npz


def _run_ema(fx_name: str):
    from pmm_lab.features.ema_regime_hold_features import (
        EMARegimeHoldFeatureConfig, compute_ema_regime_hold_features,
    )
    npz, meta = _load_ema_fixture(fx_name)
    cfg = EMARegimeHoldFeatureConfig(**meta["config"], use_numba_kernel=True)
    out = compute_ema_regime_hold_features(npz["candles"], npz["regime_candles"], cfg)
    return out, npz


# ────────────────────────────────────────────────────────────────────────────
# MR parity tests
# ────────────────────────────────────────────────────────────────────────────


MR_FIXTURES_SMALL = ["mr_small_cfg0", "mr_small_cfg1", "mr_small_cfg2"]
MR_FIXTURES_MEDIUM = ["mr_medium_cfg0", "mr_medium_cfg1", "mr_medium_cfg2"]
MR_FIXTURES_LARGE = ["mr_large_cfg0", "mr_large_cfg1", "mr_large_cfg2"]


@pytest.mark.parametrize("name", MR_FIXTURES_SMALL)
def test_mr_numba_parity_small_500bar(name):
    out, npz = _run_mr(name)
    # bbp uses rolling.std — pandas reduction order drifts ~1e-12 at 14th decimal.
    # Relax for bbp specifically (documented per §2.7.3 / §2.8.3).
    _compare_float(out.data["bbp"], npz["bbp"], atol=1e-10, name="bbp")
    _compare_float(out.data["rsi"], npz["rsi"], atol=1e-12, name="rsi")
    _compare_float(out.data["atr_pct"], npz["atr_pct"], atol=1e-12, name="atr_pct")
    _compare_float(out.data["ema_slope"], npz["ema_slope"], atol=1e-12, name="ema_slope")
    _compare_bool_via_float(out.data["volume_ok"], npz["volume_ok"], name="volume_ok")
    _compare_bool_via_float(out.data["signal"], npz["signal"], name="signal")


@pytest.mark.parametrize("name", MR_FIXTURES_MEDIUM)
def test_mr_numba_parity_medium_2000bar(name):
    out, npz = _run_mr(name)
    _compare_float(out.data["bbp"], npz["bbp"], atol=1e-10, name="bbp")
    _compare_float(out.data["rsi"], npz["rsi"], atol=1e-12, name="rsi")
    _compare_float(out.data["atr_pct"], npz["atr_pct"], atol=1e-12, name="atr_pct")
    _compare_float(out.data["ema_slope"], npz["ema_slope"], atol=1e-12, name="ema_slope")
    _compare_bool_via_float(out.data["volume_ok"], npz["volume_ok"], name="volume_ok")
    _compare_bool_via_float(out.data["signal"], npz["signal"], name="signal")


@pytest.mark.parametrize("name", MR_FIXTURES_LARGE)
def test_mr_numba_parity_large_8000bar(name):
    out, npz = _run_mr(name)
    _compare_float(out.data["bbp"], npz["bbp"], atol=1e-10, name="bbp")
    _compare_float(out.data["rsi"], npz["rsi"], atol=1e-12, name="rsi")
    _compare_float(out.data["atr_pct"], npz["atr_pct"], atol=1e-12, name="atr_pct")
    _compare_float(out.data["ema_slope"], npz["ema_slope"], atol=1e-12, name="ema_slope")
    _compare_bool_via_float(out.data["volume_ok"], npz["volume_ok"], name="volume_ok")
    _compare_bool_via_float(out.data["signal"], npz["signal"], name="signal")


# ────────────────────────────────────────────────────────────────────────────
# EMA parity tests
# ────────────────────────────────────────────────────────────────────────────


EMA_FIXTURES_SMALL = ["ema_small_cfg0", "ema_small_cfg1"]
EMA_FIXTURES_MEDIUM = ["ema_medium_cfg0", "ema_medium_cfg1"]
EMA_FIXTURES_LARGE = ["ema_large_cfg0", "ema_large_cfg1"]


@pytest.mark.parametrize("name", EMA_FIXTURES_SMALL)
def test_ema_numba_parity_small_500bar(name):
    out, npz = _run_ema(name)
    _compare_bool_via_float(out.data["signal"], npz["signal"], name="signal")
    _compare_bool_via_float(out.data["trend_on"], npz["trend_on"], name="trend_on")
    _compare_bool_via_float(out.data["vol_ok"], npz["vol_ok"], name="vol_ok")


@pytest.mark.parametrize("name", EMA_FIXTURES_MEDIUM)
def test_ema_numba_parity_medium_2000bar(name):
    out, npz = _run_ema(name)
    _compare_bool_via_float(out.data["signal"], npz["signal"], name="signal")
    _compare_bool_via_float(out.data["trend_on"], npz["trend_on"], name="trend_on")
    _compare_bool_via_float(out.data["vol_ok"], npz["vol_ok"], name="vol_ok")


@pytest.mark.parametrize("name", EMA_FIXTURES_LARGE)
def test_ema_numba_parity_large_8000bar(name):
    out, npz = _run_ema(name)
    _compare_bool_via_float(out.data["signal"], npz["signal"], name="signal")
    _compare_bool_via_float(out.data["trend_on"], npz["trend_on"], name="trend_on")
    _compare_bool_via_float(out.data["vol_ok"], npz["vol_ok"], name="vol_ok")


# ────────────────────────────────────────────────────────────────────────────
# Edge-case tests
# ────────────────────────────────────────────────────────────────────────────


def test_numba_kernel_fallback_when_numba_missing(monkeypatch):
    """With _NUMBA_AVAILABLE=False and use_numba_kernel=True, the compute
    function must still return a valid result via the pandas replay path."""
    import pmm_lab.features._numba_availability as av
    monkeypatch.setattr(av, "_NUMBA_AVAILABLE", False)

    from pmm_lab.features.mean_reversion_bb_rsi_features import (
        MRBBRSIFeatureConfig, compute_mr_bb_rsi_features,
    )
    npz, meta = _load_mr_fixture("mr_small_cfg0")
    cfg = MRBBRSIFeatureConfig(**meta["config"], use_numba_kernel=True)
    out = compute_mr_bb_rsi_features(npz["candles"], cfg)
    # Must produce the same result as the pandas path (it IS the pandas path)
    _compare_bool_via_float(out.data["signal"], npz["signal"], name="signal")


def test_existing_mr_short_100bar_fixture_with_numba_flag_on():
    """The pre-existing MR parity fixture must still pass with the Numba flag ON."""
    from pmm_lab.parity.feature_parity import check_feature_parity_frozen_mr
    from pmm_lab.parity.fixtures import load_frozen_fixture

    fx_dir = Path(__file__).resolve().parents[2] / "fixtures" / "mr_short_100bar"
    fx = load_frozen_fixture(str(fx_dir))
    # Add use_numba_kernel=True to the config
    cfg = dict(fx.config_params)
    cfg["use_numba_kernel"] = True
    result = check_feature_parity_frozen_mr(fx.candles, fx.expected_features, cfg)
    assert result.passed, (
        f"MR short_100bar fixture must pass with Numba flag ON. "
        f"Mismatches: {result.mismatches[:3]}"
    )


def test_mr_signal_array_exact_match_numba_vs_replay():
    """Cross-check: signal (boolean) must match bit-exactly on a fresh 2000-bar seed."""
    from pmm_lab.features.mean_reversion_bb_rsi_features import (
        MRBBRSIFeatureConfig, compute_mr_bb_rsi_features,
    )
    npz, meta = _load_mr_fixture("mr_medium_cfg1")
    cfg_pd = MRBBRSIFeatureConfig(**meta["config"], use_numba_kernel=False)
    cfg_nb = replace(cfg_pd, use_numba_kernel=True)
    out_pd = compute_mr_bb_rsi_features(npz["candles"], cfg_pd)
    out_nb = compute_mr_bb_rsi_features(npz["candles"], cfg_nb)
    np.testing.assert_array_equal(
        out_nb.data["signal"], out_pd.data["signal"],
        err_msg="MR signal (boolean) must be bit-exact between numba and replay",
    )


def test_ema_trend_on_exact_match_numba_vs_replay():
    """Cross-check: trend_on must match bit-exactly on a 2000-bar EMA fixture."""
    from pmm_lab.features.ema_regime_hold_features import (
        EMARegimeHoldFeatureConfig, compute_ema_regime_hold_features,
    )
    npz, meta = _load_ema_fixture("ema_medium_cfg0")
    cfg_pd = EMARegimeHoldFeatureConfig(**meta["config"], use_numba_kernel=False)
    cfg_nb = replace(cfg_pd, use_numba_kernel=True)
    out_pd = compute_ema_regime_hold_features(npz["candles"], npz["regime_candles"], cfg_pd)
    out_nb = compute_ema_regime_hold_features(npz["candles"], npz["regime_candles"], cfg_nb)
    np.testing.assert_array_equal(
        out_nb.data["trend_on"], out_pd.data["trend_on"],
        err_msg="EMA trend_on must be bit-exact between numba and replay",
    )
    np.testing.assert_array_equal(
        out_nb.data["signal"], out_pd.data["signal"],
        err_msg="EMA signal must be bit-exact between numba and replay",
    )
