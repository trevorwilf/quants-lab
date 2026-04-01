"""Tests for MACD-BB YAML export."""

import yaml
import pytest
import tempfile
import os
from pathlib import Path

from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.strategies.macd_bb import MACDBBStrategyConfig
from pmm_lab.optuna.candidate import CandidateBundle
from pmm_lab.export.hb_yaml import export_macd_bb_yaml


@pytest.fixture
def candidate():
    return CandidateBundle(
        strategy_name="macd_bb",
        strategy_config=MACDBBStrategyConfig(
            bb_length=100, bb_std=2.0,
            bb_long_threshold=0.0, bb_short_threshold=1.0,
            macd_fast=21, macd_slow=42, macd_signal=9,
            max_executors_per_side=1,
        ),
        engine_config=EngineConfig(
            total_amount_quote=100.0,
            cooldown_time=300,
            stop_loss=0.03, take_profit=0.02,
            time_limit=43200,
            take_profit_order_type="LIMIT",
            trailing_stop_activation=0.01,
            trailing_stop_delta=0.005,
        ),
        export_meta={
            "controller_name": "macd_bb_v1",
            "controller_type": "directional_trading",
        },
    )


class TestExportMACDBBYaml:
    def test_round_trip(self, candidate, tmp_path):
        out = str(tmp_path / "test.yml")
        result = export_macd_bb_yaml(
            candidate, "nonkyc", "BTC-USDT", "nonkyc", "BTC-USDT", "5m", out,
        )
        assert os.path.exists(result)
        with open(result) as f:
            data = yaml.safe_load(f)
        assert data["controller_name"] == "macd_bb_v1"
        assert data["controller_type"] == "directional_trading"

    def test_all_required_keys_present(self, candidate, tmp_path):
        out = str(tmp_path / "test.yml")
        export_macd_bb_yaml(
            candidate, "nonkyc", "BTC-USDT", "nonkyc", "BTC-USDT", "5m", out,
        )
        with open(out) as f:
            data = yaml.safe_load(f)
        required = [
            "id", "controller_name", "controller_type", "connector_name",
            "trading_pair", "candles_connector", "candles_trading_pair", "interval",
            "total_amount_quote", "max_executors_per_side", "cooldown_time",
            "stop_loss", "take_profit", "time_limit",
            "bb_length", "bb_std", "bb_long_threshold", "bb_short_threshold",
            "macd_fast", "macd_slow", "macd_signal",
            "trailing_stop",
        ]
        for key in required:
            assert key in data, f"Missing key: {key}"

    def test_strategy_params_correct(self, candidate, tmp_path):
        out = str(tmp_path / "test.yml")
        export_macd_bb_yaml(
            candidate, "nonkyc", "BTC-USDT", "nonkyc", "BTC-USDT", "5m", out,
        )
        with open(out) as f:
            data = yaml.safe_load(f)
        assert data["bb_length"] == 100
        assert data["bb_std"] == 2.0
        assert data["macd_fast"] == 21
        assert data["macd_slow"] == 42
        assert data["macd_signal"] == 9
        assert data["stop_loss"] == 0.03
        assert data["take_profit"] == 0.02

    def test_take_profit_order_type_is_int(self, candidate, tmp_path):
        out = str(tmp_path / "test.yml")
        export_macd_bb_yaml(
            candidate, "nonkyc", "BTC-USDT", "nonkyc", "BTC-USDT", "5m", out,
        )
        with open(out) as f:
            data = yaml.safe_load(f)
        assert isinstance(data["take_profit_order_type"], int)
        assert data["take_profit_order_type"] == 2  # LIMIT

    def test_custom_config_id(self, candidate, tmp_path):
        out = str(tmp_path / "test.yml")
        export_macd_bb_yaml(
            candidate, "nonkyc", "BTC-USDT", "nonkyc", "BTC-USDT", "5m", out,
            config_id="custom-id-123",
        )
        with open(out) as f:
            data = yaml.safe_load(f)
        assert data["id"] == "custom-id-123"

    def test_auto_generated_id(self, candidate, tmp_path):
        out = str(tmp_path / "test.yml")
        export_macd_bb_yaml(
            candidate, "nonkyc", "BTC-USDT", "nonkyc", "BTC-USDT", "5m", out,
        )
        with open(out) as f:
            data = yaml.safe_load(f)
        assert "BTC-USDT" in data["id"]
        assert "MACD-BB" in data["id"]
