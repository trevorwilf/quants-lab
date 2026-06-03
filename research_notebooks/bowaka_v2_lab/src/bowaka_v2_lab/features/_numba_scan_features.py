"""Numba scan-feature kernels (walk-forward numba speedup, Phase 1).

Compiled, parity-gated kernels that replicate the EXACT pure-Python scan-feature
math in :mod:`bowaka_v2_lab.features.forming_bar` — the prior-daily baselines
(``compute_prior_daily_baselines``) and the per-scan forming aggregate + features
(``aggregate_forming_session_bar`` + ``_fallback_curve_fraction`` +
``compute_forming_session_features``). They drive the scan-matrix BUILD hot loop
and the legacy scan; both call sites share these kernels so the build path and
the scan path stay mutually parity-equal.

Contract (see ``docs/walkforward_numba_runbook.md``):

* Default OFF. Enabled only by ``optuna.acceleration.numba.enabled`` + an
  installed numba. When numba is absent the ``njit`` decorator is a no-op and the
  kernels run as ordinary (interpreted) Python with identical semantics.
* No ``fastmath`` / ``parallel`` / ``prange`` over reductions.
* Recursive EMAs (``_ewm_mean_series``, reused verbatim from market_lab's
  ``_numba_indicators``) are bit-exact vs ``pandas.ewm(adjust=False)``.
* Sums (``session_volume``; the rolling means in the baselines) use the canonical
  sequential order, which matches numpy/pandas reductions to ~1e-13 — within the
  1e-10 float tolerance the parity tests use, exactly as market_lab's Bollinger
  ``bbp`` kernel does. The float guards reproduce the pure-Python truthiness
  semantics (a ``0.0`` baseline yields ``None``/NaN, not a division; a real
  ``0.0`` feature is preserved, matching ``_none_to_nan``).
"""

from __future__ import annotations

import math

import numpy as np

from ._numba_availability import _NUMBA_AVAILABLE

if _NUMBA_AVAILABLE:
    from numba import njit  # type: ignore
else:  # pragma: no cover - exercised only when numba is not installed
    def njit(*args, **kwargs):  # type: ignore
        """No-op fallback decorator so kernel bodies run as plain Python."""
        if args and callable(args[0]):
            return args[0]

        def _wrap(fn):
            return fn

        return _wrap


_NAN = math.nan


# --------------------------------------------------------------------------
# Reused recurrence — verbatim from market_lab pmm_lab/features/_numba_indicators.py
# (bit-exact vs pandas ewm(alpha=..., adjust=False, min_periods=...).mean()).
# --------------------------------------------------------------------------
@njit(cache=True)
def _ewm_mean_series(values: np.ndarray, alpha: float, min_periods: int) -> np.ndarray:
    """Full-series ewm(adjust=False) mean; NaN-masked during warmup, NaN-carried."""
    n = values.shape[0]
    out = np.empty(n, dtype=np.float64)
    ema_prev = math.nan
    one_minus_alpha = 1.0 - alpha
    seeded = False
    n_seen = 0
    for i in range(n):
        x = values[i]
        if math.isnan(x):
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


# --------------------------------------------------------------------------
# Volume curve — exact ``_fallback_curve_fraction`` (forming_bar.py:235-243).
# The matrix builder always passes ``volume_curve=None`` so this fallback is the
# only curve the matrix bakes; the legacy scan uses it too when no curve is wired.
# --------------------------------------------------------------------------
@njit(cache=True)
def _fallback_curve_fraction_nb(minute_of_day: int, fallback_opening_15m_share: float) -> float:
    if minute_of_day <= 0:
        return 0.0
    if minute_of_day <= 15:
        return fallback_opening_15m_share * (minute_of_day / 15.0)
    remainder_minutes = 390.0 - 15.0
    remainder_share = 1.0 - fallback_opening_15m_share
    if remainder_share < 0.0:
        remainder_share = 0.0
    extra = remainder_share * ((minute_of_day - 15) / remainder_minutes)
    val = fallback_opening_15m_share + extra
    return val if val < 1.0 else 1.0


