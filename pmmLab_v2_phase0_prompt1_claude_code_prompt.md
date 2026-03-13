# pmmLab v2 — Phase 0, Prompt 1: Strategy-Generic Engine Refactor

## Claude Code Prompt

**File:** `pmmLab_v2_phase0_prompt1_claude_code_prompt.md`

**Goal:** Extract a generic `SimEngine` from `CandleSimRunner`, define a `Strategy` protocol, re-implement PMM Dynamic as a strategy plugin, and keep `CandleSimRunner` as a backward-compatible wrapper. All existing tests must pass unchanged. Comprehensive new tests verify the engine, the protocol, and exact parity with the old code path.

---

## 0. Project Location — READ THIS BEFORE WRITING ANY CODE

```bash
cd /quants-lab/research_notebooks/market_lab/pmm_dynamic
```

**CRITICAL PATH RULES:**
- WRONG: `$PMM/pmm_lab/sim/engine.py`
- RIGHT: `/quants-lab/research_notebooks/market_lab/pmm_dynamic/pmm_lab/sim/engine.py`

All paths must be full absolute paths in every command, every `test -f`, every import verification.

---

## 1. Architecture Overview

### Current (v1)
```
CandleSimRunner
├── compute_pmm_dynamic_features()   ← strategy-specific
├── align_features()                 ← strategy-specific
├── _build_order_ladder()            ← strategy-specific
├── _check_triple_barrier()          ← generic
└── run()                            ← mixed: generic loop + strategy calls
```

### Target (v2)
```
SimEngine (generic)
├── _check_triple_barrier()
├── _process_fills()
├── _process_exits()
├── _force_close()
└── run(candles, strategy) → SimResult

Strategy (protocol)
├── compute_signals(candles) → SignalOutput
└── build_orders(bar_idx, signals, ...) → List[Order]

PMMDynamicStrategy (implements Strategy)
├── compute_signals() → calls compute_pmm_dynamic_features + align
└── build_orders() → builds spread ladder from reference_price × spread × spread_multiplier

CandleSimRunner (backward-compatible wrapper)
└── run() → creates PMMDynamicStrategy + SimEngine, delegates
```

---

## 2. New Files to Create

### 2a. `pmm_lab/sim/engine_config.py` — Generic execution config

```
/quants-lab/research_notebooks/market_lab/pmm_dynamic/pmm_lab/sim/engine_config.py
```

```python
"""
Generic simulation engine configuration.

Contains only execution parameters (barriers, fills, timing, inventory).
Strategy-specific parameters (indicator lengths, spread formulas) live
in each Strategy implementation.
"""

from dataclasses import dataclass
from typing import Optional


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
```

### 2b. `pmm_lab/sim/strategy.py` — Strategy protocol + SignalOutput

```
/quants-lab/research_notebooks/market_lab/pmm_dynamic/pmm_lab/sim/strategy.py
```

