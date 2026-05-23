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
from enum import Enum
from typing import Optional


def new_position_id() -> str:
    """A fresh unique ``position_id`` (UUID4 hex-with-dashes string)."""
    return str(uuid.uuid4())


class ProtectionState(str, Enum):
    """Per-lot OCO / protected-position lifecycle states (realism rem-2 Phase 6).

    The live strategy submits a parent order, polls for the parent fill, attaches
    OCO children only AFTER the actual fill, and enforces a protected-position
    invariant (``protected_position`` block in ``bowaka_v2_config.yaml`` lines
    248-254). The lab pre-Phase-6 created a ``Position`` with
    ``bracket_attached=True`` the moment the simulated fill lands — that path is
    materially simpler than live and masks the most important live failure
    mode: the unprotected interval between parent fill and bracket attach.

    Phase 6 wires the explicit state machine below. Transitions are driven by
    :class:`sim.event_loop.EventType` events (PARENT_FILL,
    OCO_ATTACH_ATTEMPT, PROTECTION_CHECK, CHILD_FILL) and the protection state
    machine in :mod:`sim.protection`. Audit §P0-007 names the lifecycle.

    Terminal states are :attr:`CHILD_EXIT_FILLED` and :attr:`MANUAL_EXIT_FILLED`
    (and :attr:`PARENT_REJECTED` / :attr:`PARENT_CANCELED` for pre-fill aborts).
    :attr:`PROTECTED` is the steady "OCO attached, lot is safe" state. The
    legacy ``Position.bracket_attached`` field is a derived view of state ==
    PROTECTED so existing consumers (parity tests, the bracket-pricing test)
    keep working unchanged.
    """

    # Pre-fill stages — the parent order is live but no shares have hit yet.
    PENDING_FILL = "pending_fill"
    PARENT_ACKNOWLEDGED = "parent_acknowledged"
    PARENT_PARTIALLY_FILLED = "parent_partially_filled"
    # Post-parent-fill stages.
    PARENT_FILLED = "parent_filled"
    PARENT_CANCELED = "parent_canceled"
    PARENT_REJECTED = "parent_rejected"
    # OCO attach loop.
    OCO_ATTACH_PENDING = "oco_attach_pending"
    OCO_ATTACHED = "oco_attached"
    OCO_ATTACH_FAILED = "oco_attach_failed"
    # Steady states.
    PROTECTED = "protected"
    UNPROTECTED_VIOLATION = "unprotected_violation"
    # Remediations applied on a violation.
    FALLBACK_STOP_SUBMITTED = "fallback_stop_submitted"
    FLATTEN_SUBMITTED = "flatten_submitted"
    ENTRIES_BLOCKED = "entries_blocked"
    # Terminal exits.
    CHILD_EXIT_FILLED = "child_exit_filled"
    MANUAL_EXIT_FILLED = "manual_exit_filled"


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
    # Realism Phase 7 — the tz-aware UTC timestamp of the FILL minute. The
    # per-lot minute-path exit lifecycle (``sim.exits.walk_lot_exit``) walks the
    # minute bars from the bar AFTER this minute, so a lot can never exit on the
    # bar it filled on. Legacy callers that omit it fall back to entry_date's
    # session open (see ``Position.entry_minute_utc``).
    entry_timestamp: Optional[str] = None
    # Realism Phase 6 — fill + bracket-attachment metadata. ``entry_price`` is
    # the *actual fill price*; ``stop_price`` / ``target_price`` are computed
    # from it (live ``bracket_pricing_mode: actual_fill``) once the fill lands,
    # so the brackets attach AFTER the fill, never off the raw signal price.
    fill_source: Optional[str] = None          # quote source the fill used
    fill_slippage_bps: float = 0.0
    fill_is_partial: bool = False
    fill_commission: float = 0.0
    fill_regulatory_fees: float = 0.0
    fill_liquidity_participation: float = 0.0
    stop_price: Optional[float] = None
    target_price: Optional[float] = None
    bracket_pricing_mode: str = "actual_fill"
    # Realism remediation 2 Phase 6 — OCO / protected-position lifecycle.
    # ``protection_state`` is the source of truth; ``bracket_attached`` is a
    # legacy dataclass field synchronized with it in __post_init__ so the live
    # state transitions and the legacy boolean stay in lock-step. Legacy
    # callers that pass ``bracket_attached=True`` (e.g. test_bracket_pricing_
    # actual_fill) pin the lot into PROTECTED via the post-init.
    bracket_attached: bool = False
    protection_state: ProtectionState = ProtectionState.PENDING_FILL
    parent_fill_ts: Optional[str] = None  # tz-aware ISO ts of the parent fill
    protected_ts: Optional[str] = None    # tz-aware ISO ts of OCO attach success
    # Number of OCO attach attempts already made for this lot.
    oco_attach_attempt_count: int = 0
    # The fallback stop submitted on attach failure (if any), as an ISO ts.
    fallback_stop_ts: Optional[str] = None
    # Flatten timestamp when ``flatten_if_unprotected`` triggers, ISO ts.
    flatten_ts: Optional[str] = None
    # Total seconds the lot spent in any unprotected state (pre-protection
    # interval + any re-entered unprotected_violation window). Mirrors the live
    # protected-position invariant audit.
    total_unprotected_seconds: float = 0.0

    def __post_init__(self) -> None:
        # Default entry_session to entry_date so legacy callers that omit it
        # still get correct session-rollover behavior.
        if self.entry_session is None:
            self.entry_session = self.entry_date
        # Realism remediation 2 Phase 6 — reconcile ``bracket_attached`` and
        # ``protection_state``. Legacy callers (parity tests, the bracket-
        # pricing test) construct ``Position(bracket_attached=True)`` and
        # expect the lot to be in the steady PROTECTED state. New callers set
        # ``protection_state`` directly; the dataclass boolean follows.
        if self.bracket_attached and self.protection_state == ProtectionState.PENDING_FILL:
            self.protection_state = ProtectionState.PROTECTED
        # ``bracket_attached`` is True iff the lot is in PROTECTED.
        self.bracket_attached = (self.protection_state == ProtectionState.PROTECTED)

    def set_protection_state(self, state: "ProtectionState") -> None:
        """Authoritative setter — keeps ``bracket_attached`` in sync.

        All state-machine transitions go through this so the legacy boolean
        stays accurate (True iff state == PROTECTED). Direct assignment to
        ``self.protection_state`` is fine for construction-time pinning; for
        runtime transitions use this method so the boolean follows.
        """
        self.protection_state = state
        self.bracket_attached = (state == ProtectionState.PROTECTED)

    @property
    def gross_dollars(self) -> float:
        if self.current_price is not None:
            return self.qty * self.current_price
        return self.qty * self.entry_price

    def entry_minute_utc(self):
        """The tz-aware UTC fill minute the Phase-7 exit walk starts after.

        Uses :attr:`entry_timestamp` when set; otherwise falls back to the
        09:30 ET regular open of :attr:`entry_date` (legacy callers / smoke
        fixtures that never carried a sub-day fill time).
        """
        import pandas as _pd

        if self.entry_timestamp:
            ts = _pd.Timestamp(self.entry_timestamp)
            return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
        open_et = _pd.Timestamp(
            _dt.datetime.combine(self.entry_date, _dt.time(9, 30)),
            tz="America/New_York",
        )
        return open_et.tz_convert("UTC")


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
    # Realism remediation 2 Phase 6 — set ``True`` by the protection state
    # machine when one or more lots are in :attr:`ProtectionState.UNPROTECTED_VIOLATION`
    # / :attr:`ProtectionState.ENTRIES_BLOCKED` AND
    # ``protected_position.block_entries_on_violation`` is True. New SCANs whose
    # risk gates would otherwise accept the candidate are rejected with reason
    # ``entries_blocked_by_protection``.
    entries_blocked: bool = False


