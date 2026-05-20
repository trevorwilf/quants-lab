"""Causality checks per [Report §8.4]."""
from __future__ import annotations

import datetime as _dt

import pandas as pd
import pytest

from bowaka_v2_lab.features import (
    aggregate_forming_session_bar,
    build_volume_curve_from_minute_bars,
    compute_prior_daily_baselines,
)
from tests.fixtures.build_daily_fixture import make_daily_bars
from tests.fixtures.build_minute_fixture import make_minute_bars


def test_daily_baseline_excludes_current_session() -> None:
    # Build 25 sessions with a sharp range expansion on the LAST session.
    df = make_daily_bars("AAA", _dt.date(2024, 9, 2), n_sessions=25)
    last = df.index[-1]
    # Mutate the last row so its high/low/close are wildly different — ATR uses
    # True Range = max(high-low, high-prev_close, low-prev_close), so we need to
    # blow out the high or low to change the ATR meaningfully.
    df.loc[last, "high"] = df.loc[last, "open"] * 2.0
    df.loc[last, "low"] = df.loc[last, "open"] * 0.5
    df.loc[last, "close"] = df.loc[last, "open"] * 1.8
    # Slice to "prior completed" — exclude last row.
    prior_only = df.iloc[:-1]
    baselines_prior = compute_prior_daily_baselines(prior_only)
    baselines_with_today = compute_prior_daily_baselines(df)
    # The today-included variant must produce a measurably different ATR.
    assert baselines_prior["prior_atr_14d"] != baselines_with_today["prior_atr_14d"]
    # The prior_close must be the second-to-last row's close in the "today-excluded" frame.
    assert baselines_prior["prior_close"] == df.iloc[-2]["close"]


def test_forming_bar_ignores_future_bars_by_caller_contract() -> None:
    df = make_minute_bars("AAA", _dt.date(2024, 9, 4), minutes=30)
    # Aggregate over only the first 10 minutes; the last 20 minutes must not contribute.
    first10 = df.iloc[:10]
    agg_first10 = aggregate_forming_session_bar(first10)
    agg_all = aggregate_forming_session_bar(df)
    # session_high must differ when we include more bars (drift_per_minute=0 still gives same high).
    # Use volume which sums monotonically.
    assert agg_first10["session_volume"] < agg_all["session_volume"]


def test_volume_curve_built_from_prior_sessions_only() -> None:
    # 3 historical sessions for one symbol.
    d1 = make_minute_bars("AAA", _dt.date(2024, 9, 3), minutes=30, minute_volume=100)
    d2 = make_minute_bars("AAA", _dt.date(2024, 9, 4), minutes=30, minute_volume=200)
    d3 = make_minute_bars("AAA", _dt.date(2024, 9, 5), minutes=30, minute_volume=300)
    bars = pd.concat([d1, d2, d3], ignore_index=True)
    # Building with current_session=Sep 5 (which is present) must assert.
    with pytest.raises(AssertionError, match="current_session"):
        build_volume_curve_from_minute_bars(
            bars,
            adv_lookup={"AAA": 1_500_000},
            current_session=_dt.date(2024, 9, 5),
        )
    # Building over d1+d2 with current_session=d3 (not present) must succeed.
    bars_prior = pd.concat([d1, d2], ignore_index=True)
    curve = build_volume_curve_from_minute_bars(
        bars_prior,
        adv_lookup={"AAA": 1_500_000},
        current_session=_dt.date(2024, 9, 5),
    )
    assert not curve.empty
    assert "minute_of_day" in curve.columns
    assert "adv_bucket" in curve.columns
    assert "cumulative_fraction" in curve.columns
