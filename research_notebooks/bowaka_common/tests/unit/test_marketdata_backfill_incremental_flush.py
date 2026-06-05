"""Incremental per-month flush for ``fetch_minute_bars`` / ``fetch_quotes``.

Both stages historically buffered the ENTIRE date range in RAM and wrote once at
the end — an OOM trap on a multi-year run + all-or-nothing (a mid-run interruption
lost everything, with no resumability). They now flush each COMPLETED month as
the date-sorted session loop crosses a month boundary. These pin:

  * multi-month output is correct (one file per (symbol, month), right rows);
  * completed months are DURABLE on disk before the run finishes — an
    interruption mid-run leaves the earlier months written (so ``resume`` skips
    them on the next run).
"""
from __future__ import annotations

import datetime as _dt
import logging
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from bowaka_common.marketdata import layout
from bowaka_common.marketdata.backfill import (
    BackfillConfig,
    RateLimiter,
    daily_file,
    fetch_minute_bars,
    fetch_quotes,
    minute_file,
)

_LOG = logging.getLogger("t")
_LOG.addHandler(logging.NullHandler())
# one session in each of three consecutive months -> two month-boundary flushes
_SESSIONS = [_dt.date(2024, 1, 16), _dt.date(2024, 2, 15), _dt.date(2024, 3, 15)]
_SYM = "AAA"


def _cfg(lake: Path) -> BackfillConfig:
    return BackfillConfig(
        api_key="x", api_secret="x", paper=True, feed="sip",
        start_date=_SESSIONS[0], end_date=_SESSIONS[-1], lake_root=lake, resume=True,
    )


def _targets(sessions=_SESSIONS) -> pd.DataFrame:
    return pd.DataFrame([{"session_date": s, "symbol": _SYM} for s in sessions])


def _bars(session) -> list:
    base = pd.Timestamp(f"{session} 14:30", tz="UTC")
    return [{"symbol": _SYM, "timestamp": base + pd.Timedelta(minutes=i),
             "open": 10.0, "high": 10.1, "low": 9.9, "close": 10.0, "volume": 100}
            for i in range(5)]


def _minute_fetcher(raise_on_month=None):
    def _f(batch, tf, start_dt, end_dt):
        s = start_dt.date()
        if raise_on_month is not None and s.month == raise_on_month:
            raise KeyboardInterrupt("simulated kill")  # not caught by `except Exception`
        return {sym: (_bars(s) if sym == _SYM else []) for sym in batch}
    return _f


def _quote_ticks(session) -> list:
    base = pd.Timestamp(f"{session} 09:00", tz="America/New_York").tz_convert("UTC")
    return [{"symbol": _SYM, "timestamp": base + pd.Timedelta(seconds=60 * i),
             "bid": 9.99, "ask": 10.01, "bid_size": 100.0, "ask_size": 100.0,
             "conditions": "R"} for i in range(int((7.5 * 3600) / 60))]


def _quote_fetcher(raise_on_month=None):
    def _f(batch, start_dt, end_dt):
        s = start_dt.date()
        if raise_on_month is not None and s.month == raise_on_month:
            raise KeyboardInterrupt("simulated kill")
        return {sym: (_quote_ticks(s) if sym == _SYM else []) for sym in batch}
    return _f


# --- minute bars ----------------------------------------------------------
def test_minute_multi_month_flushes_each_month():
    lake = Path(tempfile.mkdtemp())
    cfg = _cfg(lake)
    stats = fetch_minute_bars(cfg, _targets(), _LOG, RateLimiter(6000),
                              bars_fetcher=_minute_fetcher())
    assert stats["months_written"] == 3
    for (y, m) in [(2024, 1), (2024, 2), (2024, 3)]:
        p = minute_file(cfg, _SYM, y, m)
        assert p.is_file(), f"missing {y}-{m:02d}"
        df = pd.read_parquet(p)
        assert len(df) == 5
        assert set(pd.to_datetime(df["timestamp"], utc=True).dt.month) == {m}


