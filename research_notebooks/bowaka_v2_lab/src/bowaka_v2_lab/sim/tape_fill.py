"""Trade-tape fill oracle (PB.4).

Replay the ACTUAL trade tape to compute the achievable VWAP + fill fraction for a
marketable order of a given size at a given time — the most faithful fill
obtainable without L2 depth-of-book. Consumes the raw per-print tape written by
``MarketDataStore.trades_between`` (PA.2).

This is a PURE function over a trades ``DataFrame``, so it is deterministic and
fully unit-testable against a synthetic-trades fixture before the real tape lands
(PA.4). The sim hooks (``fill_model="tape_replay"`` on entries + the sell-side
exit path) call it through a ``trades_supplier``; with the supplier absent or the
tape empty the result is an honest no-fill that the caller treats as "fall back to
the existing fill model".
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd


@dataclass(frozen=True)
class TapeFillResult:
    """Outcome of replaying the tape for one marketable order.

    ``avg_fill_price`` is the size-weighted VWAP of the consumed prints (``0.0``
    when nothing filled). ``filled`` is ``True`` only when the whole requested
    quantity was absorbed within the window; otherwise the order is a partial
    (``filled_qty < requested_qty``) or a no-fill.
    """

    filled: bool
    requested_qty: int
    filled_qty: int
    avg_fill_price: float
    fill_fraction: float
    n_prints: int
    window_qty: int


_EMPTY_COLS = ("timestamp", "price", "size")


def _no_fill(req: int) -> TapeFillResult:
    return TapeFillResult(
        filled=False, requested_qty=int(req), filled_qty=0, avg_fill_price=0.0,
        fill_fraction=0.0, n_prints=0, window_qty=0,
    )


def replay_tape_fill(
    trades: Optional[pd.DataFrame],
    *,
    qty: int,
    start_ts: Any,
    window_seconds: float,
    participation: float = 1.0,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> TapeFillResult:
    """Fill a marketable order of ``qty`` shares starting at ``start_ts``.

    Consumes eligible prints in ``[start_ts, start_ts + window_seconds]`` in time
    order, taking ``participation`` (0..1) of each print's size, until ``qty`` is
    filled or the window's eligible volume is exhausted. The fill price is the
    size-weighted VWAP of the consumed prints.

    ``min_price`` / ``max_price`` restrict eligible prints so the oracle honours
    the order's trigger: a sell-STOP only fills at/through the trigger
    (``max_price=stop``), a sell-TARGET only at/above it (``min_price=target``); an
    unconstrained marketable order passes neither. Returns a partial when the
    window can't supply ``qty`` and an honest no-fill when ``trades`` is
    absent/empty — the caller then falls back to its existing fill model.
    """
    req = int(qty)
    if req <= 0 or trades is None or len(trades) == 0:
        return _no_fill(req)
    if not all(c in trades.columns for c in _EMPTY_COLS):
        return _no_fill(req)

    t0 = pd.Timestamp(start_ts)
    t0 = t0.tz_localize("UTC") if t0.tzinfo is None else t0.tz_convert("UTC")
    t1 = t0 + pd.Timedelta(seconds=float(window_seconds))
    ts = pd.to_datetime(trades["timestamp"], utc=True)
    mask = (ts >= t0) & (ts <= t1)
    if min_price is not None:
        mask = mask & (trades["price"] >= float(min_price))
    if max_price is not None:
        mask = mask & (trades["price"] <= float(max_price))

    elig = trades.loc[mask, ["timestamp", "price", "size"]]
    if elig.empty:
        return _no_fill(req)
    elig = elig.sort_values("timestamp", kind="stable")

    part = max(0.0, min(1.0, float(participation)))
    if part <= 0.0:
        return _no_fill(req)

    prices = elig["price"].to_numpy(dtype="float64")
    sizes = elig["size"].to_numpy(dtype="float64")
    window_qty = int(round(float(sizes.sum()) * part))

    remaining = float(req)
    notional = 0.0
    filled = 0.0
    n = 0
    for price, size in zip(prices, sizes):
        avail = float(size) * part
        if avail <= 0.0:
            continue
        take = remaining if remaining < avail else avail
        notional += take * float(price)
        filled += take
        n += 1
        remaining -= take
        if remaining <= 0.0:
            break

    if filled <= 0.0:
        return _no_fill(req)
    filled_i = int(round(filled))
    return TapeFillResult(
        filled=filled_i >= req,
        requested_qty=req,
        filled_qty=filled_i,
        avg_fill_price=round(notional / filled, 6),
        fill_fraction=round(filled / req, 6),
        n_prints=n,
        window_qty=window_qty,
    )


__all__ = ["TapeFillResult", "replay_tape_fill"]
