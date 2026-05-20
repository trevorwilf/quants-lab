"""require_aware_timestamp: naive rejected, DST transitions handled, ET/UTC roundtrip."""
from __future__ import annotations

import datetime as _dt

import pandas as pd
import pytest

from bowaka_v2_lab.utils.time import ET, UTC, is_aware, require_aware_timestamp, to_et, to_utc


def test_naive_timestamp_rejected() -> None:
    with pytest.raises(ValueError, match="naive timestamp"):
        require_aware_timestamp(pd.Timestamp("2024-01-01 12:00:00"))


def test_aware_timestamp_accepted_utc() -> None:
    ts = pd.Timestamp("2024-01-01 12:00:00", tz="UTC")
    out = require_aware_timestamp(ts)
    assert is_aware(out)
    assert out == ts


def test_aware_timestamp_accepted_et() -> None:
    ts = pd.Timestamp("2024-01-01 12:00:00", tz="America/New_York")
    out = require_aware_timestamp(ts)
    assert is_aware(out)


def test_dst_spring_forward_handled() -> None:
    # 2024 spring forward (US): 2024-03-10 07:00 UTC == 03:00 ET (after the missing 02:00).
    ts_before = pd.Timestamp("2024-03-10 06:30:00", tz="UTC")  # pre-jump
    ts_after = pd.Timestamp("2024-03-10 07:30:00", tz="UTC")   # post-jump
    et_before = to_et(ts_before)
    et_after = to_et(ts_after)
    # Crossing the missing 02:00 hour: the ET local hour jumps from 01 → 03.
    assert et_before.hour == 1
    assert et_after.hour == 3
    # Offsets shift -5 → -4 across the boundary.
    assert et_before.utcoffset() != et_after.utcoffset()


def test_dst_fall_back_handled() -> None:
    ts = pd.Timestamp("2024-11-03 06:30:00", tz="UTC")
    et = to_et(ts)
    assert et.tzinfo is not None


def test_utc_et_roundtrip() -> None:
    ts = pd.Timestamp("2024-06-15 13:30:00", tz="UTC")
    et = to_et(ts)
    back = to_utc(et)
    assert back == ts


def test_naive_datetime_rejected() -> None:
    with pytest.raises(ValueError, match="naive timestamp"):
        require_aware_timestamp(_dt.datetime(2024, 1, 1, 12, 0, 0))


def test_none_rejected() -> None:
    with pytest.raises(ValueError, match="timestamp is None"):
        require_aware_timestamp(None)
