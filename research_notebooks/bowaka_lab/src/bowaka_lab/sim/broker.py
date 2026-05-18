"""SimulatedBroker — Phase fidelity-4 broker realism.

The broker is a per-symbol minute-stepped FSM that owns parent orders, OCO
brackets, and the escalation ladder (attach → retry → fallback → flatten).
``BowakaPortfolioBacktester`` drives it by:

  parent = broker.submit_parent(...)
  for each minute bar of the session:
      events = broker.step(now_ts=bar.ts, bar=bar, quote=latest_quote)
      # engine handles events: opens position on FILLED, closes on stop/target etc.

Probabilities (partial fill / rejection / OCO attach failure) are all 0 by
default — deterministic behavior. Operators calibrate them from paper logs.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

import numpy as np
import pandas as pd

from bowaka_lab.config.models import BrokerSimConfig
from bowaka_lab.sim.orders import (
    FillEvent,
    OcoBracket,
    OrderStatus,
    ParentOrder,
    ProtectionState,
)


# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------


@dataclass
class BrokerEvent:
    event_id: int
    ts: pd.Timestamp
    event_type: str
    parent_order_id: str | None = None
    bracket_id: str | None = None
    symbol: str | None = None
    qty: int | None = None
    price: float | None = None
    reason: str | None = None
    attach_attempt: int | None = None
    protection_state: str | None = None

    def to_row(self) -> dict:
        return {
            "event_id": self.event_id,
            "ts": self.ts,
            "event_type": self.event_type,
            "parent_order_id": self.parent_order_id,
            "bracket_id": self.bracket_id,
            "symbol": self.symbol,
            "qty": self.qty,
            "price": self.price,
            "reason": self.reason,
            "attach_attempt": self.attach_attempt,
            "protection_state": self.protection_state,
        }


# Event-type constants for downstream tooling.
EVT_PARENT_SUBMITTED = "parent_submitted"
EVT_PARENT_FILLED = "parent_filled"
EVT_PARENT_PARTIALLY_FILLED = "parent_partially_filled"
EVT_PARENT_REJECTED = "parent_rejected"
EVT_MARKETABLE_LIMIT_TIMED_OUT = "marketable_limit_timed_out"
EVT_OCO_ATTACH_PENDING = "oco_attach_pending"
EVT_OCO_ATTACHED = "oco_attached"
EVT_OCO_ATTACH_FAILED = "oco_attach_failed"
EVT_FALLBACK_STOP_SUBMITTED = "fallback_stop_submitted"
EVT_FLATTEN = "flatten"
EVT_STOP_HIT = "stop_hit"
EVT_TARGET_HIT = "target_hit"


@dataclass
class _PendingParent:
    parent: ParentOrder
    target_fill_ts: pd.Timestamp
    bar_at_submit: dict | None = None


@dataclass
class _PendingBracket:
    bracket: OcoBracket
    parent: ParentOrder
    target_attach_ts: pd.Timestamp


class SimulatedBroker:
    def __init__(self, cfg: BrokerSimConfig, rng: np.random.Generator | None = None):
        self.cfg = cfg
        self.rng = rng if rng is not None else np.random.default_rng(cfg.random_seed)
        self._order_id_seq = itertools.count(1)
        self._event_id_seq = itertools.count(1)
        self._pending_parents: dict[str, _PendingParent] = {}
        self._active_brackets: dict[str, OcoBracket] = {}
        self._attach_pending: dict[str, _PendingBracket] = {}
        self.events: list[BrokerEvent] = []
        # Brackets that need step()ed beyond the parent's session (GTC carry).
        self._gtc_carry_brackets: dict[str, OcoBracket] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit_parent(
        self,
        *,
        symbol: str,
        side: Literal["buy", "sell"],
        qty: int,
        style: Literal["market", "marketable_limit"],
        limit_price: float | None,
        ts: pd.Timestamp,
        timeout_seconds: int | None = None,
    ) -> ParentOrder:
        order_id = f"parent-{next(self._order_id_seq)}"
        parent = ParentOrder(
            order_id=order_id,
            symbol=symbol,
            side=side,
            style=style,
            submitted_ts=ts,
            timeout_seconds=int(timeout_seconds if timeout_seconds is not None else self.cfg.marketable_limit_timeout_seconds),
            qty_requested=int(qty),
            limit_price=limit_price,
            status=OrderStatus.PENDING,
        )
        target = ts + pd.Timedelta(seconds=self.cfg.parent_fill_latency_seconds)
        self._pending_parents[order_id] = _PendingParent(parent=parent, target_fill_ts=target)
        self._emit(BrokerEvent(
            event_id=next(self._event_id_seq), ts=ts, event_type=EVT_PARENT_SUBMITTED,
            parent_order_id=order_id, symbol=symbol, qty=int(qty),
            reason=f"style={style}",
        ))
        return parent

    def attach_oco(
        self,
        *,
        parent: ParentOrder,
        stop_price: float,
        target_price: float,
        ts: pd.Timestamp,
        tif: Literal["GTC", "DAY"] | None = None,
    ) -> OcoBracket:
        bracket_id = f"bracket-{next(self._order_id_seq)}"
        bracket = OcoBracket(
            order_id=bracket_id,
            parent_order_id=parent.order_id,
            stop_price=float(stop_price),
            target_price=float(target_price),
            time_in_force=tif or self.cfg.oco_time_in_force,
            state=ProtectionState.ATTACH_PENDING,
            attach_attempts=1,
            parent_fill_ts=ts,
        )
        target_attach = ts + pd.Timedelta(seconds=self.cfg.oco_attach_latency_seconds)
        self._attach_pending[bracket_id] = _PendingBracket(
            bracket=bracket, parent=parent, target_attach_ts=target_attach,
        )
        self._emit(BrokerEvent(
            event_id=next(self._event_id_seq), ts=ts,
            event_type=EVT_OCO_ATTACH_PENDING,
            parent_order_id=parent.order_id, bracket_id=bracket_id,
            symbol=parent.symbol,
            attach_attempt=1,
            protection_state=bracket.state.value,
        ))
        return bracket

    def submit_fallback_stop(
        self, *, parent: ParentOrder, stop_price: float, ts: pd.Timestamp,
    ) -> ParentOrder:
        """Stand-alone fallback STOP order. Persisted as the bracket's
        ``fallback_stop_price`` and as a separate parent-style record so the
        event log shows both legs.
        """
        order_id = f"fallback-{next(self._order_id_seq)}"
        fallback = ParentOrder(
            order_id=order_id,
            symbol=parent.symbol,
            side="sell" if parent.side == "buy" else "buy",
            style="market",
            submitted_ts=ts,
            timeout_seconds=0,
            qty_requested=parent.filled_qty,
            status=OrderStatus.PENDING,
        )
        self._emit(BrokerEvent(
            event_id=next(self._event_id_seq), ts=ts,
            event_type=EVT_FALLBACK_STOP_SUBMITTED,
            parent_order_id=order_id, symbol=parent.symbol,
            qty=parent.filled_qty, price=float(stop_price),
        ))
        return fallback

    def flatten(self, *, parent: ParentOrder, ts: pd.Timestamp, fill_price: float | None = None) -> ParentOrder:
        order_id = f"flatten-{next(self._order_id_seq)}"
        sell = ParentOrder(
            order_id=order_id,
            symbol=parent.symbol,
            side="sell" if parent.side == "buy" else "buy",
            style="market",
            submitted_ts=ts,
            timeout_seconds=0,
            qty_requested=parent.filled_qty,
            status=OrderStatus.FILLED,
            filled_qty=parent.filled_qty,
            avg_fill_price=float(fill_price or parent.avg_fill_price),
        )
        self._emit(BrokerEvent(
            event_id=next(self._event_id_seq), ts=ts,
            event_type=EVT_FLATTEN, parent_order_id=order_id, symbol=parent.symbol,
            qty=parent.filled_qty, price=float(fill_price or parent.avg_fill_price),
        ))
        return sell

    def step(
        self, *, now_ts: pd.Timestamp, bar: dict | None, quote: dict | None,
    ) -> list[BrokerEvent]:
        """Advance the broker by one minute. Returns newly-emitted events."""
        start_idx = len(self.events)
        self._step_parents(now_ts=now_ts, bar=bar, quote=quote)
        self._step_attach_pending(now_ts=now_ts)
        self._step_active_brackets(now_ts=now_ts, bar=bar)
        return self.events[start_idx:]

    def events_df(self) -> pd.DataFrame:
        if not self.events:
            return pd.DataFrame(columns=[
                "event_id", "ts", "event_type", "parent_order_id", "bracket_id",
                "symbol", "qty", "price", "reason", "attach_attempt", "protection_state",
            ])
        return pd.DataFrame([e.to_row() for e in self.events])

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _emit(self, evt: BrokerEvent) -> None:
        self.events.append(evt)

    def _step_parents(
        self, *, now_ts: pd.Timestamp, bar: dict | None, quote: dict | None,
    ) -> None:
        to_remove: list[str] = []
        for oid, pend in list(self._pending_parents.items()):
            p = pend.parent
            if p.status not in (OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED):
                to_remove.append(oid)
                continue
            # Reject probability — sample on first arrival.
            if (
                p.filled_qty == 0
                and self.cfg.broker_rejection_probability > 0
                and self.rng.random() < self.cfg.broker_rejection_probability
            ):
                p.status = OrderStatus.REJECTED
                p.reject_reason = "broker_rejected_random"
                self._emit(BrokerEvent(
                    event_id=next(self._event_id_seq), ts=now_ts,
                    event_type=EVT_PARENT_REJECTED, parent_order_id=oid,
                    symbol=p.symbol, qty=p.qty_requested,
                    reason=p.reject_reason,
                ))
                to_remove.append(oid)
                continue
            # Timeout on marketable_limit.
            if p.style == "marketable_limit" and p.timeout_seconds > 0:
                elapsed = (now_ts - p.submitted_ts).total_seconds()
                if elapsed > p.timeout_seconds and p.filled_qty == 0:
                    p.status = OrderStatus.EXPIRED
                    self._emit(BrokerEvent(
                        event_id=next(self._event_id_seq), ts=now_ts,
                        event_type=EVT_MARKETABLE_LIMIT_TIMED_OUT,
                        parent_order_id=oid, symbol=p.symbol,
                        reason=f"timeout_seconds={p.timeout_seconds}",
                    ))
                    to_remove.append(oid)
                    continue
            # Latency: fill only after target_fill_ts.
            if now_ts < pend.target_fill_ts:
                continue
            # Fill price: prefer the ask side of the latest quote, fall back to bar open.
            fill_price = _resolve_buy_fill_price(quote, bar, p.limit_price)
            if fill_price is None:
                continue
            remaining = p.qty_requested - p.filled_qty
            if remaining <= 0:
                to_remove.append(oid)
                continue
            qty_this = remaining
            if (
                self.cfg.partial_fill_probability > 0
                and p.filled_qty == 0
                and self.rng.random() < self.cfg.partial_fill_probability
            ):
                frac = self.rng.uniform(self.cfg.partial_fill_min_fraction, 1.0)
                qty_this = max(1, int(remaining * frac))
            p.add_fill(ts=now_ts, qty=qty_this, price=float(fill_price))
            if p.status == OrderStatus.PARTIALLY_FILLED:
                self._emit(BrokerEvent(
                    event_id=next(self._event_id_seq), ts=now_ts,
                    event_type=EVT_PARENT_PARTIALLY_FILLED,
                    parent_order_id=oid, symbol=p.symbol,
                    qty=qty_this, price=float(fill_price),
                ))
            else:
                self._emit(BrokerEvent(
                    event_id=next(self._event_id_seq), ts=now_ts,
                    event_type=EVT_PARENT_FILLED,
                    parent_order_id=oid, symbol=p.symbol,
                    qty=qty_this, price=float(fill_price),
                ))
                to_remove.append(oid)
        for oid in to_remove:
            self._pending_parents.pop(oid, None)

    def _step_attach_pending(self, *, now_ts: pd.Timestamp) -> None:
        to_remove: list[str] = []
        for bid, pend in list(self._attach_pending.items()):
            bracket = pend.bracket
            parent = pend.parent
            if now_ts < pend.target_attach_ts:
                # Check max_unprotected_seconds escalation (this fires when
                # the broker can't attach in time).
                elapsed = (now_ts - bracket.parent_fill_ts).total_seconds() if bracket.parent_fill_ts else 0
                if elapsed > self.cfg.max_unprotected_seconds and bracket.attach_attempts >= self.cfg.max_oco_attach_attempts:
                    bracket.state = self._escalate(bracket=bracket, parent=parent, ts=now_ts)
                    to_remove.append(bid)
                continue
            # Sample attach success.
            if (
                self.cfg.oco_attach_failure_probability > 0
                and self.rng.random() < self.cfg.oco_attach_failure_probability
            ):
                self._emit(BrokerEvent(
                    event_id=next(self._event_id_seq), ts=now_ts,
                    event_type=EVT_OCO_ATTACH_FAILED,
                    parent_order_id=parent.order_id, bracket_id=bid, symbol=parent.symbol,
                    attach_attempt=bracket.attach_attempts,
                    protection_state=bracket.state.value,
                ))
                if bracket.attach_attempts < self.cfg.max_oco_attach_attempts:
                    bracket.attach_attempts += 1
                    pend.target_attach_ts = now_ts + pd.Timedelta(
                        seconds=self.cfg.oco_attach_latency_seconds
                    )
                    self._emit(BrokerEvent(
                        event_id=next(self._event_id_seq), ts=now_ts,
                        event_type=EVT_OCO_ATTACH_PENDING,
                        parent_order_id=parent.order_id, bracket_id=bid, symbol=parent.symbol,
                        attach_attempt=bracket.attach_attempts,
                        protection_state=bracket.state.value,
                    ))
                    continue
                else:
                    bracket.state = self._escalate(bracket=bracket, parent=parent, ts=now_ts)
                    to_remove.append(bid)
                    continue
            # Success.
            bracket.state = ProtectionState.OCO_ACTIVE
            bracket.attached_ts = now_ts
            self._active_brackets[bid] = bracket
            self._emit(BrokerEvent(
                event_id=next(self._event_id_seq), ts=now_ts,
                event_type=EVT_OCO_ATTACHED,
                parent_order_id=parent.order_id, bracket_id=bid, symbol=parent.symbol,
                attach_attempt=bracket.attach_attempts,
                protection_state=bracket.state.value,
            ))
            to_remove.append(bid)
        for bid in to_remove:
            self._attach_pending.pop(bid, None)

    def _step_active_brackets(self, *, now_ts: pd.Timestamp, bar: dict | None) -> None:
        if bar is None:
            return
        try:
            high = float(bar.get("high", 0.0))
            low = float(bar.get("low", 0.0))
            close = float(bar.get("close", 0.0))
        except (TypeError, ValueError):
            return
        symbol = bar.get("symbol") if isinstance(bar, dict) else None
        for bid, bracket in list(self._active_brackets.items()):
            if bracket.state != ProtectionState.OCO_ACTIVE:
                continue
            # Source semantics: stop is checked before target (conservative).
            if low <= bracket.stop_price:
                bracket.state = ProtectionState.CLOSED
                bracket.exit_ts = now_ts
                bracket.exit_price = bracket.stop_price
                bracket.exit_reason = "stop_hit"
                self._emit(BrokerEvent(
                    event_id=next(self._event_id_seq), ts=now_ts,
                    event_type=EVT_STOP_HIT,
                    parent_order_id=bracket.parent_order_id, bracket_id=bid,
                    symbol=symbol, price=bracket.stop_price,
                    protection_state=bracket.state.value,
                ))
                self._active_brackets.pop(bid, None)
                continue
            if high >= bracket.target_price:
                bracket.state = ProtectionState.CLOSED
                bracket.exit_ts = now_ts
                bracket.exit_price = bracket.target_price
                bracket.exit_reason = "target_hit"
                self._emit(BrokerEvent(
                    event_id=next(self._event_id_seq), ts=now_ts,
                    event_type=EVT_TARGET_HIT,
                    parent_order_id=bracket.parent_order_id, bracket_id=bid,
                    symbol=symbol, price=bracket.target_price,
                    protection_state=bracket.state.value,
                ))
                self._active_brackets.pop(bid, None)

    def _escalate(
        self, *, bracket: OcoBracket, parent: ParentOrder, ts: pd.Timestamp,
    ) -> ProtectionState:
        """Run the escalation ladder past OCO failure."""
        if self.cfg.fallback_stop_enabled:
            self.submit_fallback_stop(parent=parent, stop_price=bracket.stop_price, ts=ts)
            bracket.fallback_stop_price = bracket.stop_price
            return ProtectionState.FALLBACK_STOP_ACTIVE
        if self.cfg.flatten_if_unprotected:
            self.flatten(parent=parent, ts=ts)
            bracket.exit_ts = ts
            bracket.exit_reason = "flattened_unprotected"
            return ProtectionState.FLATTENING
        return ProtectionState.OCO_FAILED


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_buy_fill_price(
    quote: dict | None, bar: dict | None, limit_price: float | None,
) -> float | None:
    """Pick a fill price for the buy side. Prefers ask; falls back to bar open."""
    if quote is not None:
        ask = _safe_float(quote.get("ask_price") if isinstance(quote, dict) else getattr(quote, "ask_price", None))
        if ask and ask > 0:
            if limit_price is not None and ask > limit_price:
                return None  # marketable_limit cannot fill above the limit
            return ask
    if bar is not None:
        open_p = _safe_float(bar.get("open") if isinstance(bar, dict) else getattr(bar, "open", None))
        if open_p and open_p > 0:
            return open_p
    return None


def _safe_float(v) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f > 0 else None
