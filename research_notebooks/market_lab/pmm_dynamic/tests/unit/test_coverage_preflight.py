"""Coverage audit + 5m→1h resample + preflight abort tests (no Mongo)."""

import numpy as np
import pytest

from pmm_lab.config.params import DataQuery
from pmm_lab.data.coverage import (
    audit_pair,
    preflight_pair,
    resample_candles,
)
from tests.conftest import CANDLE_DTYPE


class FakeLoader:
    """Duck-typed MongoCandleLoader returning canned arrays per interval."""

    def __init__(self, by_interval):
        self._by_interval = by_interval

    def load_range(self, query: DataQuery, enrich_synthetic: bool = True):
        arr = self._by_interval.get(query.interval)
        if arr is None or len(arr) == 0:
            raise ValueError(
                f"No candles found for {query.connector} "
                f"{query.trading_pair} {query.interval}"
            )
        return arr


def _candles(n, interval_seconds, start_ts=1_700_000_000, drop_idx=(), ff_idx=()):
    rows = []
    for i in range(n):
        if i in drop_idx:
            continue
        ts = start_ts + i * interval_seconds
        base = 100.0 + i * 0.01
        rows.append((ts, base, base + 1.0, base - 1.0, base + 0.5,
                     float(i + 1), i in ff_idx))
    return np.array(rows, dtype=CANDLE_DTYPE)


# ----------------------------------------------------------------------
# audit_pair
# ----------------------------------------------------------------------

def test_audit_pair_gapless():
    loader = FakeLoader({"1h": _candles(48, 3600)})
    a = audit_pair("nonkyc", "XMR-USDT", "1h", loader=loader)
    assert a["bars"] == 48
    assert a["expected_bars"] == 48
    assert a["gap_pct"] == 0.0
    assert a["max_gap_hours"] == 0.0
    assert a["days"] == pytest.approx(47 / 24)


def test_audit_pair_with_gap():
    # drop 6 consecutive hourly bars → 6h max gap
    loader = FakeLoader({"1h": _candles(100, 3600, drop_idx=set(range(10, 16)))})
    a = audit_pair("nonkyc", "XMR-USDT", "1h", loader=loader)
    assert a["bars"] == 94
    assert a["expected_bars"] == 100
    assert a["gap_pct"] == pytest.approx(6.0)
    assert a["max_gap_hours"] == pytest.approx(6.0)


def test_audit_pair_missing_data_returns_zeros():
    a = audit_pair("nonkyc", "DASH-USDT", "1h", loader=FakeLoader({}))
    assert a["bars"] == 0
    assert a["days"] == 0.0
    assert a["gap_pct"] == 100.0


def test_audit_pair_invalid_interval_raises():
    with pytest.raises(ValueError, match="Invalid interval"):
        audit_pair("nonkyc", "XMR-USDT", "2h", loader=FakeLoader({}))


# ----------------------------------------------------------------------
# resample_candles
# ----------------------------------------------------------------------

def test_resample_ohlc_bucket_aggregation():
    # two full UTC-aligned hours of 5m bars, deterministic values
    start = 1_700_000_000 - (1_700_000_000 % 3600)  # exact hour boundary
    five = _candles(24, 300, start_ts=start)
    hourly = resample_candles(five, "5m", "1h")
    assert len(hourly) == 2
    for row in hourly:
        assert row["timestamp"] % 3600 == 0, "buckets must be UTC-aligned"
    first, second = hourly[0], hourly[1]
    chunk = five[:12]
    assert first["open"] == chunk["open"][0]
    assert first["close"] == chunk["close"][-1]
    assert first["high"] == np.max(chunk["high"])
    assert first["low"] == np.min(chunk["low"])
    assert first["volume"] == pytest.approx(np.sum(chunk["volume"]))
    chunk2 = five[12:]
    assert second["open"] == chunk2["open"][0]
    assert second["close"] == chunk2["close"][-1]


def test_resample_misaligned_start_partial_first_bucket():
    start = 1_700_000_000 - (1_700_000_000 % 3600) + 1800  # :30 past the hour
    five = _candles(12, 300, start_ts=start)  # spans two UTC hours
    hourly = resample_candles(five, "5m", "1h")
    assert len(hourly) == 2
    assert hourly[0]["timestamp"] % 3600 == 0
    assert hourly[1]["timestamp"] - hourly[0]["timestamp"] == 3600


def test_resample_forward_fill_all_semantics():
    start = 1_700_000_000 - (1_700_000_000 % 3600)
    all_ff = _candles(12, 300, start_ts=start, ff_idx=set(range(12)))
    some_ff = _candles(12, 300, start_ts=start, ff_idx={0, 1})
    assert resample_candles(all_ff, "5m", "1h")[0]["is_forward_fill"]
    assert not resample_candles(some_ff, "5m", "1h")[0]["is_forward_fill"]


def test_resample_rejects_finer_target():
    five = _candles(12, 300)
    with pytest.raises(ValueError, match="coarser multiple"):
        resample_candles(five, "5m", "1m")


# ----------------------------------------------------------------------
# preflight_pair
# ----------------------------------------------------------------------

def _long_history(interval_seconds, days):
    n = int(days * 86400 / interval_seconds)
    return _candles(n, interval_seconds)


def test_preflight_prefers_native_interval():
    loader = FakeLoader({
        "1h": _long_history(3600, 200),
        "5m": _long_history(300, 200),
    })
    candles, info = preflight_pair("nonkyc", "XMR-USDT", loader=loader)
    assert info["source"] == "native"
    assert len(candles) == len(loader._by_interval["1h"])


def test_preflight_falls_back_to_resampled_5m():
    loader = FakeLoader({"5m": _long_history(300, 200)})
    candles, info = preflight_pair("nonkyc", "XMR-USDT", loader=loader)
    assert info["source"] == "resampled_5m"
    assert np.all(candles["timestamp"] % 3600 == 0)


def test_preflight_aborts_on_short_history():
    loader = FakeLoader({"1h": _long_history(3600, 100)})
    with pytest.raises(RuntimeError, match="preflight ABORT"):
        preflight_pair("nonkyc", "XMR-USDT", loader=loader)


def test_preflight_aborts_on_gappy_history():
    n = int(200 * 86400 / 3600)
    gappy = _candles(n, 3600, drop_idx=set(range(100, 100 + n // 10)))
    loader = FakeLoader({"1h": gappy})
    with pytest.raises(RuntimeError, match="gap_pct"):
        preflight_pair("nonkyc", "XMR-USDT", loader=loader)


def test_preflight_aborts_when_no_data_anywhere():
    with pytest.raises(RuntimeError, match="no candles in the lake"):
        preflight_pair("nonkyc", "DASH-USDT", loader=FakeLoader({}))