```python
"""
Strategy protocol for the generic simulation engine.

Any trading strategy must implement this protocol to be runnable
by SimEngine. The engine handles fills, barriers, inventory, and equity.
The strategy handles signals, order construction, and warmup.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Protocol, runtime_checkable, Optional

from pmm_lab.sim.executor_model import Order
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.inventory import Inventory
from pmm_lab.config.params import PairRules


@dataclass
class SignalOutput:
    """Output from Strategy.compute_signals().

    Contains:
    - warmup_end: first bar index where all signals are valid
    - data: dict of strategy-specific signal arrays, each length == n_candles
    """
    warmup_end: int
    data: Dict[str, np.ndarray] = field(default_factory=dict)

    def get(self, key: str, bar_idx: int) -> float:
        """Get a signal value at a specific bar. Returns NaN if unavailable."""
        arr = self.data.get(key)
        if arr is None or bar_idx >= len(arr):
            return float('nan')
        return float(arr[bar_idx])

    def is_valid(self, bar_idx: int) -> bool:
        """Check if signals are valid (past warmup) at this bar."""
        return bar_idx >= self.warmup_end


@runtime_checkable
class Strategy(Protocol):
    """Protocol that all trading strategies must implement.

    The engine calls:
    1. compute_signals(candles) once at the start → SignalOutput
    2. build_orders(...) at each refresh → list of Order objects

    The engine handles everything else: fills, barriers, inventory,
    equity tracking, and position management.
    """

    def compute_signals(self, candles: np.ndarray) -> SignalOutput:
        """Compute all strategy signals from candle data.

        Must be causal: signal at bar t depends only on candles[0:t+1].

        Parameters
        ----------
        candles : np.ndarray
            Canonical structured candle array.

        Returns
        -------
        SignalOutput
            Signal arrays and warmup index.
        """
        ...

    def build_orders(
        self,
        bar_idx: int,
        signals: SignalOutput,
        engine_config: EngineConfig,
        pair_rules: PairRules,
        inventory: Inventory,
    ) -> Tuple[List[Order], int, int]:
        """Build orders for a single bar.

        Called by the engine when a refresh is triggered.

        Parameters
        ----------
        bar_idx : int
            Current bar index.
        signals : SignalOutput
            Pre-computed signals (from compute_signals).
        engine_config : EngineConfig
            Generic execution configuration.
        pair_rules : PairRules
            Exchange rules for rounding and min-notional.
        inventory : Inventory
            Current inventory state.

        Returns
        -------
        Tuple[List[Order], int placed, int rejected]
        """
        ...
```

### 2c. `pmm_lab/sim/engine.py` — Generic simulation engine

```
/quants-lab/research_notebooks/market_lab/pmm_dynamic/pmm_lab/sim/engine.py
```

This is the big one. Extract ALL generic logic from `CandleSimRunner.run()` and `_check_triple_barrier()` into `SimEngine`. The engine:

1. Calls `strategy.compute_signals(candles)` once
2. Iterates over bars
3. At each bar: processes exits → processes fills → checks refresh → calls `strategy.build_orders()` if refresh needed
4. Records equity and position
5. Force-closes at end

