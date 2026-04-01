"""
Generic candle-based simulation engine.

Handles: fills, triple-barrier exits, inventory, equity tracking, order lifecycle.
Does NOT handle: signal computation, order construction — those come from the Strategy.

INTRABAR ORDERING ASSUMPTION:
The engine processes each bar's extremes in a fixed priority order:
  1. Stop-loss check (uses low for buys, high for sells)
  2. Trailing stop: peak update then trigger check (same bar)
  3. Take-profit check
  4. Time-limit check

Because OHLC bars do not reveal intrabar path ordering, this is a
modeling choice. The trailing stop can update its peak AND trigger
on the same bar if both conditions are met. This is the "aggressive"
model — it may overcount trailing stop exits on high-volatility bars.

For conservative trailing-stop evaluation, use sub-bar data or disable
same-bar activation-and-trigger (not currently implemented).
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
        """Check triple barrier conditions for an open trade.

        Returns (exit_price, exit_type) or None if no exit triggered.
        Priority: stop_loss > trailing_stop > take_profit > time_limit.
        """
        cfg = self.config
        entry = trade.entry_price

        if trade.side == "buy":
            # Stop loss: price drops below entry * (1 - stop_loss)
            sl_price = entry * (1.0 - cfg.stop_loss)
            if candle_low <= sl_price:
                exit_p = compute_slippage(sl_price, cfg.slippage_bps, "buy")
                return exit_p, "stop_loss"

            # Trailing stop
            if cfg.trailing_stop_activation > 0 and cfg.trailing_stop_delta > 0:
                # Update peak
                if trade.peak_price is None:
                    trade.peak_price = candle_high
                else:
                    trade.peak_price = max(trade.peak_price, candle_high)

                activation_price = entry * (1.0 + cfg.trailing_stop_activation)
                if trade.peak_price >= activation_price:
                    trade.trailing_activated = True
                    trail_trigger = trade.peak_price * (1.0 - cfg.trailing_stop_delta)
                    if candle_low <= trail_trigger:
                        exit_p = compute_slippage(trail_trigger, cfg.slippage_bps, "buy")
                        return exit_p, "trailing_stop"

            # Take profit: price rises above entry * (1 + take_profit)
            tp_price = entry * (1.0 + cfg.take_profit)
            tp_triggered = candle_high > tp_price if cfg.touch_through else candle_high >= tp_price
            if tp_triggered:
                if cfg.take_profit_order_type == "MARKET":
                    exit_p = compute_slippage(tp_price, cfg.slippage_bps, "buy")
                else:
                    exit_p = tp_price  # LIMIT — no slippage
                return exit_p, "take_profit"

            # Time limit
            if current_ts - trade.entry_timestamp >= cfg.time_limit:
                exit_p = compute_slippage(candle_close, cfg.slippage_bps, "buy")
                return exit_p, "time_limit"

        else:  # sell trade
            # Stop loss: price rises above entry * (1 + stop_loss)
            sl_price = entry * (1.0 + cfg.stop_loss)
            if candle_high >= sl_price:
                exit_p = compute_slippage(sl_price, cfg.slippage_bps, "sell")
                return exit_p, "stop_loss"

            # Trailing stop for sell: track low, activate when price drops enough
            if cfg.trailing_stop_activation > 0 and cfg.trailing_stop_delta > 0:
                if trade.peak_price is None:
                    trade.peak_price = candle_low
                else:
                    trade.peak_price = min(trade.peak_price, candle_low)

                activation_price = entry * (1.0 - cfg.trailing_stop_activation)
                if trade.peak_price <= activation_price:
                    trade.trailing_activated = True
                    trail_trigger = trade.peak_price * (1.0 + cfg.trailing_stop_delta)
                    if candle_high >= trail_trigger:
                        exit_p = compute_slippage(trail_trigger, cfg.slippage_bps, "sell")
                        return exit_p, "trailing_stop"

            # Take profit: price drops below entry * (1 - take_profit)
            tp_price = entry * (1.0 - cfg.take_profit)
            tp_triggered = candle_low < tp_price if cfg.touch_through else candle_low <= tp_price
            if tp_triggered:
                if cfg.take_profit_order_type == "MARKET":
                    exit_p = compute_slippage(tp_price, cfg.slippage_bps, "sell")
                else:
                    exit_p = tp_price
                return exit_p, "take_profit"

            # Time limit
            if current_ts - trade.entry_timestamp >= cfg.time_limit:
                exit_p = compute_slippage(candle_close, cfg.slippage_bps, "sell")
                return exit_p, "time_limit"

        return None

    def _compute_required_base(
        self,
        strategy: Strategy,
        bar_idx: int,
        signals: SignalOutput,
        inventory: Inventory,
    ) -> float:
        """Compute the base amount required to fully fund the sell ladder.

        Builds a hypothetical order set and sums the sell-side quantities.
        This tells us how much base inventory is needed for sells.
        """
        # Build hypothetical orders with infinite base to see what the strategy wants
        temp_inventory = inventory.copy()
        temp_inventory.enforce_spot_constraints = False  # don't clamp to available base
        orders, _, _ = strategy.build_orders(
            bar_idx, signals, self.config, self.pair_rules, temp_inventory
        )
        required_base = sum(o.quantity for o in orders if o.side == "sell")
        return required_base

    def _execute_rebalance(
        self,
        bar_idx: int,
        signals: SignalOutput,
        strategy: Strategy,
        inventory: Inventory,
        current_price: float,
    ) -> tuple:
        """Check and execute position rebalance if needed.

        Returns (rebalance_quantity, rebalance_fee) — both 0 if no rebalance.
        """
        cfg = self.config
        rules = self.pair_rules

        if cfg.skip_rebalance or cfg.position_rebalance_threshold_pct <= 0:
            return 0.0, 0.0

        required_base = self._compute_required_base(
            strategy, bar_idx, signals, inventory
        )

        if required_base <= 0:
            return 0.0, 0.0

        current_base = inventory.base_balance
        deficit = required_base - current_base

        # Check if deficit exceeds threshold
        deficit_pct = abs(deficit) / required_base if required_base > 0 else 0.0
        if deficit_pct <= cfg.position_rebalance_threshold_pct:
            return 0.0, 0.0

        if deficit > 0:
            # Need to BUY base — market buy with taker fees + slippage
            buy_price = compute_slippage(current_price, cfg.slippage_bps, "sell")
            # "sell" side slippage = price goes up (adverse for buyer)
            buy_qty = deficit
            fee = compute_fee(buy_price, buy_qty, rules.fees, "taker")
            cost = buy_qty * buy_price + fee

            # Clamp to available quote
            available = inventory.available_quote_for_buy()
            if cost > available:
                buy_qty = inventory.max_buy_quantity(buy_price, rules.fees.taker_fee)
                buy_qty = round_amount(buy_qty, rules)
                if buy_qty <= 0:
                    return 0.0, 0.0
                fee = compute_fee(buy_price, buy_qty, rules.fees, "taker")

            executed = inventory.buy(buy_qty, buy_price, fee)
            if executed:
                return buy_qty, fee
            return 0.0, 0.0

        else:
            # Surplus base — sell some back (rare but complete)
            sell_qty = abs(deficit)
            sell_price = compute_slippage(current_price, cfg.slippage_bps, "buy")
            # "buy" side slippage = price goes down (adverse for seller)
            sell_qty = min(sell_qty, inventory.available_base_for_sell())
            if sell_qty <= 0:
                return 0.0, 0.0
            fee = compute_fee(sell_price, sell_qty, rules.fees, "taker")
            executed = inventory.sell(sell_qty, sell_price, fee)
            if executed:
                return -sell_qty, fee  # negative = sold
            return 0.0, 0.0

    def run(
        self,
        candles: np.ndarray,
        strategy: Strategy,
        sim_start_idx: Optional[int] = None,
        bar_index_offset: int = 0,
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
        bar_index_offset : int
            Offset added to bar indices in trade metadata. Defaults to 0.

        Returns
        -------
        SimResult
        """
        signals = strategy.compute_signals(candles)
        return self.run_with_signals(
            candles, strategy, signals, sim_start_idx, bar_index_offset=bar_index_offset
        )

    def run_with_signals(
        self,
        candles: np.ndarray,
        strategy: Strategy,
        precomputed_signals: SignalOutput,
        sim_start_idx: Optional[int] = None,
        bar_index_offset: int = 0,
    ) -> SimResult:
        """Run a backtest using pre-computed signals (skips signal computation).

        This is identical to run() except it uses precomputed_signals instead of
        calling strategy.compute_signals(candles). Use this when running the same
        strategy config across multiple candle slices (walk-forward folds) or
        stress scenarios where signals don't change.

        IMPORTANT: precomputed_signals must have been computed on a candle array
        that is >= len(candles). Signal arrays are indexed by bar position, so
        signals[0:len(candles)] are used.

        Parameters
        ----------
        candles : np.ndarray
            Canonical structured candle array (may be a slice of the full array).
        strategy : Strategy
            Strategy implementation (used for build_orders only, NOT compute_signals).
        precomputed_signals : SignalOutput
            Pre-computed signals from strategy.compute_signals() on the full candle array.
        sim_start_idx : int, optional
            Bar index where simulation starts.

        Returns
        -------
        SimResult
        """
        cfg = self.config
        rules = self.pair_rules
        n = len(candles)
        self._warned_no_orders = False

        signals = precomputed_signals
        warmup_end = signals.warmup_end

        loop_start = max(warmup_end, sim_start_idx) if sim_start_idx is not None else warmup_end

        # 2. Initialize inventory and tracking arrays
        inventory = Inventory(base_balance=0.0, quote_balance=cfg.total_amount_quote)
        equity_curve = np.zeros(n, dtype="float64")
        position_history = np.zeros(n, dtype="float64")

        # Pre-bind structured array fields to avoid repeated lookup overhead
        _ts_arr = candles["timestamp"]
        _open_arr = candles["open"]
        _high_arr = candles["high"]
        _low_arr = candles["low"]
        _close_arr = candles["close"]
        _vol_arr = candles["volume"]

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
        n_rebalance_events = 0
        total_rebalance_fees = 0.0

        # Initial base allocation (pre-buys base at market open)
        initial_rebal_fee = 0.0
        if cfg.initial_base_pct > 0 and n > 0:
            open_price = float(_close_arr[min(loop_start, n - 1)])
            initial_quote = cfg.initial_base_pct * cfg.total_amount_quote
            initial_buy_price = compute_slippage(open_price, cfg.slippage_bps, "sell")
            initial_qty = initial_quote / initial_buy_price if initial_buy_price > 0 else 0.0
            initial_qty = round_amount(initial_qty, rules)
            if initial_qty > 0:
                initial_rebal_fee = compute_fee(initial_buy_price, initial_qty, rules.fees, "taker")
                inventory.buy(initial_qty, initial_buy_price, initial_rebal_fee)
                total_rebalance_fees += initial_rebal_fee
                n_rebalance_events += 1

        # Fill pre-loop bars with initial equity
        for i in range(min(loop_start, n)):
            equity_curve[i] = inventory.equity(float(_close_arr[i]))
            position_history[i] = inventory.base_balance

        # 3. Main simulation loop
        for bar in range(loop_start, n):
            abs_bar = bar + bar_index_offset
            ts = int(_ts_arr[bar])
            c_open = float(_open_arr[bar])
            c_high = float(_high_arr[bar])
            c_low = float(_low_arr[bar])
            c_close = float(_close_arr[bar])
            c_volume = float(_vol_arr[bar])

            # Skip bar if signals are not valid
            if not signals.is_valid(bar):
                equity_curve[bar] = inventory.equity(c_close)
                position_history[bar] = inventory.base_balance
                continue

            # a. Check triple barrier exits on all open trades
            closed_trade_ids = set()
            for trade in open_trades:
                result = self._check_triple_barrier(
                    trade, bar, c_high, c_low, c_close, ts
                )
                if result is not None:
                    exit_price, exit_type = result
                    trade.exit_price = exit_price
                    trade.exit_bar = abs_bar
                    trade.exit_timestamp = ts
                    trade.exit_type = exit_type

                    # Determine fee type
                    if exit_type == "take_profit" and cfg.take_profit_order_type == "LIMIT":
                        fee_type = "maker"
                    else:
                        fee_type = "taker"

                    exit_fee = compute_fee(exit_price, trade.quantity, rules.fees, fee_type)

                    # Execute the exit
                    if trade.side == "buy":
                        # Closing a buy = selling base
                        available = inventory.available_base_for_sell()
                        close_qty = min(trade.quantity, available)
                        if close_qty <= 0:
                            continue  # cannot close, skip
                        exit_fee = compute_fee(exit_price, close_qty, rules.fees, fee_type)
                        inventory.sell(close_qty, exit_price, exit_fee)
                        trade.pnl_quote = (exit_price - trade.entry_price) * close_qty - trade.fee_quote - exit_fee
                    else:
                        # Closing a sell = buying base back
                        close_qty = trade.quantity
                        cost = close_qty * exit_price + exit_fee
                        if inventory.available_quote_for_buy() < cost:
                            max_affordable = inventory.max_buy_quantity(exit_price, rules.fees.taker_fee)
                            close_qty = round_amount(max_affordable, rules)
                            if close_qty <= 0:
                                continue
                            # If we can't fully close, keep trade open entirely
                            if close_qty < trade.quantity:
                                continue
                            exit_fee = compute_fee(exit_price, close_qty, rules.fees, fee_type)
                        executed = inventory.buy(close_qty, exit_price, exit_fee)
                        if not executed:
                            continue
                        trade.pnl_quote = (trade.entry_price - exit_price) * close_qty - trade.fee_quote - exit_fee

                    trade.exit_fee_quote = exit_fee
                    trade.exit_fee_type = fee_type
                    trade.fee_quote += exit_fee
                    closed_trade_ids.add(trade.trade_id)

                    if exit_type in ("stop_loss", "time_limit", "trailing_stop"):
                        n_market_exits += 1

                    last_fill_ts = ts

            open_trades = [t for t in open_trades if t.trade_id not in closed_trade_ids]

            # b. Check fills on active orders — per-side or shared capacity
            # Volume conversion
            effective_volume = c_volume
            if not cfg.volume_is_base and c_close > 0:
                effective_volume = c_volume / c_close  # convert quote volume to base

            # Per-side or shared capacity
            if cfg.split_volume_by_side:
                buy_bar_capacity = cfg.fill_participation_rate * effective_volume * cfg.buy_volume_fraction
                sell_bar_capacity = cfg.fill_participation_rate * effective_volume * (1.0 - cfg.buy_volume_fraction)
            else:
                buy_bar_capacity = cfg.fill_participation_rate * effective_volume
                sell_bar_capacity = buy_bar_capacity  # shared pool — tracked as one

            remaining_orders = []
            for order in active_orders:
                if not is_order_active(bar, order.placed_bar, cfg.latency_bars):
                    remaining_orders.append(order)
                    continue

                # Select capacity pool
                if order.side == "buy":
                    current_capacity = buy_bar_capacity
                else:
                    current_capacity = sell_bar_capacity

                if current_capacity <= 0:
                    remaining_orders.append(order)
                    continue

                if order.side == "buy":
                    fill = check_buy_fill(
                        order.price, order.remaining_quantity,
                        c_low, effective_volume, cfg.fill_participation_rate,
                        remaining_capacity=current_capacity,
                        touch_through=cfg.touch_through,
                        entry_spread_bps=cfg.entry_spread_bps,
                        maker_fill_probability=cfg.maker_fill_probability,
                        fill_seed=abs_bar * 1000 + order.level,
                    )
                else:
                    fill = check_sell_fill(
                        order.price, order.remaining_quantity,
                        c_high, effective_volume, cfg.fill_participation_rate,
                        remaining_capacity=current_capacity,
                        touch_through=cfg.touch_through,
                        entry_spread_bps=cfg.entry_spread_bps,
                        maker_fill_probability=cfg.maker_fill_probability,
                        fill_seed=abs_bar * 1000 + order.level,
                    )

                if fill.filled:
                    actual_qty = fill.fill_quantity

                    if order.side == "buy":
                        # Check if we can afford this buy (spot constraint)
                        entry_fee = compute_fee(fill.fill_price, actual_qty, rules.fees, "maker")
                        cost = actual_qty * fill.fill_price + entry_fee
                        available_quote = inventory.available_quote_for_buy()
                        if available_quote < cost:
                            # Reduce quantity to what we can afford
                            max_affordable = inventory.max_buy_quantity(
                                fill.fill_price, rules.fees.maker_fee
                            )
                            actual_qty = round_amount(max_affordable, rules)
                            if actual_qty <= 0:
                                remaining_orders.append(order)
                                continue
                            entry_fee = compute_fee(fill.fill_price, actual_qty, rules.fees, "maker")
                        executed = inventory.buy(actual_qty, fill.fill_price, entry_fee)
                        if not executed:
                            remaining_orders.append(order)
                            continue
                    else:
                        # Clamp sell quantity to available base (spot constraint)
                        available = inventory.available_base_for_sell()
                        actual_qty = min(fill.fill_quantity, available)
                        if actual_qty <= 0:
                            remaining_orders.append(order)
                            continue
                        entry_fee = compute_fee(fill.fill_price, actual_qty, rules.fees, "maker")
                        executed = inventory.sell(actual_qty, fill.fill_price, entry_fee)
                        if not executed:
                            remaining_orders.append(order)
                            continue

                    # Decrement capacity by the ACTUALLY EXECUTED quantity
                    # (after spot-constraint clamping, not the original fill request)
                    if cfg.split_volume_by_side:
                        if order.side == "buy":
                            buy_bar_capacity -= actual_qty
                        else:
                            sell_bar_capacity -= actual_qty
                    else:
                        buy_bar_capacity -= actual_qty
                        sell_bar_capacity -= actual_qty

                    trade = Trade(
                        trade_id=trade_counter,
                        side=order.side,
                        entry_price=fill.fill_price,
                        quantity=actual_qty,
                        entry_bar=abs_bar,
                        entry_timestamp=ts,
                        fee_quote=entry_fee,
                        entry_fee_quote=entry_fee,
                    )
                    trades.append(trade)
                    open_trades.append(trade)
                    trade_counter += 1
                    n_orders_filled += 1
                    last_fill_ts = ts

                    # Handle partial fill
                    remaining = order.remaining_quantity - actual_qty
                    if remaining > 0:
                        order.remaining_quantity = remaining
                        remaining_orders.append(order)
                else:
                    remaining_orders.append(order)

            active_orders = remaining_orders

            # c. Check if refresh needed
            needs_refresh = False
            if last_refresh_ts is None:
                needs_refresh = True
            elif ts - last_refresh_ts >= cfg.executor_refresh_time:
                needs_refresh = True

            # Check cooldown
            in_cooldown = False
            if last_fill_ts is not None and ts - last_fill_ts < cfg.cooldown_time:
                in_cooldown = True

            if needs_refresh and not in_cooldown:
                # Cancel existing orders
                active_orders = []

                # Rebalance check (before building new ladder)
                rebal_qty, rebal_fee = self._execute_rebalance(
                    bar, signals, strategy, inventory, c_close
                )
                if rebal_qty != 0:
                    n_rebalance_events += 1
                    total_rebalance_fees += rebal_fee

                # Build new orders via strategy
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

            # d. Record equity and position
            equity_curve[bar] = inventory.equity(c_close)
            position_history[bar] = inventory.base_balance

        # 4. Force-close remaining open trades at final bar close
        force_close_failures = 0
        if open_trades and n > 0:
            final_close = float(_close_arr[n - 1])
            final_ts = int(_ts_arr[n - 1])
            for trade in open_trades:
                exit_price = compute_slippage(final_close, cfg.slippage_bps, trade.side)

                if trade.side == "buy":
                    # Closing buy = selling base. Clamp to available.
                    available = inventory.available_base_for_sell()
                    close_qty = min(trade.quantity, available)
                    if close_qty <= 0:
                        force_close_failures += 1
                        continue
                    exit_fee = compute_fee(exit_price, close_qty, rules.fees, "taker")
                    executed = inventory.sell(close_qty, exit_price, exit_fee)
                    if not executed:
                        force_close_failures += 1
                        continue
                    trade.pnl_quote = (exit_price - trade.entry_price) * close_qty - trade.fee_quote - exit_fee
                else:
                    # Closing sell = buying base back. Clamp to available quote.
                    close_qty = trade.quantity
                    exit_fee = compute_fee(exit_price, close_qty, rules.fees, "taker")
                    cost = close_qty * exit_price + exit_fee
                    if inventory.available_quote_for_buy() < cost:
                        max_affordable = inventory.max_buy_quantity(exit_price, rules.fees.taker_fee)
                        close_qty = round_amount(max_affordable, rules)
                        if close_qty <= 0:
                            force_close_failures += 1
                            continue
                        # If we can't fully close, keep trade open entirely
                        if close_qty < trade.quantity:
                            force_close_failures += 1
                            continue
                        exit_fee = compute_fee(exit_price, close_qty, rules.fees, "taker")
                    executed = inventory.buy(close_qty, exit_price, exit_fee)
                    if not executed:
                        force_close_failures += 1
                        continue
                    trade.pnl_quote = (trade.entry_price - exit_price) * close_qty - trade.fee_quote - exit_fee

                trade.exit_price = exit_price
                trade.exit_bar = bar_index_offset + n - 1
                trade.exit_timestamp = final_ts
                trade.exit_type = "final_liquidation"
                trade.exit_fee_quote = exit_fee
                trade.exit_fee_type = "taker"
                trade.fee_quote += exit_fee
                n_market_exits += 1

            # Update final equity
            equity_curve[n - 1] = inventory.equity(final_close)
            position_history[n - 1] = inventory.base_balance

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
            n_rebalance_events=n_rebalance_events,
            total_rebalance_fees=total_rebalance_fees,
            open_trade_count=sum(1 for t in trades if t.exit_price is None),
            force_close_failures=force_close_failures,
        )
