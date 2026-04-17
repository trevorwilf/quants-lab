"""EMA regime-hold vs the real Hummingbot controller's pandas pipeline.

Skipped if hummingbot is not importable.
"""

import numpy as np
import pandas as pd
import pytest

from tests.conftest import CANDLE_DTYPE

hb_ta = pytest.importorskip("hummingbot.strategy_v2.utils.ta_utils")

from pmm_lab.features.ema_regime_hold_features import (
    EMARegimeHoldFeatureConfig,
    compute_ema_regime_hold_features,
)


def _make_fast(n=800, seed=31):
    rng = np.random.default_rng(seed=seed)
    start_ts = 1_700_000_000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 0.4)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.15))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.15))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.2, 2.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


def _make_slow(n=100, seed=37):
    rng = np.random.default_rng(seed=seed)
    start_ts = 1_700_000_000
    interval = 14400
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 1.2)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.6))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.6))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.5, 8.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


def test_ema_controller_equivalence_close_mode():
    fast = _make_fast()
    slow = _make_slow()

    config = EMARegimeHoldFeatureConfig(
        regime_ema_fast=10,
        regime_ema_slow=30,
        regime_adx_length=14,
        regime_adx_threshold=15.0,
        volume_filter_window=48,
        min_volume_quantile=0.30,
        hold_mode="reentry",
        timestamp_mode="close",
        controller_compat=False,
    )

    lab = compute_ema_regime_hold_features(fast, slow, config)

    # Replicate the controller's multi-timeframe pipeline using HB ta_utils
    close_s = pd.Series(slow["close"].astype("float64"))
    high_s = pd.Series(slow["high"].astype("float64"))
    low_s = pd.Series(slow["low"].astype("float64"))
    ts_s = pd.Series(slow["timestamp"].astype("int64"))

    df_slow = pd.DataFrame({"timestamp": ts_s, "close": close_s, "high": high_s, "low": low_s})
    df_slow["ema_fast"] = hb_ta.ema(close_s, config.regime_ema_fast)
    df_slow["ema_slow"] = hb_ta.ema(close_s, config.regime_ema_slow)
    df_slow["adx"] = hb_ta.adx_wilder(high_s, low_s, close_s, config.regime_adx_length)
    df_slow.dropna(inplace=True)
    df_slow["trend_on"] = (
        (df_slow["ema_fast"] >= df_slow["ema_slow"])
        & (df_slow["adx"] >= config.regime_adx_threshold)
    )
    slow_ind = df_slow[["timestamp", "trend_on"]].copy()

    fast_ts = pd.Series(fast["timestamp"].astype("int64"))
    fast_df = pd.DataFrame({"timestamp": fast_ts, "volume": fast["volume"]}).sort_values("timestamp")
    merged = pd.merge_asof(
        fast_df,
        slow_ind.sort_values("timestamp").reset_index(drop=True),
        on="timestamp",
        direction="backward",
    )
    trend = merged["trend_on"].fillna(False).astype(bool).to_numpy()
    vol_ok = hb_ta.rolling_volume_quantile_ok(
        pd.Series(fast["volume"].astype("float64")),
        config.volume_filter_window,
        config.min_volume_quantile,
    ).astype(bool).to_numpy()
    expected_signal = (trend & vol_ok).astype("float64")

    lab_signal = lab.data["signal"]
    assert len(lab_signal) == len(expected_signal)

    diff_count = 0
    for i in range(lab.warmup_end, len(fast)):
        if lab_signal[i] != expected_signal[i]:
            diff_count += 1
    assert diff_count == 0, f"{diff_count} bars differ between lab and controller replica"