@dataclass
class ProtectionMetrics:
    """Cross-session counters surfaced in the run report (Phase 6 task 4).

    Per the audit (P0-007) the run report must expose:

    * ``max_unprotected_seconds_observed`` — the worst-case observed gap between
      a PARENT_FILL and the lot reaching :attr:`ProtectionState.PROTECTED`.
    * ``oco_attach_attempts_count`` — total attach attempts across all lots.
    * ``oco_attach_failure_count`` — total attach attempts that failed.
    * ``fallback_stop_count`` — lots for which a fallback stop was submitted.
    * ``flatten_unprotected_count`` — lots flattened on unprotected violation.
    * ``entries_blocked_by_protection_count`` — SCANs rejected by
      :attr:`PortfolioState.entries_blocked`.
    * ``total_unprotected_seconds_across_lots`` — Σ over lots of the unprotected
      seconds, useful for the optuna objective penalty hook (task 5).
    * ``unprotected_violation_count`` — lots that entered
      :attr:`ProtectionState.UNPROTECTED_VIOLATION` (drives the Phase-8 penalty).
    """

    max_unprotected_seconds_observed: float = 0.0
    oco_attach_attempts_count: int = 0
    oco_attach_failure_count: int = 0
    fallback_stop_count: int = 0
    flatten_unprotected_count: int = 0
    entries_blocked_by_protection_count: int = 0
    total_unprotected_seconds_across_lots: float = 0.0
    unprotected_violation_count: int = 0


