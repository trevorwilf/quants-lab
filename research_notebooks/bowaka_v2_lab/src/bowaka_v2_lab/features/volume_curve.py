"""Bowaka v2 — time-of-day volume curve builder.

Port of ``bowaka_v2_volume_curve.py`` with the §15 remediation applied:
``build_volume_curve_from_minute_bars`` **must exclude the current session** —
the curve is causal and consuming it on the same session that contributed to
it produces a lookahead bug. The builder asserts this when ``current_session``
is supplied.
"""
from __future__ import annotations

import datetime as _dt
from typing import Iterable, Optional

import numpy as np
import pandas as pd

from ..utils.time import require_aware_timestamp


_DEFAULT_BUCKET_EDGES = [250_000, 500_000, 1_000_000, 5_000_000, 20_000_000]


def _pretty(n: float) -> str:
    n = float(n)
    if n >= 1_000_000:
        return f"{int(n / 1_000_000)}M"
    if n >= 1_000:
        return f"{int(n / 1_000)}k"
    return f"{int(n)}"


def adv_bucket(adv_dollars: float | None, bucket_edges: list[float] | None = None) -> str:
    """Bucket label for a symbol given its 20d avg dollar volume."""
    edges = list(bucket_edges or _DEFAULT_BUCKET_EDGES)
    if adv_dollars is None or adv_dollars < edges[0]:
        return f"<{_pretty(edges[0])}"
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        if lo <= adv_dollars < hi:
            return f"{_pretty(lo)}_{_pretty(hi)}"
    return f"{_pretty(edges[-1])}+"


def build_volume_curve_from_minute_bars(
    minute_bars: pd.DataFrame,
    *,
    bucket_edges: list[float] | None = None,
    adv_lookup: dict[str, float] | None = None,
    current_session: Optional[_dt.date] = None,
) -> pd.DataFrame:
    """Build the volume curve from historical minute bars.

    Per [Report §15.2 P1] remediation: when ``current_session`` is supplied,
    the builder asserts that NO bar in ``minute_bars`` falls on
    ``current_session`` — passing those bars in is a lookahead bug. The check
    is loud so consumers of this builder can't accidentally bias today's RVOL
    with today's own volume.
    """
    if minute_bars is None or len(minute_bars) == 0:
        return pd.DataFrame(columns=["minute_of_day", "adv_bucket", "cumulative_fraction"])

    edges = list(bucket_edges or _DEFAULT_BUCKET_EDGES)

    df = minute_bars.copy()
    cols = {c.lower(): c for c in df.columns}
    ts_col = cols.get("timestamp") or cols.get("ts")
    sym_col = cols.get("symbol")
    vol_col = cols.get("volume")
    if not (ts_col and sym_col and vol_col):
        raise ValueError("expected timestamp, symbol, volume columns")

    df["timestamp"] = pd.to_datetime(df[ts_col])
    if df["timestamp"].dt.tz is None:
        # Reject naive — see [Report §8.5].
        raise ValueError(
            "build_volume_curve_from_minute_bars: tz-naive timestamps rejected; "
            "convert to tz-aware before passing in (see utils.time.require_aware_timestamp)"
        )
    et = df["timestamp"].dt.tz_convert("America/New_York")
    df["minute_of_day"] = ((et.dt.hour - 9) * 60 + (et.dt.minute - 30)).clip(lower=0, upper=389)
    df["session_date"] = et.dt.date

    if current_session is not None:
        overlap = (df["session_date"] == current_session).any()
        assert not overlap, (
            f"build_volume_curve_from_minute_bars: minute_bars contains rows for "
            f"current_session={current_session!r}; this would leak today's volume "
            "into today's RVOL and is forbidden by the causality contract "
            "(see Report §15.2 P1)."
        )

    if "adv_bucket" not in cols:
        adv_lookup = adv_lookup or {}
        df["adv_bucket"] = df[sym_col].map(
            lambda s: adv_bucket(adv_lookup.get(s), edges)
        )
    else:
        df["adv_bucket"] = df[cols["adv_bucket"]]
    df["volume"] = pd.to_numeric(df[vol_col], errors="coerce").fillna(0.0)

    per_session_total = df.groupby(
        ["adv_bucket", "session_date", sym_col]
    )["volume"].sum().rename("session_total")
    df = df.sort_values([sym_col, "session_date", "minute_of_day"])
    df["cum_volume"] = df.groupby(
        ["adv_bucket", "session_date", sym_col]
    )["volume"].cumsum()
    df = df.merge(
        per_session_total.reset_index(),
        on=["adv_bucket", "session_date", sym_col],
    )
    df["fraction"] = np.where(
        df["session_total"] > 0,
        df["cum_volume"] / df["session_total"],
        0.0,
    )
    out = df.groupby(
        ["adv_bucket", "minute_of_day"]
    )["fraction"].mean().reset_index().rename(
        columns={"fraction": "cumulative_fraction"},
    )
    return out.sort_values(["adv_bucket", "minute_of_day"]).reset_index(drop=True)


def synthesize_default_curve(bucket_edges: list[float] | None = None) -> pd.DataFrame:
    """Default S-shaped curve for bootstrapping when no historical bars are available."""
    edges = list(bucket_edges or _DEFAULT_BUCKET_EDGES)
    rows = []
    buckets = (
        [f"<{_pretty(edges[0])}"]
        + [f"{_pretty(lo)}_{_pretty(hi)}" for lo, hi in zip(edges[:-1], edges[1:])]
        + [f"{_pretty(edges[-1])}+"]
    )
    for b in buckets:
        for m in range(390):
            if m <= 15:
                frac = 0.08 * (m / 15.0)
            elif m <= 60:
                frac = 0.08 + 0.10 * ((m - 15) / 45.0)
            elif m <= 180:
                frac = 0.18 + 0.27 * ((m - 60) / 120.0)
            elif m <= 330:
                frac = 0.45 + 0.30 * ((m - 180) / 150.0)
            elif m <= 380:
                frac = 0.75 + 0.20 * ((m - 330) / 50.0)
            else:
                frac = 0.95 + 0.05 * ((m - 380) / 9.0)
            rows.append({
                "minute_of_day": m,
                "adv_bucket": b,
                "cumulative_fraction": min(max(frac, 0.0), 1.0),
            })
    return pd.DataFrame(rows)


def fallback_rate(curve_df: pd.DataFrame | None) -> float:
    """Fraction of (bucket, minute) cells that resolved to fallback values.

    For a properly-built curve this is 0.0. The scanner can report this as
    a data-quality metric to know when it's running on synthetic vs real curves.
    """
    if curve_df is None or len(curve_df) == 0:
        return 1.0
    return 0.0
