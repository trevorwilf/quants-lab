"""
Base and quote balance tracking for the simulator.

Spot constraints (when enforce_spot_constraints=True):
- Cannot sell more base than you hold (no naked shorting)
- Cannot spend more quote than you hold (no unbacked buying)
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class Inventory:
    """Tracks base and quote balances during simulation."""
    base_balance: float = 0.0
    quote_balance: float = 0.0
    enforce_spot_constraints: bool = True

    def buy(self, quantity: float, price: float, fee_quote: float) -> bool:
        """Execute a buy: spend quote, receive base, pay fee in quote.

        Returns True if executed, False if insufficient quote (spot mode).
        """
        cost = quantity * price + fee_quote
        if self.enforce_spot_constraints and cost > self.quote_balance:
            return False
        self.quote_balance -= cost
        self.base_balance += quantity
        return True

    def sell(self, quantity: float, price: float, fee_quote: float) -> bool:
        """Execute a sell: spend base, receive quote, pay fee in quote.

        Returns True if executed, False if insufficient base (spot mode).
        """
        if self.enforce_spot_constraints and quantity > self.base_balance:
            return False
        revenue = quantity * price - fee_quote
        self.quote_balance += revenue
        self.base_balance -= quantity
        return True

    def available_base_for_sell(self) -> float:
        """Return the maximum base that can be sold (spot mode)."""
        if not self.enforce_spot_constraints:
            return float('inf')
        return max(0.0, self.base_balance)

    def available_quote_for_buy(self) -> float:
        """Return the maximum quote available to spend (spot mode)."""
        if not self.enforce_spot_constraints:
            return float('inf')
        return max(0.0, self.quote_balance)

    def max_buy_quantity(self, price: float, fee_rate: float = 0.0) -> float:
        """Return the maximum base quantity that can be bought at given price.

        Accounts for fees: cost = qty * price * (1 + fee_rate).
        """
        if price <= 0:
            return 0.0
        available = self.available_quote_for_buy()
        if available <= 0:
            return 0.0
        # qty * price * (1 + fee_rate) <= available
        return available / (price * (1.0 + fee_rate))

    def equity(self, mid_price: float) -> float:
        """Total equity in quote terms."""
        return self.quote_balance + self.base_balance * mid_price

    def copy(self) -> "Inventory":
        """Return a copy of the current state."""
        return Inventory(self.base_balance, self.quote_balance, self.enforce_spot_constraints)
