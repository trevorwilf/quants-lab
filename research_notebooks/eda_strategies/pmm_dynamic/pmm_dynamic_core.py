"""
pmm_dynamic_core.py — Shared core library for PMM Dynamic backtester.

Contains all backend-agnostic components: configuration, data models, indicators,
parameter suggestion, Optuna scoring, YAML export, and walk-forward evaluation.

Both pmm_dynamic_optimizer.py (CPU) and pmm_dynamic_optimizer_gpu.py (GPU) import
from this module. All changes to shared logic belong here.

Author: Trading Pod project
"""

# =============================================================================
# RECOMMENDED SETTINGS FOR NONKYC.IO LIVE DEPLOYMENT
#
# Fee structure (NonKYC.io):
#   maker_fee = 0.001  (0.1%)    taker_fee = 0.002  (0.2%)
#
# Minimum viable spread per round trip:
#   = maker_fee + taker_fee + slippage_max_pct = 0.001 + 0.002 + 0.001 = 0.004
#   auto_spread_floor=True enforces this automatically.
#
# Execution realism:
#   slippage_max_pct = 0.001    fill_rate_pct = 0.05    cooldown_seconds = 15
#
# Capital controls:
#   deploy_fraction = 0.4       max_open_positions = 4
#   compounding = False         max_order_quote = 0.0
#
# Quality gates (create_objective defaults):
#   min_trades = 50             max_trades_per_day = 20.0
#   turnover_penalty_weight = 0.1    n_eval_seeds = 3
#   auto_spread_floor = True
#
# Deployment gates (run before exporting YAML):
#   walk_forward_evaluate(): median_test_sharpe > 0.5, n_profitable_windows >= 3 of 5
#   Stress test: re-run with slippage x2 and fill_rate x0.5 — must stay profitable
# =============================================================================

from __future__ import annotations

import hashlib
import logging
import math
import os
import random
import uuid
from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MongoDB helpers
# ---------------------------------------------------------------------------

def get_mongo_client(uri: Optional[str] = None):
    """Return a MongoClient using env or explicit URI."""
    try:
        from pymongo import MongoClient
    except ImportError:
        raise ImportError("pymongo is required for MongoDB data loading. Install with: pip install pymongo")
    uri = uri or os.environ.get(
        "MONGO_URI", "mongodb://admin:admin@localhost:27017/quants_lab?authSource=admin"
    )
    return MongoClient(uri)


def load_candles(
    connector: str,
    pair: str,
    interval: str,
    start: Optional[pd.Timestamp] = None,
    end: Optional[pd.Timestamp] = None,
    db_name: Optional[str] = None,
    mongo_uri: Optional[str] = None,
    validate: bool = False,
    interval_for_validation: str = None,  # FIX-1: auto-derive from interval
) -> pd.DataFrame:
    """
    Load OHLCV candles from MongoDB into a pandas DataFrame.

    Returns DataFrame with columns:
        timestamp (datetime64, UTC), open, high, low, close, volume
    sorted ascending by timestamp.
    """
    db_name = db_name or os.environ.get("MONGO_DATABASE", "quants_lab")
    client = get_mongo_client(mongo_uri)
    db = client[db_name]

    # MongoDB stores pair as "BTC-USDT" (hyphen), but user may pass "BTC/USDT" (slash)
    mongo_pair = pair.replace("/", "-")

    query: Dict[str, Any] = {
        "connector": connector,
        "trading_pair": mongo_pair,
        "interval": interval,
    }
    if start or end:
        ts_filter: Dict[str, Any] = {}
        if start:
            ts_filter["$gte"] = int(start.timestamp())
        if end:
            ts_filter["$lte"] = int(end.timestamp())
        query["timestamp"] = ts_filter

    cursor = db.candles.find(query, {"_id": 0}).sort("timestamp", 1)
    rows = list(cursor)
    client.close()

    if not rows:
        log.warning("No candles found for %s %s %s", connector, mongo_pair, interval)
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    df = pd.DataFrame(rows)
    # Timestamps are stored as Unix seconds (integers)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
    # Drop the trading_pair column if present (we don't need it in the DataFrame)
    if "trading_pair" in df.columns:
        df = df.drop(columns=["trading_pair"])
    if "connector" in df.columns:
        df = df.drop(columns=["connector"])
    if "interval" in df.columns:
        df = df.drop(columns=["interval"])
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.sort_values("timestamp").reset_index(drop=True)

    if validate and len(df) > 1:
        val_interval = interval_for_validation or interval  # FIX-1: auto-derive
        v = validate_candles(df, interval=val_interval, raise_on_failure=False)
        if not v["passed"]:
            log.error("Candle validation FAILED: %s", v["warnings"])
        else:
            log.info("Candle validation passed: %d candles, gap_pct=%.4f%%",
                     v["n_candles"], v["gap_pct"] * 100)
        for w in v["warnings"]:
            log.warning("Candle QA: %s", w)

    return df


# ---------------------------------------------------------------------------
# Technical indicators
# ---------------------------------------------------------------------------

def compute_macd(
    close: pd.Series, fast: int = 21, slow: int = 42, signal: int = 9
) -> pd.DataFrame:
    """Compute MACD line, signal line, and histogram."""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame({
        "macd": macd_line,
        "macd_signal": signal_line,
        "macd_hist": histogram,
    })


def compute_natr(
    high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14
) -> pd.Series:
    """Normalized Average True Range (as a decimal, e.g. 0.02 = 2%)."""
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = tr.ewm(span=length, adjust=False).mean()
    natr = atr / close
    return natr


def _auto_spread_min_multiplier(
    candles_df: pd.DataFrame,
    entry_fee: float,
    exit_fee: float,
    slippage_max_pct: float,
    natr_length: int = 14,
    safety_buffer: float = 1.2,
) -> float:
    """
    Compute the minimum viable spread NATR multiplier such that a round-trip
    covers entry_fee + exit_fee + slippage, with a safety buffer.

    Returns a multiplier (e.g., 1.5 means the spread must be >= 1.5x NATR).
    Uses the median NATR computed from candles_df. Falls back to a direct
    absolute calculation when NATR cannot be computed.
    """
    try:
        natr_series = compute_natr(
            candles_df["high"], candles_df["low"], candles_df["close"], natr_length
        )
        typical_natr = float(natr_series.dropna().median())
    except Exception:
        typical_natr = 0.0

    min_cost = entry_fee + exit_fee + slippage_max_pct
    if typical_natr > 1e-8:
        return round(min_cost / typical_natr * safety_buffer, 1)
    # Fallback: return a multiplier of 1.0 (spread must be at least 1x whatever NATR is)
    return 1.0


# ---------------------------------------------------------------------------
# PMM Dynamic config dataclass
# ---------------------------------------------------------------------------

