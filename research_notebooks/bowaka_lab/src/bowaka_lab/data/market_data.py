"""bowaka_lab access to the shared market-data lake.

v1 reads the canonical lake through the same ``bowaka_common.marketdata`` layer
that ``bowaka_v2_lab`` uses — the lake is strategy-neutral and neither lab owns
the on-disk layout. v1's strategy-specific universe construction (the "scope-3"
ADV gate) is provided here as :func:`scope_3_universe`, layered on top of
:class:`MarketDataStore` reads.

The legacy standalone backfill (``db_tools/_backfill_lib.py``) is retained as-is
for the existing Mongo-backed workflow; the canonical Parquet-only backfill is
``bowaka_common.marketdata.run_backfill``.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any, Iterable

import pandas as pd

from bowaka_common.marketdata import (
    MarketDataStore,
    available_symbols,
    dataset_hash,
    date_coverage,
    resolve_market_data_root,
)

__all__ = [
    "MarketDataStore",
    "resolve_market_data_root",
    "available_symbols",
    "date_coverage",
    "dataset_hash",
    "open_market_data_store",
    "scope_3_universe",
]


def open_market_data_store(
    root: str | Any | None = None, *, vendor: str = "alpaca"
) -> MarketDataStore:
    """Open the shared market-data lake for v1 reads."""
    return MarketDataStore(root, vendor=vendor)


def _to_date(x: Any) -> _dt.date:
    if isinstance(x, _dt.datetime):
        return x.date()
    if isinstance(x, _dt.date):
        return x
    return pd.Timestamp(x).date()


def scope_3_universe(
    store: MarketDataStore,
    symbols: Iterable[str],
    start: Any,
    end: Any,
    *,
    price_min: float = 1.0,
    price_max: float = 20.0,
    adv_min: float = 200_000.0,
    adv_window_days: int = 20,
    feed: str = "iex",
    adjustment: str = "raw",
) -> pd.DataFrame:
    """v1 "scope-3" ADV-gated universe, computed from shared-lake daily bars.

    For each session_date ``D`` and ``symbol``, ``D`` is in scope when:

    - ``close`` on ``D`` is within ``[price_min, price_max]``;
    - the rolling ADV over the prior ``adv_window_days`` sessions **excluding D**
      (no-lookahead — ``shift(1).rolling(N).mean()``) is ``>= adv_min``;
    - ``D`` is within ``[start, end]``.

    Returns a DataFrame with columns ``session_date`` and ``symbol``. This is the
    strategy-specific universe logic that previously lived in the standalone
    backfill — it now reads the shared lake rather than a v1-private parquet tree.
    """
    start_d, end_d = _to_date(start), _to_date(end)
    # Warmup pad so the rolling ADV is already valid on ``start_d``.
    pad_days = int(adv_window_days * 1.5) + 7
    fetch_start = start_d - _dt.timedelta(days=pad_days)

    frames: list[pd.DataFrame] = []
    for symbol in symbols:
        df = store.daily_bars(symbol, fetch_start, end_d, feed=feed, adjustment=adjustment)
        if df.empty:
            continue
        df = df.copy()
        if "session_date" in df.columns:
            df["session_date"] = pd.to_datetime(df["session_date"]).dt.date
        else:
            df["session_date"] = (
                pd.to_datetime(df["timestamp"], utc=True)
                .dt.tz_convert("America/New_York")
                .dt.date
            )
        df = df.sort_values("session_date").reset_index(drop=True)
        df["dollar_volume"] = df["close"] * df["volume"]
        df["adv"] = df["dollar_volume"].shift(1).rolling(adv_window_days).mean()
        mask = (
            df["adv"].notna()
            & df["close"].between(price_min, price_max, inclusive="both")
            & (df["adv"] >= adv_min)
            & (df["session_date"] >= start_d)
            & (df["session_date"] <= end_d)
        )
        selected = df.loc[mask, ["session_date"]].copy()
        selected["symbol"] = symbol
        frames.append(selected[["session_date", "symbol"]])

    if not frames:
        return pd.DataFrame(columns=["session_date", "symbol"])
    return (
        pd.concat(frames, ignore_index=True)
        .sort_values(["session_date", "symbol"])
        .reset_index(drop=True)
    )
