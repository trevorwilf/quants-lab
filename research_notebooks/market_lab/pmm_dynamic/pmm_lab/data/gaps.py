"""
Gap detection and forward-fill handling.

Forward-filled candles are detected using heuristics when the MongoDB schema
doesn't include a source/quality field. Three heuristics are used:

1. FLAT candle: open == high == low == close (price didn't move at all)
2. ZERO volume: volume == 0 (no trades occurred)
3. REPEATED close: close[t] == close[t-1] AND volume[t] == 0

A candle must match at least TWO of these heuristics to be flagged,
reducing false positives on legitimately quiet bars.
"""

import numpy as np


def detect_forward_fill(candles: np.ndarray) -> np.ndarray:
    """Detect likely forward-filled candles using heuristics.

    A candle is flagged as forward-filled if it matches at least 2 of:
    1. Flat OHLC: open == high == low == close
    2. Zero volume: volume == 0
    3. Repeated close with zero volume: close[t] == close[t-1] AND volume[t] == 0

    Parameters
    ----------
    candles : np.ndarray
        Canonical structured candle array.

    Returns
    -------
    np.ndarray
        Boolean array of same length, True where candle is likely forward-filled.
    """
    n = len(candles)
    if n == 0:
        return np.zeros(0, dtype=bool)

    o = candles["open"].astype("float64")
    h = candles["high"].astype("float64")
    lo = candles["low"].astype("float64")
    c = candles["close"].astype("float64")
    v = candles["volume"].astype("float64")

    # Heuristic 1: flat candle (all OHLC identical)
    flat = (o == h) & (h == lo) & (lo == c)

    # Heuristic 2: zero volume
    zero_vol = v == 0

    # Heuristic 3: repeated close with zero volume
    repeated_close = np.zeros(n, dtype=bool)
    if n > 1:
        repeated_close[1:] = (c[1:] == c[:-1]) & (v[1:] == 0)

    # Score: count how many heuristics match per bar
    score = flat.astype(int) + zero_vol.astype(int) + repeated_close.astype(int)

    # Flag if >= 2 heuristics match
    return score >= 2
