"""Numba-compiled port of EMA regime-hold controller-compat feature kernel.

Mirrors `_compute_controller_compat` in `ema_regime_hold_features.py`. For each
fast bar t:
  1. Find the most recent SLOW_MAX_RECORDS regime bars with timestamp <= t_now.
  2. Compute ema_fast, ema_slow, adx on that slow slice.
  3. trend_on = (ema_fast >= ema_slow) & (adx >= threshold).
  4. Drop NaN rows (both EMAs and ADX must be warmed up).
  5. Project: the most recent non-NaN trend_on value (from the last valid slow
     bar in the window).
  6. Compute vol_ok on the last FAST_MAX_RECORDS fast bars ending at t.

The Numba kernel computes these per-fast-bar via full-series EMA/ADX over the
slow slice (bounded to SLOW_MAX_RECORDS) — mirroring the replay path's
per-bar recompute semantics exactly.
"""

from __future__ import annotations

import math

import numpy as np

from pmm_lab.features._numba_availability import _NUMBA_AVAILABLE
from pmm_lab.features._numba_indicators import (
    _adx_wilder_last,
    _ema_last,
    _rolling_volume_quantile_ok_last,
)

if _NUMBA_AVAILABLE:
    from numba import njit  # type: ignore
else:
    def njit(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]
        def _wrap(fn):
            return fn
        return _wrap


# The fast/slow replay-path bounds from ema_regime_hold_features.py:
SLOW_MAX_RECORDS = 3000
FAST_MAX_RECORDS = 6000


