"""Tests for live_tracker.py schema fix (Fix 1).

Uses in-memory SQLite with the correct Hummingbot TradeFill schema.
"""

import json
import pytest
from datetime import datetime, timezone, timedelta

from pmm_lab.deploy.live_tracker import (
    LivePerformanceTracker,
    TrackerHealth,
    SCHEMA_VERSION,
    _EXPECTED_COLUMNS,
)


def _create_test_db(tmp_path, rows=None, schema="correct"):
    """Create a SQLite database with TradeFill table.

    Parameters
    ----------
    schema : str
        "correct" — real Hummingbot schema
        "old_broken" — the old wrong schema (trade_id, trade_fee_amount, etc.)
    """
    import sqlite3
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    if schema == "correct":
        cur.execute("""
            CREATE TABLE "TradeFill" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_file_path TEXT,
                strategy TEXT,
                market TEXT,
                symbol TEXT,
                base_asset TEXT,
                quote_asset TEXT,
                timestamp INTEGER,
                order_id TEXT,
                trade_type TEXT,
                order_type TEXT,
                price REAL,
                amount REAL,
                leverage INTEGER DEFAULT 0,
                trade_fee TEXT,
                trade_fee_in_quote REAL,
                exchange_trade_id TEXT,
                position TEXT,
                exchange_order_id TEXT
            )
        """)
    elif schema == "old_broken":
        cur.execute("""
            CREATE TABLE "TradeFill" (
                trade_id TEXT,
                symbol TEXT,
                trade_type TEXT,
                price REAL,
                amount REAL,
                trade_fee_amount REAL,
                trade_fee_currency TEXT,
                timestamp TEXT,
                order_type TEXT,
                market TEXT
            )
        """)

    if rows:
        for row in rows:
            if schema == "correct":
                cur.execute(
                    """INSERT INTO "TradeFill"
                       (market, symbol, trade_type, price, amount,
                        trade_fee, trade_fee_in_quote, timestamp,
                        order_type, exchange_trade_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    row,
                )
            elif schema == "old_broken":
                cur.execute(
                    """INSERT INTO "TradeFill"
                       (market, symbol, trade_type, price, amount,
                        trade_fee_amount, trade_fee_currency, timestamp,
                        order_type, trade_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    row,
                )

    conn.commit()
    conn.close()
    return f"sqlite:///{db_path}"


def _make_fee_json(flat_amount, token="USDT"):
    """Create a Hummingbot-style trade_fee JSON string."""
    return json.dumps({
        "percent": "0",
        "percent_token": token,
        "flat_fees": [{"token": token, "amount": str(flat_amount)}],
    })


class TestSchemaVersion:
    def test_schema_version_is_2(self):
        assert SCHEMA_VERSION == 2

    def test_expected_columns_includes_correct_names(self):
        assert "exchange_trade_id" in _EXPECTED_COLUMNS
        assert "trade_fee" in _EXPECTED_COLUMNS
        assert "trade_fee_in_quote" in _EXPECTED_COLUMNS
        assert "trade_id" not in _EXPECTED_COLUMNS
        assert "trade_fee_amount" not in _EXPECTED_COLUMNS
        assert "trade_fee_currency" not in _EXPECTED_COLUMNS


class TestGetTradesCorrectSchema:
    """Verify get_trades() works with the real Hummingbot TradeFill schema."""

    def test_basic_trade_fetch(self, tmp_path):
        ts_ms = int(datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
        fee_json = _make_fee_json(0.05, "USDT")
        rows = [
            ("nonkyc", "XMR-USDT", "BUY", 150.0, 0.5,
             fee_json, 0.05, ts_ms, "LIMIT", "ext-trade-001"),
        ]
        db_url = _create_test_db(tmp_path, rows)
        tracker = LivePerformanceTracker(db_url)
        since = datetime(2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc)
        trades = tracker.get_trades("nonkyc", "XMR-USDT", since=since)

        assert len(trades) == 1
        t = trades[0]
        assert t.trade_id == "ext-trade-001"
        assert t.trading_pair == "XMR-USDT"
        assert t.side == "buy"
        assert t.price == 150.0
        assert t.amount == 0.5
        assert t.fee_amount == 0.05  # from trade_fee_in_quote
        assert t.order_type == "LIMIT"
        assert t.timestamp.tzinfo is not None  # timezone-aware

    def test_timestamp_filtering_milliseconds(self, tmp_path):
        """Timestamp filtering uses milliseconds correctly."""
        base_dt = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)
        ts1 = int(base_dt.timestamp() * 1000)
        ts2 = int((base_dt + timedelta(hours=2)).timestamp() * 1000)
        fee_json = _make_fee_json(0.01)
        rows = [
            ("nonkyc", "XMR-USDT", "BUY", 150.0, 0.1,
             fee_json, 0.01, ts1, "LIMIT", "t1"),
            ("nonkyc", "XMR-USDT", "SELL", 151.0, 0.1,
             fee_json, 0.01, ts2, "LIMIT", "t2"),
        ]
        db_url = _create_test_db(tmp_path, rows)
        tracker = LivePerformanceTracker(db_url)

        # Fetch only trades after the first one
        since = base_dt + timedelta(hours=1)
        trades = tracker.get_trades("nonkyc", "XMR-USDT", since=since)
        assert len(trades) == 1
        assert trades[0].trade_id == "t2"

    def test_fee_from_trade_fee_in_quote(self, tmp_path):
        """Prefers trade_fee_in_quote when available."""
        ts_ms = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp() * 1000)
        fee_json = _make_fee_json(0.99, "XMR")  # JSON says 0.99 in XMR
        rows = [
            ("nonkyc", "XMR-USDT", "BUY", 150.0, 0.5,
             fee_json, 0.075, ts_ms, "LIMIT", "t1"),  # trade_fee_in_quote=0.075
        ]
        db_url = _create_test_db(tmp_path, rows)
        tracker = LivePerformanceTracker(db_url)
        since = datetime(2026, 3, 1, tzinfo=timezone.utc)
        trades = tracker.get_trades("nonkyc", "XMR-USDT", since=since)
        assert trades[0].fee_amount == 0.075  # prefers trade_fee_in_quote

    def test_fee_fallback_to_json(self, tmp_path):
        """Falls back to JSON parsing when trade_fee_in_quote is 0."""
        ts_ms = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp() * 1000)
        fee_json = _make_fee_json(0.123, "USDT")
        rows = [
            ("nonkyc", "XMR-USDT", "BUY", 150.0, 0.5,
             fee_json, 0.0, ts_ms, "LIMIT", "t1"),  # trade_fee_in_quote=0
        ]
        db_url = _create_test_db(tmp_path, rows)
        tracker = LivePerformanceTracker(db_url)
        since = datetime(2026, 3, 1, tzinfo=timezone.utc)
        trades = tracker.get_trades("nonkyc", "XMR-USDT", since=since)
        assert abs(trades[0].fee_amount - 0.123) < 1e-9
        assert trades[0].fee_currency == "USDT"

    def test_fee_in_base_currency(self, tmp_path):
        """Fee in base currency is parsed from JSON."""
        ts_ms = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp() * 1000)
        fee_json = _make_fee_json(0.001, "XMR")
        rows = [
            ("nonkyc", "XMR-USDT", "BUY", 150.0, 0.5,
             fee_json, 0.0, ts_ms, "LIMIT", "t1"),
        ]
        db_url = _create_test_db(tmp_path, rows)
        tracker = LivePerformanceTracker(db_url)
        since = datetime(2026, 3, 1, tzinfo=timezone.utc)
        trades = tracker.get_trades("nonkyc", "XMR-USDT", since=since)
        assert abs(trades[0].fee_amount - 0.001) < 1e-9
        assert trades[0].fee_currency == "XMR"

    def test_fee_third_party_token(self, tmp_path):
        """Fee in a third-party token preserves the currency info."""
        ts_ms = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp() * 1000)
        fee_json = _make_fee_json(5.0, "BNB")
        rows = [
            ("nonkyc", "XMR-USDT", "BUY", 150.0, 0.5,
             fee_json, 0.0, ts_ms, "LIMIT", "t1"),
        ]
        db_url = _create_test_db(tmp_path, rows)
        tracker = LivePerformanceTracker(db_url)
        since = datetime(2026, 3, 1, tzinfo=timezone.utc)
        trades = tracker.get_trades("nonkyc", "XMR-USDT", since=since)
        assert abs(trades[0].fee_amount - 5.0) < 1e-9
        assert trades[0].fee_currency == "BNB"


