"""Bowaka v2 — pure-function feature module.

Port of the v2 archive's ``bowaka_v2_features.py`` with the §15 remediations
applied:

- ``instrument_gate``: **fail-closed by default**. The archive defaulted to
  fail-OPEN when ``instrument_class is None``; per [Report §8.6] this is a
  data-quality risk because a missing class would silently pass. The new
  signature requires either an explicit class or
  ``allow_unknown_for_research=True``.
- ``_et_minute_of_day``: uses ``require_aware_timestamp()`` from
  ``bowaka_v2_lab.utils.time`` per [Report §8.5]. The archive silently
  localised naive timestamps to UTC, which produces wrong ET minutes when
  the input was actually local clock time.

Causality (handoff §5.7 + Appendix B):

- prior_atr_14d / avg_volume_20d / avg_dollar_volume_20d / ema_10_prior are
  computed from completed daily bars only — the input frame MUST end on
  the prior session. Functions enforce this only by indexing from the tail;
  callers are responsible for slicing.
- Forming-session features use minute bars up to the scan time ``t``; bars
  at or beyond ``t+1`` minute must not be in the input frame.
- Volume curve is causal: it is built from prior sessions only.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from ..utils.time import require_aware_timestamp


# ---------------------------------------------------------------- prior baselines


def compute_prior_daily_baselines(
    daily_bars_df: pd.DataFrame,
    *,
    atr_n: int = 14,
    lookback: int = 20,
    ema_n: int = 10,
    ema_slope_lookback: int = 3,
) -> dict[str, float | None]:
    """Compute prior-daily baselines (ATR / volume / EMA) used by the scanner.

    See module docstring for the causality contract.
    """
    if daily_bars_df is None or len(daily_bars_df) == 0:
        return _empty_baselines()

    df = daily_bars_df.copy()
    df.columns = [c.lower() for c in df.columns]
    needed = {"open", "high", "low", "close", "volume"}
    if not needed.issubset(df.columns):
        return _empty_baselines()

    df["prev_close"] = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["prev_close"]).abs(),
        (df["low"] - df["prev_close"]).abs(),
    ], axis=1).max(axis=1)
    if len(tr) >= atr_n + 1:
        prior_atr_14d = float(tr.iloc[-atr_n:].mean())
    else:
        prior_atr_14d = None

    prior_close = float(df["close"].iloc[-1]) if len(df) > 0 else None
    prior_atr_pct = (
        prior_atr_14d / prior_close
        if (prior_atr_14d is not None and prior_close and prior_close > 0)
        else None
    )

    if len(df) >= lookback:
        avg_volume_20d = float(df["volume"].iloc[-lookback:].mean())
        avg_dollar_volume_20d = float(
            (df["close"].iloc[-lookback:] * df["volume"].iloc[-lookback:]).mean()
        )
    else:
        avg_volume_20d = None
        avg_dollar_volume_20d = None

    if len(df) >= ema_n + ema_slope_lookback:
        ema_series = df["close"].ewm(span=ema_n, adjust=False).mean()
        ema_10_prior = float(ema_series.iloc[-1])
        ema_10_lag_3 = float(ema_series.iloc[-(ema_slope_lookback + 1)])
        ema_slope_prior = (
            ema_10_prior / ema_10_lag_3 - 1.0
            if ema_10_lag_3 != 0.0 else None
        )
    else:
        ema_10_prior = None
        ema_10_lag_3 = None
        ema_slope_prior = None

    return {
        "prior_close": prior_close,
        "prior_atr_14d": prior_atr_14d,
        "prior_atr_pct": prior_atr_pct,
        "avg_volume_20d": avg_volume_20d,
        "avg_dollar_volume_20d": avg_dollar_volume_20d,
        "ema_10_prior": ema_10_prior,
        "ema_10_lag_3": ema_10_lag_3,
        "ema_slope_prior": ema_slope_prior,
    }


def _empty_baselines() -> dict[str, float | None]:
    return {
        "prior_close": None,
        "prior_atr_14d": None,
        "prior_atr_pct": None,
        "avg_volume_20d": None,
        "avg_dollar_volume_20d": None,
        "ema_10_prior": None,
        "ema_10_lag_3": None,
        "ema_slope_prior": None,
    }


# ---------------------------------------------------------------- forming session


def aggregate_forming_session_bar(
    minute_bars_through_t: pd.DataFrame,
) -> dict[str, float | None]:
    """Aggregate minute bars up to scan time ``t`` into a forming session summary."""
    if minute_bars_through_t is None or len(minute_bars_through_t) == 0:
        return {
            "session_open": None, "session_high": None,
            "session_low": None, "last_price": None,
            "session_volume": None, "session_range": None,
            "last_bar_timestamp": None,
        }
    df = minute_bars_through_t
    cols = {c.lower(): c for c in df.columns}
    open_col = cols.get("open")
    high_col = cols.get("high")
    low_col = cols.get("low")
    close_col = cols.get("close")
    vol_col = cols.get("volume")
    ts_col = cols.get("timestamp") or cols.get("ts")

    session_open = float(df[open_col].iloc[0]) if open_col else None
    session_high = float(df[high_col].max()) if high_col else None
    session_low = float(df[low_col].min()) if low_col else None
    last_price = float(df[close_col].iloc[-1]) if close_col else None
    session_vol = float(df[vol_col].sum()) if vol_col else None
    session_range = (
        session_high - session_low
        if (session_high is not None and session_low is not None)
        else None
    )
    last_ts = df[ts_col].iloc[-1] if ts_col else None
    if last_ts is not None:
        if isinstance(last_ts, (pd.Timestamp, datetime)):
            ts_obj = pd.Timestamp(last_ts)
            # Per [Report §8.5]: tz-aware required. Reject naive at ingest.
            if ts_obj.tzinfo is None:
                raise ValueError(
                    "aggregate_forming_session_bar: naive last_bar_timestamp rejected; "
                    "callers must supply tz-aware bar timestamps (see utils.time.require_aware_timestamp)"
                )
            last_ts = ts_obj.isoformat()
        else:
            last_ts = str(last_ts)
    return {
        "session_open": session_open,
        "session_high": session_high,
        "session_low": session_low,
        "last_price": last_price,
        "session_volume": session_vol,
        "session_range": session_range,
        "last_bar_timestamp": last_ts,
    }


# ---------------------------------------------------------------- volume curve


def compute_volume_curve_fraction(
    volume_curve_df: pd.DataFrame | None,
    t: Any,
    adv_bucket_label: str,
    *,
    fallback_opening_15m_share: float = 0.08,
) -> float:
    """Expected cumulative full-day volume fraction at scan time ``t``."""
    t_et_minute = _et_minute_of_day(t)

    if volume_curve_df is None or len(volume_curve_df) == 0:
        return _fallback_curve_fraction(t_et_minute, fallback_opening_15m_share)

    df = volume_curve_df
    cols = {c.lower(): c for c in df.columns}
    bucket_col = cols.get("adv_bucket")
    frac_col = cols.get("cumulative_fraction") or cols.get("fraction")
    min_col = cols.get("minute_of_day")
    if bucket_col is None or frac_col is None or min_col is None:
        return _fallback_curve_fraction(t_et_minute, fallback_opening_15m_share)

    sub = df[df[bucket_col] == adv_bucket_label]
    if len(sub) == 0:
        return _fallback_curve_fraction(t_et_minute, fallback_opening_15m_share)
    sub = sub.sort_values(min_col)
    minutes = sub[min_col].to_numpy(dtype=float)
    fractions = sub[frac_col].to_numpy(dtype=float)
    if t_et_minute <= minutes[0]:
        return float(max(min(fractions[0], 1.0), 0.0))
    if t_et_minute >= minutes[-1]:
        return float(max(min(fractions[-1], 1.0), 0.0))
    interp = float(np.interp(t_et_minute, minutes, fractions))
    return max(min(interp, 1.0), 0.0)


def _et_minute_of_day(t: Any) -> int:
    """ET minute-of-day [0..389] for a tz-aware scan timestamp.

    Per [Report §8.5] / fix to v2 source lines 273-284: naive timestamps are
    rejected via ``require_aware_timestamp`` rather than silently localised to UTC.
    """
    ts = require_aware_timestamp(t, label="_et_minute_of_day")
    et = ts.tz_convert("America/New_York")
    minute = (et.hour - 9) * 60 + (et.minute - 30)
    return max(0, min(minute, 389))


def _fallback_curve_fraction(minute_of_day: int, fallback_opening_15m_share: float) -> float:
    if minute_of_day <= 0:
        return 0.0
    if minute_of_day <= 15:
        return fallback_opening_15m_share * (minute_of_day / 15.0)
    remainder_minutes = 390 - 15
    remainder_share = max(0.0, 1.0 - fallback_opening_15m_share)
    extra = remainder_share * ((minute_of_day - 15) / remainder_minutes)
    return min(fallback_opening_15m_share + extra, 1.0)


# ---------------------------------------------------------------- forming features


def compute_forming_session_features(
    session_bar: dict[str, float | None],
    prior_baselines: dict[str, float | None],
    volume_curve_fraction: float,
) -> dict[str, float | None]:
    sess_open = session_bar.get("session_open")
    sess_high = session_bar.get("session_high")
    sess_low = session_bar.get("session_low")
    last_price = session_bar.get("last_price")
    sess_vol = session_bar.get("session_volume")
    sess_range = session_bar.get("session_range")

    prior_close = prior_baselines.get("prior_close")
    prior_atr_14d = prior_baselines.get("prior_atr_14d")
    avg_volume_20d = prior_baselines.get("avg_volume_20d")
    ema_10_prior = prior_baselines.get("ema_10_prior")

    if avg_volume_20d and avg_volume_20d > 0 and volume_curve_fraction > 0:
        expected_volume_until_scan = avg_volume_20d * volume_curve_fraction
    else:
        expected_volume_until_scan = None
    if expected_volume_until_scan and sess_vol is not None:
        rvol_so_far = sess_vol / expected_volume_until_scan
    else:
        rvol_so_far = None
    if avg_volume_20d and avg_volume_20d > 0 and volume_curve_fraction > 0 and sess_vol is not None:
        projected_full_day_rvol = (sess_vol / volume_curve_fraction) / avg_volume_20d
    else:
        projected_full_day_rvol = None

    if prior_atr_14d and prior_atr_14d > 0 and sess_range is not None:
        range_expansion_so_far = sess_range / prior_atr_14d
    else:
        range_expansion_so_far = None
    if (sess_high is not None and sess_low is not None
            and last_price is not None and (sess_high - sess_low) > 0):
        close_location_so_far = (last_price - sess_low) / (sess_high - sess_low)
    else:
        close_location_so_far = None

    if ema_10_prior and ema_10_prior > 0 and last_price is not None:
        ema_distance = last_price / ema_10_prior - 1.0
    else:
        ema_distance = None
    if prior_close and prior_close > 0 and last_price is not None:
        current_return_pct = last_price / prior_close - 1.0
    else:
        current_return_pct = None
    if prior_close and prior_close > 0 and sess_open is not None:
        gap_pct = sess_open / prior_close - 1.0
    else:
        gap_pct = None

    return {
        "rvol_so_far": rvol_so_far,
        "projected_full_day_rvol": projected_full_day_rvol,
        "range_expansion_so_far": range_expansion_so_far,
        "close_location_so_far": close_location_so_far,
        "ema_distance": ema_distance,
        "current_return_pct": current_return_pct,
        "gap_pct": gap_pct,
        "expected_volume_until_scan": expected_volume_until_scan,
    }


# ---------------------------------------------------------------- gates


def instrument_gate(
    instrument_class: str | None,
    *,
    allow_unknown_for_research: bool = False,
) -> bool:
    """Instrument-class gate.

    Per [Report §8.6] (fix for v2 source lines 473-477): the gate is
    fail-CLOSED by default. ``None`` rejects unless
    ``allow_unknown_for_research=True``. ``"operating_equity"`` always passes.
    Any other explicit class (e.g. ``"etf"``, ``"spac"``, ``"warrant"``,
    ``"adr"``) is rejected.
    """
    if instrument_class is None:
        return bool(allow_unknown_for_research)
    return instrument_class == "operating_equity"


def apply_v2_gates(
    features: dict[str, float | None],
    signals_cfg: dict,
    *,
    price: float | None = None,
    avg_dollar_volume_20d: float | None = None,
    prior_atr_pct: float | None = None,
    ema_slope_prior: float | None = None,
    instrument_class: str | None = None,
) -> tuple[bool, dict[str, bool]]:
    """Apply every v2 entry gate and return ``(all_passed, per_gate_results)``."""
    s = signals_cfg or {}
    gates: dict[str, bool] = {}

    price_min = _to_float(s.get("price_min"))
    price_max = _to_float(s.get("price_max"))
    gates["price_gate"] = _between(price, price_min, price_max)

    adv_min = _to_float(s.get("avg_dollar_volume_min"))
    adv_max = _to_float(s.get("avg_dollar_volume_max"))
    gates["avg_dollar_volume_gate"] = _between(
        avg_dollar_volume_20d, adv_min, adv_max,
    )

    gates["rvol_gate"] = _ge(
        features.get("rvol_so_far"), _to_float(s.get("rvol_so_far_min")),
    )
    gates["projected_rvol_gate"] = _ge(
        features.get("projected_full_day_rvol"),
        _to_float(s.get("projected_full_day_rvol_min")),
    )
    gates["prior_atr_pct_gate"] = _ge(
        prior_atr_pct, _to_float(s.get("prior_atr_pct_min")),
    )
    gates["range_expansion_gate"] = _ge(
        features.get("range_expansion_so_far"),
        _to_float(s.get("range_expansion_so_far_min")),
    )
    gates["close_location_gate"] = _ge(
        features.get("close_location_so_far"),
        _to_float(s.get("close_location_so_far_min")),
    )
    gates["ema_distance_gate"] = _ge(
        features.get("ema_distance"), _to_float(s.get("ema_distance_min")),
    )
    gates["ema_slope_gate"] = _ge(
        ema_slope_prior, _to_float(s.get("ema_slope_min")),
    )
    gates["max_gap_gate"] = _le(
        features.get("gap_pct"), _to_float(s.get("gap_pct_max")),
    )
    gates["max_rvol_gate"] = _le(
        features.get("rvol_so_far"), _to_float(s.get("rvol_so_far_max")),
    )
    gates["max_range_expansion_gate"] = _le(
        features.get("range_expansion_so_far"),
        _to_float(s.get("range_expansion_so_far_max")),
    )

    # Per [Report §8.6]: fail-closed instrument_gate, threaded from config.
    allow_unknown = bool(s.get("allow_unknown_instrument_class_for_research", False))
    gates["instrument_gate"] = instrument_gate(
        instrument_class, allow_unknown_for_research=allow_unknown
    )

    all_passed = all(gates.values())
    return all_passed, gates


def _to_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _ge(val: float | None, threshold: float | None) -> bool:
    if threshold is None:
        return True
    if val is None:
        return False
    return float(val) >= float(threshold)


def _le(val: float | None, threshold: float | None) -> bool:
    if threshold is None:
        return True
    if val is None:
        return True
    return float(val) <= float(threshold)


def _between(val: float | None, lo: float | None, hi: float | None) -> bool:
    if val is None and (lo is not None or hi is not None):
        return False
    if val is None:
        return True
    if lo is not None and float(val) < float(lo):
        return False
    if hi is not None and float(val) > float(hi):
        return False
    return True


# ---------------------------------------------------------------- score


def compute_signal_strength(
    features: dict[str, float | None],
    score_cfg: dict,
    *,
    ema_slope_prior: float | None = None,
) -> float:
    cfg = score_cfg or {}
    bounded = bool(cfg.get("bounded", True))

    rvol = _to_float(features.get("rvol_so_far")) or 0.0
    rng = _to_float(features.get("range_expansion_so_far")) or 0.0
    cl = _to_float(features.get("close_location_so_far")) or 0.0
    ed = _to_float(features.get("ema_distance")) or 0.0
    es = _to_float(ema_slope_prior) or 0.0
    gap = _to_float(features.get("gap_pct")) or 0.0

    cl_weight = float(cfg.get("close_location_weight", 0.75))
    gap_above = float(cfg.get("gap_penalty_above", 0.25))

    if bounded:
        rvol_cap = float(cfg.get("rvol_score_cap", 5.0))
        rng_cap = float(cfg.get("range_score_cap", 2.5))
        ed_cap = float(cfg.get("ema_distance_score_cap", 0.40))
        es_cap = float(cfg.get("ema_slope_score_cap", 0.25))
        rvol_term = min(max(rvol, 0.0), rvol_cap)
        rng_term = min(max(rng, 0.0), rng_cap)
        ed_term = min(max(ed, 0.0), ed_cap)
        es_term = min(max(es, 0.0), es_cap)
        score = (
            1.00 * rvol_term
            + 1.00 * rng_term
            + cl_weight * cl
            + 10.0 * ed_term
            + 10.0 * es_term
            - 1.00 * max(gap - gap_above, 0.0)
        )
    else:
        score = (
            1.00 * rvol
            + 1.00 * rng
            + cl_weight * cl
            + 10.0 * ed
            + 10.0 * es
            - 1.00 * max(gap - gap_above, 0.0)
        )
    return float(score)
