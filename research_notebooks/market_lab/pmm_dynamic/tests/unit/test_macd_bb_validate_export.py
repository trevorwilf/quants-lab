"""Tests for MACD-BB YAML validation."""

import yaml
import pytest
import tempfile

from pmm_lab.export.validate_export import validate_yaml_file, _validate_macd_bb_mirror


@pytest.fixture
def valid_macd_bb_dict():
    return {
        "id": "BTC-USDT-MACD-BB_100",
        "controller_name": "macd_bb_v1",
        "controller_type": "directional_trading",
        "connector_name": "nonkyc",
        "trading_pair": "BTC-USDT",
        "candles_connector": "nonkyc",
        "candles_trading_pair": "BTC-USDT",
        "interval": "5m",
        "total_amount_quote": 100.0,
        "max_executors_per_side": 1,
        "cooldown_time": 300,
        "stop_loss": 0.03,
        "take_profit": 0.02,
        "time_limit": 43200,
        "take_profit_order_type": 2,
        "bb_length": 100,
        "bb_std": 2.0,
        "bb_long_threshold": 0.0,
        "bb_short_threshold": 1.0,
        "macd_fast": 21,
        "macd_slow": 42,
        "macd_signal": 9,
        "leverage": 1,
        "trailing_stop": {
            "activation_price": 0.01,
            "trailing_delta": 0.005,
        },
    }


class TestValidYaml:
    def test_valid_passes(self, valid_macd_bb_dict):
        result = _validate_macd_bb_mirror(valid_macd_bb_dict)
        assert result.valid, f"Errors: {result.errors}"

    def test_round_trip_via_file(self, valid_macd_bb_dict, tmp_path):
        out = tmp_path / "test.yml"
        with open(out, "w") as f:
            yaml.dump(valid_macd_bb_dict, f)
        result = validate_yaml_file(str(out))
        assert result.valid, f"Errors: {result.errors}"


class TestMissingKeys:
    def test_missing_required_key(self, valid_macd_bb_dict):
        del valid_macd_bb_dict["bb_length"]
        result = _validate_macd_bb_mirror(valid_macd_bb_dict)
        assert not result.valid
        assert any("bb_length" in e for e in result.errors)


class TestControllerName:
    def test_wrong_controller_name(self, valid_macd_bb_dict):
        valid_macd_bb_dict["controller_name"] = "pmm_dynamic"
        result = _validate_macd_bb_mirror(valid_macd_bb_dict)
        assert not result.valid

    def test_wrong_controller_type(self, valid_macd_bb_dict):
        valid_macd_bb_dict["controller_type"] = "market_making"
        result = _validate_macd_bb_mirror(valid_macd_bb_dict)
        assert not result.valid


class TestConstraints:
    def test_macd_fast_ge_slow(self, valid_macd_bb_dict):
        valid_macd_bb_dict["macd_fast"] = 50
        valid_macd_bb_dict["macd_slow"] = 42
        result = _validate_macd_bb_mirror(valid_macd_bb_dict)
        assert not result.valid

    def test_bb_threshold_order(self, valid_macd_bb_dict):
        valid_macd_bb_dict["bb_long_threshold"] = 1.5
        valid_macd_bb_dict["bb_short_threshold"] = 0.5
        result = _validate_macd_bb_mirror(valid_macd_bb_dict)
        assert not result.valid

    def test_invalid_tp_order_type(self, valid_macd_bb_dict):
        valid_macd_bb_dict["take_profit_order_type"] = 5
        result = _validate_macd_bb_mirror(valid_macd_bb_dict)
        assert not result.valid


class TestDispatch:
    def test_pmm_yaml_still_validated(self, tmp_path):
        """PMM Dynamic YAML should still be validated by the PMM validator."""
        pmm_dict = {
            "id": "test",
            "controller_name": "pmm_dynamic",
            "controller_type": "market_making",
            "connector_name": "nonkyc",
            "trading_pair": "BTC-USDT",
            "candles_connector": "nonkyc",
            "candles_trading_pair": "BTC-USDT",
            "interval": "5m",
            "buy_spreads": [0.01],
            "sell_spreads": [0.01],
            "buy_amounts_pct": [0.5],
            "sell_amounts_pct": [0.5],
            "total_amount_quote": 100.0,
            "macd_fast": 21,
            "macd_slow": 42,
            "macd_signal": 9,
            "natr_length": 14,
        }
        out = tmp_path / "pmm.yml"
        with open(out, "w") as f:
            yaml.dump(pmm_dict, f)
        result = validate_yaml_file(str(out))
        # Should use PMM validator, not MACD-BB
        assert result.mode == "mirror"  # mirror mode for PMM
