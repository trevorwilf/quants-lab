"""EMA regime-hold: dedicated timestamp leakage test.

This is the highest-risk defect for the multi-timeframe strategy per the
prompt's Phase 2 guidance (D20). If it fails, there is a lookahead bug.

Contract: if we mutate a single 4h regime bar at index k_slow with timestamp
T_k, then for every 5m signal bar with timestamp < T_k, the output `signal[i]`
must be identical between the pre-mutation and post-mutation runs. Any
difference at `timestamp < T_k` is a leak.

We run this for both controller_compat=True (replay) AND
controller_compat=False (vectorized). Either failing blocks merge.
"""

import numpy as np
import pytest

from pmm_lab.features.ema_regime_hold_features import (
    EMARegimeHoldFeatureConfig,
    compute_ema_regime_hold_features,
)
from tests.conftest import CANDLE_DTYPE


def _make_fast(n: int = 2000, start_ts: int = 1_700_000_000, seed: int = 23) -> np.ndarray:
    rng = np.random.default_rng(seed=seed)
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 0.4)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.2))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.2))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.2, 2.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


def _make_slow(n: int = 180, start_ts: int = 1_700_000_000, seed: int = 29) -> np.ndarray:
    rng = np.random.default_rng(seed=seed)
    interval = 14400
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 1.5)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.8))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.8))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.5, 10.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.mark.parametrize("controller_compat", [False])
def test_ema_timestamp_leakage_fast_path(controller_compat):
    """Vectorized path: mutating a slow bar must not affect signals at timestamps
    earlier than that slow bar.
    """
    fast = _make_fast()
    slow = _make_slow()

    config = EMARegimeHoldFeatureConfig(
        regime_ema_fast=10,
        regime_ema_slow=30,
        regime_adx_length=14,
        regime_adx_threshold=0.0,
        volume_filter_window=48,
        min_volume_quantile=0.0,
        hold_mode="reentry",
        controller_compat=controller_compat,
    )

    baseline = compute_ema_regime_hold_features(fast, slow, config)

    # Pick a slow bar well past warmup
    k_slow = len(slow) // 2
    T_k = int(slow["timestamp"][k_slow])

    mutated_slow = slow.copy()
    mutated_slow["close"][k_slow] = mutated_slow["close"][k_slow] * 1.3
    mutated_slow["high"][k_slow] = mutated_slow["high"][k_slow] * 1.3
    mutated_slow["low"][k_slow] = mutated_slow["low"][k_slow] * 1.3

    perturbed = compute_ema_regime_hold_features(fast, mutated_slow, config)

    sig_a = baseline.data["signal"]
    sig_b = perturbed.data["signal"]
    fast_ts = fast["timestamp"]

    # For fast bars with timestamp < T_k, signals must be identical.
    pre_mask = fast_ts < T_k
    diffs = np.where(pre_mask, sig_a - sig_b, 0.0)
    assert np.all(np.abs(diffs) < 1e-12), (
        f"Timestamp leak detected in controller_compat={controller_compat}: "
        f"{int(np.sum(np.abs(diffs) >= 1e-12))} fast bars with ts<T_k differ"
    )


@pytest.mark.slow
def test_ema_timestamp_leakage_replay_path():
    """Replay (controller_compat=True) path: same invariant.

    Marked slow because the replay path is O(n * slow_max_records); on 2000
    fast bars with ~180 slow bars this takes a while.
    """
    fast = _make_fast(n=400)  # smaller for speed — replay is O(n^2)-ish
    slow = _make_slow(n=50)

    config = EMARegimeHoldFeatureConfig(
        regime_ema_fast=10,
        regime_ema_slow=20,
        regime_adx_length=14,
        regime_adx_threshold=0.0,
        volume_filter_window=24,
        min_volume_quantile=0.0,
        hold_mode="reentry",
        controller_compat=True,
    )

    baseline = compute_ema_regime_hold_features(fast, slow, config)

    k_slow = len(slow) // 2
    T_k = int(slow["timestamp"][k_slow])

    mutated_slow = slow.copy()
    mutated_slow["close"][k_slow] = mutated_slow["close"][k_slow] * 1.3
    mutated_slow["high"][k_slow] = mutated_slow["high"][k_slow] * 1.3
    mutated_slow["low"][k_slow] = mutated_slow["low"][k_slow] * 1.3

    perturbed = compute_ema_regime_hold_features(fast, mutated_slow, config)

    sig_a = baseline.data["signal"]
    sig_b = perturbed.data["signal"]
    fast_ts = fast["timestamp"]

    pre_mask = fast_ts < T_k
    diffs = np.where(pre_mask, sig_a - sig_b, 0.0)
    assert np.all(np.abs(diffs) < 1e-12), (
        "Timestamp leak detected in replay path"
    )
