"""Order types for the v2 simulator."""
from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from typing import Optional


class OrderSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"


@dataclass
class OrderPlan:
    side: OrderSide
    order_style: str  # "marketable_limit" | "market" | "limit"
    qty: int
    limit_price: Optional[float] = None
    stop_pct: Optional[float] = None
    target_pct: Optional[float] = None
    max_hold_days: int = 5
    estimated_notional: Optional[float] = None


@dataclass
class ParentOrder:
    parent_order_id: str
    symbol: str
    plan: OrderPlan
    status: OrderStatus = OrderStatus.PENDING
    created_at: Optional[str] = None
    candidate_event_id: Optional[str] = None
    decision_event_id: Optional[str] = None
    filled_qty: int = 0
    avg_fill_price: Optional[float] = None
    raw_broker_response: Optional[dict] = None

    @staticmethod
    def make_id() -> str:
        return f"po_{uuid.uuid4().hex[:16]}"


@dataclass
class ChildOrder:
    child_order_id: str
    parent_order_id: str
    symbol: str
    side: OrderSide
    qty: int
    limit_price: Optional[float]
    status: OrderStatus = OrderStatus.PENDING
    filled_qty: int = 0
    avg_fill_price: Optional[float] = None
    created_at: Optional[str] = None

    @staticmethod
    def make_id() -> str:
        return f"co_{uuid.uuid4().hex[:16]}"
