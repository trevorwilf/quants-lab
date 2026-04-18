"""Composite dataset identity for EMA regime-hold (multi-timeframe).

EMA sweeps use two candle streams (signal + regime). A `dataset_hash` that
covers only `signal_candles` cannot distinguish runs with different regime
data. This module provides a composite identity that hashes both streams
together with their interval labels and first/last timestamps.
"""

from __future__ import annotations

import hashlib
import json

from pmm_lab.data.hashing import hash_candles


def compute_ema_dataset_identity(
    *,
    signal_candles,
    regime_candles,
    signal_interval: str,
    regime_interval: str,
) -> dict:
    """Return a dict with all fields needed to uniquely identify an EMA dataset.

    Returns
    -------
    dict
        Keys: signal_hash, regime_hash, signal_interval, regime_interval,
        signal_first_ts, signal_last_ts, regime_first_ts, regime_last_ts,
        composite_hash.
        `composite_hash` is a 64-char hex SHA-256 over the sorted-json of
        all other fields.
    """
    signal_hash = hash_candles(signal_candles)
    regime_hash = hash_candles(regime_candles)
    identity = {
        "signal_hash": signal_hash,
        "regime_hash": regime_hash,
        "signal_interval": signal_interval,
        "regime_interval": regime_interval,
        "signal_first_ts": int(signal_candles[0]["timestamp"]),
        "signal_last_ts": int(signal_candles[-1]["timestamp"]),
        "regime_first_ts": int(regime_candles[0]["timestamp"]),
        "regime_last_ts": int(regime_candles[-1]["timestamp"]),
    }
    composite = hashlib.sha256(
        json.dumps(identity, sort_keys=True).encode("utf-8")
    ).hexdigest()
    identity["composite_hash"] = composite
    return identity
