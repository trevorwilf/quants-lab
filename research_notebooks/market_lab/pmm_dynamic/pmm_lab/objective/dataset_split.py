"""Release-gated dataset splitting."""
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

from pmm_lab.objective.holdout import split_holdout

logger = logging.getLogger(__name__)


@dataclass
class DatasetSlices:
    """All dataset slices for optimization and validation."""
    full_candles: np.ndarray
    pre_release_candles: np.ndarray
    recent_release_candles: np.ndarray
    dev_candles: np.ndarray
    holdout_candles: np.ndarray
    recent_start_idx: int
    recent_start_timestamp: int
    holdout_start_idx_in_pre_release: int


def split_for_release_gate(
    candles: np.ndarray,
    recent_days: int = 28,
    holdout_fraction: float = 0.20,
    min_holdout_bars: int = 100,
    min_pre_release_bars: int = 1000,
) -> DatasetSlices:
    """Split candles with an untouched recent release window.

    1. recent_start_ts = last_ts - recent_days * 86400
    2. Reserve candles[recent_start_idx:] as untouched release window
    3. Split candles[:recent_start_idx] into dev and holdout via split_holdout()

    Raises ValueError if recent window is empty, pre-release too short,
    or holdout impossible.
    """
    if len(candles) == 0:
        raise ValueError("Empty candle array")

    last_ts = int(candles["timestamp"][-1])
    recent_start_ts = last_ts - recent_days * 86400
    recent_start_idx = int(np.searchsorted(candles["timestamp"], recent_start_ts))

    if recent_start_idx >= len(candles):
        raise ValueError(
            f"Recent window is empty: recent_start_ts={recent_start_ts} "
            f"beyond last {last_ts}"
        )

    recent_release_candles = candles[recent_start_idx:]
    pre_release_candles = candles[:recent_start_idx]

    if len(recent_release_candles) == 0:
        raise ValueError("Recent release window has 0 bars")
    if len(pre_release_candles) < min_pre_release_bars:
        raise ValueError(
            f"Pre-release data too short: {len(pre_release_candles)} "
            f"< {min_pre_release_bars}"
        )

    dev_candles, holdout_candles = split_holdout(
        pre_release_candles, holdout_fraction, min_holdout_bars
    )
    holdout_start_idx = len(dev_candles)

    logger.info(
        "Dataset split: full=%d, pre_release=%d, dev=%d, holdout=%d, recent=%d",
        len(candles), len(pre_release_candles), len(dev_candles),
        len(holdout_candles), len(recent_release_candles),
    )

    return DatasetSlices(
        full_candles=candles,
        pre_release_candles=pre_release_candles,
        recent_release_candles=recent_release_candles,
        dev_candles=dev_candles,
        holdout_candles=holdout_candles,
        recent_start_idx=recent_start_idx,
        recent_start_timestamp=int(recent_release_candles["timestamp"][0]),
        holdout_start_idx_in_pre_release=holdout_start_idx,
    )
