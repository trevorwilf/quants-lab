"""Integration tests requiring a real MongoDB connection.

These tests auto-skip if MongoDB is not reachable.
Set MONGO_URI environment variable to connect:
    MONGO_URI=mongodb://root:<password>@<host>:27017/candles?authSource=admin
"""

import numpy as np
import pytest

from tests.conftest import MONGO_AVAILABLE
from pmm_lab.config.params import DataQuery
from pmm_lab.data.mongo import MongoCandleLoader
from pmm_lab.data.candles import validate_candles


@pytest.fixture
def loader():
    return MongoCandleLoader()


@pytest.mark.live_mongo
@pytest.mark.skipif(not MONGO_AVAILABLE, reason="MongoDB not reachable")
def test_live_ping(loader):
    """MongoDB is reachable."""
    assert loader.ping() is True


@pytest.mark.live_mongo
@pytest.mark.skipif(not MONGO_AVAILABLE, reason="MongoDB not reachable")
def test_live_list_combos_not_empty(loader):
    """At least one USDT combo exists."""
    combos = loader.list_combos(quote_asset="USDT")
    assert len(combos) > 0


@pytest.mark.live_mongo
@pytest.mark.skipif(not MONGO_AVAILABLE, reason="MongoDB not reachable")
def test_live_load_range_btc_usdt_5m(loader):
    """Load BTC-USDT 5m candles from nonkyc."""
    query = DataQuery(connector="nonkyc", trading_pair="BTC-USDT", interval="5m")
    arr = loader.load_range(query)
    assert len(arr) >= 100
    assert arr.dtype.names == (
        "timestamp", "open", "high", "low", "close", "volume", "is_forward_fill"
    )
    assert np.all(np.diff(arr["timestamp"]) > 0)


@pytest.mark.live_mongo
@pytest.mark.skipif(not MONGO_AVAILABLE, reason="MongoDB not reachable")
def test_live_audit_passes_strict(loader):
    """Real data passes strict validation."""
    query = DataQuery(connector="nonkyc", trading_pair="BTC-USDT", interval="5m")
    arr = loader.load_range(query)
    if len(arr) > 500:
        arr = arr[:500]
    audit = validate_candles(arr, "5m", strict=True)
    assert audit.passed_strict is True
