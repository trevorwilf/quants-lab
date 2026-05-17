"""Phase 3: compute_daily_features against frozen golden output."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bowaka_lab.config.models import PrefilterConfig, ScoreConfig
from bowaka_lab.features.daily_features import compute_daily_features


@pytest.fixture(scope="module")
def fixture_bars(fixtures_dir: Path) -> pd.DataFrame:
    return pd.read_parquet(fixtures_dir / "daily_bars_small.parquet")


@pytest.fixture(scope="module")
def expected_features(fixtures_dir: Path) -> dict:
    return json.loads((fixtures_dir / "expected_features.json").read_text())


@pytest.fixture(scope="module")
def cfg() -> PrefilterConfig:
    return PrefilterConfig(
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


def test_features_match_expected(fixture_bars, expected_features, cfg):
    signal_date = pd.Timestamp(expected_features["signal_date"]).date()
    feats = compute_daily_features(fixture_bars, cfg, signal_date=signal_date)
    feats_records = feats.reset_index().to_dict(orient="records")

    by_symbol = {r["symbol"]: r for r in feats_records}
    for expected in expected_features["rows"]:
        actual = by_symbol[expected["symbol"]]
        for key in ("close", "rvol", "atr_pct", "range_expansion", "close_location", "ema_distance", "ema_slope"):
            ev = expected[key]
            av = actual[key]
            if ev is None or (isinstance(ev, float) and np.isnan(ev)):
                assert av is None or (isinstance(av, float) and np.isnan(av))
            else:
                assert abs(float(av) - float(ev)) < 1e-9, f"{expected['symbol']}.{key}: {av} != {ev}"


def test_no_lookahead_invariant_holds(fixture_bars, cfg):
    signal_date = fixture_bars["session_date"].max()
    feats = compute_daily_features(fixture_bars, cfg, signal_date=signal_date)
    assert (feats["latest_bar_date"] <= signal_date).all()


def test_empty_bars_returns_empty():
    feats = compute_daily_features(pd.DataFrame(), PrefilterConfig(price_min=1.0, price_max=20.0), signal_date=date(2026, 5, 15))
    assert feats.empty


def test_dropping_signal_date_bar_changes_features(fixture_bars, cfg):
    signal_date = fixture_bars["session_date"].max()
    feats_all = compute_daily_features(fixture_bars, cfg, signal_date=signal_date)
    earlier = fixture_bars[fixture_bars["session_date"] < signal_date]
    earlier_signal = earlier["session_date"].max()
    feats_earlier = compute_daily_features(fixture_bars, cfg, signal_date=earlier_signal)
    # Different signal date should produce different rvol for at least one symbol.
    diffs = (feats_all["rvol"].fillna(-1) - feats_earlier["rvol"].fillna(-1)).abs()
    assert diffs.sum() > 0


def test_required_columns_present(fixture_bars, cfg):
    signal_date = fixture_bars["session_date"].max()
    feats = compute_daily_features(fixture_bars, cfg, signal_date=signal_date)
    for col in (
        "close",
        "rvol",
        "atr",
        "atr_pct",
        "gap_pct",
        "range_expansion",
        "close_location",
        "ema",
        "ema_distance",
        "ema_slope",
        "avg_dollar_volume",
    ):
        assert col in feats.columns


def test_missing_required_column_raises():
    bad = pd.DataFrame({"symbol": ["X"], "open": [1.0], "high": [1.1], "low": [0.9], "close": [1.0]})
    with pytest.raises(ValueError, match="missing required column"):
        compute_daily_features(bad, PrefilterConfig(price_min=1.0, price_max=20.0), signal_date=date(2026, 5, 15))
