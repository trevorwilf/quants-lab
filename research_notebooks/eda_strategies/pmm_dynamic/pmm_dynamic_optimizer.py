"""
pmm_dynamic_optimizer.py — CPU PMM Dynamic backtester + Optuna optimizer.

CPU-specific components: PMMDynamicBacktester (simulation loop) and create_objective.
All shared logic lives in pmm_dynamic_core.py.

Reads OHLCV candles from MongoDB (populated by candle_ingest.py on the Trading Pod),
simulates the PMM Dynamic market-making strategy with triple-barrier exits,
and uses Optuna to find optimal parameters.

Author: Trading Pod project
"""

from __future__ import annotations

import logging
import math
import statistics
from dataclasses import replace
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

# All shared components come from core
from pmm_dynamic_core import (
    PMMDynamicConfig,
    PendingOrder,
    Position,
    BacktestResult,
    _suggest_params,
    _compute_objective,
    _interval_to_seconds,
    _auto_spread_min_multiplier,
    _position_pnl,
    _position_pnl_pct,
    _close_position,
    compute_macd,
    compute_natr,
    trial_to_controller_yaml,
    trial_to_config,
    walk_forward_evaluate,
    get_top_n_trials,
    load_candles,
    get_mongo_client,
    validate_candles,
)

log = logging.getLogger(__name__)

# Avoid spamming the same candle QA warnings on every trial/backtest call.
_SEEN_VALIDATE_WARNINGS: set[str] = set()

# ---------------------------------------------------------------------------
# Re-exports — maintained for backward compatibility.
# Any code importing these names from pmm_dynamic_optimizer will continue to work.
# ---------------------------------------------------------------------------
__all__ = [
    # CPU-specific
    "PMMDynamicBacktester",
    "create_objective",
    # Re-exported from core
    "PMMDynamicConfig",
    "PendingOrder",
    "Position",
    "BacktestResult",
    "_suggest_params",
    "_compute_objective",
    "_interval_to_seconds",
    "trial_to_controller_yaml",
    "trial_to_config",
    "walk_forward_evaluate",
    "get_top_n_trials",
    "load_candles",
    "get_mongo_client",
    "compute_macd",
    "compute_natr",
]


# ---------------------------------------------------------------------------
# Backtesting engine
# ---------------------------------------------------------------------------

