"""
Generic simulation engine configuration.

Contains only execution parameters (barriers, fills, timing, inventory).
Strategy-specific parameters (indicator lengths, spread formulas) live
in each Strategy implementation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EngineConfig:
    """Execution parameters for the generic simulation engine.

    These are strategy-independent: any market-making strategy needs
    stop-loss, take-profit, refresh timing, fill model settings, etc.
    """
    # Capital allocation
    total_amount_quote: float = 100.0
    buy_side_weight: float = 0.5

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
    slippage_bps: float = 5.0              # basis points adverse slippage on market exits

    # Rebalance
    initial_base_pct: float = 0.0               # fraction of total_amount_quote to pre-buy as base (0 = start empty)
    position_rebalance_threshold_pct: float = 0.0  # 0 = disabled; >0 triggers rebalance when deficit exceeds this %
    skip_rebalance: bool = True                  # True = no rebalance (v1 behavior); False = rebalance enabled

    # Fill realism (v2)
    touch_through: bool = False             # False = v1 touch (<=/>= ), True = strict through (</>)
    entry_spread_bps: float = 0.0           # half-spread adverse cost on maker entries (0 = v1 behavior)
    maker_fill_probability: float = 1.0     # probability a price-eligible fill actually executes (1.0 = v1 behavior)
    taker_probability: float = 0.0          # probability a filled limit order executes as taker (0.0 = v1 behavior)

    # Per-side volume splitting (v2)
    split_volume_by_side: bool = False      # False = v1 shared capacity; True = separate buy/sell pools
    buy_volume_fraction: float = 0.5        # fraction of volume allocated to buy fills (only used when split=True)

    # Volume unit
    volume_is_base: bool = True             # True = volume is base units (default); False = convert from quote

    # Refresh close mode
    refresh_close_mode: str = "keep"        # "keep" = open trades survive refresh (v1)
                                            # "market_close" = force-close open trades at refresh with taker fees + slippage

    # Pre-existing base balance (wallet inventory modeling)
    initial_base_balance: float = 0.0       # base tokens held before bot starts (no fees/slippage — pre-existing)
