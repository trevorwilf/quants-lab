"""Shared fixtures for the Phase-3 point-in-time universe-builder tests.

A :class:`FakeLakeStore` stands in for ``bowaka_common.marketdata.MarketDataStore``
— it serves a fixed asset master plus per-symbol daily bars, with the same
``assets`` / ``latest_snapshot_id`` / ``daily_bars`` surface the PIT builder
calls.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any

import pandas as pd


class FakeLakeStore:
    """In-memory lake store: an asset master + per-symbol daily-bar frames."""

    def __init__(
        self,
        asset_master: pd.DataFrame,
        daily: dict[str, pd.DataFrame],
        *,
        snapshot_id: str = "test_snapshot_2024",
    ) -> None:
        self._asset_master = asset_master
        self._daily = daily
        self._snapshot_id = snapshot_id

    def latest_snapshot_id(self) -> str:
        return self._snapshot_id

    def assets(self, snapshot_id: str | None = None) -> pd.DataFrame:
        return self._asset_master

    def daily_bars(
        self, symbol: str, start: Any, end: Any, *, feed: str = "iex", adjustment: str = "raw"
    ) -> pd.DataFrame:
        df = self._daily.get(symbol, pd.DataFrame())
        if df.empty:
            return df
        sd = pd.to_datetime(df["session_date"]).dt.date
        s = start if isinstance(start, _dt.date) else pd.Timestamp(start).date()
        e = end if isinstance(end, _dt.date) else pd.Timestamp(end).date()
        return df[(sd >= s) & (sd <= e)].reset_index(drop=True)


def daily_bars_frame(
    symbol: str,
    *,
    end_before: _dt.date,
    n_sessions: int = 30,
    close: float = 10.0,
    volume: float = 500_000.0,
) -> pd.DataFrame:
    """``n_sessions`` daily bars ending the business day before ``end_before``.

    Default close $10 × 500k volume → $5M 20-day ADV, comfortably inside the
    contract price band ($1-20) and over the $250k ADV minimum.
    """
    days = [
        d.date()
        for d in pd.bdate_range(end=end_before - _dt.timedelta(days=1), periods=n_sessions)
    ]
    return pd.DataFrame(
        {
            "symbol": [symbol] * len(days),
            "session_date": days,
            "open": [close] * len(days),
            "high": [close * 1.01] * len(days),
            "low": [close * 0.99] * len(days),
            "close": [close] * len(days),
            "volume": [float(volume)] * len(days),
        }
    )


def asset_master_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Build an asset-master frame, filling sensible defaults per row.

    Each ``rows`` dict needs at least ``symbol``; ``name`` / ``exchange`` /
    ``status`` / ``tradable`` default to an active NASDAQ operating equity.
    """
    filled: list[dict[str, Any]] = []
    for r in rows:
        sym = r["symbol"]
        filled.append(
            {
                "snapshot_id": "test_snapshot_2024",
                "symbol": sym,
                "name": r.get("name", f"{sym} Holdings Inc."),
                "exchange": r.get("exchange", "NASDAQ"),
                "asset_class": r.get("asset_class", "us_equity"),
                "tradable": r.get("tradable", True),
                "marginable": r.get("marginable", True),
                "shortable": r.get("shortable", True),
                "fractionable": r.get("fractionable", True),
                "status": r.get("status", "active"),
            }
        )
    return pd.DataFrame(filled)


def write_lake_asset_master(
    lake_root: Any,
    symbols: list[str],
    *,
    snapshot_id: str = "test_snapshot_2024",
    exchange: str = "NASDAQ",
) -> str:
    """Write a minimal asset-master snapshot into a real lake directory.

    Used by the realism DQ tests, which build a physical lake and now also need
    a PIT-buildable asset master. Every symbol is an active operating equity.
    Returns the ``snapshot_id``.
    """
    from pathlib import Path

    from bowaka_common.marketdata import layout

    df = asset_master_frame([{"symbol": s, "exchange": exchange} for s in symbols])
    df["snapshot_id"] = snapshot_id
    path = layout.assets_path(Path(lake_root), snapshot_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return snapshot_id


def realism_cfg(**universe_overrides: Any) -> dict:
    """A non-smoke (``intended_realism``) config with the contract universe block."""
    universe = {
        "allowed_exchanges": ["NASDAQ", "NYSE", "AMEX", "ARCA", "BATS"],
        "exclude_otc": True,
        "price_min": 1.0,
        "price_max": 20.0,
        "avg_dollar_volume_min": 250_000,
        "ticker_blocklist": ["TSLL", "CONL", "SMCX"],
    }
    universe.update(universe_overrides)
    return {
        "universe": universe,
        "market_data": {"feed": "iex"},
        "simulation": {"mode": "intended_realism"},
    }