```python
"""
Generic candle-based simulation engine.

Handles: fills, triple-barrier exits, inventory, equity tracking, order lifecycle.
Does NOT handle: signal computation, order construction — those come from the Strategy.
"""

import logging
import numpy as np
from typing import Optional, List

from pmm_lab.config.params import PairRules
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.strategy import Strategy, SignalOutput
from pmm_lab.sim.executor_model import SimResult, Trade, Order
from pmm_lab.sim.inventory import Inventory
from pmm_lab.sim.fill_model import check_buy_fill, check_sell_fill
from pmm_lab.sim.fees import compute_fee, compute_slippage
from pmm_lab.sim.latency import is_order_active
from pmm_lab.config.exchange_rules import round_amount

logger = logging.getLogger(__name__)


class SimEngine:
    """Generic candle-based simulation engine.

    Usage:
        engine = SimEngine(engine_config, pair_rules)
        result = engine.run(candles, strategy)
    """

    def __init__(self, config: EngineConfig, pair_rules: PairRules):
        self.config = config
        self.pair_rules = pair_rules
        self._warned_no_orders = False

    def _check_triple_barrier(
        self,
        trade: Trade,
        bar_idx: int,
        candle_high: float,
        candle_low: float,
        candle_close: float,
        current_ts: int,
    ) -> Optional[tuple[float, str]]:
        """Check triple barrier conditions. Identical logic to v1 CandleSimRunner."""
        # COPY THE ENTIRE _check_triple_barrier METHOD FROM runner.py
        # Use self.config (EngineConfig) instead of self.config (SimConfig)
        # The fields are named identically, so the code is the same.
        ...

    def run(
        self,
        candles: np.ndarray,
        strategy: Strategy,
        sim_start_idx: Optional[int] = None,
    ) -> SimResult:
        """Run a full backtest.

        Parameters
        ----------
        candles : np.ndarray
            Canonical structured candle array.
        strategy : Strategy
            Strategy implementation providing signals and orders.
        sim_start_idx : int, optional
            Bar index where simulation starts. Defaults to signals warmup_end.

        Returns
        -------
        SimResult
        """
        cfg = self.config
        rules = self.pair_rules
        n = len(candles)
        self._warned_no_orders = False

        # 1. Compute signals via strategy
        signals = strategy.compute_signals(candles)
        warmup_end = signals.warmup_end

        loop_start = max(warmup_end, sim_start_idx) if sim_start_idx is not None else warmup_end

        # 2. Initialize inventory and tracking arrays
        inventory = Inventory(base_balance=0.0, quote_balance=cfg.total_amount_quote)
        equity_curve = np.zeros(n, dtype="float64")
        position_history = np.zeros(n, dtype="float64")

        trades: List[Trade] = []
        open_trades: List[Trade] = []
        active_orders: List[Order] = []
        n_orders_placed = 0
        n_orders_filled = 0
        n_orders_rejected = 0
        n_market_exits = 0
        trade_counter = 0
        last_refresh_ts: Optional[int] = None
        last_fill_ts: Optional[int] = None

        # Fill pre-loop bars
        for i in range(min(loop_start, n)):
            equity_curve[i] = inventory.equity(float(candles["close"][i]))
            position_history[i] = inventory.base_balance

        # 3. Main loop
        for bar in range(loop_start, n):
            ts = int(candles["timestamp"][bar])
            c_high = float(candles["high"][bar])
            c_low = float(candles["low"][bar])
            c_close = float(candles["close"][bar])
            c_volume = float(candles["volume"][bar])

            # Skip if signals not valid
            if not signals.is_valid(bar):
                equity_curve[bar] = inventory.equity(c_close)
                position_history[bar] = inventory.base_balance
                continue

            # a. Triple barrier exits
            # ... SAME LOGIC AS v1 runner.py lines 307-370 ...

            # b. Fill processing with shared bar capacity
            # ... SAME LOGIC AS v1 runner.py lines 372-457 ...

            # c. Refresh check — calls strategy.build_orders()
            needs_refresh = False
            if last_refresh_ts is None:
                needs_refresh = True
            elif ts - last_refresh_ts >= cfg.executor_refresh_time:
                needs_refresh = True

            in_cooldown = False
            if last_fill_ts is not None and ts - last_fill_ts < cfg.cooldown_time:
                in_cooldown = True

            if needs_refresh and not in_cooldown:
                active_orders = []
                new_orders, placed, rejected = strategy.build_orders(
                    bar, signals, cfg, rules, inventory
                )
                if placed == 0 and not self._warned_no_orders:
                    self._warned_no_orders = True
                    logger.warning(
                        "Bar %d: no orders placed (this warning will not repeat)", bar
                    )
                active_orders = new_orders
                n_orders_placed += placed
                n_orders_rejected += rejected
                last_refresh_ts = ts

            # d. Record equity
            equity_curve[bar] = inventory.equity(c_close)
            position_history[bar] = inventory.base_balance

        # 4. Force-close
        # ... SAME LOGIC AS v1 runner.py lines 495-539 ...

        return SimResult(
            trades=trades,
            equity_curve=equity_curve,
            position_history=position_history,
            n_orders_placed=n_orders_placed,
            n_orders_filled=n_orders_filled,
            n_orders_rejected=n_orders_rejected,
            n_market_exits=n_market_exits,
            final_base_balance=inventory.base_balance,
            final_quote_balance=inventory.quote_balance,
        )
```

**IMPORTANT:** The sections marked `# ... SAME LOGIC AS v1 ...` must be copied exactly from the current `runner.py`. The only changes are:
- Use `self.config` (EngineConfig) instead of `self.config` (SimConfig) — field names are identical
- Use `strategy.build_orders()` instead of `self._build_order_ladder()`
- Use `signals.is_valid(bar)` instead of `np.isnan(ref_price) or np.isnan(spread_mult)`
- The triple barrier, fill processing, spot constraints, and force-close logic are UNCHANGED

### 2d. `pmm_lab/strategies/__init__.py` — New strategies package

```
/quants-lab/research_notebooks/market_lab/pmm_dynamic/pmm_lab/strategies/__init__.py
```

