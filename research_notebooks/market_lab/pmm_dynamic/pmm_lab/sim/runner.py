"""
CandleSimRunner — deterministic candle-based PMM Dynamic backtester.

This is the ONLY backtest runner in v1. A Quants Lab HBRunner may be added
in a future version for semantic parity validation.
"""

import logging
import numpy as np
from typing import Optional, List

from pmm_lab.config.params import PairRules
from pmm_lab.features.pmm_dynamic_features import (
    PMMDynamicConfig, compute_pmm_dynamic_features
)
from pmm_lab.features.alignment import align_features
from pmm_lab.sim.executor_model import SimConfig, SimResult, Trade, Order
from pmm_lab.sim.inventory import Inventory
from pmm_lab.sim.fill_model import check_buy_fill, check_sell_fill
from pmm_lab.sim.fees import compute_fee, compute_slippage
from pmm_lab.sim.latency import is_order_active
from pmm_lab.config.exchange_rules import round_price, round_amount, check_min_notional, check_order_size

logger = logging.getLogger(__name__)


class CandleSimRunner:
    """Deterministic candle-based PMM Dynamic simulator.

    Usage:
        runner = CandleSimRunner(sim_config, pair_rules)
        result = runner.run(candles)
    """

    def __init__(self, config: SimConfig, pair_rules: PairRules):
        """Initialize the simulator.

        Parameters
        ----------
        config : SimConfig
            Full simulation configuration.
        pair_rules : PairRules
            Exchange rules for price/amount rounding and fee rates.
        """
        self.config = config
        self.pair_rules = pair_rules

    def _build_order_ladder(
        self,
        reference_price: float,
        spread_multiplier: float,
        bar_idx: int,
        inventory: Optional['Inventory'] = None,
    ) -> tuple[List[Order], int, int]:
        """Build buy and sell order ladders.

        Returns
        -------
        tuple[List[Order], int placed, int rejected]
        """
        cfg = self.config
        rules = self.pair_rules
        orders: List[Order] = []
        n_placed = 0
        n_rejected = 0

        # Use current available balances if inventory provided, else use initial config
        if inventory is not None:
            available_quote = inventory.available_quote_for_buy()
            buy_capital = min(cfg.buy_side_weight * cfg.total_amount_quote, available_quote)
            # For sell capital, we track in base terms via available_base_for_sell
            sell_capital = (1.0 - cfg.buy_side_weight) * cfg.total_amount_quote
        else:
            buy_capital = cfg.buy_side_weight * cfg.total_amount_quote
            sell_capital = (1.0 - cfg.buy_side_weight) * cfg.total_amount_quote

        # Buy side
        for i, spread in enumerate(cfg.buy_spreads):
            price = reference_price * (1.0 - spread * spread_multiplier)
            price = round_price(price, rules)
            if price <= 0:
                n_rejected += 1
                continue

            amount_pct = cfg.buy_amounts_pct[i] if i < len(cfg.buy_amounts_pct) else 0.0
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
                side="buy",
                price=price,
                quantity=base_amount,
                remaining_quantity=base_amount,
                placed_bar=bar_idx,
                active_bar=bar_idx + cfg.latency_bars,
                level=i,
            ))
            n_placed += 1

        # Sell side
        for i, spread in enumerate(cfg.sell_spreads):
            price = reference_price * (1.0 + spread * spread_multiplier)
            price = round_price(price, rules)
            if price <= 0:
                n_rejected += 1
                continue

            amount_pct = cfg.sell_amounts_pct[i] if i < len(cfg.sell_amounts_pct) else 0.0
            quote_amount = sell_capital * amount_pct
            base_amount = quote_amount / price if price > 0 else 0.0
            base_amount = round_amount(base_amount, rules)

            # Clamp to available base (spot constraint)
            if inventory is not None and inventory.enforce_spot_constraints:
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
                side="sell",
                price=price,
                quantity=base_amount,
                remaining_quantity=base_amount,
                placed_bar=bar_idx,
                active_bar=bar_idx + cfg.latency_bars,
                level=i,
            ))
            n_placed += 1

        return orders, n_placed, n_rejected

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
            if candle_high >= tp_price:
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
            if candle_low <= tp_price:
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

    def run(self, candles: np.ndarray, sim_start_idx: Optional[int] = None) -> SimResult:
        """Run a full backtest on the given candle data.

        Parameters
        ----------
        candles : np.ndarray
            Canonical structured candle array (including warmup bars).
        sim_start_idx : int, optional
            Bar index where order placement and fill checking begins.
            Bars before this are used only for indicator warmup.
            If None, defaults to features.warmup_end (after alignment).

        Returns
        -------
        SimResult
            Complete backtest results including trades, equity curve, and statistics.
        """
        cfg = self.config
        rules = self.pair_rules
        n = len(candles)
        self._warned_no_orders = False

        # 1. Compute features
        feat_config = PMMDynamicConfig(
            macd_fast=cfg.macd_fast,
            macd_slow=cfg.macd_slow,
            macd_signal=cfg.macd_signal,
            natr_length=cfg.natr_length,
        )
        raw_features = compute_pmm_dynamic_features(candles, feat_config)

        # 2. Align features
        features = align_features(raw_features, timestamp_mode=cfg.timestamp_mode)
        warmup_end = features.warmup_end

        # Use sim_start_idx if provided, otherwise default to warmup_end
        loop_start = max(warmup_end, sim_start_idx) if sim_start_idx is not None else warmup_end

        # 3. Initialize
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

        # Fill pre-loop bars with initial equity
        for i in range(min(loop_start, n)):
            equity_curve[i] = inventory.equity(float(candles["close"][i]))
            position_history[i] = inventory.base_balance

        # 4. Main simulation loop
        for bar in range(loop_start, n):
            ts = int(candles["timestamp"][bar])
            c_open = float(candles["open"][bar])
            c_high = float(candles["high"][bar])
            c_low = float(candles["low"][bar])
            c_close = float(candles["close"][bar])
            c_volume = float(candles["volume"][bar])

            ref_price = float(features.reference_price[bar])
            spread_mult = float(features.spread_multiplier[bar])

            # Skip bar if features are NaN
            if np.isnan(ref_price) or np.isnan(spread_mult):
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
                    trade.exit_bar = bar
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
                        # Check available quote; if insufficient, buy what we can
                        close_qty = trade.quantity
                        cost = close_qty * exit_price + exit_fee
                        if inventory.available_quote_for_buy() < cost:
                            max_affordable = inventory.max_buy_quantity(exit_price, rules.fees.taker_fee)
                            close_qty = round_amount(max_affordable, rules)
                            if close_qty <= 0:
                                continue
                            exit_fee = compute_fee(exit_price, close_qty, rules.fees, fee_type)
                        executed = inventory.buy(close_qty, exit_price, exit_fee)
                        if not executed:
                            continue
                        trade.pnl_quote = (trade.entry_price - exit_price) * close_qty - trade.fee_quote - exit_fee

                    trade.exit_fee_quote = exit_fee
                    trade.fee_quote += exit_fee
                    closed_trade_ids.add(trade.trade_id)

                    if exit_type in ("stop_loss", "time_limit", "trailing_stop"):
                        n_market_exits += 1

                    last_fill_ts = ts

            open_trades = [t for t in open_trades if t.trade_id not in closed_trade_ids]

            # b. Check fills on active orders — shared capacity per bar
            bar_capacity = cfg.fill_participation_rate * c_volume
            remaining_orders = []
            for order in active_orders:
                if not is_order_active(bar, order.placed_bar, cfg.latency_bars):
                    remaining_orders.append(order)
                    continue

                if bar_capacity <= 0:
                    remaining_orders.append(order)
                    continue

                if order.side == "buy":
                    fill = check_buy_fill(
                        order.price, order.remaining_quantity,
                        c_low, c_volume, cfg.fill_participation_rate,
                        remaining_capacity=bar_capacity,
                    )
                else:
                    fill = check_sell_fill(
                        order.price, order.remaining_quantity,
                        c_high, c_volume, cfg.fill_participation_rate,
                        remaining_capacity=bar_capacity,
                    )

                if fill.filled:
                    actual_qty = fill.fill_quantity
                    bar_capacity -= actual_qty  # decrement shared capacity

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

                    trade = Trade(
                        trade_id=trade_counter,
                        side=order.side,
                        entry_price=fill.fill_price,
                        quantity=actual_qty,
                        entry_bar=bar,
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

                # Build new ladder
                new_orders, placed, rejected = self._build_order_ladder(
                    ref_price, spread_mult, bar, inventory=inventory
                )

                if placed == 0 and len(cfg.buy_spreads) + len(cfg.sell_spreads) > 0:
                    if not self._warned_no_orders:
                        self._warned_no_orders = True
                        logger.warning(
                            "Bar %d: total_amount_quote too small to place any orders at price %g "
                            "(this warning will not repeat for this run)",
                            bar, ref_price,
                        )

                active_orders = new_orders
                n_orders_placed += placed
                n_orders_rejected += rejected
                last_refresh_ts = ts

            # d. Record equity and position
            equity_curve[bar] = inventory.equity(c_close)
            position_history[bar] = inventory.base_balance

        # 5. Force-close remaining open trades at final bar close
        if open_trades and n > 0:
            final_close = float(candles["close"][n - 1])
            final_ts = int(candles["timestamp"][n - 1])
            for trade in open_trades:
                exit_price = compute_slippage(final_close, cfg.slippage_bps, trade.side)

                if trade.side == "buy":
                    # Closing buy = selling base. Clamp to available.
                    available = inventory.available_base_for_sell()
                    close_qty = min(trade.quantity, available)
                    if close_qty <= 0:
                        continue
                    exit_fee = compute_fee(exit_price, close_qty, rules.fees, "taker")
                    executed = inventory.sell(close_qty, exit_price, exit_fee)
                    if not executed:
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
                            continue
                        exit_fee = compute_fee(exit_price, close_qty, rules.fees, "taker")
                    executed = inventory.buy(close_qty, exit_price, exit_fee)
                    if not executed:
                        continue
                    trade.pnl_quote = (trade.entry_price - exit_price) * close_qty - trade.fee_quote - exit_fee

                trade.exit_price = exit_price
                trade.exit_bar = n - 1
                trade.exit_timestamp = final_ts
                trade.exit_type = "time_limit"
                trade.exit_fee_quote = exit_fee
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
        )