@dataclass
class PMMDynamicConfig:
    """All tunable parameters for the PMM Dynamic strategy."""

    # -- Exchange / pair (fixed for a given optimization run) --
    connector: str = "nonkyc"
    trading_pair: str = "BTC/USDT"
    candles_connector: str = "nonkyc"
    candles_pair: str = "BTC/USDT"
    interval: str = "5m"

    # -- Capital --
    total_amount_quote: float = 1000.0
    leverage: int = 1  # 1 for spot

    # -- MACD --
    macd_fast: int = 21
    macd_slow: int = 42
    macd_signal: int = 9

    # -- NATR --
    natr_length: int = 14

    # -- Spreads (volatility multipliers, e.g. 1.0 = 1x NATR) --
    buy_spreads: List[float] = field(default_factory=lambda: [1.0, 2.0])
    sell_spreads: List[float] = field(default_factory=lambda: [1.0, 2.0])
    buy_amounts_pct: List[float] = field(default_factory=lambda: [50.0, 50.0])
    sell_amounts_pct: List[float] = field(default_factory=lambda: [50.0, 50.0])

    # -- Triple barrier (as decimals) --
    stop_loss: float = 0.03
    take_profit: float = 0.02
    time_limit_seconds: int = 3600  # 1 hour
    trailing_stop_activation: float = 0.01  # activate when 1% in profit
    trailing_stop_delta: float = 0.005  # trail by 0.5%

    # -- Execution --
    executor_refresh_seconds: int = 300  # 5 minutes
    cooldown_seconds: int = 15

    # -- Fees (maker/taker split) --
    maker_fee: float = 0.001    # 0.1%
    taker_fee: float = 0.002    # 0.2% NonKYC taker
    entry_fee_type: str = "maker"
    exit_fee_type: str = "taker"

    # -- Intrabar exit priority --
    intrabar_exit_mode: str = "worst_case"  # "worst_case" or "best_case"

    # -- Realism controls --
    # Compounding: False = fixed order sizes based on initial capital (no snowball)
    compounding: bool = False
    # Max quote per individual order (0 = unlimited). Prevents unrealistic giant orders.
    max_order_quote: float = 0.0
    # Slippage: random penalty applied to each fill (uniform 0 to slippage_max_pct).
    # E.g., 0.003 = up to 0.3% adverse slippage per fill.
    slippage_max_pct: float = 0.001
    # Volume-based fill rate: probability of fill = min(1, (candle_volume_quote * fill_rate_pct) / order_quote).
    # 0 = disabled (any price touch = 100% fill). 0.1 = your order must be ≤10% of candle volume to fill reliably.
    fill_rate_pct: float = 0.0
    # Max simultaneous open positions (0 = unlimited). Prevents unrealistic position stacking.
    max_open_positions: int = 0
    # Capital deployment fraction: what fraction of available balance to deploy per refresh (0.0-1.0)
    # 0.5 = deploy half to buys, half to sells. Prevents all-in on every candle.
    deploy_fraction: float = 0.5
    # Minimum spread floor: spread_adj is floored at max(entry_fee + exit_fee + slippage, this value)
    min_spread_floor: float = 0.0

    # -- Spread floor mode (BUG-5 FIX: reviewer §2.4) --
    enforce_spread_floor: bool = False  # False = match Hummingbot exactly; True = simulator enforces floors
    enforce_nc_guard: bool = False      # False = match Hummingbot exactly; True = simulator enforces non-crossing

    # -- Cooldown mode (ADD-2: match Hummingbot) --
    cooldown_on_stop_loss_only: bool = True  # True = match Hummingbot; False = cooldown on any closure

    # -- Timestamp semantics (BUG-3 V3) --
    timestamp_mode: str = "unknown"  # "unknown" = conservative (shift signals by 1 candle); "close" = no shift; "open" = shift
    # "close" = candle timestamps represent CLOSE times — no look-ahead, signals use same candle
    # "open"  = candle timestamps represent OPEN times — signals shift by 1 candle (conservative)
    # "unknown" = not confirmed — defaults to conservative behavior (same as "open")

    # -- Volume units (FIX-3 V3) --
    volume_units: str = "base"  # "base", "quote", or "unknown"
    # "base"   : volume column is in base currency (candle_vol_quote = volume * close)
    # "quote"  : volume column is already in quote currency (candle_vol_quote = volume)
    # "unknown": not confirmed — defaults to "base" with a warning when fill_rate_pct > 0

    # -- Starting inventory (FIX-4) --
    initial_inventory_mode: str = "half_and_half"
    # "half_and_half" : quote = total/2, base = (total/2) / first_mid_price  [DEFAULT]
    # "all_quote"     : quote = total, base = 0  (original behavior — biases toward buys)
    # "all_base"      : base = total / first_mid_price, quote = 0

    # -- Fill model hardening (FIX-5) --
    latency_candles: int = 1
    # Orders placed at candle i are only eligible for fill starting at candle i+latency_candles.
    # Default 1: "next-candle" fill (realistic for limit orders).

    maker_validity_check: bool = True
    # If True: if the next candle's OPEN crosses the limit order price (i.e., price gaps
    # through your limit), treat it as a TAKER fill (apply taker fee instead of maker fee)

    @property
    def z_window(self) -> int:
        """Rolling z-score window to match Hummingbot's bounded candle history."""
        return max(self.macd_fast, self.macd_slow, self.macd_signal, self.natr_length) + 100

    @property
    def entry_fee(self) -> float:
        return self.maker_fee if self.entry_fee_type == "maker" else self.taker_fee

    @property
    def exit_fee(self) -> float:
        return self.maker_fee if self.exit_fee_type == "maker" else self.taker_fee


# ---------------------------------------------------------------------------
# PendingOrder dataclass
# ---------------------------------------------------------------------------

@dataclass
class PendingOrder:
    """An order placed at candle i, fillable starting candle i+1."""
    side: str           # "buy" or "sell"
    price: float
    amount: float       # base currency
    quote_reserved: float  # quote locked for buy orders
    base_reserved: float = 0.0  # base currency locked for sell orders
    placed_ts: float = 0.0
    expires_ts: float = 0.0  # canceled at next refresh


# ---------------------------------------------------------------------------
# Position / Executor tracker
# ---------------------------------------------------------------------------

@dataclass
class Position:
    """Tracks a single open position from order fill to exit."""
    side: str  # "buy" or "sell"
    entry_price: float = 0.0
    amount: float = 0.0
    entry_quote: float = 0.0  # quote currency locked at entry
    entry_time: float = 0.0  # unix seconds
    peak_pnl_pct: float = 0.0
    trailing_active: bool = False
    closed: bool = False
    exit_price: float = 0.0
    exit_time: float = 0.0
    exit_reason: str = ""
    pnl_quote: float = 0.0
    entry_fee_paid: float = 0.0
    exit_fee_paid: float = 0.0


# ---------------------------------------------------------------------------
# Position helpers
# ---------------------------------------------------------------------------

def _position_pnl(pos: Position, current_price: float) -> float:
    """Unrealized PnL in quote currency."""
    if pos.side == "buy":
        return pos.amount * (current_price - pos.entry_price)
    else:  # sell (short)
        return pos.amount * (pos.entry_price - current_price)


def _position_pnl_pct(pos: Position, current_price: float) -> float:
    """Unrealized PnL as a fraction of entry."""
    if pos.entry_price == 0:
        return 0.0
    if pos.side == "buy":
        return (current_price - pos.entry_price) / pos.entry_price
    else:
        return (pos.entry_price - current_price) / pos.entry_price


def _close_position(pos: Position, price: float, ts: float, reason: str, exit_fee_rate: float = 0.0):
    """Mark position as closed with net PnL (after fees)."""
    pos.closed = True
    pos.exit_price = price
    pos.exit_time = ts
    pos.exit_reason = reason
    exit_notional = pos.amount * price
    pos.exit_fee_paid = exit_notional * exit_fee_rate
    pos.pnl_quote = _position_pnl(pos, price) - pos.entry_fee_paid - pos.exit_fee_paid


def _interval_to_seconds(interval: str) -> int:
    """Convert interval string like '5m', '1h', '1d' to seconds."""
    multipliers = {"m": 60, "h": 3600, "d": 86400}
    for suffix, mult in multipliers.items():
        if interval.endswith(suffix):
            try:
                return int(interval[:-1]) * mult
            except ValueError:
                pass
    return 300  # default 5 minutes


