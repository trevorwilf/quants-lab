"""Integration tests for LivePerformanceTracker (Hummingbot PostgreSQL).

Auto-skip if the database is unreachable.
"""

import pytest

from pmm_lab.deploy.live_tracker import LivePerformanceTracker, LivePerformanceMetrics


def _hbot_db_reachable() -> bool:
    try:
        tracker = LivePerformanceTracker()
        return tracker.ping()
    except Exception:
        return False


HBOT_DB_AVAILABLE = _hbot_db_reachable()


@pytest.mark.live_hbot_db
@pytest.mark.skipif(not HBOT_DB_AVAILABLE, reason="Hummingbot PostgreSQL not reachable")
class TestTrackerPing:
    def test_tracker_ping(self):
        tracker = LivePerformanceTracker()
        assert tracker.ping() is True


@pytest.mark.live_hbot_db
@pytest.mark.skipif(not HBOT_DB_AVAILABLE, reason="Hummingbot PostgreSQL not reachable")
class TestTrackerGetTradesReturnsList:
    def test_tracker_get_trades_returns_list(self):
        tracker = LivePerformanceTracker()
        trades = tracker.get_trades("nonkyc", "XMR-USDT", hours=24)
        assert isinstance(trades, list)


@pytest.mark.live_hbot_db
@pytest.mark.skipif(not HBOT_DB_AVAILABLE, reason="Hummingbot PostgreSQL not reachable")
class TestTrackerGetPerformanceReturnsMetrics:
    def test_tracker_get_performance_returns_metrics(self):
        tracker = LivePerformanceTracker()
        metrics = tracker.get_performance("nonkyc", "XMR-USDT", hours=24)
        assert isinstance(metrics, LivePerformanceMetrics)
        assert metrics.trading_pair == "XMR-USDT"
