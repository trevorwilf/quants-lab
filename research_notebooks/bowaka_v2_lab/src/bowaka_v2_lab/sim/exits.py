"""Exit evaluator: stop-loss / take-profit / time-stop / signal-fade.

Per [Report §9.6, §9.7]:
- Same-bar stop+target ambiguity resolves via ``ambiguity.resolve_same_bar``
  (default ``stop_first``); resolution is logged in the trade record.
- ``_trading_days_since`` uses ``exchange-calendars`` XNYS sessions, NOT
  ``pd.bdate_range`` (§15.2 P1 fix — bdate_range ignores US market holidays).
- ``signal_fade_mode`` is ``telemetry_only`` by default; can be ``active`` per config.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Optional

import pandas as pd

try:
    import exchange_calendars as xcals
except ImportError:  # pragma: no cover
    xcals = None  # type: ignore

from .ambiguity import resolve_same_bar
from .portfolio import Position


@dataclass
class ExitEvent:
    symbol: str
    exit_date: _dt.date
    exit_price: float
    exit_reason: str
    ambiguous_bar_resolved: bool = False
    # Realism Phase 5 — the specific lot this exit closes. open_positions is
    # keyed by position_id, so a symbol may hold several lots; callers close
    # the exact lot via Portfolio.close_position_by_id(position_id, ...).
    position_id: Optional[str] = None


def trading_days_since(start: _dt.date, end: _dt.date, *, calendar: str = "XNYS") -> int:
    """Trading-day count using exchange-calendars XNYS sessions.

    Per [Report §15.2 P1]: replaces ``pd.bdate_range`` which ignored US market
    holidays (Christmas, July 4, MLK Day, etc.) and miscounted ``max_hold_days``.
    """
    if end <= start:
        return 0
    if xcals is None:
        # Conservative fallback: use bdate_range with a warning.
        return len(pd.bdate_range(start=start, end=end)) - (1 if start.weekday() < 5 else 0)
    cal = xcals.get_calendar(calendar)
    sessions = cal.sessions_in_range(pd.Timestamp(start), pd.Timestamp(end))
    return max(0, len(sessions) - 1)  # exclude the entry day itself


def evaluate_exits(
    pos: Position,
    *,
    bar: dict,
    bar_date: _dt.date,
    exit_cfg: dict,
    same_bar_policy: str = "stop_first",
) -> Optional[ExitEvent]:
    """Evaluate a single bar for stop / target / time-stop hits."""
    high = float(bar.get("high", bar.get("session_high", 0.0)) or 0.0)
    low = float(bar.get("low", bar.get("session_low", 0.0)) or 0.0)
    close = float(bar.get("close", bar.get("last_price", 0.0)) or 0.0)
    if high == 0 or low == 0:
        return None

    stop_price = pos.entry_price * (1.0 - pos.stop_pct)
    target_price = pos.entry_price * (1.0 + pos.target_pct)

    stop_hit = low <= stop_price
    target_hit = high >= target_price
    ambiguous = stop_hit and target_hit
    pid = pos.position_id
    if ambiguous:
        winner = resolve_same_bar(same_bar_policy)
        if winner == "stop":
            return ExitEvent(pos.symbol, bar_date, stop_price, "stop_loss",
                             ambiguous_bar_resolved=True, position_id=pid)
        else:
            return ExitEvent(pos.symbol, bar_date, target_price, "take_profit",
                             ambiguous_bar_resolved=True, position_id=pid)
    if stop_hit:
        return ExitEvent(pos.symbol, bar_date, stop_price, "stop_loss", position_id=pid)
    if target_hit:
        return ExitEvent(pos.symbol, bar_date, target_price, "take_profit", position_id=pid)

    # Time stop.
    days_held = trading_days_since(pos.entry_date, bar_date)
    if days_held >= pos.max_hold_days:
        return ExitEvent(pos.symbol, bar_date, close, "time_stop", position_id=pid)

    return None