```python
"""Trading strategy implementations for the generic SimEngine."""
```

### 2e. `pmm_lab/strategies/pmm_dynamic.py` — PMM Dynamic strategy plugin

```
/quants-lab/research_notebooks/market_lab/pmm_dynamic/pmm_lab/strategies/pmm_dynamic.py
```

```python
"""
PMM Dynamic strategy implementation.

Implements the Strategy protocol for the PMM Dynamic market-making controller.
Signal computation (NATR, MACD z-score) and order ladder construction are
strategy-specific. Everything else (fills, barriers, inventory) is handled
by SimEngine.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional

from pmm_lab.sim.strategy import Strategy, SignalOutput
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.executor_model import Order
from pmm_lab.sim.inventory import Inventory
from pmm_lab.config.params import PairRules
from pmm_lab.features.pmm_dynamic_features import (
    PMMDynamicConfig, compute_pmm_dynamic_features
)
from pmm_lab.features.alignment import align_features
from pmm_lab.config.exchange_rules import round_price, round_amount, check_min_notional


@dataclass(frozen=True)
class PMMDynamicStrategyConfig:
    """PMM Dynamic strategy-specific parameters."""
    # Indicator config
    macd_fast: int = 21
    macd_slow: int = 42
    macd_signal: int = 9
    natr_length: int = 14
    timestamp_mode: str = "open"

    # Spread ladders (in NATR multiplier units)
    buy_spreads: tuple = ()        # e.g., (1.0, 2.0, 4.0)
    sell_spreads: tuple = ()       # e.g., (1.0, 2.0, 4.0)
    buy_amounts_pct: tuple = ()    # per-level percentage of buy-side capital
    sell_amounts_pct: tuple = ()   # per-level percentage of sell-side capital


class PMMDynamicStrategy:
    """PMM Dynamic market-making strategy.

    Implements the Strategy protocol:
    - compute_signals: NATR + MACD z-score → reference_price, spread_multiplier
    - build_orders: spread ladder from reference_price ± spread × spread_multiplier
    """

    def __init__(self, config: PMMDynamicStrategyConfig):
        self.config = config

    @classmethod
    def from_sim_config(cls, sim_config) -> 'PMMDynamicStrategy':
        """Create from a legacy SimConfig for backward compatibility."""
        from pmm_lab.sim.executor_model import SimConfig
        return cls(PMMDynamicStrategyConfig(
            macd_fast=sim_config.macd_fast,
            macd_slow=sim_config.macd_slow,
            macd_signal=sim_config.macd_signal,
            natr_length=sim_config.natr_length,
            timestamp_mode=sim_config.timestamp_mode,
            buy_spreads=tuple(sim_config.buy_spreads),
            sell_spreads=tuple(sim_config.sell_spreads),
            buy_amounts_pct=tuple(sim_config.buy_amounts_pct),
            sell_amounts_pct=tuple(sim_config.sell_amounts_pct),
        ))

    def compute_signals(self, candles: np.ndarray) -> SignalOutput:
        """Compute PMM Dynamic signals: reference_price and spread_multiplier."""
        feat_config = PMMDynamicConfig(
            macd_fast=self.config.macd_fast,
            macd_slow=self.config.macd_slow,
            macd_signal=self.config.macd_signal,
            natr_length=self.config.natr_length,
        )
        raw_features = compute_pmm_dynamic_features(candles, feat_config)
        features = align_features(raw_features, timestamp_mode=self.config.timestamp_mode)

        return SignalOutput(
            warmup_end=features.warmup_end,
            data={
                "reference_price": features.reference_price,
                "spread_multiplier": features.spread_multiplier,
                "natr": features.natr,
                "macd_signal_z": features.macd_signal_z,
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
        """Build buy and sell order ladders using PMM Dynamic spread formula.

        This is the EXACT same logic as v1 CandleSimRunner._build_order_ladder(),
        extracted into the strategy.
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

        # Capital allocation — use current available balances
        available_quote = inventory.available_quote_for_buy()
        buy_capital = min(cfg.buy_side_weight * cfg.total_amount_quote, available_quote)
        sell_capital = (1.0 - cfg.buy_side_weight) * cfg.total_amount_quote

        # Buy side
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

            if not check_min_notional(price, base_amount, rules):
                n_rejected += 1
                continue

            orders.append(Order(
                side="buy", price=price, quantity=base_amount,
                remaining_quantity=base_amount,
                placed_bar=bar_idx, active_bar=bar_idx + cfg.latency_bars, level=i,
            ))
            n_placed += 1

        # Sell side
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

            # Spot constraint: clamp to available base
            if inventory.enforce_spot_constraints:
                available = inventory.available_base_for_sell()
                if base_amount > available:
                    base_amount = round_amount(available, rules)
                    if base_amount <= 0 or not check_min_notional(price, base_amount, rules):
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
```

