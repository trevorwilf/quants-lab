"""Tests for MACD-BB Optuna search space."""

import optuna
import pytest

from pmm_lab.optuna.search_space_macd_bb import suggest_macd_bb_params


EXPECTED_KEYS = {
    "bb_length", "bb_std", "bb_long_threshold", "bb_short_threshold",
    "macd_fast", "macd_slow", "macd_signal", "max_executors_per_side",
    "cooldown_time", "stop_loss", "take_profit", "time_limit",
    "take_profit_order_type", "trailing_stop_activation", "trailing_stop_delta",
    "total_amount_quote",
}


class TestSuggestParams:
    def test_all_expected_keys_present(self):
        study = optuna.create_study()
        trial = study.ask()
        params = suggest_macd_bb_params(trial)
        assert set(params.keys()) == EXPECTED_KEYS

    def test_macd_fast_less_than_slow(self):
        """macd_fast upper bound is capped at macd_slow - 1."""
        study = optuna.create_study()
        for _ in range(20):
            trial = study.ask()
            params = suggest_macd_bb_params(trial)
            assert params["macd_fast"] < params["macd_slow"]

    def test_fixed_quote(self):
        study = optuna.create_study()
        trial = study.ask()
        params = suggest_macd_bb_params(trial, fixed_quote=500.0)
        assert params["total_amount_quote"] == 500.0

    def test_parameter_bounds(self):
        study = optuna.create_study()
        for _ in range(10):
            trial = study.ask()
            params = suggest_macd_bb_params(trial)
            assert 10 <= params["bb_length"] <= 200
            assert 0.5 <= params["bb_std"] <= 3.0
            assert -0.5 <= params["bb_long_threshold"] <= 0.5
            assert 0.5 <= params["bb_short_threshold"] <= 1.5
            assert 5 <= params["macd_fast"] <= 49
            assert 20 <= params["macd_slow"] <= 200
            assert 5 <= params["macd_signal"] <= 30
            assert params["max_executors_per_side"] == 1
            assert 60 <= params["cooldown_time"] <= 14400
            assert 0.01 <= params["stop_loss"] <= 0.10
            assert 0.01 <= params["take_profit"] <= 0.15
            assert 3600 <= params["time_limit"] <= 259200
            assert params["take_profit_order_type"] in ("LIMIT", "MARKET")
            assert 0.0 <= params["trailing_stop_activation"] <= 0.05
            assert 0.0 <= params["trailing_stop_delta"] <= 0.03

    def test_no_executor_refresh_time(self):
        """Directional search space must not include executor_refresh_time."""
        study = optuna.create_study()
        trial = study.ask()
        params = suggest_macd_bb_params(trial)
        assert "executor_refresh_time" not in params, (
            "executor_refresh_time should not be in MACD-BB search space — "
            "it is always set to bar_interval_seconds by the canonicalizer"
        )
