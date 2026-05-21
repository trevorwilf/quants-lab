"""Write via the layout, read via MarketDataStore — round-trip + range filter."""
from __future__ import annotations

import pandas as pd

from bowaka_common.marketdata import layout
from bowaka_common.marketdata.store import MarketDataStore


def _write(path, df):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _bars(symbol, timestamps):
    n = len(timestamps)
    return pd.DataFrame(
        {
            "symbol": [symbol] * n,
            "timestamp": timestamps,
            "open": [1.0] * n,
            "high": [2.0] * n,
            "low": [0.5] * n,
            "close": [1.5] * n,
            "volume": [1000] * n,
        }
    )


def test_daily_roundtrip_and_range_filter(tmp_path):
    ts = pd.to_datetime(
        ["2026-05-01", "2026-05-02", "2026-05-03", "2026-05-04"], utc=True
    ) + pd.Timedelta(hours=20)
    _write(layout.daily_bars_path(tmp_path, "AAA"), _bars("AAA", ts))
    out = MarketDataStore(tmp_path).daily_bars("AAA", "2026-05-02", "2026-05-03")
    assert list(out["timestamp"].dt.day) == [2, 3]
    assert str(out["timestamp"].dt.tz) == "UTC"


def test_minute_bars_span_two_month_partitions(tmp_path):
    may = pd.to_datetime(["2026-05-30 14:00", "2026-05-30 15:00"], utc=True)
    jun = pd.to_datetime(["2026-06-01 14:00", "2026-06-02 14:00"], utc=True)
    _write(layout.minute_bars_path(tmp_path, "AAA", 2026, 5), _bars("AAA", may))
    _write(layout.minute_bars_path(tmp_path, "AAA", 2026, 6), _bars("AAA", jun))
    out = MarketDataStore(tmp_path).minute_bars("AAA", "2026-05-30 14:30", "2026-06-02 23:00")
    # May-30 14:00 is before start; the other three are inside the range.
    assert len(out) == 3
    assert str(out["timestamp"].dt.tz) == "UTC"
    assert out["timestamp"].is_monotonic_increasing


def test_missing_symbol_returns_empty(tmp_path):
    store = MarketDataStore(tmp_path)
    assert store.daily_bars("NOPE", "2026-01-01", "2026-12-31").empty
    assert store.minute_bars("NOPE", "2026-01-01", "2026-12-31").empty
    assert store.quotes("NOPE", "2026-01-01", "2026-12-31").empty


def test_assets_roundtrip(tmp_path):
    snap = "2026-05-01T120000Z_alpaca_assets"
    _write(layout.assets_path(tmp_path, snap), pd.DataFrame({"snapshot_id": [snap], "symbol": ["AAA"]}))
    store = MarketDataStore(tmp_path)
    assert store.latest_snapshot_id() == snap
    assert store.assets()["symbol"].tolist() == ["AAA"]