@njit(cache=True)
def _run_ema_kernel(
    fast_ts: np.ndarray,
    fast_volumes: np.ndarray,
    regime_ts: np.ndarray,
    regime_highs: np.ndarray,
    regime_lows: np.ndarray,
    regime_closes: np.ndarray,
    regime_ema_fast: int,
    regime_ema_slow: int,
    regime_adx_length: int,
    regime_adx_threshold: float,
    volume_filter_window: int,
    min_volume_quantile: float,
):
    """Inner Numba-compiled loop.

    Returns (trend_on, vol_ok) as bool arrays of length n_fast.

    For trend_on at fast bar t:
      - Find largest j with regime_ts[j] <= fast_ts[t]. If none, trend_on[t]=False.
      - slow_start = max(0, j+1 - SLOW_MAX_RECORDS)
      - slice = regime[slow_start : j+1]
      - Compute ema_fast[-1], ema_slow[-1], adx[-1] on slice.
      - If any are NaN, skip this bar (trend_on stays False).
      - Else trend_on[t] = (ema_fast >= ema_slow) & (adx >= threshold).
    """
    n_fast = fast_ts.shape[0]
    n_regime = regime_ts.shape[0]
    trend_arr = np.zeros(n_fast, dtype=np.bool_)
    volok_arr = np.zeros(n_fast, dtype=np.bool_)

    # Precompute regime EMA/ADX at every regime bar index once — OUTSIDE the
    # fast loop. This is O(n_regime * length) vs O(n_fast * SLOW_MAX_RECORDS)
    # inside the loop, so it's a huge win for long sweeps.
    # BUT: we must respect the SLOW_MAX_RECORDS-bounded slice per fast bar.
    # Trick: on each fast bar, compute ema/adx over the bounded regime window
    # ending at the identified slow index.
    # For correctness with the replay path, we must recompute per-fast-bar.
    # In practice, for n_regime <= SLOW_MAX_RECORDS, the bounded window is
    # identical to "all regime bars up to j", so we can precompute ONCE and
    # lookup by index. This is the common case.
    # We check this condition at the outer level in the wrapper.

    # Full-series EMA/ADX over the whole regime array once:
    # ema_fast, ema_slow, adx evaluated at every regime index i = [0, n_regime)
    ema_fast_arr = np.full(n_regime, np.nan, dtype=np.float64)
    ema_slow_arr = np.full(n_regime, np.nan, dtype=np.float64)
    adx_arr = np.full(n_regime, np.nan, dtype=np.float64)

    # To respect SLOW_MAX_RECORDS bounding, we compute per-fast-bar.
    # When n_regime <= SLOW_MAX_RECORDS, this reduces to a single full-series
    # pass (precomputed below).

    if n_regime <= SLOW_MAX_RECORDS:
        # Fast path: compute EMA/ADX series once over the whole regime array.
        # For each slow index j, evaluate via bounded slice [0:j+1] of the full array.
        # We emulate "full-series ewm evaluated at bar j" via _ema_last on prefix.
        # Since ewm is recursive (state propagates), we compute in a single pass.
        alpha_fast = 2.0 / (regime_ema_fast + 1.0)
        alpha_slow = 2.0 / (regime_ema_slow + 1.0)

        ema_f_prev = math.nan
        ema_s_prev = math.nan
        ema_f_seeded = False
        ema_s_seeded = False
        ema_f_seen = 0
        ema_s_seen = 0
        for i in range(n_regime):
            x = regime_closes[i]
            if not math.isnan(x):
                ema_f_seen += 1
                ema_s_seen += 1
                if not ema_f_seeded:
                    ema_f_prev = x
                    ema_f_seeded = True
                else:
                    ema_f_prev = alpha_fast * x + (1.0 - alpha_fast) * ema_f_prev
                if not ema_s_seeded:
                    ema_s_prev = x
                    ema_s_seeded = True
                else:
                    ema_s_prev = alpha_slow * x + (1.0 - alpha_slow) * ema_s_prev
            ema_fast_arr[i] = ema_f_prev if ema_f_seen >= regime_ema_fast else math.nan
            ema_slow_arr[i] = ema_s_prev if ema_s_seen >= regime_ema_slow else math.nan

        # ADX — single pass via the primitive (which is iterative).
        # We need adx at EVERY index, not just the last, so we replicate the
        # _adx_wilder_last logic but emit the full trace.
        alpha_adx = 1.0 / regime_adx_length
        one_minus_alpha = 1.0 - alpha_adx
        atr_prev = math.nan
        atr_seeded = False
        atr_n_seen = 0
        plus_dm_ewm = math.nan
        minus_dm_ewm = math.nan
        dm_seeded = False
        dm_n_seen = 0
        adx_prev_local = math.nan
        adx_seeded = False
        adx_n_seen = 0

        for i in range(n_regime):
            # ATR
            if i == 0:
                tr = regime_highs[0] - regime_lows[0]
            else:
                pc = regime_closes[i - 1]
                a = regime_highs[i] - regime_lows[i]
                b = abs(regime_highs[i] - pc)
                c = abs(regime_lows[i] - pc)
                tr = a
                if b > tr:
                    tr = b
                if c > tr:
                    tr = c
            atr_n_seen += 1
            if not atr_seeded:
                atr_prev = tr
                atr_seeded = True
            else:
                atr_prev = alpha_adx * tr + one_minus_alpha * atr_prev
            atr_out = atr_prev if atr_n_seen >= regime_adx_length else math.nan

            # +DM, -DM
            if i == 0:
                plus_dm = 0.0
                minus_dm = 0.0
            else:
                up_move = regime_highs[i] - regime_highs[i - 1]
                down_move = -(regime_lows[i] - regime_lows[i - 1])
                if (up_move > down_move) and (up_move > 0.0):
                    plus_dm = up_move
                else:
                    plus_dm = 0.0
                if (down_move > up_move) and (down_move > 0.0):
                    minus_dm = down_move
                else:
                    minus_dm = 0.0
            dm_n_seen += 1
            if not dm_seeded:
                plus_dm_ewm = plus_dm
                minus_dm_ewm = minus_dm
                dm_seeded = True
            else:
                plus_dm_ewm = alpha_adx * plus_dm + one_minus_alpha * plus_dm_ewm
                minus_dm_ewm = alpha_adx * minus_dm + one_minus_alpha * minus_dm_ewm
            plus_dm_out = plus_dm_ewm if dm_n_seen >= regime_adx_length else math.nan
            minus_dm_out = minus_dm_ewm if dm_n_seen >= regime_adx_length else math.nan

            if math.isnan(atr_out) or atr_out == 0.0 or math.isnan(plus_dm_out):
                plus_di = math.nan
            else:
                plus_di = 100.0 * plus_dm_out / atr_out
            if math.isnan(atr_out) or atr_out == 0.0 or math.isnan(minus_dm_out):
                minus_di = math.nan
            else:
                minus_di = 100.0 * minus_dm_out / atr_out

            if math.isnan(plus_di) or math.isnan(minus_di):
                dx = math.nan
            else:
                s = plus_di + minus_di
                if s == 0.0:
                    dx = math.nan
                else:
                    dx = 100.0 * abs(plus_di - minus_di) / s

            if not math.isnan(dx):
                adx_n_seen += 1
                if not adx_seeded:
                    adx_prev_local = dx
                    adx_seeded = True
                else:
                    adx_prev_local = alpha_adx * dx + one_minus_alpha * adx_prev_local
            adx_arr[i] = adx_prev_local if adx_n_seen >= regime_adx_length else math.nan

    # For each fast bar, find the most recent valid (non-NaN) regime trend_on
    # where regime_ts[j] <= fast_ts[t] AND j is within SLOW_MAX_RECORDS of the
    # latest included slow bar.
    # If n_regime > SLOW_MAX_RECORDS, we must re-evaluate per-fast-bar on the
    # bounded window. Otherwise we use the precomputed arrays.
    j = -1  # rolling index into regime_ts
    for t in range(n_fast):
        t_now = fast_ts[t]
        # Advance j to the last regime bar with regime_ts[j] <= t_now
        while j + 1 < n_regime and regime_ts[j + 1] <= t_now:
            j += 1
        if j < 0:
            # No regime bar yet — pandas replay `continue`s here, leaving
            # BOTH trend_arr[t] and volok_arr[t] at their zero-init default.
            continue

        # Determine whether the regime has warmed up enough to produce at least
        # one non-NaN trend. If not, pandas replay hits `if slow_ind.empty:
        # continue` and both arrays stay at default False.
        trend_ready = False
        trend_on_t = False
        if n_regime <= SLOW_MAX_RECORDS:
            # Walk backward from j to find the last NON-NaN trend value
            for k in range(j, -1, -1):
                ef = ema_fast_arr[k]
                es = ema_slow_arr[k]
                ad = adx_arr[k]
                if math.isnan(ef) or math.isnan(es) or math.isnan(ad):
                    continue
                trend_on_t = (ef >= es) and (ad >= regime_adx_threshold)
                trend_ready = True
                break
        else:
            # Bounded-slice recompute per fast bar
            slow_start = j + 1 - SLOW_MAX_RECORDS
            if slow_start < 0:
                slow_start = 0
            for k in range(j, slow_start - 1, -1):
                c_slice = regime_closes[slow_start:k + 1]
                h_slice = regime_highs[slow_start:k + 1]
                l_slice = regime_lows[slow_start:k + 1]
                ef = _ema_last(c_slice, regime_ema_fast)
                es = _ema_last(c_slice, regime_ema_slow)
                ad = _adx_wilder_last(h_slice, l_slice, c_slice, regime_adx_length)
                if math.isnan(ef) or math.isnan(es) or math.isnan(ad):
                    continue
                trend_on_t = (ef >= es) and (ad >= regime_adx_threshold)
                trend_ready = True
                break

        if not trend_ready:
            # pandas replay `continue`s here — volok_arr[t] stays False too.
            continue

        trend_arr[t] = trend_on_t

        # vol_ok on FAST_MAX_RECORDS ending at t (only when regime is ready)
        fast_start = t - FAST_MAX_RECORDS + 1
        if fast_start < 0:
            fast_start = 0
        v_slice = fast_volumes[fast_start:t + 1]
        volok_arr[t] = _rolling_volume_quantile_ok_last(
            v_slice, volume_filter_window, min_volume_quantile,
        )

    return trend_arr, volok_arr


def compute_controller_compat_ema_numba(
    *,
    fast_timestamps: np.ndarray,
    fast_volumes: np.ndarray,
    regime_timestamps: np.ndarray,
    regime_highs: np.ndarray,
    regime_lows: np.ndarray,
    regime_closes: np.ndarray,
    regime_ema_fast: int,
    regime_ema_slow: int,
    regime_adx_length: int,
    regime_adx_threshold: float,
    volume_filter_window: int,
    min_volume_quantile: float,
):
    """Public entrypoint. Returns (trend_on, vol_ok) bool arrays of length n_fast."""
    return _run_ema_kernel(
        np.ascontiguousarray(fast_timestamps, dtype=np.int64),
        np.ascontiguousarray(fast_volumes, dtype=np.float64),
        np.ascontiguousarray(regime_timestamps, dtype=np.int64),
        np.ascontiguousarray(regime_highs, dtype=np.float64),
        np.ascontiguousarray(regime_lows, dtype=np.float64),
        np.ascontiguousarray(regime_closes, dtype=np.float64),
        int(regime_ema_fast), int(regime_ema_slow),
        int(regime_adx_length), float(regime_adx_threshold),
        int(volume_filter_window), float(min_volume_quantile),
    )
