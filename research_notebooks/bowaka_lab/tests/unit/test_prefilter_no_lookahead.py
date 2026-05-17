"""Phase 3: no-lookahead invariant test.

For ``signal_date D``, the candidate rank must be invariant to the existence
of any bar with ``session_date > D``. This guards against accidentally letting
the trade-day bar leak into feature computation.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bowaka_lab.config.models import PrefilterConfig, ScoreConfig, UniverseConfig
from bowaka_lab.features.daily_features import compute_daily_features
from bowaka_lab.features.prefilter import apply_prefilter


def _make_synthetic_bars(*, signal_date: date, post_signal_volume_x: float, seed: int = 7) -> pd.DataFrame:
    """Synthetic bars with two symbols and an artificial post-signal volume spike on AAA.

    Timestamps are anchored at 21:00 UTC (16:00 ET market close) so that
    each bar's session_date in ET equals the calendar date we built it for.
    Otherwise UTC-midnight timestamps map to the *previous* ET session date
    and a "post-signal" bar can accidentally be classified as on-or-before
    signal_date, masking real look-ahead leaks.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for sym, base in (("AAA", 5.0), ("BBB", 10.0)):
        price = base
        for i in range(40):
            d = date(2026, 4, 1) + pd.Timedelta(days=i).to_pytimedelta()
            if d.weekday() >= 5:
                continue
            move = float(rng.normal(0, 0.01))
            price = max(0.5, price * (1.0 + move))
            high = price * 1.02
            low = price * 0.98
            vol = int(rng.integers(200_000, 400_000))
            if sym == "AAA" and d > signal_date:
                vol = int(vol * post_signal_volume_x)
            ts = pd.Timestamp(d).tz_localize("America/New_York") + pd.Timedelta(hours=16)
            ts = ts.tz_convert("UTC")
            rows.append({"symbol": sym, "timestamp": ts, "open": price, "high": high, "low": low, "close": price, "volume": vol})
    df = pd.DataFrame(rows)
    df["session_date"] = df["timestamp"].dt.tz_convert("America/New_York").dt.date
    return df


def test_candidate_rank_invariant_to_post_signal_bar():
    signal_date = date(2026, 4, 22)
    cfg = PrefilterConfig(
        lookback_days=10,
        atr_days=7,
        ema_days=5,
        price_min=1.0,
        price_max=30.0,
        avg_dollar_volume_min=None,
        rvol_min=None,
        atr_pct_min=None,
        range_expansion_min=None,
        close_location_min=None,
        ema_distance_min=None,
        ema_slope_min=None,
        score=ScoreConfig(bounded=False),
    )
    universe = UniverseConfig()

    bars_a = _make_synthetic_bars(signal_date=signal_date, post_signal_volume_x=1.0)
    bars_b = _make_synthetic_bars(signal_date=signal_date, post_signal_volume_x=100.0)

    feats_a = compute_daily_features(bars_a, cfg, signal_date=signal_date)
    feats_b = compute_daily_features(bars_b, cfg, signal_date=signal_date)

    for col in ("rvol", "ema_distance", "ema_slope", "range_expansion"):
        np.testing.assert_allclose(
            feats_a[col].astype(float).values,
            feats_b[col].astype(float).values,
            equal_nan=True,
            err_msg=f"Lookahead detected in feature {col!r}",
        )

    cset_a = apply_prefilter(feats_a, cfg, signal_date=signal_date, trade_date=date(2026, 4, 23), universe=universe)
    cset_b = apply_prefilter(feats_b, cfg, signal_date=signal_date, trade_date=date(2026, 4, 23), universe=universe)
    rank_a = cset_a.all_decisions["rank"].to_dict()
    rank_b = cset_b.all_decisions["rank"].to_dict()
    assert rank_a == rank_b


def test_features_filter_to_signal_date():
    signal_date = date(2026, 4, 22)
    cfg = PrefilterConfig(price_min=1.0, price_max=30.0)
    bars = _make_synthetic_bars(signal_date=signal_date, post_signal_volume_x=10.0)
    feats = compute_daily_features(bars, cfg, signal_date=signal_date)
    assert (feats["latest_bar_date"] <= signal_date).all()