# --------------------------------------------------------------------------
# Forming features — exact ``compute_forming_session_features``
# (forming_bar.py:249-311). Shared by the BUILD batch kernel and the legacy
# scan so both produce identical features. NaN stands for the pure-Python
# ``None`` on every input; the ``> 0`` guards reproduce the truthiness checks
# (a ``0.0`` baseline yields a ``None``/NaN feature). Returns an 8-vector:
# [expected_volume_until_scan, rvol_so_far, projected_full_day_rvol,
#  range_expansion_so_far, close_location_so_far, ema_distance,
#  current_return_pct, gap_pct].
# --------------------------------------------------------------------------
@njit(cache=True)
def _forming_features_nb(
    sess_vol: float, sess_range: float, sess_high: float, sess_low: float,
    last_price: float, sess_open: float, vcf: float,
    avg_volume_20d: float, prior_atr_14d: float, prior_close: float,
    ema_10_prior: float,
) -> np.ndarray:
    out = np.full(8, _NAN, dtype=np.float64)
    avgv = avg_volume_20d
    atr = prior_atr_14d
    emap = ema_10_prior
    pc = prior_close

    if (not math.isnan(avgv)) and avgv > 0.0 and vcf > 0.0:
        expv = avgv * vcf
        out[0] = expv
    else:
        expv = _NAN
    if (not math.isnan(expv)) and (not math.isnan(sess_vol)):
        out[1] = sess_vol / expv
    if (not math.isnan(avgv)) and avgv > 0.0 and vcf > 0.0 and (not math.isnan(sess_vol)):
        out[2] = (sess_vol / vcf) / avgv
    if (not math.isnan(atr)) and atr > 0.0 and (not math.isnan(sess_range)):
        out[3] = sess_range / atr
    if ((not math.isnan(sess_high)) and (not math.isnan(sess_low))
            and (not math.isnan(last_price)) and (sess_high - sess_low) > 0.0):
        out[4] = (last_price - sess_low) / (sess_high - sess_low)
    if (not math.isnan(emap)) and emap > 0.0 and (not math.isnan(last_price)):
        out[5] = last_price / emap - 1.0
    if (not math.isnan(pc)) and pc > 0.0 and (not math.isnan(last_price)):
        out[6] = last_price / pc - 1.0
    if (not math.isnan(pc)) and pc > 0.0 and (not math.isnan(sess_open)):
        out[7] = sess_open / pc - 1.0
    return out


# --------------------------------------------------------------------------
# Prior-daily baselines — exact ``compute_prior_daily_baselines``
# (forming_bar.py:42-112). NOTE: the ATR baseline is a SIMPLE mean of the last
# ``atr_n`` true-range values (NOT Wilder), and the EMA is span/adjust=False.
# Returns an 8-vector; ``NaN`` stands for the pure-Python ``None``.
# --------------------------------------------------------------------------
@njit(cache=True)
def compute_baselines_nb(
    close: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    volume: np.ndarray,
    atr_n: int,
    lookback: int,
    ema_n: int,
    ema_slope_lookback: int,
) -> np.ndarray:
    """[prior_close, prior_atr_14d, prior_atr_pct, avg_volume_20d,
        avg_dollar_volume_20d, ema_10_prior, ema_10_lag_3, ema_slope_prior]."""
    out = np.full(8, _NAN, dtype=np.float64)
    n = close.shape[0]
    if n == 0:
        return out

    prior_close = close[n - 1]
    out[0] = prior_close

    # prior_atr_14d: mean of the last atr_n TR values, requires len(tr) >= atr_n+1.
    # tr[0] = high[0]-low[0]; tr[i>=1] = max(h-l, |h-prevclose|, |l-prevclose|).
    if n >= atr_n + 1:
        s = 0.0
        for i in range(n - atr_n, n):
            if i == 0:
                tr = high[0] - low[0]
            else:
                pc = close[i - 1]
                a = high[i] - low[i]
                b = abs(high[i] - pc)
                c = abs(low[i] - pc)
                tr = a
                if b > tr:
                    tr = b
                if c > tr:
                    tr = c
            s += tr
        prior_atr_14d = s / atr_n
        out[1] = prior_atr_14d
        if (not math.isnan(prior_close)) and prior_close > 0.0:
            out[2] = prior_atr_14d / prior_close

    # avg_volume_20d / avg_dollar_volume_20d: simple mean of the last `lookback`.
    if n >= lookback:
        sv = 0.0
        sdv = 0.0
        for i in range(n - lookback, n):
            sv += volume[i]
            sdv += close[i] * volume[i]
        out[3] = sv / lookback
        out[4] = sdv / lookback

    # EMA(span=ema_n, adjust=False) — full series, no min_periods (pandas default
    # min_periods=0). Requires len >= ema_n + ema_slope_lookback to be computed.
    if n >= ema_n + ema_slope_lookback:
        alpha = 2.0 / (ema_n + 1.0)
        ema_series = _ewm_mean_series(close, alpha, 0)
        ema_10_prior = ema_series[n - 1]
        ema_10_lag_3 = ema_series[n - (ema_slope_lookback + 1)]
        out[5] = ema_10_prior
        out[6] = ema_10_lag_3
        if ema_10_lag_3 != 0.0:
            out[7] = ema_10_prior / ema_10_lag_3 - 1.0

    return out