class PMMDynamicBacktester:
    """
    Vectorized-ish backtester for PMM Dynamic.

    For each candle:
      1. Compute MACD histogram → price_multiplier (shifts mid-price)
      2. Compute NATR → spread_multiplier (scales spreads)
      3. Check if any pending orders would fill (price touches order level)
      4. For open positions: check triple-barrier exits
      5. Track PnL, drawdown, etc.
    """

    def __init__(self, config: PMMDynamicConfig):
        self.cfg = config
        self._rng = random.Random(42)

    def run(self, candles: pd.DataFrame) -> "BacktestResult":
        """
        Run backtest on candle DataFrame.

        Loop per candle:
          STEP 1: Process exits on open positions (ALWAYS, even if indicators NaN)
          STEP 2: Check fills on PENDING ORDERS (placed at candle i-1 or earlier)
          STEP 3: If signals valid AND refresh elapsed: cancel pending, place NEW orders
                  (new orders fillable starting candle i+1 only)
          STEP 4: Mark-to-market equity (ALWAYS)

        Parameters
        ----------
        candles : DataFrame with columns timestamp, open, high, low, close, volume

        Returns
        -------
        BacktestResult with all metrics
        """
        cfg = self.cfg
        df = candles.copy()

        if len(df) < cfg.z_window + 2:
            return BacktestResult.empty()

        # FIX-2: Validate candles at backtester entry (strict mode)
        try:
            vc = validate_candles(df, cfg.interval, raise_on_failure=False, strict=True)
            if vc["warnings"]:
                for w in vc["warnings"]:
                    if w in _SEEN_VALIDATE_WARNINGS:
                        continue
                    _SEEN_VALIDATE_WARNINGS.add(w)
                    log.warning("validate_candles: %s", w)
        except Exception as e:
            log.warning("validate_candles failed: %s", e)

        # BUG-3 V3: Timestamp semantics warning and signal shift logic
        # Determine whether to shift signals by 1 candle (conservative, no look-ahead)
        signal_shift = 0
        if cfg.timestamp_mode == "unknown":
            import warnings
            warnings.warn(
                "timestamp_mode='unknown': Cannot confirm whether candle timestamps are OPEN or "
                "CLOSE times. Defaulting to conservative behavior (shift signals by 1 candle). "
                "Set timestamp_mode='close' ONLY if you have confirmed your data source timestamps "
                "represent candle CLOSE times. Most exchanges (including NonKYC.io) use OPEN times.",
                UserWarning,
                stacklevel=2,
            )
            signal_shift = 1
        elif cfg.timestamp_mode == "open":
            signal_shift = 1

        # ── Compute indicators ──
        macd_df = compute_macd(df["close"], cfg.macd_fast, cfg.macd_slow, cfg.macd_signal)
        df["macd_line"] = macd_df["macd"]
        df["macd_hist"] = macd_df["macd_hist"]
        df["natr"] = compute_natr(df["high"], df["low"], df["close"], cfg.natr_length)

        # BUG-4 FIX: Windowed z-score to match Hummingbot controller (not expanding)
        z_window = max(cfg.macd_fast, cfg.macd_slow, cfg.macd_signal, cfg.natr_length) + 100
        macd_mean = df["macd_line"].rolling(window=z_window, min_periods=20).mean()
        macd_std = df["macd_line"].rolling(window=z_window, min_periods=20).std()
        macd_std = macd_std.replace(0, np.nan).ffill().fillna(1.0)
        df["macd_zscore"] = -((df["macd_line"] - macd_mean) / macd_std)

        # Production signal 2: sign of MACD histogram
        df["macdh_sign"] = df["macd_hist"].apply(lambda x: 1.0 if x > 0 else -1.0)

        # Combined signal (production formula)
        df["price_signal"] = 0.5 * df["macd_zscore"] + 0.5 * df["macdh_sign"]

        # ── Simulation state (spot portfolio model) ──
        positions: List[Position] = []
        closed_positions: List[Position] = []
        pending_orders: List[PendingOrder] = []
        equity_curve: List[float] = []

        # FIX-4: Realistic starting inventory
        initial_capital = cfg.total_amount_quote
        warmup = cfg.z_window
        first_mid_price = float(df.iloc[warmup]["close"]) if len(df) > warmup else float(df.iloc[0]["close"])
        if first_mid_price <= 0:
            first_mid_price = 1.0

        if cfg.initial_inventory_mode == "half_and_half":
            quote_balance = initial_capital * 0.5
            base_balance  = (initial_capital * 0.5) / first_mid_price
        elif cfg.initial_inventory_mode == "all_base":
            quote_balance = 0.0
            base_balance  = initial_capital / first_mid_price
        else:  # "all_quote" — original behavior
            quote_balance = initial_capital
            base_balance  = 0.0

        peak_equity = initial_capital
        max_drawdown = 0.0

        # Time per candle (seconds) — infer from interval string
        candle_seconds = _interval_to_seconds(cfg.interval)

        last_refresh_time = 0.0
        last_close_time = 0.0  # for cooldown_seconds

        # Pre-seed RNG for reproducibility within a single backtest
        rng = self._rng
        rng.seed(42)

        for i in range(warmup, len(df)):
            row = df.iloc[i]
            ts = row["timestamp"].timestamp() if hasattr(row["timestamp"], "timestamp") else float(row["timestamp"])
            mid_price = row["close"]
            candle_high = row["high"]
            candle_low = row["low"]
            candle_volume = row["volume"] if "volume" in row.index else 0.0

            # BUG-3 V3: Signal shift — use previous candle's indicators for order placement
            # Fill checking (Steps 1 & 2) still use candle i's OHLC
            if signal_shift > 0 and i >= warmup + signal_shift:
                signal_row = df.iloc[i - signal_shift]
                natr_val = signal_row["natr"]
                price_signal = signal_row["price_signal"]
            else:
                natr_val = row["natr"]
                price_signal = row["price_signal"]

            # ── STEP 1: Process exits on open positions (ALWAYS) ──
            for pos in positions:
                if pos.closed:
                    continue
                self._check_exit(pos, candle_high, candle_low, mid_price, ts, cfg)

            # Move closed positions, update portfolio
            still_open = []
            for pos in positions:
                if pos.closed:
                    if pos.side == "buy":
                        # Closing a buy: sell base back for quote
                        exit_notional = pos.amount * pos.exit_price
                        exit_fee = pos.exit_fee_paid  # FIX-5: use per-exit fee already set by _close_position
                        quote_balance += exit_notional - exit_fee
                        base_balance -= pos.amount
                    else:
                        # Closing a sell: buy base back with quote
                        exit_notional = pos.amount * pos.exit_price
                        exit_fee = pos.exit_fee_paid  # FIX-5: use per-exit fee already set by _close_position
                        quote_balance -= exit_notional + exit_fee
                        base_balance += pos.amount
                    closed_positions.append(pos)
                    # ADD-2: Cooldown only after stop_loss (match Hummingbot)
                    if cfg.cooldown_on_stop_loss_only:
                        if pos.exit_reason == "stop_loss":
                            last_close_time = ts
                    else:
                        last_close_time = ts
                else:
                    still_open.append(pos)
            positions = still_open

            # ── STEP 2: Check fills on PENDING ORDERS (placed earlier) ──
            # FIX-1 V3: max_open_positions semantics — n_open counts only ACTIVE filled positions.
            # The >= threshold means: if we already have max_open filled positions, cancel pending.
            remaining_orders: List[PendingOrder] = []
            n_open = len(positions)
            # FIX-3 V3: Volume units — compute candle volume in quote
            if cfg.volume_units == "quote":
                candle_volume_quote = candle_volume if candle_volume > 0 else float("inf")
            else:
                # "base" or "unknown" — multiply by close to get quote volume
                if cfg.volume_units == "unknown" and cfg.fill_rate_pct > 0:
                    pass  # warning already emitted via validate_candles
                candle_volume_quote = candle_volume * mid_price if candle_volume > 0 else float("inf")

            for order in pending_orders:
                # Enforce expiration (GPU parity)
                if order.expires_ts > 0 and ts > order.expires_ts:
                    if order.side == "buy":
                        quote_balance += order.quote_reserved
                    elif order.side == "sell":
                        base_balance += order.base_reserved  # FIX-3: refund reserved base
                    continue  # discard expired order

                # Check position cap — cancel order if at capacity
                if cfg.max_open_positions > 0 and n_open >= cfg.max_open_positions:
                    # Cancel: refund reserved capital, do NOT keep order pending
                    if order.side == "buy":
                        quote_balance += order.quote_reserved
                    elif order.side == "sell":
                        base_balance += order.base_reserved  # FIX-3: refund reserved base
                    continue  # order is dropped (not appended to remaining_orders)

                # Latency gate: order must age >= latency_candles candles before it can fill
                if cfg.latency_candles and cfg.latency_candles > 1:
                    min_age_s = float(cfg.latency_candles * candle_seconds)
                    if (ts - order.placed_ts) < min_age_s:
                        remaining_orders.append(order)
                        continue

                filled = False
                if order.side == "buy" and candle_low <= order.price:
                    # ── Realism: deterministic volume-based fill gate (GPU parity) ──
                    if cfg.fill_rate_pct > 0 and candle_volume_quote < float("inf"):
                        if candle_volume_quote * cfg.fill_rate_pct < order.quote_reserved:
                            remaining_orders.append(order)
                            continue
                    # FIX-5: Maker validity check — if open gapped through, it's a taker fill
                    effective_entry_fee = cfg.entry_fee
                    if cfg.maker_validity_check:
                        candle_open = row["open"]
                        if candle_open <= order.price:
                            effective_entry_fee = cfg.taker_fee
                    # Fill the buy: quote already reserved, receive base
                    entry_fee = order.quote_reserved * effective_entry_fee
                    quote_balance -= entry_fee  # fee from remaining balance
                    base_balance += order.amount
                    pos = Position(
                        side="buy",
                        entry_price=order.price,
                        amount=order.amount,
                        entry_quote=order.quote_reserved,
                        entry_time=ts,
                        entry_fee_paid=entry_fee,
                    )
                    positions.append(pos)
                    n_open += 1
                    filled = True

                elif order.side == "sell" and candle_high >= order.price:
                    # ── Realism: deterministic volume-based fill gate (GPU parity) ──
                    if cfg.fill_rate_pct > 0 and candle_volume_quote < float("inf"):
                        if candle_volume_quote * cfg.fill_rate_pct < (order.amount * order.price):
                            remaining_orders.append(order)
                            continue
                    # FIX-5: Maker validity check — if open gapped through, it's a taker fill
                    effective_entry_fee = cfg.entry_fee
                    if cfg.maker_validity_check:
                        candle_open = row["open"]
                        if candle_open >= order.price:
                            effective_entry_fee = cfg.taker_fee
                    # FIX-3: Base was already reserved at placement; do NOT subtract again
                    sell_notional = order.amount * order.price
                    entry_fee = sell_notional * effective_entry_fee
                    quote_balance += sell_notional - entry_fee
                    # base_balance already reduced at placement
                    pos = Position(
                        side="sell",
                        entry_price=order.price,
                        amount=order.amount,
                        entry_quote=sell_notional,
                        entry_time=ts,
                        entry_fee_paid=entry_fee,
                    )
                    positions.append(pos)
                    n_open += 1
                    filled = True

                if not filled:
                    remaining_orders.append(order)

            pending_orders = remaining_orders

            # ── STEP 3: Place new orders (if signals valid AND refresh elapsed) ──
            cooldown_ok = cfg.cooldown_seconds <= 0 or (ts - last_close_time) >= cfg.cooldown_seconds
            signals_valid = not (pd.isna(natr_val) or pd.isna(price_signal) or natr_val == 0)
            if cooldown_ok and signals_valid and (ts - last_refresh_time) >= cfg.executor_refresh_seconds:
                # Cancel all pending orders, return reserved capital
                for order in pending_orders:
                    if order.side == "buy":
                        quote_balance += order.quote_reserved
                    elif order.side == "sell":
                        base_balance += order.base_reserved  # FIX-3: refund reserved base
                pending_orders = []

                # Compute dynamic levels (production formula)
                max_price_shift = natr_val / 2.0  # Production: natr/2
                price_signal_val = price_signal if not pd.isna(price_signal) else 0.0
                price_multiplier = price_signal_val * max_price_shift
                reference_price = mid_price * (1 + price_multiplier)
                spread_multiplier = natr_val  # Production: spread_multiplier IS natr

                n_buy = len(cfg.buy_spreads)
                n_sell = len(cfg.sell_spreads)
                buy_pcts = cfg.buy_amounts_pct if len(cfg.buy_amounts_pct) == n_buy else [100.0 / n_buy] * n_buy
                sell_pcts = cfg.sell_amounts_pct if len(cfg.sell_amounts_pct) == n_sell else [100.0 / n_sell] * n_sell

                # Realism: compounding control
                sizing_equity = (quote_balance + base_balance * mid_price) if cfg.compounding else initial_capital
                available_quote = sizing_equity * cfg.deploy_fraction

                # FIX-1 V3: For order PLACEMENT, count positions + pending, use >= threshold.
                # This prevents placing new orders when we're already at capacity including pending.
                n_open = len(positions) + len(pending_orders)

                # Place buy orders (pending — fillable next candle)
                for lvl_idx, base_spread in enumerate(cfg.buy_spreads):
                    if cfg.max_open_positions > 0 and n_open >= cfg.max_open_positions:
                        break

                    spread_adj = base_spread * spread_multiplier
                    # BUG-5 FIX: Spread floor only when enforce_spread_floor=True
                    if cfg.enforce_spread_floor:
                        min_spread = max(cfg.entry_fee + cfg.exit_fee + cfg.slippage_max_pct, cfg.min_spread_floor)
                        spread_adj = max(spread_adj, min_spread)
                    order_price = reference_price * (1 - spread_adj)

                    alloc_pct = buy_pcts[lvl_idx] / 100.0
                    order_quote = available_quote * alloc_pct

                    # Realism: cap order size
                    if cfg.max_order_quote > 0:
                        order_quote = min(order_quote, cfg.max_order_quote)

                    if order_quote < 1.0:
                        continue

                    # Can't spend more than we have
                    order_quote = min(order_quote, quote_balance * 0.95)
                    if order_quote < 1.0:
                        continue

                    # Realism: slippage (adverse price movement)
                    if cfg.slippage_max_pct > 0:
                        slip = cfg.slippage_max_pct / 2.0  # deterministic avg, matches GPU
                        order_price = reference_price * (1 - spread_adj) * (1 + slip)

                    # BUG-5 FIX: Non-crossing guard only when enforce_nc_guard=True
                    if cfg.enforce_nc_guard:
                        nc_floor = max(cfg.entry_fee + cfg.exit_fee + cfg.slippage_max_pct, cfg.min_spread_floor)
                        order_price = min(order_price, mid_price * (1.0 - nc_floor))
                    if order_price <= 0:
                        continue

                    amount = order_quote / order_price

                    # Reserve capital: quote_balance reduced on placement
                    quote_balance -= order_quote
                    pending_orders.append(PendingOrder(
                        side="buy",
                        price=order_price,
                        amount=amount,
                        quote_reserved=order_quote,
                        placed_ts=ts,
                        expires_ts=ts + cfg.executor_refresh_seconds,
                    ))
                    n_open += 1

                # Place sell orders (pending — fillable next candle)
                for lvl_idx, base_spread in enumerate(cfg.sell_spreads):
                    if cfg.max_open_positions > 0 and n_open >= cfg.max_open_positions:
                        break

                    spread_adj = base_spread * spread_multiplier
                    # BUG-5 FIX: Spread floor only when enforce_spread_floor=True
                    if cfg.enforce_spread_floor:
                        min_spread = max(cfg.entry_fee + cfg.exit_fee + cfg.slippage_max_pct, cfg.min_spread_floor)
                        spread_adj = max(spread_adj, min_spread)
                    order_price = reference_price * (1 + spread_adj)

                    alloc_pct = sell_pcts[lvl_idx] / 100.0
                    order_quote = available_quote * alloc_pct

                    # Realism: cap order size
                    if cfg.max_order_quote > 0:
                        order_quote = min(order_quote, cfg.max_order_quote)

                    if order_quote < 1.0:
                        continue

                    # Realism: slippage (adverse)
                    if cfg.slippage_max_pct > 0:
                        slip = cfg.slippage_max_pct / 2.0  # deterministic avg, matches GPU
                        order_price = reference_price * (1 + spread_adj) * (1 - slip)

                    # BUG-5 FIX: Non-crossing guard only when enforce_nc_guard=True
                    if cfg.enforce_nc_guard:
                        nc_floor = max(cfg.entry_fee + cfg.exit_fee + cfg.slippage_max_pct, cfg.min_spread_floor)
                        order_price = max(order_price, mid_price * (1.0 + nc_floor))

                    sell_amount_base = order_quote / order_price

                    # BUG-3 FIX: base_balance already reflects reservations from prior sells
                    available_base = base_balance
                    if available_base < sell_amount_base * 0.999:
                        # Not enough base — skip this sell level
                        continue
                    # Reserve the base
                    base_balance -= sell_amount_base
                    pending_orders.append(PendingOrder(
                        side="sell",
                        price=order_price,
                        amount=sell_amount_base,
                        quote_reserved=0.0,
                        base_reserved=sell_amount_base,
                        placed_ts=ts,
                        expires_ts=ts + cfg.executor_refresh_seconds,
                    ))
                    n_open += 1

                last_refresh_time = ts

            # ── STEP 4: Mark-to-market equity (ALWAYS) ──
            reserved_quote = sum(o.quote_reserved for o in pending_orders if o.side == "buy")
            reserved_base = sum(o.base_reserved for o in pending_orders if o.side == "sell")
            equity = (quote_balance + reserved_quote) + (base_balance + reserved_base) * mid_price
            equity_curve.append(equity)

            # Drawdown
            peak_equity = max(peak_equity, equity)
            dd = (peak_equity - equity) / peak_equity if peak_equity > 0 else 0
            max_drawdown = max(max_drawdown, dd)

        # Cancel remaining pending orders, return reserved capital
        for order in pending_orders:
            if order.side == "buy":
                quote_balance += order.quote_reserved
            elif order.side == "sell":
                base_balance += order.base_reserved  # FIX-3: refund reserved base
        pending_orders = []

        # Close any remaining open positions at last price
        if len(df) > 0:
            last_price = df.iloc[-1]["close"]
            last_ts = df.iloc[-1]["timestamp"].timestamp() if hasattr(df.iloc[-1]["timestamp"], "timestamp") else 0
            for pos in positions:
                if not pos.closed:
                    # FIX-5: end_of_data is MARKET order → taker fee
                    _close_position(pos, last_price, last_ts, "end_of_data", exit_fee_rate=cfg.taker_fee)
                    if pos.side == "buy":
                        exit_notional = pos.amount * pos.exit_price
                        exit_fee = pos.exit_fee_paid
                        quote_balance += exit_notional - exit_fee
                        base_balance -= pos.amount
                    else:
                        exit_notional = pos.amount * pos.exit_price
                        exit_fee = pos.exit_fee_paid
                        quote_balance -= exit_notional + exit_fee
                        base_balance += pos.amount
                    closed_positions.append(pos)

        final_balance = quote_balance + base_balance * (df.iloc[-1]["close"] if len(df) > 0 else 0)

        return BacktestResult.compute(
            initial_capital=initial_capital,
            final_balance=final_balance,
            equity_curve=equity_curve,
            closed_positions=closed_positions,
            max_drawdown=max_drawdown,
            candle_seconds=candle_seconds,
        )

    def _check_exit(
        self, pos: Position, high: float, low: float, close: float, ts: float, cfg: PMMDynamicConfig
    ):
        """Check triple-barrier exit conditions with slippage on fills."""
        # Update peak PnL from intrabar extremes (Fix 4)
        best_intrabar = high if pos.side == "buy" else low
        intrabar_best_pnl = _position_pnl_pct(pos, best_intrabar)
        if intrabar_best_pnl > pos.peak_pnl_pct:
            pos.peak_pnl_pct = intrabar_best_pnl

        # Trailing stop activation from intrabar extremes
        if not pos.trailing_active and intrabar_best_pnl >= cfg.trailing_stop_activation:
            pos.trailing_active = True

        # Helper: apply adverse slippage to exit price
        def _slipped_exit(base_price: float, side: str) -> float:
            if cfg.slippage_max_pct <= 0:
                return base_price
            slip = cfg.slippage_max_pct / 2.0  # deterministic avg, matches GPU
            if side == "buy":
                return base_price * (1 - slip)
            else:
                return base_price * (1 + slip)

        # ── Inner exit checks ──
        def _check_stop_loss() -> bool:
            worst_price = low if pos.side == "buy" else high
            worst_pnl = _position_pnl_pct(pos, worst_price)
            if worst_pnl <= -cfg.stop_loss:
                exit_price = pos.entry_price * (1 - cfg.stop_loss) if pos.side == "buy" else pos.entry_price * (1 + cfg.stop_loss)
                exit_price = _slipped_exit(exit_price, pos.side)
                # FIX-5: SL is MARKET order → taker fee
                _close_position(pos, exit_price, ts, "stop_loss", exit_fee_rate=cfg.taker_fee)
                return True
            return False

        def _check_take_profit() -> bool:
            best_price = high if pos.side == "buy" else low
            best_pnl = _position_pnl_pct(pos, best_price)
            if best_pnl >= cfg.take_profit:
                exit_price = pos.entry_price * (1 + cfg.take_profit) if pos.side == "buy" else pos.entry_price * (1 - cfg.take_profit)
                # ADD-3: TP is a LIMIT order — NO slippage
                # FIX-5: TP is LIMIT order → maker fee
                _close_position(pos, exit_price, ts, "take_profit", exit_fee_rate=cfg.maker_fee)
                return True
            return False

        # ── Configurable intrabar exit priority (Fix 6) ──
        if cfg.intrabar_exit_mode == "worst_case":
            if _check_stop_loss():
                return
            if _check_take_profit():
                return
        else:
            if _check_take_profit():
                return
            if _check_stop_loss():
                return

        # ── Trailing stop (uses trail_price, not close) ──
        if pos.trailing_active:
            pnl_pct = _position_pnl_pct(pos, close)
            drawback = pos.peak_pnl_pct - pnl_pct
            if drawback >= cfg.trailing_stop_delta:
                if pos.side == "buy":
                    trail_price = pos.entry_price * (1 + pos.peak_pnl_pct - cfg.trailing_stop_delta)
                else:
                    trail_price = pos.entry_price * (1 - pos.peak_pnl_pct + cfg.trailing_stop_delta)
                trail_price = _slipped_exit(trail_price, pos.side)
                # FIX-5: Trailing stop is MARKET order → taker fee
                _close_position(pos, trail_price, ts, "trailing_stop", exit_fee_rate=cfg.taker_fee)
                return

        # ── Time limit ──
        if cfg.time_limit_seconds > 0 and (ts - pos.entry_time) >= cfg.time_limit_seconds:
            exit_price = _slipped_exit(close, pos.side)
            # FIX-5: Time limit is MARKET order → taker fee
            _close_position(pos, exit_price, ts, "time_limit", exit_fee_rate=cfg.taker_fee)
            return


