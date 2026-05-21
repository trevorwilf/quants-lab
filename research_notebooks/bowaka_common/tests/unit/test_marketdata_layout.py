"""The canonical market-data lake layout — path builders are stable & exact."""
from __future__ import annotations

from bowaka_common.marketdata import layout


def test_daily_bars_path_is_canonical():
    p = layout.daily_bars_path("/lake", "AAPL")
    assert p.as_posix() == (
        "/lake/bars/vendor=alpaca/feed=iex/timeframe=1d/adjustment=raw/symbol=AAPL/part.parquet"
    )


def test_minute_bars_path_is_canonical_and_zero_padded():
    p = layout.minute_bars_path("/lake", "AAPL", 2026, 5)
    assert p.as_posix() == (
        "/lake/bars/vendor=alpaca/feed=iex/timeframe=1m/adjustment=raw/symbol=AAPL/"
        "year=2026/month=05/part.parquet"
    )


def test_minute_month_padding():
    assert "month=03" in layout.minute_bars_path("/lake", "X", 2026, 3).parts
    assert "month=12" in layout.minute_bars_path("/lake", "X", 2026, 12).parts


def test_quotes_path_is_canonical():
    p = layout.quotes_path("/lake", "MSFT", 2026, 1)
    assert p.as_posix() == (
        "/lake/quotes/vendor=alpaca/feed=iex/symbol=MSFT/year=2026/month=01/part.parquet"
    )


def test_assets_path_is_canonical():
    p = layout.assets_path("/lake", "2026-05-01T120000Z_alpaca_assets")
    assert p.as_posix() == (
        "/lake/assets/vendor=alpaca/snapshot_id=2026-05-01T120000Z_alpaca_assets/assets.parquet"
    )


def test_corporate_actions_path_is_canonical():
    p = layout.corporate_actions_path("/lake", "TSLA")
    assert p.as_posix() == "/lake/corporate_actions/vendor=alpaca/symbol=TSLA/part.parquet"


def test_ingestion_paths():
    assert layout.ingestion_manifest_path("/lake").as_posix() == "/lake/_ingestion/manifest.json"
    assert layout.ingestion_run_path("/lake", "r1").as_posix() == "/lake/_ingestion/runs/r1.json"
    assert layout.ingestion_audit_path("/lake", "a1").as_posix() == "/lake/_ingestion/audits/a1.parquet"


def test_bars_timeframe_root_is_the_scan_dir():
    root = layout.bars_timeframe_root("/lake", "1d")
    assert root.as_posix() == "/lake/bars/vendor=alpaca/feed=iex/timeframe=1d/adjustment=raw"
    # the symbol dir is a direct child of the timeframe root
    assert layout.daily_bars_symbol_dir("/lake", "AAPL").parent == root


def test_vendor_feed_overrides_flow_through():
    p = layout.daily_bars_path("/lake", "X", vendor="polygon", feed="sip", adjustment="split")
    assert "vendor=polygon" in p.parts
    assert "feed=sip" in p.parts
    assert "adjustment=split" in p.parts
