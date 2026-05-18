"""Verbatim excerpt of source ``_confirm_entry`` for parity tests.

Lifted from ``reference/source_strategy/scripts/bowaka_strategy.py``
(lines 1943-1991). Importing the source module directly fails on missing
``alpaca`` deps, so the function under test is copied here. The signature
takes an ``Entry`` namedtuple stand-in (we only need ``close_price``) and a
quote dict.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Entry:
    close_price: float


def _confirm_entry(
    entry: Entry,
    cfg_ic: dict,
    quote: dict[str, Any],
    *,
    now_utc: datetime,
) -> tuple[bool, str | None]:
    """Source verbatim. Returns (passed, fail_reason)."""
    try:
        bid = float(quote.get("bid") or 0)
        ask = float(quote.get("ask") or 0)
    except (TypeError, ValueError):
        return False, "bad_bid_ask"
    if bid <= 0 or ask <= 0 or ask <= bid:
        return False, "no_quote"
    mid = (bid + ask) / 2.0

    max_spread = float(cfg_ic.get("max_spread_pct") or 0)
    if max_spread > 0 and (ask - bid) / mid > max_spread:
        return False, f"spread>{max_spread:.4f}"

    max_age_s = float(cfg_ic.get("max_quote_age_seconds") or 0)
    if max_age_s > 0:
        ts = quote.get("timestamp")
        if isinstance(ts, str):
            try:
                quote_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if quote_dt.tzinfo is None:
                    quote_dt = quote_dt.replace(tzinfo=timezone.utc)
                age_s = (now_utc - quote_dt).total_seconds()
                if age_s > max_age_s:
                    return False, f"quote_age>{max_age_s:.0f}s"
            except ValueError:
                return False, "bad_quote_timestamp"

    band = cfg_ic.get("price_band") or {}
    max_above = band.get("max_pct_above_close")
    min_below = band.get("min_pct_below_close")
    if max_above is not None and entry.close_price > 0:
        if mid > entry.close_price * (1.0 + float(max_above)):
            return False, f"chase>{max_above}"
    if min_below is not None and entry.close_price > 0:
        if mid < entry.close_price * (1.0 + float(min_below)):
            return False, f"failure<{min_below}"

    return True, None
