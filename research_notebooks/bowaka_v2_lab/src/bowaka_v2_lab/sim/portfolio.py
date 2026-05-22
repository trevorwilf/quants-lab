"""Multi-session, multi-lot portfolio state.

Per [Report §9.6, §9.10] and realism remediation Phase 5:

- ``open_positions`` is keyed by ``position_id`` (a UUID string), NOT by
  symbol. A single symbol may therefore hold several concurrent lots — one
  per entry session, capped by ``risk.max_lots_per_symbol``. This mirrors the
  live strategy's ``link_id``-keyed ``open_positions``
  (``bowaka_v2_strategy.py:_migrate_open_positions``).
- ``begin_session(date)`` recomputes ``gross_exposure_dollars`` from ALL open
  lots (sum across ``position_id``) (§15.1 P0 fix — archive forgot to roll
  forward) and recomputes ``entered_symbols_today`` from lots whose
  ``entry_session == session_date``.
- ``end_session(date)`` rolls forward open positions; resets per-day counters.
- ``gross_exposure_pct`` is dollars / bankroll (§15.2 P1 fix — archive
  returned 0).
- Per-day counters tracked: entries_today, stopouts_today,
  consecutive_stopouts, daily_realized_pnl, daily_unrealized_pnl,
  gross_exposure_dollars, gross_exposure_pct, kill_switch_state.

Helpers ``lots_for_symbol`` / ``symbol_open_notional`` / ``positions_for_symbol``
expose the per-symbol aggregate so the risk gates can apply the ADV-tier cap to
the combined symbol notional (existing lots + the candidate), per live
``bowaka_v2_strategy.py:474-488``.
"""
from __future__ import annotations

import datetime as _dt
import uuid
from dataclasses import dataclass, field
from typing import Optional


def new_position_id() -> str:
    """A fresh unique ``position_id`` (UUID4 hex-with-dashes string)."""
    return str(uuid.uuid4())


@dataclass
class Position:
    symbol: str
    entry_date: _dt.date
    entry_price: float
    qty: int
    stop_pct: float
    target_pct: float
    max_hold_days: int
    candidate_event_id: Optional[str] = None
    current_price: Optional[float] = None
    unrealized_pnl: float = 0.0
    peak_price: Optional[float] = None  # for trailing-stop work in later phases
    # Realism Phase 5 — multi-lot identity. ``position_id`` is the dict key in
    # ``Portfolio.open_positions``; ``entry_session`` is the session the lot was
    # opened on (drives ``entered_symbols_today`` rollover); ``lot_index`` is the
    # 0-based ordinal of this lot among the symbol's concurrent lots.
    position_id: str = field(default_factory=new_position_id)
    parent_order_id: Optional[str] = None
    link_id: Optional[str] = None
    entry_session: Optional[_dt.date] = None
    lot_index: int = 0

    def __post_init__(self) -> None:
        # Default entry_session to entry_date so legacy callers that omit it
        # still get correct session-rollover behavior.
        if self.entry_session is None:
            self.entry_session = self.entry_date

    @property
    def gross_dollars(self) -> float:
        if self.current_price is not None:
            return self.qty * self.current_price
        return self.qty * self.entry_price


@dataclass
class PortfolioState:
    session_date: _dt.date
    bankroll: float
    entries_today: int = 0
    stopouts_today: int = 0
    consecutive_stopouts: int = 0
    daily_realized_pnl: float = 0.0
    daily_unrealized_pnl: float = 0.0
    gross_exposure_dollars: float = 0.0
    gross_exposure_pct: float = 0.0
    kill_switch_state: Optional[str] = None  # None | "daily_loss" | "strategy_loss"
    # Realism Phase 5 — symbols opened in THIS session (recomputed every
    # begin_session from lots whose entry_session == session_date). Drives the
    # ``same_symbol_entries_per_day`` gate.
    entered_symbols_today: set[str] = field(default_factory=set)


