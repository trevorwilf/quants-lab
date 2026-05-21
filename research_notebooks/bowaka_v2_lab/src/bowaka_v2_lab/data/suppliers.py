"""Lake-backed suppliers for the v2 backtester.

Bridges ``bowaka_common.marketdata.MarketDataStore`` to the callable suppliers
that ``run_backtest`` / ``replay`` expect, plus a no-lookahead daily-feature
cache builder. This is the v2 counterpart of the synthetic fixtures in
``sim/replay_fixtures.py`` — same shapes, real data.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any, Callable, Iterable

import pandas as pd

from bowaka_common.marketdata import MarketDataStore

#: Columns of the v2 daily-feature cache (mirrors ``synthetic_daily_cache``).
DAILY_CACHE_COLUMNS = [
    "symbol",
    "prior_close",
    "avg_volume_20d",
    "avg_dollar_volume_20d",
    "prior_atr_14d",
    "prior_atr_pct",
    "ema_10_prior",
    "ema_10_lag_3",
    "ema_slope_prior",
]


def _as_date(x: Any) -> _dt.date:
    if isinstance(x, _dt.datetime):
        return x.date()
    if isinstance(x, _dt.date):
        return x
    return pd.Timestamp(x).date()


def _as_store(store_or_root: Any, *, vendor: str) -> MarketDataStore:
    if isinstance(store_or_root, MarketDataStore):
        return store_or_root
    return MarketDataStore(store_or_root, vendor=vendor)


def make_lake_suppliers(
    shared_root: str | Path | None = None,
    *,
    feed: str = "iex",
    vendor: str = "alpaca",
    daily_lookback_days: int = 400,
) -> tuple[Callable[[str, Any], pd.DataFrame], Callable[[str, Any], pd.DataFrame]]:
    """Return ``(minute_bars_supplier, daily_bars_supplier)`` reading the shared lake.

    - ``minute_bars_supplier(symbol, cutoff)`` → that session's minute bars up to
      ``cutoff`` (tz-aware).
    - ``daily_bars_supplier(symbol, session_date)`` → daily bars over the trailing
      ``daily_lookback_days`` ending on ``session_date``.
    """
    store = _as_store(shared_root, vendor=vendor)

    def minute_bars_supplier(symbol: str, cutoff: Any) -> pd.DataFrame:
        ts = pd.Timestamp(cutoff)
        ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
        session_date = ts.tz_convert("America/New_York").date()
        session_start = pd.Timestamp(session_date, tz="UTC")
        return store.minute_bars(symbol, session_start, ts, feed=feed)

    def daily_bars_supplier(symbol: str, session_date: Any) -> pd.DataFrame:
        end = _as_date(session_date)
        start = end - _dt.timedelta(days=daily_lookback_days)
        return store.daily_bars(symbol, start, end, feed=feed)

    return minute_bars_supplier, daily_bars_supplier


def build_daily_cache_from_lake(
    store_or_root: Any,
    symbols: Iterable[str],
    session_date: Any,
    *,
    feed: str = "iex",
    vendor: str = "alpaca",
    atr_window: int = 14,
    vol_window: int = 20,
    ema_span: int = 10,
    lookback_days: int = 400,
) -> pd.DataFrame:
    """Build the v2 daily-feature cache as-of the session **before** ``session_date``.

    No-lookahead: every value uses only sessions strictly earlier than
    ``session_date``. Returns a DataFrame with :data:`DAILY_CACHE_COLUMNS`.
    """
    store = _as_store(store_or_root, vendor=vendor)
    target = _as_date(session_date)
    rows: list[dict[str, Any]] = []
    for symbol in symbols:
        df = store.daily_bars(
            symbol, target - _dt.timedelta(days=lookback_days), target, feed=feed
        )
        if df.empty:
            continue
        if "session_date" in df.columns:
            sd = pd.to_datetime(df["session_date"]).dt.date
        else:
            sd = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("America/New_York").dt.date
        prior = df.assign(_sd=sd)
        prior = prior[prior["_sd"] < target].sort_values("_sd").reset_index(drop=True)
        if prior.empty:
            continue
        close = prior["close"].astype(float)
        high = prior["high"].astype(float)
        low = prior["low"].astype(float)
        volume = prior["volume"].astype(float)
        prev_close = close.shift(1)
        true_range = pd.concat(
            [(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1
        ).max(axis=1)
        atr = true_range.rolling(atr_window).mean()
        ema = close.ewm(span=ema_span, adjust=False).mean()
        prior_close = float(close.iloc[-1])
        prior_atr = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0.0
        ema_prior = float(ema.iloc[-1])
        ema_lag3 = float(ema.iloc[-4]) if len(ema) >= 4 else ema_prior
        rows.append(
            {
                "symbol": symbol,
                "prior_close": prior_close,
                "avg_volume_20d": float(volume.tail(vol_window).mean()),
                "avg_dollar_volume_20d": float((close * volume).tail(vol_window).mean()),
                "prior_atr_14d": prior_atr,
                "prior_atr_pct": (prior_atr / prior_close) if prior_close else 0.0,
                "ema_10_prior": ema_prior,
                "ema_10_lag_3": ema_lag3,
                "ema_slope_prior": (ema_prior - ema_lag3) / 3.0,
            }
        )
    if not rows:
        return pd.DataFrame(columns=DAILY_CACHE_COLUMNS)
    return pd.DataFrame(rows, columns=DAILY_CACHE_COLUMNS)
