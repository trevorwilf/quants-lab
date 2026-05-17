"""Tests for the vectorized prefilter-replay helper."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest

from bowaka_lab.config.models import PrefilterConfig, ScoreConfig, UniverseConfig
from bowaka_lab.features.daily_features import (
    compute_daily_features,
    compute_daily_features_history,
)
from bowaka_lab.features.prefilter import (
    apply_prefilter,
    replay_prefilter_over_window,
)


def _trading_dates(start: date, end: date) -> list[date]:
    out = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def _make_bars(symbol: str, sessions: list[date], *, close: float = 5.0, volume: int = 1_000_000) -> pd.DataFrame:
    rows = []
    for s in sessions:
        ts = pd.Timestamp(s).tz_localize("America/New_York") + pd.Timedelta(hours=16)
        ts = ts.tz_convert("UTC")
        rows.append(
            {
                "symbol": symbol,
                "timestamp": ts,
                "open": close,
                "high": close * 1.02,
                "low": close * 0.98,
                "close": close,
                "volume": volume,
            }
        )
    return pd.DataFrame(rows)


def test_history_emits_one_row_per_session(small_bars):
    cfg = PrefilterConfig(lookback_days=5, atr_days=5, ema_days=5, price_min=0.1, price_max=100.0)
    out = compute_daily_features_history(small_bars, cfg)
    assert out.shape[0] == small_bars.shape[0]
    # Every (symbol, session_date) is unique.
    assert not out.duplicated(subset=["symbol", "session_date"]).any()


def test_history_matches_per_date_function_on_latest(small_bars):
    cfg = PrefilterConfig(lookback_days=5, atr_days=5, ema_days=5, price_min=0.1, price_max=100.0)
    history = compute_daily_features_history(small_bars, cfg)
    latest_sd = small_bars["timestamp"].max().tz_convert("America/New_York").date()
    per_date = compute_daily_features(small_bars, cfg, signal_date=latest_sd)
    sliced = history[history["session_date"] == latest_sd].set_index("symbol")
    # For each symbol in `per_date`, the rvol/atr_pct from history equals
    # the per-date computation (no-lookahead preserved).
    for sym in per_date.index:
        for col in ("rvol", "atr_pct", "range_expansion", "ema_distance"):
            a = per_date.loc[sym, col]
            b = sliced.loc[sym, col]
            if pd.isna(a) and pd.isna(b):
                continue
            assert abs(float(a) - float(b)) < 1e-9, f"{sym}.{col} {a} != {b}"


def test_replay_over_window_matches_per_date_loop(small_bars):
    cfg = PrefilterConfig(
        lookback_days=5,
        atr_days=5,
        ema_days=5,
        price_min=0.1,
        price_max=100.0,
        rvol_min=None,
        atr_pct_min=None,
        range_expansion_min=None,
        close_location_min=None,
        ema_distance_min=None,
        ema_slope_min=None,
    )
    universe = UniverseConfig()
    sessions = sorted(small_bars["session_date"].unique().tolist())
    # Exclude the last session — no next-session callable target.
    candidate_signals = sessions[5:-1]

    def _next(s):
        return s + timedelta(days=1)

    vec_csets = replay_prefilter_over_window(
        small_bars, cfg, signal_dates=candidate_signals, next_session_fn=_next, universe=universe
    )
    for sd in candidate_signals:
        feats = compute_daily_features(small_bars, cfg, signal_date=sd)
        if feats.empty:
            assert sd not in vec_csets
            continue
        per_date = apply_prefilter(feats, cfg, signal_date=sd, trade_date=_next(sd), universe=universe)
        if per_date.candidates.empty:
            # vectorized replay may still admit nothing if no feature rows; the
            # candidate lists must agree either way.
            vec = vec_csets.get(sd)
            if vec is None:
                continue
            assert vec.candidates.empty
            continue
        vec = vec_csets[sd]
        assert sorted(vec.candidates.reset_index()["symbol"]) == sorted(per_date.candidates.reset_index()["symbol"])


def test_replay_skips_signal_dates_with_no_bars():
    cfg = PrefilterConfig(lookback_days=3, atr_days=3, ema_days=3, price_min=0.1, price_max=100.0)
    sessions = _trading_dates(date(2025, 1, 6), date(2025, 1, 17))
    bars = _make_bars("AAA", sessions)
    # Ask about a date with no bars in the dataset.
    csets = replay_prefilter_over_window(
        bars,
        cfg,
        signal_dates=[date(2025, 2, 1)],
        next_session_fn=lambda s: s + timedelta(days=1),
        universe=UniverseConfig(),
    )
    assert csets == {}


def test_replay_empty_inputs():
    cfg = PrefilterConfig(price_min=0.1, price_max=100.0)
    assert replay_prefilter_over_window(pd.DataFrame(), cfg, signal_dates=[date(2025, 1, 2)], next_session_fn=lambda s: s) == {}
    sessions = _trading_dates(date(2025, 1, 6), date(2025, 1, 17))
    bars = _make_bars("AAA", sessions)
    assert replay_prefilter_over_window(bars, cfg, signal_dates=[], next_session_fn=lambda s: s) == {}


@pytest.fixture
def small_bars() -> pd.DataFrame:
    """Two symbols × 20 trading sessions of synthetic daily bars."""
    sessions = _trading_dates(date(2025, 1, 6), date(2025, 1, 31))
    frames = [
        _make_bars("AAA", sessions, close=5.0, volume=2_000_000),
        _make_bars("BBB", sessions, close=12.0, volume=500_000),
    ]
    df = pd.concat(frames, ignore_index=True)
    df["session_date"] = df["timestamp"].dt.tz_convert("America/New_York").dt.date
    return df
