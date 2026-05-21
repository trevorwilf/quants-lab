"""bowaka_v2_lab.data.suppliers — lake-backed bar suppliers + daily-cache builder."""
from __future__ import annotations

import datetime as dt

import pandas as pd

from bowaka_common.marketdata import layout
from bowaka_v2_lab.data.suppliers import (
    DAILY_CACHE_COLUMNS,
    build_daily_cache_from_lake,
    make_lake_suppliers,
)


def _write(path, df):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _daily(symbol, dates, *, close=10.0, volume=100_000):
    n = len(dates)
    return pd.DataFrame(
        {
            "symbol": [symbol] * n,
            "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in dates],
            "open": [close] * n,
            "high": [close + 1.0] * n,
            "low": [close - 1.0] * n,
            "close": [close] * n,
            "volume": [volume] * n,
            "session_date": list(dates),
        }
    )


def test_make_lake_suppliers_minute(tmp_path):
    ts = pd.to_datetime(["2026-05-04 14:00", "2026-05-04 14:30"], utc=True)
    _write(
        layout.minute_bars_path(tmp_path, "AAA", 2026, 5),
        pd.DataFrame(
            {
                "symbol": ["AAA"] * 2,
                "timestamp": ts,
                "open": [1.0] * 2,
                "high": [2.0] * 2,
                "low": [0.5] * 2,
                "close": [1.5] * 2,
                "volume": [100] * 2,
            }
        ),
    )
    minute_supplier, _ = make_lake_suppliers(tmp_path, feed="iex")
    out = minute_supplier("AAA", pd.Timestamp("2026-05-04 15:00", tz="UTC"))
    assert len(out) == 2
    assert str(out["timestamp"].dt.tz) == "UTC"


def test_make_lake_suppliers_daily(tmp_path):
    dates = [dt.date(2026, 4, 1) + dt.timedelta(days=i) for i in range(10)]
    _write(layout.daily_bars_path(tmp_path, "AAA"), _daily("AAA", dates))
    _, daily_supplier = make_lake_suppliers(tmp_path)
    out = daily_supplier("AAA", dt.date(2026, 4, 10))
    assert not out.empty


def test_build_daily_cache_columns_and_values(tmp_path):
    dates = [dt.date(2026, 3, 1) + dt.timedelta(days=i) for i in range(40)]
    _write(layout.daily_bars_path(tmp_path, "AAA"), _daily("AAA", dates, close=10.0, volume=100_000))
    cache = build_daily_cache_from_lake(tmp_path, ["AAA"], dt.date(2026, 4, 5), feed="iex")
    assert list(cache.columns) == DAILY_CACHE_COLUMNS
    assert len(cache) == 1
    row = cache.iloc[0]
    assert row["symbol"] == "AAA"
    assert row["prior_close"] == 10.0
    assert row["avg_dollar_volume_20d"] > 0.0


def test_build_daily_cache_no_lookahead(tmp_path):
    # sessions 2026-03-01..03-20 all close 10.0; the as-of date is 2026-03-15
    early = [dt.date(2026, 3, 1) + dt.timedelta(days=i) for i in range(14)]
    _write(layout.daily_bars_path(tmp_path, "AAA"), _daily("AAA", early, close=10.0))
    cache = build_daily_cache_from_lake(tmp_path, ["AAA"], dt.date(2026, 3, 15))
    # only sessions strictly before 2026-03-15 contribute
    assert cache.iloc[0]["prior_close"] == 10.0


def test_build_daily_cache_empty_for_missing_symbol(tmp_path):
    cache = build_daily_cache_from_lake(tmp_path, ["NOPE"], dt.date(2026, 4, 1))
    assert cache.empty
    assert list(cache.columns) == DAILY_CACHE_COLUMNS
