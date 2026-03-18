"""Tests for MongoCandleLoader using mongomock."""

import numpy as np
import pytest
import mongomock

from pmm_lab.config.params import DataQuery
from pmm_lab.data.mongo import MongoCandleLoader, CANDLE_DTYPE


@pytest.fixture
def mock_loader():
    """Create a MongoCandleLoader with a mongomock client."""
    client = mongomock.MongoClient()
    return MongoCandleLoader(client=client, db_name="test_db")


@pytest.fixture
def populated_loader(mock_loader, mongo_docs_5m):
    """Loader with 100 BTC-USDT 5m candles inserted."""
    mock_loader._collection.insert_many(mongo_docs_5m)
    return mock_loader


def _make_doc(connector, pair, interval, ts, price=100.0, vol=1.0):
    return {
        "connector": connector,
        "trading_pair": pair,
        "interval": interval,
        "timestamp": ts,
        "open": price,
        "high": price + 1,
        "low": price - 1,
        "close": price + 0.5,
        "volume": vol,
    }


def test_list_combos_returns_correct_structure(mock_loader):
    """Insert docs for 2 connectors x 2 pairs x 2 intervals. Check structure."""
    docs = []
    for conn in ("mexc", "nonkyc"):
        for pair in ("BTC-USDT", "ETH-USDT"):
            for interval in ("5m", "1h"):
                for i in range(3):
                    docs.append(_make_doc(conn, pair, interval, 1000 + i * 300))
    mock_loader._collection.insert_many(docs)

    combos = mock_loader.list_combos(quote_asset=None)
    assert len(combos) == 8  # 2 * 2 * 2
    for c in combos:
        assert set(c.keys()) == {"connector", "trading_pair", "interval", "count", "first_ts", "last_ts"}


def test_list_combos_filters_by_quote_asset(mock_loader):
    """Only USDT pairs returned when filtering by quote_asset."""
    docs = [
        _make_doc("nonkyc", "BTC-USDT", "5m", 1000),
        _make_doc("nonkyc", "ARRR-XMR", "5m", 1000),
    ]
    mock_loader._collection.insert_many(docs)

    combos = mock_loader.list_combos(quote_asset="USDT")
    assert len(combos) == 1
    assert combos[0]["trading_pair"] == "BTC-USDT"


def test_list_combos_filters_by_connector(mock_loader):
    """Only nonkyc entries when filtering by connector."""
    docs = [
        _make_doc("mexc", "BTC-USDT", "5m", 1000),
        _make_doc("nonkyc", "BTC-USDT", "5m", 1000),
    ]
    mock_loader._collection.insert_many(docs)

    combos = mock_loader.list_combos(connector="nonkyc", quote_asset=None)
    assert len(combos) == 1
    assert combos[0]["connector"] == "nonkyc"


def test_load_range_returns_canonical_dtype(populated_loader):
    """Returned array has canonical dtype with all 7 fields."""
    query = DataQuery(connector="nonkyc", trading_pair="BTC-USDT", interval="5m")
    arr = populated_loader.load_range(query)
    assert arr.dtype == CANDLE_DTYPE
    assert len(arr.dtype.names) == 7


def test_load_range_sorted_ascending(mock_loader):
    """Timestamps are strictly increasing even if inserted in random order."""
    import random
    rng = random.Random(42)
    timestamps = list(range(1000, 1000 + 50 * 300, 300))
    rng.shuffle(timestamps)
    docs = [_make_doc("nonkyc", "BTC-USDT", "5m", ts) for ts in timestamps]
    mock_loader._collection.insert_many(docs)

    query = DataQuery(connector="nonkyc", trading_pair="BTC-USDT", interval="5m")
    arr = mock_loader.load_range(query)
    assert np.all(np.diff(arr["timestamp"]) > 0)


def test_load_range_respects_time_bounds(populated_loader):
    """Query with start_ts/end_ts selects correct subset."""
    # populated_loader has 100 docs starting at 1756833000 with 300s spacing
    start_ts = 1756833000 + 10 * 300  # skip first 10
    end_ts = 1756833000 + 19 * 300    # 10 candles (indices 10-19)

    query = DataQuery(
        connector="nonkyc",
        trading_pair="BTC-USDT",
        interval="5m",
        start_ts=start_ts,
        end_ts=end_ts,
    )
    arr = populated_loader.load_range(query)
    assert len(arr) == 10
    assert arr["timestamp"][0] == start_ts
    assert arr["timestamp"][-1] == end_ts