# ---------------------------------------------------------------------------
# Backtest result
# ---------------------------------------------------------------------------

@dataclass
class BacktestResult:
    """Aggregated backtest metrics."""
    net_pnl: float = 0.0
    net_pnl_pct: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    profit_factor: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    avg_trade_pnl: float = 0.0
    total_volume: float = 0.0

    # Exit breakdown
    n_take_profit: int = 0
    n_stop_loss: int = 0
    n_trailing_stop: int = 0
    n_time_limit: int = 0
    n_end_of_data: int = 0

    equity_curve: List[float] = field(default_factory=list)
    trades: List[Dict[str, Any]] = field(default_factory=list)

    @staticmethod
    def empty() -> "BacktestResult":
        return BacktestResult(sharpe_ratio=-10.0)

    @staticmethod
    def compute(
        initial_capital: float,
        final_balance: float,
        equity_curve: List[float],
        closed_positions: List[Position],
        max_drawdown: float,
        candle_seconds: int,
    ) -> "BacktestResult":
        r = BacktestResult()
        r.equity_curve = equity_curve
        r.net_pnl = final_balance - initial_capital
        r.net_pnl_pct = r.net_pnl / initial_capital if initial_capital > 0 else 0
        r.max_drawdown = max_drawdown
        r.total_trades = len(closed_positions)

        if r.total_trades == 0:
            r.sharpe_ratio = -10.0
            return r

        # Trade-level stats
        pnls = [p.pnl_quote for p in closed_positions]
        gross_profit = sum(p for p in pnls if p > 0)
        gross_loss = abs(sum(p for p in pnls if p < 0))
        wins = sum(1 for p in pnls if p > 0)

        r.win_rate = wins / r.total_trades
        r.avg_trade_pnl = np.mean(pnls)
        r.profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
        r.total_volume = sum(
            abs(p.amount * p.entry_price) + abs(p.amount * p.exit_price)
            for p in closed_positions
        )

        # Exit reasons
        for p in closed_positions:
            if p.exit_reason == "take_profit":
                r.n_take_profit += 1
            elif p.exit_reason == "stop_loss":
                r.n_stop_loss += 1
            elif p.exit_reason == "trailing_stop":
                r.n_trailing_stop += 1
            elif p.exit_reason == "time_limit":
                r.n_time_limit += 1
            elif p.exit_reason == "end_of_data":
                r.n_end_of_data += 1

        # Sharpe ratio (annualized from equity curve returns)
        if len(equity_curve) >= 2:
            eq = pd.Series(equity_curve)
            returns = eq.pct_change().dropna()
            if len(returns) > 1 and returns.std() > 0:
                candles_per_year = (365.25 * 86400) / candle_seconds
                r.sharpe_ratio = (returns.mean() / returns.std()) * math.sqrt(candles_per_year)
            else:
                r.sharpe_ratio = 0.0
        else:
            r.sharpe_ratio = -10.0

        # Trade details for analysis
        r.trades = [
            {
                "side": p.side,
                "entry_price": p.entry_price,
                "exit_price": p.exit_price,
                "amount": p.amount,
                "pnl_quote": p.pnl_quote,
                "entry_fee_paid": p.entry_fee_paid,
                "exit_fee_paid": p.exit_fee_paid,
                "exit_reason": p.exit_reason,
                "duration_s": p.exit_time - p.entry_time,
            }
            for p in closed_positions
        ]

        return r


# ---------------------------------------------------------------------------
# Parameter suggestion — single source of truth (imported by GPU module)
# ---------------------------------------------------------------------------

def _suggest_params(
    trial,
    n_levels: int = 2,
    spread_min: float = 0.5,
    spread_max: float = 8.0,
    spread_step: float = 0.1,
    optimize_n_levels: bool = False,
    min_levels: int = 1,
    max_levels: int = 10,
    optimize_amounts: bool = True,
) -> dict:
    """
    Suggest Optuna trial parameters. Single source of truth — imported by GPU module.
    Returns a flat dict of all suggested parameter keys (mirrors trial.params after call).
    """
    macd_slow = trial.suggest_int("macd_slow", 30, 60)
    macd_fast = trial.suggest_int("macd_fast", 8, macd_slow - 1)
    macd_signal = trial.suggest_int("macd_signal", 5, 15)
    natr_length = trial.suggest_int("natr_length", 7, 30)

    if optimize_n_levels:
        actual_levels = trial.suggest_int("n_levels", min_levels, max_levels)
    else:
        actual_levels = n_levels

    prev_spread = 0.0
    for lvl in range(actual_levels):
        lvl_min = max(spread_min, prev_spread + spread_step)
        lvl_max = min(spread_max,
                      spread_min + (spread_max - spread_min) * (lvl + 1) / actual_levels * 1.5)
        lvl_max = max(lvl_max, lvl_min + spread_step)
        lvl_min = round(math.ceil(lvl_min / spread_step) * spread_step, 6)
        lvl_max = round(math.floor(lvl_max / spread_step) * spread_step, 6)
        if lvl_max <= lvl_min:
            lvl_max = round(lvl_min + spread_step, 6)
        sv = trial.suggest_float(f"spread_level_{lvl + 1}", lvl_min, lvl_max, step=spread_step)
        sv = max(sv, prev_spread + spread_step)
        prev_spread = round(sv, 6)

    stop_loss = trial.suggest_float("stop_loss", 0.01, 0.15, step=0.005)
    take_profit = trial.suggest_float("take_profit", 0.005, 0.10, step=0.005)
    time_limit_minutes = trial.suggest_int("time_limit_minutes", 15, 480, step=15)
    trailing_activation = trial.suggest_float("trailing_activation", 0.005, 0.05, step=0.005)
    # trailing_delta MUST be strictly less than trailing_activation
    trailing_delta_max = max(0.002, trailing_activation - 0.001)
    trailing_delta = trial.suggest_float(
        "trailing_delta",
        0.002,
        min(0.025, trailing_delta_max),
        step=0.001,
    )
    refresh_minutes = trial.suggest_int("refresh_minutes", 3, 60, step=3)

    if optimize_amounts and actual_levels > 1:
        for lvl in range(actual_levels):
            trial.suggest_float(f"amount_weight_{lvl + 1}", 0.5, 10.0, step=0.5)

    params = dict(trial.params)
    params["n_levels"] = actual_levels

    # Amount normalization guard
    if optimize_amounts and actual_levels > 1:
        raw_weights = [params.get(f"amount_weight_{lvl + 1}", 1.0) for lvl in range(actual_levels)]
        total_weight = sum(raw_weights)
        buy_amounts_pct = [round(w / total_weight * 100, 2) for w in raw_weights]
        total_pct = sum(buy_amounts_pct)
        if abs(total_pct - 100.0) > 0.5:
            buy_amounts_pct = [round(w / total_pct * 100, 2) for w in buy_amounts_pct]

    return params


# ---------------------------------------------------------------------------
# Optuna objective scoring — shared between CPU and GPU backends
# ---------------------------------------------------------------------------

