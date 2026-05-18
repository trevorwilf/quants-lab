"""Simulated order objects + Phase fidelity-4 broker FSM types.

The legacy ``SimulatedOrder`` dataclass is kept for back-compat (signal_fade
and a couple of other paths reference it). New code uses the
``ParentOrder``/``OcoBracket`` types alongside ``SimulatedBroker``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

import pandas as pd


@dataclass
class SimulatedOrder:
    order_id: str
    symbol: str
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit", "stop"]
    submitted_at: pd.Timestamp
    limit_price: float | None = None
    stop_price: float | None = None
    status: Literal["pending", "filled", "canceled", "rejected"] = "pending"
    fill_price: float | None = None
    fill_time: pd.Timestamp | None = None
    qty_requested: int = 0
    qty_filled: int = 0
    diagnostics: dict = field(default_factory=dict)

    def mark_filled(self, *, fill_price: float, fill_time: pd.Timestamp, qty: int | None = None) -> None:
        self.status = "filled"
        self.fill_price = fill_price
        self.fill_time = fill_time
        self.qty_filled = qty if qty is not None else self.qty_requested


class OrderStatus(str, Enum):
    NEW = "new"
    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ProtectionState(str, Enum):
    UNPROTECTED = "unprotected"
    ATTACH_PENDING = "attach_pending"
    OCO_ACTIVE = "oco_active"
    OCO_FAILED = "oco_failed"
    FALLBACK_STOP_ACTIVE = "fallback_stop_active"
    FLATTENING = "flattening"
    CLOSED = "closed"


@dataclass
class FillEvent:
    ts: pd.Timestamp
    qty: int
    price: float


@dataclass
class ParentOrder:
    order_id: str
    symbol: str
    side: Literal["buy", "sell"]
    style: Literal["market", "marketable_limit"]
    submitted_ts: pd.Timestamp
    timeout_seconds: int
    qty_requested: int
    limit_price: float | None = None
    status: OrderStatus = OrderStatus.NEW
    filled_qty: int = 0
    avg_fill_price: float = 0.0
    fills: list[FillEvent] = field(default_factory=list)
    reject_reason: str | None = None

    def add_fill(self, *, ts: pd.Timestamp, qty: int, price: float) -> None:
        if qty <= 0:
            return
        fill = FillEvent(ts=ts, qty=qty, price=price)
        self.fills.append(fill)
        new_qty = self.filled_qty + qty
        if new_qty > 0:
            self.avg_fill_price = (
                (self.avg_fill_price * self.filled_qty + price * qty) / new_qty
            )
        self.filled_qty = new_qty
        if self.filled_qty >= self.qty_requested:
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIALLY_FILLED


@dataclass
class OcoBracket:
    order_id: str
    parent_order_id: str
    stop_price: float
    target_price: float
    time_in_force: Literal["GTC", "DAY"]
    state: ProtectionState = ProtectionState.UNPROTECTED
    attach_attempts: int = 0
    attached_ts: pd.Timestamp | None = None
    fallback_stop_price: float | None = None
    parent_fill_ts: pd.Timestamp | None = None
    exit_ts: pd.Timestamp | None = None
    exit_price: float | None = None
    exit_reason: str | None = None