class TestSchemaCheck:
    """Verify _check_schema() detects missing columns."""

    def test_correct_schema_passes(self, tmp_path):
        db_url = _create_test_db(tmp_path, schema="correct")
        tracker = LivePerformanceTracker(db_url)
        since = datetime(2026, 3, 1, tzinfo=timezone.utc)
        tracker.get_trades("nonkyc", "XMR-USDT", since=since)
        assert tracker.last_health != TrackerHealth.SCHEMA_ERROR

    def test_old_broken_schema_detected(self, tmp_path):
        """The old wrong schema (trade_id, trade_fee_amount) triggers SCHEMA_ERROR."""
        db_url = _create_test_db(tmp_path, schema="old_broken")
        tracker = LivePerformanceTracker(db_url)
        since = datetime(2026, 3, 1, tzinfo=timezone.utc)
        trades = tracker.get_trades("nonkyc", "XMR-USDT", since=since)
        assert trades == []
        assert tracker.last_health == TrackerHealth.SCHEMA_ERROR
        assert "missing columns" in tracker.last_error.lower()


class TestTimestampConversion:
    """Verify millisecond timestamps are correctly converted to datetime."""

    def test_timestamp_roundtrip(self, tmp_path):
        expected_dt = datetime(2026, 4, 1, 15, 30, 45, tzinfo=timezone.utc)
        ts_ms = int(expected_dt.timestamp() * 1000)
        fee_json = _make_fee_json(0.01)
        rows = [
            ("nonkyc", "XMR-USDT", "BUY", 100.0, 1.0,
             fee_json, 0.01, ts_ms, "LIMIT", "t1"),
        ]
        db_url = _create_test_db(tmp_path, rows)
        tracker = LivePerformanceTracker(db_url)
        since = datetime(2026, 3, 1, tzinfo=timezone.utc)
        trades = tracker.get_trades("nonkyc", "XMR-USDT", since=since)
        # Should match within 1 second (millisecond precision)
        delta = abs((trades[0].timestamp - expected_dt).total_seconds())
        assert delta < 1.0


class TestOldQueryWouldFail:
    """Regression guard: the old query with wrong columns would fail."""

    def test_old_column_names_not_in_correct_schema(self, tmp_path):
        """Columns trade_id, trade_fee_amount, trade_fee_currency don't exist."""
        import sqlite3
        db_path = tmp_path / "test.db"
        db_url = _create_test_db(tmp_path, schema="correct")
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        with pytest.raises(sqlite3.OperationalError):
            cur.execute("""
                SELECT trade_id, symbol, trade_type, price, amount,
                       trade_fee_amount, trade_fee_currency, timestamp, order_type
                FROM "TradeFill"
            """)
        conn.close()