def _compute_objective(
    result: dict,
    metric: str,
    max_dd_constraint: float,
    min_trades: int = 50,
    max_trades_per_day: float = 20.0,
    turnover_penalty_weight: float = 0.1,
    candle_seconds: int = 300,
    n_candles: int = 0,
    use_robust_score: bool = False,
    lambda_dd: float = 2.0,
    lambda_cvar: float = 1.0,
    equity_curve: list = None,
    use_enhanced: bool = False,
) -> float:
    """
    Compute penalized Optuna objective from a backtest result dict.

    This is the SINGLE scoring path used by both CPU and GPU backends.
    When use_enhanced=True, delegates to compute_enhanced_objective() (reviewer's formula).
    """
    if result["n_trades"] < min_trades:
        return -10.0

    # Enhanced scoring path (V3 reviewer's formula)
    if use_enhanced:
        return compute_enhanced_objective(
            result,
            candle_seconds=candle_seconds,
            n_candles=n_candles,
            equity_curve=equity_curve,
            min_trades=min_trades,
            max_mdd=max_dd_constraint,
        )

    # Robust scoring path: requires a BacktestResult object, not a raw dict
    if use_robust_score and isinstance(result, BacktestResult):
        return compute_robust_score(
            result, candle_seconds, n_candles,
            lambda_dd=lambda_dd, lambda_cvar=lambda_cvar,
        )

    penalty = 0.0
    if result["max_dd"] > max_dd_constraint:
        penalty = (result["max_dd"] - max_dd_constraint) * 50.0

    turnover_penalty = 0.0
    if max_trades_per_day > 0 and turnover_penalty_weight > 0 and n_candles > 0:
        total_days = n_candles * candle_seconds / 86400.0
        trades_per_day = result["n_trades"] / max(total_days, 1.0)
        if trades_per_day > max_trades_per_day:
            turnover_penalty = (trades_per_day - max_trades_per_day) * turnover_penalty_weight

    if metric == "sharpe_ratio":
        return result["sharpe"] - penalty - turnover_penalty
    elif metric == "net_pnl_pct":
        return result["pnl_pct"] - penalty - turnover_penalty
    elif metric == "profit_factor":
        gl = result.get("gross_loss", 0.0)
        gw = result.get("gross_win", 0.0)
        pf = gw / gl if gl > 0.0 else 100.0
        return min(pf, 100.0) - penalty - turnover_penalty
    return result["sharpe"] - penalty - turnover_penalty


def compute_robust_score(
    result: "BacktestResult",
    candle_seconds: int,
    n_candles: int,
    lambda_dd: float = 2.0,
    lambda_cvar: float = 1.0,
    lambda_tpd: float = 0.05,
    lambda_to: float = 0.02,
    tpd_max: float = 20.0,
) -> float:
    """
    Compute a robust single-scenario score:

        Score = Sharpe
                - lambda_dd   * MDD
                - lambda_cvar * CVaR_95
                - lambda_tpd  * max(0, TPD - tpd_max)
                - lambda_to   * Turnover

    Parameters
    ----------
    result       : BacktestResult from a backtest run
    candle_seconds : seconds per candle
    n_candles    : total candles in the backtest window
    lambda_dd    : MDD penalty weight (default 2.0)
    lambda_cvar  : CVaR_95 penalty weight (default 1.0)
    lambda_tpd   : trades-per-day penalty weight (default 0.05)
    lambda_to    : turnover penalty weight (default 0.02)
    tpd_max      : trades/day above which to penalize (default 20.0)

    Returns
    -------
    float score (higher = better)
    """
    if result.total_trades == 0 or result.sharpe_ratio <= -9.0:
        return -10.0

    sharpe = result.sharpe_ratio
    mdd    = result.max_drawdown

    # CVaR_95: expected loss magnitude in the worst 5% of candle returns
    cvar95 = 0.0
    if len(result.equity_curve) >= 20:
        eq = np.array(result.equity_curve, dtype=np.float64)
        rets = np.diff(eq) / np.maximum(eq[:-1], 1e-10)
        q05 = np.quantile(rets, 0.05)
        tail = rets[rets <= q05]
        if len(tail) > 0:
            cvar95 = float(-np.mean(tail))   # positive = bad

    # Trades per day
    total_days = n_candles * candle_seconds / 86400.0
    tpd = result.total_trades / max(total_days, 1.0)
    tpd_excess = max(0.0, tpd - tpd_max)

    # Turnover: total volume / initial capital (proxy)
    initial_capital = result.equity_curve[0] if result.equity_curve else 1.0
    turnover = result.total_volume / max(initial_capital, 1.0) if hasattr(result, "total_volume") else 0.0

    score = (
        sharpe
        - lambda_dd   * mdd
        - lambda_cvar * cvar95
        - lambda_tpd  * tpd_excess
        - lambda_to   * turnover
    )
    return float(score)


def compute_enhanced_objective(
    result: dict,
    candle_seconds: int,
    n_candles: int,
    equity_curve: list = None,
    # OBJ-1: Reviewer's formula weights (§5.1)
    w_sharpe: float = 0.35,
    w_pnl: float = 0.35,
    w_pf: float = 0.15,
    w_dd: float = 0.30,
    w_low_trades: float = 0.10,
    w_high_trades: float = 0.10,
    # Clamp ranges
    sharpe_clamp: tuple = (-3.0, 5.0),
    pnl_clamp: tuple = (-50.0, 200.0),
    pf_clamp: tuple = (-2.0, 2.0),
    # Gates
    min_trades: int = 50,
    max_mdd: float = 0.25,
    n_min: int = 50,
    tpd_max: float = 20.0,
) -> float:
    """
    OBJ-1: Reviewer's recommended objective formula (§5.1).

    score = w_sharpe * clamp(Sharpe)
          + w_pnl   * clamp(PnL%)
          + w_pf    * clamp(log(PF))
          - w_dd    * clamp(MDD)
          - w_low_trades  * max(0, (n_min - n_trades) / n_min)
          - w_high_trades * max(0, (TPD / tpd_max - 1))
    """
    n_trades = result.get("n_trades", 0) if isinstance(result, dict) else result["n_trades"]
    if n_trades < min_trades:
        return -10.0

    sharpe = result.get("sharpe", 0.0) if isinstance(result, dict) else result["sharpe"]
    pnl_pct = result.get("pnl_pct", 0.0) if isinstance(result, dict) else result["pnl_pct"]
    mdd = result.get("max_dd", 0.0) if isinstance(result, dict) else result["max_dd"]

    if mdd > max_mdd:
        return -10.0

    # Profit factor
    gw = result.get("gross_win", 0.0) if isinstance(result, dict) else 0.0
    gl = result.get("gross_loss", 0.0) if isinstance(result, dict) else 0.0
    pf = gw / gl if gl > 0 else 10.0
    log_pf = math.log(max(pf, 0.01))  # clamp before log to avoid -inf

    # Trades per day
    total_days = n_candles * candle_seconds / 86400.0 if n_candles > 0 else 1.0
    tpd = n_trades / max(total_days, 1.0)

    # Reviewer's formula (§5.1)
    score = (
        w_sharpe * max(sharpe_clamp[0], min(sharpe, sharpe_clamp[1]))
        + w_pnl * max(pnl_clamp[0], min(pnl_pct * 100, pnl_clamp[1]))
        + w_pf * max(pf_clamp[0], min(log_pf, pf_clamp[1]))
        - w_dd * max(0.0, min(mdd, 1.0))
        - w_low_trades * max(0.0, (n_min - n_trades) / max(n_min, 1))
        - w_high_trades * max(0.0, (tpd / max(tpd_max, 1.0) - 1.0))
    )
    return float(score)


