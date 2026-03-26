"""Verify export contract consistency with data dictionary."""
from pmm_lab.export.hb_yaml import sim_config_to_hb_dict, ExportParams
from pmm_lab.sim.executor_model import SimConfig


# Fields that the lab exports for pmm_dynamic
EXPORTED_FIELDS = {
    "buy_amounts_pct", "buy_spreads",
    "candles_connector", "candles_trading_pair", "connector_name",
    "controller_name", "controller_type", "cooldown_time",
    "executor_refresh_time", "id", "interval", "leverage",
    "macd_fast", "macd_signal", "macd_slow", "manual_kill_switch",
    "natr_length", "position_mode", "position_rebalance_threshold_pct",
    "sell_amounts_pct", "sell_spreads", "skip_rebalance",
    "stop_loss", "take_profit", "take_profit_order_type",
    "time_limit", "total_amount_quote", "trading_pair", "trailing_stop",
}

# Fields documented in data dictionary but intentionally NOT exported
NOT_EXPORTED_BY_DESIGN = {
    "rebalance_cooldown_time",  # base-class runtime default
    "use_wallet_balance",       # base-class runtime default
    "initial_positions",        # optional, not optimized
}


def test_exported_fields_match_expected():
    """Verify the set of exported fields hasn't drifted."""
    config = SimConfig(
        buy_spreads=[1.0], sell_spreads=[1.0],
        buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
    )
    d = sim_config_to_hb_dict(config)
    actual_fields = set(d.keys())
    assert actual_fields == EXPORTED_FIELDS, (
        f"Missing: {EXPORTED_FIELDS - actual_fields}, "
        f"Extra: {actual_fields - EXPORTED_FIELDS}"
    )


def test_not_exported_fields_absent():
    """Fields intentionally not exported must not appear in output."""
    config = SimConfig(
        buy_spreads=[1.0], sell_spreads=[1.0],
        buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
    )
    d = sim_config_to_hb_dict(config)
    for field in NOT_EXPORTED_BY_DESIGN:
        assert field not in d, f"Field '{field}' should not be exported but was found"
