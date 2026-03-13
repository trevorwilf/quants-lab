"""Tests for pmm_lab.optuna.search_space — parameter suggestion."""

import optuna
import pytest

from pmm_lab.optuna.search_space import suggest_params

EXPECTED_KEYS = {
    "macd_fast", "macd_slow", "macd_signal", "natr_length",
    "buy_n_levels", "sell_n_levels",
    "buy_spread_base", "buy_spread_ratio", "sell_spread_base", "sell_spread_ratio",
    "buy_side_weight", "amount_skew", "total_amount_quote",
    "executor_refresh_time", "cooldown_time",
    "stop_loss", "take_profit", "time_limit",
    "trailing_stop_activation", "trailing_stop_delta",
}


def _make_fixed_params():
    """Complete parameter dict for FixedTrial."""
    return {
        "macd_fast": 21,
        "macd_slow": 42,
        "macd_signal": 9,
        "natr_length": 14,
        "buy_n_levels": 3,
        "sell_n_levels": 3,
        "buy_spread_base": 1.0,
        "buy_spread_ratio": 2.0,
        "sell_spread_base": 1.0,
        "sell_spread_ratio": 2.0,
        "buy_side_weight": 0.5,
        "amount_skew": 1.0,
        "total_amount_quote": 100.0,
        "executor_refresh_time": 3120.0,
        "cooldown_time": 3120.0,
        "stop_loss": 0.03,
        "take_profit": 0.015,
        "time_limit": 43200,
        "trailing_stop_activation": 0.01,
        "trailing_stop_delta": 0.005,
    }


class TestSuggestParams:
    def test_suggest_params_returns_all_keys(self):
        """FixedTrial with complete params → all expected keys returned."""
        trial = optuna.trial.FixedTrial(_make_fixed_params())
        result = suggest_params(trial)
        assert set(result.keys()) == EXPECTED_KEYS

    def test_macd_fast_and_slow_ranges(self):
        """macd_fast in [5, 50], macd_slow in [20, 100]. Constraint enforced in canonicalizer."""
        study = optuna.create_study(direction="maximize")
        for i in range(50):
            trial = study.ask()
            params = suggest_params(trial)
            assert 5 <= params["macd_fast"] <= 50
            assert 20 <= params["macd_slow"] <= 100
            study.tell(trial, 0.0)

    def test_spread_base_positive(self):
        """buy_spread_base > 0 and sell_spread_base > 0."""
        study = optuna.create_study(direction="maximize")
        for _ in range(20):
            trial = study.ask()
            params = suggest_params(trial)
            assert params["buy_spread_base"] > 0
            assert params["sell_spread_base"] > 0
            study.tell(trial, 0.0)

    def test_level_counts_in_range(self):
        """1 <= levels <= 10."""
        study = optuna.create_study(direction="maximize")
        for _ in range(20):
            trial = study.ask()
            params = suggest_params(trial)
            assert 1 <= params["buy_n_levels"] <= 10
            assert 1 <= params["sell_n_levels"] <= 10
            study.tell(trial, 0.0)

    def test_buy_side_weight_in_range(self):
        """0.2 <= buy_side_weight <= 0.8."""
        study = optuna.create_study(direction="maximize")
        for _ in range(20):
            trial = study.ask()
            params = suggest_params(trial)
            assert 0.2 <= params["buy_side_weight"] <= 0.8
            study.tell(trial, 0.0)

    def test_stop_loss_greater_than_zero(self):
        """stop_loss > 0."""
        study = optuna.create_study(direction="maximize")
        for _ in range(20):
            trial = study.ask()
            params = suggest_params(trial)
            assert params["stop_loss"] > 0
            study.tell(trial, 0.0)