@dataclass
class Portfolio:
    initial_bankroll: float
    # Realism Phase 5: keyed by ``position_id`` (UUID), not symbol.
    open_positions: dict[str, Position] = field(default_factory=dict)
    closed_trades: list[dict] = field(default_factory=list)
    state: Optional[PortfolioState] = None

    @property
    def current_bankroll(self) -> float:
        return self.state.bankroll if self.state else self.initial_bankroll

    # ---- per-symbol helpers (Realism Phase 5) -----------------------------

    def positions_for_symbol(self, symbol: str) -> list[Position]:
        """All open lots currently held for ``symbol`` (insertion order)."""
        return [p for p in self.open_positions.values() if p.symbol == symbol]

    def lots_for_symbol(self, symbol: str) -> int:
        """Count of concurrent open lots held for ``symbol``."""
        return sum(1 for p in self.open_positions.values() if p.symbol == symbol)

    def symbol_open_notional(self, symbol: str) -> float:
        """Aggregate dollar exposure already held in ``symbol`` across all its
        open lots — used so the ADV cap binds the combined position, not a lot.

        Matches live ``bowaka_v2_strategy._symbol_open_notional``: notional is
        ``qty * entry_price`` per lot.
        """
        total = 0.0
        for p in self.open_positions.values():
            if p.symbol == symbol:
                total += p.qty * p.entry_price
        return total

    # ---- session lifecycle ------------------------------------------------

    def begin_session(self, session_date: _dt.date) -> None:
        # Per §15.1 P0: recompute gross_exposure_dollars from ALL open lots.
        gross = sum(p.gross_dollars for p in self.open_positions.values())
        bankroll = self.state.bankroll if self.state else self.initial_bankroll
        pct = gross / bankroll if bankroll > 0 else 0.0
        # Realism Phase 5: entered_symbols_today is recomputed from lots whose
        # entry_session is THIS session — a fresh session starts empty unless a
        # lot was somehow already opened today.
        entered = {
            p.symbol
            for p in self.open_positions.values()
            if p.entry_session == session_date
        }
        self.state = PortfolioState(
            session_date=session_date,
            bankroll=bankroll,
            entries_today=0,
            stopouts_today=0,
            consecutive_stopouts=self.state.consecutive_stopouts if self.state else 0,
            daily_realized_pnl=0.0,
            daily_unrealized_pnl=0.0,
            gross_exposure_dollars=gross,
            gross_exposure_pct=pct,
            kill_switch_state=None,
            entered_symbols_today=entered,
        )

    def end_session(self, session_date: _dt.date) -> None:
        # Roll forward open positions; per-day counters already reset by begin_session.
        if self.state is None:
            return
        # No-op; state is overwritten on next begin_session.

    def update_mtm(self, marks: dict[str, float]) -> None:
        """Mark open positions to market using ``marks[symbol] -> price``.

        All lots of the same symbol mark to the same per-symbol price.
        """
        unrealized = 0.0
        for pos in self.open_positions.values():
            mark = marks.get(pos.symbol)
            if mark is None:
                continue
            pos.current_price = float(mark)
            pos.unrealized_pnl = (mark - pos.entry_price) * pos.qty
            unrealized += pos.unrealized_pnl
        if self.state is not None:
            self.state.daily_unrealized_pnl = unrealized
            gross = sum(p.gross_dollars for p in self.open_positions.values())
            self.state.gross_exposure_dollars = gross
            self.state.gross_exposure_pct = gross / self.state.bankroll if self.state.bankroll > 0 else 0.0

    def add_position(self, pos: Position) -> None:
        """Register a new lot, keyed by its ``position_id``.

        ``lot_index`` is assigned as the 0-based ordinal of this lot among the
        symbol's already-open lots, so the first lot is 0, the next 1, etc.
        ``entry_session`` (if unset) defaults to the lot's ``entry_date``.
        """
        if pos.entry_session is None:
            pos.entry_session = pos.entry_date
        # Assign lot_index from the count of existing lots for this symbol.
        pos.lot_index = self.lots_for_symbol(pos.symbol)
        self.open_positions[pos.position_id] = pos
        if self.state is not None:
            self.state.entries_today += 1
            if pos.entry_session == self.state.session_date:
                self.state.entered_symbols_today.add(pos.symbol)
            gross = sum(p.gross_dollars for p in self.open_positions.values())
            self.state.gross_exposure_dollars = gross
            self.state.gross_exposure_pct = gross / self.state.bankroll if self.state.bankroll > 0 else 0.0

    # ---- closure ----------------------------------------------------------

    def _record_close(
        self, pos: Position, *, exit_price: float, exit_reason: str, exit_date: _dt.date
    ) -> dict:
        """Common closure bookkeeping for a single lot ``pos`` (already popped)."""
        pnl = (exit_price - pos.entry_price) * pos.qty
        trade = {
            "symbol": pos.symbol,
            "position_id": pos.position_id,
            "entry_date": pos.entry_date.isoformat(),
            "entry_price": pos.entry_price,
            "exit_date": exit_date.isoformat(),
            "exit_price": exit_price,
            "qty": pos.qty,
            "pnl": pnl,
            "exit_reason": exit_reason,
            "candidate_event_id": pos.candidate_event_id,
        }
        self.closed_trades.append(trade)
        if self.state is not None:
            self.state.bankroll += pnl
            self.state.daily_realized_pnl += pnl
            is_loss = pnl < 0
            if exit_reason in ("stop_loss", "trailing_stop"):
                self.state.stopouts_today += 1
                if is_loss:
                    self.state.consecutive_stopouts += 1
                else:
                    self.state.consecutive_stopouts = 0
            elif is_loss:
                self.state.consecutive_stopouts += 1
            else:
                self.state.consecutive_stopouts = 0
            gross = sum(p.gross_dollars for p in self.open_positions.values())
            self.state.gross_exposure_dollars = gross
            self.state.gross_exposure_pct = gross / self.state.bankroll if self.state.bankroll > 0 else 0.0
        return trade

    def close_position_by_id(
        self, position_id: str, *, exit_price: float, exit_reason: str, exit_date: _dt.date
    ) -> dict:
        """Close exactly one lot, identified by its ``position_id``.

        This is the canonical closer in the multi-lot model — closing one lot
        of a symbol leaves the symbol's other lots open.
        """
        pos = self.open_positions.pop(position_id)
        return self._record_close(
            pos, exit_price=exit_price, exit_reason=exit_reason, exit_date=exit_date
        )

    def close_position(
        self, symbol: str, *, exit_price: float, exit_reason: str, exit_date: _dt.date
    ) -> dict:
        """DEPRECATED — back-compat closer that closes the OLDEST open lot of
        ``symbol`` (lowest ``lot_index``, then insertion order).

        Prefer :meth:`close_position_by_id` in the multi-lot model. Retained so
        symbol-keyed callers (and pre-Phase-5 tests) keep working.
        """
        lots = self.positions_for_symbol(symbol)
        if not lots:
            raise KeyError(symbol)
        # Oldest lot first: lowest lot_index, ties broken by insertion order.
        oldest = min(lots, key=lambda p: p.lot_index)
        self.open_positions.pop(oldest.position_id)
        return self._record_close(
            oldest, exit_price=exit_price, exit_reason=exit_reason, exit_date=exit_date
        )
