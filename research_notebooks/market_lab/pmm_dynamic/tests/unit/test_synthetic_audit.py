"""Tests for synthetic candle audit pipeline."""

import numpy as np
import pytest
import mongomock

from pmm_lab.config.params import DataQuery
from pmm_lab.data.mongo import MongoCandleLoader, CANDLE_DTYPE
from pmm_lab.data.candles import validate_candles


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


class TestSyntheticEnrichment:
    """Test loader enrichment from candle_features collection."""

    def test_loader_enriches_synthetic_from_features(self):
        """Loader populates is_forward_fill=True for synthetic rows."""
        client = mongomock.MongoClient()
        loader = MongoCandleLoader(client=client, db_name="test_db")

        # Insert candles
        docs = []
        for i in range(20):
            docs.append(_make_doc("nonkyc", "BTC-USDT", "5m", 1000 + i * 300))
        loader._collection.insert_many(docs)

        # Insert candle_features with is_synthetic=True for bars 5 and 10
        features_coll = client["test_db"]["candle_features"]
        features_coll.insert_many([
            {
                "connector": "nonkyc",
                "trading_pair": "BTC-USDT",
                "interval": "5m",
                "timestamp": 1000 + 5 * 300,
                "is_synthetic": True,
                "no_trade_interval": False,
            },
            {
                "connector": "nonkyc",
                "trading_pair": "BTC-USDT",
                "interval": "5m",
                "timestamp": 1000 + 10 * 300,
                "is_synthetic": False,
                "no_trade_interval": True,
            },
        ])

        query = DataQuery(connector="nonkyc", trading_pair="BTC-USDT", interval="5m")
        arr = loader.load_range(query)
        assert len(arr) == 20
        assert arr[5]["is_forward_fill"] == True
        assert arr[10]["is_forward_fill"] == True
        # Other bars remain False
        assert arr[0]["is_forward_fill"] == False
        assert arr[15]["is_forward_fill"] == False

    def test_loader_no_enrichment_when_features_empty(self):
        """Loader returns all is_forward_fill=False when candle_features is empty."""
        client = mongomock.MongoClient()
        loader = MongoCandleLoader(client=client, db_name="test_db")

        docs = [_make_doc("nonkyc", "BTC-USDT", "5m", 1000 + i * 300) for i in range(10)]
        loader._collection.insert_many(docs)

        query = DataQuery(connector="nonkyc", trading_pair="BTC-USDT", interval="5m")
        arr = loader.load_range(query)
        assert not np.any(arr["is_forward_fill"])


class TestValidatorSplitAudit:
    """Test that validator distinguishes source-declared vs unexpected forward-fills."""

    def test_source_declared_not_unexpected(self):
        """Source-declared forward-fills don't count as unexpected."""
        rows = []
        for i in range(100):
            rows.append((1000 + i * 300, 100.0, 101.0, 99.0, 100.0, 1.0, False))
        candles = np.array(rows, dtype=CANDLE_DTYPE)

        # Mark 2 bars as source-declared synthetic (via is_forward_fill)
        candles[10]["is_forward_fill"] = True
        candles[11]["is_forward_fill"] = True

        audit = validate_candles(candles, "5m", strict=True)
        assert audit.source_synthetic_count == 2
        assert audit.source_synthetic_fraction == pytest.approx(0.02)
        # These are NOT unexpected
        assert audit.unexpected_forward_fill_count == 0
        assert audit.unexpected_forward_fill_fraction == 0.0
        # Should pass strict (2% source synthetic < 5% threshold)
        assert audit.passed_strict is True

    def test_unexpected_forward_fills_fail_strict(self):
        """Heuristic-detected forward-fills that are NOT source-declared fail strict."""
        rows = []
        for i in range(12):
            rows.append([1000 + i * 300, 100.0, 101.0, 99.0, 100.0, 1.0, False])
        # Make bars 2-5 flat + zero volume (heuristic forward-fills) => 4/12 ~33% > 25%
        for bar in [2, 3, 4, 5]:
            rows[bar] = [rows[bar][0], 100.0, 100.0, 100.0, 100.0, 0.0, False]
        candles = np.array([tuple(r) for r in rows], dtype=CANDLE_DTYPE)

        audit = validate_candles(candles, "5m", strict=True)
        assert audit.heuristic_forward_fill_count >= 4
        assert audit.unexpected_forward_fill_count >= 4
        assert audit.passed_strict is False
        assert any("forward-fill" in r for r in audit.failure_reasons)

    def test_heuristic_not_unexpected_when_source_declared(self):
        """If heuristic detects a bar already source-declared, it's NOT unexpected."""
        rows = []
        for i in range(100):
            rows.append([1000 + i * 300, 100.0, 101.0, 99.0, 100.0, 1.0, False])
        # Bar 10: flat + zero vol (heuristic match) AND source-declared
        rows[10] = [rows[10][0], 100.0, 100.0, 100.0, 100.0, 0.0, True]
        candles = np.array([tuple(r) for r in rows], dtype=CANDLE_DTYPE)

        audit = validate_candles(candles, "5m", strict=True)
        assert audit.source_synthetic_count == 1
        assert audit.heuristic_forward_fill_count >= 1
        # Not unexpected because it's source-declared
        assert audit.unexpected_forward_fill_count == 0
        assert audit.passed_strict is True


class TestBackwardCompatibility:
    """Test that legacy data (all is_forward_fill=False) works unchanged."""

    def test_legacy_heuristic_fallback(self):
        """When all is_forward_fill=False, heuristic detection still works."""
        rows = []
        for i in range(20):
            rows.append([1000 + i * 300, 100.0, 101.0, 99.0, 100.0, 1.0, False])
        # Make bars 5 and 6 flat + zero volume
        for bar in [5, 6]:
            rows[bar] = [rows[bar][0], 100.0, 100.0, 100.0, 100.0, 0.0, False]
        candles = np.array([tuple(r) for r in rows], dtype=CANDLE_DTYPE)

        audit = validate_candles(candles, "5m", strict=True)
        assert audit.forward_fill_count >= 2
        assert audit.source_synthetic_count == 0
        assert audit.unexpected_forward_fill_count >= 2

    def test_clean_data_unchanged(self, sample_candles_5m):
        """Clean data still passes strict audit."""
        audit = validate_candles(sample_candles_5m, "5m", strict=True)
        assert audit.passed_strict is True
        assert audit.forward_fill_count == 0
        assert audit.source_synthetic_count == 0
        assert audit.unexpected_forward_fill_count == 0


class TestPreviouslySkippedPairs:
    """Test that pairs with source-declared synthetics now pass."""

    def test_source_declared_1_6_pct_passes(self):
        """A dataset where 1.6% of bars are source-declared synthetic passes strict."""
        n = 500
        rows = []
        for i in range(n):
            rows.append((1000 + i * 300, 100.0, 101.0, 99.0, 100.0, 1.0, False))
        candles = np.array(rows, dtype=CANDLE_DTYPE)

        # Mark 8 bars (1.6%) as source-declared synthetic
        for idx in [10, 50, 100, 150, 200, 250, 300, 350]:
            candles[idx]["is_forward_fill"] = True

        audit = validate_candles(candles, "5m", strict=True)
        assert audit.source_synthetic_fraction == pytest.approx(8 / 500)
        assert audit.unexpected_forward_fill_count == 0
        # 1.6% < 5% source threshold => passes
        assert audit.passed_strict is True
