"""Tests for MR BB+RSI Optuna search space."""

import optuna
import pytest

from pmm_lab.optuna.search_space_mean_reversion_bb_rsi import suggest_mr_bb_rsi_params


EXPECTED_KEYS = {
    "bb_length", "bb_std", "bbp_entry_threshold",
    "rsi_length", "rsi_entry_threshold",
    "use_trend_filter", "trend_ema_length", "min_trend_slope",
    "atr_length", "max_atr_pct_for_entry",
    "volume_filter_window", "min_volume_quantile",
    "max_spread_pct", "max_trades_per_day", "max_executors_per_side",
    "cooldown_time", "stop_loss", "take_profit", "time_limit",
    "take_profit_order_type", "trailing_stop_activation", "trailing_stop_delta",
    "total_amount_quote",
}


class TestKeyPresence:
    def test_all_expected_keys(self):
        study = optuna.create_study()
        trial = study.ask()
        params = suggest_mr_bb_rsi_params(trial, bar_interval_seconds=300)
        assert set(params.keys()) == EXPECTED_KEYS

    def test_no_executor_refresh_time_sampled(self):
        study = optuna.create_study()
        trial = study.ask()
        params = suggest_mr_bb_rsi_params(trial, bar_interval_seconds=300)
        assert "executor_refresh_time" not in params


class TestFixedValues:
    def test_min_trend_slope_fixed_at_zero(self):
        """D17: min_trend_slope must NOT be sampled."""
        study = optuna.create_study()
        for _ in range(10):
            trial = study.ask()
            params = suggest_mr_bb_rsi_params(trial, bar_interval_seconds=300)
            assert params["min_trend_slope"] == 0.0

    def test_max_trades_per_day_fixed_at_6(self):
        """D3: max_trades_per_day is a live-safety cap, not tuned."""
        study = optuna.create_study()
        for _ in range(10):
            trial = study.ask()
            params = suggest_mr_bb_rsi_params(trial, bar_interval_seconds=300)
            assert params["max_trades_per_day"] == 6

    def test_max_spread_pct_fixed(self):
        study = optuna.create_study()
        for _ in range(10):
            trial = study.ask()
            params = suggest_mr_bb_rsi_params(trial, bar_interval_seconds=300)
            assert params["max_spread_pct"] == 0.006

    def test_max_executors_per_side_fixed_at_1(self):
        study = optuna.create_study()
        for _ in range(10):
            trial = study.ask()
            params = suggest_mr_bb_rsi_params(trial, bar_interval_seconds=300)
            assert params["max_executors_per_side"] == 1


class TestCooldownLowerBound:
    def test_cooldown_respects_bar_interval_5m(self):
        study = optuna.create_study()
        for _ in range(50):
            trial = study.ask()
            params = suggest_mr_bb_rsi_params(trial, bar_interval_seconds=300)
            # 2 × 300 = 600, floor 300 so lower is 600
            assert params["cooldown_time"] >= 600

    def test_cooldown_respects_bar_interval_1h(self):
        study = optuna.create_study()
        for _ in range(20):
            trial = study.ask()
            params = suggest_mr_bb_rsi_params(trial, bar_interval_seconds=3600)
            assert params["cooldown_time"] >= 7200  # 2 * 3600


class TestFixedQuote:
    def test_fixed_quote_omits_sampling(self):
        study = optuna.create_study()
        trial = study.ask()
        params = suggest_mr_bb_rsi_params(trial, fixed_quote=500.0, bar_interval_seconds=300)
        assert params["total_amount_quote"] == 500.0


class TestParameterBounds:
    def test_bounds(self):
        study = optuna.create_study()
        for _ in range(30):
            trial = study.ask()
            p = suggest_mr_bb_rsi_params(trial, bar_interval_seconds=300)
            assert 20 <= p["bb_length"] <= 200
            assert 1.0 <= p["bb_std"] <= 3.0
            assert 0.05 <= p["bbp_entry_threshold"] <= 0.40
            assert 7 <= p["rsi_length"] <= 30
            assert 20.0 <= p["rsi_entry_threshold"] <= 50.0
            assert isinstance(p["use_trend_filter"], bool)
            assert 50 <= p["trend_ema_length"] <= 400
            assert 7 <= p["atr_length"] <= 30
            assert 0.005 <= p["max_atr_pct_for_entry"] <= 0.10
            assert 48 <= p["volume_filter_window"] <= 576
            assert 0.0 <= p["min_volume_quantile"] <= 0.6
            assert 0.015 <= p["stop_loss"] <= 0.08
            assert 0.005 <= p["take_profit"] <= 0.06
            assert 3600 <= p["time_limit"] <= 345600
            assert p["take_profit_order_type"] in ("LIMIT", "MARKET")
            assert 0.0 <= p["trailing_stop_activation"] <= 0.04
            assert 0.0 <= p["trailing_stop_delta"] <= 0.02