---

## 3. Files to Modify

### 3a. `pmm_lab/sim/runner.py` — Convert to thin wrapper

Replace the ENTIRE file with a backward-compatible wrapper:

```python
"""
CandleSimRunner — backward-compatible wrapper over SimEngine + PMMDynamicStrategy.

v1 code that uses CandleSimRunner(config, pair_rules).run(candles) continues
to work unchanged. Internally, it delegates to the generic SimEngine.
"""

import numpy as np
from typing import Optional

from pmm_lab.config.params import PairRules
from pmm_lab.sim.executor_model import SimConfig, SimResult
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.engine import SimEngine
from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy


def _sim_config_to_engine_config(sc: SimConfig) -> EngineConfig:
    """Extract generic EngineConfig from a PMM Dynamic SimConfig."""
    return EngineConfig(
        total_amount_quote=sc.total_amount_quote,
        buy_side_weight=sc.buy_side_weight,
        executor_refresh_time=sc.executor_refresh_time,
        cooldown_time=sc.cooldown_time,
        stop_loss=sc.stop_loss,
        take_profit=sc.take_profit,
        time_limit=sc.time_limit,
        take_profit_order_type=sc.take_profit_order_type,
        trailing_stop_activation=sc.trailing_stop_activation,
        trailing_stop_delta=sc.trailing_stop_delta,
        fill_participation_rate=sc.fill_participation_rate,
        latency_bars=sc.latency_bars,
        slippage_bps=sc.slippage_bps,
    )


class CandleSimRunner:
    """Backward-compatible PMM Dynamic simulator.

    Delegates to SimEngine + PMMDynamicStrategy. Existing code that uses
    CandleSimRunner(config, pair_rules).run(candles) works unchanged.

    Usage:
        runner = CandleSimRunner(sim_config, pair_rules)
        result = runner.run(candles)
    """

    def __init__(self, config: SimConfig, pair_rules: PairRules):
        self.config = config
        self.pair_rules = pair_rules
        self._engine_config = _sim_config_to_engine_config(config)
        self._strategy = PMMDynamicStrategy.from_sim_config(config)
        self._engine = SimEngine(self._engine_config, pair_rules)

    def run(self, candles: np.ndarray, sim_start_idx: Optional[int] = None) -> SimResult:
        """Run a full backtest. Delegates to SimEngine."""
        return self._engine.run(candles, self._strategy, sim_start_idx)
```

### 3b. `pmm_lab/sim/__init__.py` — Add new exports

Add to the existing `__init__.py`:

```python
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.strategy import Strategy, SignalOutput
```

---

## 4. New Test Files

### 4a. `tests/unit/test_engine_config.py`

```
/quants-lab/research_notebooks/market_lab/pmm_dynamic/tests/unit/test_engine_config.py
```

Tests:
- `test_engine_config_defaults` — verify all default values match SimConfig defaults
- `test_engine_config_frozen` — verify EngineConfig is frozen (immutable)
- `test_sim_config_to_engine_config_roundtrip` — create SimConfig, extract EngineConfig, verify all 13 fields match

### 4b. `tests/unit/test_signal_output.py`

```
/quants-lab/research_notebooks/market_lab/pmm_dynamic/tests/unit/test_signal_output.py
```

