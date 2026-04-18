"""Stateless single-bar-output indicator primitives for the Numba kernels.

Each function takes a 1D float64 numpy array (a slice of the full series) and
returns the LAST value of the indicator over that slice — mirroring what the
pandas replay path does when it calls `bollinger_percent_b(c, ...).iloc[-1]`.

Semantics must match the pandas reference in `ta_utils_shim.py` exactly:

- `ema`                → pandas.ewm(span=length, adjust=False, min_periods=length).mean()
- `rsi_wilder`         → ewm(alpha=1/length, adjust=False, min_periods=length).mean()
                         on gain/loss from close.diff(), with edge cases:
                           gain>0, loss=0  → 100   (all-gain window)
                           gain=0, loss>0  → 0     (all-loss window)
                           gain=0, loss=0  → 50    (flat window)
                         Returns NaN if either avg_gain or avg_loss is in warmup.
- `atr_wilder`         → ewm(alpha=1/length, adjust=False, min_periods=length).mean()
                         on true_range, with TR[0] = high[0] - low[0] (prev_close NaN
                         → the other two TR components are NaN → max ignores NaN).
- `bollinger_percent_b`→ mid = rolling(length).mean(); sd = rolling(length).std(ddof=0)
                         upper = mid + std*sd; lower = mid - std*sd
                         bbp = (close - lower) / (upper - lower)  (NaN if upper==lower)
                         **NOTE: pandas ddof=0 is population std, NOT ddof=1 sample.**
- `rolling_volume_quantile_ok`
                       → threshold = volume.rolling(window).quantile(q).shift(1)
                         ok = threshold.isna() | (volume >= threshold)
                         **linear interpolation** between bracketing values.

If Numba is installed, each function is `@njit(cache=True)`. If not, the
pure-Python definitions (identical numeric code) serve as the fallback.
"""

from __future__ import annotations

import math

import numpy as np

from pmm_lab.features._numba_availability import _NUMBA_AVAILABLE

if _NUMBA_AVAILABLE:
    from numba import njit, prange  # type: ignore
else:
    # Fallback decorator: no-op so the same function body works without Numba.
    def njit(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]
        def _wrap(fn):
            return fn
        return _wrap

    def prange(n):  # noqa: D401
        return range(n)


# ────────────────────────────────────────────────────────────────────────────
# Pandas-parity EWM helper — `ewm(alpha=..., adjust=False, min_periods=N).mean()`
#
# pandas semantics with adjust=False, min_periods=N:
#   - y[0] = x[0]
#   - y[t] = alpha * x[t] + (1-alpha) * y[t-1]   for t >= 1
#   - Outputs BEFORE index (N-1) are masked as NaN (min_periods gate).
#   - BUT the RECURRENCE itself still starts at bar 0 using x[0] as the seed.
#   - NaN handling: a NaN input resets nothing; pandas carries the previous
#     ema_prev through. (Empirically: `pd.Series([np.nan, 1.0, 2.0]).ewm(...).mean()`
#     produces [NaN, 1.0, alpha*2+(1-alpha)*1] when adjust=False.)
#
# For our Numba primitives the input slices do not contain NaN (we only call
# on slices of pure float OHLCV arrays), so we implement the simple recurrence
# and apply the min_periods mask at the end.
# ────────────────────────────────────────────────────────────────────────────


@njit(cache=True)
def _ewm_mean_last(values: np.ndarray, alpha: float, min_periods: int) -> float:
    """Return the last value of ewm(alpha=alpha, adjust=False, min_periods=...).mean().

    If len(values) < min_periods → NaN.
    If NaN appears in values, it is carried (ema stays at previous value for
    that bar — matches pandas adjust=False behavior).
    """
    n = values.shape[0]
    if n < min_periods:
        return math.nan

    ema_prev = math.nan
    one_minus_alpha = 1.0 - alpha
    # Find first non-NaN to seed the recurrence
    seeded = False
    last = math.nan
    for i in range(n):
        x = values[i]
        if math.isnan(x):
            # Pandas adjust=False: carry ema_prev unchanged through NaN inputs
            last = ema_prev
            continue
        if not seeded:
            ema_prev = x
            seeded = True
        else:
            ema_prev = alpha * x + one_minus_alpha * ema_prev
        last = ema_prev
    return last


