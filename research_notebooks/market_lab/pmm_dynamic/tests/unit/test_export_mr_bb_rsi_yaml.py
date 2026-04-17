"""Round-trip tests for MR BB+RSI YAML export."""

from pathlib import Path

import pytest
import yaml

from pmm_lab.export.hb_yaml_mr_bb_rsi import (
    MRBBRSIExportParams,
    export_mr_bb_rsi_yaml,
    validate_export_mr_bb_rsi,
)
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.strategies.mean_reversion_bb_rsi import MeanReversionBBRSIStrategyConfig


@pytest.fixture
def strategy_config():
    return MeanReversionBBRSIStrategyConfig()


@pytest.fixture
def engine_config():
    return EngineConfig(
        total_amount_quote=300.0, executor_refresh_time=300.0,
        cooldown_time=3600.0,
        stop_loss=0.04, take_profit=0.03, time_limit=172800,
        take_profit_order_type="LIMIT",
        trailing_stop_activation=0.0, trailing_stop_delta=0.0,
    )


@pytest.fixture
def export_params():
    return MRBBRSIExportParams(
        connector_name="nonkyc", trading_pair="XMR-USDT",
        interval="5m", config_id="test_config",
    )


def test_export_and_validate_roundtrip(tmp_path, strategy_config, engine_config, export_params):
    out = tmp_path / "mr.yml"
    path = export_mr_bb_rsi_yaml(strategy_config, engine_config, export_params, out)
    assert path.exists()
    validate_export_mr_bb_rsi(path)


def test_exported_keys_match_live_template(tmp_path, strategy_config, engine_config, export_params):
    out = tmp_path / "mr.yml"
    export_mr_bb_rsi_yaml(strategy_config, engine_config, export_params, out)
    with open(out) as f:
        data = yaml.safe_load(f)
    # Must include every key the live YAML has
    live_keys = {
        "id", "controller_name", "controller_type", "connector_name", "trading_pair",
        "total_amount_quote", "manual_kill_switch", "initial_positions",
        "max_executors_per_side", "cooldown_time", "leverage", "position_mode",
        "stop_loss", "take_profit", "time_limit", "take_profit_order_type", "trailing_stop",
        "candles_connector", "candles_trading_pair", "interval",
        "bb_length", "bb_std", "bbp_entry_threshold", "rsi_length", "rsi_entry_threshold",
        "use_trend_filter", "trend_ema_length", "min_trend_slope",
        "atr_length", "max_atr_pct_for_entry", "volume_filter_window", "min_volume_quantile",
        "max_spread_pct", "max_trades_per_day",
    }
    assert live_keys.issubset(set(data.keys()))


def test_controller_name_is_correct(tmp_path, strategy_config, engine_config, export_params):
    out = tmp_path / "mr.yml"
    export_mr_bb_rsi_yaml(strategy_config, engine_config, export_params, out)
    with open(out) as f:
        data = yaml.safe_load(f)
    assert data["controller_name"] == "mean_reversion_bb_rsi_v1"


def test_trailing_stop_empty_when_disabled(tmp_path, strategy_config, engine_config, export_params):
    out = tmp_path / "mr.yml"
    export_mr_bb_rsi_yaml(strategy_config, engine_config, export_params, out)
    with open(out) as f:
        data = yaml.safe_load(f)
    assert data["trailing_stop"] == ""


def test_trailing_stop_formatted_when_enabled(tmp_path, strategy_config, export_params):
    ec = EngineConfig(
        total_amount_quote=300.0, cooldown_time=3600.0,
        trailing_stop_activation=0.02, trailing_stop_delta=0.01,
    )
    out = tmp_path / "mr.yml"
    export_mr_bb_rsi_yaml(strategy_config, ec, export_params, out)
    with open(out) as f:
        data = yaml.safe_load(f)
    assert data["trailing_stop"] == "0.02/0.01"
