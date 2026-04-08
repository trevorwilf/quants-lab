"""Tests for NonKYC post-only warning in validate_export.py (Fix 5)."""

import tempfile
import yaml
from pathlib import Path

from pmm_lab.export.validate_export import validate_yaml_file


def _make_valid_config():
    return {
        "id": "test-001",
        "controller_name": "pmm_dynamic",
        "controller_type": "market_making",
        "connector_name": "nonkyc",
        "trading_pair": "XMR-USDT",
        "buy_spreads": [1.0, 2.0],
        "sell_spreads": [1.0, 2.0],
        "buy_amounts_pct": [0.25, 0.25],
        "sell_amounts_pct": [0.25, 0.25],
        "total_amount_quote": 100.0,
        "macd_fast": 12,
        "macd_slow": 26,
        "macd_signal": 9,
        "natr_length": 14,
        "candles_connector": "nonkyc",
        "candles_trading_pair": "XMR-USDT",
        "interval": "5m",
        "stop_loss": 0.03,
        "take_profit": 0.02,
        "time_limit": 3600,
        "cooldown_time": 60,
        "executor_refresh_time": 120,
        "skip_rebalance": True,
        "position_rebalance_threshold_pct": 0.0,
    }


def _write_yaml(config, tmp_path):
    path = tmp_path / "test_config.yaml"
    with open(path, "w") as f:
        yaml.dump(config, f)
    return str(path)


class TestPostOnlyWarning:
    def test_warning_fires_for_nonkyc_no_taker_prob(self, tmp_path):
        """Warning should fire for nonkyc with taker_probability=0.0."""
        path = _write_yaml(_make_valid_config(), tmp_path)
        result = validate_yaml_file(path, supports_post_only=False, taker_probability=0.0)
        post_only_warnings = [w for w in result.warnings if "post-only" in w.lower()]
        assert len(post_only_warnings) == 1
        assert "nonkyc" in post_only_warnings[0]

    def test_no_warning_for_mexc(self, tmp_path):
        """Warning should NOT fire for mexc (supports post-only)."""
        config = _make_valid_config()
        config["connector_name"] = "mexc"
        path = _write_yaml(config, tmp_path)
        result = validate_yaml_file(path, supports_post_only=True, taker_probability=0.0)
        post_only_warnings = [w for w in result.warnings if "post-only" in w.lower()]
        assert len(post_only_warnings) == 0

    def test_no_warning_with_taker_probability(self, tmp_path):
        """Warning should NOT fire when taker_probability > 0."""
        path = _write_yaml(_make_valid_config(), tmp_path)
        result = validate_yaml_file(path, supports_post_only=False, taker_probability=0.1)
        post_only_warnings = [w for w in result.warnings if "post-only" in w.lower()]
        assert len(post_only_warnings) == 0

    def test_no_warning_when_no_kwargs(self, tmp_path):
        """No warning when kwargs not provided (backward compat)."""
        path = _write_yaml(_make_valid_config(), tmp_path)
        result = validate_yaml_file(path)
        post_only_warnings = [w for w in result.warnings if "post-only" in w.lower()]
        assert len(post_only_warnings) == 0