Tests:
- `test_signal_output_get` — verify `.get(key, bar_idx)` returns correct float
- `test_signal_output_get_missing_key` — returns NaN for unknown key
- `test_signal_output_get_out_of_bounds` — returns NaN for bar_idx beyond array length
- `test_signal_output_is_valid` — returns False before warmup_end, True after
- `test_signal_output_empty_data` — empty dict, is_valid works, get returns NaN

### 4c. `tests/unit/test_strategy_protocol.py`

```
/quants-lab/research_notebooks/market_lab/pmm_dynamic/tests/unit/test_strategy_protocol.py
```

Tests:
- `test_pmm_dynamic_implements_strategy` — `isinstance(PMMDynamicStrategy(...), Strategy)` is True
- `test_strategy_protocol_requires_compute_signals` — a class missing compute_signals is NOT a Strategy
- `test_strategy_protocol_requires_build_orders` — a class missing build_orders is NOT a Strategy
- `test_minimal_strategy_implementation` — create a trivial strategy (returns empty orders, constant signals) and verify it runs through SimEngine without error

### 4d. `tests/unit/test_pmm_dynamic_strategy.py`

```
/quants-lab/research_notebooks/market_lab/pmm_dynamic/tests/unit/test_pmm_dynamic_strategy.py
```

Tests:
- `test_from_sim_config` — create from SimConfig, verify all fields transferred correctly
- `test_compute_signals_returns_signal_output` — verify return type and required keys
- `test_compute_signals_warmup_end` — verify warmup_end matches expected value for given params
- `test_compute_signals_has_reference_price` — verify "reference_price" key in data
- `test_compute_signals_has_spread_multiplier` — verify "spread_multiplier" key in data
- `test_build_orders_returns_tuple` — verify (orders, placed, rejected) tuple
- `test_build_orders_buy_and_sell` — verify both sides produced with sufficient inventory
- `test_build_orders_spot_constraint` — verify sell orders clamped when base=0
- `test_build_orders_nan_signals_returns_empty` — NaN signals produce no orders

### 4e. `tests/unit/test_engine.py`

```
/quants-lab/research_notebooks/market_lab/pmm_dynamic/tests/unit/test_engine.py
```

Tests:
- `test_engine_runs_with_pmm_dynamic` — basic end-to-end, verify SimResult fields
- `test_engine_runs_with_minimal_strategy` — use the trivial strategy, verify no crash
- `test_engine_equity_curve_length` — equity_curve length == candle length
- `test_engine_position_history_length` — position_history length == candle length
- `test_engine_sim_start_idx` — verify sim_start_idx is respected
- `test_engine_spot_constraints_no_negative_base` — final_base_balance >= 0
- `test_engine_spot_constraints_no_negative_quote` — final_quote_balance >= -epsilon
- `test_engine_shared_fill_capacity` — total fills per bar <= participation × volume
- `test_engine_triple_barrier_priority` — stop_loss triggers before take_profit when both conditions met

### 4f. `tests/unit/test_engine_parity.py` — **CRITICAL: proves refactor is exact**

```
/quants-lab/research_notebooks/market_lab/pmm_dynamic/tests/unit/test_engine_parity.py
```

This file proves that `SimEngine + PMMDynamicStrategy` produces **byte-identical** results to the old `CandleSimRunner` wrapper path.

Tests:
- `test_parity_equity_curve` — run both paths on `sample_candles_5m`, assert `np.array_equal(result1.equity_curve, result2.equity_curve)`
- `test_parity_position_history` — assert `np.array_equal` for position history
- `test_parity_trade_count` — assert `len(result1.trades) == len(result2.trades)`
- `test_parity_trade_details` — for each trade, assert entry_price, quantity, exit_price, exit_type, pnl_quote match within 1e-12
- `test_parity_order_counts` — assert n_orders_placed, n_orders_filled, n_orders_rejected, n_market_exits match exactly
- `test_parity_final_balances` — assert final_base_balance and final_quote_balance match within 1e-12
- `test_parity_with_sim_start_idx` — run both with sim_start_idx, assert identical
- `test_parity_with_trailing_stop` — config with trailing stop enabled, assert identical
- `test_parity_sample_candles_500` — run on 500-bar fixture, assert identical