@njit(cache=True)
def _ewm_mean_series(values: np.ndarray, alpha: float, min_periods: int) -> np.ndarray:
    """Full-series version of `_ewm_mean_last` (returns array matching pandas)."""
    n = values.shape[0]
    out = np.empty(n, dtype=np.float64)
    ema_prev = math.nan
    one_minus_alpha = 1.0 - alpha
    seeded = False
    # Track how many non-NaN inputs we've seen; NaN outputs until min_periods.
    n_seen = 0
    for i in range(n):
        x = values[i]
        if math.isnan(x):
            # Carry ema_prev; do not increment n_seen.
            out[i] = math.nan if n_seen < min_periods else ema_prev
            continue
        n_seen += 1
        if not seeded:
            ema_prev = x
            seeded = True
        else:
            ema_prev = alpha * x + one_minus_alpha * ema_prev
        out[i] = math.nan if n_seen < min_periods else ema_prev
    return out


# ────────────────────────────────────────────────────────────────────────────
# EMA — `ewm(span=length, adjust=False, min_periods=length).mean()`
# alpha = 2 / (length + 1)
# ────────────────────────────────────────────────────────────────────────────


@njit(cache=True)
def _ema_last(values: np.ndarray, length: int) -> float:
    if length <= 0:
        return math.nan
    alpha = 2.0 / (length + 1.0)
    return _ewm_mean_last(values, alpha, length)


@njit(cache=True)
def _ema_diff_last(values: np.ndarray, length: int) -> float:
    """EMA slope = EMA(last) - EMA(second-to-last). Matches `ema(...).diff().iloc[-1]`."""
    n = values.shape[0]
    if n < length + 1:
        return math.nan
    # Compute EMA over the full slice and take the last two values.
    alpha = 2.0 / (length + 1.0)
    ema_series = _ewm_mean_series(values, alpha, length)
    prev = ema_series[n - 2]
    curr = ema_series[n - 1]
    if math.isnan(prev) or math.isnan(curr):
        return math.nan
    return curr - prev


# ────────────────────────────────────────────────────────────────────────────
# Wilder RSI — ewm(alpha=1/length, adjust=False, min_periods=length)
# ────────────────────────────────────────────────────────────────────────────


@njit(cache=True)
def _rsi_wilder_last(closes: np.ndarray, length: int) -> float:
    n = closes.shape[0]
    # pandas diff() produces NaN at bar 0; so gain/loss have NaN at bar 0.
    # ewm with min_periods=length on a series whose first value is NaN needs
    # at least `length` non-NaN updates. That means we need at least length+1
    # closes (for length diffs) to fully warm up. Match pandas exactly:
    # avg_gain and avg_loss must each have had min_periods=length non-NaN
    # observations before they return a non-NaN value.
    if n < length + 1:
        return math.nan
    alpha = 1.0 / length
    one_minus_alpha = 1.0 - alpha

    avg_gain = math.nan
    avg_loss = math.nan
    seeded = False
    n_seen = 0  # count of non-NaN gain/loss observations (both are NaN at bar 0 only)
    # Iterate over diff array logically — we skip index 0 (NaN) and process 1..n-1.
    for i in range(1, n):
        delta = closes[i] - closes[i - 1]
        gain = delta if delta > 0.0 else 0.0
        loss = -delta if delta < 0.0 else 0.0
        n_seen += 1
        if not seeded:
            avg_gain = gain
            avg_loss = loss
            seeded = True
        else:
            avg_gain = alpha * gain + one_minus_alpha * avg_gain
            avg_loss = alpha * loss + one_minus_alpha * avg_loss

    if n_seen < length:
        return math.nan
    if math.isnan(avg_gain) or math.isnan(avg_loss):
        return math.nan

    # Edge cases (match ta_utils_shim.rsi_wilder exactly)
    if avg_gain > 0.0 and avg_loss == 0.0:
        return 100.0
    if avg_gain == 0.0 and avg_loss > 0.0:
        return 0.0
    if avg_gain == 0.0 and avg_loss == 0.0:
        return 50.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


# ────────────────────────────────────────────────────────────────────────────
# Wilder ATR — TR ewm with alpha=1/length, TR[0] = high[0]-low[0]
# (because prev_close NaN causes the |high-prev| and |low-prev| components
# to be NaN, and pandas `.max(axis=1)` ignores NaN, so TR[0] = high-low)
# ────────────────────────────────────────────────────────────────────────────


