"""EMA: exporting a YAML with hold_mode='hold' must fail validation until parity exists."""
import pytest


def test_hold_mode_hold_is_blocked_by_export_validator(tmp_path):
    from pmm_lab.export.validate_export import validate_yaml_file
    yaml_text = """
id: test
controller_name: ema_regime_hold_v1
controller_type: directional_trading
connector_name: nonkyc
trading_pair: XMR-USDT
total_amount_quote: 100.0
max_executors_per_side: 1
cooldown_time: 600
stop_loss: 0.03
take_profit: 0.02
time_limit: 86400
take_profit_order_type: LIMIT
trailing_stop: ''
signal_interval: 5m
regime_interval: 4h
regime_ema_fast: 10
regime_ema_slow: 30
regime_adx_length: 14
regime_adx_threshold: 20.0
volume_filter_window: 288
min_volume_quantile: 0.3
hold_mode: hold
"""
    p = tmp_path / "bad.yml"
    p.write_text(yaml_text.strip())
    result = validate_yaml_file(p)
    assert not result.valid, "hold_mode='hold' must fail export validation"
    assert any("hold_mode" in e and "hold" in e for e in result.errors), (
        f"Expected a hold_mode error, got: {result.errors}"
    )


def test_hold_mode_reentry_passes_export_validator(tmp_path):
    from pmm_lab.export.validate_export import validate_yaml_file
    yaml_text = """
id: test
controller_name: ema_regime_hold_v1
controller_type: directional_trading
connector_name: nonkyc
trading_pair: XMR-USDT
total_amount_quote: 100.0
max_executors_per_side: 1
cooldown_time: 600
stop_loss: 0.03
take_profit: 0.02
time_limit: 86400
take_profit_order_type: LIMIT
trailing_stop: ''
signal_interval: 5m
regime_interval: 4h
regime_ema_fast: 10
regime_ema_slow: 30
regime_adx_length: 14
regime_adx_threshold: 20.0
volume_filter_window: 288
min_volume_quantile: 0.3
hold_mode: reentry
"""
    p = tmp_path / "good.yml"
    p.write_text(yaml_text.strip())
    result = validate_yaml_file(p)
    assert result.valid, f"hold_mode='reentry' must pass, got errors: {result.errors}"


def test_hold_mode_hold_blocked_by_strategy_specific_validator(tmp_path):
    """The strategy-specific validator raises; the generic one returns ValidationResult."""
    from pmm_lab.export.hb_yaml_ema_regime_hold import validate_export_ema_regime_hold
    yaml_text = """
id: test
controller_name: ema_regime_hold_v1
controller_type: directional_trading
connector_name: nonkyc
trading_pair: XMR-USDT
total_amount_quote: '100.0'
max_executors_per_side: 1
cooldown_time: 600
stop_loss: '0.03'
take_profit: '0.02'
time_limit: 86400
take_profit_order_type: LIMIT
trailing_stop: ''
candles_connector: ''
candles_trading_pair: ''
signal_interval: 5m
regime_interval: 4h
regime_ema_fast: 10
regime_ema_slow: 30
regime_adx_length: 14
regime_adx_threshold: 20.0
volume_filter_window: 288
min_volume_quantile: 0.3
hold_mode: hold
"""
    p = tmp_path / "bad.yml"
    p.write_text(yaml_text.strip())
    with pytest.raises(ValueError, match="hold_mode='hold'"):
        validate_export_ema_regime_hold(p)
