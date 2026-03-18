"""LivePerformanceTracker must expose query health state, not just empty results."""
import pytest
from unittest.mock import patch, MagicMock
from pmm_lab.deploy.live_tracker import LivePerformanceTracker, TrackerHealth


class TestTrackerHealthState:
    """Tracker must distinguish DB errors from no-data."""

    def test_initial_health_is_ok(self):
        tracker = LivePerformanceTracker(db_url="postgresql+psycopg2://x:x@localhost/test")
        assert tracker.last_health == TrackerHealth.OK

    def test_db_error_sets_health(self):
        tracker = LivePerformanceTracker(db_url="postgresql+psycopg2://x:x@localhost/test")
        # Force a DB error by mocking the engine
        with patch.object(tracker, '_get_engine') as mock_engine:
            mock_conn = MagicMock()
            mock_conn.__enter__ = MagicMock(side_effect=Exception("Connection refused"))
            mock_engine.return_value.connect.return_value = mock_conn
            trades = tracker.get_trades("nonkyc", "XMR-USDT")

        assert trades == []
        assert tracker.last_health == TrackerHealth.DB_ERROR
        assert "Connection refused" in tracker.last_error

    def test_health_property_exists(self):
        tracker = LivePerformanceTracker(db_url="postgresql+psycopg2://x:x@localhost/test")
        assert hasattr(tracker, 'last_health')
        assert hasattr(tracker, 'last_error')