def test_load_range_deduplicates(mock_loader):
    """Duplicate timestamps are removed (keep first)."""
    docs = [
        _make_doc("nonkyc", "BTC-USDT", "5m", 1000, price=100),
        _make_doc("nonkyc", "BTC-USDT", "5m", 1300, price=101),
        _make_doc("nonkyc", "BTC-USDT", "5m", 1300, price=102),  # duplicate
        _make_doc("nonkyc", "BTC-USDT", "5m", 1600, price=103),
    ]
    mock_loader._collection.insert_many(docs)

    query = DataQuery(connector="nonkyc", trading_pair="BTC-USDT", interval="5m")
    arr = mock_loader.load_range(query)
    assert len(arr) == 3  # 4 docs - 1 duplicate = 3 unique


def test_load_range_empty_raises(mock_loader):
    """ValueError when no documents match."""
    query = DataQuery(connector="nonkyc", trading_pair="MISSING-USDT", interval="5m")
    with pytest.raises(ValueError, match="No candles found"):
        mock_loader.load_range(query)


def test_load_range_invalid_interval_raises(mock_loader):
    """ValueError for invalid interval."""
    query = DataQuery(connector="nonkyc", trading_pair="BTC-USDT", interval="2m")
    with pytest.raises(ValueError, match="Invalid interval"):
        mock_loader.load_range(query)


def test_is_forward_fill_all_false_without_features(populated_loader):
    """is_forward_fill column is all False when candle_features has no synthetic rows."""
    query = DataQuery(connector="nonkyc", trading_pair="BTC-USDT", interval="5m")
    arr = populated_loader.load_range(query)
    assert not np.any(arr["is_forward_fill"])


def test_ensure_indexes_idempotent(mock_loader):
    """ensure_indexes() can be called twice without error."""
    mock_loader.ensure_indexes()
    mock_loader.ensure_indexes()
    indexes = mock_loader._collection.index_information()
    assert "connector_pair_interval_ts" in indexes


def test_ping_success(mock_loader):
    """ping() returns True with mongomock."""
    assert mock_loader.ping() is True


def test_dedup_keeps_highest_volume(mock_loader):
    """When timestamps collide, the row with highest volume is kept."""
    docs = [
        _make_doc("nonkyc", "BTC-USDT", "5m", 1000, price=100, vol=0.5),
        _make_doc("nonkyc", "BTC-USDT", "5m", 1300, price=101, vol=1.0),   # low vol
        _make_doc("nonkyc", "BTC-USDT", "5m", 1300, price=102, vol=5.0),   # high vol — should be kept
        _make_doc("nonkyc", "BTC-USDT", "5m", 1600, price=103, vol=2.0),
    ]
    mock_loader._collection.insert_many(docs)

    query = DataQuery(connector="nonkyc", trading_pair="BTC-USDT", interval="5m")
    arr = mock_loader.load_range(query)
    assert len(arr) == 3  # 4 docs - 1 duplicate = 3 unique

    # The row at ts=1300 should have the higher volume doc's price
    ts1300_row = arr[arr["timestamp"] == 1300]
    assert len(ts1300_row) == 1
    assert ts1300_row[0]["volume"] == 5.0
    assert ts1300_row[0]["open"] == 102.0


class TestMongoProjection:
    """Mongo queries should project only OHLCV fields."""

    def test_load_range_returns_correct_fields(self, sample_candles_5m, mongo_docs_5m):
        import mongomock
        client = mongomock.MongoClient()
        db = client["test_db"]
        db["candles"].insert_many(mongo_docs_5m)

        from pmm_lab.data.mongo import MongoCandleLoader
        from pmm_lab.config.params import DataQuery
        loader = MongoCandleLoader(client=client, db_name="test_db")
        query = DataQuery(connector="nonkyc", trading_pair="BTC-USDT", interval="5m")
        candles = loader.load_range(query, enrich_synthetic=False)

        assert len(candles) == len(sample_candles_5m)
        for field in ["timestamp", "open", "high", "low", "close", "volume", "is_forward_fill"]:
            assert field in candles.dtype.names
