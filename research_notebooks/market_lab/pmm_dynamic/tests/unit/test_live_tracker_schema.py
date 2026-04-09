"""Tests for live_tracker.py schema fix.

Uses in-memory SQLite with the correct Hummingbot TradeFill schema.
All price/amount/trade_fee_in_quote values are stored as BIGINT * 1e6
to match real Hummingbot behavior.
"""

import json
import pytest
from datetime import datetime, timezone, timedelta

from pmm_lab.deploy.live_tracker import (
    LivePerformanceTracker,
    TrackerHealth,
    SCHEMA_VERSION,
    BIGINT_SCALE,
    _EXPECTED_COLUMNS,
)

# Helper: convert a human-readable float to the BIGINT value Hummingbot stores
def _to_bigint(value):
    return int(value * BIGINT_SCALE)


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
                price INTEGER,
                amount INTEGER,
                leverage INTEGER DEFAULT 0,
                trade_fee TEXT,
                trade_fee_in_quote INTEGER,
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

    def test_bigint_scale_is_1e6(self):
        assert BIGINT_SCALE == 1_000_000

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
            ("nonkyc", "XMR-USDT", "BUY", _to_bigint(150.0), _to_bigint(0.5),
             fee_json, _to_bigint(0.05), ts_ms, "LIMIT", "ext-trade-001"),
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
        assert abs(t.price - 150.0) < 1e-6
        assert abs(t.amount - 0.5) < 1e-6
        assert abs(t.fee_amount - 0.05) < 1e-6  # from trade_fee_in_quote
        assert t.order_type == "LIMIT"
        assert t.timestamp.tzinfo is not None  # timezone-aware

    def test_timestamp_filtering_milliseconds(self, tmp_path):
        """Timestamp filtering uses milliseconds correctly."""
        base_dt = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)
        ts1 = int(base_dt.timestamp() * 1000)
        ts2 = int((base_dt + timedelta(hours=2)).timestamp() * 1000)
        fee_json = _make_fee_json(0.01)
        rows = [
            ("nonkyc", "XMR-USDT", "BUY", _to_bigint(150.0), _to_bigint(0.1),
             fee_json, _to_bigint(0.01), ts1, "LIMIT", "t1"),
            ("nonkyc", "XMR-USDT", "SELL", _to_bigint(151.0), _to_bigint(0.1),
             fee_json, _to_bigint(0.01), ts2, "LIMIT", "t2"),
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
            ("nonkyc", "XMR-USDT", "BUY", _to_bigint(150.0), _to_bigint(0.5),
             fee_json, _to_bigint(0.075), ts_ms, "LIMIT", "t1"),
        ]
        db_url = _create_test_db(tmp_path, rows)
        tracker = LivePerformanceTracker(db_url)
        since = datetime(2026, 3, 1, tzinfo=timezone.utc)
        trades = tracker.get_trades("nonkyc", "XMR-USDT", since=since)
        assert abs(trades[0].fee_amount - 0.075) < 1e-6

    def test_fee_fallback_to_json(self, tmp_path):
        """Falls back to JSON parsing when trade_fee_in_quote is 0."""
        ts_ms = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp() * 1000)
        fee_json = _make_fee_json(0.123, "USDT")
        rows = [
            ("nonkyc", "XMR-USDT", "BUY", _to_bigint(150.0), _to_bigint(0.5),
             fee_json, 0, ts_ms, "LIMIT", "t1"),  # trade_fee_in_quote=0
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
            ("nonkyc", "XMR-USDT", "BUY", _to_bigint(150.0), _to_bigint(0.5),
             fee_json, 0, ts_ms, "LIMIT", "t1"),
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
            ("nonkyc", "XMR-USDT", "BUY", _to_bigint(150.0), _to_bigint(0.5),
             fee_json, 0, ts_ms, "LIMIT", "t1"),
        ]
        db_url = _create_test_db(tmp_path, rows)
        tracker = LivePerformanceTracker(db_url)
        since = datetime(2026, 3, 1, tzinfo=timezone.utc)
        trades = tracker.get_trades("nonkyc", "XMR-USDT", since=since)
        assert abs(trades[0].fee_amount - 5.0) < 1e-9
        assert trades[0].fee_currency == "BNB"


