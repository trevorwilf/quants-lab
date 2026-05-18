"""Phase 3: parity test against legacy ``bowaka_prefilter.py``.

The ``compute_features`` parity branch is skipped unless
``BOWAKA_SOURCE_STRATEGY_ROOT`` is set (it depends on importing the full
legacy module which pulls Alpaca SDK deps).

Phase fidelity-2 adds ``classify_instrument`` parity tests, which run
against a verbatim excerpt of the source function under
``tests/fixtures/source_classify_instrument.py``. These do not depend on
the env var and always run.
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
from bowaka_lab.features.instrument_classification import (
    DEFAULT_NAME_KEYWORDS,
    classify_instrument as lab_classify,
)
from tests.fixtures.source_classify_instrument import (
    classify_instrument as source_classify,
)


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


# ----------------------------------------------------------------------------
# Phase fidelity-2: classify_instrument parity (verbatim source excerpt).
# ----------------------------------------------------------------------------

_SOURCE_CFG = {
    "instrument_rules": {
        "ticker_blocklist": ["TSLL", "CONL", "SMCX"],
        "name_keywords": DEFAULT_NAME_KEYWORDS,
    }
}

_FIXTURE_ROWS = [
    # (symbol, name, asset_class, expected_label)
    ("AAPL",    "APPLE INC",                          "us_equity", "operating_equity"),
    ("SPXS",    "DIREXION DAILY S&P 500 BEAR 3X",     "us_equity", "leveraged_etp"),
    ("SH",      "PROSHARES SHORT S&P500",             "us_equity", "inverse_etp"),
    ("DJP",     "IPATH BLOOMBERG COMMODITY ETN",      "us_equity", "etn"),
    ("TSLL",    "DIREXION DAILY TSLA BULL 1.5X",      "us_equity", "leveraged_etp"),
    ("UNKNOWN", "",                                   "us_equity", "operating_equity"),
    ("ETF1",    "QQQ TRUST",                          "etf",       "etf"),
    ("ETF2",    "QQQ TRUST",                          "us_etf",    "etf"),
    ("ZZZZ",    None,                                 None,        "operating_equity"),
]


@pytest.mark.parametrize("symbol,name,asset_class,expected", _FIXTURE_ROWS)
def test_classify_instrument_matches_source(symbol, name, asset_class, expected):
    lab_out = lab_classify(
        symbol,
        name=name,
        asset_class=asset_class,
        ticker_blocklist=_SOURCE_CFG["instrument_rules"]["ticker_blocklist"],
    )
    src_out = source_classify(symbol, {"name": name, "asset_class": asset_class}, _SOURCE_CFG)
    assert lab_out.instrument_class == src_out["instrument_class"], (
        f"{symbol}: lab={lab_out.instrument_class!r} vs source={src_out['instrument_class']!r}"
    )
    assert (
        lab_out.eligible_for_bowaka_equity_bucket
        == src_out["eligible_for_bowaka_equity_bucket"]
    )
    assert lab_out.classification_reason == src_out["classification_reason"]
    assert lab_out.instrument_class == expected


def test_classify_instrument_blocklist_precedence():
    cfg_local = {
        "instrument_rules": {
            "ticker_blocklist": ["AAPL"],
            "name_keywords": DEFAULT_NAME_KEYWORDS,
        }
    }
    lab_out = lab_classify("AAPL", name="APPLE INC", asset_class="us_equity", ticker_blocklist=["AAPL"])
    src_out = source_classify("AAPL", {"name": "APPLE INC", "asset_class": "us_equity"}, cfg_local)
    assert lab_out.classification_reason == "ticker_blocklist"
    assert src_out["classification_reason"] == "ticker_blocklist"


def test_classify_instrument_leveraged_wins_over_inverse():
    name = "DIREXION DAILY BEAR 3X"
    lab_out = lab_classify("FOO", name=name, asset_class="us_equity")
    src_out = source_classify(
        "FOO", {"name": name, "asset_class": "us_equity"},
        {"instrument_rules": {"name_keywords": DEFAULT_NAME_KEYWORDS}},
    )
    assert lab_out.instrument_class == "leveraged_etp"
    assert src_out["instrument_class"] == "leveraged_etp"
