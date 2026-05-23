"""SIP partition path helpers return the canonical paths (Phase 10 scaffolding).

Realism remediation 2 Phase 10 / audit §11 Phase 9. The SIP ingestion stage
has not run yet; the path helpers ship before the data does so the
SIP-preflight + DQ + MarketDataStore SIP probes have a canonical spelling for
every partition.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from bowaka_common.marketdata import layout


def test_sip_constants_defined():
    assert layout.FEED_SIP == "sip"
    assert layout.FEED_IEX == "iex"
    assert layout.SIP_DAILY_ADJUSTMENT == "split_adjusted"
    assert layout.DS_STATUSES == "statuses"


def test_sip_daily_bars_path_is_canonical():
    p = layout.sip_daily_bars_path("/lake", "AAPL")
    assert p.as_posix() == (
        "/lake/bars/vendor=alpaca/feed=sip/timeframe=1d/adjustment=split_adjusted/"
        "symbol=AAPL/part.parquet"
    )


def test_sip_minute_bars_path_is_canonical():
    p = layout.sip_minute_bars_path("/lake", "AAPL", 2026, 5)
    assert p.as_posix() == (
        "/lake/bars/vendor=alpaca/feed=sip/timeframe=1m/adjustment=raw/"
        "symbol=AAPL/year=2026/month=05/part.parquet"
    )


def test_sip_quotes_path_is_canonical():
    p = layout.sip_quotes_path("/lake", "MSFT", 2026, 1)
    assert p.as_posix() == (
        "/lake/quotes/vendor=alpaca/feed=sip/symbol=MSFT/year=2026/month=01/part.parquet"
    )


def test_sip_bars_root_returns_canonical_root():
    daily = layout.sip_bars_root("/lake", "1d")
    assert daily.as_posix() == (
        "/lake/bars/vendor=alpaca/feed=sip/timeframe=1d/adjustment=split_adjusted"
    )
    minute = layout.sip_bars_root("/lake", "1m")
    assert minute.as_posix() == (
        "/lake/bars/vendor=alpaca/feed=sip/timeframe=1m/adjustment=raw"
    )


def test_sip_quotes_root_returns_canonical_root():
    root = layout.sip_quotes_root("/lake")
    assert root.as_posix() == "/lake/quotes/vendor=alpaca/feed=sip"


def test_statuses_path_is_canonical():
    p = layout.statuses_path("/lake", "AAPL", dt.date(2026, 5, 4))
    assert p.as_posix() == (
        "/lake/statuses/vendor=alpaca/symbol=AAPL/date=2026-05-04/part.parquet"
    )


def test_statuses_path_accepts_string_date():
    p = layout.statuses_path("/lake", "AAPL", "2026-05-04")
    assert p.as_posix() == (
        "/lake/statuses/vendor=alpaca/symbol=AAPL/date=2026-05-04/part.parquet"
    )


def test_sip_partitions_available_returns_false_on_empty_lake(tmp_path):
    # Empty lake → no SIP partitions.
    assert not layout.sip_partitions_available(tmp_path)


def test_sip_partitions_available_detects_daily_bars(tmp_path):
    # Drop a fake SIP daily parquet — the existence probe is content-agnostic.
    target = layout.sip_daily_bars_path(tmp_path, "AAA")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"PAR1\x00\x00\x00\x00")  # placeholder bytes
    assert layout.sip_partitions_available(tmp_path)


def test_sip_partitions_available_detects_minute_bars(tmp_path):
    target = layout.sip_minute_bars_path(tmp_path, "AAA", 2026, 5)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"PAR1\x00\x00\x00\x00")
    assert layout.sip_partitions_available(tmp_path)


def test_sip_partitions_available_detects_quotes(tmp_path):
    target = layout.sip_quotes_path(tmp_path, "AAA", 2026, 5)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"PAR1\x00\x00\x00\x00")
    assert layout.sip_partitions_available(tmp_path)


def test_sip_partitions_available_ignores_iex_data(tmp_path):
    # IEX partition exists; SIP should still report absent.
    iex_path = layout.daily_bars_path(tmp_path, "AAA", feed="iex")
    iex_path.parent.mkdir(parents=True, exist_ok=True)
    iex_path.write_bytes(b"PAR1\x00\x00\x00\x00")
    assert not layout.sip_partitions_available(tmp_path)
