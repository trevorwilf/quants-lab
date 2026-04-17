"""Round-trip tests for EMA regime-hold YAML export."""

from pathlib import Path

import pytest
import yaml

from pmm_lab.export.hb_yaml_ema_regime_hold import (
    EMARegimeHoldExportParams,
    export_ema_regime_hold_yaml,
    validate_export_ema_regime_hold,
)
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig


@pytest.fixture
def strategy_config():
    return EMARegimeHoldStrategyConfig()


@pytest.fixture
def engine_config():
    return EngineConfig(
        total_amount_quote=300.0, executor_refresh_time=300.0, cooldown_time=3600.0,
        stop_loss=0.04, take_profit=0.03, time_limit=172800,
        take_profit_order_type="LIMIT",
        trailing_stop_activation=0.0, trailing_stop_delta=0.0,
    )


@pytest.fixture
def export_params():
    return EMARegimeHoldExportParams(
        connector_name="nonkyc", trading_pair="XMR-USDT",
        signal_interval="5m", regime_interval="4h",
        config_id="test_config",
    )


def test_export_and_validate_roundtrip(tmp_path, strategy_config, engine_config, export_params):
    out = tmp_path / "ema.yml"
    export_ema_regime_hold_yaml(strategy_config, engine_config, export_params, out)
    validate_export_ema_regime_hold(out)


def test_hold_mode_always_reentry(tmp_path, strategy_config, engine_config, export_params):
    out = tmp_path / "ema.yml"
    export_ema_regime_hold_yaml(strategy_config, engine_config, export_params, out)
    with open(out) as f:
        data = yaml.safe_load(f)
    assert data["hold_mode"] == "reentry"


def test_exported_keys_match_live_template(tmp_path, strategy_config, engine_config, export_params):
    out = tmp_path / "ema.yml"
    export_ema_regime_hold_yaml(strategy_config, engine_config, export_params, out)
    with open(out) as f:
        data = yaml.safe_load(f)
    required = {
        "id", "controller_name", "controller_type", "connector_name", "trading_pair",
        "total_amount_quote", "max_executors_per_side", "cooldown_time",
        "stop_loss", "take_profit", "time_limit", "take_profit_order_type", "trailing_stop",
        "signal_interval", "regime_interval",
        "regime_ema_fast", "regime_ema_slow", "regime_adx_length", "regime_adx_threshold",
        "volume_filter_window", "min_volume_quantile", "hold_mode",
    }
    assert required.issubset(set(data.keys()))


def test_fast_slow_ordering_validated(tmp_path, engine_config, export_params):
    # Force bad ordering
    bad = EMARegimeHoldStrategyConfig(regime_ema_fast=100, regime_ema_slow=50)
    out = tmp_path / "ema.yml"
    export_ema_regime_hold_yaml(bad, engine_config, export_params, out)
    with pytest.raises(ValueError, match="regime_ema_fast"):
        validate_export_ema_regime_hold(out)
