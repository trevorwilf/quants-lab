"""Configurable, incremental backfill runner — no network (injected fetchers)."""
from __future__ import annotations

import datetime as dt
import logging
import types

import pandas as pd
import pytest

from bowaka_common.marketdata import layout
from bowaka_common.marketdata.runner import (
    load_backfill_config,
    resolve_end_date,
    run_configured_backfill,
)

_LOG = logging.getLogger("test_marketdata_runner")


def _config(**over):
    cfg = {
        "feed": "iex",
        "adjustment": "raw",
        "paper": True,
        "start_date": "2024-09-03",
        "end_date": "2024-09-10",
        "daily_universe": {"source": "explicit", "symbols": ["AAA", "BBB"]},
        "minute_bars": {"enabled": True, "policy": "explicit", "symbols": ["AAA"]},
        "rate_limit_rpm": 100000,
        "batch_size_symbols": 200,
    }
    cfg.update(over)
    return cfg


def _fake_bars(batch, timeframe, start, end):
    """Injected fetcher — returns coerced bar rows, no network."""
    out = {}
    if timeframe == "1d":
        days = pd.bdate_range(pd.Timestamp(start).date(), pd.Timestamp(end).date() - pd.Timedelta(days=1))
        for sym in batch:
            out[sym] = [
                {
                    "symbol": sym,
                    "timestamp": pd.Timestamp(d.date(), tz="UTC") + pd.Timedelta(hours=20),
                    "open": 10.0, "high": 11.0, "low": 9.5, "close": 10.5, "volume": 100000,
                }
                for d in days
            ]
    else:  # 1m
        d = pd.Timestamp(start).date()
        for sym in batch:
            out[sym] = [
                {
                    "symbol": sym,
                    "timestamp": pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=14),
                    "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 1000,
                }
            ]
    return out


def _raising_bars(*_a, **_k):
    raise AssertionError("bars_fetcher must NOT be called in quotes_only mode")


def _fake_quotes(batch, start_dt, end_dt):
    """Injected NBBO fetcher — ticks across the regular session, no network."""
    out = {}
    for s in batch:
        t0 = pd.Timestamp(start_dt) + pd.Timedelta(hours=14)  # ~10:00 ET
        rows = []
        for i in range(60):
            ts = t0 + pd.Timedelta(minutes=i)
            if ts >= pd.Timestamp(end_dt):
                break
            rows.append({"symbol": s, "timestamp": ts, "bid": 9.99, "ask": 10.01,
                         "bid_size": 100.0, "ask_size": 100.0, "conditions": "R"})
        out[s] = rows
    return out


def test_quotes_only_skips_bars_and_shared_writes(tmp_path):
    """--quotes-only must skip the daily/minute FETCH and the shared
    audit/manifest/ingestion writes (so parallel month-range workers can't race),
    while still fetching quotes for the existing minute universe."""
    lake = tmp_path / "lake"
    # Populate daily + minute + manifest with a normal run.
    run_configured_backfill(_config(), lake_root=lake, bars_fetcher=_fake_bars)
    manifest = layout.ingestion_manifest_path(lake)
    assert manifest.is_file()
    mtime0 = manifest.stat().st_mtime_ns

    # quotes-only: bars_fetcher must NOT be called (would raise); manifest must NOT
    # be rewritten; quotes for the minute universe (AAA) are written.
    result = run_configured_backfill(
        _config(quotes_only=True, quotes={"enabled": True, "batch_size_symbols": 10}),
        lake_root=lake, bars_fetcher=_raising_bars, quotes_fetcher=_fake_quotes)
    assert result["counts"]["quotes"]["pairs_written"] >= 1
    assert manifest.stat().st_mtime_ns == mtime0  # shared bookkeeping untouched
    assert layout.quotes_path(lake, "AAA", 2024, 9, feed="iex").is_file()


