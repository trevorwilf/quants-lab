"""P7 §3.4/§5.3 — PIT survivorship + min-history drive the universe builder.

The CA-derived PIT master (corporate_actions/ partition) drops a symbol delisted /
renamed AS OF the session; ``min_history_trading_days`` drops a too-short history; and
blank asset-master status is no longer silently treated as active. Graceful: a lake
with NO corporate_actions/ partition leaves the asset-master status gate in charge.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from bowaka_common.marketdata import MarketDataStore, layout
from bowaka_v2_lab.universe.builder import (
    _pit_daily_history_cache_clear,
    _status_active,
    build_pit_universe,
)
from tests.fixtures.universe_fixture import write_lake_asset_master


def _write(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _daily(symbol: str, start: dt.date, end: dt.date, close: float = 10.0) -> pd.DataFrame:
    days = [d.date() for d in pd.bdate_range(start, end)]
    return pd.DataFrame({
        "symbol": [symbol] * len(days),
        "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in days],
        "open": [close] * len(days), "high": [close * 1.01] * len(days),
        "low": [close * 0.99] * len(days), "close": [close] * len(days),
        "volume": [1_000_000] * len(days), "session_date": days,
    })


def _ca_row(ca_type: str, symbol: str, effective_date: str, *, is_delisting=False,
            is_symbol_change=False, new_symbol=None) -> dict:
    return {
        "ca_type": ca_type, "symbol": symbol, "old_symbol": None, "new_symbol": new_symbol,
        "effective_date": effective_date, "ex_date": None, "process_date": effective_date,
        "record_date": None, "payable_date": None, "old_rate": None, "new_rate": None,
        "rate": None, "cusip": None, "id": f"{symbol}-{effective_date}",
        "is_delisting": is_delisting, "is_symbol_change": is_symbol_change, "is_split": False,
    }


def _write_ca(lake: Path, symbol: str, rows: list[dict]) -> None:
    _write(layout.corporate_actions_path(lake, symbol, vendor="alpaca"), pd.DataFrame(rows))


def _cfg(lake: Path, *, min_history: int = 45) -> dict:
    return {
        "market_data": {"feed": "iex", "shared_root": str(lake)},
        "simulation": {"mode": "current_code_parity"},
        "universe": {"min_price": 1.0, "max_price": 1_000.0, "min_adv_dollars": 0,
                     "min_history_trading_days": min_history},
    }


def test_status_active_blank_is_not_active() -> None:
    """§3.4: the ``_status_active("")`` blank-is-active no-op survivorship bug is fixed."""
    assert _status_active("active") is True
    assert _status_active("active_tradable") is True
    assert _status_active("inactive") is False
    assert _status_active("") is False
    assert _status_active(None) is False
    assert _status_active("  ") is False


def test_pit_delisting_drops_symbol_only_after_effective_date(tmp_path: Path) -> None:
    _pit_daily_history_cache_clear()
    lake = tmp_path / "lake"
    for s in ("LIVE", "DEAD"):
        _write(layout.daily_bars_path(lake, s, feed="iex", adjustment="raw"),
               _daily(s, dt.date(2024, 1, 1), dt.date(2024, 9, 3)))
    # DEAD is removed (worthless) effective 2024-08-01 — though its asset-master status
    # is still "active", the CA-derived PIT master must drop it from 2024-08-01 on.
    _write_ca(lake, "DEAD", [_ca_row("worthless_removals", "DEAD", "2024-08-01", is_delisting=True)])
    write_lake_asset_master(lake, ["LIVE", "DEAD"])
    store = MarketDataStore(lake)

    post = build_pit_universe(dt.date(2024, 9, 4), _cfg(lake), store)
    assert post["LIVE"].eligible_for_bowaka_equity_bucket is True
    assert post["DEAD"].eligible_for_bowaka_equity_bucket is False
    assert "delisted" in post["DEAD"].rejection_reasons

    _pit_daily_history_cache_clear()
    pre = build_pit_universe(dt.date(2024, 7, 15), _cfg(lake), store)  # before the removal
    assert pre["DEAD"].eligible_for_bowaka_equity_bucket is True
    _pit_daily_history_cache_clear()


def test_pit_rename_drops_old_symbol_after_effective_date(tmp_path: Path) -> None:
    _pit_daily_history_cache_clear()
    lake = tmp_path / "lake"
    _write(layout.daily_bars_path(lake, "OLD", feed="iex", adjustment="raw"),
           _daily("OLD", dt.date(2024, 1, 1), dt.date(2024, 9, 3)))
    _write_ca(lake, "OLD", [_ca_row("name_changes", "OLD", "2024-08-01",
                                    is_symbol_change=True, new_symbol="NEW")])
    write_lake_asset_master(lake, ["OLD"])
    store = MarketDataStore(lake)
    u = build_pit_universe(dt.date(2024, 9, 4), _cfg(lake), store)
    assert u["OLD"].eligible_for_bowaka_equity_bucket is False
    assert "renamed_away" in u["OLD"].rejection_reasons
    _pit_daily_history_cache_clear()


def test_min_history_gate_rejects_short_history(tmp_path: Path) -> None:
    _pit_daily_history_cache_clear()
    lake = tmp_path / "lake"
    _write(layout.daily_bars_path(lake, "LONG", feed="iex", adjustment="raw"),
           _daily("LONG", dt.date(2024, 1, 1), dt.date(2024, 9, 3)))      # ~170 bars
    _write(layout.daily_bars_path(lake, "SHORT", feed="iex", adjustment="raw"),
           _daily("SHORT", dt.date(2024, 8, 20), dt.date(2024, 9, 3)))    # ~11 bars
    write_lake_asset_master(lake, ["LONG", "SHORT"])
    store = MarketDataStore(lake)

    u = build_pit_universe(dt.date(2024, 9, 4), _cfg(lake, min_history=45), store)
    assert u["LONG"].eligible_for_bowaka_equity_bucket is True
    assert "insufficient_history" in u["SHORT"].rejection_reasons

    _pit_daily_history_cache_clear()
    off = build_pit_universe(dt.date(2024, 9, 4), _cfg(lake, min_history=0), store)
    assert "insufficient_history" not in off["SHORT"].rejection_reasons
    _pit_daily_history_cache_clear()


def test_no_ca_partition_is_graceful_noop(tmp_path: Path) -> None:
    """No corporate_actions/ partition -> the PIT gate is a no-op (asset-master status
    governs); the universe still builds (the common pre-CA-backfill / fixture case)."""
    _pit_daily_history_cache_clear()
    lake = tmp_path / "lake"
    _write(layout.daily_bars_path(lake, "AAA", feed="iex", adjustment="raw"),
           _daily("AAA", dt.date(2024, 1, 1), dt.date(2024, 9, 3)))
    write_lake_asset_master(lake, ["AAA"])
    u = build_pit_universe(dt.date(2024, 9, 4), _cfg(lake, min_history=0), MarketDataStore(lake))
    assert u["AAA"].eligible_for_bowaka_equity_bucket is True
    _pit_daily_history_cache_clear()