# ---------------------------------------------------------------------------
# Optuna objective function
# ---------------------------------------------------------------------------

def create_objective(
    candles: pd.DataFrame,
    connector: str = "nonkyc",
    trading_pair: str = "BTC/USDT",
    interval: str = "5m",
    total_amount_quote: float = 1000.0,
    leverage: int = 1,
    n_levels: int = 2,
    optimize_metric: str = "sharpe_ratio",
    max_drawdown_constraint: float = 0.15,
    optimize_n_levels: bool = False,
    min_levels: int = 1,
    max_levels: int = 10,
    spread_min: float = 0.5,      # 0.5x NATR
    spread_max: float = 8.0,      # 8x NATR
    spread_step: float = 0.1,     # 0.1x steps
    optimize_amounts: bool = True,
    # ── Realism controls (passed through to backtester) ──
    compounding: bool = False,
    max_order_quote: float = 0.0,
    slippage_max_pct: float = 0.001,
    fill_rate_pct: float = 0.0,
    max_open_positions: int = 0,
    deploy_fraction: float = 0.5,
    maker_fee: float = 0.001,
    taker_fee: float = 0.002,
    entry_fee_type: str = "maker",
    exit_fee_type: str = "taker",
    intrabar_exit_mode: str = "worst_case",
    # ── Quality gates ──
    min_trades: int = 50,
    max_trades_per_day: float = 20.0,
    turnover_penalty_weight: float = 0.1,
    # ── Multi-seed robustness ──
    n_eval_seeds: int = 1,
    # ── Auto spread floor ──
    auto_spread_floor: bool = True,
    # ── Candle semantics (V3) ──
    timestamp_mode: str = "unknown",
    volume_units: str = "base",
    # ── BUG-5: Spread floor mode ──
    enforce_spread_floor: bool = False,
    enforce_nc_guard: bool = False,
    # ── ADD-2: Cooldown mode ──
    cooldown_on_stop_loss_only: bool = True,
    # ── OBJ-1: Enhanced objective (reviewer's formula) ──
    use_enhanced: bool = False,
    # ── Walk-forward integration (FIX-6) ──
    use_walk_forward: bool = False,
    wf_n_windows: int = 5,
    wf_train_pct: float = 0.70,
    wf_min_profitable: int = 3,
    wf_min_median_sharpe: float = 0.5,
    wf_max_degradation: float = 0.5,
):
    """
    Returns an Optuna objective function that backtests PMM Dynamic
    with trial-suggested parameters.

    Parameters
    ----------
    candles : Pre-loaded candle DataFrame
    optimize_metric : "sharpe_ratio", "net_pnl_pct", or "profit_factor"
    max_drawdown_constraint : Penalize trials exceeding this drawdown
    optimize_n_levels : If True, Optuna also searches over the number of levels
    min_levels / max_levels : Bounds for n_levels search (only when optimize_n_levels=True)
    spread_min / spread_max : Global bounds for spread search space (volatility multipliers)
    spread_step : Step size for spread suggestions
    optimize_amounts : If True, optimize per-level amount allocation; else equal split
    compounding : If False, order sizes stay fixed to initial capital (no snowball)
    max_order_quote : Cap each individual order to this many quote units (0 = unlimited)
    slippage_max_pct : Max random adverse slippage per fill (e.g. 0.002 = 0.2%)
    fill_rate_pct : Volume-based fill model — order fills if order_quote <= candle_vol * pct (0 = off)
    max_open_positions : Max simultaneous positions (0 = unlimited)
    deploy_fraction : Fraction of capital deployed per refresh cycle (0.0-1.0)
    maker_fee : Maker fee as decimal (e.g. 0.001 = 0.1%)
    taker_fee : Taker fee as decimal (e.g. 0.002 = 0.2%)
    entry_fee_type : "maker" or "taker" for entry fills
    exit_fee_type : "maker" or "taker" for exit fills
    intrabar_exit_mode : "worst_case" (SL first) or "best_case" (TP first)
    max_trades_per_day : If > 0, penalize strategies exceeding this trades/day rate
    turnover_penalty_weight : Scaling factor for the turnover penalty
    n_eval_seeds : Number of evaluation passes with jittered capital (robustness)
    auto_spread_floor : If True, dynamically compute spread_min from fees
    """
    # ── Recommended settings for NonKYC.io live deployment ──
    # maker_fee = 0.001, taker_fee = 0.002, slippage_max_pct = 0.001
    # fill_rate_pct = 0.05, max_open_positions = 4, deploy_fraction = 0.4
    # max_trades_per_day = 20, turnover_penalty_weight = 0.1, n_eval_seeds = 3

    # BUG-1C: Auto spread floor from fees — uses shared helper
    if auto_spread_floor:
        entry_fee_val = maker_fee if entry_fee_type == "maker" else taker_fee
        exit_fee_val  = maker_fee if exit_fee_type  == "maker" else taker_fee
        min_mult = _auto_spread_min_multiplier(
            candles, entry_fee_val, exit_fee_val, slippage_max_pct
        )
        spread_min = max(spread_min, min_mult)

    def objective(trial) -> float:
        # Use the module-level _suggest_params (single source of truth)
        suggested = _suggest_params(
            trial, n_levels, spread_min, spread_max, spread_step,
            optimize_n_levels, min_levels, max_levels, optimize_amounts,
        )
        p = trial.params
        actual_levels = suggested["n_levels"]

        # Reconstruct spread/amount lists from trial params
        buy_spreads = [p[f"spread_level_{lvl + 1}"] for lvl in range(actual_levels)
                       if f"spread_level_{lvl + 1}" in p]
        sell_spreads = buy_spreads[:]

        has_weights = any(k.startswith("amount_weight_") for k in p)
        if has_weights:
            raw_weights = [p.get(f"amount_weight_{lvl + 1}", 1.0) for lvl in range(actual_levels)]
            total_weight = sum(raw_weights)
            buy_amounts_pct = [round(w / total_weight * 100, 2) for w in raw_weights]
            sell_amounts_pct = buy_amounts_pct[:]
        else:
            equal_pct = round(100.0 / actual_levels, 2)
            buy_amounts_pct = [equal_pct] * actual_levels
            sell_amounts_pct = [equal_pct] * actual_levels

        # ── Build config ──
        cfg = PMMDynamicConfig(
            connector=connector,
            trading_pair=trading_pair,
            candles_connector=connector,
            candles_pair=trading_pair,
            interval=interval,
            total_amount_quote=total_amount_quote,
            leverage=leverage,
            macd_fast=p["macd_fast"],
            macd_slow=p["macd_slow"],
            macd_signal=p["macd_signal"],
            natr_length=p["natr_length"],
            buy_spreads=buy_spreads,
            sell_spreads=sell_spreads,
            buy_amounts_pct=buy_amounts_pct,
            sell_amounts_pct=sell_amounts_pct,
            stop_loss=p["stop_loss"],
            take_profit=p["take_profit"],
            time_limit_seconds=p["time_limit_minutes"] * 60,
            trailing_stop_activation=p["trailing_activation"],
            trailing_stop_delta=p["trailing_delta"],
            executor_refresh_seconds=p["refresh_minutes"] * 60,
            maker_fee=maker_fee,
            taker_fee=taker_fee,
            entry_fee_type=entry_fee_type,
            exit_fee_type=exit_fee_type,
            intrabar_exit_mode=intrabar_exit_mode,
            # Realism controls
            compounding=compounding,
            max_order_quote=max_order_quote,
            slippage_max_pct=slippage_max_pct,
            fill_rate_pct=fill_rate_pct,
            max_open_positions=max_open_positions,
            deploy_fraction=deploy_fraction,
            timestamp_mode=timestamp_mode,
            volume_units=volume_units,
            enforce_spread_floor=enforce_spread_floor,
            enforce_nc_guard=enforce_nc_guard,
            cooldown_on_stop_loss_only=cooldown_on_stop_loss_only,
        )

        # ── Run backtest (with optional multi-seed robustness) ──
        if n_eval_seeds > 1:
            import statistics
            results = []
            for seed_i in range(n_eval_seeds):
                jitter = 1.0 + (seed_i - n_eval_seeds // 2) * 0.01
                jittered_cfg = replace(cfg, total_amount_quote=cfg.total_amount_quote * jitter)
                try:
                    results.append(PMMDynamicBacktester(jittered_cfg).run(candles))
                except Exception as e:
                    log.warning("Backtest seed %d failed: %s", seed_i, e)
                    return -10.0
            # Use median Sharpe for robustness
            sharpe_values = [r.sharpe_ratio for r in results]
            median_idx = sorted(range(len(sharpe_values)), key=lambda k: sharpe_values[k])[len(sharpe_values) // 2]
            result = results[median_idx]
        else:
            try:
                bt = PMMDynamicBacktester(cfg)
                result = bt.run(candles)
            except Exception as e:
                log.warning("Backtest failed: %s", e)
                return -10.0

        # Compute gross_profit and gross_loss for _compute_objective
        gross_profit = sum(t["pnl_quote"] for t in result.trades if t["pnl_quote"] > 0)
        gross_loss_val = abs(sum(t["pnl_quote"] for t in result.trades if t["pnl_quote"] < 0))
        candle_seconds = _interval_to_seconds(interval)

        # ── FIX-6: Walk-forward gate (CPU-only extension) ──
        if use_walk_forward:
            wf = walk_forward_evaluate(
                candles, cfg,
                n_windows=wf_n_windows,
                train_pct=wf_train_pct,
            )
            # Walk-forward gates
            if wf["n_profitable_windows"] < wf_min_profitable:
                return -10.0
            if wf["median_test_sharpe"] < wf_min_median_sharpe:
                return -10.0
            if wf["train_test_degradation"] > wf_max_degradation:
                return -8.0   # penalized but not completely rejected
            # Use median test Sharpe as the objective when walk-forward passes
            return wf["median_test_sharpe"]

        # BUG-2 V3: Single-seed, non-walk-forward path — MUST match GPU via _compute_objective
        return _compute_objective(
            {
                "sharpe": result.sharpe_ratio,
                "pnl_pct": result.net_pnl_pct,
                "max_dd": result.max_drawdown,
                "n_trades": result.total_trades,
                "gross_win": gross_profit,
                "gross_loss": gross_loss_val,
            },
            optimize_metric, max_drawdown_constraint,
            min_trades, max_trades_per_day, turnover_penalty_weight,
            candle_seconds=candle_seconds, n_candles=len(candles),
            use_enhanced=use_enhanced,
        )

    return objective


# ---------------------------------------------------------------------------
# Ensure `random` is available for PMMDynamicBacktester.__init__
# ---------------------------------------------------------------------------
import random