@dataclass
class Portfolio:
    initial_bankroll: float
    # Realism Phase 5: keyed by ``position_id`` (UUID), not symbol.
    open_positions: dict[str, Position] = field(default_factory=dict)
    closed_trades: list[dict] = field(default_factory=list)
    state: Optional[PortfolioState] = None
    # Realism remediation 2 Phase 6 — per-run protection counters. Rolled into
    # the run summary by the backtester for the report and (Phase 8) the optuna
    # objective penalty.
    protection_metrics: ProtectionMetrics = field(default_factory=ProtectionMetrics)

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
        # Realism remediation 2 Phase 6 — recompute entries_blocked from the
        # surviving lots. If any open lot is still in a violation / blocking
        # state, the new session inherits the block; otherwise the new session
        # starts unblocked.
        violation_states = {
            ProtectionState.UNPROTECTED_VIOLATION,
            ProtectionState.ENTRIES_BLOCKED,
            ProtectionState.FALLBACK_STOP_SUBMITTED,
            ProtectionState.FLATTEN_SUBMITTED,
        }
        carryover_block = any(
            p.protection_state in violation_states
            for p in self.open_positions.values()
        )
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
            entries_blocked=carryover_block,
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
        self,
        pos: Position,
        *,
        exit_price: float,
        exit_reason: str,
        exit_date: _dt.date,
        exit_event: Optional["object"] = None,
    ) -> dict:
        """Common closure bookkeeping for a single lot ``pos`` (already popped).

        ``exit_event`` (a Phase-7 :class:`sim.exits.ExitEvent`) enriches the
        trade record with the minute-path forensics — exit timestamp, MFE/MAE,
        exit slippage and the halt flag — that the exit-analysis report reads.
        """
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
            # Phase 7 minute-path forensics (defaults when closed off a daily
            # bar / a non-minute-path closer).
            "exit_timestamp": getattr(exit_event, "exit_timestamp", None),
            "ambiguous_bar_resolved": bool(
                getattr(exit_event, "ambiguous_bar_resolved", False)
            ),
            "mfe_pct": float(getattr(exit_event, "mfe_pct", 0.0) or 0.0),
            "mae_pct": float(getattr(exit_event, "mae_pct", 0.0) or 0.0),
            "exit_slippage_bps": float(
                getattr(exit_event, "exit_slippage_bps", 0.0) or 0.0
            ),
            "halted": bool(getattr(exit_event, "halted", False)),
        }
        self.closed_trades.append(trade)
        if self.state is not None:
            self.state.bankroll += pnl
            self.state.daily_realized_pnl += pnl
            is_loss = pnl < 0
            # Phase 7 minute-path reasons (``stop`` / ``gap_stop``) count as
            # stop-outs alongside the legacy daily-bar reason names.
            if exit_reason in (
                "stop_loss", "trailing_stop", "stop", "gap_stop",
            ):
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
        # Realism remediation 2 Phase 6 — roll the closed lot's per-lot
        # unprotected seconds onto the run-wide protection metrics, then
        # transition the in-memory copy to a terminal state and (if no other
        # lot is still in violation) release ``entries_blocked``.
        self.protection_metrics.total_unprotected_seconds_across_lots += float(
            getattr(pos, "total_unprotected_seconds", 0.0) or 0.0
        )
        # Reflect terminal state on the popped lot for any later inspection.
        if pos.protection_state not in (
            ProtectionState.CHILD_EXIT_FILLED,
            ProtectionState.MANUAL_EXIT_FILLED,
        ):
            pos.protection_state = (
                ProtectionState.MANUAL_EXIT_FILLED
                if exit_reason in ("manual_flatten", "fallback_stop")
                else ProtectionState.CHILD_EXIT_FILLED
            )
        self._refresh_entries_blocked()
        return trade

    def _refresh_entries_blocked(self) -> None:
        """Clear ``state.entries_blocked`` when no remaining lot is in violation.

        Called after every lot close so a flatten / fallback-stop unwind
        releases the block in the same event loop the lot closes on. If any
        surviving lot is still in violation the block stays.
        """
        if self.state is None:
            return
        violation_states = {
            ProtectionState.UNPROTECTED_VIOLATION,
            ProtectionState.ENTRIES_BLOCKED,
            ProtectionState.FALLBACK_STOP_SUBMITTED,
            ProtectionState.FLATTEN_SUBMITTED,
        }
        any_open_violation = any(
            p.protection_state in violation_states
            for p in self.open_positions.values()
        )
        if not any_open_violation:
            self.state.entries_blocked = False

    def close_position_by_id(
        self,
        position_id: str,
        *,
        exit_price: float,
        exit_reason: str,
        exit_date: _dt.date,
        exit_event: Optional["object"] = None,
    ) -> dict:
        """Close exactly one lot, identified by its ``position_id``.

        This is the canonical closer in the multi-lot model — closing one lot
        of a symbol leaves the symbol's other lots open. ``exit_event`` (a
        Phase-7 :class:`sim.exits.ExitEvent`) carries the minute-path forensics
        onto the trade record.
        """
        pos = self.open_positions.pop(position_id)
        return self._record_close(
            pos, exit_price=exit_price, exit_reason=exit_reason,
            exit_date=exit_date, exit_event=exit_event,
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
