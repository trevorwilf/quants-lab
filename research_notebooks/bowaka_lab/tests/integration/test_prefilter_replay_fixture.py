"""Phase 3: end-to-end prefilter replay against expected_candidates.json."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from bowaka_lab.config.models import PrefilterConfig, ScoreConfig, UniverseConfig
from bowaka_lab.features.daily_features import compute_daily_features
from bowaka_lab.features.prefilter import apply_prefilter


def test_replay_matches_expected(fixtures_dir: Path):
    bars = pd.read_parquet(fixtures_dir / "daily_bars_small.parquet")
    expected = json.loads((fixtures_dir / "expected_candidates.json").read_text())
    signal_date = pd.Timestamp(expected["signal_date"]).date()

    cfg = PrefilterConfig(
        lookback_days=10,
        atr_days=7,
        ema_days=5,
        ema_slope_lookback=2,
        price_min=1.0,
        price_max=30.0,
        avg_dollar_volume_min=100_000,
        rvol_min=None,
        atr_pct_min=None,
        range_expansion_min=None,
        close_location_min=None,
        ema_distance_min=None,
        ema_slope_min=None,
        score=ScoreConfig(bounded=False),
    )
    universe = UniverseConfig()
    feats = compute_daily_features(bars, cfg, signal_date=signal_date)
    cset = apply_prefilter(feats, cfg, signal_date=signal_date, trade_date=signal_date + timedelta(days=1), universe=universe)

    actual_metadata = cset.metadata
    assert actual_metadata["n_universe_with_features"] == expected["metadata"]["n_universe_with_features"]
    assert actual_metadata["n_candidates"] == expected["metadata"]["n_candidates"]

    expected_symbols = [r["symbol"] for r in expected["candidates"]]
    actual_symbols = cset.candidates.reset_index()["symbol"].tolist()
    assert actual_symbols == expected_symbols