def test_minute_completed_months_durable_before_interruption():
    # fetcher dies on the March session — Jan + Feb must already be flushed.
    lake = Path(tempfile.mkdtemp())
    cfg = _cfg(lake)
    with pytest.raises(KeyboardInterrupt):
        fetch_minute_bars(cfg, _targets(), _LOG, RateLimiter(6000),
                          bars_fetcher=_minute_fetcher(raise_on_month=3))
    assert minute_file(cfg, _SYM, 2024, 1).is_file()   # flushed at Jan->Feb boundary
    assert minute_file(cfg, _SYM, 2024, 2).is_file()   # flushed at Feb->Mar boundary
    assert not minute_file(cfg, _SYM, 2024, 3).exists()  # never reached


def test_minute_resume_skips_completed_months():
    lake = Path(tempfile.mkdtemp())
    cfg = _cfg(lake)
    fetch_minute_bars(cfg, _targets(_SESSIONS[:2]), _LOG, RateLimiter(6000),
                      bars_fetcher=_minute_fetcher())             # Jan + Feb
    again = fetch_minute_bars(cfg, _targets(), _LOG, RateLimiter(6000),
                              bars_fetcher=_minute_fetcher())     # all 3
    assert again["pairs_skipped_resume"] == 2  # Jan + Feb already on disk
    assert again["months_written"] == 1        # only March written


# --- quotes ---------------------------------------------------------------
def test_quotes_multi_month_flushes_each_month():
    lake = Path(tempfile.mkdtemp())
    stats = fetch_quotes(_cfg(lake), _targets(), _LOG, RateLimiter(6000),
                         quotes_fetcher=_quote_fetcher(), batch_size=10)
    assert stats["months_written"] == 3
    for (y, m) in [(2024, 1), (2024, 2), (2024, 3)]:
        assert layout.quotes_path(lake, _SYM, y, m, feed="sip").is_file()


def test_quotes_completed_months_durable_before_interruption():
    lake = Path(tempfile.mkdtemp())
    with pytest.raises(KeyboardInterrupt):
        fetch_quotes(_cfg(lake), _targets(), _LOG, RateLimiter(6000),
                     quotes_fetcher=_quote_fetcher(raise_on_month=3), batch_size=10)
    assert layout.quotes_path(lake, _SYM, 2024, 1, feed="sip").is_file()
    assert layout.quotes_path(lake, _SYM, 2024, 2, feed="sip").is_file()
    assert not layout.quotes_path(lake, _SYM, 2024, 3, feed="sip").exists()


# --- minute bars are RAW, daily uses cfg.adjustment ------------------------
def test_minute_stored_raw_even_when_cfg_is_split_adjusted():
    """Minute bars are the live-traded RAW prices everywhere in the lab;
    cfg.adjustment (split_adjusted) governs DAILY bars only. A regression here
    silently mis-files minute bars so every reader (preflight, suppliers, scan
    matrix) — which all read adjustment='raw' — finds nothing."""
    cfg = BackfillConfig(
        api_key="x", api_secret="x", paper=True, feed="sip",
        start_date=_SESSIONS[0], end_date=_SESSIONS[-1],
        lake_root=Path("/tmp/lk"), adjustment="split_adjusted",
    )
    assert "adjustment=raw" in str(minute_file(cfg, "AAA", 2025, 8))
    assert "adjustment=split_adjusted" in str(daily_file(cfg, "AAA"))


def test_fetched_minute_bars_land_in_raw_partition():
    """End-to-end: fetch_minute_bars writes to the raw partition (where the lab
    reads), not the cfg.adjustment partition."""
    lake = Path(tempfile.mkdtemp())
    cfg = BackfillConfig(
        api_key="x", api_secret="x", paper=True, feed="sip",
        start_date=_SESSIONS[0], end_date=_SESSIONS[0],
        lake_root=lake, adjustment="split_adjusted", resume=True,
    )
    fetch_minute_bars(cfg, _targets([_SESSIONS[0]]), _LOG, RateLimiter(6000),
                      bars_fetcher=_minute_fetcher())
    assert minute_file(cfg, _SYM, 2024, 1).is_file()            # raw partition
    assert "adjustment=raw" in str(minute_file(cfg, _SYM, 2024, 1))
    assert not layout.minute_bars_path(
        lake, _SYM, 2024, 1, feed="sip", adjustment="split_adjusted").is_file()
