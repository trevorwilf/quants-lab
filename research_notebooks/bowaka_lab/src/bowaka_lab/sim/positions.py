"""Simulated position objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

import pandas as pd


@dataclass
class SimulatedPosition:
    trade_id: str
    symbol: str
    signal_date: date
    trade_date: date
    entry_time: pd.Timestamp
    entry_price: float
    qty: int
    stop_price: float
    target_price: float
    max_hold_exit_date: date
    status: Literal["open", "closed"] = "open"
    mfe_pct: float = 0.0
    mae_pct: float = 0.0
    mfe_high_since_entry: float | None = None
    mae_low_since_entry: float | None = None
    time_to_mfe_minutes: int | None = None
    time_to_mae_minutes: int | None = None
    exit_time: pd.Timestamp | None = None
    exit_price: float | None = None
    exit_reason: str | None = None
    realized_pnl: float = 0.0
    diagnostics: dict = field(default_factory=dict)

    @property
    def notional(self) -> float:
        return self.entry_price * self.qty

    def update_mfe_mae(self, *, ts: pd.Timestamp, high: float, low: float, minutes_since_entry: int) -> None:
        if self.entry_price <= 0:
            return
        gain_high = high / self.entry_price - 1.0
        gain_low = low / self.entry_price - 1.0
        if self.mfe_high_since_entry is None or high > self.mfe_high_since_entry:
            self.mfe_high_since_entry = high
            self.mfe_pct = gain_high
            self.time_to_mfe_minutes = minutes_since_entry
        if self.mae_low_since_entry is None or low < self.mae_low_since_entry:
            self.mae_low_since_entry = low
            self.mae_pct = gain_low
            self.time_to_mae_minutes = minutes_since_entry

    def close(self, *, exit_time: pd.Timestamp, exit_price: float, exit_reason: str) -> None:
        self.status = "closed"
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.exit_reason = exit_reason
        self.realized_pnl = (exit_price - self.entry_price) * self.qty