@njit(cache=True)
def _atr_wilder_last(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                      length: int) -> float:
    n = highs.shape[0]
    if n < length:
        return math.nan
    alpha = 1.0 / length
    one_minus_alpha = 1.0 - alpha

    atr_prev = math.nan
    seeded = False
    n_seen = 0
    for i in range(n):
        if i == 0:
            tr = highs[0] - lows[0]
        else:
            pc = closes[i - 1]
            a = highs[i] - lows[i]
            b = abs(highs[i] - pc)
            c = abs(lows[i] - pc)
            tr = a
            if b > tr:
                tr = b
            if c > tr:
                tr = c
        n_seen += 1
        if not seeded:
            atr_prev = tr
            seeded = True
        else:
            atr_prev = alpha * tr + one_minus_alpha * atr_prev

    if n_seen < length:
        return math.nan
    return atr_prev


# ────────────────────────────────────────────────────────────────────────────
# Bollinger %B (last) — mid + std*sd, bbp = (close-lower) / (upper-lower)
# sd uses ddof=0 (population std).
# ────────────────────────────────────────────────────────────────────────────


@njit(cache=True)
def _bollinger_percent_b_last(closes: np.ndarray, length: int, num_std: float) -> float:
    n = closes.shape[0]
    if n < length:
        return math.nan
    # Window = last `length` values
    start = n - length
    # Mean
    total = 0.0
    for i in range(start, n):
        total += closes[i]
    mean = total / length
    # Population std (ddof=0)
    sq = 0.0
    for i in range(start, n):
        d = closes[i] - mean
        sq += d * d
    sd = math.sqrt(sq / length)
    upper = mean + num_std * sd
    lower = mean - num_std * sd
    rng = upper - lower
    if rng == 0.0:
        return math.nan
    return (closes[n - 1] - lower) / rng


# ────────────────────────────────────────────────────────────────────────────
# Wilder ADX — replicates ta_utils_shim.adx_wilder bar-by-bar.
#
# plus_dm[t]  = (up_move > down_move) & (up_move > 0)  ? up_move   : 0  (NaN-safe; NaN → False)
# minus_dm[t] = (down_move > up_move) & (down_move > 0) ? down_move : 0
# atr         = atr_wilder(high, low, close, length)
# plus_di     = 100 * ewm(plus_dm, alpha=1/length) / atr  (NaN where atr==0)
# minus_di    = 100 * ewm(minus_dm, alpha=1/length) / atr
# dx          = 100 * |plus_di - minus_di| / (plus_di + minus_di)  (NaN where sum==0)
# adx         = ewm(dx, alpha=1/length, min_periods=length)
#
# Because ADX needs `min_periods=length` on BOTH the inner (plus/minus_di via
# plus/minus_dm ewm) AND the outer ewm (dx ewm), the full-length warmup is
# approximately 2*length bars.
# ────────────────────────────────────────────────────────────────────────────


