"""Generate MR and EMA parity fixtures at small/medium/large sizes.

Computes the pandas replay-path output (use_numba_kernel=False) and stores
candles + full output arrays in .npz, with a JSON sidecar holding the config.

The Numba parity tests load each fixture and compare the Numba kernel's
output against these pandas-path values at atol=1e-12 tolerance.

Run once, commit the resulting `fixtures/numba_parity/*` files:
    python scripts/generate_numba_parity_fixtures.py
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
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


def _make_candles(n: int, seed: int, dt_seconds: int, start_ts: int = 1_700_000_000) -> np.ndarray:
    rng = np.random.default_rng(seed)
    rows = []
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
        rows.append((start_ts + i * dt_seconds, op, hi, lo, cl, rng.uniform(0.5, 3.0), False))
        price = cl
    return np.array(rows, dtype=CANDLE_DTYPE)


MR_CONFIGS = [
    {
        "bb_length": 20, "bb_std": 2.0, "bbp_entry_threshold": 0.15,
        "rsi_length": 14, "rsi_entry_threshold": 35.0,
        "use_trend_filter": False, "trend_ema_length": 50,
        "min_trend_slope": 0.0, "atr_length": 14, "max_atr_pct_for_entry": 0.10,
        "volume_filter_window": 30, "min_volume_quantile": 0.0,
        "timestamp_mode": "open", "controller_compat": True,
    },
    {
        "bb_length": 80, "bb_std": 2.0, "bbp_entry_threshold": 0.20,
        "rsi_length": 14, "rsi_entry_threshold": 40.0,
        "use_trend_filter": True, "trend_ema_length": 200,
        "min_trend_slope": 0.0, "atr_length": 14, "max_atr_pct_for_entry": 0.10,
        "volume_filter_window": 50, "min_volume_quantile": 0.30,
        "timestamp_mode": "open", "controller_compat": True,
    },
    {
        "bb_length": 40, "bb_std": 2.5, "bbp_entry_threshold": 0.25,
        "rsi_length": 21, "rsi_entry_threshold": 45.0,
        "use_trend_filter": True, "trend_ema_length": 100,
        "min_trend_slope": 0.0, "atr_length": 14, "max_atr_pct_for_entry": 0.08,
        "volume_filter_window": 288, "min_volume_quantile": 0.25,
        "timestamp_mode": "open", "controller_compat": True,
    },
]


EMA_CONFIGS = [
    {
        "regime_ema_fast": 10, "regime_ema_slow": 30,
        "regime_adx_length": 14, "regime_adx_threshold": 20.0,
        "volume_filter_window": 30, "min_volume_quantile": 0.0,
        "hold_mode": "reentry", "timestamp_mode": "open",
        "controller_compat": True,
    },
    {
        "regime_ema_fast": 50, "regime_ema_slow": 200,
        "regime_adx_length": 14, "regime_adx_threshold": 20.0,
        "volume_filter_window": 288, "min_volume_quantile": 0.30,
        "hold_mode": "reentry", "timestamp_mode": "open",
        "controller_compat": True,
    },
]


SIZES = [("small", 500), ("medium", 2000), ("large", 8000)]


def generate_mr_fixture(out_dir: Path, size_name: str, n_bars: int, cfg_idx: int, cfg: dict):
    from pmm_lab.features.mean_reversion_bb_rsi_features import (
        MRBBRSIFeatureConfig, compute_mr_bb_rsi_features,
    )
    candles = _make_candles(n_bars, seed=42 + cfg_idx, dt_seconds=300)
    feature_cfg = MRBBRSIFeatureConfig(**cfg, use_numba_kernel=False)
    out = compute_mr_bb_rsi_features(candles, feature_cfg)

    fixture_path = out_dir / f"mr_{size_name}_cfg{cfg_idx}.npz"
    cfg_path = fixture_path.with_suffix(".json")

    np.savez(
        fixture_path,
        candles=candles,
        signal=np.asarray(out.data["signal"], dtype=np.float64),
        bbp=np.asarray(out.data["bbp"], dtype=np.float64),
        rsi=np.asarray(out.data["rsi"], dtype=np.float64),
        atr_pct=np.asarray(out.data["atr_pct"], dtype=np.float64),
        ema_slope=np.asarray(out.data["ema_slope"], dtype=np.float64),
        volume_ok=np.asarray(out.data["volume_ok"], dtype=np.float64),
        close_price=np.asarray(out.data["close_price"], dtype=np.float64),
        timestamp=np.asarray(out.data["timestamp"], dtype=np.float64),
        warmup_end=np.int64(out.warmup_end),
    )
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump({"type": "mr", "size": size_name, "n_bars": n_bars, "config": cfg}, f, indent=2)
    print(f"wrote {fixture_path} (n={n_bars}, cfg{cfg_idx})")


def generate_ema_fixture(out_dir: Path, size_name: str, n_bars: int, cfg_idx: int, cfg: dict):
    from pmm_lab.features.ema_regime_hold_features import (
        EMARegimeHoldFeatureConfig, compute_ema_regime_hold_features,
    )
    # Fast at 5m (300s), regime at 20m (1200s) — 4x ratio
    fast = _make_candles(n_bars, seed=42 + cfg_idx, dt_seconds=300)
    # Regime = n_bars // 4 bars to cover the same time span
    regime = _make_candles(max(n_bars // 4, 50), seed=142 + cfg_idx, dt_seconds=1200)
    feature_cfg = EMARegimeHoldFeatureConfig(**cfg, use_numba_kernel=False)
    out = compute_ema_regime_hold_features(fast, regime, feature_cfg)

    fixture_path = out_dir / f"ema_{size_name}_cfg{cfg_idx}.npz"
    cfg_path = fixture_path.with_suffix(".json")

    np.savez(
        fixture_path,
        candles=fast,
        regime_candles=regime,
        signal=np.asarray(out.data["signal"], dtype=np.float64),
        trend_on=np.asarray(out.data["trend_on"], dtype=np.float64),
        vol_ok=np.asarray(out.data["vol_ok"], dtype=np.float64),
        close_price=np.asarray(out.data["close_price"], dtype=np.float64),
        timestamp=np.asarray(out.data["timestamp"], dtype=np.float64),
        warmup_end=np.int64(out.warmup_end),
    )
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump({"type": "ema", "size": size_name, "n_bars": n_bars, "config": cfg}, f, indent=2)
    print(f"wrote {fixture_path} (n={n_bars}, cfg{cfg_idx})")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(__file__).resolve().parent.parent
    out_dir = root / "fixtures" / "numba_parity"
    out_dir.mkdir(parents=True, exist_ok=True)

    for size_name, n in SIZES:
        for idx, cfg in enumerate(MR_CONFIGS):
            generate_mr_fixture(out_dir, size_name, n, idx, cfg)
        for idx, cfg in enumerate(EMA_CONFIGS):
            generate_ema_fixture(out_dir, size_name, n, idx, cfg)


if __name__ == "__main__":
    main()