def compute_robust_wf_objective(
    per_fold_scores: list,
    per_fold_stress_scores: list = None,
) -> float:
    """
    OBJ-2: Reviewer's multi-scenario robust objective (§5.2).

    robust_score = median(worst-stress per fold) - 0.25 * IQR(scores)

    Hard gates:
    - At least 60% of folds must be profitable (score > 0)
    """
    if not per_fold_scores:
        return -10.0

    scores = np.array(per_fold_scores)
    n = len(scores)

    # Hard gate: at least 60% of folds profitable
    n_profitable = int(np.sum(scores > 0))
    if n_profitable / n < 0.6:
        return -10.0

    # Reviewer's formula (§5.2): median of worst-stress per fold
    if per_fold_stress_scores is not None and len(per_fold_stress_scores) == n:
        fold_worst_stress = [min(stresses) if stresses else s
                            for s, stresses in zip(per_fold_scores, per_fold_stress_scores)]
        median_score = float(np.median(fold_worst_stress))
    else:
        median_score = float(np.median(scores))

    # IQR penalty for parameter stability
    q25 = float(np.percentile(scores, 25))
    q75 = float(np.percentile(scores, 75))
    iqr = q75 - q25

    robust_score = median_score - 0.25 * iqr
    return robust_score


def parameter_sensitivity_check(
    candles: pd.DataFrame,
    best_cfg: "PMMDynamicConfig",
    perturbation_pct: float = 0.10,
) -> dict:
    """
    Perturb each numeric parameter by +/- perturbation_pct and re-run.

    Returns dict mapping param_name -> {"base": score, "up": score, "down": score, "cliff": bool}.
    A "cliff" means the score drops by >50% from a 10% perturbation.
    """
    from dataclasses import fields as dc_fields, replace as dc_replace
    try:
        from pmm_dynamic_optimizer import PMMDynamicBacktester
    except ImportError:
        raise ImportError("pmm_dynamic_optimizer must be importable")

    candle_seconds = _interval_to_seconds(best_cfg.interval)
    n_candles = len(candles)

    def _run_score(cfg):
        bt = PMMDynamicBacktester(cfg)
        result = bt.run(candles)
        return compute_enhanced_objective(
            {
                "sharpe": result.sharpe_ratio,
                "pnl_pct": result.net_pnl_pct,
                "max_dd": result.max_drawdown,
                "n_trades": result.total_trades,
            },
            candle_seconds=candle_seconds,
            n_candles=n_candles,
            equity_curve=result.equity_curve,
            min_trades=0,  # don't gate during sensitivity analysis
        )

    base_score = _run_score(best_cfg)
    results = {}

    # Numeric fields to perturb
    numeric_fields = []
    for f in dc_fields(best_cfg):
        val = getattr(best_cfg, f.name)
        if isinstance(val, (int, float)) and f.name not in (
            "leverage", "cooldown_seconds", "latency_candles",
        ):
            numeric_fields.append(f.name)

    for fname in numeric_fields:
        val = getattr(best_cfg, fname)
        if val == 0:
            continue
        delta = abs(val * perturbation_pct)
        if isinstance(val, int):
            delta = max(1, int(delta))
            up_val = val + delta
            down_val = max(0, val - delta)
        else:
            up_val = val + delta
            down_val = max(0.0, val - delta)

        try:
            up_score = _run_score(dc_replace(best_cfg, **{fname: up_val}))
        except Exception:
            up_score = -10.0
        try:
            down_score = _run_score(dc_replace(best_cfg, **{fname: down_val}))
        except Exception:
            down_score = -10.0

        cliff = False
        if base_score > 0:
            if up_score < base_score * 0.5 or down_score < base_score * 0.5:
                cliff = True

        results[fname] = {
            "base": base_score,
            "up": up_score,
            "down": down_score,
            "cliff": cliff,
        }

    return results


# ---------------------------------------------------------------------------
# Export best trial to deployable YAML
# ---------------------------------------------------------------------------

def trial_to_controller_yaml(
    trial,
    connector: str = "nonkyc",
    trading_pair: str = "BTC/USDT",
    candles_connector: str = "nonkyc",
    interval: str = "5m",
    total_amount_quote: float = 1000.0,
    leverage: int = 1,
    n_levels: int = 2,
    walk_forward_result: dict = None,
    cooldown_seconds: int = 15,
    realism_config: dict = None,
) -> str:
    """Convert an Optuna trial's parameters to a Hummingbot controller YAML."""
    params = trial.params

    # Detect actual number of levels from trial params
    actual_levels = params.get("n_levels", n_levels)
    # Fallback: count spread_level_* keys
    level_keys = sorted([k for k in params if k.startswith("spread_level_")])
    if level_keys:
        actual_levels = len(level_keys)

    # Build spread lists
    buy_spread_lines = []
    sell_spread_lines = []
    for lvl in range(1, actual_levels + 1):
        key = f"spread_level_{lvl}"
        if key in params:
            buy_spread_lines.append(f"  - {params[key]}")
            sell_spread_lines.append(f"  - {params[key]}")

    # Build amount lists
    buy_amt_lines = []
    sell_amt_lines = []
    has_weights = any(k.startswith("amount_weight_") for k in params)
    if has_weights:
        raw_weights = []
        for lvl in range(1, actual_levels + 1):
            key = f"amount_weight_{lvl}"
            raw_weights.append(params.get(key, 1.0))
        total_weight = sum(raw_weights)
        for w in raw_weights:
            pct = round(w / total_weight * 100, 2)
            buy_amt_lines.append(f"  - {pct}")
            sell_amt_lines.append(f"  - {pct}")
    else:
        equal_pct = round(100.0 / actual_levels, 2)
        for _ in range(actual_levels):
            buy_amt_lines.append(f"  - {equal_pct}")
            sell_amt_lines.append(f"  - {equal_pct}")

    buy_spreads = "\n".join(buy_spread_lines)
    sell_spreads = "\n".join(sell_spread_lines)
    buy_amts = "\n".join(buy_amt_lines)
    sell_amts = "\n".join(sell_amt_lines)

    # FIX-3: Generate deterministic UUID from params + pair + interval
    id_seed = f"{connector}:{trading_pair}:{interval}:{sorted(params.items())}"
    deterministic_uuid = str(uuid.UUID(hashlib.md5(id_seed.encode()).hexdigest()))

    # FIX-4: Effective capital (deploy_fraction)
    effective_quote = total_amount_quote
    if realism_config and realism_config.get("deploy_fraction", 1.0) < 1.0:
        effective_quote = total_amount_quote * realism_config["deploy_fraction"]

    yaml_str = f"""###############################################
# PMM Dynamic — Optuna-Optimized Configuration
# Generated from trial #{trial.number}
# Objective value: {trial.value:.4f}
# Levels: {actual_levels}
###############################################

id: {deterministic_uuid}
controller_name: pmm_dynamic
controller_type: market_making

connector_name: {connector}
trading_pair: {trading_pair}

candles_connector: {candles_connector}
candles_trading_pair: {trading_pair}
interval: {interval}

# -- MACD (trend detection / mid-price shift) --
macd_fast: {params['macd_fast']}
macd_slow: {params['macd_slow']}
macd_signal: {params['macd_signal']}

# -- NATR (volatility-adjusted spreads) --
natr_length: {params['natr_length']}

# -- Capital --
total_amount_quote: {effective_quote}
leverage: {leverage}
position_mode: ONEWAY

# -- Order levels ({actual_levels} per side) --
buy_spreads:
{buy_spreads}
sell_spreads:
{sell_spreads}
buy_amounts_pct:
{buy_amts}
sell_amounts_pct:
{sell_amts}

# -- Risk management (triple barrier) --
stop_loss: {params['stop_loss']}
take_profit: {params['take_profit']}
time_limit: {params['time_limit_minutes'] * 60}
take_profit_order_type: LIMIT
trailing_stop:
  activation_price: {params['trailing_activation']}
  trailing_delta: {params['trailing_delta']}

# -- Execution --
executor_refresh_time: {params['refresh_minutes'] * 60}
cooldown_time: {realism_config.get("cooldown_seconds", cooldown_seconds) if realism_config else cooldown_seconds}
"""

    if walk_forward_result is not None:
        wf = walk_forward_result
        yaml_str += "\n# -- Walk-forward validation --\n"
        yaml_str += f"# median_test_sharpe: {wf['median_test_sharpe']:.4f}\n"
        yaml_str += f"# median_test_pnl_pct: {wf['median_test_pnl_pct']:.4f}\n"
        yaml_str += f"# median_test_drawdown: {wf['median_test_drawdown']:.4f}\n"
        yaml_str += f"# train_test_degradation: {wf['train_test_degradation']:.4f}\n"
        yaml_str += f"# n_profitable_windows: {wf['n_profitable_windows']}\n"
        if wf['n_profitable_windows'] < 3 or wf['median_test_sharpe'] < 0.5:
            yaml_str += "# WARN: LOW ROBUSTNESS\n"

    # Always add realism knobs as comment block (whether realism_config is passed or not)
    rc = realism_config if realism_config is not None else {}
    yaml_str += "\n# -- Backtest assumptions (live controller must enforce these exactly) --\n"
    yaml_str += f"# maker_fee: {rc.get('maker_fee', 0.001)}\n"
    yaml_str += f"# taker_fee: {rc.get('taker_fee', 0.002)}\n"
    yaml_str += f"# slippage_max_pct: {rc.get('slippage_max_pct', 0.001)}\n"
    yaml_str += f"# fill_rate_pct: {rc.get('fill_rate_pct', 0.05)}\n"
    yaml_str += f"# max_open_positions: {rc.get('max_open_positions', 4)}\n"
    yaml_str += f"# deploy_fraction: {rc.get('deploy_fraction', 0.4)}\n"
    yaml_str += f"# cooldown_seconds: {rc.get('cooldown_seconds', cooldown_seconds)}\n"
    yaml_str += f"# initial_inventory_mode: {rc.get('initial_inventory_mode', 'half_and_half')}\n"
    yaml_str += f"# timestamp_mode: {rc.get('timestamp_mode', 'unknown')}\n"
    yaml_str += f"# volume_units: {rc.get('volume_units', 'base')}\n"

    # Auto-validate YAML contract
    validation = validate_yaml_contract(yaml_str)
    if not validation["passed"]:
        import warnings
        warnings.warn(
            f"YAML contract validation FAILED: {validation['errors']}",
            UserWarning,
            stacklevel=2,
        )
    return yaml_str


