"""Simulated order objects."""

from __future__ import annotations

from dataclasses import dataclass, field
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
