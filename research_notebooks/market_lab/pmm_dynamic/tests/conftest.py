"""Shared test fixtures for PMM Lab tests."""

import pytest
import numpy as np

CANDLE_DTYPE = np.dtype([
    ("timestamp", "int64"),
    ("open", "float64"),
    ("high", "float64"),
    ("low", "float64"),
    ("close", "float64"),
    ("volume", "float64"),
    ("is_forward_fill", "bool"),
])


def _make_sample_candles_5m():
    """Standalone factory (not a fixture) for use in Makefile smoke tests."""
    rng = np.random.default_rng(seed=42)
    n = 100
    start_ts = 1756833000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100000.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 50)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 20))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 20))
        open_p = max(open_p, 1.0)
        close_p = max(close_p, 1.0)
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = rng.uniform(0.05, 2.0)
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = close_p
    return np.array(rows, dtype=CANDLE_DTYPE)


def _make_sample_candles_500():
    """Standalone factory for 500-bar candles."""
    rng = np.random.default_rng(seed=99)
    n = 500
    start_ts = 1756833000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100000.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 80)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 30))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 30))
        open_p = max(open_p, 1.0)
        close_p = max(close_p, 1.0)
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = rng.uniform(0.1, 3.0)
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = close_p
    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def sample_candles_5m():
    """Generate a clean 100-bar 5m candle array with realistic BTC-USDT data.

    - Timestamps start at 1756833000 (2025-09-02 17:10:00 UTC), 300s apart.
    - Prices in the 90000-110000 range with small random walks.
    - OHLC sanity enforced: high >= max(open,close), low <= min(open,close), all > 0.
    - Volume between 0.05 and 2.0, no zeros.
    - is_forward_fill all False.
    - Reproducible with seed=42.
    """
    rng = np.random.default_rng(seed=42)
    n = 100
    start_ts = 1756833000
    interval = 300

    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")

    # Random walk for prices
    price = 100000.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 50)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 20))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 20))
        # Ensure all positive
        open_p = max(open_p, 1.0)
        close_p = max(close_p, 1.0)
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = rng.uniform(0.05, 2.0)
        rows.append((
            int(timestamps[i]),
            open_p, high_p, low_p, close_p, vol, False,
        ))
        price = close_p

    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def sample_candles_with_violations():
    """Generate a 20-bar candle array with known violations.

    - Row 5: high < close (OHLC violation)
    - Row 10: low > open (OHLC violation)
    - Row 15: close = 0 (non-positive price)
    - Row 18: volume = 0
    All other rows are clean.
    """
    rng = np.random.default_rng(seed=123)
    n = 20
    start_ts = 1756833000
    interval = 300

    rows = []
    for i in range(n):
        ts = start_ts + i * interval
        open_p = 100000.0 + rng.normal(0, 50)
        close_p = 100000.0 + rng.normal(0, 50)
        high_p = max(open_p, close_p) + abs(rng.normal(0, 20))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 20))
        low_p = max(low_p, 0.01)
        vol = rng.uniform(0.1, 1.0)
        rows.append([ts, open_p, high_p, low_p, close_p, vol, False])

    # Row 5: high < close (make high less than close)
    rows[5][2] = rows[5][4] - 10.0  # high = close - 10

    # Row 10: low > open (make low greater than open)
    rows[10][3] = rows[10][1] + 10.0  # low = open + 10

    # Row 15: close = 0 (non-positive)
    rows[15][4] = 0.0

    # Row 18: volume = 0
    rows[18][5] = 0.0

    return np.array([tuple(r) for r in rows], dtype=CANDLE_DTYPE)


@pytest.fixture
def sample_candles_with_duplicates():
    """Generate a 50-bar candle array where rows 20 and 21 have the same timestamp."""
    rng = np.random.default_rng(seed=99)
    n = 50
    start_ts = 1756833000
    interval = 300

    rows = []
    for i in range(n):
        ts = start_ts + i * interval
        open_p = 100000.0 + rng.normal(0, 50)
        close_p = 100000.0 + rng.normal(0, 50)
        high_p = max(open_p, close_p) + abs(rng.normal(0, 20))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 20))
        low_p = max(low_p, 0.01)
        vol = rng.uniform(0.1, 1.0)
        rows.append((ts, open_p, high_p, low_p, close_p, vol, False))

    arr = np.array(rows, dtype=CANDLE_DTYPE)
    # Make row 21 have the same timestamp as row 20
    arr[21]["timestamp"] = arr[20]["timestamp"]
    return arr


@pytest.fixture
def sample_candles_with_gaps():
    """Generate a 50-bar candle array at 5m intervals with a 30-min gap.

    Between rows 24 and 25, there is a 30-minute gap (6 missing bars).
    """
    rng = np.random.default_rng(seed=77)
    n = 50
    start_ts = 1756833000
    interval = 300
    gap_at = 25  # gap starts after row 24
    gap_bars = 6  # 6 missing bars = 30 minutes

    rows = []
    ts = start_ts
    for i in range(n):
        if i == gap_at:
            ts += gap_bars * interval  # skip 6 bars
        open_p = 100000.0 + rng.normal(0, 50)
        close_p = 100000.0 + rng.normal(0, 50)
        high_p = max(open_p, close_p) + abs(rng.normal(0, 20))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 20))
        low_p = max(low_p, 0.01)
        vol = rng.uniform(0.1, 1.0)
        rows.append((ts, open_p, high_p, low_p, close_p, vol, False))
        ts += interval

    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def sample_candles_500():
    """Generate a 500-bar 5m candle array for walk-forward / Optuna testing.

    Same generation logic as sample_candles_5m but with 500 bars.
    Uses seed=99 for a different but reproducible sequence.
    Timestamps start at 1756833000 with 300s spacing.
    """
    rng = np.random.default_rng(seed=99)
    n = 500
    start_ts = 1756833000
    interval = 300

    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")

    price = 100000.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 80)  # slightly more volatile for trade generation
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 30))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 30))
        open_p = max(open_p, 1.0)
        close_p = max(close_p, 1.0)
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = rng.uniform(0.1, 3.0)
        rows.append((
            int(timestamps[i]),
            open_p, high_p, low_p, close_p, vol, False,
        ))
        price = close_p

    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def mongo_docs_5m(sample_candles_5m):
    """Return list of 100 dicts matching MongoDB candle schema.

    Uses the same data as sample_candles_5m.
    Connector: 'nonkyc', pair: 'BTC-USDT', interval: '5m'.
    """
    docs = []
    for row in sample_candles_5m:
        docs.append({
            "connector": "nonkyc",
            "trading_pair": "BTC-USDT",
            "interval": "5m",
            "timestamp": int(row["timestamp"]),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row["volume"]),
        })
    return docs