Implementation pattern for each parity test:

```python
def test_parity_equity_curve(sample_candles_5m, default_pair_rules):
    config = SimConfig(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5],
        sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
    )

    # Path 1: Old CandleSimRunner (which now wraps SimEngine)
    from pmm_lab.sim.runner import CandleSimRunner
    result_wrapper = CandleSimRunner(config, default_pair_rules).run(sample_candles_5m)

    # Path 2: Direct SimEngine + PMMDynamicStrategy
    from pmm_lab.sim.engine import SimEngine
    from pmm_lab.sim.engine_config import EngineConfig
    from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy
    from pmm_lab.sim.runner import _sim_config_to_engine_config

    engine_config = _sim_config_to_engine_config(config)
    strategy = PMMDynamicStrategy.from_sim_config(config)
    engine = SimEngine(engine_config, default_pair_rules)
    result_direct = engine.run(sample_candles_5m, strategy)

    np.testing.assert_array_equal(result_wrapper.equity_curve, result_direct.equity_curve)
```

Add a `default_pair_rules` fixture to conftest.py if not present:

```python
@pytest.fixture
def default_pair_rules():
    from pmm_lab.config.params import PairRules, FeeConfig
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )
```

---

## 5. Implementation Order

1. Create `pmm_lab/sim/engine_config.py`
2. Create `pmm_lab/sim/strategy.py`
3. Create `pmm_lab/strategies/__init__.py`
4. Create `pmm_lab/strategies/pmm_dynamic.py`
5. Create `pmm_lab/sim/engine.py` — copy all generic logic from `runner.py`, replacing strategy-specific calls with `strategy.build_orders()` and `signals.is_valid()`
6. Replace `pmm_lab/sim/runner.py` with the thin wrapper
7. Update `pmm_lab/sim/__init__.py`
8. Create all test files
9. Run full test suite

---

## 6. Mandatory Validation Protocol

### Step 0: Verify new files exist
```bash
cd /quants-lab/research_notebooks/market_lab/pmm_dynamic

echo "=== Checking new files ==="
for f in \
    pmm_lab/sim/engine_config.py \
    pmm_lab/sim/strategy.py \
    pmm_lab/sim/engine.py \
    pmm_lab/strategies/__init__.py \
    pmm_lab/strategies/pmm_dynamic.py \
    tests/unit/test_engine_config.py \
    tests/unit/test_signal_output.py \
    tests/unit/test_strategy_protocol.py \
    tests/unit/test_pmm_dynamic_strategy.py \
    tests/unit/test_engine.py \
    tests/unit/test_engine_parity.py; do
    test -f "$f" && echo "  OK: $f" || echo "  MISSING: $f"
done
```

### Step 1: Verify imports work
```bash
python -c "
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.strategy import Strategy, SignalOutput
from pmm_lab.sim.engine import SimEngine
from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy, PMMDynamicStrategyConfig
from pmm_lab.sim.runner import CandleSimRunner, _sim_config_to_engine_config
print('All imports OK')
"
```

### Step 2: Verify Strategy protocol
```bash
python -c "
from pmm_lab.sim.strategy import Strategy
from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy, PMMDynamicStrategyConfig

strat = PMMDynamicStrategy(PMMDynamicStrategyConfig(
    buy_spreads=(1.0, 2.0), sell_spreads=(1.0, 2.0),
    buy_amounts_pct=(0.5, 0.5), sell_amounts_pct=(0.5, 0.5),
))
assert isinstance(strat, Strategy), 'PMMDynamicStrategy does not implement Strategy protocol!'
print('Protocol compliance: PASS')
"
```

### Step 3: Run ALL existing tests (must be 100% pass — nothing should break)
```bash
python -m pytest tests/ -v --tb=long -m "not live_mongo" 2>&1
```

**Paste the FULL output of this command so I can verify every existing test still passes.**

