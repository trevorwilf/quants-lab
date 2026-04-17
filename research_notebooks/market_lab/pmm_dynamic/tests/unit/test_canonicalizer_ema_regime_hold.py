"""Tests for EMA regime-hold canonicalizer."""

import numpy as np
import pytest

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.optuna.candidate import CandidateBundle
from pmm_lab.optuna.canonicalizer_ema_regime_hold import (
    canonicalize_ema_regime_hold_params,
)
from tests.conftest import CANDLE_DTYPE


def _make_regime_candles(n=100):
    rng = np.random.default_rng(seed=101)
    start_ts = 1_700_000_000
    interval = 14400
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    rows = [(int(timestamps[i]), 100.0, 105.0, 95.0, 102.0, 1.5, False) for i in range(n)]
    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def pair_rules():
    return PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )


@pytest.fixture
def regime_candles():
    return _make_regime_candles()


@pytest.fixture
def valid_params():
    return {
        "regime_ema_fast": 50, "regime_ema_slow": 200,
        "regime_adx_length": 14, "regime_adx_threshold": 20.0,
        "volume_filter_window": 288, "min_volume_quantile": 0.30,
        "hold_mode": "reentry",
        "max_executors_per_side": 1,
        "cooldown_time": 3600,
        "stop_loss": 0.05, "take_profit": 0.03,
        "time_limit": 172800,
        "take_profit_order_type": "LIMIT",
        "trailing_stop_activation": 0.01, "trailing_stop_delta": 0.005,
        "total_amount_quote": 300.0,
    }


class TestHappyPath:
    def test_valid_params_produce_bundle(self, valid_params, pair_rules, regime_candles):
        bundle, reason = canonicalize_ema_regime_hold_params(
            valid_params, pair_rules, 340.0,
            signal_interval_seconds=300, regime_candles=regime_candles,
        )
        assert bundle is not None, reason

    def test_bundle_name_and_meta(self, valid_params, pair_rules, regime_candles):
        bundle, _ = canonicalize_ema_regime_hold_params(
            valid_params, pair_rules, 340.0,
            signal_interval_seconds=300, regime_candles=regime_candles,
        )
        assert bundle.strategy_name == "ema_regime_hold"
        assert bundle.export_meta == {
            "controller_name": "ema_regime_hold_v1",
            "controller_type": "directional_trading",
        }

    def test_regime_candles_wired_on_strategy_config(self, valid_params, pair_rules, regime_candles):
        bundle, _ = canonicalize_ema_regime_hold_params(
            valid_params, pair_rules, 340.0,
            signal_interval_seconds=300, regime_candles=regime_candles,
        )
        assert bundle.strategy_config._regime_candles is not None
        assert len(bundle.strategy_config._regime_candles) == len(regime_candles)

    def test_refresh_time_equals_signal_interval(self, valid_params, pair_rules, regime_candles):
        bundle, _ = canonicalize_ema_regime_hold_params(
            valid_params, pair_rules, 340.0,
            signal_interval_seconds=300, regime_candles=regime_candles,
        )
        assert bundle.engine_config.executor_refresh_time == 300.0


class TestD4:
    def test_hold_mode_rejected(self, valid_params, pair_rules, regime_candles):
        valid_params["hold_mode"] = "hold"
        bundle, reason = canonicalize_ema_regime_hold_params(
            valid_params, pair_rules, 340.0,
            signal_interval_seconds=300, regime_candles=regime_candles,
        )
        assert bundle is None
        assert "hold" in reason.lower()


class TestFastSlow:
    def test_fast_ge_slow_rejected(self, valid_params, pair_rules, regime_candles):
        valid_params["regime_ema_fast"] = 200
        valid_params["regime_ema_slow"] = 200
        bundle, reason = canonicalize_ema_regime_hold_params(
            valid_params, pair_rules, 340.0,
            signal_interval_seconds=300, regime_candles=regime_candles,
        )
        assert bundle is None
        assert "regime_ema_fast" in reason


class TestRegimeCandlesRequired:
    def test_none_regime_rejected(self, valid_params, pair_rules):
        bundle, reason = canonicalize_ema_regime_hold_params(
            valid_params, pair_rules, 340.0,
            signal_interval_seconds=300, regime_candles=None,
        )
        assert bundle is None
        assert "regime_candles" in reason


class TestD19SlowBuffer:
    def test_slow_ema_too_large_rejected(self, valid_params, pair_rules, regime_candles):
        valid_params["regime_ema_slow"] = 3000
        bundle, reason = canonicalize_ema_regime_hold_params(
            valid_params, pair_rules, 340.0,
            signal_interval_seconds=300, regime_candles=regime_candles,
        )
        assert bundle is None
        assert "slow" in reason.lower()

    def test_within_slow_buffer_accepted(self, valid_params, pair_rules, regime_candles):
        """200 + 50 = 250 < 2950 — accepted."""
        valid_params["regime_ema_slow"] = 200
        valid_params["regime_adx_length"] = 14
        bundle, _ = canonicalize_ema_regime_hold_params(
            valid_params, pair_rules, 340.0,
            signal_interval_seconds=300, regime_candles=regime_candles,
        )
        assert bundle is not None


class TestD19FastBuffer:
    def test_huge_volume_window_rejected(self, valid_params, pair_rules, regime_candles):
        valid_params["volume_filter_window"] = 6000
        bundle, reason = canonicalize_ema_regime_hold_params(
            valid_params, pair_rules, 340.0,
            signal_interval_seconds=300, regime_candles=regime_candles,
        )
        assert bundle is None
        assert "fast" in reason.lower() or "volume" in reason.lower()
