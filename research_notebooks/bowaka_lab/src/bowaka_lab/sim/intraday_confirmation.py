"""Intraday-confirmation simulator — semantic parity with source ``_confirm_entry``.

Source: ``reference/source_strategy/scripts/bowaka_strategy.py`` lines 1943-1991.
The lab port replicates the same gate sequence (validity → spread → quote age →
price band) but drops production logging and the live-quote try/except wrapper
around float coercion. Fail reasons are stable strings the engine writes to
``entry_skips.parquet`` and the report.

Sequence:

1. bid/ask validity. ``ask <= bid`` → ``no_quote``; float coercion failure →
   ``bad_bid_ask``.
2. spread / mid > ``max_spread_pct`` → ``"spread>{max_spread_pct:.4f}"``.
3. quote age > ``max_quote_age_seconds`` →
   ``"quote_age>{max_quote_age_seconds:.0f}s"`` (or ``bad_quote_timestamp``).
4. mid > close × (1 + ``max_above``) → ``"chase>{max_above}"``.
5. mid < close × (1 + ``min_below``) → ``"failure<{min_below}"``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd


@dataclass(frozen=True)
class ConfirmationResult:
    passed: bool
    fail_reason: str | None
    mid: float | None
    spread_pct: float | None
    quote_age_seconds: float | None


def confirm_entry(
    *,
    candidate_close: float,
    quote_row: pd.Series | dict | None,
    now_utc: pd.Timestamp,
    max_spread_pct: float,
    max_quote_age_seconds: float,
    price_band_max_above: float,
    price_band_min_below: float,
) -> ConfirmationResult:
    """Apply the intraday gates against ``quote_row``.

    Returns ``ConfirmationResult(passed, fail_reason, mid, spread_pct,
    quote_age_seconds)``. ``fail_reason`` is None on pass; otherwise a short
    label matching source semantics.
    """
    if quote_row is None:
        return ConfirmationResult(False, "no_quote", None, None, None)

    try:
        bid = float(_get(quote_row, "bid_price", _get(quote_row, "bid", 0.0)) or 0.0)
        ask = float(_get(quote_row, "ask_price", _get(quote_row, "ask", 0.0)) or 0.0)
    except (TypeError, ValueError):
        return ConfirmationResult(False, "bad_bid_ask", None, None, None)

    if bid <= 0 or ask <= 0 or ask <= bid:
        return ConfirmationResult(False, "no_quote", None, None, None)

    mid = (bid + ask) / 2.0
    spread_pct = (ask - bid) / mid

    if max_spread_pct > 0 and spread_pct > max_spread_pct:
        return ConfirmationResult(
            False, f"spread>{max_spread_pct:.4f}", mid, spread_pct, None
        )

    quote_age_seconds: float | None = None
    if max_quote_age_seconds > 0:
        ts = _get(quote_row, "timestamp")
        try:
            quote_dt = _to_utc(ts)
        except ValueError:
            return ConfirmationResult(False, "bad_quote_timestamp", mid, spread_pct, None)
        if quote_dt is not None:
            quote_age_seconds = (_to_utc(now_utc) - quote_dt).total_seconds()
            if quote_age_seconds > max_quote_age_seconds:
                return ConfirmationResult(
                    False,
                    f"quote_age>{max_quote_age_seconds:.0f}s",
                    mid, spread_pct, quote_age_seconds,
                )

    if candidate_close > 0 and price_band_max_above is not None:
        if mid > candidate_close * (1.0 + float(price_band_max_above)):
            return ConfirmationResult(
                False, f"chase>{price_band_max_above}", mid, spread_pct, quote_age_seconds,
            )
    if candidate_close > 0 and price_band_min_below is not None:
        if mid < candidate_close * (1.0 + float(price_band_min_below)):
            return ConfirmationResult(
                False, f"failure<{price_band_min_below}", mid, spread_pct, quote_age_seconds,
            )

    return ConfirmationResult(True, None, mid, spread_pct, quote_age_seconds)


def _get(obj, key, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    if hasattr(obj, "get"):
        try:
            return obj.get(key, default)
        except Exception:
            pass
    return getattr(obj, key, default)


def _to_utc(ts) -> datetime | None:
    """Coerce ``ts`` (str, pd.Timestamp, datetime) to a tz-aware UTC datetime.

    Raises ``ValueError`` for unparseable strings (matches source's
    ``bad_quote_timestamp`` branch).
    """
    if ts is None:
        return None
    if isinstance(ts, str):
        # Accept both `Z` and `+HH:MM` ISO strings.
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            raise
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    if isinstance(ts, pd.Timestamp):
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        return ts.to_pydatetime()
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts
    # Last resort — try pandas coercion.
    try:
        dt = pd.Timestamp(ts)
        if dt.tzinfo is None:
            dt = dt.tz_localize("UTC")
        return dt.to_pydatetime()
    except Exception:
        raise ValueError(f"Cannot coerce timestamp: {ts!r}")


def latest_quote_at_or_before(
    quotes_df: pd.DataFrame, ts: pd.Timestamp
) -> dict | None:
    """Return the newest quote whose timestamp is <= ``ts`` from ``quotes_df``,
    or ``None`` if no such row exists.
    """
    if quotes_df is None or quotes_df.empty:
        return None
    df = quotes_df
    if "timestamp" not in df.columns:
        return None
    target = pd.Timestamp(ts)
    if target.tzinfo is None:
        target = target.tz_localize("UTC")
    eligible = df[pd.to_datetime(df["timestamp"], utc=True) <= target]
    if eligible.empty:
        return None
    row = eligible.iloc[-1]
    return row.to_dict()
