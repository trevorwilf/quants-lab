"""range_ladder strategy — passive maker ladder of FIXED price rungs.

Models the live Hummingbot controller `range_inventory_ladder` (NonKYC +
Kraken): buy rungs below price, sell rungs above, weighted capital per rung.

Unlike the directional strategies (MR BB+RSI, EMA regime-hold) this strategy
does NOT run through SimEngine's order/fill machinery. Fills are simulated by
the dedicated OHLC-path kernel in `pmm_lab.features._numba_range_ladder`
(an exact port of the validated ladder_lab kernel). The Strategy-protocol
methods exist for factory/registry uniformity:

- `compute_signals` returns a passthrough SignalOutput (the ladder has no
  indicator signals; the shared signal cache treats it as a no-op entry).
- `build_orders` always returns no orders — the SimEngine path is unused.

Phase A scope: ladder STRUCTURE only. Timing parameters are FROZEN at live
values (cooldown 3600 s → `cooldown_bars`; `executor_refresh_time` is NOT
modeled — Phase B, event-level sim).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, fields
from typing import List, Optional, Tuple

import numpy as np

from pmm_lab.config.params import PairRules
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.executor_model import Order, SimResult
from pmm_lab.sim.inventory import Inventory
from pmm_lab.sim.strategy import SignalOutput
from pmm_lab.strategies.range_ladder_gen import (
    DEFAULT_MIN_WEIGHT_FRAC,
    RungSet,
    build_rungs,
)

logger = logging.getLogger(__name__)

# Number of trailing train closes the anchor median is computed from.
ANCHOR_LOOKBACK_BARS = 3


@dataclass(frozen=True)
class RangeLadderConfig:
    """Generative ladder parameters + fund/fee/timing fields.

    All rung placement is relative to a per-fold anchor; the config carries
    NO absolute prices unless the `literal_*` escape hatch is used (needed to
    benchmark live incumbent configs whose raw rung prices are not in the
    generative search space).
    """

    # --- Generative structure (the Phase A search space) ---
    n_buy: int = 5
    n_sell: int = 5
    buy_near_pct: float = 0.02
    buy_far_pct: float = 0.15
    sell_near_pct: float = 0.02
    sell_far_pct: float = 0.15
    buy_gamma: float = 1.0
    sell_gamma: float = 1.0
    k_buy: float = 0.0
    k_sell: float = 0.0
    min_weight_frac: float = DEFAULT_MIN_WEIGHT_FRAC

    # --- Fund / economics ---
    fund_quote: float = 1000.0
    quote_frac: float = 0.5
    fee: float = 0.002          # maker fee — set from exchange rules by the canonicalizer
    slip: float = 0.0           # base-sim slip (stress uses its own floor)

    # --- Timing (Phase A frozen; executor_refresh_time NOT modeled → Phase B) ---
    cooldown_bars: int = 1      # round(3600 / bar_seconds) at the study interval
    max_fills_per_bar: int = 0  # 0 = unbounded (base sim); stress forces 1
    body_only: bool = False

    # --- Stress plumbing ---
    stress_spread_pct: float = 0.0   # measured spread; stress slip = max(0.001, spread/2)

    # --- Literal escape hatch (live incumbent benchmarking) ---
    literal_buy_prices: Optional[Tuple[float, ...]] = None
    literal_buy_weights: Optional[Tuple[float, ...]] = None
    literal_sell_prices: Optional[Tuple[float, ...]] = None
    literal_sell_weights: Optional[Tuple[float, ...]] = None

    def __post_init__(self):
        if not self.uses_literal_ladder:
            if self.n_buy < 3 or self.n_sell < 3:
                raise ValueError(
                    f"range_ladder requires n_buy/n_sell >= 3 (n == 1 or 2 is "
                    f"not allowed); got n_buy={self.n_buy}, n_sell={self.n_sell}"
                )
        else:
            literal = (
                self.literal_buy_prices, self.literal_buy_weights,
                self.literal_sell_prices, self.literal_sell_weights,
            )
            if any(x is None for x in literal):
                raise ValueError(
                    "literal ladder requires all four of literal_buy_prices, "
                    "literal_buy_weights, literal_sell_prices, literal_sell_weights"
                )
            if (len(self.literal_buy_prices) != len(self.literal_buy_weights)
                    or len(self.literal_sell_prices) != len(self.literal_sell_weights)):
                raise ValueError("literal ladder price/weight lengths must match")
        if not (0.0 < self.quote_frac < 1.0):
            raise ValueError(f"quote_frac must be in (0, 1); got {self.quote_frac}")
        if self.fund_quote <= 0:
            raise ValueError(f"fund_quote must be positive; got {self.fund_quote}")

    @property
    def uses_literal_ladder(self) -> bool:
        return self.literal_buy_prices is not None or self.literal_sell_prices is not None

    def to_fingerprint(self) -> tuple:
        """Hashable fingerprint of ALL fields (candidate dedup in notebooks)."""
        parts = []
        for f in fields(self):
            val = getattr(self, f.name)
            if isinstance(val, list):
                val = tuple(val)
            parts.append(val)
        return tuple(parts)

    def resolve_rungs(self, anchor: float, price_tick: float) -> RungSet:
        """Concrete ladder at the given anchor (or the literal ladder)."""
        if self.uses_literal_ladder:
            return RungSet(
                buys=np.sort(np.asarray(self.literal_buy_prices, dtype=np.float64))[::-1],
                sells=np.sort(np.asarray(self.literal_sell_prices, dtype=np.float64)),
                buy_weights=np.asarray(self.literal_buy_weights, dtype=np.float64),
                sell_weights=np.asarray(self.literal_sell_weights, dtype=np.float64),
            )
        return build_rungs(anchor, self, price_tick)


def compute_anchor(closes: np.ndarray, lookback: int = ANCHOR_LOOKBACK_BARS) -> float:
    """Median of the last `lookback` closes — the ladder anchor.

    Callers are responsible for passing TRAIN-only closes (leakage tests
    assert the anchor never sees test bars).
    """
    closes = np.asarray(closes, dtype=np.float64)
    if len(closes) == 0:
        raise ValueError("compute_anchor: empty close array")
    return float(np.median(closes[-lookback:]))


class RangeLadderStrategy:
    """range_ladder strategy — Strategy-protocol shell + kernel runner."""

    def __init__(self, config: RangeLadderConfig):
        self.config = config

    def compute_signals(self, candles: np.ndarray) -> SignalOutput:
        """Passthrough signals — the ladder has no indicator pipeline.

        Exposes close/timestamp so generic tooling that inspects signals
        keeps working; warmup_end=0 because rung placement needs no warmup.
        """
        return SignalOutput(
            warmup_end=0,
            data={
                "close_price": candles["close"].astype(np.float64),
                "timestamp": candles["timestamp"].astype(np.float64),
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
        """No-op: range_ladder does not use the SimEngine order path.

        Fills are simulated by the ladder kernel (`run`); this exists only
        to satisfy the Strategy protocol.
        """
        return [], 0, 0

    def run(
        self,
        candles: np.ndarray,
        anchor: float,
        pair_rules: PairRules,
        bar_interval_seconds: int,
        use_numba: Optional[bool] = None,
    ) -> dict:
        """Run the base (non-stress) ladder sim on a candle window."""
        cfg = self.config
        rungs = cfg.resolve_rungs(anchor, pair_rules.price_tick)
        from pmm_lab.features._numba_range_ladder import run_ladder_sim
        return run_ladder_sim(
            candles["open"], candles["high"], candles["low"], candles["close"],
            rungs.buys, rungs.sells, rungs.buy_weights, rungs.sell_weights,
            fund=cfg.fund_quote,
            quote_frac=cfg.quote_frac,
            fee=cfg.fee,
            slip=cfg.slip,
            cooldown_bars=cfg.cooldown_bars,
            max_fills_per_bar=cfg.max_fills_per_bar,
            body_only=cfg.body_only,
            bar_interval_seconds=bar_interval_seconds,
            use_numba=use_numba,
        )


def run_range_ladder_window(
    config: RangeLadderConfig,
    pair_rules: PairRules,
    candles: np.ndarray,
    sim_start_idx: int = 0,
    bar_interval_seconds: int = 3600,
) -> SimResult:
    """Adapter for the generic dispatch layer (runner_dispatch/walkforward).

    Computes the anchor from the closes strictly BEFORE `sim_start_idx`
    (train side of the fold boundary — never test data), runs the kernel on
    `candles[sim_start_idx:]`, and assembles a SimResult whose equity and
    position arrays align with the full `candles` index space (bars before
    sim_start hold the initial fund / zero position).

    The ladder kernel records fill COUNTS, not fill events, so `trades` is
    empty; `n_orders_filled` carries the total fill count.
    """
    sim_start_idx = int(sim_start_idx or 0)
    n = len(candles)
    if sim_start_idx >= n:
        raise ValueError(
            f"sim_start_idx ({sim_start_idx}) beyond candle array ({n} bars)"
        )
    closes = candles["close"].astype(np.float64)
    if config.uses_literal_ladder:
        anchor = float(closes[max(sim_start_idx - 1, 0)])  # unused for rung placement
    elif sim_start_idx > 0:
        anchor = compute_anchor(closes[:sim_start_idx])
    else:
        anchor = float(closes[0])

    strategy = RangeLadderStrategy(config)
    window = candles[sim_start_idx:]
    result = strategy.run(window, anchor, pair_rules, bar_interval_seconds)

    fund = config.fund_quote
    equity = np.full(n, fund, dtype=np.float64)
    equity[sim_start_idx:] = result["equity"]
    position = np.zeros(n, dtype=np.float64)
    position[sim_start_idx:] = result["base_history"]

    return SimResult(
        trades=[],
        equity_curve=equity,
        position_history=position,
        n_orders_placed=result["trades"],
        n_orders_filled=result["trades"],
        n_orders_rejected=0,
        n_market_exits=0,
        final_base_balance=result["final_base"],
        final_quote_balance=result["final_quote"],
    )
