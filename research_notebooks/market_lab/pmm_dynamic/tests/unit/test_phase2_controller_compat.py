"""Tests for explicit Phase 2 controller_compat wiring."""

from dataclasses import replace

from pmm_lab.optuna.canonicalizer import canonicalize_params
from pmm_lab.sim.executor_model import SimConfig


def test_canonicalizer_does_not_set_controller_compat():
    """canonicalize_params returns config with SimConfig default controller_compat=True.

    The canonicalizer must NOT override controller_compat — the caller is
    responsible for setting it via dataclasses.replace() so that Phase 1,
    Phase 2, and validation can each use their own setting.
    """
    from pmm_lab.config.params import PairRules, FeeConfig
    pair_rules = PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=5.0,
        fees=FeeConfig(0.001, 0.002),
    )
    # Minimal valid params matching the search space format
    raw_params = {
        "macd_fast": 21,
        "macd_slow": 42,
        "macd_signal": 9,
        "natr_length": 14,
        "buy_n_levels": 3,
        "sell_n_levels": 3,
        "buy_spread_base": 1.0,
        "buy_spread_ratio": 1.5,
        "sell_spread_base": 1.0,
        "sell_spread_ratio": 1.5,
        "buy_side_weight": 0.5,
        "amount_skew": 0.0,
        "stop_loss": 0.03,
        "take_profit": 0.02,
        "time_limit": 3600,
        "trailing_stop_activation": 0.015,
        "trailing_stop_delta": 0.005,
        "total_amount_quote": 100.0,
        "executor_refresh_time": 120,
        "cooldown_time": 60,
        "take_profit_order_type": "LIMIT",
    }
    config, reject_reason = canonicalize_params(raw_params, pair_rules, reference_price=100.0)
    if config is not None:
        # The key assertion: canonicalizer produces the SimConfig default
        assert config.controller_compat is True


def test_phase2_explicit_override():
    """Applying replace(config, controller_compat=X) must change the field."""
    base = SimConfig(
        buy_spreads=[1.0], sell_spreads=[1.0],
        buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
    )
    assert base.controller_compat is True  # default
    overridden = replace(base, controller_compat=False)
    assert overridden.controller_compat is False