# --------------------------------------------------------------------------
# Build hot-loop kernel — replicates the per-(scan_ts, symbol) inner loop of
# ``build_session_partition`` (scan_matrix.py:575-643) for ONE symbol over all
# scans: aggregate_forming_session_bar + fallback vcf + compute_forming_session_
# features, written into the matrix-column layout (NaN / -1 / 0 defaults).
#
# Bars MUST be sorted ascending by ts (callers sort). Returns a fixed-order tuple
# of per-scan arrays the caller assigns into the dyn_* matrix columns.
# --------------------------------------------------------------------------
@njit(cache=True)
def build_session_columns_nb(
    bar_ts_ns: np.ndarray,
    b_open: np.ndarray,
    b_high: np.ndarray,
    b_low: np.ndarray,
    b_close: np.ndarray,
    b_volume: np.ndarray,
    scan_ts_ns: np.ndarray,
    scan_minute_of_day: np.ndarray,
    has_baseline: bool,
    avg_volume_20d: float,
    prior_atr_14d: float,
    prior_close: float,
    ema_10_prior: float,
    fallback_share: float,
):
    n_scans = scan_ts_ns.shape[0]
    n_bars = bar_ts_ns.shape[0]

    has_bar = np.zeros(n_scans, dtype=np.uint8)
    has_valid_ts = np.zeros(n_scans, dtype=np.uint8)
    has_bl = np.zeros(n_scans, dtype=np.uint8)
    last_bar_ts_ns = np.full(n_scans, -1, dtype=np.int64)

    s_open = np.full(n_scans, _NAN, dtype=np.float64)
    s_high = np.full(n_scans, _NAN, dtype=np.float64)
    s_low = np.full(n_scans, _NAN, dtype=np.float64)
    s_last = np.full(n_scans, _NAN, dtype=np.float64)
    s_vol = np.full(n_scans, _NAN, dtype=np.float64)
    s_range = np.full(n_scans, _NAN, dtype=np.float64)
    bar_age = np.full(n_scans, _NAN, dtype=np.float64)

    vcf_out = np.full(n_scans, _NAN, dtype=np.float64)
    expv_out = np.full(n_scans, _NAN, dtype=np.float64)
    rvol_out = np.full(n_scans, _NAN, dtype=np.float64)
    proj_out = np.full(n_scans, _NAN, dtype=np.float64)
    rexp_out = np.full(n_scans, _NAN, dtype=np.float64)
    cloc_out = np.full(n_scans, _NAN, dtype=np.float64)
    edist_out = np.full(n_scans, _NAN, dtype=np.float64)
    cret_out = np.full(n_scans, _NAN, dtype=np.float64)
    gap_out = np.full(n_scans, _NAN, dtype=np.float64)

    j = 0
    opened = False
    first_open = _NAN
    cum_high = -math.inf
    cum_low = math.inf
    cum_vol = 0.0
    last_close = _NAN
    last_ts = -1

    for t in range(n_scans):
        sc = scan_ts_ns[t]
        while j < n_bars and bar_ts_ns[j] <= sc:
            if not opened:
                first_open = b_open[j]
                opened = True
            if b_high[j] > cum_high:
                cum_high = b_high[j]
            if b_low[j] < cum_low:
                cum_low = b_low[j]
            cum_vol += b_volume[j]
            last_close = b_close[j]
            last_ts = bar_ts_ns[j]
            j += 1

        if j < 1:
            continue  # no bars at/through this scan; keep defaults

        has_bar[t] = 1
        s_open[t] = first_open
        s_high[t] = cum_high
        s_low[t] = cum_low
        s_last[t] = last_close
        s_vol[t] = cum_vol
        rng = cum_high - cum_low
        s_range[t] = rng
        last_bar_ts_ns[t] = last_ts
        has_valid_ts[t] = 1
        bar_age[t] = (sc - last_ts) / 1.0e9

        if not has_baseline:
            continue
        has_bl[t] = 1

        vcf = _fallback_curve_fraction_nb(scan_minute_of_day[t], fallback_share)
        vcf_out[t] = vcf
        f = _forming_features_nb(
            cum_vol, rng, cum_high, cum_low, last_close, first_open, vcf,
            avg_volume_20d, prior_atr_14d, prior_close, ema_10_prior,
        )
        expv_out[t] = f[0]
        rvol_out[t] = f[1]
        proj_out[t] = f[2]
        rexp_out[t] = f[3]
        cloc_out[t] = f[4]
        edist_out[t] = f[5]
        cret_out[t] = f[6]
        gap_out[t] = f[7]

    return (
        has_bar, has_valid_ts, has_bl, last_bar_ts_ns,
        s_open, s_high, s_low, s_last, s_vol, s_range, bar_age,
        vcf_out, expv_out, rvol_out, proj_out, rexp_out, cloc_out,
        edist_out, cret_out, gap_out,
    )


__all__ = [
    "_NUMBA_AVAILABLE",
    "_ewm_mean_series",
    "_fallback_curve_fraction_nb",
    "_forming_features_nb",
    "compute_baselines_nb",
    "build_session_columns_nb",
]
