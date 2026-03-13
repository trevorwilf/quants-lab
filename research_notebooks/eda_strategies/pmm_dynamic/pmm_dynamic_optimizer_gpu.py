"""
pmm_dynamic_optimizer_gpu.py — GPU-accelerated PMM Dynamic backtester.

GPU-specific components: CUDA kernel, parameter packing, gpu_backtest_single,
create_objective_gpu, and assert_cpu_gpu_parity.
All shared logic lives in pmm_dynamic_core.py.

Uses Numba CUDA for the simulation kernel. CuPy is optional; by default we use Numba device arrays for transfers/allocations for maximum compatibility.
Falls back to the CPU backtester (pmm_dynamic_optimizer.py) if GPU is unavailable.

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

import logging
import math
import os
from typing import Any, Dict, List, Optional

import numpy as np

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
    compute_natr,
    trial_to_controller_yaml,
    trial_to_config,
    walk_forward_evaluate,
    get_top_n_trials,
    load_candles,
    validate_candles,
)

# CPU backtester needed for GPU-unavailable fallback path only
from pmm_dynamic_optimizer import PMMDynamicBacktester, create_objective

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Re-exports — maintained for backward compatibility.
# ---------------------------------------------------------------------------
__all__ = [
    # GPU-specific
    "gpu_available",
    "get_gpu_info",
    "get_gpu_backend",
    "prepare_candles_gpu",
    "gpu_backtest_single",
    "create_objective_gpu",
    "assert_cpu_gpu_parity",
    # Re-exported from core
    "PMMDynamicConfig",
    "BacktestResult",
    "_suggest_params",
    "_compute_objective",
    "_interval_to_seconds",
    "trial_to_controller_yaml",
    "trial_to_config",
    "walk_forward_evaluate",
    "get_top_n_trials",
    "load_candles",
    "compute_natr",
]

# ---------------------------------------------------------------------------
# GPU detection
# ---------------------------------------------------------------------------

# NOTE: This module intentionally does NOT require CuPy. CuPy is optional.
# The only hard dependency for the GPU path is `numba.cuda`.
#
# For CPU-only machines, you can run the GPU path deterministically via:
#   NUMBA_ENABLE_CUDASIM=1
#
# This is critical for CI and for CPU/GPU parity debugging.

_HAS_CUDA = False
_HAS_CUPY = False
_GPU_OK = False

try:
    from numba import cuda  # type: ignore
    _HAS_CUDA = True
    # In NUMBA_ENABLE_CUDASIM=1 mode, cuda.is_available() returns True even on CPU-only machines.
    _GPU_OK = bool(cuda.is_available())
except Exception:  # pragma: no cover
    cuda = None  # type: ignore
    _HAS_CUDA = False
    _GPU_OK = False

try:
    import cupy as cp  # type: ignore
    _HAS_CUPY = True
except Exception:  # pragma: no cover
    cp = None  # type: ignore
    _HAS_CUPY = False

# ---------------------------------------------------------------------------
# Backend selection (CuPy vs Numba device arrays)
# ---------------------------------------------------------------------------

_GPU_BACKEND = os.environ.get("PMM_DYNAMIC_GPU_BACKEND", "numba").strip().lower()
if _GPU_BACKEND not in ("numba", "cupy"):
    log.warning("Unknown PMM_DYNAMIC_GPU_BACKEND=%r; falling back to 'numba'.", _GPU_BACKEND)
    _GPU_BACKEND = "numba"

# Default to Numba device arrays for maximum compatibility/determinism.
# Use CuPy only when explicitly requested via PMM_DYNAMIC_GPU_BACKEND='cupy'.
_USE_CUPY = bool(_GPU_BACKEND == "cupy" and _HAS_CUPY and cp is not None)
if _GPU_BACKEND == "cupy" and not _USE_CUPY and _GPU_OK:
    log.warning("PMM_DYNAMIC_GPU_BACKEND='cupy' requested but CuPy is unavailable; using Numba device arrays.")



def _device_zeros(shape, dtype=np.float64):
    """Allocate a zero-initialized device array (real CUDA, CuPy, or CUDASIM)."""
    if not _GPU_OK:
        raise RuntimeError("GPU not available")
    if _USE_CUPY:
        return cp.zeros(shape, dtype=dtype)
    return cuda.to_device(np.zeros(shape, dtype=dtype))


def _to_device(arr: np.ndarray, dtype=None):
    """Transfer a NumPy array to device memory."""
    if not _GPU_OK:
        raise RuntimeError("GPU not available")
    if dtype is not None:
        arr = np.asarray(arr, dtype=dtype)
    else:
        arr = np.asarray(arr)
    if _USE_CUPY:
        return cp.asarray(arr)
    return cuda.to_device(arr)


def _to_host(arr):
    """Transfer a device array back to host as NumPy."""
    if _USE_CUPY and cp is not None and isinstance(arr, cp.ndarray):
        return cp.asnumpy(arr)
    if hasattr(arr, "copy_to_host"):
        return arr.copy_to_host()
    return np.asarray(arr)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_THREADS_PER_BLOCK = 256
_MAX_LEVELS = 10

# ---------------------------------------------------------------------------
# Public GPU helpers
# ---------------------------------------------------------------------------


def gpu_available() -> bool:
    """Return True if a CUDA GPU is available and all libraries are installed."""
    return _GPU_OK



def get_gpu_backend() -> str:
    """Return the active GPU array backend: 'numba', 'cupy', or 'none'."""
    if not _GPU_OK:
        return "none"
    return "cupy" if _USE_CUPY else "numba"

def get_gpu_info() -> dict:
    """Return GPU device information or empty dict if unavailable."""
    if not _GPU_OK or not _HAS_CUDA:
        return {}
    try:
        dev = cuda.current_context().device  # type: ignore[attr-defined]
    except Exception:
        return {}

    info: dict = {
        "name": getattr(dev, "name", None) or str(dev),
        "compute_capability": getattr(dev, "compute_capability", None),
    }
    info["backend"] = get_gpu_backend()

    # `TOTAL_GLOBAL_MEM` is available on real devices; simulator may not expose it.
    total_mem = getattr(dev, "TOTAL_GLOBAL_MEM", None)
    if isinstance(total_mem, (int, float)) and total_mem:
        info["total_memory_mb"] = float(total_mem) / (1024.0 * 1024.0)

    return info


def prepare_candles_gpu(candles_df, interval: str = "5m", dtype: str = "float64"):
    """
    Upload candle OHLCV data to device memory.

    Returns a dict of device arrays ready for kernel consumption.

    Notes
    -----
    * Works on real CUDA GPUs.
    * Works on CPU-only machines when running with NUMBA_ENABLE_CUDASIM=1.
    * Backend defaults to Numba device arrays. Set PMM_DYNAMIC_GPU_BACKEND='cupy' to use CuPy.
    """
    if not _GPU_OK:
        raise RuntimeError("GPU not available")

    dt = np.float32 if dtype == "float32" else np.float64

    # FIX: Sort BEFORE extracting any columns to prevent timestamp-OHLCV misalignment
    try:
        candles_df = candles_df.sort_values("timestamp").reset_index(drop=True)
    except Exception:
        pass

    ts_vals = candles_df["timestamp"].values.astype("int64") // 10**9
    ts_vals = ts_vals.astype(np.float64)

    # Volume array for deterministic fill-rate gate
    if "volume" in candles_df.columns:
        vol_col = np.asarray(candles_df["volume"].values, dtype=dt)
    else:
        vol_col = np.zeros(len(candles_df), dtype=dt)

    open_col = candles_df["open"].values if "open" in candles_df.columns else candles_df["close"].values

    # Force contiguous host buffers before upload (important when mixing pandas/numpy backends)
    open_arr = np.ascontiguousarray(np.asarray(open_col, dtype=dt))
    high_arr = np.ascontiguousarray(np.asarray(candles_df["high"].values, dtype=dt))
    low_arr = np.ascontiguousarray(np.asarray(candles_df["low"].values, dtype=dt))
    close_arr = np.ascontiguousarray(np.asarray(candles_df["close"].values, dtype=dt))
    vol_arr = np.ascontiguousarray(vol_col)
    ts_arr = np.ascontiguousarray(ts_vals, dtype=np.float64)

    return {
        "open": _to_device(open_arr),
        "high": _to_device(high_arr),
        "low": _to_device(low_arr),
        "close": _to_device(close_arr),
        "volume": _to_device(vol_arr),
        "timestamps": _to_device(ts_arr, dtype=np.float64),
        "n_candles": int(len(candles_df)),
        "candle_seconds": int(_interval_to_seconds(interval)),
    }



# ---------------------------------------------------------------------------
# CUDA kernel — single kernel, indicators computed inline
# ---------------------------------------------------------------------------

if _HAS_CUDA:
    from numba import float64 as numba_float64
    from numba import int32 as numba_int32

    @cuda.jit
    def _simulate_kernel(
        # Candle arrays (1-D, length = n_candles) — shared across all threads
        open_arr, close, high, low, volume, timestamps,
        n_candles, candle_secs,
        # Per-param-set arrays (1-D, length = n_sets)
        p_macd_fast, p_macd_slow, p_macd_signal, p_natr_length,
        p_spread_levels,      # 2-D: (n_sets, _MAX_LEVELS)
        p_n_levels,
        p_amount_pcts,        # 2-D: (n_sets, _MAX_LEVELS)
        p_stop_loss, p_take_profit, p_time_limit_s,
        p_trailing_act, p_trailing_delta,
        p_refresh_s,
        p_entry_fee, p_exit_fee,
        p_capital, p_initial_capital,
        p_deploy_frac, p_compounding_flag,
        p_max_order_quote, p_slippage_avg,
        p_max_open_pos, p_fill_rate,
        p_cooldown_s,
        p_min_spread_floor,
        p_init_base,          # FIX-4: initial base balance
        p_maker_validity,     # FIX-5: maker validity check (0/1)
        p_taker_fee_entry,    # FIX-5: taker fee for entry when maker validity fails
        p_timestamp_shift,    # BUG-3 V3: signal shift (0=close, 1=open/unknown)
        p_volume_is_quote,    # FIX-3 V3: volume units flag (1=quote, 0=base)
        p_enforce_spread_floor,  # BUG-5: 0.0 or 1.0
        p_enforce_nc_guard,      # BUG-5: 0.0 or 1.0
        p_cooldown_sl_only,      # ADD-2: cooldown on stop_loss only (0.0 or 1.0)
        p_exit_fee_tp,           # FIX-5: maker fee for take-profit exits
        p_latency_candles,       # FIX-9: minimum age (in candles) before a new order can fill
        n_sets,
        # Output arrays (1-D, length = n_sets)
        out_sharpe, out_pnl_pct, out_max_dd, out_n_trades,
        out_gross_win, out_gross_loss,
        out_final_balance,    # BUG-4 V3: final balance output
    ):
        tid = cuda.grid(1)
        if tid >= n_sets:
            return

        # ── Read parameters for this thread ──
        fast = int(p_macd_fast[tid])
        slow = int(p_macd_slow[tid])
        sig = int(p_macd_signal[tid])
        nlen = int(p_natr_length[tid])

        n_lvl = int(p_n_levels[tid])
        stop_loss = p_stop_loss[tid]
        take_profit = p_take_profit[tid]
        time_limit_s = p_time_limit_s[tid]
        trailing_act = p_trailing_act[tid]
        trailing_delta = p_trailing_delta[tid]
        refresh_s = p_refresh_s[tid]
        entry_fee = p_entry_fee[tid]
        exit_fee = p_exit_fee[tid]
        balance = p_capital[tid]
        init_capital = p_initial_capital[tid]
        deploy_frac = p_deploy_frac[tid]
        compounding_on = p_compounding_flag[tid]
        max_order_q = p_max_order_quote[tid]
        slip = p_slippage_avg[tid]
        max_open = int(p_max_open_pos[tid])
        fill_rate_pct = p_fill_rate[tid]
        cooldown_s = p_cooldown_s[tid]
        min_spread_floor = p_min_spread_floor[tid]
        maker_validity = int(p_maker_validity[tid])
        taker_fee_entry = p_taker_fee_entry[tid]
        timestamp_shift = int(p_timestamp_shift[tid])
        volume_is_quote = p_volume_is_quote[tid]
        enforce_spread_floor = p_enforce_spread_floor[tid]
        enforce_nc_guard = p_enforce_nc_guard[tid]
        cooldown_sl_only = p_cooldown_sl_only[tid]
        exit_fee_tp = p_exit_fee_tp[tid]
        latency_candles = int(p_latency_candles[tid])
        latency_s = float(latency_candles) * float(candle_secs)

        # Spread/amount levels (read into registers)
        sp_lvl = cuda.local.array(10, dtype=numba_float64)
        amt_pct = cuda.local.array(10, dtype=numba_float64)
        for lv in range(10):
            sp_lvl[lv] = p_spread_levels[tid, lv]
            amt_pct[lv] = p_amount_pcts[tid, lv]

        # ── Position arrays (64 slots) ──
        pos_active = cuda.local.array(64, dtype=numba_int32)
        pos_side = cuda.local.array(64, dtype=numba_int32)       # 1=buy, -1=sell
        pos_entry_price = cuda.local.array(64, dtype=numba_float64)
        pos_amount = cuda.local.array(64, dtype=numba_float64)
        pos_entry_quote = cuda.local.array(64, dtype=numba_float64)
        pos_entry_fee_paid = cuda.local.array(64, dtype=numba_float64)
        pos_entry_time = cuda.local.array(64, dtype=numba_float64)
        pos_peak_pnl = cuda.local.array(64, dtype=numba_float64)
        pos_trailing = cuda.local.array(64, dtype=numba_int32)
        for j in range(64):
            pos_active[j] = 0
            pos_side[j] = 0
            pos_entry_price[j] = 0.0
            pos_amount[j] = 0.0
            pos_entry_quote[j] = 0.0
            pos_entry_fee_paid[j] = 0.0
            pos_entry_time[j] = 0.0
            pos_peak_pnl[j] = 0.0
            pos_trailing[j] = 0

        # ── Pending order arrays (20 slots) ──
        pend_active = cuda.local.array(20, dtype=numba_int32)
        pend_side = cuda.local.array(20, dtype=numba_int32)      # 1=buy, -1=sell
        pend_price = cuda.local.array(20, dtype=numba_float64)
        pend_amt = cuda.local.array(20, dtype=numba_float64)
        pend_quote = cuda.local.array(20, dtype=numba_float64)   # quote reserved (buy)
        pend_placed = cuda.local.array(20, dtype=numba_float64)
        pend_expires = cuda.local.array(20, dtype=numba_float64)
        pend_base_reserved = cuda.local.array(20, dtype=numba_float64)  # FIX-3
        for j in range(20):
            pend_active[j] = 0
            pend_base_reserved[j] = 0.0

        # ── Simulation state ──
        # FIX-4: Starting inventory from p_init_base (set by caller based on initial_inventory_mode)
        base_bal = p_init_base[tid]
        peak_equity = init_capital
        max_dd = 0.0
        n_trades = 0
        gross_win = 0.0
        gross_loss = 0.0
        last_refresh_time = 0.0
        last_close_time = 0.0

        # ── Indicator state ──
        alpha_f = 2.0 / (fast + 1.0)
        alpha_s = 2.0 / (slow + 1.0)
        alpha_sig = 2.0 / (sig + 1.0)
        alpha_n = 2.0 / (nlen + 1.0)

        ema_f = float(close[0])
        ema_s = float(close[0])
        ema_signal = 0.0
        atr_val = 0.0
        prev_c = float(close[0])

        # BUG-4 FIX: Ring buffer for windowed MACD z-score (replaces expanding accumulators)
        z_window = int(max(fast, slow, sig, nlen)) + 100
        z_buf_size = min(z_window, 256)  # cap at local array limit
        macd_ring = cuda.local.array(256, dtype=numba_float64)
        for _ri in range(256):
            macd_ring[_ri] = 0.0
        macd_ring_idx = 0
        macd_ring_count = 0

        # Online Sharpe accumulators
        prev_equity = init_capital
        ret_sum = 0.0
        ret_sum_sq = 0.0
        ret_count = 0
        first_equity_set = 0  # FIX-7B: skip first return to match CPU pct_change().dropna()

        # Rule K-1: Warmup
        warmup = z_window

        # Pre-initialize all variables that are assigned only inside the i>0 else-branch.
        # Numba CUDA JIT requires every variable to have a definite assignment path visible
        # at compile time — without these, the kernel silently returns zeros for all outputs.
        natr = 0.0
        ref_price = float(close[0])
        sp_mult = 0.0
        macd_line = 0.0
        hist = 0.0
        macd_zscore = 0.0
        macdh_sign = 1.0
        price_signal = 0.0

        # BUG-3 V3: Previous candle signals for timestamp shift
        prev_natr = 0.0
        prev_price_signal = 0.0

        for i in range(n_candles):
            c = float(close[i])
            h = float(high[i])
            lo = float(low[i])
            vol = float(volume[i])
            ts = float(timestamps[i])
            # ── Rule K-2: Update indicators ──
            if i == 0:
                ema_f = c
                ema_s = c
                macd_line = 0.0
                ema_signal = 0.0
                hist = 0.0

                # ATR seed (same as CPU: first TR)
                atr_val = h - lo if h > lo else 0.0
                natr = atr_val / c if c > 0.0 else 0.0

                # Seed ring buffer with MACD line at i=0 (CPU has macd_line[0] == 0)
                ring_pos = macd_ring_idx % z_buf_size
                macd_ring[ring_pos] = macd_line
                macd_ring_idx += 1
                macd_ring_count = min(macd_ring_count + 1, z_buf_size)

                macd_zscore = 0.0
                macdh_sign = -1.0
                price_signal = 0.5 * macd_zscore + 0.5 * macdh_sign
                ref_price = c * (1.0 + price_signal * natr / 2.0)
                sp_mult = natr

                prev_c = c
            else:
                ema_f = ema_f + alpha_f * (c - ema_f)
                ema_s = ema_s + alpha_s * (c - ema_s)
                macd_line = ema_f - ema_s
                ema_signal = ema_signal + alpha_sig * (macd_line - ema_signal)
                hist = macd_line - ema_signal

                # ATR (EMA-based, same formula as CPU compute_natr)
                tr1 = h - lo
                tr2 = h - prev_c
                if tr2 < 0.0:
                    tr2 = -tr2
                tr3 = lo - prev_c
                if tr3 < 0.0:
                    tr3 = -tr3
                tr = tr1
                if tr2 > tr:
                    tr = tr2
                if tr3 > tr:
                    tr = tr3
                atr_val = atr_val + alpha_n * (tr - atr_val)
                natr = atr_val / c if c > 0.0 else 0.0

                # Windowed z-score via ring buffer (matches CPU rolling window)
                ring_pos = macd_ring_idx % z_buf_size
                macd_ring[ring_pos] = macd_line
                macd_ring_idx += 1
                macd_ring_count = min(macd_ring_count + 1, z_buf_size)

                macd_zscore = 0.0
                if macd_ring_count >= 20:
                    # Two-pass variance (numerically stable — matches CPU pandas rolling)
                    # Pass 1: compute mean
                    ring_sum = 0.0
                    for rr in range(macd_ring_count):
                        ring_sum += macd_ring[rr]
                    mean_m = ring_sum / macd_ring_count
                    # Pass 2: compute sum of squared deviations from mean
                    ss = 0.0
                    for rr in range(macd_ring_count):
                        d = macd_ring[rr] - mean_m
                        ss += d * d
                    # Bessel correction (ddof=1) — sample variance
                    if macd_ring_count > 1:
                        var_m = ss / (macd_ring_count - 1)
                    else:
                        var_m = 0.0
                    # Guard: clamp to zero (belt-and-suspenders for float rounding)
                    if var_m < 0.0:
                        var_m = 0.0
                    std_m = math.sqrt(var_m) if var_m > 0.0 else 1.0
                    macd_zscore = -(macd_line - mean_m) / std_m

                macdh_sign = 1.0 if hist > 0.0 else -1.0
                price_signal = 0.5 * macd_zscore + 0.5 * macdh_sign
                ref_price = c * (1.0 + price_signal * natr / 2.0)
                sp_mult = natr

                prev_c = c

            # Determine which signals to use for order placement.
            #
            # Important: to match the CPU backtester semantics, `timestamp_shift=1`
            # shifts the *indicators/signals* by one candle, but still uses the
            # current candle's mid-price `c` as the reference base price.
            order_natr = natr
            order_price_signal = price_signal
            if timestamp_shift == 1:
                order_natr = prev_natr
                order_price_signal = prev_price_signal

            order_ref_price = c * (1.0 + order_price_signal * order_natr / 2.0)
            order_sp_mult = order_natr

            # Skip warmup candles — indicators only (match CPU: no DD/Sharpe tracking before warmup)
            if i < warmup:
                # Update shift caches during warmup so timestamp_shift=1 works
                prev_natr = natr
                prev_price_signal = price_signal
                continue


            # ════════════════════════════════════════════════════════════
            for j in range(64):
                if pos_active[j] == 0:
                    continue

                side = pos_side[j]
                ep = pos_entry_price[j]
                amt = pos_amount[j]

                # Update peak PnL from intrabar extremes
                if side == 1:
                    best_price = h
                    worst_price = lo
                else:
                    best_price = lo
                    worst_price = h

                if ep > 0.0:
                    if side == 1:
                        best_pnl = (best_price - ep) / ep
                        worst_pnl = (worst_price - ep) / ep
                    else:
                        best_pnl = (ep - best_price) / ep
                        worst_pnl = (ep - worst_price) / ep
                else:
                    best_pnl = 0.0
                    worst_pnl = 0.0

                if best_pnl > pos_peak_pnl[j]:
                    pos_peak_pnl[j] = best_pnl

                # Trailing stop activation
                if pos_trailing[j] == 0 and best_pnl >= trailing_act:
                    pos_trailing[j] = 1

                # ── Worst-case exit order: stop_loss first, then take_profit ──
                closed = False

                # Stop loss check
                if worst_pnl <= -stop_loss:
                    if side == 1:
                        exit_p = ep * (1.0 - stop_loss)
                    else:
                        exit_p = ep * (1.0 + stop_loss)
                    # Apply slippage to exit
                    if side == 1:
                        exit_p = exit_p * (1.0 - slip)
                    else:
                        exit_p = exit_p * (1.0 + slip)
                    # Close position
                    exit_notional = amt * exit_p
                    ex_fee = exit_notional * exit_fee
                    if side == 1:
                        balance += exit_notional - ex_fee
                        base_bal -= amt
                    else:
                        balance -= exit_notional + ex_fee
                        base_bal += amt
                    # PnL tracking
                    if side == 1:
                        pnl = amt * (exit_p - ep) - (pos_entry_fee_paid[j]) - ex_fee
                    else:
                        pnl = amt * (ep - exit_p) - (pos_entry_fee_paid[j]) - ex_fee
                    if pnl > 0.0:
                        gross_win += pnl
                    else:
                        gross_loss += (-pnl)
                    n_trades += 1
                    pos_active[j] = 0
                    # ADD-2: SL always triggers cooldown
                    last_close_time = ts
                    closed = True

                # Take profit check
                if not closed and best_pnl >= take_profit:
                    if side == 1:
                        exit_p = ep * (1.0 + take_profit)
                    else:
                        exit_p = ep * (1.0 - take_profit)
                    # ADD-3: TP is LIMIT order — NO slippage
                    # FIX-5: TP uses maker fee
                    exit_notional = amt * exit_p
                    ex_fee = exit_notional * exit_fee_tp
                    if side == 1:
                        balance += exit_notional - ex_fee
                        base_bal -= amt
                    else:
                        balance -= exit_notional + ex_fee
                        base_bal += amt
                    if side == 1:
                        pnl = amt * (exit_p - ep) - (pos_entry_fee_paid[j]) - ex_fee
                    else:
                        pnl = amt * (ep - exit_p) - (pos_entry_fee_paid[j]) - ex_fee
                    if pnl > 0.0:
                        gross_win += pnl
                    else:
                        gross_loss += (-pnl)
                    n_trades += 1
                    pos_active[j] = 0
                    # ADD-2: TP does NOT trigger cooldown
                    if cooldown_sl_only < 0.5:
                        last_close_time = ts
                    closed = True

                # Trailing stop check
                if not closed and pos_trailing[j] == 1:
                    if ep > 0.0:
                        if side == 1:
                            close_pnl = (c - ep) / ep
                        else:
                            close_pnl = (ep - c) / ep
                    else:
                        close_pnl = 0.0
                    drawback = pos_peak_pnl[j] - close_pnl
                    if drawback >= trailing_delta:
                        if side == 1:
                            trail_p = ep * (1.0 + pos_peak_pnl[j] - trailing_delta)
                        else:
                            trail_p = ep * (1.0 - pos_peak_pnl[j] + trailing_delta)
                        if side == 1:
                            trail_p = trail_p * (1.0 - slip)
                        else:
                            trail_p = trail_p * (1.0 + slip)
                        exit_notional = amt * trail_p
                        ex_fee = exit_notional * exit_fee
                        if side == 1:
                            balance += exit_notional - ex_fee
                            base_bal -= amt
                        else:
                            balance -= exit_notional + ex_fee
                            base_bal += amt
                        if side == 1:
                            pnl = amt * (trail_p - ep) - (pos_entry_fee_paid[j]) - ex_fee
                        else:
                            pnl = amt * (ep - trail_p) - (pos_entry_fee_paid[j]) - ex_fee
                        if pnl > 0.0:
                            gross_win += pnl
                        else:
                            gross_loss += (-pnl)
                        n_trades += 1
                        pos_active[j] = 0
                        # ADD-2: Trailing stop cooldown based on config
                        if cooldown_sl_only < 0.5:
                            last_close_time = ts
                        closed = True

                # Time limit check
                if not closed and time_limit_s > 0.0:
                    if (ts - pos_entry_time[j]) >= time_limit_s:
                        exit_p = c
                        if side == 1:
                            exit_p = exit_p * (1.0 - slip)
                        else:
                            exit_p = exit_p * (1.0 + slip)
                        exit_notional = amt * exit_p
                        ex_fee = exit_notional * exit_fee
                        if side == 1:
                            balance += exit_notional - ex_fee
                            base_bal -= amt
                        else:
                            balance -= exit_notional + ex_fee
                            base_bal += amt
                        if side == 1:
                            pnl = amt * (exit_p - ep) - (pos_entry_fee_paid[j]) - ex_fee
                        else:
                            pnl = amt * (ep - exit_p) - (pos_entry_fee_paid[j]) - ex_fee
                        if pnl > 0.0:
                            gross_win += pnl
                        else:
                            gross_loss += (-pnl)
                        n_trades += 1
                        pos_active[j] = 0
                        # ADD-2: Time limit cooldown based on config
                        if cooldown_sl_only < 0.5:
                            last_close_time = ts
                        closed = True

            # ════════════════════════════════════════════════════════════
            # STEP 2: Check fills on PENDING ORDERS
            # ════════════════════════════════════════════════════════════
            # FIX-3 V3: Volume units handling
            if volume_is_quote > 0.5:
                candle_vol_q = vol if vol > 0.0 else 1.0e18
            else:
                candle_vol_q = vol * c if vol > 0.0 else 1.0e18
            o_price = float(open_arr[i])  # FIX-5: candle open for maker validity check

            # FIX-7A: Count only FILLED positions (to match CPU semantics)
            pos_count = 0
            for j in range(64):
                if pos_active[j] == 1:
                    pos_count += 1

            for j in range(20):
                if pend_active[j] == 0:
                    continue

                # Enforce expiration
                if pend_expires[j] > 0.0 and ts > pend_expires[j]:
                    if pend_side[j] == 1:
                        balance += pend_quote[j]
                    elif pend_side[j] == -1:
                        base_bal += pend_base_reserved[j]  # FIX-3: refund reserved base
                        pend_base_reserved[j] = 0.0
                    pend_active[j] = 0
                    continue

                # FIX-7A: Position cap — cancel if at capacity (uses pos_count, not n_open)
                if max_open > 0 and pos_count >= max_open:
                    if pend_side[j] == 1:
                        balance += pend_quote[j]
                    elif pend_side[j] == -1:
                        base_bal += pend_base_reserved[j]  # FIX-3
                        pend_base_reserved[j] = 0.0
                    pend_active[j] = 0
                    continue

                # Fill latency gate (in candles)
                if latency_s > 0.0 and (ts - pend_placed[j]) < latency_s:
                    continue

                # Buy order fill check
                if pend_side[j] == 1 and lo <= pend_price[j]:
                    # Rule K-7: Volume fill gate
                    if fill_rate_pct > 0.0:
                        order_q_gate = pend_quote[j]
                        if candle_vol_q * fill_rate_pct < order_q_gate:
                            continue  # not enough volume, try next candle

                    # FIX-5: Maker validity check — if open gapped through limit, taker fill
                    eff_entry_fee = entry_fee
                    if maker_validity == 1:
                        if o_price <= pend_price[j]:
                            eff_entry_fee = taker_fee_entry

                    # Fill: quote already reserved, receive base
                    fill_fee = pend_quote[j] * eff_entry_fee
                    balance -= fill_fee
                    fill_amt = pend_amt[j]
                    base_bal += fill_amt

                    # Find empty position slot
                    for k in range(64):
                        if pos_active[k] == 0:
                            pos_active[k] = 1
                            pos_side[k] = 1
                            pos_entry_price[k] = pend_price[j]
                            pos_amount[k] = fill_amt
                            pos_entry_quote[k] = pend_quote[j]
                            pos_entry_fee_paid[k] = fill_fee
                            pos_entry_time[k] = ts
                            pos_peak_pnl[k] = 0.0
                            pos_trailing[k] = 0
                            break

                    pend_active[j] = 0
                    pos_count += 1  # FIX-7A: increment AFTER fill

                # Sell order fill check
                elif pend_side[j] == -1 and h >= pend_price[j]:
                    # Rule K-7: Volume fill gate
                    if fill_rate_pct > 0.0:
                        order_q_gate = pend_amt[j] * pend_price[j]
                        if candle_vol_q * fill_rate_pct < order_q_gate:
                            continue

                    # FIX-5: Maker validity check — if open gapped through limit, taker fill
                    eff_entry_fee = entry_fee
                    if maker_validity == 1:
                        if o_price >= pend_price[j]:
                            eff_entry_fee = taker_fee_entry

                    # FIX-3: Base was already reserved at placement; do NOT subtract again
                    sell_amt = pend_amt[j]
                    sell_notional = sell_amt * pend_price[j]
                    fill_fee = sell_notional * eff_entry_fee
                    # base_bal already reduced at placement
                    balance += sell_notional - fill_fee

                    for k in range(64):
                        if pos_active[k] == 0:
                            pos_active[k] = 1
                            pos_side[k] = -1
                            pos_entry_price[k] = pend_price[j]
                            pos_amount[k] = sell_amt
                            pos_entry_quote[k] = sell_notional
                            pos_entry_fee_paid[k] = fill_fee
                            pos_entry_time[k] = ts
                            pos_peak_pnl[k] = 0.0
                            pos_trailing[k] = 0
                            break

                    pend_base_reserved[j] = 0.0  # FIX-3: clear reservation
                    pend_active[j] = 0
                    pos_count += 1  # FIX-7A: increment AFTER fill

            # ════════════════════════════════════════════════════════════
            # STEP 3: Place new orders (if signals valid AND refresh elapsed)
            # ════════════════════════════════════════════════════════════

            # Rule K-5: Cooldown check
            cooldown_ok = cooldown_s <= 0.0 or (ts - last_close_time) >= cooldown_s

            # BUG-3 V3: Use order_natr for validity check (shifted or not)
            signals_valid = (order_natr > 0.0 and macd_ring_count >= 20) if i > 0 else False

            if cooldown_ok and signals_valid and (ts - last_refresh_time) >= refresh_s:
                # Cancel all pending orders, return reserved capital
                for j in range(20):
                    if pend_active[j] == 1:
                        if pend_side[j] == 1:
                            balance += pend_quote[j]
                        elif pend_side[j] == -1:
                            base_bal += pend_base_reserved[j]  # FIX-3
                            pend_base_reserved[j] = 0.0
                        pend_active[j] = 0

                # Rule K-6: Capital sizing
                if compounding_on > 0.5:
                    sizing_base = balance + base_bal * c
                else:
                    sizing_base = init_capital
                avail_q = sizing_base * deploy_frac

                # Count open positions + pending for cap check
                n_open = 0
                for j in range(64):
                    if pos_active[j] == 1:
                        n_open += 1
                for j in range(20):
                    if pend_active[j] == 1:
                        n_open += 1

                # ── Place buy orders ──
                # BUG-3 V3: Use order_* for placement (may be shifted by 1 candle)
                for lv in range(n_lvl):
                    if max_open > 0 and n_open >= max_open:
                        break

                    spread_val = sp_lvl[lv]
                    sa = spread_val * order_sp_mult

                    # BUG-5 FIX: Spread floor only when enforce_spread_floor > 0.5
                    if enforce_spread_floor > 0.5:
                        min_spread_val = entry_fee + exit_fee + slip * 2.0
                        if min_spread_floor > min_spread_val:
                            min_spread_val = min_spread_floor
                        if sa < min_spread_val:
                            sa = min_spread_val

                    bp = order_ref_price * (1.0 - sa)

                    # Apply slippage (adverse for buyer: price goes up)
                    bp = bp * (1.0 + slip)

                    # BUG-5 FIX: Non-crossing guard only when enforce_nc_guard > 0.5
                    if enforce_nc_guard > 0.5:
                        nc_floor = entry_fee + exit_fee + slip * 2.0
                        if min_spread_floor > nc_floor:
                            nc_floor = min_spread_floor
                        bp = min(bp, c * (1.0 - nc_floor))
                    if bp <= 0.0:
                        continue

                    alloc_pct = amt_pct[lv] / 100.0
                    order_q = avail_q * alloc_pct

                    if max_order_q > 0.0 and order_q > max_order_q:
                        order_q = max_order_q

                    if order_q < 1.0:
                        continue

                    # Can't spend more than balance
                    cap_q = balance * 0.95
                    if order_q > cap_q:
                        order_q = cap_q
                    if order_q < 1.0:
                        continue

                    buy_amt = order_q / bp

                    # Find empty pending slot
                    placed = False
                    for j in range(20):
                        if pend_active[j] == 0:
                            pend_active[j] = 1
                            pend_side[j] = 1
                            pend_price[j] = bp
                            pend_amt[j] = buy_amt
                            pend_quote[j] = order_q
                            pend_placed[j] = ts
                            pend_expires[j] = ts + refresh_s
                            placed = True
                            break
                    if placed:
                        balance -= order_q  # reserve quote
                        n_open += 1

                # ── Place sell orders ──
                # BUG-3 V3: Use order_* for placement (may be shifted by 1 candle)
                for lv in range(n_lvl):
                    if max_open > 0 and n_open >= max_open:
                        break

                    spread_val = sp_lvl[lv]
                    sa = spread_val * order_sp_mult

                    # BUG-5 FIX: Spread floor only when enforce_spread_floor > 0.5
                    if enforce_spread_floor > 0.5:
                        min_spread_val = entry_fee + exit_fee + slip * 2.0
                        if min_spread_floor > min_spread_val:
                            min_spread_val = min_spread_floor
                        if sa < min_spread_val:
                            sa = min_spread_val

                    sp_price = order_ref_price * (1.0 + sa)

                    # Apply slippage (adverse for seller: price goes down)
                    sp_price = sp_price * (1.0 - slip)

                    # BUG-5 FIX: Non-crossing guard only when enforce_nc_guard > 0.5
                    if enforce_nc_guard > 0.5:
                        nc_floor = entry_fee + exit_fee + slip * 2.0
                        if min_spread_floor > nc_floor:
                            nc_floor = min_spread_floor
                        sp_price = max(sp_price, c * (1.0 + nc_floor))

                    alloc_pct = amt_pct[lv] / 100.0
                    order_q = avail_q * alloc_pct

                    if max_order_q > 0.0 and order_q > max_order_q:
                        order_q = max_order_q

                    if order_q < 1.0:
                        continue

                    sell_amt_base = order_q / sp_price

                    # BUG-3 FIX: base_bal already reflects reservations
                    avail_base = base_bal
                    if avail_base < sell_amt_base * 0.999:
                        continue  # not enough base inventory

                    base_bal -= sell_amt_base  # FIX-3: reserve base

                    placed = False
                    for j in range(20):
                        if pend_active[j] == 0:
                            pend_active[j] = 1
                            pend_side[j] = -1
                            pend_price[j] = sp_price
                            pend_amt[j] = sell_amt_base
                            pend_quote[j] = 0.0  # sells don't reserve quote
                            pend_base_reserved[j] = sell_amt_base  # FIX-3
                            pend_placed[j] = ts
                            pend_expires[j] = ts + refresh_s
                            placed = True
                            break
                    if placed:
                        n_open += 1
                    else:
                        base_bal += sell_amt_base  # refund if no slot available

                last_refresh_time = ts

            # BUG-3 V3: Update prev_ signal values at end of candle for next iteration
            prev_natr = natr
            prev_price_signal = price_signal

            # ════════════════════════════════════════════════════════════
            # STEP 4: Mark-to-market equity (ALWAYS)
            # ════════════════════════════════════════════════════════════
            # BUG-2 FIX: Include both reserved quote (buy) AND reserved base (sell)
            reserved_q = 0.0
            reserved_b = 0.0
            for j in range(20):
                if pend_active[j] == 1:
                    if pend_side[j] == 1:
                        reserved_q += pend_quote[j]
                    elif pend_side[j] == -1:
                        reserved_b += pend_base_reserved[j]
            equity = (balance + reserved_q) + (base_bal + reserved_b) * c

            if equity > peak_equity:
                peak_equity = equity
            if peak_equity > 0.0:
                dd = (peak_equity - equity) / peak_equity
                if dd > max_dd:
                    max_dd = dd

            # FIX-7B: Online Sharpe — skip first return to match CPU pct_change().dropna()
            if first_equity_set == 0:
                prev_equity = equity
                first_equity_set = 1
            else:
                if prev_equity > 0.0:
                    ret = (equity - prev_equity) / prev_equity
                    ret_sum += ret
                    ret_sum_sq += ret * ret
                    ret_count += 1
                prev_equity = equity

        # ════════════════════════════════════════════════════════════
        # Rule K-10: End-of-simulation cleanup
        # ════════════════════════════════════════════════════════════

        # 1. Cancel all pending orders
        for j in range(20):
            if pend_active[j] == 1:
                if pend_side[j] == 1:
                    balance += pend_quote[j]
                elif pend_side[j] == -1:
                    base_bal += pend_base_reserved[j]  # FIX-3
                    pend_base_reserved[j] = 0.0
                pend_active[j] = 0

        # 2. Close all open positions at last close
        last_c = float(close[n_candles - 1])
        for j in range(64):
            if pos_active[j] == 0:
                continue
            side = pos_side[j]
            ep = pos_entry_price[j]
            amt = pos_amount[j]

            exit_p = last_c

            exit_notional = amt * exit_p
            ex_fee = exit_notional * exit_fee
            if side == 1:
                balance += exit_notional - ex_fee
                base_bal -= amt
            else:
                balance -= exit_notional + ex_fee
                base_bal += amt

            if side == 1:
                pnl = amt * (exit_p - ep) - (pos_entry_fee_paid[j]) - ex_fee
            else:
                pnl = amt * (ep - exit_p) - (pos_entry_fee_paid[j]) - ex_fee
            if pnl > 0.0:
                gross_win += pnl
            else:
                gross_loss += (-pnl)
            n_trades += 1
            pos_active[j] = 0

        # 3. Safety net: any remaining base
        if base_bal > 0.0001:
            balance += base_bal * last_c

        # ── Compute final metrics ──
        final_equity = balance
        pnl_pct = (final_equity - init_capital) / init_capital if init_capital > 0.0 else 0.0

        # FIX-7B: Online Sharpe with sample variance (ddof=1)
        sharpe = 0.0
        if ret_count > 1:
            mean_r = ret_sum / ret_count
            # Sample variance: divide by (n-1) to match CPU ddof=1
            var_r = (ret_sum_sq - ret_sum * ret_sum / ret_count) / (ret_count - 1)
            if var_r > 0.0:
                std_r = math.sqrt(var_r)
                cpy = (365.25 * 86400.0) / candle_secs
                sharpe = (mean_r / std_r) * math.sqrt(cpy)

        # CPU parity: if no trades, Sharpe is sentinel -10.0
        if n_trades == 0.0:
            sharpe = -10.0
        out_sharpe[tid] = sharpe
        out_pnl_pct[tid] = pnl_pct
        out_max_dd[tid] = max_dd
        out_n_trades[tid] = n_trades
        out_gross_win[tid] = gross_win
        out_gross_loss[tid] = gross_loss
        out_final_balance[tid] = final_equity  # BUG-4 V3



# ---------------------------------------------------------------------------
# Parameter packing
# ---------------------------------------------------------------------------

def _pack_params(
    param_dicts,
    total_capital=1000.0,
    maker_fee=0.001,
    taker_fee=0.002,
    n_levels=2,
    deploy_fraction=0.5,
    compounding=False,
    max_order_quote=0.0,
    slippage_max_pct=0.001,
    max_open_positions=0,
    fill_rate_pct=0.0,
    cooldown_seconds=15,
    min_spread_floor=0.0,
    init_base=0.0,
    init_quote=None,       # None = total_capital
    maker_validity_check=True,
    timestamp_shift=0,     # 0 = close semantics, 1 = shifted signals
    volume_is_quote=False,
    enforce_spread_floor=False,
    enforce_nc_guard=False,
    cooldown_sl_only=True,
    exit_fee_tp=None,      # None = maker_fee
    latency_candles: int = 1,
):
    """Pack a list of param dicts into device arrays for the CUDA kernel."""
    n = len(param_dicts)

    # ── Allocate host arrays ──
    p_macd_fast = np.zeros(n, dtype=np.int32)
    p_macd_slow = np.zeros(n, dtype=np.int32)
    p_macd_signal = np.zeros(n, dtype=np.int32)
    p_natr_length = np.zeros(n, dtype=np.int32)

    p_spread_levels = np.full((n, _MAX_LEVELS), 999.0, dtype=np.float64)
    p_n_levels = np.zeros(n, dtype=np.int32)
    p_amount_pcts = np.full((n, _MAX_LEVELS), 0.0, dtype=np.float64)

    p_stop_loss = np.zeros(n, dtype=np.float64)
    p_take_profit = np.zeros(n, dtype=np.float64)
    p_time_limit_s = np.zeros(n, dtype=np.float64)
    p_trailing_act = np.zeros(n, dtype=np.float64)
    p_trailing_delta = np.zeros(n, dtype=np.float64)
    p_refresh_s = np.zeros(n, dtype=np.float64)

    p_entry_fee = np.full(n, maker_fee, dtype=np.float64)
    p_exit_fee = np.full(n, taker_fee, dtype=np.float64)

    # p_capital is the INITIAL QUOTE balance. p_initial_capital is used for fixed sizing when compounding=False.
    p_capital = np.full(n, total_capital, dtype=np.float64)
    if init_quote is not None:
        p_capital[:] = float(init_quote)

    p_initial_capital = np.full(n, total_capital, dtype=np.float64)

    p_deploy_frac = np.full(n, deploy_fraction, dtype=np.float64)
    p_compounding_flag = np.full(n, 1.0 if compounding else 0.0, dtype=np.float64)
    p_max_order_quote = np.full(n, max_order_quote, dtype=np.float64)
    p_slippage_avg = np.full(n, slippage_max_pct / 2.0, dtype=np.float64)
    p_max_open_pos = np.full(n, float(max_open_positions), dtype=np.float64)
    p_fill_rate = np.full(n, fill_rate_pct, dtype=np.float64)
    p_cooldown_s = np.full(n, float(cooldown_seconds), dtype=np.float64)
    p_min_spread_floor = np.full(n, min_spread_floor, dtype=np.float64)

    p_init_base_arr = np.full(n, init_base, dtype=np.float64)

    p_maker_validity = np.full(n, 1.0 if maker_validity_check else 0.0, dtype=np.float64)
    p_taker_fee_entry = np.full(n, taker_fee, dtype=np.float64)

    p_timestamp_shift = np.full(n, float(timestamp_shift), dtype=np.float64)
    p_volume_is_quote_arr = np.full(n, 1.0 if volume_is_quote else 0.0, dtype=np.float64)
    p_enforce_spread_floor_arr = np.full(n, 1.0 if enforce_spread_floor else 0.0, dtype=np.float64)
    p_enforce_nc_guard_arr = np.full(n, 1.0 if enforce_nc_guard else 0.0, dtype=np.float64)
    p_cooldown_sl_only_arr = np.full(n, 1.0 if cooldown_sl_only else 0.0, dtype=np.float64)

    _exit_fee_tp = exit_fee_tp if exit_fee_tp is not None else maker_fee
    p_exit_fee_tp_arr = np.full(n, _exit_fee_tp, dtype=np.float64)

    p_latency_candles_arr = np.full(n, float(latency_candles), dtype=np.float64)

    # ── Fill arrays per param dict ──
    for idx, params in enumerate(param_dicts):
        p_macd_fast[idx] = int(params.get("macd_fast", 21))
        p_macd_slow[idx] = int(params.get("macd_slow", 42))
        p_macd_signal[idx] = int(params.get("macd_signal", 9))
        p_natr_length[idx] = int(params.get("natr_length", 14))
        p_stop_loss[idx] = float(params.get("stop_loss", 0.03))
        p_take_profit[idx] = float(params.get("take_profit", 0.02))
        p_time_limit_s[idx] = float(params.get("time_limit_minutes", 60)) * 60.0
        p_trailing_act[idx] = float(params.get("trailing_activation", 0.01))
        p_trailing_delta[idx] = float(params.get("trailing_delta", 0.005))
        p_refresh_s[idx] = float(params.get("refresh_minutes", 5)) * 60.0

        actual_levels = int(params.get("n_levels", n_levels))
        p_n_levels[idx] = actual_levels

        # Spread levels
        for lv in range(actual_levels):
            key = f"spread_level_{lv + 1}"
            if key in params:
                p_spread_levels[idx, lv] = float(params[key])

        # Amount percentages
        has_weights = any(k.startswith("amount_weight_") for k in params)
        if has_weights:
            raw_weights = []
            for lv in range(actual_levels):
                raw_weights.append(float(params.get(f"amount_weight_{lv + 1}", 1.0)))
            total_weight = sum(raw_weights) if raw_weights else 1.0
            for lv in range(actual_levels):
                p_amount_pcts[idx, lv] = (raw_weights[lv] / total_weight) * 100.0
        else:
            # Direct amount_pct_N keys
            has_pcts = any(f"amount_pct_{lv + 1}" in params for lv in range(actual_levels))
            if has_pcts:
                for lv in range(actual_levels):
                    p_amount_pcts[idx, lv] = float(params.get(f"amount_pct_{lv + 1}", 100.0 / actual_levels))
            else:
                equal_pct = 100.0 / actual_levels
                for lv in range(actual_levels):
                    p_amount_pcts[idx, lv] = equal_pct

    # ── Transfer to device ──
    return {
        "p_macd_fast": _to_device(p_macd_fast),
        "p_macd_slow": _to_device(p_macd_slow),
        "p_macd_signal": _to_device(p_macd_signal),
        "p_natr_length": _to_device(p_natr_length),
        "p_spread_levels": _to_device(p_spread_levels),
        "p_n_levels": _to_device(p_n_levels),
        "p_amount_pcts": _to_device(p_amount_pcts),
        "p_stop_loss": _to_device(p_stop_loss),
        "p_take_profit": _to_device(p_take_profit),
        "p_time_limit_s": _to_device(p_time_limit_s),
        "p_trailing_act": _to_device(p_trailing_act),
        "p_trailing_delta": _to_device(p_trailing_delta),
        "p_refresh_s": _to_device(p_refresh_s),
        "p_entry_fee": _to_device(p_entry_fee),
        "p_exit_fee": _to_device(p_exit_fee),
        "p_capital": _to_device(p_capital),
        "p_initial_capital": _to_device(p_initial_capital),
        "p_deploy_frac": _to_device(p_deploy_frac),
        "p_compounding_flag": _to_device(p_compounding_flag),
        "p_max_order_quote": _to_device(p_max_order_quote),
        "p_slippage_avg": _to_device(p_slippage_avg),
        "p_max_open_pos": _to_device(p_max_open_pos),
        "p_fill_rate": _to_device(p_fill_rate),
        "p_cooldown_s": _to_device(p_cooldown_s),
        "p_min_spread_floor": _to_device(p_min_spread_floor),
        "p_init_base": _to_device(p_init_base_arr),
        "p_maker_validity": _to_device(p_maker_validity),
        "p_taker_fee_entry": _to_device(p_taker_fee_entry),
        "p_timestamp_shift": _to_device(p_timestamp_shift),
        "p_volume_is_quote": _to_device(p_volume_is_quote_arr),
        "p_enforce_spread_floor": _to_device(p_enforce_spread_floor_arr),
        "p_enforce_nc_guard": _to_device(p_enforce_nc_guard_arr),
        "p_cooldown_sl_only": _to_device(p_cooldown_sl_only_arr),
        "p_exit_fee_tp": _to_device(p_exit_fee_tp_arr),
        "p_latency_candles": _to_device(p_latency_candles_arr),
        "n": n,
    }



# ---------------------------------------------------------------------------
# Public API: gpu_backtest_single
# ---------------------------------------------------------------------------

def gpu_backtest_single(
    candles_gpu: dict,
    params: dict,
    total_capital: float = 1000.0,
    maker_fee: float = 0.001,
    taker_fee: float = 0.002,
    n_levels: int = 2,
    deploy_fraction: float = 0.5,
    compounding: bool = False,
    max_order_quote: float = 0.0,
    slippage_max_pct: float = 0.001,
    max_open_positions: int = 0,
    fill_rate_pct: float = 0.0,
    cooldown_seconds: int = 15,
    min_spread_floor: float = 0.0,
    initial_inventory_mode: str = "half_and_half",
    timestamp_shift: int = 0,
    volume_is_quote: bool = False,
    enforce_spread_floor: bool = False,
    enforce_nc_guard: bool = False,
    cooldown_sl_only: bool = True,
) -> dict:
    """
    Run a single PMM Dynamic backtest on GPU.

    Parameters
    ----------
    candles_gpu : dict from prepare_candles_gpu()
    params      : flat dict of parameter keys (same format as Optuna trial.params)

    Returns
    -------
    dict with keys: sharpe, pnl_pct, max_dd, n_trades, gross_win, gross_loss, final_balance

    Falls back to CPU PMMDynamicBacktester if GPU is unavailable.
    """
    if not _GPU_OK:
        # CPU fallback
        log.info("GPU unavailable — falling back to CPU backtester")
        actual_levels = int(params.get("n_levels", n_levels))
        buy_spreads = [params.get(f"spread_level_{lv + 1}", 1.0) for lv in range(actual_levels)]
        sell_spreads = buy_spreads[:]

        has_weights = any(k.startswith("amount_weight_") for k in params)
        if has_weights:
            raw_w = [params.get(f"amount_weight_{lv + 1}", 1.0) for lv in range(actual_levels)]
            tw = sum(raw_w)
            buy_amounts_pct = [round(w / tw * 100, 2) for w in raw_w]
        else:
            equal_pct = round(100.0 / actual_levels, 2)
            buy_amounts_pct = [equal_pct] * actual_levels
        sell_amounts_pct = buy_amounts_pct[:]

        import pandas as pd
        cfg = PMMDynamicConfig(
            total_amount_quote=total_capital,
            macd_fast=int(params.get("macd_fast", 21)),
            macd_slow=int(params.get("macd_slow", 42)),
            macd_signal=int(params.get("macd_signal", 9)),
            natr_length=int(params.get("natr_length", 14)),
            buy_spreads=buy_spreads,
            sell_spreads=sell_spreads,
            buy_amounts_pct=buy_amounts_pct,
            sell_amounts_pct=sell_amounts_pct,
            stop_loss=float(params.get("stop_loss", 0.03)),
            take_profit=float(params.get("take_profit", 0.02)),
            time_limit_seconds=int(float(params.get("time_limit_minutes", 60)) * 60),
            trailing_stop_activation=float(params.get("trailing_activation", 0.01)),
            trailing_stop_delta=float(params.get("trailing_delta", 0.005)),
            executor_refresh_seconds=int(float(params.get("refresh_minutes", 5)) * 60),
            maker_fee=maker_fee,
            taker_fee=taker_fee,
            compounding=compounding,
            max_order_quote=max_order_quote,
            slippage_max_pct=slippage_max_pct,
            fill_rate_pct=fill_rate_pct,
            max_open_positions=max_open_positions,
            deploy_fraction=deploy_fraction,
            cooldown_seconds=cooldown_seconds,
            min_spread_floor=min_spread_floor,
            initial_inventory_mode=initial_inventory_mode,
        )

        # Build candles DataFrame from GPU arrays
        candles_np = {
            "close": _to_host(candles_gpu["close"]),
            "high": _to_host(candles_gpu["high"]),
            "low": _to_host(candles_gpu["low"]),
            "volume": _to_host(candles_gpu["volume"]),
        }
        ts_arr = _to_host(candles_gpu["timestamps"])
        candles_df = pd.DataFrame({
            "timestamp": pd.to_datetime(ts_arr, unit="s"),
            "open": candles_np["close"],  # open not critical for this backtest
            "high": candles_np["high"],
            "low": candles_np["low"],
            "close": candles_np["close"],
            "volume": candles_np["volume"],
        })
        result = PMMDynamicBacktester(cfg).run(candles_df)
        gross_profit = sum(t["pnl_quote"] for t in result.trades if t["pnl_quote"] > 0)
        gross_loss_val = abs(sum(t["pnl_quote"] for t in result.trades if t["pnl_quote"] < 0))
        return {
            "sharpe": result.sharpe_ratio,
            "pnl_pct": result.net_pnl_pct,
            "max_dd": result.max_drawdown,
            "n_trades": result.total_trades,
            "gross_win": gross_profit,
            "gross_loss": gross_loss_val,
        }

    # ── GPU path ──
    # FIX-6: Guard against GPU array overflow
    actual_levels = int(params.get("n_levels", n_levels))
    if actual_levels > _MAX_LEVELS:
        raise ValueError(f"n_levels={actual_levels} exceeds GPU max {_MAX_LEVELS}")
    if max_open_positions == 0 or max_open_positions > 64:
        log.warning("max_open_positions=%d exceeds GPU max 64; clamping to 64", max_open_positions)
        max_open_positions = 64

    # FIX-4: Compute initial inventory based on mode
    n_candles_total = candles_gpu["n_candles"]
    z_window = max(
        int(params.get("macd_fast", 21)),
        int(params.get("macd_slow", 42)),
        int(params.get("macd_signal", 9)),
        int(params.get("natr_length", 14)),
    ) + 100
    warmup_k = min(z_window, max(n_candles_total - 1, 0))

    if initial_inventory_mode == "all_quote":
        init_quote = total_capital
        init_base = 0.0
    else:
        first_close = float(candles_gpu["close"][warmup_k])
        if first_close <= 0:
            first_close = 1.0
        if initial_inventory_mode == "all_base":
            init_quote = 0.0
            init_base = total_capital / first_close
        else:
            init_quote = total_capital * 0.5
            init_base = (total_capital * 0.5) / first_close


    packed = _pack_params(
        [params],
        total_capital=total_capital,
        maker_fee=maker_fee,
        taker_fee=taker_fee,
        n_levels=n_levels,
        deploy_fraction=deploy_fraction,
        compounding=compounding,
        max_order_quote=max_order_quote,
        slippage_max_pct=slippage_max_pct,
        max_open_positions=max_open_positions,
        fill_rate_pct=fill_rate_pct,
        cooldown_seconds=cooldown_seconds,
        min_spread_floor=min_spread_floor,
        init_base=init_base,
        init_quote=init_quote,
        timestamp_shift=timestamp_shift,
        volume_is_quote=volume_is_quote,
        enforce_spread_floor=enforce_spread_floor,
        enforce_nc_guard=enforce_nc_guard,
        cooldown_sl_only=cooldown_sl_only,
    )

    n_sets = 1
    out_sharpe = _device_zeros(n_sets, dtype=np.float64)
    out_pnl_pct = _device_zeros(n_sets, dtype=np.float64)
    out_max_dd = _device_zeros(n_sets, dtype=np.float64)
    out_n_trades = _device_zeros(n_sets, dtype=np.float64)
    out_gross_win = _device_zeros(n_sets, dtype=np.float64)
    out_gross_loss = _device_zeros(n_sets, dtype=np.float64)
    out_final_balance = _device_zeros(n_sets, dtype=np.float64)  # BUG-4 V3

    threads = _THREADS_PER_BLOCK
    blocks = (n_sets + threads - 1) // threads

    _simulate_kernel[blocks, threads](
        candles_gpu["open"], candles_gpu["close"], candles_gpu["high"], candles_gpu["low"],
        candles_gpu["volume"], candles_gpu["timestamps"],
        candles_gpu["n_candles"], candles_gpu["candle_seconds"],
        packed["p_macd_fast"], packed["p_macd_slow"],
        packed["p_macd_signal"], packed["p_natr_length"],
        packed["p_spread_levels"], packed["p_n_levels"],
        packed["p_amount_pcts"],
        packed["p_stop_loss"], packed["p_take_profit"], packed["p_time_limit_s"],
        packed["p_trailing_act"], packed["p_trailing_delta"],
        packed["p_refresh_s"],
        packed["p_entry_fee"], packed["p_exit_fee"],
        packed["p_capital"], packed["p_initial_capital"],
        packed["p_deploy_frac"], packed["p_compounding_flag"],
        packed["p_max_order_quote"], packed["p_slippage_avg"],
        packed["p_max_open_pos"], packed["p_fill_rate"],
        packed["p_cooldown_s"],
        packed["p_min_spread_floor"],
        packed["p_init_base"],
        packed["p_maker_validity"],
        packed["p_taker_fee_entry"],
        packed["p_timestamp_shift"],
        packed["p_volume_is_quote"],
        packed["p_enforce_spread_floor"],
        packed["p_enforce_nc_guard"],
        packed["p_cooldown_sl_only"],
        packed["p_exit_fee_tp"],
        packed["p_latency_candles"],
        n_sets,
        out_sharpe, out_pnl_pct, out_max_dd, out_n_trades,
        out_gross_win, out_gross_loss,
        out_final_balance,
    )

    cuda.synchronize()

    h_sharpe = float(_to_host(out_sharpe)[0])
    h_pnl = float(_to_host(out_pnl_pct)[0])
    h_dd = float(_to_host(out_max_dd)[0])
    h_trades = int(float(_to_host(out_n_trades)[0]))
    h_gw = float(_to_host(out_gross_win)[0])
    h_gl = float(_to_host(out_gross_loss)[0])
    h_fb = float(_to_host(out_final_balance)[0])

    return {
        "sharpe": h_sharpe,
        "pnl_pct": h_pnl,
        "max_dd": h_dd,
        "n_trades": h_trades,
        "gross_win": h_gw,
        "gross_loss": h_gl,
        "final_balance": h_fb,  # BUG-4 V3
    }




def _dummy_candles_from_gpu(candles_gpu: dict):
    """Convert device candle arrays back to a pandas DataFrame for CPU fallback."""
    import pandas as pd
    ts_arr = _to_host(candles_gpu["timestamps"])
    close_arr = _to_host(candles_gpu["close"])
    high_arr = _to_host(candles_gpu["high"])
    low_arr = _to_host(candles_gpu["low"])
    vol_arr = _to_host(candles_gpu["volume"])
    return pd.DataFrame({
        "timestamp": pd.to_datetime(ts_arr, unit="s"),
        "open": close_arr,
        "high": high_arr,
        "low": low_arr,
        "close": close_arr,
        "volume": vol_arr,
    })


# ---------------------------------------------------------------------------
# Public Optuna objective factory
# ---------------------------------------------------------------------------

def create_objective_gpu(
    candles_gpu: dict,
    connector: str = "nonkyc",
    trading_pair: str = "BTC/USDT",
    interval: str = "5m",
    total_amount_quote: float = 1000.0,
    leverage: int = 1,
    n_levels: int = 2,
    optimize_metric: str = "sharpe_ratio",
    max_drawdown_constraint: float = 0.15,
    maker_fee: float = 0.001,
    taker_fee: float = 0.002,
    spread_min: float = 0.5,
    spread_max: float = 8.0,
    spread_step: float = 0.1,
    optimize_n_levels: bool = False,
    min_levels: int = 1,
    max_levels: int = 10,
    optimize_amounts: bool = True,
    deploy_fraction: float = 0.5,
    compounding: bool = False,
    max_order_quote: float = 0.0,
    slippage_max_pct: float = 0.001,
    fill_rate_pct: float = 0.0,
    max_open_positions: int = 0,
    cooldown_seconds: int = 15,
    min_spread_floor: float = 0.0,
    auto_spread_floor: bool = True,
    min_trades: int = 50,
    max_trades_per_day: float = 20.0,
    turnover_penalty_weight: float = 0.1,
    candles_df=None,
    initial_inventory_mode: str = "half_and_half",
    timestamp_shift: int = 0,
    volume_is_quote: bool = False,
    enforce_spread_floor: bool = False,
    enforce_nc_guard: bool = False,
    cooldown_sl_only: bool = True,
    use_enhanced: bool = False,
) -> callable:
    """
    Return an Optuna objective function that backtests PMM Dynamic on GPU.

    Parameters mirror create_objective from the CPU module. The GPU kernel
    handles fill_rate_pct natively — there is no CPU fallback for fill_rate.
    """
    # If GPU is not available, fall back to CPU objective
    if not _GPU_OK:
        log.warning("GPU unavailable — delegating to CPU create_objective")
        from pmm_dynamic_optimizer import create_objective
        return create_objective(
            candles_df if candles_df is not None else _dummy_candles_from_gpu(candles_gpu),
            connector=connector,
            trading_pair=trading_pair,
            interval=interval,
            total_amount_quote=total_amount_quote,
            leverage=leverage,
            n_levels=n_levels,
            optimize_metric=optimize_metric,
            max_drawdown_constraint=max_drawdown_constraint,
            maker_fee=maker_fee,
            taker_fee=taker_fee,
            spread_min=spread_min,
            spread_max=spread_max,
            spread_step=spread_step,
            optimize_n_levels=optimize_n_levels,
            min_levels=min_levels,
            max_levels=max_levels,
            optimize_amounts=optimize_amounts,
            compounding=compounding,
            max_order_quote=max_order_quote,
            slippage_max_pct=slippage_max_pct,
            fill_rate_pct=fill_rate_pct,
            max_open_positions=max_open_positions,
            deploy_fraction=deploy_fraction,
            min_trades=min_trades,
            max_trades_per_day=max_trades_per_day,
            turnover_penalty_weight=turnover_penalty_weight,
            auto_spread_floor=auto_spread_floor,
            enforce_spread_floor=enforce_spread_floor,
            enforce_nc_guard=enforce_nc_guard,
            cooldown_on_stop_loss_only=cooldown_sl_only,
            use_enhanced=use_enhanced,
        )

    # BUG-1 V3: Auto spread floor — reconstruct candles_df from GPU arrays when None
    if auto_spread_floor:
        if candles_df is None:
            log.warning(
                "auto_spread_floor=True but candles_df is None — reconstructing "
                "DataFrame from GPU arrays. Always pass candles_df for best accuracy."
            )
            candles_df = _dummy_candles_from_gpu(candles_gpu)
        entry_f = maker_fee   # entry is maker by default
        exit_f  = taker_fee   # exit is taker by default
        min_mult = _auto_spread_min_multiplier(
            candles_df, entry_f, exit_f, slippage_max_pct
        )
        spread_min = max(spread_min, min_mult)
        # Keep min_spread_floor as a SEPARATE absolute floor (fees+slippage, no NATR division)
        abs_floor = (entry_f + exit_f + slippage_max_pct) * 1.2
        min_spread_floor = max(min_spread_floor, abs_floor)

    candle_seconds = candles_gpu["candle_seconds"]
    n_candles_val = candles_gpu["n_candles"]

    def objective(trial) -> float:
        # 1. Suggest params — imported from CPU (single source of truth)
        _suggest_params(
            trial, n_levels, spread_min, spread_max, spread_step,
            optimize_n_levels, min_levels, max_levels, optimize_amounts,
        )
        params = dict(trial.params)

        # 2. Run GPU backtest
        result = gpu_backtest_single(
            candles_gpu, params,
            total_capital=total_amount_quote,
            maker_fee=maker_fee,
            taker_fee=taker_fee,
            n_levels=n_levels,
            deploy_fraction=deploy_fraction,
            compounding=compounding,
            max_order_quote=max_order_quote,
            slippage_max_pct=slippage_max_pct,
            max_open_positions=max_open_positions,
            fill_rate_pct=fill_rate_pct,
            cooldown_seconds=cooldown_seconds,
            min_spread_floor=min_spread_floor,
            initial_inventory_mode=initial_inventory_mode,
            timestamp_shift=timestamp_shift,
            volume_is_quote=volume_is_quote,
            enforce_spread_floor=enforce_spread_floor,
            enforce_nc_guard=enforce_nc_guard,
            cooldown_sl_only=cooldown_sl_only,
        )

        # 3. Compute penalized objective
        return _compute_objective(
            result, optimize_metric, max_drawdown_constraint,
            min_trades, max_trades_per_day, turnover_penalty_weight,
            candle_seconds=candle_seconds, n_candles=n_candles_val,
            use_enhanced=use_enhanced,
        )

    return objective


# ---------------------------------------------------------------------------
# Public parity validator
# ---------------------------------------------------------------------------

def assert_cpu_gpu_parity(
    candles,
    params: dict,
    total_capital: float = 1000.0,
    maker_fee: float = 0.001,
    taker_fee: float = 0.002,
    slippage_max_pct: float = 0.001,
    fill_rate_pct: float = 0.0,
    max_open_positions: int = 2,
    deploy_fraction: float = 0.5,
    compounding: bool = False,
    max_order_quote: float = 0.0,
    cooldown_seconds: int = 15,
    min_spread_floor: float = 0.0,
    interval: str = "5m",
    tolerance: float = 0.02,
    initial_inventory_mode: str = "half_and_half",
    auto_spread_floor: bool = False,
    candles_df=None,
    timestamp_shift: int = 0,
    volume_is_quote: bool = False,
    enforce_spread_floor: bool = False,
    enforce_nc_guard: bool = False,
    cooldown_sl_only: bool = True,
) -> dict:
    """
    Run the same backtest on CPU and GPU, assert results match within tolerance.

    Both sides receive identical economics — this is the whole point.

    Returns dict with cpu_result, gpu_result, diff_pct, and pass flag.
    Raises AssertionError if any metric differs by more than tolerance.
    """
    import pandas as pd

    # ── CPU run ──
    actual_levels = int(params.get("n_levels", 2))
    buy_spreads = [params.get(f"spread_level_{lv + 1}", 1.0) for lv in range(actual_levels)]
    sell_spreads = buy_spreads[:]

    has_weights = any(k.startswith("amount_weight_") for k in params)
    if has_weights:
        raw_w = [params.get(f"amount_weight_{lv + 1}", 1.0) for lv in range(actual_levels)]
        tw = sum(raw_w)
        buy_amounts_pct = [round(w / tw * 100, 2) for w in raw_w]
    else:
        has_pcts = any(f"amount_pct_{lv + 1}" in params for lv in range(actual_levels))
        if has_pcts:
            buy_amounts_pct = [params.get(f"amount_pct_{lv + 1}", 100.0 / actual_levels) for lv in range(actual_levels)]
        else:
            equal_pct = round(100.0 / actual_levels, 2)
            buy_amounts_pct = [equal_pct] * actual_levels
    sell_amounts_pct = buy_amounts_pct[:]

    # FIX-2 V3: Auto spread floor parity — compute and apply to both sides
    parity_min_spread_floor = min_spread_floor
    if auto_spread_floor:
        parity_candles = candles_df if candles_df is not None else candles
        entry_f = maker_fee
        exit_f = taker_fee
        min_mult = _auto_spread_min_multiplier(parity_candles, entry_f, exit_f, slippage_max_pct)
        # For parity, we need to adjust spread levels, not spread_min (which is an Optuna search param)
        abs_floor = (entry_f + exit_f + slippage_max_pct) * 1.2
        parity_min_spread_floor = max(parity_min_spread_floor, abs_floor)

    # Map timestamp_shift to timestamp_mode for CPU config
    ts_mode = "close" if timestamp_shift == 0 else "open"
    vol_units = "quote" if volume_is_quote else "base"

    cfg = PMMDynamicConfig(
        total_amount_quote=total_capital,
        macd_fast=int(params.get("macd_fast", 21)),
        macd_slow=int(params.get("macd_slow", 42)),
        macd_signal=int(params.get("macd_signal", 9)),
        natr_length=int(params.get("natr_length", 14)),
        buy_spreads=buy_spreads,
        sell_spreads=sell_spreads,
        buy_amounts_pct=buy_amounts_pct,
        sell_amounts_pct=sell_amounts_pct,
        stop_loss=float(params.get("stop_loss", 0.03)),
        take_profit=float(params.get("take_profit", 0.02)),
        time_limit_seconds=int(float(params.get("time_limit_minutes", 60)) * 60),
        trailing_stop_activation=float(params.get("trailing_activation", 0.01)),
        trailing_stop_delta=float(params.get("trailing_delta", 0.005)),
        executor_refresh_seconds=int(float(params.get("refresh_minutes", 5)) * 60),
        maker_fee=maker_fee,
        taker_fee=taker_fee,
        interval=interval,
        compounding=compounding,
        max_order_quote=max_order_quote,
        slippage_max_pct=slippage_max_pct,
        fill_rate_pct=fill_rate_pct,
        max_open_positions=max_open_positions,
        deploy_fraction=deploy_fraction,
        cooldown_seconds=cooldown_seconds,
        min_spread_floor=parity_min_spread_floor,
        initial_inventory_mode=initial_inventory_mode,
        timestamp_mode=ts_mode,
        volume_units=vol_units,
        enforce_spread_floor=enforce_spread_floor,
        enforce_nc_guard=enforce_nc_guard,
        cooldown_on_stop_loss_only=cooldown_sl_only,
    )

    cpu_result_obj = PMMDynamicBacktester(cfg).run(candles)
    gross_profit = sum(t["pnl_quote"] for t in cpu_result_obj.trades if t["pnl_quote"] > 0)
    gross_loss_val = abs(sum(t["pnl_quote"] for t in cpu_result_obj.trades if t["pnl_quote"] < 0))
    cpu_result = {
        "sharpe": cpu_result_obj.sharpe_ratio,
        "pnl_pct": cpu_result_obj.net_pnl_pct,
        "max_dd": cpu_result_obj.max_drawdown,
        "n_trades": cpu_result_obj.total_trades,
        "gross_win": gross_profit,
        "gross_loss": gross_loss_val,
    }
    # ADD-5: Expose final_balance from CPU run
    cpu_result["final_balance"] = float(total_capital + cpu_result_obj.net_pnl)

    # ── GPU run ──
    candles_gpu = prepare_candles_gpu(candles, interval=interval, dtype="float64")
    gpu_result = gpu_backtest_single(
        candles_gpu, params,
        total_capital=total_capital,
        maker_fee=maker_fee,
        taker_fee=taker_fee,
        n_levels=actual_levels,
        deploy_fraction=deploy_fraction,
        compounding=compounding,
        max_order_quote=max_order_quote,
        slippage_max_pct=slippage_max_pct,
        max_open_positions=max_open_positions,
        fill_rate_pct=fill_rate_pct,
        cooldown_seconds=cooldown_seconds,
        min_spread_floor=parity_min_spread_floor,
        initial_inventory_mode=initial_inventory_mode,
        timestamp_shift=timestamp_shift,
        volume_is_quote=volume_is_quote,
        enforce_spread_floor=enforce_spread_floor,
        enforce_nc_guard=enforce_nc_guard,
        cooldown_sl_only=cooldown_sl_only,
    )

    # FIX-8: Enhanced comparison with tighter tolerances
    diff_pct = {}
    all_pass = True

    # n_trades MUST be identical (FIX-8 invariant)
    ct = cpu_result["n_trades"]
    gt = gpu_result["n_trades"]
    if ct != gt:
        all_pass = False
        diff_pct["n_trades_mismatch"] = abs(ct - gt)
    diff_pct["n_trades"] = abs(ct - gt) / max(ct, 1)

    # PnL: tighter tolerance (FIX-8: 0.5% absolute, was 2% relative)
    pnl_diff = abs(cpu_result["pnl_pct"] - gpu_result["pnl_pct"])
    diff_pct["pnl_pct_abs"] = pnl_diff
    if pnl_diff > 0.005:
        all_pass = False

    # Max drawdown: tight tolerance (FIX-8: 0.1% absolute)
    dd_diff = abs(cpu_result["max_dd"] - gpu_result["max_dd"])
    diff_pct["max_dd_abs"] = dd_diff
    if dd_diff > 0.001:
        all_pass = False

    # Sharpe: tight tolerance (FIX-8: 0.05 absolute)
    sharpe_abs_diff = abs(cpu_result["sharpe"] - gpu_result["sharpe"])
    diff_pct["sharpe_abs"] = sharpe_abs_diff
    if sharpe_abs_diff > 0.05:
        all_pass = False

    # final_balance comparison
    cb = cpu_result.get("final_balance", None)
    gb = gpu_result.get("final_balance", None)
    if cb is not None and gb is not None:
        abs_diff = abs(cb - gb)
        rel_diff = abs_diff / max(abs(cb), 1e-9)
        diff_pct["final_balance_rel"] = rel_diff
        if abs_diff > 1e-4 * total_capital:
            all_pass = False

    # gross_win and gross_loss comparison
    for gkey in ["gross_win", "gross_loss"]:
        cv = cpu_result.get(gkey, 0.0)
        gv = gpu_result.get(gkey, 0.0)
        denom = max(abs(cv), 1e-9)
        rel = abs(cv - gv) / denom
        diff_pct[gkey] = rel
        if rel > 1e-3:
            all_pass = False

    result = {
        "cpu_result": cpu_result,
        "gpu_result": gpu_result,
        "diff_pct": diff_pct,
        "pass": all_pass,
    }

    if not all_pass:
        raise AssertionError(
            f"CPU/GPU parity failed: diffs={diff_pct}, "
            f"cpu={cpu_result}, gpu={gpu_result}"
        )

    return result