def trial_to_config(trial, **kwargs) -> PMMDynamicConfig:
    """Convert an Optuna trial back into a PMMDynamicConfig for re-running."""
    p = trial.params
    n_levels = kwargs.get("n_levels", 2)

    # Detect actual levels from trial params
    actual_levels = p.get("n_levels", n_levels)
    level_keys = sorted([k for k in p if k.startswith("spread_level_")])
    if level_keys:
        actual_levels = len(level_keys)

    # Reconstruct spread lists
    buy_spreads = []
    sell_spreads = []
    for lvl in range(1, actual_levels + 1):
        key = f"spread_level_{lvl}"
        if key in p:
            buy_spreads.append(p[key])
            sell_spreads.append(p[key])

    # Reconstruct amount lists
    has_weights = any(k.startswith("amount_weight_") for k in p)
    if has_weights:
        raw_weights = []
        for lvl in range(1, actual_levels + 1):
            raw_weights.append(p.get(f"amount_weight_{lvl}", 1.0))
        total_weight = sum(raw_weights)
        buy_amounts_pct = [round(w / total_weight * 100, 2) for w in raw_weights]
        sell_amounts_pct = buy_amounts_pct[:]
    else:
        equal_pct = round(100.0 / actual_levels, 2)
        buy_amounts_pct = [equal_pct] * actual_levels
        sell_amounts_pct = [equal_pct] * actual_levels

    return PMMDynamicConfig(
        connector=kwargs.get("connector", "nonkyc"),
        trading_pair=kwargs.get("trading_pair", "BTC/USDT"),
        candles_connector=kwargs.get("candles_connector", "nonkyc"),
        candles_pair=kwargs.get("trading_pair", "BTC/USDT"),
        interval=kwargs.get("interval", "5m"),
        total_amount_quote=kwargs.get("total_amount_quote", 1000.0),
        leverage=kwargs.get("leverage", 1),
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
        maker_fee=kwargs.get("maker_fee", 0.001),
        taker_fee=kwargs.get("taker_fee", 0.002),
        entry_fee_type=kwargs.get("entry_fee_type", "maker"),
        exit_fee_type=kwargs.get("exit_fee_type", "taker"),
        intrabar_exit_mode=kwargs.get("intrabar_exit_mode", "worst_case"),
        # Realism controls (passed via kwargs from notebook config)
        compounding=kwargs.get("compounding", False),
        max_order_quote=kwargs.get("max_order_quote", 0.0),
        slippage_max_pct=kwargs.get("slippage_max_pct", 0.001),
        fill_rate_pct=kwargs.get("fill_rate_pct", 0.0),
        max_open_positions=kwargs.get("max_open_positions", 0),
        deploy_fraction=kwargs.get("deploy_fraction", 0.5),
        timestamp_mode=kwargs.get("timestamp_mode", "unknown"),
        volume_units=kwargs.get("volume_units", "base"),
        # V4 realism controls
        enforce_spread_floor=kwargs.get("enforce_spread_floor", False),
        enforce_nc_guard=kwargs.get("enforce_nc_guard", False),
        cooldown_on_stop_loss_only=kwargs.get("cooldown_on_stop_loss_only", True),
    )


# ---------------------------------------------------------------------------
# Walk-forward evaluation (Fix 11)
# ---------------------------------------------------------------------------

