"""Tests that `USE_NUMBA_KERNEL=True` is enabled in the sweep notebooks AND
propagates end-to-end from strategy config → feature config → kernel dispatch.

The dataclass defaults stay `use_numba_kernel=False`. The notebook turns the
flag ON via a top-level constant, and every `_replace(...)` call on a
directional strategy config threads it through.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest


_ROOT = Path(__file__).resolve().parents[2]
_LEGACY_CELL8 = _ROOT / "notebooks" / "direction-custom" / "_legacy" / "_build_cell8.py"
_NOTEBOOKS = [
    _ROOT / "notebooks" / "direction-custom" / "mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb",
    _ROOT / "notebooks" / "direction-custom" / "mean_reversion_bb_rsi_retest_sweep.ipynb",
    _ROOT / "notebooks" / "direction-custom" / "ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb",
    _ROOT / "notebooks" / "direction-custom" / "ema_regime_hold_retest_sweep.ipynb",
]


# ────────────────────────────────────────────────────────────────────────────
# 1. Flag is present in the notebook generator AND in every committed .ipynb
# ────────────────────────────────────────────────────────────────────────────


def test_notebook_cell_code_enables_numba_flag():
    """The generator `_build_cell8.py` (and every committed .ipynb) defines
    `USE_NUMBA_KERNEL = True` and threads it through every directional
    `_replace(...)` that also sets `controller_compat=...`."""
    # Generator file — source-of-truth for cell 8 structure
    src = _LEGACY_CELL8.read_text(encoding="utf-8")
    assert "USE_NUMBA_KERNEL = True" in src, (
        "_build_cell8.py must define USE_NUMBA_KERNEL = True at module level"
    )

    # Every _replace(...) that references controller_compat=PHASE2_CONTROLLER_COMPAT
    # or controller_compat=VALIDATION_CONTROLLER_COMPAT and operates on a directional
    # strategy config must also reference use_numba_kernel=USE_NUMBA_KERNEL.
    #
    # We match across lines — the EMA multi-line _replace blocks span 4-5 lines.
    # A simple regex pattern matches each _replace(...) parenthesized call.
    # For robustness, enumerate each directional _replace block and check flag presence.
    bad_sites: list[str] = []
    # Find each _replace( on a strategy_config or best_config, grab up to 6 lines.
    for m in re.finditer(
        r"_replace\(\s*(?:bundle\.strategy_config|best_config|tc_bundle\.strategy_config)",
        src,
    ):
        start = src.rfind("\n", 0, m.start()) + 1
        end = src.find(")", m.start())
        # Handle multi-line _replace
        while end != -1:
            opened = src.count("(", m.start(), end + 1)
            closed = src.count(")", m.start(), end + 1)
            if opened == closed:
                break
            end = src.find(")", end + 1)
        if end == -1:
            end = m.start() + 400
        snippet = src[start:end + 1]
        if "controller_compat=" not in snippet:
            # Not a directional config-replace site
            continue
        if "use_numba_kernel=USE_NUMBA_KERNEL" not in snippet:
            bad_sites.append(snippet.strip())
    assert not bad_sites, (
        "Found _replace(...) on directional strategy config(s) without "
        "use_numba_kernel=USE_NUMBA_KERNEL. Offenders:\n" +
        "\n---\n".join(bad_sites[:3])
    )


@pytest.mark.parametrize("nb_path", _NOTEBOOKS)
def test_committed_notebook_has_flag_enabled(nb_path):
    """Every committed .ipynb has `USE_NUMBA_KERNEL = True` in a config cell
    and threads the flag through every directional `_replace` in cell 8."""
    with open(nb_path, encoding="utf-8") as f:
        nb = json.load(f)
    # Find cell that defines USE_NUMBA_KERNEL
    all_code = []
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = cell["source"]
        if isinstance(src, list):
            src = "".join(src)
        all_code.append(src)
    combined = "\n".join(all_code)
    assert "USE_NUMBA_KERNEL = True" in combined, (
        f"{nb_path.name}: notebook missing USE_NUMBA_KERNEL = True"
    )

    # Every directional _replace must reference use_numba_kernel=USE_NUMBA_KERNEL
    for m in re.finditer(
        r"_replace\(\s*(?:bundle\.strategy_config|best_config|tc_bundle\.strategy_config)",
        combined,
    ):
        end = m.start()
        opened = 0
        closed = 0
        while end < len(combined):
            if combined[end] == "(":
                opened += 1
            elif combined[end] == ")":
                closed += 1
                if opened == closed:
                    break
            end += 1
        snippet = combined[m.start(): end + 1]
        if "controller_compat=" not in snippet:
            continue
        assert "use_numba_kernel=USE_NUMBA_KERNEL" in snippet, (
            f"{nb_path.name}: _replace without use_numba_kernel: {snippet[:200]}"
        )


# ────────────────────────────────────────────────────────────────────────────
# 2. Flag propagates through compute_signals (strategy → feature config)
# ────────────────────────────────────────────────────────────────────────────


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


def test_numba_flag_propagates_through_compute_signals_mr(monkeypatch):
    """MR: flag=True on strategy config must yield use_numba_kernel=True on the
    feature config passed into compute_mr_bb_rsi_features."""
    from pmm_lab.strategies.mean_reversion_bb_rsi import (
        MeanReversionBBRSIStrategy, MeanReversionBBRSIStrategyConfig,
    )
    import pmm_lab.strategies.mean_reversion_bb_rsi as mr_mod

    captured = {}

    def _spy(candles, feat_cfg):
        captured["feat_cfg"] = feat_cfg
        # Return a minimal SignalOutput
        from pmm_lab.sim.strategy import SignalOutput
        n = len(candles)
        return SignalOutput(warmup_end=0, data={
            "signal": np.zeros(n, dtype=np.float64),
            "bbp": np.zeros(n, dtype=np.float64),
            "rsi": np.zeros(n, dtype=np.float64),
            "atr_pct": np.zeros(n, dtype=np.float64),
            "ema_slope": np.zeros(n, dtype=np.float64),
            "volume_ok": np.zeros(n, dtype=np.float64),
            "close_price": candles["close"].astype("float64"),
            "timestamp": candles["timestamp"].astype("float64"),
        })

    monkeypatch.setattr(mr_mod, "compute_mr_bb_rsi_features", _spy)
    cfg = MeanReversionBBRSIStrategyConfig(use_numba_kernel=True, controller_compat=True)
    strat = MeanReversionBBRSIStrategy(cfg)
    strat.compute_signals(_make_candles(200))
    assert captured["feat_cfg"].use_numba_kernel is True


def test_numba_flag_propagates_through_compute_signals_ema(monkeypatch):
    """EMA: flag=True on strategy config yields use_numba_kernel=True on the
    feature config passed into compute_ema_regime_hold_features."""
    from pmm_lab.strategies.ema_regime_hold import (
        EMARegimeHoldStrategy, EMARegimeHoldStrategyConfig,
    )
    import pmm_lab.strategies.ema_regime_hold as ema_mod

    captured = {}

    def _spy(signal_candles, regime_candles, feat_cfg):
        captured["feat_cfg"] = feat_cfg
        from pmm_lab.sim.strategy import SignalOutput
        n = len(signal_candles)
        return SignalOutput(warmup_end=0, data={
            "signal": np.zeros(n, dtype=np.float64),
            "trend_on": np.zeros(n, dtype=np.float64),
            "vol_ok": np.zeros(n, dtype=np.float64),
            "close_price": signal_candles["close"].astype("float64"),
            "timestamp": signal_candles["timestamp"].astype("float64"),
        })

    monkeypatch.setattr(ema_mod, "compute_ema_regime_hold_features", _spy)
    regime = _make_candles(50, seed=7)
    cfg = EMARegimeHoldStrategyConfig(
        use_numba_kernel=True, controller_compat=True,
    )
    cfg = replace(cfg, _regime_candles=regime)
    strat = EMARegimeHoldStrategy(cfg)
    strat.compute_signals(_make_candles(200))
    assert captured["feat_cfg"].use_numba_kernel is True


# ────────────────────────────────────────────────────────────────────────────
# 3. Dataclass defaults are preserved
# ────────────────────────────────────────────────────────────────────────────


def test_numba_flag_off_by_default_on_dataclass():
    """Library-level defaults remain OFF. The notebook opts in explicitly."""
    from pmm_lab.features.mean_reversion_bb_rsi_features import MRBBRSIFeatureConfig
    from pmm_lab.features.ema_regime_hold_features import EMARegimeHoldFeatureConfig
    from pmm_lab.strategies.mean_reversion_bb_rsi import MeanReversionBBRSIStrategyConfig
    from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig

    assert MRBBRSIFeatureConfig().use_numba_kernel is False
    assert EMARegimeHoldFeatureConfig().use_numba_kernel is False
    assert MeanReversionBBRSIStrategyConfig().use_numba_kernel is False
    assert EMARegimeHoldStrategyConfig().use_numba_kernel is False


def test_numba_flag_off_produces_pandas_path(monkeypatch):
    """With use_numba_kernel=False (even when Numba is installed), the Numba
    kernel entry point is NOT called."""
    from pmm_lab.features.mean_reversion_bb_rsi_features import (
        MRBBRSIFeatureConfig, compute_mr_bb_rsi_features,
    )
    import pmm_lab.features._numba_mr_bb_rsi as nb_mod

    called = {"n": 0}
    real = nb_mod.compute_controller_compat_mr_numba

    def _counter(*args, **kw):
        called["n"] += 1
        return real(*args, **kw)

    monkeypatch.setattr(nb_mod, "compute_controller_compat_mr_numba", _counter)

    cfg = MRBBRSIFeatureConfig(
        bb_length=20, bb_std=2.0, bbp_entry_threshold=0.15,
        rsi_length=14, rsi_entry_threshold=35.0,
        use_trend_filter=False, trend_ema_length=50,
        atr_length=14, max_atr_pct_for_entry=0.10,
        volume_filter_window=30, min_volume_quantile=0.0,
        timestamp_mode="open", controller_compat=True,
        use_numba_kernel=False,  # <-- OFF
    )
    compute_mr_bb_rsi_features(_make_candles(300), cfg)
    assert called["n"] == 0, (
        "With use_numba_kernel=False, the Numba kernel must NOT be invoked"
    )

    # Sanity: with flag ON the kernel IS invoked
    cfg_on = replace(cfg, use_numba_kernel=True)
    compute_mr_bb_rsi_features(_make_candles(300), cfg_on)
    assert called["n"] >= 1, "With use_numba_kernel=True, kernel must run"
