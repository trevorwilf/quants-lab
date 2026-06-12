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


# --- PA.3: exchange/tape coercion + canonical-sampler byte-identity --------

def _quote_ticks(symbol, session):
    """Coerce raw NBBO quote dicts that carry the new exchange/tape fields."""
    base = pd.Timestamp(session, tz="UTC") + pd.Timedelta(hours=14)
    raw = [
        {"symbol": symbol, "t": base, "bp": 9.99, "ap": 10.01, "bs": 100, "as": 200,
         "c": ["R"], "bx": "V", "ax": "Q", "z": "C"},
        {"symbol": symbol, "t": base + pd.Timedelta(seconds=30), "bp": 9.98, "ap": 10.02,
         "bs": 150, "as": 250, "c": ["R"], "bx": "P", "ax": "Z", "z": "C"},
    ]
    return [backfill._coerce_quote_row(symbol, q) for q in raw]


def test_coerce_quote_row_carries_exchange_tape():
    rows = _quote_ticks("AAA", dt.date(2026, 5, 1))
    assert rows[0]["bid_exchange"] == "V"
    assert rows[0]["ask_exchange"] == "Q"
    assert rows[0]["tape"] == "C"


def test_canonical_sampler_drops_exchange_tape_columns():
    # The canonical 1/min sampler MUST project to the 7 canonical columns so the
    # PA.3 exchange/tape additions never reach the canonical quotes/ tree (keeping
    # quote_partitions_hash byte-identical).
    session = dt.date(2026, 5, 1)
    ticks = pd.DataFrame(_quote_ticks("AAA", session))
    ticks["timestamp"] = pd.to_datetime(ticks["timestamp"], utc=True)
    out = backfill._sample_session_nbbo(ticks, session)
    assert list(out.columns) == [
        "symbol", "timestamp", "bid", "ask", "bid_size", "ask_size", "conditions"]
    for dropped in ("bid_exchange", "ask_exchange", "tape"):
        assert dropped not in out.columns


def test_fetch_trades_writes_raw_preserving_prints(tmp_path):
    cfg = _cfg(tmp_path)
    targets = pd.DataFrame([{"session_date": dt.date(2026, 5, 1), "symbol": "AAA"}])

    def fake(batch, start_dt, end_dt):
        base = pd.Timestamp(start_dt) + pd.Timedelta(hours=14)
        return {s: [
            {"symbol": s, "timestamp": base, "price": 10.0, "size": 100.0,
             "exchange": "V", "conditions": "@", "tape": "C", "trade_id": 1},
            {"symbol": s, "timestamp": base, "price": 10.01, "size": 50.0,
             "exchange": "V", "conditions": "@", "tape": "C", "trade_id": 2},
        ] for s in batch}

    stats = backfill.fetch_trades(cfg, targets, _LOG, backfill.RateLimiter(100000),
                                  trades_fetcher=fake)
    assert stats["pairs_written"] == 1
    tfile = layout.trades_path(tmp_path, "AAA", 2026, 5, feed="iex")
    assert tfile.is_file()
    df = pd.read_parquet(tfile)
    assert len(df) == 2  # both prints sharing the timestamp survive (no ts-dedup)
    assert set(df["trade_id"]) == {1, 2}


def test_fetch_quotes_fine_keeps_exchange_codes_on_sibling_path(tmp_path):
    cfg = _cfg(tmp_path)
    targets = pd.DataFrame([{"session_date": dt.date(2026, 5, 1), "symbol": "AAA"}])

    def fake(batch, start_dt, end_dt):
        base = pd.Timestamp(start_dt) + pd.Timedelta(hours=14)
        return {s: [
            {"symbol": s, "timestamp": base + pd.Timedelta(seconds=10 * i),
             "bid": 9.99, "ask": 10.01, "bid_size": 100.0, "ask_size": 200.0,
             "conditions": "R", "bid_exchange": "V", "ask_exchange": "Q", "tape": "C"}
            for i in range(5)
        ] for s in batch}

    stats = backfill.fetch_quotes_fine(cfg, targets, _LOG, backfill.RateLimiter(100000),
                                       quotes_fetcher=fake)  # samples_per_minute=None -> raw
    assert stats["pairs_written"] == 1
    fpath = layout.quotes_fine_path(tmp_path, "AAA", 2026, 5, feed="iex")
    assert fpath.is_file()
    df = pd.read_parquet(fpath)
    assert len(df) == 5  # raw ticks (no sampling)
    for col in ("bid_exchange", "ask_exchange", "tape"):
        assert col in df.columns
    # the fine stage writes ONLY the sibling path, never the canonical quotes/
    assert not layout.quotes_path(tmp_path, "AAA", 2026, 5, feed="iex").is_file()
