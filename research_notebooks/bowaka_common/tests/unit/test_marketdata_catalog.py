"""Catalog: coverage queries + deterministic dataset hashing."""
from __future__ import annotations

import datetime as dt

import pandas as pd

from bowaka_common.marketdata import catalog, layout


def _write_daily(root, symbol, dates):
    n = len(dates)
    df = pd.DataFrame(
        {
            "symbol": [symbol] * n,
            "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in dates],
            "open": [1.0] * n,
            "high": [2.0] * n,
            "low": [0.5] * n,
            "close": [1.5] * n,
            "volume": [100] * n,
        }
    )
    path = layout.daily_bars_path(root, symbol)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def test_available_symbols(tmp_path):
    _write_daily(tmp_path, "AAA", [dt.date(2026, 5, 1)])
    _write_daily(tmp_path, "BBB", [dt.date(2026, 5, 1)])
    assert catalog.available_symbols(tmp_path) == ["AAA", "BBB"]


def test_available_symbols_empty_lake(tmp_path):
    assert catalog.available_symbols(tmp_path) == []


def test_date_coverage(tmp_path):
    _write_daily(tmp_path, "AAA", [dt.date(2026, 5, 1), dt.date(2026, 5, 10)])
    assert catalog.date_coverage("AAA", tmp_path) == (dt.date(2026, 5, 1), dt.date(2026, 5, 10))


def test_date_coverage_missing_symbol(tmp_path):
    assert catalog.date_coverage("NOPE", tmp_path) is None


def test_dataset_hash_is_deterministic_and_order_independent(tmp_path):
    _write_daily(tmp_path, "AAA", [dt.date(2026, 5, 1), dt.date(2026, 5, 2)])
    _write_daily(tmp_path, "BBB", [dt.date(2026, 5, 1)])
    h1 = catalog.dataset_hash(["AAA", "BBB"], "2026-05-01", "2026-05-31", tmp_path)
    h2 = catalog.dataset_hash(["BBB", "AAA"], "2026-05-01", "2026-05-31", tmp_path)
    assert h1 == h2
    assert h1.startswith("sha256:")


def test_dataset_hash_changes_with_selection(tmp_path):
    _write_daily(tmp_path, "AAA", [dt.date(2026, 5, 1)])
    _write_daily(tmp_path, "BBB", [dt.date(2026, 5, 1)])
    h_a = catalog.dataset_hash(["AAA"], "2026-05-01", "2026-05-31", tmp_path)
    h_ab = catalog.dataset_hash(["AAA", "BBB"], "2026-05-01", "2026-05-31", tmp_path)
    assert h_a != h_ab
