"""
Bollinger Bands market-making strategy.

Places buy orders near the lower Bollinger Band and sell orders near the
upper band. Band width serves as the dynamic spread multiplier.

Signals:
  - reference_price = SMA(close, window)
  - spread_multiplier = (upper - lower) / SMA  (band width fraction)
  - upper_band, lower_band (for diagnostics)
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

from pmm_lab.sim.strategy import SignalOutput
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.executor_model import Order
from pmm_lab.sim.inventory import Inventory
from pmm_lab.config.params import PairRules
from pmm_lab.config.exchange_rules import round_price, round_amount, check_min_notional, check_order_size


@dataclass(frozen=True)
class BollingerStrategyConfig:
    """Bollinger Bands strategy parameters."""
    # Bollinger parameters
    bb_window: int = 20              # SMA window length
    bb_stdev: float = 2.0            # number of standard deviations
    timestamp_mode: str = "open"

    # Spread ladders (in band-width multiplier units)
    buy_spreads: tuple = ()          # e.g., (0.5, 1.0, 1.5) — fraction of band width
    sell_spreads: tuple = ()
    buy_amounts_pct: tuple = ()      # per-level capital allocation
    sell_amounts_pct: tuple = ()


class BollingerStrategy:
    """Bollinger Bands market-making strategy.

    Implements the Strategy protocol:
    - compute_signals: SMA + std -> reference_price, spread_multiplier, bands
    - build_orders: spread ladder from SMA +/- spread * band_width_fraction
    """

    def __init__(self, config: BollingerStrategyConfig):
        self.config = config

    def compute_signals(self, candles: np.ndarray) -> SignalOutput:
        """Compute Bollinger Band signals from candle close prices.

        Causal: uses only data up to and including bar t.
        Rolling window ensures no look-ahead.
        """
        close = candles["close"].astype("float64")
        n = len(close)
        cfg = self.config

        # Compute rolling SMA and std (causal)
        sma = np.full(n, np.nan, dtype="float64")
        std = np.full(n, np.nan, dtype="float64")

        for i in range(cfg.bb_window - 1, n):
            window = close[i - cfg.bb_window + 1 : i + 1]
            sma[i] = np.mean(window)
            std[i] = np.std(window, ddof=1) if len(window) > 1 else 0.0

        upper = sma + cfg.bb_stdev * std
        lower = sma - cfg.bb_stdev * std

        # Spread multiplier = band width as fraction of SMA
        # When bands are wide (high volatility), spreads widen automatically
        spread_mult = np.where(sma > 0, (upper - lower) / sma, 0.0)
        # Where SMA is NaN, spread_mult should be NaN too
        spread_mult = np.where(np.isnan(sma), np.nan, spread_mult)

        # Reference price = SMA (middle band)
        reference_price = sma.copy()

        # Warmup: first valid bar is bb_window - 1
        warmup_end = cfg.bb_window  # need bb_window bars of data

        # Apply timestamp alignment (1-bar shift in open mode)
        if cfg.timestamp_mode == "open":
            reference_price = np.roll(reference_price, 1)
            reference_price[0] = np.nan
            spread_mult = np.roll(spread_mult, 1)
            spread_mult[0] = np.nan
            upper = np.roll(upper, 1)
            upper[0] = np.nan
            lower = np.roll(lower, 1)
            lower[0] = np.nan
            warmup_end += 1

        return SignalOutput(
            warmup_end=warmup_end,
            data={
                "reference_price": reference_price,
                "spread_multiplier": spread_mult,
                "upper_band": upper,
                "lower_band": lower,
                "sma": sma if cfg.timestamp_mode == "close" else np.roll(sma, 1),
            },
        )

    def build_orders(
        self,
        bar_idx: int,
        signals: SignalOutput,
        engine_config: EngineConfig,
        pair_rules: PairRules,
        inventory: Inventory,
    ) -> Tuple[List[Order], int, int]:
        """Build buy/sell order ladders using Bollinger band-width spread.

        Same ladder structure as PMM Dynamic, but using Bollinger signals
        instead of NATR + MACD.
        """
        cfg = engine_config
        scfg = self.config
        rules = pair_rules
        orders: List[Order] = []
        n_placed = 0
        n_rejected = 0

        reference_price = signals.get("reference_price", bar_idx)
        spread_multiplier = signals.get("spread_multiplier", bar_idx)

        if np.isnan(reference_price) or np.isnan(spread_multiplier):
            return orders, n_placed, n_rejected

        # Capital allocation
        available_quote = inventory.available_quote_for_buy()
        buy_capital = min(cfg.buy_side_weight * cfg.total_amount_quote, available_quote)
        sell_capital = (1.0 - cfg.buy_side_weight) * cfg.total_amount_quote

        # Buy side — orders below SMA, near lower band
        for i, spread in enumerate(scfg.buy_spreads):
            price = reference_price * (1.0 - spread * spread_multiplier)
            price = round_price(price, rules)
            if price <= 0:
                n_rejected += 1
                continue

            amount_pct = scfg.buy_amounts_pct[i] if i < len(scfg.buy_amounts_pct) else 0.0
            quote_amount = buy_capital * amount_pct
            base_amount = quote_amount / price if price > 0 else 0.0
            base_amount = round_amount(base_amount, rules)

            base_amount, size_reject = check_order_size(base_amount, rules)
            if size_reject:
                n_rejected += 1
                continue

            if not check_min_notional(price, base_amount, rules):
                n_rejected += 1
                continue

            orders.append(Order(
                side="buy", price=price, quantity=base_amount,
                remaining_quantity=base_amount,
                placed_bar=bar_idx, active_bar=bar_idx + cfg.latency_bars, level=i,
            ))
            n_placed += 1

        # Sell side — orders above SMA, near upper band
        for i, spread in enumerate(scfg.sell_spreads):
            price = reference_price * (1.0 + spread * spread_multiplier)
            price = round_price(price, rules)
            if price <= 0:
                n_rejected += 1
                continue

            amount_pct = scfg.sell_amounts_pct[i] if i < len(scfg.sell_amounts_pct) else 0.0
            quote_amount = sell_capital * amount_pct
            base_amount = quote_amount / price if price > 0 else 0.0
            base_amount = round_amount(base_amount, rules)

            # Spot constraint
            if inventory.enforce_spot_constraints:
                available = inventory.available_base_for_sell()
                if base_amount > available:
                    base_amount = round_amount(available, rules)
                    if base_amount <= 0 or not check_min_notional(price, base_amount, rules):
                        n_rejected += 1
                        continue

            base_amount, size_reject = check_order_size(base_amount, rules)
            if size_reject:
                n_rejected += 1
                continue

            if not check_min_notional(price, base_amount, rules):
                n_rejected += 1
                continue

            orders.append(Order(
                side="sell", price=price, quantity=base_amount,
                remaining_quantity=base_amount,
                placed_bar=bar_idx, active_bar=bar_idx + cfg.latency_bars, level=i,
            ))
            n_placed += 1

        return orders, n_placed, n_rejected
