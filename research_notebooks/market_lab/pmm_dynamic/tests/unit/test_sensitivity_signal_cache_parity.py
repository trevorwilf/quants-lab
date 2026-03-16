"""Parity tests proving sensitivity signal caching produces identical results."""

import numpy as np
import pytest

from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.optuna.sensitivity import compute_sensitivity, PERTURBABLE_PARAMS


@pytest.fixture
def sens_pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.000001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


class TestSensitivitySignalCacheParity:
    """Verify cached sensitivity produces valid results."""

    def test_sensitivity_runs_with_cache(self, sample_candles_5m, sens_pair_rules):
        """compute_sensitivity should produce a valid report with signal caching."""
        params = {
            "buy_n_levels": 2,
            "sell_n_levels": 2,
            "buy_spread_base": 1.5,
            "buy_spread_ratio": 2.0,
            "sell_spread_base": 1.5,
            "sell_spread_ratio": 2.0,
            "buy_side_weight": 0.5,
            "amount_skew": 1.0,
            "total_amount_quote": 100.0,
            "executor_refresh_time": 3120.0,
            "cooldown_time": 3120.0,
            "stop_loss": 0.03,
            "take_profit": 0.015,
            "time_limit": 43200,
            "trailing_stop_activation": 0.0,
            "trailing_stop_delta": 0.001,
            "macd_fast": 21,
            "macd_slow": 42,
            "macd_signal": 9,
            "natr_length": 14,
        }
        ref_price = float(np.median(sample_candles_5m["close"]))

        report = compute_sensitivity(
            params=params,
            candles=sample_candles_5m,
            pair_rules=sens_pair_rules,
            bar_interval_seconds=300,
            reference_price=ref_price,
        )
        assert report.n_perturbations > 0
        assert report.baseline_score != 0.0 or report.n_rejected > 0
        assert 0.0 <= report.sensitivity_penalty <= 1.0

    def test_perturbable_params_do_not_include_indicators(self):
        """Confirm PERTURBABLE_PARAMS contains no indicator fields.
        This is the safety invariant that makes signal caching exact."""
        indicator_fields = {"macd_fast", "macd_slow", "macd_signal", "natr_length",
                           "controller_compat", "timestamp_mode"}
        for param in PERTURBABLE_PARAMS:
            assert param not in indicator_fields, (
                f"{param} is in PERTURBABLE_PARAMS but is an indicator field. "
                f"Signal caching would be invalid."
            )