def test_run_configured_backfill_writes_the_lake(tmp_path):
    lake = tmp_path / "lake"
    result = run_configured_backfill(_config(), lake_root=lake, bars_fetcher=_fake_bars)
    assert result["feed"] == "iex"
    assert layout.daily_bars_path(lake, "AAA", feed="iex").is_file()
    assert layout.daily_bars_path(lake, "BBB", feed="iex").is_file()
    minute_dir = layout.minute_bars_symbol_dir(lake, "AAA", feed="iex")
    assert any(minute_dir.rglob("part.parquet"))
    assert layout.ingestion_manifest_path(lake).is_file()


def test_rerun_is_incremental(tmp_path):
    lake = tmp_path / "lake"
    run_configured_backfill(_config(), lake_root=lake, bars_fetcher=_fake_bars)
    second = run_configured_backfill(_config(), lake_root=lake, bars_fetcher=_fake_bars)
    # daily: every symbol already up to date — nothing re-written
    assert second["counts"]["daily"]["symbols_written"] == 0
    assert second["counts"]["daily"]["symbols_up_to_date"] == 2
    # minute: every (symbol, session) already covered — resume skips them
    assert second["counts"]["minute"]["pairs_written"] == 0
    assert second["counts"]["minute"]["pairs_skipped_resume"] > 0


def test_extending_end_date_fetches_only_the_tail(tmp_path):
    lake = tmp_path / "lake"
    run_configured_backfill(_config(end_date="2024-09-10"), lake_root=lake, bars_fetcher=_fake_bars)
    extended = run_configured_backfill(
        _config(end_date="2024-09-20"), lake_root=lake, bars_fetcher=_fake_bars
    )
    # the symbols already on disk are extended in place, not re-written from scratch
    assert extended["counts"]["daily"]["symbols_extended"] == 2
    assert extended["counts"]["daily"]["symbols_written"] == 0


def test_feed_switch_writes_a_separate_partition(tmp_path):
    lake = tmp_path / "lake"
    run_configured_backfill(_config(feed="iex"), lake_root=lake, bars_fetcher=_fake_bars)
    run_configured_backfill(_config(feed="sip"), lake_root=lake, bars_fetcher=_fake_bars)
    assert layout.daily_bars_path(lake, "AAA", feed="iex").is_file()
    assert layout.daily_bars_path(lake, "AAA", feed="sip").is_file()
    # the iex partition is untouched by the sip run
    assert "feed=iex" in layout.daily_bars_path(lake, "AAA", feed="iex").parts
    assert "feed=sip" in layout.daily_bars_path(lake, "AAA", feed="sip").parts


def test_minute_policy_none_skips_minute_stage(tmp_path):
    lake = tmp_path / "lake"
    cfg = _config(minute_bars={"enabled": True, "policy": "none"})
    result = run_configured_backfill(cfg, lake_root=lake, bars_fetcher=_fake_bars)
    assert result["counts"]["minute"] == {}
    assert layout.daily_bars_path(lake, "AAA", feed="iex").is_file()


def test_resolve_end_date():
    auto = resolve_end_date("auto")
    assert auto == dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=1)
    assert resolve_end_date(None) == auto
    assert resolve_end_date("2025-06-15") == dt.date(2025, 6, 15)


def test_load_backfill_config_validates(tmp_path):
    good = tmp_path / "good.yml"
    good.write_text("start_date: 2024-01-01\nfeed: sip\n", encoding="utf-8")
    assert load_backfill_config(good)["feed"] == "sip"

    bad_feed = tmp_path / "bad_feed.yml"
    bad_feed.write_text("start_date: 2024-01-01\nfeed: nasdaq\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_backfill_config(bad_feed)

    no_start = tmp_path / "no_start.yml"
    no_start.write_text("feed: iex\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_backfill_config(no_start)

    bad_policy = tmp_path / "bad_policy.yml"
    bad_policy.write_text("start_date: 2024-01-01\nminute_bars:\n  policy: random\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_backfill_config(bad_policy)


def test_repo_backfill_config_is_valid(repo_root):
    cfg = load_backfill_config(repo_root / "config" / "marketdata_backfill.yml")
    assert cfg["feed"] in ("iex", "sip")
    assert "start_date" in cfg
