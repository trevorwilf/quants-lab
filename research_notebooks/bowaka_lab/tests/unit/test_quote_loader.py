"""Phase fidelity-3: ``QuoteLoader`` partitioned-parquet behavior."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from bowaka_lab.data.quote_loader import QuoteLoader


@pytest.fixture
def quote_root(tmp_path):
    root = tmp_path / "parquet" / "quotes" / "vendor=alpaca" / "feed=iex"
    return root


def _write_quotes(root, trade_date, symbol, rows):
    out_dir = root / f"session_date={trade_date.isoformat()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(out_dir / f"symbol={symbol}.parquet")


def test_quote_loader_returns_empty_when_partition_missing(quote_root):
    loader = QuoteLoader(quote_root)
    out = loader(date(2026, 5, 17), ["AAPL", "MSFT"])
    assert out.empty
    assert "symbol" in out.columns
    assert loader.has_quotes_for(date(2026, 5, 17)) is False


def test_quote_loader_reads_single_symbol(quote_root):
    td = date(2026, 5, 17)
    _write_quotes(quote_root, td, "AAPL", [
        {"symbol": "AAPL", "timestamp": pd.Timestamp("2026-05-17 14:00:00", tz="UTC"),
         "bid_price": 100.0, "ask_price": 100.5, "bid_size": 100, "ask_size": 100,
         "spread": 0.5, "mid": 100.25, "spread_pct": 0.5 / 100.25},
        {"symbol": "AAPL", "timestamp": pd.Timestamp("2026-05-17 14:01:00", tz="UTC"),
         "bid_price": 100.1, "ask_price": 100.6, "bid_size": 100, "ask_size": 100,
         "spread": 0.5, "mid": 100.35, "spread_pct": 0.5 / 100.35},
    ])
    loader = QuoteLoader(quote_root)
    assert loader.has_quotes_for(td) is True
    out = loader(td, ["AAPL"])
    assert out.shape[0] == 2
    assert set(out["symbol"]) == {"AAPL"}
    assert "spread_pct" in out.columns


def test_quote_loader_aggregates_multiple_symbols(quote_root):
    td = date(2026, 5, 17)
    for sym in ("AAPL", "MSFT"):
        _write_quotes(quote_root, td, sym, [
            {"symbol": sym, "timestamp": pd.Timestamp("2026-05-17 14:00:00", tz="UTC"),
             "bid_price": 50.0, "ask_price": 50.5, "bid_size": 100, "ask_size": 100,
             "spread": 0.5, "mid": 50.25, "spread_pct": 0.01},
        ])
    loader = QuoteLoader(quote_root)
    out = loader(td, ["AAPL", "MSFT", "GOOG"])  # GOOG file doesn't exist
    assert set(out["symbol"]) == {"AAPL", "MSFT"}


def test_quote_loader_backfills_derived_columns(quote_root):
    td = date(2026, 5, 17)
    _write_quotes(quote_root, td, "AAPL", [
        {"symbol": "AAPL", "timestamp": pd.Timestamp("2026-05-17 14:00:00", tz="UTC"),
         "bid_price": 100.0, "ask_price": 100.5, "bid_size": 100, "ask_size": 100},
    ])
    loader = QuoteLoader(quote_root)
    out = loader(td, ["AAPL"])
    assert "spread" in out.columns
    assert "mid" in out.columns
    assert "spread_pct" in out.columns
    assert float(out["spread"].iloc[0]) == 0.5
