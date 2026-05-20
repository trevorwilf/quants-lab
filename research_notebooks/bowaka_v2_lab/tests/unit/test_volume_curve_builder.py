"""volume_curve builder: excludes current session; raises on bad inputs."""
from __future__ import annotations

import datetime as _dt

import pandas as pd
import pytest

from bowaka_v2_lab.features import (
    adv_bucket,
    build_volume_curve_from_minute_bars,
    synthesize_default_curve,
)
from tests.fixtures.build_minute_fixture import make_minute_bars


def test_synthesize_default_curve_shape() -> None:
    curve = synthesize_default_curve()
    # 6 buckets × 390 minutes = 2340 rows
    assert len(curve) == 2340
    assert set(curve.columns) == {"minute_of_day", "adv_bucket", "cumulative_fraction"}
    assert curve["cumulative_fraction"].min() >= 0.0
    assert curve["cumulative_fraction"].max() <= 1.0


def test_build_from_minute_bars_excludes_current_session() -> None:
    d1 = make_minute_bars("AAA", _dt.date(2024, 9, 3))
    d2 = make_minute_bars("AAA", _dt.date(2024, 9, 4))
    bars = pd.concat([d1, d2], ignore_index=True)
    # current_session=Sep 4 (present in bars) → assertion fires.
    with pytest.raises(AssertionError):
        build_volume_curve_from_minute_bars(
            bars, adv_lookup={"AAA": 1_500_000}, current_session=_dt.date(2024, 9, 4),
        )


def test_build_from_minute_bars_succeeds_when_session_not_in_bars() -> None:
    d1 = make_minute_bars("AAA", _dt.date(2024, 9, 3))
    curve = build_volume_curve_from_minute_bars(
        d1, adv_lookup={"AAA": 1_500_000}, current_session=_dt.date(2024, 9, 4),
    )
    assert not curve.empty


def test_build_requires_required_columns() -> None:
    bad = pd.DataFrame({"a": [1, 2, 3]})
    with pytest.raises(ValueError, match="timestamp"):
        build_volume_curve_from_minute_bars(bad)


def test_build_rejects_naive_timestamps() -> None:
    df = pd.DataFrame({
        "symbol": ["AAA"] * 3,
        "timestamp": [pd.Timestamp("2024-09-03 13:30:00")] * 3,  # naive
        "volume": [100.0, 200.0, 300.0],
    })
    with pytest.raises(ValueError, match="tz-naive"):
        build_volume_curve_from_minute_bars(df)


def test_adv_bucket_labels() -> None:
    assert adv_bucket(None) == "<250k"
    assert adv_bucket(100_000) == "<250k"
    assert adv_bucket(300_000) == "250k_500k"
    assert adv_bucket(1_500_000) == "1M_5M"
    assert adv_bucket(100_000_000) == "20M+"
