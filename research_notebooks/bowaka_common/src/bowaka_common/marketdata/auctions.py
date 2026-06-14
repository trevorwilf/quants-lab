"""Official open/close auction extraction (§5.1).

Pure parsing of the Alpaca ``GET /v2/stocks/auctions`` response into one row per
session carrying the OFFICIAL opening + closing auction price. The continuous
daily-bar O/C is the first/last *continuous* trade, which differs from the
official auction print — the EOD mark, gap logic and any MOO/MOC logic should use
the official print. Network I/O lives in ``scripts/backfill_auctions.py``; this
module is pure and unit-testable (no live API).

Per-day response shape: ``{"d": "YYYY-MM-DD", "o": [opening prints], "c":
[closing prints]}`` where each print is ``{"c": condition, "p": price, "s":
size, "t": ts, "x": exchange}``. The official OPEN is the CTS opening print
``"O"`` (else the Nasdaq official-open / reopening ``"Q"``); the official CLOSE is
the CTS official close ``"M"`` (else the UTP closing print ``"6"``).
"""
from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

#: Sale-condition priority for the OFFICIAL opening auction print.
_OPEN_PRIORITY = ("O", "Q")
#: Sale-condition priority for the OFFICIAL closing auction print.
_CLOSE_PRIORITY = ("M", "6")


def _pick_auction_print(
    prints: Sequence[Mapping[str, Any]], priority: Sequence[str]
) -> Optional[Mapping[str, Any]]:
    """The official auction print: the largest-size print whose condition is the
    highest-priority match; falls back to the largest-size print overall (the
    best proxy when the venue tags conditions differently)."""
    if not prints:
        return None
    for cond in priority:
        matches = [p for p in prints if str(p.get("c", "")).strip() == cond]
        if matches:
            return max(matches, key=lambda p: float(p.get("s") or 0.0))
    return max(prints, key=lambda p: float(p.get("s") or 0.0))


def extract_official_auction(day: Mapping[str, Any], *, symbol: str) -> Optional[dict]:
    """One day's auctions -> a row with the official open/close, or ``None`` when
    neither side has a usable print."""
    session_date = day.get("d")
    open_p = _pick_auction_print(day.get("o") or [], _OPEN_PRIORITY)
    close_p = _pick_auction_print(day.get("c") or [], _CLOSE_PRIORITY)
    if not session_date or (open_p is None and close_p is None):
        return None
    # ``timestamp`` anchors range queries (the close auction ~16:00 ET; fall back
    # to the open auction, then the session date).
    ts = (close_p or open_p or {}).get("t") or f"{session_date}T20:00:00Z"
    return {
        "symbol": str(symbol),
        "session_date": str(session_date),
        "timestamp": ts,
        "official_open": float(open_p["p"]) if open_p and open_p.get("p") is not None else None,
        "official_close": float(close_p["p"]) if close_p and close_p.get("p") is not None else None,
        "open_size": float(open_p.get("s") or 0.0) if open_p else None,
        "close_size": float(close_p.get("s") or 0.0) if close_p else None,
        "open_condition": str(open_p.get("c", "")) if open_p else None,
        "close_condition": str(close_p.get("c", "")) if close_p else None,
    }


def parse_auctions_response(data: Mapping[str, Any], symbol: str) -> list[dict]:
    """Parse ``{"auctions": {SYM: [day, ...]}}`` -> a list of official-auction rows."""
    days = (data.get("auctions") or {}).get(symbol) or []
    rows: list[dict] = []
    for day in days:
        row = extract_official_auction(day, symbol=symbol)
        if row is not None:
            rows.append(row)
    return rows


__all__ = ["extract_official_auction", "parse_auctions_response"]