def walk_forward_evaluate(
    candles: pd.DataFrame,
    best_cfg: PMMDynamicConfig,
    n_windows: int = 5,
    train_pct: float = 0.7,
    overlap: bool = False,
    run_stress: bool = False,
) -> dict:
    """
    Evaluate best_cfg on N non-overlapping (or rolling) train/test windows.

    Returns dict with per-window results, median metrics, and degradation.
    """
    import statistics
    from pmm_dynamic_optimizer import PMMDynamicBacktester

    total = len(candles)
    if overlap:
        # Rolling windows
        step = max(1, (total - int(total * train_pct)) // n_windows)
        window_size = int(total * train_pct) + step
    else:
        # Non-overlapping sequential folds
        window_size = total // n_windows

    windows = []
    for w in range(n_windows):
        if overlap:
            start_idx = w * step
            end_idx = min(start_idx + window_size, total)
        else:
            start_idx = w * window_size
            end_idx = min((w + 1) * window_size, total)

        if end_idx - start_idx < 50:
            continue

        split_idx = start_idx + int((end_idx - start_idx) * train_pct)
        train_df = candles.iloc[start_idx:split_idx].reset_index(drop=True)
        test_df = candles.iloc[split_idx:end_idx].reset_index(drop=True)

        if len(train_df) < 30 or len(test_df) < 10:
            continue

        bt = PMMDynamicBacktester(best_cfg)
        train_result = bt.run(train_df)
        bt2 = PMMDynamicBacktester(best_cfg)
        test_result = bt2.run(test_df)

        # WF-1: Optional stress scenarios per fold
        stress_scores = []
        if run_stress:
            stress_results = stress_test_config(test_df, best_cfg)
            for name, sr in stress_results.items():
                if name != "_summary" and hasattr(sr, 'sharpe_ratio'):
                    stress_scores.append(sr.sharpe_ratio)

        windows.append({
            "train": train_result,
            "test": test_result,
            "stress_scores": stress_scores,
            "start": start_idx,
            "split": split_idx,
            "end": end_idx,
        })

    if not windows:
        return {"windows": [], "median_test_sharpe": -10.0, "median_test_pnl_pct": 0.0,
                "median_test_drawdown": 0.0, "train_test_degradation": 0.0, "n_profitable_windows": 0}

    test_sharpes = [w["test"].sharpe_ratio for w in windows]
    test_pnls = [w["test"].net_pnl_pct for w in windows]
    test_dds = [w["test"].max_drawdown for w in windows]
    train_sharpes = [w["train"].sharpe_ratio for w in windows]

    degradation_vals = [t - te for t, te in zip(train_sharpes, test_sharpes)]

    result = {
        "windows": windows,
        "median_test_sharpe": statistics.median(test_sharpes),
        "median_test_pnl_pct": statistics.median(test_pnls),
        "median_test_drawdown": statistics.median(test_dds),
        "train_test_degradation": statistics.median(degradation_vals),
        "n_profitable_windows": sum(1 for p in test_pnls if p > 0),
    }

    # WF-1: Add stress-aware metrics
    if run_stress:
        all_stress = [w.get("stress_scores", []) for w in windows]
        result["per_fold_stress_scores"] = all_stress

    return result


# ---------------------------------------------------------------------------
# Top-N trials reporter (Fix 13)
# ---------------------------------------------------------------------------

def get_top_n_trials(
    study,
    n: int = 10,
    candles: pd.DataFrame = None,
    **backtest_kwargs,
) -> list:
    """
    Return the top-N Optuna trials sorted by objective value.

    If candles is provided, re-evaluate each trial with the CPU backtester
    and report per-trial metrics including trades/day and drawdown.
    """
    from pmm_dynamic_optimizer import PMMDynamicBacktester

    completed = [t for t in study.trials if t.state.name == "COMPLETE" and t.value is not None]
    sorted_trials = sorted(completed, key=lambda t: t.value, reverse=True)[:n]

    results = []
    for trial in sorted_trials:
        entry = {
            "trial_number": trial.number,
            "objective_value": trial.value,
            "params": trial.params,
        }

        if candles is not None:
            try:
                cfg = trial_to_config(trial, **backtest_kwargs)
                bt = PMMDynamicBacktester(cfg)
                result = bt.run(candles)

                candle_seconds = _interval_to_seconds(backtest_kwargs.get("interval", "5m"))
                total_days = len(candles) * candle_seconds / 86400.0

                entry["sharpe_ratio"] = result.sharpe_ratio
                entry["net_pnl_pct"] = result.net_pnl_pct
                entry["max_drawdown"] = result.max_drawdown
                entry["total_trades"] = result.total_trades
                entry["trades_per_day"] = result.total_trades / max(total_days, 1.0)
                entry["profit_factor"] = result.profit_factor
                entry["win_rate"] = result.win_rate
            except Exception as e:
                entry["error"] = str(e)

        results.append(entry)

    return results


# ---------------------------------------------------------------------------
# Candle validation (BUG-2)
# ---------------------------------------------------------------------------

def validate_candles(
    df: pd.DataFrame,
    interval: str,
    max_gap_pct: float = 0.005,
    raise_on_failure: bool = True,
    strict: bool = False,
) -> dict:
    """
    Validate a candle DataFrame before backtesting.

    Checks:
      1. Required columns present: timestamp, open, high, low, close, volume
      2. Timestamps are monotonically increasing
      3. Candle spacing is consistent with `interval`
      4. No duplicate timestamps
      5. Gap rate (missing candles) is below max_gap_pct
      6. OHLC sanity: low <= min(open,close), high >= max(open,close), all > 0
      7. Warns about timestamp semantics (open-time vs close-time)

    Returns
    -------
    dict with keys: n_candles, n_duplicates, gap_pct, longest_gap_candles,
                    ohlc_violations, warnings, passed
    """
    result = {
        "n_candles": len(df),
        "n_duplicates": 0,
        "gap_pct": 0.0,
        "longest_gap_candles": 0,
        "ohlc_violations": 0,
        "warnings": [],
        "passed": True,
    }

    required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        msg = f"Missing required columns: {missing_cols}"
        result["warnings"].append(msg)
        result["passed"] = False
        if raise_on_failure:
            raise ValueError(msg)
        return result

    if len(df) < 2:
        result["warnings"].append("Fewer than 2 candles — cannot validate spacing.")
        result["passed"] = False
        return result

    # 1. Monotonic timestamps
    ts = pd.to_datetime(df["timestamp"], utc=True) if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]) else df["timestamp"]
    if not ts.is_monotonic_increasing:
        msg = "Timestamps are NOT monotonically increasing."
        result["warnings"].append(msg)
        result["passed"] = False
        if raise_on_failure:
            raise ValueError(msg)

    # 2. Duplicates
    n_dup = int(ts.duplicated().sum())
    result["n_duplicates"] = n_dup
    if n_dup > 0:
        msg = f"{n_dup} duplicate timestamps found."
        result["warnings"].append(msg)
        result["passed"] = False
        if strict:
            raise ValueError(f"STRICT: {msg}")
        if raise_on_failure:
            raise ValueError(msg)

    # 3. Spacing
    candle_secs = _interval_to_seconds(interval)
    diffs = ts.diff().dropna().dt.total_seconds()
    expected_gaps = (diffs / candle_secs).round().astype(int)  # 1 = normal, >1 = gap
    n_gaps = int((expected_gaps > 1).sum())
    missing_candles = int((expected_gaps - 1).clip(lower=0).sum())
    expected_total = int(expected_gaps.sum()) + 1
    gap_pct = missing_candles / max(expected_total, 1)
    longest_gap = int(expected_gaps.max()) - 1
    result["gap_pct"] = round(gap_pct, 6)
    result["longest_gap_candles"] = longest_gap

    if gap_pct > max_gap_pct:
        msg = (f"Gap rate {gap_pct:.2%} exceeds threshold {max_gap_pct:.2%}. "
               f"Missing ~{missing_candles} candles out of ~{expected_total}.")
        result["warnings"].append(msg)
        result["passed"] = False
        if strict:
            raise ValueError(f"STRICT: {msg}")
        if raise_on_failure:
            raise ValueError(msg)
    elif n_gaps > 0:
        result["warnings"].append(
            f"{n_gaps} gaps found (longest={longest_gap} candles); gap rate {gap_pct:.4%} within threshold."
        )

    # 4. OHLC sanity
    ohlc_ok = (
        (df["low"]  <= df[["open", "close"]].min(axis=1) + 1e-10) &
        (df["high"] >= df[["open", "close"]].max(axis=1) - 1e-10) &
        (df["low"]  > 0) &
        (df["high"] > 0) &
        (df["close"] > 0)
    )
    n_violations = int((~ohlc_ok).sum())
    result["ohlc_violations"] = n_violations
    if n_violations > 0:
        msg = f"{n_violations} rows violate OHLC sanity (low > min(O,C) or high < max(O,C) or non-positive price)."
        result["warnings"].append(msg)
        # FIX-2: In strict mode, OHLC violations > 1% of rows are hard failures
        if strict and n_violations > len(df) * 0.01:
            raise ValueError(f"STRICT: {msg}")

    # 5. Timestamp semantics warning — ALWAYS emit this
    result["warnings"].append(
        "TIMESTAMP SEMANTICS: Cannot auto-detect whether timestamps are "
        "OPEN-TIME or CLOSE-TIME. "
        "Set timestamp_mode='close' ONLY if you have confirmed your data source timestamps "
        "represent candle CLOSE times. Most exchanges (including NonKYC.io) use OPEN times. "
        "When in doubt, use timestamp_mode='open' (conservative, no look-ahead)."
    )

    # 6. Volume units heuristic — warn if volume might already be in quote units
    if "volume" in df.columns and "close" in df.columns:
        med_vol = float(df["volume"].median())
        med_close = float(df["close"].median())
        if med_vol > 0 and med_close > 0:
            implied_quote_vol = med_vol * med_close
            if implied_quote_vol > 1e12:
                result["warnings"].append(
                    f"VOLUME UNITS: median(volume) * median(close) = {implied_quote_vol:.2e} > 1e12. "
                    "Volume may already be in QUOTE units. "
                    "Set volume_units='quote' in your config if so, otherwise the fill-rate gate "
                    "will be wrong by a factor of price."
                )

    return result


