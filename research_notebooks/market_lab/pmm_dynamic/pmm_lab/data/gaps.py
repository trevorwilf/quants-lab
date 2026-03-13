"""Gap detection and forward-fill handling.

v1: Forward-fill detection is deferred. This module provides placeholder
functions that will be expanded in a future version when the MongoDB
candle schema includes a 'source' field.
"""

import numpy as np


def detect_forward_fill(candles: np.ndarray) -> np.ndarray:
    """Detect forward-filled candles.

    v1 implementation: returns an array of all False values.
    Future versions will use heuristics (volume==0 AND open==high==low==close)
    or the 'source' field from MongoDB if available.

    Parameters
    ----------
    candles : np.ndarray
        Canonical structured candle array.

    Returns
    -------
    np.ndarray
        Boolean array of same length, True where candle is forward-filled.
    """
    return np.zeros(len(candles), dtype=bool)
