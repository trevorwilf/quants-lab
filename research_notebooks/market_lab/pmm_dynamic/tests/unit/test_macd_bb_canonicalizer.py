"""Tests for MACD-BB parameter canonicalization."""

import pytest

from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.optuna.canonicalizer_macd_bb import canonicalize_macd_bb_params
from pmm_lab.optuna.candidate import CandidateBundle


@pytest.fixture
def pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


@pytest.fixture
def valid_params():
    return {
        "bb_length": 100,
        "bb_std": 2.0,
        "bb_long_threshold": 0.0,
        "bb_short_threshold": 1.0,
        "macd_fast": 21,
        "macd_slow": 42,
        "macd_signal": 9,
        "max_executors_per_side": 1,
        "cooldown_time": 300,
        "stop_loss": 0.03,
        "take_profit": 0.02,
        "time_limit": 43200,
        "take_profit_order_type": "LIMIT",
        "trailing_stop_activation": 0.01,
        "trailing_stop_delta": 0.005,
        "total_amount_quote": 100.0,
    }


class TestValidParams:
    def test_valid_params_produce_bundle(self, valid_params, pair_rules):
        bundle, reason = canonicalize_macd_bb_params(valid_params, pair_rules, 100000.0)
        assert bundle is not None
        assert reason is None
        assert isinstance(bundle, CandidateBundle)

    def test_bundle_strategy_name(self, valid_params, pair_rules):
        bundle, _ = canonicalize_macd_bb_params(valid_params, pair_rules, 100000.0)
        assert bundle.strategy_name == "macd_bb"

    def test_bundle_export_meta(self, valid_params, pair_rules):
        bundle, _ = canonicalize_macd_bb_params(valid_params, pair_rules, 100000.0)
        assert bundle.export_meta["controller_name"] == "macd_bb_v1"
        assert bundle.export_meta["controller_type"] == "directional_trading"


class TestHardConstraints:
    def test_macd_fast_ge_slow_rejected(self, valid_params, pair_rules):
        valid_params["macd_fast"] = 50
        valid_params["macd_slow"] = 42
        bundle, reason = canonicalize_macd_bb_params(valid_params, pair_rules, 100000.0)
        assert bundle is None
        assert "macd_fast" in reason

    def test_bb_threshold_order_rejected(self, valid_params, pair_rules):
        valid_params["bb_long_threshold"] = 1.0
        valid_params["bb_short_threshold"] = 0.5
        bundle, reason = canonicalize_macd_bb_params(valid_params, pair_rules, 100000.0)
        assert bundle is None
        assert "bb_long_threshold" in reason


class TestTrailingStopConstraints:
    def test_zero_activation_forces_zero_delta(self, valid_params, pair_rules):
        valid_params["trailing_stop_activation"] = 0.0
        valid_params["trailing_stop_delta"] = 0.01
        bundle, _ = canonicalize_macd_bb_params(valid_params, pair_rules, 100000.0)
        assert bundle.engine_config.trailing_stop_delta == 0.0

    def test_delta_capped_below_activation(self, valid_params, pair_rules):
        valid_params["trailing_stop_activation"] = 0.02
        valid_params["trailing_stop_delta"] = 0.03  # exceeds activation
        bundle, _ = canonicalize_macd_bb_params(valid_params, pair_rules, 100000.0)
        assert bundle.engine_config.trailing_stop_delta < bundle.engine_config.trailing_stop_activation


class TestRefreshTime:
    def test_canonicalizer_sets_refresh_to_bar_interval(self, valid_params, pair_rules):
        """executor_refresh_time must equal bar_interval_seconds for directional."""
        # 5m bars (300s)
        bundle, _ = canonicalize_macd_bb_params(
            valid_params, pair_rules, 100000.0, bar_interval_seconds=300,
        )
        assert bundle is not None
        assert bundle.engine_config.executor_refresh_time == 300.0

    def test_refresh_time_1m_bars(self, valid_params, pair_rules):
        bundle, _ = canonicalize_macd_bb_params(
            valid_params, pair_rules, 100000.0, bar_interval_seconds=60,
        )
        assert bundle is not None
        assert bundle.engine_config.executor_refresh_time == 60.0

    def test_refresh_time_1h_bars(self, valid_params, pair_rules):
        bundle, _ = canonicalize_macd_bb_params(
            valid_params, pair_rules, 100000.0, bar_interval_seconds=3600,
        )
        assert bundle is not None
        assert bundle.engine_config.executor_refresh_time == 3600.0

    def test_default_bar_interval(self, valid_params, pair_rules):
        """Default bar_interval_seconds=300 should set refresh to 300."""
        bundle, _ = canonicalize_macd_bb_params(valid_params, pair_rules, 100000.0)
        assert bundle.engine_config.executor_refresh_time == 300.0


class TestMinNotional:
    def test_tiny_capital_rejected(self, pair_rules):
        params = {
            "bb_length": 20, "bb_std": 2.0,
            "bb_long_threshold": 0.0, "bb_short_threshold": 1.0,
            "macd_fast": 12, "macd_slow": 26, "macd_signal": 9,
            "max_executors_per_side": 1,
            "cooldown_time": 300,
            "stop_loss": 0.03, "take_profit": 0.02,
            "time_limit": 43200,
            "take_profit_order_type": "LIMIT",
            "trailing_stop_activation": 0.0, "trailing_stop_delta": 0.0,
            "total_amount_quote": 0.001,  # way too small
        }
        high_min = PairRules(
            price_tick=0.01, amount_step=0.00001,
            min_notional_quote=10.0,
            fees=FeeConfig(0.001, 0.002),
        )
        bundle, reason = canonicalize_macd_bb_params(params, high_min, 100000.0)
        assert bundle is None
        assert "notional" in reason.lower()