# ---------------------------------------------------------------------------
# YAML contract validator (ADD-2)
# ---------------------------------------------------------------------------

def validate_yaml_contract(yaml_str: str) -> dict:
    """
    Validate an exported controller YAML against the parameter output contract.

    Returns dict with keys: passed (bool), errors (list[str]), warnings (list[str]).
    """
    try:
        import yaml as _yaml
    except ImportError:
        raise ImportError("pyyaml required: pip install pyyaml")

    data = _yaml.safe_load(yaml_str)
    errors = []
    warnings_list = []

    def _check(cond, msg, is_error=True):
        if not cond:
            (errors if is_error else warnings_list).append(msg)

    # Required top-level keys
    for key in ("id", "controller_name", "controller_type", "connector_name",
                "trading_pair", "candles_connector", "candles_trading_pair",
                "interval", "macd_fast", "macd_slow", "macd_signal",
                "natr_length", "total_amount_quote", "leverage",
                "position_mode", "take_profit_order_type",
                "buy_spreads", "sell_spreads", "buy_amounts_pct", "sell_amounts_pct",
                "stop_loss", "take_profit", "time_limit", "trailing_stop",
                "executor_refresh_time", "cooldown_time"):
        _check(key in data, f"Missing required key: '{key}'")

    if not errors:
        # Structural constraints
        _check(data.get("controller_name") == "pmm_dynamic",
               f"controller_name must be 'pmm_dynamic', got '{data.get('controller_name')}'")
        _check(data.get("macd_fast", 99) < data.get("macd_slow", 0),
               "macd_fast must be < macd_slow")

        buy_s  = data.get("buy_spreads",  [])
        sell_s = data.get("sell_spreads", [])
        buy_a  = data.get("buy_amounts_pct",  [])
        sell_a = data.get("sell_amounts_pct", [])

        _check(len(buy_s) == len(sell_s) == len(buy_a) == len(sell_a),
               f"Spread/amount list lengths mismatch: {len(buy_s)},{len(sell_s)},{len(buy_a)},{len(sell_a)}")
        _check(buy_s  == sorted(buy_s),  "buy_spreads must be strictly increasing")
        _check(sell_s == sorted(sell_s), "sell_spreads must be strictly increasing")
        _check(abs(sum(buy_a)  - 100.0) < 0.5, f"buy_amounts_pct sum={sum(buy_a):.2f} (expected ~100)")
        _check(abs(sum(sell_a) - 100.0) < 0.5, f"sell_amounts_pct sum={sum(sell_a):.2f} (expected ~100)")

        ts = data.get("trailing_stop", {})
        act   = ts.get("activation_price", 0)
        delta = ts.get("trailing_delta",   0)
        _check(delta < act,
               f"trailing_delta ({delta}) must be < activation_price ({act})")

        # NaN/inf check on numerics
        for key in ("stop_loss", "take_profit", "total_amount_quote"):
            val = data.get(key, None)
            if val is not None:
                _check(math.isfinite(val), f"{key}={val} is not finite")

    # V3: Check that volume_units and timestamp_mode are documented in the YAML
    # These live in the comment block, so check the raw string
    _check("timestamp_mode" in yaml_str,
           "YAML should document timestamp_mode (in comment block)", is_error=False)
    _check("volume_units" in yaml_str,
           "YAML should document volume_units (in comment block)", is_error=False)

    return {"passed": len(errors) == 0, "errors": errors, "warnings": warnings_list}


# ---------------------------------------------------------------------------
# Stress test helper (ADD-3)
# ---------------------------------------------------------------------------

def stress_test_config(
    candles: pd.DataFrame,
    cfg: "PMMDynamicConfig",
    scenarios: list = None,
) -> dict:
    """
    Run a set of stress scenarios on a PMMDynamicConfig and report results.

    Default scenarios:
      - baseline: as-is
      - fees_plus50: maker_fee * 1.5, taker_fee * 1.5
      - slippage_x2: slippage_max_pct * 2
      - fill_rate_half: fill_rate_pct * 0.5 (if > 0, else skip)
      - latency_taker: maker_validity_check=True (forces taker on crosses)

    Returns dict: scenario_name -> BacktestResult.
    """
    from dataclasses import replace as dc_replace
    try:
        from pmm_dynamic_optimizer import PMMDynamicBacktester
    except ImportError:
        raise ImportError("pmm_dynamic_optimizer must be importable")

    if scenarios is None:
        scenarios = [
            ("baseline",       {}),
            ("fees_plus50",    {"maker_fee": cfg.maker_fee * 1.5,
                                "taker_fee": cfg.taker_fee * 1.5}),
            ("slippage_x2",    {"slippage_max_pct": cfg.slippage_max_pct * 2}),
            ("fill_rate_half", {"fill_rate_pct": cfg.fill_rate_pct * 0.5}
                               if cfg.fill_rate_pct > 0 else None),
            ("latency_taker",  {"maker_validity_check": True}),
        ]

    results = {}
    for name, overrides in scenarios:
        if overrides is None:
            continue
        stressed_cfg = dc_replace(cfg, **overrides)
        try:
            bt = PMMDynamicBacktester(stressed_cfg)
            results[name] = bt.run(candles)
        except Exception as e:
            log.warning("Stress scenario '%s' failed: %s", name, e)
            results[name] = BacktestResult.empty()

    # Acceptance summary
    n_profitable = sum(1 for r in results.values() if hasattr(r, 'net_pnl_pct') and r.net_pnl_pct > 0)
    results["_summary"] = {
        "n_scenarios": len(results) - 1 if "_summary" not in results else len(results),
        "n_profitable": n_profitable,
        "passed": n_profitable >= max(1, len(results) // 2),
    }
    return results


__all__ = [
    # MongoDB helpers
    "get_mongo_client",
    "load_candles",
    # Indicators
    "compute_macd",
    "compute_natr",
    "_auto_spread_min_multiplier",
    # Config and data models
    "PMMDynamicConfig",
    "PendingOrder",
    "Position",
    "BacktestResult",
    # Helper functions
    "_position_pnl",
    "_position_pnl_pct",
    "_close_position",
    "_interval_to_seconds",
    # Optuna utilities
    "_suggest_params",
    "_compute_objective",
    "compute_robust_score",
    "compute_enhanced_objective",
    "compute_robust_wf_objective",
    # Export utilities
    "trial_to_controller_yaml",
    "trial_to_config",
    # Validation
    "validate_candles",
    "validate_yaml_contract",
    # Analysis
    "walk_forward_evaluate",
    "get_top_n_trials",
    # Stress testing
    "stress_test_config",
    # Sensitivity analysis
    "parameter_sensitivity_check",
]
