"""
PMM Dynamic executor model — order placement, refresh, cooldown, triple barrier.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Order:
    """A single limit order."""
    side: str                  # "buy" or "sell"
    price: float
    quantity: float
    remaining_quantity: float
    placed_bar: int            # bar index when placed
    active_bar: int            # bar index when eligible for fills (placed_bar + latency)
    level: int                 # level index (0 = tightest spread)


@dataclass
class Trade:
    """A completed trade (entry fill)."""
    trade_id: int
    side: str                  # "buy" or "sell"
    entry_price: float
    quantity: float
    entry_bar: int
    entry_timestamp: int
    exit_price: Optional[float] = None
    exit_bar: Optional[int] = None
    exit_timestamp: Optional[int] = None
    exit_type: Optional[str] = None   # "take_profit", "stop_loss", "time_limit", "trailing_stop", "refresh"
    pnl_quote: Optional[float] = None
    fee_quote: float = 0.0            # total fees (entry + exit)
    entry_fee_quote: float = 0.0      # entry fill fee (always maker)
    exit_fee_quote: float = 0.0       # exit fee (maker or taker depending on exit_type)
    peak_price: Optional[float] = None  # for trailing stop tracking
    trailing_activated: bool = False


@dataclass(frozen=True)
class SimConfig:
    """Full simulation configuration for one backtest run."""
    # Spread ladders (in NATR multiplier units, NOT percentages)
    buy_spreads: List[float]           # e.g., [1.0, 2.0, 4.0] — length = buy_n_levels
    sell_spreads: List[float]          # e.g., [1.0, 2.0, 4.0] — length = sell_n_levels

    # Amount allocation
    buy_amounts_pct: List[float]       # per-level percentage of buy-side capital
    sell_amounts_pct: List[float]      # per-level percentage of sell-side capital
    buy_side_weight: float = 0.5       # fraction of total_amount_quote allocated to buy side
    total_amount_quote: float = 100.0

    # Timing
    executor_refresh_time: float = 3120.0   # seconds between order refreshes
    cooldown_time: float = 3120.0           # seconds cooldown after a fill

    # Triple barrier
    stop_loss: float = 0.03                 # fraction (e.g., 0.03 = 3%)
    take_profit: float = 0.015              # fraction
    time_limit: int = 43200                 # seconds
    take_profit_order_type: str = "LIMIT"   # "LIMIT" or "MARKET"
    trailing_stop_activation: float = 0.0   # 0 = disabled
    trailing_stop_delta: float = 0.0        # 0 = disabled

    # Fill model
    fill_participation_rate: float = 0.1    # max fraction of candle volume per fill
    latency_bars: int = 1                   # bars delay before order becomes eligible
    slippage_bps: float = 5.0               # basis points adverse slippage on market exits

    # Indicator config (passed through to features)
    macd_fast: int = 21
    macd_slow: int = 42
    macd_signal: int = 9
    natr_length: int = 14

    # Timestamp
    timestamp_mode: str = "open"            # "open" or "close"


@dataclass
class SimResult:
    """Output of a single backtest run."""
    trades: List[Trade]
    equity_curve: np.ndarray         # float64, length = n_candles, quote-denominated
    position_history: np.ndarray     # float64, length = n_candles, base inventory
    n_orders_placed: int
    n_orders_filled: int
    n_orders_rejected: int           # rejected by exchange rules (min notional, etc.)
    n_market_exits: int              # stop-loss, time-limit, trailing-stop exits
    final_base_balance: float
    final_quote_balance: float
