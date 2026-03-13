"""Deterministic dataset hashing."""

import hashlib

import numpy as np


def hash_candles(candles: np.ndarray) -> str:
    """Compute a deterministic SHA-256 hash of a canonical candle array.

    The hash covers: timestamp, open, high, low, close, volume columns.
    The is_forward_fill column is excluded (it's derived, not source data).

    Parameters
    ----------
    candles : np.ndarray
        Canonical structured candle array.

    Returns
    -------
    str
        64-character hex digest of SHA-256 hash.
    """
    # Extract the 6 source columns as a contiguous float64 array
    cols = np.column_stack([
        candles["timestamp"].astype("float64"),
        candles["open"].astype("float64"),
        candles["high"].astype("float64"),
        candles["low"].astype("float64"),
        candles["close"].astype("float64"),
        candles["volume"].astype("float64"),
    ])
    # Ensure C-contiguous for consistent byte representation
    cols = np.ascontiguousarray(cols)
    return hashlib.sha256(cols.tobytes()).hexdigest()
