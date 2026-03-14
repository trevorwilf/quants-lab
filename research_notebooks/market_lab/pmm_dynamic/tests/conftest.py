"""Shared test fixtures for PMM Lab tests."""

import os
from pathlib import Path

import pytest
import numpy as np

from pmm_lab.config.params import PairRules, FeeConfig


def _load_dotenv() -> dict:
    """Load key=value pairs from .env file, searching upward from project root."""
    env_vars = {}
    # Walk up from pmm_dynamic/ to find .env
    search_dir = Path(__file__).resolve().parent.parent
    for _ in range(10):
        env_file = search_dir / ".env"
        if env_file.exists():
            break
        parent = search_dir.parent
        if parent == search_dir:
            return env_vars  # hit filesystem root
        search_dir = parent
    else:
        return env_vars

    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env_vars[key.strip()] = value.strip()
    return env_vars


def _build_mongo_uri() -> str:
    # 1. Already set in environment
    uri = os.environ.get("MONGO_URI")
    if uri:
        return uri

    # 2. Check .env file
    dotenv = _load_dotenv()

    # 2a. MONGO_URI in .env (highest priority from file)
    uri = dotenv.get("MONGO_URI", "").strip()
    if uri:
        os.environ["MONGO_URI"] = uri
        return uri

    # 2b. Build from components
    host = dotenv.get("TRUENAS_LAN_IP", "").strip()
    password = dotenv.get("MONGO_ROOT_PASSWORD", "").strip()
    if host and password:
        uri = f"mongodb://root:{password}@{host}:27017/candles?authSource=admin"
        os.environ["MONGO_URI"] = uri
        return uri

    # 3. Fallback
    return "mongodb://localhost:27017"


def _mongo_is_reachable() -> bool:
    """Check if MongoDB is reachable. Used for auto-skip."""
    try:
        from pymongo import MongoClient
        uri = _build_mongo_uri()
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        client.close()
        return True
    except Exception:
        return False


MONGO_AVAILABLE = _mongo_is_reachable()

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
def default_pair_rules():
    """Default exchange rules for testing."""
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


@pytest.fixture
def sample_candles_with_forward_fills():
    """Generate a 50-bar candle array with known forward-filled bars.

    - Bars 10, 11: flat OHLC + zero volume (clear forward fills)
    - Bar 20: zero volume but different OHLC (not flagged — only 1 heuristic)
    - Bars 30, 31: repeated close from bar 29 + zero volume (flagged)
    - All other bars are clean with normal OHLCV.
    """
    rng = np.random.default_rng(seed=555)
    n = 50
    start_ts = 1756833000
    interval = 300

    rows = []
    price = 100000.0
    for i in range(n):
        ts = start_ts + i * interval
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
        vol = rng.uniform(0.1, 2.0)
        rows.append([ts, open_p, high_p, low_p, close_p, vol, False])
        price = close_p

    # Bars 10, 11: flat OHLC + zero volume (clear forward fills)
    for bar in [10, 11]:
        flat_price = rows[bar][4]  # use the close
        rows[bar] = [rows[bar][0], flat_price, flat_price, flat_price, flat_price, 0.0, False]

    # Bar 20: zero volume but different OHLC (should NOT be flagged — only 1 heuristic)
    rows[20][5] = 0.0  # zero volume, but OHLC varies

    # Bars 30, 31: repeated close from bar 29 + zero volume
    prev_close = rows[29][4]
    for bar in [30, 31]:
        rows[bar][4] = prev_close  # same close as bar 29
        rows[bar][5] = 0.0         # zero volume
        # Keep different open/high/low so flat heuristic doesn't fire (testing repeated close path)
        rows[bar][1] = prev_close + 1.0   # open slightly different
        rows[bar][2] = prev_close + 2.0   # high
        rows[bar][3] = prev_close - 1.0   # low

    return np.array([tuple(r) for r in rows], dtype=CANDLE_DTYPE)


@pytest.fixture
def sample_candles_empty():
    """Return an empty candle array."""
    return np.array([], dtype=CANDLE_DTYPE)


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
