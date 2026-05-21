"""Backfill stages against injected fetchers — no network, no alpaca needed."""
from __future__ import annotations

import datetime as dt
import logging
import types

import pandas as pd

from bowaka_common.marketdata import backfill, layout

_LOG = logging.getLogger("test_marketdata_backfill")


def _cfg(tmp_path, **kw):
    base = dict(
        api_key="k",
        api_secret="s",
        paper=True,
        feed="iex",
        start_date=dt.date(2026, 5, 1),
        end_date=dt.date(2026, 5, 5),
        lake_root=tmp_path,
    )
    base.update(kw)
    return backfill.BackfillConfig(**base)


def _asset(symbol, name, *, tradable=True, exchange="NASDAQ"):
    return types.SimpleNamespace(
        symbol=symbol,
        name=name,
        tradable=tradable,
        exchange=exchange,
        marginable=True,
        shortable=True,
        fractionable=True,
        status="active",
    )


def _daily_rows(symbol, dates):
    return [
        {
            "symbol": symbol,
            "timestamp": pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20),
            "open": 10.0, "high": 11.0, "low": 9.5, "close": 10.5, "volume": 100000,
        }
        for d in dates
    ]


def _minute_rows(symbol, session):
    return [
        {
            "symbol": symbol,
            "timestamp": pd.Timestamp(session, tz="UTC") + pd.Timedelta(hours=14),
            "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 1000,
        }
    ]


def test_fetch_assets_filters_and_writes(tmp_path):
    cfg = _cfg(tmp_path)
    raw = [
        _asset("AAA", "Aaa Industries"),
        _asset("BBB", "Bbb Holdings"),
        _asset("ETFY", "Some Index ETF Trust"),      # name pattern → excluded
        _asset("DEAD", "Dead Co", tradable=False),   # not tradable → excluded
        _asset("OTCX", "Otc Co", exchange="OTC"),    # exchange → excluded
    ]
    snap, df = backfill.fetch_assets(cfg, _LOG, assets_fetcher=lambda: raw)
    assert set(df["symbol"]) == {"AAA", "BBB"}
    assert layout.assets_path(tmp_path, snap).is_file()


def test_fetch_daily_bars_writes_per_symbol(tmp_path):
    cfg = _cfg(tmp_path, resume=False)
    assets_df = pd.DataFrame({"symbol": ["AAA", "BBB"]})

    def fake(batch, timeframe, start, end):
        assert timeframe == "1d"
        return {s: _daily_rows(s, [dt.date(2026, 4, 1), dt.date(2026, 4, 2)]) for s in batch}

    stats = backfill.fetch_daily_bars(cfg, assets_df, _LOG, backfill.RateLimiter(100000), bars_fetcher=fake)
    assert stats["symbols_written"] == 2
    got = pd.read_parquet(backfill.daily_file(cfg, "AAA"))
    assert "session_date" in got.columns
    assert len(got) == 2


def test_fetch_minute_bars_groups_per_symbol_month(tmp_path):
    cfg = _cfg(tmp_path)
    targets = pd.DataFrame(
        [
            {"session_date": dt.date(2026, 5, 1), "symbol": "AAA"},
            {"session_date": dt.date(2026, 5, 2), "symbol": "AAA"},
        ]
    )

    def fake(batch, timeframe, start, end):
        assert timeframe == "1m"
        return {s: _minute_rows(s, start.date()) for s in batch}

    stats = backfill.fetch_minute_bars(cfg, targets, _LOG, backfill.RateLimiter(100000), bars_fetcher=fake)
    assert stats["pairs_written"] == 2
    month_file = backfill.minute_file(cfg, "AAA", 2026, 5)
    assert month_file.is_file()
    # both sessions land in the single May month-file
    assert len(pd.read_parquet(month_file)) == 2


def test_fetch_minute_bars_resume_skips_done_pairs(tmp_path):
    cfg = _cfg(tmp_path)
    targets = pd.DataFrame([{"session_date": dt.date(2026, 5, 1), "symbol": "AAA"}])

    def fake(batch, timeframe, start, end):
        return {s: _minute_rows(s, start.date()) for s in batch}

    first = backfill.fetch_minute_bars(cfg, targets, _LOG, backfill.RateLimiter(100000), bars_fetcher=fake)
    second = backfill.fetch_minute_bars(cfg, targets, _LOG, backfill.RateLimiter(100000), bars_fetcher=fake)
    assert first["pairs_written"] == 1
    assert second["pairs_written"] == 0
    assert second["pairs_skipped_resume"] == 1


def test_run_backfill_orchestrates(tmp_path):
    cfg = _cfg(tmp_path, resume=False)

    def fake_bars(batch, timeframe, start, end):
        return {s: _daily_rows(s, [dt.date(2026, 4, 1)]) for s in batch}

    result = backfill.run_backfill(
        cfg,
        _LOG,
        assets_fetcher=lambda: [_asset("AAA", "Aaa Co")],
        bars_fetcher=fake_bars,
    )
    assert result["assets_count"] == 1
    assert layout.ingestion_manifest_path(tmp_path).is_file()
    assert layout.ingestion_run_path(tmp_path, result["ingestion_run_id"]).is_file()
