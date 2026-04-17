"""Tests for EMA regime-hold Optuna search space."""

import optuna
import pytest

from pmm_lab.optuna.search_space_ema_regime_hold import suggest_ema_regime_hold_params


EXPECTED_KEYS = {
    "regime_ema_fast", "regime_ema_slow", "regime_adx_length", "regime_adx_threshold",
    "volume_filter_window", "min_volume_quantile",
    "hold_mode", "max_executors_per_side",
    "cooldown_time", "stop_loss", "take_profit", "time_limit",
    "take_profit_order_type", "trailing_stop_activation", "trailing_stop_delta",
    "total_amount_quote",
}


class TestKeyPresence:
    def test_all_expected_keys(self):
        study = optuna.create_study()
        trial = study.ask()
        params = suggest_ema_regime_hold_params(trial)
        assert set(params.keys()) == EXPECTED_KEYS


class TestFixedValues:
    def test_hold_mode_always_reentry(self):
        """D4: 'hold' mode not supported; search space must always return 'reentry'."""
        study = optuna.create_study()
        for _ in range(20):
            trial = study.ask()
            params = suggest_ema_regime_hold_params(trial)
            assert params["hold_mode"] == "reentry"

    def test_max_executors_fixed(self):
        study = optuna.create_study()
        for _ in range(10):
            trial = study.ask()
            params = suggest_ema_regime_hold_params(trial)
            assert params["max_executors_per_side"] == 1


class TestFastLessThanSlow:
    def test_fast_lt_slow(self):
        study = optuna.create_study()
        for _ in range(30):
            trial = study.ask()
            params = suggest_ema_regime_hold_params(trial)
            assert params["regime_ema_fast"] < params["regime_ema_slow"]


class TestCooldownLowerBound:
    def test_default_signal_interval_300(self):
        study = optuna.create_study()
        for _ in range(30):
            trial = study.ask()
            params = suggest_ema_regime_hold_params(trial, signal_interval_seconds=300)
            assert params["cooldown_time"] >= 600


class TestFixedQuote:
    def test_fixed_quote_omits_sampling(self):
        study = optuna.create_study()
        trial = study.ask()
        params = suggest_ema_regime_hold_params(trial, fixed_quote=250.0)
        assert params["total_amount_quote"] == 250.0
