"""bowaka_lab.data.market_data — v1's lake-backed read adapter."""
from __future__ import annotations

import datetime as dt

import pandas as pd

from bowaka_common.marketdata import layout
from bowaka_lab.data.market_data import (
    MarketDataStore,
    open_market_data_store,
    scope_3_universe,
)


def _write_daily(root, symbol, dates, *, close=10.0, volume=100_000):
    n = len(dates)
    df = pd.DataFrame(
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
    path = layout.daily_bars_path(root, symbol)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def test_open_market_data_store_returns_store(tmp_path):
    store = open_market_data_store(tmp_path)
    assert isinstance(store, MarketDataStore)
    assert store.root == tmp_path


def test_scope_3_universe_applies_price_and_adv_gates(tmp_path):
    dates = [dt.date(2026, 3, 1) + dt.timedelta(days=i) for i in range(60)]
    # GOOD: dollar volume 1e6 >= adv_min, price in band -> in scope
    _write_daily(tmp_path, "GOOD", dates, close=10.0, volume=100_000)
    # PENNY: price below price_min -> excluded
    _write_daily(tmp_path, "PENNY", dates, close=0.50, volume=100_000)
    # THIN: dollar volume 5e4 below adv_min -> excluded
    _write_daily(tmp_path, "THIN", dates, close=10.0, volume=5_000)

    store = open_market_data_store(tmp_path)
    scope = scope_3_universe(
        store,
        ["GOOD", "PENNY", "THIN"],
        dt.date(2026, 4, 1),
        dt.date(2026, 4, 10),
        price_min=1.0,
        price_max=20.0,
        adv_min=200_000.0,
        adv_window_days=20,
    )
    symbols = set(scope["symbol"])
    assert "GOOD" in symbols
    assert "PENNY" not in symbols
    assert "THIN" not in symbols
    # all selected sessions fall inside the requested window
    assert scope["session_date"].min() >= dt.date(2026, 4, 1)
    assert scope["session_date"].max() <= dt.date(2026, 4, 10)


def test_scope_3_universe_empty_when_no_data(tmp_path):
    store = open_market_data_store(tmp_path)
    scope = scope_3_universe(store, ["NOPE"], dt.date(2026, 4, 1), dt.date(2026, 4, 10))
    assert list(scope.columns) == ["session_date", "symbol"]
    assert scope.empty
