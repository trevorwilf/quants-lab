"""Phase 3: parity test against legacy ``bowaka_prefilter.py``.

Skipped unless ``BOWAKA_SOURCE_STRATEGY_ROOT`` is set. The env var must point
to a directory containing ``scripts/bowaka_prefilter.py`` — typically the
openalgo strategies checkout.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bowaka_lab.config.models import PrefilterConfig, ScoreConfig
from bowaka_lab.features.daily_features import compute_daily_features


def _legacy_module():
    root = os.environ.get("BOWAKA_SOURCE_STRATEGY_ROOT")
    if not root:
        pytest.skip("BOWAKA_SOURCE_STRATEGY_ROOT not set")
    legacy_path = Path(root) / "scripts" / "bowaka_prefilter.py"
    if not legacy_path.exists():
        pytest.skip(f"Legacy script not found at {legacy_path}")
    spec = importlib.util.spec_from_file_location("legacy_bowaka_prefilter", legacy_path)
    if spec is None or spec.loader is None:
        pytest.skip("Cannot load legacy module")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["legacy_bowaka_prefilter"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_compute_features_parity(fixtures_dir: Path):
    legacy = _legacy_module()
    bars = pd.read_parquet(fixtures_dir / "daily_bars_small.parquet")
    # Legacy expects a MultiIndex (symbol, timestamp). Build it.
    legacy_input = bars.copy().set_index(["symbol", "timestamp"]).sort_index()

    legacy_cfg = {
        "indicators": {
            "lookback_days": 10,
            "atr_days": 7,
            "ema_days": 5,
            "ema_slope_lookback": 2,
        }
    }
    legacy_features = legacy.compute_features(legacy_input, legacy_cfg)

    cfg = PrefilterConfig(
        lookback_days=10,
        atr_days=7,
        ema_days=5,
        ema_slope_lookback=2,
        price_min=1.0,
        price_max=100.0,
        avg_dollar_volume_min=None,
        rvol_min=None,
        atr_pct_min=None,
        range_expansion_min=None,
        close_location_min=None,
        ema_distance_min=None,
        ema_slope_min=None,
        score=ScoreConfig(bounded=False),
    )
    signal_date = bars["session_date"].max()
    new_features = compute_daily_features(bars, cfg, signal_date=signal_date)

    feature_cols = ("rvol", "atr_pct", "range_expansion", "close_location", "ema_distance", "ema_slope", "avg_dollar_volume")
    for col in feature_cols:
        for sym in legacy_features.index:
            if sym not in new_features.index:
                continue
            legacy_val = legacy_features.loc[sym, col]
            new_val = new_features.loc[sym, col]
            if pd.isna(legacy_val) and pd.isna(new_val):
                continue
            assert abs(float(legacy_val) - float(new_val)) < 1e-9, (
                f"feature parity broken for {sym}.{col}: legacy={legacy_val} new={new_val}"
            )
