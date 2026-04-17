"""Tests for MR BB+RSI canonicalizer."""

import pytest

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.optuna.candidate import CandidateBundle
from pmm_lab.optuna.canonicalizer_mean_reversion_bb_rsi import (
    canonicalize_mr_bb_rsi_params,
)


@pytest.fixture
def pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.001,
        min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )


@pytest.fixture
def valid_params():
    return {
        "bb_length": 80, "bb_std": 2.0, "bbp_entry_threshold": 0.20,
        "rsi_length": 14, "rsi_entry_threshold": 40.0,
        "use_trend_filter": True, "trend_ema_length": 200, "min_trend_slope": 0.0,
        "atr_length": 14, "max_atr_pct_for_entry": 0.10,
        "volume_filter_window": 288, "min_volume_quantile": 0.30,
        "max_spread_pct": 0.006, "max_trades_per_day": 6,
        "max_executors_per_side": 1,
        "cooldown_time": 3600,
        "stop_loss": 0.04, "take_profit": 0.03,
        "time_limit": 86400,
        "take_profit_order_type": "LIMIT",
        "trailing_stop_activation": 0.01, "trailing_stop_delta": 0.005,
        "total_amount_quote": 300.0,
    }


class TestHappyPath:
    def test_valid_params_produce_bundle(self, valid_params, pair_rules):
        bundle, reason = canonicalize_mr_bb_rsi_params(valid_params, pair_rules, 340.0)
        assert bundle is not None, reason
        assert isinstance(bundle, CandidateBundle)

    def test_bundle_strategy_name(self, valid_params, pair_rules):
        bundle, _ = canonicalize_mr_bb_rsi_params(valid_params, pair_rules, 340.0)
        assert bundle.strategy_name == "mean_reversion_bb_rsi"

    def test_bundle_export_meta(self, valid_params, pair_rules):
        bundle, _ = canonicalize_mr_bb_rsi_params(valid_params, pair_rules, 340.0)
        assert bundle.export_meta == {
            "controller_name": "mean_reversion_bb_rsi_v1",
            "controller_type": "directional_trading",
        }

    def test_engine_refresh_equals_bar_interval(self, valid_params, pair_rules):
        bundle, _ = canonicalize_mr_bb_rsi_params(valid_params, pair_rules, 340.0, bar_interval_seconds=300)
        assert bundle.engine_config.executor_refresh_time == 300.0

    def test_engine_latency_is_1(self, valid_params, pair_rules):
        bundle, _ = canonicalize_mr_bb_rsi_params(valid_params, pair_rules, 340.0)
        assert bundle.engine_config.latency_bars == 1


class TestTrailingStop:
    def test_zero_activation_forces_zero_delta(self, valid_params, pair_rules):
        valid_params["trailing_stop_activation"] = 0.0
        valid_params["trailing_stop_delta"] = 0.02
        bundle, _ = canonicalize_mr_bb_rsi_params(valid_params, pair_rules, 340.0)
        assert bundle.engine_config.trailing_stop_delta == 0.0

    def test_delta_clamped_below_activation(self, valid_params, pair_rules):
        valid_params["trailing_stop_activation"] = 0.02
        valid_params["trailing_stop_delta"] = 0.05
        bundle, _ = canonicalize_mr_bb_rsi_params(valid_params, pair_rules, 340.0)
        assert bundle.engine_config.trailing_stop_delta < bundle.engine_config.trailing_stop_activation


class TestD17:
    def test_nonzero_min_slope_clamped(self, valid_params, pair_rules):
        """D17: raw min_trend_slope != 0 is clamped to 0.0, not rejected."""
        valid_params["min_trend_slope"] = 0.001
        bundle, reason = canonicalize_mr_bb_rsi_params(valid_params, pair_rules, 340.0)
        assert bundle is not None, reason
        assert bundle.strategy_config.min_trend_slope == 0.0


class TestD18:
    def test_volume_window_exceeds_buffer_rejected(self, valid_params, pair_rules):
        """D18: vfw=576 with short indicator buffer — reject."""
        valid_params["volume_filter_window"] = 576
        valid_params["bb_length"] = 20
        valid_params["trend_ema_length"] = 50
        valid_params["rsi_length"] = 14
        valid_params["atr_length"] = 14
        # required_records = max(50, 20, 14, 14) + 500 = 550
        # 576 + 50 = 626 > 550 -> reject
        bundle, reason = canonicalize_mr_bb_rsi_params(valid_params, pair_rules, 340.0)
        assert bundle is None
        assert "volume_filter_window" in reason

    def test_volume_window_within_buffer_accepted(self, valid_params, pair_rules):
        """Same vfw but longer trend EMA moves required_records up."""
        valid_params["volume_filter_window"] = 576
        valid_params["bb_length"] = 20
        valid_params["trend_ema_length"] = 200
        valid_params["rsi_length"] = 14
        valid_params["atr_length"] = 14
        # required = max(200, 20, 14, 14) + 500 = 700 ; 576 + 50 = 626 < 700
        bundle, reason = canonicalize_mr_bb_rsi_params(valid_params, pair_rules, 340.0)
        assert bundle is not None, reason


class TestD3:
    def test_max_trades_per_day_threaded_through(self, valid_params, pair_rules):
        bundle, _ = canonicalize_mr_bb_rsi_params(valid_params, pair_rules, 340.0)
        assert bundle.strategy_config.max_trades_per_day == 6


class TestMinNotional:
    def test_tiny_capital_rejected(self, valid_params):
        valid_params["total_amount_quote"] = 0.001
        high_min = PairRules(
            price_tick=0.01, amount_step=0.001,
            min_notional_quote=10.0,
            fees=FeeConfig(0.001, 0.002),
        )
        bundle, reason = canonicalize_mr_bb_rsi_params(valid_params, high_min, 340.0)
        assert bundle is None
        assert "notional" in reason.lower()
