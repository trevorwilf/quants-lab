"""Tests for pmm_lab.optuna.sensitivity — parameter sensitivity analysis."""

import numpy as np
import pytest

from pmm_lab.optuna.sensitivity import (
    compute_sensitivity, SensitivityReport,
    _perturb_params, PERTURBABLE_PARAMS,
)


def _make_working_params():
    """A known working parameter set."""
    return {
        "macd_fast": 21,
        "macd_slow": 42,
        "macd_signal": 9,
        "natr_length": 14,
        "buy_n_levels": 2,
        "sell_n_levels": 2,
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
        "trailing_stop_activation": 0.0,
        "trailing_stop_delta": 0.001,
    }


class TestStableConfigLowPenalty:
    def test_stable_config_low_penalty(self, sample_candles_5m, default_pair_rules):
        params = _make_working_params()
        ref_price = float(np.median(sample_candles_5m["close"]))
        report = compute_sensitivity(
            params, sample_candles_5m, default_pair_rules, 300, ref_price,
        )
        assert isinstance(report, SensitivityReport)
        assert report.sensitivity_penalty < 0.5


class TestSensitivityReportHasAllFields:
    def test_sensitivity_report_has_all_fields(self, sample_candles_5m, default_pair_rules):
        params = _make_working_params()
        ref_price = float(np.median(sample_candles_5m["close"]))
        report = compute_sensitivity(
            params, sample_candles_5m, default_pair_rules, 300, ref_price,
        )
        assert isinstance(report.baseline_score, float)
        assert isinstance(report.perturbed_scores, dict)
        assert isinstance(report.sign_flips, int)
        assert isinstance(report.collapse_count, int)
        assert isinstance(report.sensitivity_penalty, float)
        assert isinstance(report.n_perturbations, int)
        assert isinstance(report.n_rejected, int)
        assert report.n_perturbations > 0


class TestPerturbParamsCreatesVariants:
    def test_perturb_params_creates_variants(self):
        params = {"buy_spread_base": 1.0, "stop_loss": 0.03}
        variants = _perturb_params(params, "buy_spread_base", delta_pct=0.10)
        assert len(variants) == 2
        # One should be higher, one lower
        vals = [v["buy_spread_base"] for v in variants]
        assert vals[0] > 1.0
        assert vals[1] < 1.0


class TestPerturbParamsIntAtLeastOne:
    def test_perturb_params_int_at_least_one(self):
        params = {"macd_fast": 5}
        variants = _perturb_params(params, "macd_fast", delta_pct=0.10)
        assert len(variants) == 2
        vals = [v["macd_fast"] for v in variants]
        # 10% of 5 = 0.5, rounds to 1
        assert vals[0] == 6  # +1
        assert vals[1] == 4  # -1


class TestRejectedBaselineMaxPenalty:
    def test_rejected_baseline_max_penalty(self, sample_candles_5m, default_pair_rules):
        # Params that will fail canonicalization (e.g., macd_fast > macd_slow)
        bad_params = _make_working_params()
        bad_params["macd_fast"] = 200
        bad_params["macd_slow"] = 10
        ref_price = float(np.median(sample_candles_5m["close"]))
        report = compute_sensitivity(
            bad_params, sample_candles_5m, default_pair_rules, 300, ref_price,
        )
        assert report.sensitivity_penalty == 1.0


class TestSensitivityDeterministic:
    def test_sensitivity_deterministic(self, sample_candles_5m, default_pair_rules):
        params = _make_working_params()
        ref_price = float(np.median(sample_candles_5m["close"]))
        r1 = compute_sensitivity(params, sample_candles_5m, default_pair_rules, 300, ref_price)
        r2 = compute_sensitivity(params, sample_candles_5m, default_pair_rules, 300, ref_price)
        assert r1.baseline_score == r2.baseline_score
        assert r1.sensitivity_penalty == r2.sensitivity_penalty
        assert r1.sign_flips == r2.sign_flips
        assert r1.collapse_count == r2.collapse_count


class TestCustomPerturbParams:
    def test_custom_perturb_params(self, sample_candles_5m, default_pair_rules):
        params = _make_working_params()
        ref_price = float(np.median(sample_candles_5m["close"]))
        custom = ["buy_spread_base", "stop_loss"]
        report = compute_sensitivity(
            params, sample_candles_5m, default_pair_rules, 300, ref_price,
            perturb_params=custom,
        )
        assert set(report.perturbed_scores.keys()) == set(custom)
        assert report.n_perturbations == 4  # 2 params x 2 variants each
