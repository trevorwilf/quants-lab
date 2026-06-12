"""Write via the layout, read via MarketDataStore — round-trip + range filter."""
from __future__ import annotations

import pandas as pd

from bowaka_common.marketdata import layout
from bowaka_common.marketdata.store import MICROSTRUCTURE_COLUMNS, MarketDataStore


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


# --- PA.1: opt-in microstructure (vwap / trade_count) ---------------------

def _bars_micro(symbol, timestamps):
    """OHLCV bars that ALSO carry vwap + trade_count (as the SIP lake does)."""
    df = _bars(symbol, timestamps)
    n = len(timestamps)
    df["vwap"] = [1.25] * n
    df["trade_count"] = [42] * n
    return df


def _daily_ts():
    return pd.to_datetime(["2026-05-01", "2026-05-02"], utc=True) + pd.Timedelta(hours=20)


def test_default_read_omits_microstructure_when_partition_lacks_it(tmp_path):
    _write(layout.daily_bars_path(tmp_path, "AAA"), _bars("AAA", _daily_ts()))
    out = MarketDataStore(tmp_path).daily_bars("AAA", "2026-05-01", "2026-05-02")
    assert "vwap" not in out.columns and "trade_count" not in out.columns


def test_default_read_passes_real_microstructure_through_unchanged(tmp_path):
    # Default (with_microstructure=False) is byte-identical to a plain read:
    # if the partition carries vwap/trade_count they flow through untouched.
    _write(layout.daily_bars_path(tmp_path, "AAA"), _bars_micro("AAA", _daily_ts()))
    out = MarketDataStore(tmp_path).daily_bars("AAA", "2026-05-01", "2026-05-02")
    assert list(out["vwap"]) == [1.25, 1.25]
    assert list(out["trade_count"]) == [42, 42]


def test_with_microstructure_adds_columns_when_absent(tmp_path):
    _write(layout.daily_bars_path(tmp_path, "AAA"), _bars("AAA", _daily_ts()))
    out = MarketDataStore(tmp_path).daily_bars(
        "AAA", "2026-05-01", "2026-05-02", with_microstructure=True)
    for col in MICROSTRUCTURE_COLUMNS:
        assert col in out.columns
    assert out["vwap"].isna().all() and out["trade_count"].isna().all()
    assert str(out["vwap"].dtype) == "Float64"
    assert str(out["trade_count"].dtype) == "Int64"


def test_with_microstructure_coerces_present_values_to_stable_dtypes(tmp_path):
    _write(layout.daily_bars_path(tmp_path, "AAA"), _bars_micro("AAA", _daily_ts()))
    out = MarketDataStore(tmp_path).daily_bars(
        "AAA", "2026-05-01", "2026-05-02", with_microstructure=True)
    assert list(out["vwap"]) == [1.25, 1.25]
    assert list(out["trade_count"]) == [42, 42]
    assert str(out["vwap"].dtype) == "Float64"
    assert str(out["trade_count"].dtype) == "Int64"


def test_sip_minute_bars_plumbs_microstructure_flag(tmp_path):
    may = pd.to_datetime(["2026-05-30 14:00", "2026-05-30 15:00"], utc=True)
    _write(layout.minute_bars_path(tmp_path, "AAA", 2026, 5, feed=layout.FEED_SIP,
                                   adjustment="raw"), _bars("AAA", may))
    out = MarketDataStore(tmp_path).sip_minute_bars(
        "AAA", "2026-05-30 13:00", "2026-05-30 16:00", with_microstructure=True)
    assert len(out) == 2
    for col in MICROSTRUCTURE_COLUMNS:
        assert col in out.columns


def test_empty_with_microstructure_has_columns(tmp_path):
    out = MarketDataStore(tmp_path).minute_bars(
        "NOPE", "2026-01-01", "2026-12-31", with_microstructure=True)
    assert out.empty
    for col in MICROSTRUCTURE_COLUMNS:
        assert col in out.columns


# --- PA.2: raw trade-tape reader (trades_between) -------------------------

def test_trades_between_roundtrip_preserves_all_prints(tmp_path):
    ts = pd.to_datetime(
        ["2026-05-30 14:00", "2026-05-30 14:00", "2026-05-30 14:01"], utc=True)
    df = pd.DataFrame({
        "symbol": ["AAA"] * 3, "timestamp": ts,
        "price": [10.0, 10.01, 10.02], "size": [100.0, 50.0, 75.0],
        "exchange": ["V"] * 3, "conditions": ["@"] * 3, "tape": ["C"] * 3,
        "trade_id": [1, 2, 3],
    })
    _write(layout.trades_path(tmp_path, "AAA", 2026, 5), df)
    out = MarketDataStore(tmp_path).trades_between(
        "AAA", "2026-05-30 13:00", "2026-05-30 15:00")
    assert len(out) == 3  # incl. the two prints sharing 14:00 — NO ts-dedup
    assert out["timestamp"].is_monotonic_increasing
    assert list(out["price"]) == [10.0, 10.01, 10.02]


def test_trades_between_empty_when_absent(tmp_path):
    store = MarketDataStore(tmp_path)
    assert store.trades_between("NOPE", "2026-01-01", "2026-12-31").empty
    assert store.sip_trades_between("NOPE", "2026-01-01", "2026-12-31").empty


# --- PA.3: fine NBBO reader (quotes_fine_between) -------------------------

def test_quotes_fine_between_keeps_exchange_codes(tmp_path):
    ts = pd.to_datetime(["2026-05-30 14:00:10", "2026-05-30 14:00:40"], utc=True)
    df = pd.DataFrame({
        "symbol": ["AAA"] * 2, "timestamp": ts,
        "bid": [9.99, 9.98], "ask": [10.01, 10.02],
        "bid_size": [100.0, 150.0], "ask_size": [200.0, 250.0],
        "conditions": ["R", "R"], "bid_exchange": ["V", "P"],
        "ask_exchange": ["Q", "Z"], "tape": ["C", "C"],
    })
    _write(layout.quotes_fine_path(tmp_path, "AAA", 2026, 5), df)
    out = MarketDataStore(tmp_path).quotes_fine_between(
        "AAA", "2026-05-30 13:00", "2026-05-30 15:00")
    assert len(out) == 2
    for col in ("bid_exchange", "ask_exchange", "tape"):
        assert col in out.columns
    assert out["timestamp"].is_monotonic_increasing


def test_quotes_fine_between_empty_when_absent(tmp_path):
    store = MarketDataStore(tmp_path)
    assert store.quotes_fine_between("NOPE", "2026-01-01", "2026-12-31").empty
    assert store.sip_quotes_fine_between("NOPE", "2026-01-01", "2026-12-31").empty
