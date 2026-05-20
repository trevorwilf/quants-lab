"""tz-aware timestamps required; DST spring-forward + fall-back handled."""
from __future__ import annotations

import datetime as _dt

import pandas as pd
import pytest

from bowaka_v2_lab.features.forming_bar import _et_minute_of_day


def test_naive_timestamp_rejected() -> None:
    with pytest.raises(ValueError, match="naive timestamp"):
        _et_minute_of_day(pd.Timestamp("2024-04-15 13:30:00"))  # naive


def test_normal_day_minute_zero_at_open() -> None:
    ts = pd.Timestamp("2024-04-15 13:30:00", tz="UTC")  # 09:30 ET on a non-DST-edge weekday
    assert _et_minute_of_day(ts) == 0


def test_normal_day_minute_60_at_1030_et() -> None:
    ts = pd.Timestamp("2024-04-15 14:30:00", tz="UTC")  # 10:30 ET
    assert _et_minute_of_day(ts) == 60


def test_dst_spring_forward_minute_math() -> None:
    # 2024-03-11 (Monday after DST start): 09:30 ET == 13:30 UTC (EDT, UTC-4)
    ts = pd.Timestamp("2024-03-11 13:30:00", tz="UTC")
    assert _et_minute_of_day(ts) == 0


def test_dst_fall_back_minute_math() -> None:
    # 2024-11-04 (Monday after DST end): 09:30 ET == 14:30 UTC (EST, UTC-5)
    ts = pd.Timestamp("2024-11-04 14:30:00", tz="UTC")
    assert _et_minute_of_day(ts) == 0


def test_after_close_clamped() -> None:
    ts = pd.Timestamp("2024-04-15 21:30:00", tz="UTC")  # 17:30 ET (after close)
    assert _et_minute_of_day(ts) == 389
