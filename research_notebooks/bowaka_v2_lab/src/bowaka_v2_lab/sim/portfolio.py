"""Multi-session portfolio state.

Per [Report §9.6, §9.10]:
- ``begin_session(date)`` recomputes ``gross_exposure_dollars`` FROM
  ``open_positions`` (§15.1 P0 fix — archive forgot to roll forward).
- ``end_session(date)`` rolls forward open positions; resets per-day counters.
- ``gross_exposure_pct`` is dollars / bankroll (§15.2 P1 fix — archive
  returned 0).
- Per-day counters tracked: entries_today, stopouts_today,
  consecutive_stopouts, daily_realized_pnl, daily_unrealized_pnl,
  gross_exposure_dollars, gross_exposure_pct, kill_switch_state.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Optional


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


@dataclass
class Portfolio:
    initial_bankroll: float
    open_positions: dict[str, Position] = field(default_factory=dict)
    closed_trades: list[dict] = field(default_factory=list)
    state: Optional[PortfolioState] = None

    @property
    def current_bankroll(self) -> float:
        return self.state.bankroll if self.state else self.initial_bankroll

    def begin_session(self, session_date: _dt.date) -> None:
        # Per §15.1 P0: recompute gross_exposure_dollars from open_positions.
        gross = sum(p.gross_dollars for p in self.open_positions.values())
        bankroll = self.state.bankroll if self.state else self.initial_bankroll
        pct = gross / bankroll if bankroll > 0 else 0.0
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
        )

    def end_session(self, session_date: _dt.date) -> None:
        # Roll forward open positions; per-day counters already reset by begin_session.
        if self.state is None:
            return
        # No-op; state is overwritten on next begin_session.

    def update_mtm(self, marks: dict[str, float]) -> None:
        """Mark open positions to market using ``marks[symbol] -> price``."""
        unrealized = 0.0
        for sym, pos in self.open_positions.items():
            mark = marks.get(sym)
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
        self.open_positions[pos.symbol] = pos
        if self.state is not None:
            self.state.entries_today += 1
            gross = sum(p.gross_dollars for p in self.open_positions.values())
            self.state.gross_exposure_dollars = gross
            self.state.gross_exposure_pct = gross / self.state.bankroll if self.state.bankroll > 0 else 0.0

    def close_position(self, symbol: str, *, exit_price: float, exit_reason: str, exit_date: _dt.date) -> dict:
        pos = self.open_positions.pop(symbol)
        pnl = (exit_price - pos.entry_price) * pos.qty
        trade = {
            "symbol": symbol,
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