@njit(cache=True)
def _adx_wilder_last(
    highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, length: int,
) -> float:
    n = highs.shape[0]
    if n < length + 1:
        return math.nan

    alpha = 1.0 / length
    one_minus_alpha = 1.0 - alpha

    # Running averages (ewm with adjust=False, seeded by first non-NaN value,
    # min_periods=length)
    atr_prev = math.nan
    atr_seeded = False
    atr_n_seen = 0
    plus_dm_ewm = math.nan
    minus_dm_ewm = math.nan
    dm_seeded = False
    dm_n_seen = 0
    # Outer ewm over dx
    adx_prev = math.nan
    adx_seeded = False
    adx_n_seen = 0

    # plus_di/minus_di have NaN where atr is NaN (i.e. during atr warmup) or atr==0.
    # Those NaN feed into dx (via division), which propagates NaN into the dx ewm.
    # Pandas ewm with adjust=False carries ema_prev through NaN inputs without
    # incrementing min_periods count. Match that behavior explicitly.
    for i in range(n):
        # ATR recurrence (same as _atr_wilder_last)
        if i == 0:
            tr = highs[0] - lows[0]
        else:
            pc = closes[i - 1]
            a = highs[i] - lows[i]
            b = abs(highs[i] - pc)
            c = abs(lows[i] - pc)
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
            atr_prev = alpha * tr + one_minus_alpha * atr_prev
        atr_out = atr_prev if atr_n_seen >= length else math.nan

        # +DM, -DM
        if i == 0:
            # up_move = NaN, down_move = NaN → both NaN > X are False → dm values are 0
            plus_dm = 0.0
            minus_dm = 0.0
        else:
            up_move = highs[i] - highs[i - 1]
            down_move = -(lows[i] - lows[i - 1])
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
            plus_dm_ewm = alpha * plus_dm + one_minus_alpha * plus_dm_ewm
            minus_dm_ewm = alpha * minus_dm + one_minus_alpha * minus_dm_ewm
        plus_dm_out = plus_dm_ewm if dm_n_seen >= length else math.nan
        minus_dm_out = minus_dm_ewm if dm_n_seen >= length else math.nan

        # plus_di, minus_di
        if math.isnan(atr_out) or atr_out == 0.0 or math.isnan(plus_dm_out):
            plus_di = math.nan
        else:
            plus_di = 100.0 * plus_dm_out / atr_out
        if math.isnan(atr_out) or atr_out == 0.0 or math.isnan(minus_dm_out):
            minus_di = math.nan
        else:
            minus_di = 100.0 * minus_dm_out / atr_out

        # dx
        if math.isnan(plus_di) or math.isnan(minus_di):
            dx = math.nan
        else:
            s = plus_di + minus_di
            if s == 0.0:
                dx = math.nan
            else:
                dx = 100.0 * abs(plus_di - minus_di) / s

        # adx — outer ewm(alpha=1/length, min_periods=length) on dx
        # Pandas adjust=False with NaN inputs: carry the previous value; do NOT
        # increment the min_periods counter.
        if not math.isnan(dx):
            adx_n_seen += 1
            if not adx_seeded:
                adx_prev = dx
                adx_seeded = True
            else:
                adx_prev = alpha * dx + one_minus_alpha * adx_prev
        # If dx is NaN, adx_prev and adx_n_seen are unchanged (pandas carries)

    if adx_n_seen < length:
        return math.nan
    return adx_prev


# ────────────────────────────────────────────────────────────────────────────
# Rolling volume quantile — linear interpolation
# threshold[t] = quantile(volumes[t-window:t], q)   (computed as rolling.quantile.shift(1))
# ok[t] = threshold.isna() | (volumes[t] >= threshold[t])
# ────────────────────────────────────────────────────────────────────────────


@njit(cache=True)
def _linear_quantile(sorted_vals: np.ndarray, q: float) -> float:
    """Compute q-th quantile using pandas' default linear interpolation.

    For a sorted array of length n, position = q * (n - 1). Integer part is the
    lower index; fractional part is the interpolation weight toward the upper.
    """
    n = sorted_vals.shape[0]
    if n == 0:
        return math.nan
    if n == 1:
        return sorted_vals[0]
    pos = q * (n - 1)
    lo = int(pos)
    hi = lo + 1
    if hi >= n:
        return sorted_vals[n - 1]
    frac = pos - lo
    return sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac


@njit(cache=True)
def _rolling_volume_quantile_ok_last(volumes: np.ndarray, window: int,
                                       quantile_threshold: float) -> bool:
    """Reproduces `rolling_volume_quantile_ok(volume, window, q).iloc[-1]`.

    ok[t] = threshold.isna() | (volume[t] >= threshold[t])
    threshold[t] = quantile(volumes[t-window:t], q)  (i.e., rolling.quantile.shift(1))

    For the LAST bar (index n-1), threshold = quantile of volumes[n-1-window : n-1]
    (i.e., a window of length `window` ending at index n-2). If n < window + 1,
    threshold is NaN → returns True.
    """
    if window <= 0 or quantile_threshold <= 0.0:
        return True
    n = volumes.shape[0]
    # threshold is NaN for bars where the rolling has not yet accumulated `window`
    # non-NaN observations. After .shift(1), the first `window` bars have NaN
    # threshold. For the last bar (index n-1), we need volumes[n-1-window:n-1]
    # to have exactly `window` values.
    if n < window + 1:
        return True  # threshold isna() → ok=True
    # Sort volumes[n-1-window:n-1]
    start = n - 1 - window
    end = n - 1  # exclusive
    # Copy slice into a local buffer and sort in-place
    buf = np.empty(window, dtype=np.float64)
    for i in range(window):
        buf[i] = volumes[start + i]
    # Sort ascending (use numpy sort, supported under numba)
    buf.sort()
    threshold = _linear_quantile(buf, quantile_threshold)
    if math.isnan(threshold):
        return True
    return volumes[n - 1] >= threshold
