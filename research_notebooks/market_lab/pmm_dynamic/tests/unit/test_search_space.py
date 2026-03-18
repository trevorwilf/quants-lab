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

    def test_fixed_quote_not_suggested(self):
        """When fixed_quote=100.0, total_amount_quote is NOT a trial param but IS in returned dict."""
        trial = optuna.trial.FixedTrial(_make_fixed_params())
        params = suggest_params(trial, fixed_quote=100.0)
        assert params["total_amount_quote"] == 100.0
        assert set(params.keys()) == EXPECTED_KEYS

    def test_fixed_quote_none_suggests_total(self):
        """When fixed_quote=None, total_amount_quote IS suggested (backward compat)."""
        trial = optuna.trial.FixedTrial(_make_fixed_params())
        params = suggest_params(trial, fixed_quote=None)
        assert "total_amount_quote" in params
        assert params["total_amount_quote"] == 100.0  # from FixedTrial

    def test_log_scaled_params_explore_small_values(self):
        """Run 100 trials, verify spread_base includes values < 1.0."""
        study = optuna.create_study(direction="maximize")
        spread_values = []
        for _ in range(100):
            trial = study.ask()
            params = suggest_params(trial)
            spread_values.append(params["buy_spread_base"])
            study.tell(trial, 0.0)
        # Log-uniform should explore small values (< 1.0) more than linear
        small_count = sum(1 for v in spread_values if v < 1.0)
        assert small_count > 0, "Log-scaled spread_base should include values < 1.0"

    def test_macd_fast_always_less_than_slow(self):
        """Search space must never produce macd_fast >= macd_slow."""
        study = optuna.create_study(direction="maximize")

        violations = 0
        n_samples = 200
        for _ in range(n_samples):
            trial = study.ask()
            params = suggest_params(trial)
            if params["macd_fast"] >= params["macd_slow"]:
                violations += 1
            study.tell(trial, 0.0)

        assert violations == 0, (
            f"{violations}/{n_samples} samples had macd_fast >= macd_slow"
        )

    def test_log_scaled_stop_loss_range(self):
        """Verify stop_loss can be both small and large values."""
        study = optuna.create_study(direction="maximize")
        stop_losses = []
        for _ in range(100):
            trial = study.ask()
            params = suggest_params(trial)
            stop_losses.append(params["stop_loss"])
            study.tell(trial, 0.0)
        assert min(stop_losses) < 0.05, "Should have small stop_loss values"
        assert max(stop_losses) > 0.05, "Should have larger stop_loss values"