### Step 4: Run new tests only
```bash
python -m pytest tests/unit/test_engine_config.py tests/unit/test_signal_output.py tests/unit/test_strategy_protocol.py tests/unit/test_pmm_dynamic_strategy.py tests/unit/test_engine.py tests/unit/test_engine_parity.py -v --tb=long 2>&1
```

**Paste the FULL output of this command so I can verify all new tests pass.**

### Step 5: Parity smoke test (quick manual check)
```bash
python -c "
import numpy as np
from tests.conftest import _make_sample_candles_5m
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.sim.runner import CandleSimRunner, _sim_config_to_engine_config
from pmm_lab.sim.engine import SimEngine
from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy
from pmm_lab.config.params import PairRules, FeeConfig

candles = _make_sample_candles_5m()
config = SimConfig(
    buy_spreads=[1.0, 2.0, 4.0],
    sell_spreads=[1.0, 2.0, 4.0],
    buy_amounts_pct=[0.33, 0.34, 0.33],
    sell_amounts_pct=[0.33, 0.34, 0.33],
    total_amount_quote=100.0,
)
rules = PairRules(price_tick=0.01, amount_step=0.00001, min_notional_quote=1.0,
                  fees=FeeConfig(maker_fee=0.001, taker_fee=0.002))

# Path 1: wrapper
r1 = CandleSimRunner(config, rules).run(candles)

# Path 2: direct engine
engine = SimEngine(_sim_config_to_engine_config(config), rules)
strategy = PMMDynamicStrategy.from_sim_config(config)
r2 = engine.run(candles, strategy)

# Compare
assert np.array_equal(r1.equity_curve, r2.equity_curve), 'Equity curves differ!'
assert np.array_equal(r1.position_history, r2.position_history), 'Position histories differ!'
assert len(r1.trades) == len(r2.trades), f'Trade count: {len(r1.trades)} vs {len(r2.trades)}'
assert r1.n_orders_placed == r2.n_orders_placed, 'Orders placed differ!'
assert r1.n_orders_filled == r2.n_orders_filled, 'Orders filled differ!'
assert abs(r1.final_base_balance - r2.final_base_balance) < 1e-12, 'Final base differs!'
assert abs(r1.final_quote_balance - r2.final_quote_balance) < 1e-12, 'Final quote differs!'

for i, (t1, t2) in enumerate(zip(r1.trades, r2.trades)):
    assert abs(t1.entry_price - t2.entry_price) < 1e-12, f'Trade {i} entry_price differs'
    assert abs(t1.quantity - t2.quantity) < 1e-12, f'Trade {i} quantity differs'
    if t1.exit_price is not None:
        assert abs(t1.exit_price - t2.exit_price) < 1e-12, f'Trade {i} exit_price differs'
    assert t1.exit_type == t2.exit_type, f'Trade {i} exit_type differs'

print()
print('=' * 60)
print('PARITY CHECK: PASS')
print(f'  Trades: {len(r1.trades)}')
print(f'  Orders placed: {r1.n_orders_placed}')
print(f'  Orders filled: {r1.n_orders_filled}')
print(f'  Final equity: {r1.equity_curve[-1]:.4f}')
print(f'  Final base: {r1.final_base_balance:.8f}')
print(f'  Final quote: {r1.final_quote_balance:.4f}')
print('=' * 60)
"
```

**Paste the output so I can verify the parity numbers.**

### Step 6: Summary
```
After all 5 steps pass, report:
============================================================
PHASE 0 PROMPT 1 COMPLETE
============================================================
  New files created:
    pmm_lab/sim/engine_config.py
    pmm_lab/sim/strategy.py
    pmm_lab/sim/engine.py
    pmm_lab/strategies/__init__.py
    pmm_lab/strategies/pmm_dynamic.py

  New test files:
    tests/unit/test_engine_config.py
    tests/unit/test_signal_output.py
    tests/unit/test_strategy_protocol.py
    tests/unit/test_pmm_dynamic_strategy.py
    tests/unit/test_engine.py
    tests/unit/test_engine_parity.py

  Existing tests: XX passed, 0 failed
  New tests: XX passed, 0 failed
  Parity check: PASS (byte-identical results)
============================================================
```
