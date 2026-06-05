"""SIP NBBO quote backfill — producer/consumer round-trip + sampling + resume.

The backfill's quote stage writes the EXACT schema
``MarketDataStore.quotes_at_or_before`` reads (``symbol, timestamp(UTC), bid,
ask, bid_size, ask_size, conditions``), down-sampled to one prevailing NBBO per
regular-session minute. These pin that contract with an injected (no-network)
quote fetcher.
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
    _sample_session_nbbo,
    fetch_quotes,
)
from bowaka_common.marketdata.store import MarketDataStore

_LOG = logging.getLogger("test_quotes")
_LOG.addHandler(logging.NullHandler())
_SESS = _dt.date(2025, 5, 1)  # a weekday
_SYM = "TEST"


def _synthetic_ticks(symbol: str = _SYM):
    """NBBO ticks every 20s across 09:00–16:30 ET (covers the regular session)."""
    base = pd.Timestamp(f"{_SESS} 09:00", tz="America/New_York").tz_convert("UTC")
    rows = []
    for i in range(int((7.5 * 3600) / 20)):
        ts = base + pd.Timedelta(seconds=20 * i)
        mid = 10.0 + (i % 50) * 0.001
        rows.append({
            "symbol": symbol, "timestamp": ts,
            "bid": round(mid - 0.006, 4), "ask": round(mid + 0.006, 4),
            "bid_size": 500.0, "ask_size": 600.0, "conditions": "R",
        })
    return rows


def _cfg(lake: Path) -> BackfillConfig:
    return BackfillConfig(
        api_key="x", api_secret="x", paper=True, feed="sip",
        start_date=_SESS, end_date=_SESS, lake_root=lake, resume=True,
    )


def _fake_fetcher(ticks):
    def _f(batch, start_dt, end_dt):
        return {
            s: ([t for t in ticks if start_dt <= t["timestamp"] < end_dt]
                if s == _SYM else [])
            for s in batch
        }
    return _f


def test_sample_session_nbbo_one_per_minute() -> None:
    ticks = pd.DataFrame(_synthetic_ticks())
    sampled = _sample_session_nbbo(ticks, _SESS)
    assert list(sampled.columns) == [
        "symbol", "timestamp", "bid", "ask", "bid_size", "ask_size", "conditions"]
    assert len(sampled) == 390  # 09:30..15:59 ET (regular session)
    # first/last boundaries map to 13:30 / 19:59 UTC on 2025-05-01 (EDT)
    assert sampled["timestamp"].min() <= pd.Timestamp(f"{_SESS} 13:30", tz="UTC")
    assert sampled["timestamp"].max() <= pd.Timestamp(f"{_SESS} 19:59", tz="UTC")
    assert sampled["timestamp"].is_monotonic_increasing


def test_fetch_quotes_roundtrip_and_consumer_reads_it() -> None:
    lake = Path(tempfile.mkdtemp())
    cfg = _cfg(lake)
    targets = pd.DataFrame([{"session_date": _SESS, "symbol": _SYM}])
    stats = fetch_quotes(cfg, targets, _LOG, RateLimiter(6000),
                         quotes_fetcher=_fake_fetcher(_synthetic_ticks()), batch_size=10)
    assert stats["pairs_written"] == 1 and stats["months_written"] == 1

    path = layout.quotes_path(lake, _SYM, _SESS.year, _SESS.month, feed="sip")
    assert path.is_file()
    df = pd.read_parquet(path)
    assert set(df.columns) >= {"symbol", "timestamp", "bid", "ask", "bid_size", "ask_size"}

    store = MarketDataStore(lake)
    look = pd.Timestamp(f"{_SESS} 10:30", tz="America/New_York").tz_convert("UTC")
    q = store.quotes_at_or_before(_SYM, look, max_age_seconds=60, feed="sip")
    assert q is not None
    assert q.bid < q.ask and q.source == "historical"
    assert q.quote_age_seconds <= 60.0


def test_fetch_quotes_is_resume_aware() -> None:
    lake = Path(tempfile.mkdtemp())
    cfg = _cfg(lake)
    targets = pd.DataFrame([{"session_date": _SESS, "symbol": _SYM}])
    fetcher = _fake_fetcher(_synthetic_ticks())
    fetch_quotes(cfg, targets, _LOG, RateLimiter(6000), quotes_fetcher=fetcher, batch_size=10)
    second = fetch_quotes(cfg, targets, _LOG, RateLimiter(6000), quotes_fetcher=fetcher, batch_size=10)
    assert second["pairs_skipped_resume"] == 1
    assert second["pairs_written"] == 0 and second["months_written"] == 0


def test_empty_targets_is_noop() -> None:
    cfg = _cfg(Path(tempfile.mkdtemp()))
    stats = fetch_quotes(cfg, pd.DataFrame(columns=["session_date", "symbol"]),
                         _LOG, RateLimiter(6000), quotes_fetcher=_fake_fetcher([]))
    assert stats["pairs_written"] == 0
