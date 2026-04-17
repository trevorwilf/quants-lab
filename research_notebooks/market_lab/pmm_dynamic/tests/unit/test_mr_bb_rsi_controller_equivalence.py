"""MR BB+RSI vs the real Hummingbot controller's update_processed_data() math.

We don't instantiate the controller (it requires a MarketDataProvider).
Instead we replicate the pandas pipeline using the live `ta_utils` module,
and assert the resulting signal equals pmm_lab's
`compute_mr_bb_rsi_features(... timestamp_mode='close')` to atol=1e-10.

Skipped if hummingbot is not importable.
"""

import numpy as np
import pandas as pd
import pytest

from tests.conftest import CANDLE_DTYPE

hb_ta = pytest.importorskip("hummingbot.strategy_v2.utils.ta_utils")

from pmm_lab.features.mean_reversion_bb_rsi_features import (
    MRBBRSIFeatureConfig,
    compute_mr_bb_rsi_features,
)


def _make_candles(n=800, seed=17):
    rng = np.random.default_rng(seed=seed)
    start_ts = 1_700_000_000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 0.7)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.3))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.3))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.1, 3.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


def test_mr_controller_equivalence():
    candles = _make_candles()
    config = MRBBRSIFeatureConfig(
        bb_length=20,
        bb_std=2.0,
        bbp_entry_threshold=0.30,
        rsi_length=14,
        rsi_entry_threshold=40.0,
        use_trend_filter=True,
        trend_ema_length=50,
        min_trend_slope=0.0,
        atr_length=14,
        max_atr_pct_for_entry=0.20,
        volume_filter_window=48,
        min_volume_quantile=0.30,
        timestamp_mode="close",  # match controller's close-time interpretation
        controller_compat=False,
    )

    lab = compute_mr_bb_rsi_features(candles, config)

    # Replicate the controller's pandas pipeline using hummingbot's ta_utils
    close = pd.Series(candles["close"].astype("float64"))
    high = pd.Series(candles["high"].astype("float64"))
    low = pd.Series(candles["low"].astype("float64"))
    vol = pd.Series(candles["volume"].astype("float64"))

    bbp, _, _, _ = hb_ta.bollinger_percent_b(close, config.bb_length, config.bb_std)
    rsi = hb_ta.rsi_wilder(close, config.rsi_length)
    atr = hb_ta.atr_wilder(high, low, close, config.atr_length)
    atr_pct = atr / close.replace(0.0, np.nan)
    ema_trend = hb_ta.ema(close, config.trend_ema_length)
    ema_slope = ema_trend.diff()
    vol_ok = hb_ta.rolling_volume_quantile_ok(
        vol, config.volume_filter_window, config.min_volume_quantile
    )

    entry = (
        (bbp <= config.bbp_entry_threshold)
        & (rsi <= config.rsi_entry_threshold)
        & (atr_pct <= config.max_atr_pct_for_entry)
        & vol_ok.astype(bool)
    )
    if config.use_trend_filter:
        entry = entry & (ema_slope >= config.min_trend_slope)

    expected_signal = entry.astype("float64").to_numpy()
    # Warmup-pad the expected signal: anywhere NaN in indicators, signal is 0
    # (matches the lab's zero-out-warmup behavior before the shift).

    lab_signal = lab.data["signal"]

    # Same length
    assert len(lab_signal) == len(expected_signal)

    # Compare on bars past warmup
    diff_count = 0
    for i in range(lab.warmup_end, len(candles)):
        a = lab_signal[i]
        b = expected_signal[i]
        if np.isnan(a) and np.isnan(b):
            continue
        if a != b:
            diff_count += 1
    assert diff_count == 0, f"{diff_count} signal bars differ between lab and controller-math replica"
