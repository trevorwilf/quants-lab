"""Fill model: next-minute-open + slippage, or quote-based ask/bid + buffer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import pandas as pd


@dataclass(frozen=True)
class FillResult:
    fill_price: float
    fill_time: pd.Timestamp
    model: str
    diagnostics: dict


class BowakaFillModel:
    """Default Bowaka fill model.

    - Buy at next-minute open * (1 + slippage_bps / 10000), or
      ask_price * (1 + slippage_bps / 10000) when quote data is available.
    - Sell at next-minute open * (1 - slippage_bps / 10000), or
      bid_price * (1 - slippage_bps / 10000) when quote data is available.
    """

    def __init__(self, slippage_bps: float = 25.0):
        if slippage_bps < 0:
            raise ValueError("slippage_bps must be >= 0")
        self.slippage_bps = float(slippage_bps)

    @property
    def slip(self) -> float:
        return self.slippage_bps / 10_000.0

    def buy_from_bar(self, bar: dict | pd.Series) -> FillResult:
        open_price = float(bar["open"])
        price = open_price * (1.0 + self.slip)
        return FillResult(
            fill_price=price,
            fill_time=pd.Timestamp(bar["timestamp"]),
            model="next_minute_open_plus_slippage",
            diagnostics={"open": open_price, "slippage_bps": self.slippage_bps},
        )

    def sell_from_bar(self, bar: dict | pd.Series) -> FillResult:
        open_price = float(bar["open"])
        price = open_price * (1.0 - self.slip)
        return FillResult(
            fill_price=price,
            fill_time=pd.Timestamp(bar["timestamp"]),
            model="next_minute_open_minus_slippage",
            diagnostics={"open": open_price, "slippage_bps": self.slippage_bps},
        )

    def buy_from_quote(self, quote: dict | pd.Series) -> FillResult:
        ask = float(quote["ask_price"])
        price = ask * (1.0 + self.slip)
        return FillResult(
            fill_price=price,
            fill_time=pd.Timestamp(quote["timestamp"]),
            model="ask_plus_slippage",
            diagnostics={"ask": ask, "slippage_bps": self.slippage_bps},
        )

    def sell_from_quote(self, quote: dict | pd.Series) -> FillResult:
        bid = float(quote["bid_price"])
        price = bid * (1.0 - self.slip)
        return FillResult(
            fill_price=price,
            fill_time=pd.Timestamp(quote["timestamp"]),
            model="bid_minus_slippage",
            diagnostics={"bid": bid, "slippage_bps": self.slippage_bps},
        )

    def stop_fill(
        self,
        *,
        stop_price: float,
        intrabar_low: float,
        bar_open: float,
        stop_gap_policy: Literal["next_available_open", "stop_price"],
        stop_slippage_pct: float = 0.0,
    ) -> float:
        """Compute stop fill price under bar-based simulation.

        - If bar opens below stop (gap-through-stop), fill at the open under
          ``next_available_open``, or stop_price under ``stop_price``.
        - If stop is touched intrabar without gapping, fill at
          ``stop_price * (1 - stop_slippage_pct)``.
        """
        if bar_open <= stop_price:
            if stop_gap_policy == "next_available_open":
                return bar_open
            return stop_price
        return stop_price * (1.0 - stop_slippage_pct)

    def target_fill(
        self,
        *,
        target_price: float,
        intrabar_high: float,
        bar_open: float,
        target_fill_policy: Literal["limit_touch", "next_minute_open"],
    ) -> float:
        if target_fill_policy == "next_minute_open":
            return bar_open
        return target_price