class TestBigintScaling:
    """Verify BIGINT columns are correctly divided by 1e6."""

    def test_price_scaled(self, tmp_path):
        """price=187325 (BIGINT) → 0.187325"""
        ts_ms = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp() * 1000)
        fee_json = _make_fee_json(0.001)
        rows = [
            ("nonkyc", "ARRR-USDT", "BUY", 187325, _to_bigint(24.44),
             fee_json, 0, ts_ms, "LIMIT", "t1"),
        ]
        db_url = _create_test_db(tmp_path, rows)
        tracker = LivePerformanceTracker(db_url)
        since = datetime(2026, 3, 1, tzinfo=timezone.utc)
        trades = tracker.get_trades("nonkyc", "ARRR-USDT", since=since)
        assert abs(trades[0].price - 0.187325) < 1e-9

    def test_amount_scaled(self, tmp_path):
        """amount=24440000 (BIGINT) → 24.44"""
        ts_ms = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp() * 1000)
        fee_json = _make_fee_json(0.001)
        rows = [
            ("nonkyc", "ARRR-USDT", "BUY", _to_bigint(0.187), 24440000,
             fee_json, 0, ts_ms, "LIMIT", "t1"),
        ]
        db_url = _create_test_db(tmp_path, rows)
        tracker = LivePerformanceTracker(db_url)
        since = datetime(2026, 3, 1, tzinfo=timezone.utc)
        trades = tracker.get_trades("nonkyc", "ARRR-USDT", since=since)
        assert abs(trades[0].amount - 24.44) < 1e-9

    def test_trade_fee_in_quote_scaled(self, tmp_path):
        """trade_fee_in_quote=9156 (BIGINT) → 0.009156"""
        ts_ms = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp() * 1000)
        fee_json = _make_fee_json(0.009, "USDT")
        rows = [
            ("nonkyc", "ARRR-USDT", "BUY", _to_bigint(0.187), _to_bigint(24.44),
             fee_json, 9156, ts_ms, "LIMIT", "t1"),
        ]
        db_url = _create_test_db(tmp_path, rows)
        tracker = LivePerformanceTracker(db_url)
        since = datetime(2026, 3, 1, tzinfo=timezone.utc)
        trades = tracker.get_trades("nonkyc", "ARRR-USDT", since=since)
        assert abs(trades[0].fee_amount - 0.009156) < 1e-9

    def test_json_fee_not_double_scaled(self, tmp_path):
        """Fee from JSON flat_fees should NOT be divided by 1e6."""
        ts_ms = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp() * 1000)
        fee_json = _make_fee_json(0.0041455046, "USDT")
        rows = [
            ("nonkyc", "ARRR-USDT", "BUY", _to_bigint(0.187), _to_bigint(24.44),
             fee_json, 0, ts_ms, "LIMIT", "t1"),  # trade_fee_in_quote=0 → fallback to JSON
        ]
        db_url = _create_test_db(tmp_path, rows)
        tracker = LivePerformanceTracker(db_url)
        since = datetime(2026, 3, 1, tzinfo=timezone.utc)
        trades = tracker.get_trades("nonkyc", "ARRR-USDT", since=since)
        assert abs(trades[0].fee_amount - 0.0041455046) < 1e-12

    def test_timestamp_not_scaled(self, tmp_path):
        """Timestamp should NOT be divided by 1e6 — it's already milliseconds."""
        expected_dt = datetime(2026, 4, 1, 15, 30, 45, tzinfo=timezone.utc)
        ts_ms = int(expected_dt.timestamp() * 1000)
        fee_json = _make_fee_json(0.01)
        rows = [
            ("nonkyc", "XMR-USDT", "BUY", _to_bigint(100.0), _to_bigint(1.0),
             fee_json, _to_bigint(0.01), ts_ms, "LIMIT", "t1"),
        ]
        db_url = _create_test_db(tmp_path, rows)
        tracker = LivePerformanceTracker(db_url)
        since = datetime(2026, 3, 1, tzinfo=timezone.utc)
        trades = tracker.get_trades("nonkyc", "XMR-USDT", since=since)
        delta = abs((trades[0].timestamp - expected_dt).total_seconds())
        assert delta < 1.0


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
