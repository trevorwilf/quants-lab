"""Tests for pmm_lab.objective.holdout — holdout validation."""

import numpy as np
import pytest

from pmm_lab.objective.holdout import (
    split_holdout, evaluate_holdout,
    HoldoutReport, HoldoutCandidateResult,
)
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.config.params import PairRules, FeeConfig


def _make_config(**overrides):
    defaults = dict(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5],
        sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
    )
    defaults.update(overrides)
    return SimConfig(**defaults)


def _make_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )


# ── Split tests ──────────────────────────────────────────────


class TestSplitHoldoutDefault20pct:
    def test_split_holdout_default_20pct(self, sample_candles_500):
        dev, holdout = split_holdout(sample_candles_500, holdout_fraction=0.20)
        assert len(dev) == 400
        assert len(holdout) == 100


class TestSplitHoldoutCustomFraction:
    def test_split_holdout_custom_fraction(self, sample_candles_500):
        dev, holdout = split_holdout(sample_candles_500, holdout_fraction=0.30)
        assert len(dev) == 350
        assert len(holdout) == 150


class TestSplitHoldoutMinBars:
    def test_split_holdout_min_bars(self, sample_candles_500):
        # 20% of 500 = 100, but min_holdout_bars=200 → holdout = 200
        dev, holdout = split_holdout(sample_candles_500, holdout_fraction=0.20, min_holdout_bars=200)
        assert len(holdout) == 200
        assert len(dev) == 300


class TestSplitHoldoutInsufficientData:
    def test_split_holdout_insufficient_data(self):
        from tests.conftest import CANDLE_DTYPE
        tiny = np.zeros(50, dtype=CANDLE_DTYPE)
        with pytest.raises(ValueError, match="Holdout size"):
            split_holdout(tiny, holdout_fraction=0.20, min_holdout_bars=100)


class TestSplitHoldoutNoOverlap:
    def test_split_holdout_no_overlap(self, sample_candles_500):
        dev, holdout = split_holdout(sample_candles_500)
        assert dev["timestamp"][-1] < holdout["timestamp"][0]


class TestSplitHoldoutCoversAllData:
    def test_split_holdout_covers_all_data(self, sample_candles_500):
        dev, holdout = split_holdout(sample_candles_500)
        assert len(dev) + len(holdout) == len(sample_candles_500)


# ── Evaluation tests ─────────────────────────────────────────


class TestEvaluateHoldoutBasic:
    def test_evaluate_holdout_basic(self, sample_candles_500):
        dev, holdout = split_holdout(sample_candles_500)
        config = _make_config()
        rules = _make_rules()
        report = evaluate_holdout(
            holdout, [(config, 0.5)], rules, 300, run_stress=False,
        )
        assert isinstance(report, HoldoutReport)
        assert report.holdout_bars == len(holdout)
        assert len(report.candidates) == 1
        assert report.regime.label != "unknown"
        assert isinstance(report.best_holdout_score, float)
        assert isinstance(report.passed, bool)


class TestEvaluateHoldoutMultipleCandidates:
    def test_evaluate_holdout_multiple_candidates(self, sample_candles_500):
        dev, holdout = split_holdout(sample_candles_500)
        rules = _make_rules()
        configs = [
            (_make_config(buy_spreads=[0.5, 1.0], sell_spreads=[0.5, 1.0]), 0.3),
            (_make_config(buy_spreads=[1.0, 2.0], sell_spreads=[1.0, 2.0]), 0.5),
            (_make_config(buy_spreads=[2.0, 4.0], sell_spreads=[2.0, 4.0]), 0.2),
        ]
        report = evaluate_holdout(holdout, configs, rules, 300, run_stress=False)
        assert len(report.candidates) == 3
        ranks = [c.rank for c in report.candidates]
        assert sorted(ranks) == [0, 1, 2]


class TestEvaluateHoldoutCollapseDetected:
    def test_evaluate_holdout_collapse_detected(self, sample_candles_500):
        """Artificially high dev_score -> collapse when holdout score is much lower."""
        dev, holdout = split_holdout(sample_candles_500)
        config = _make_config()
        rules = _make_rules()
        # Set dev_score very high — holdout will almost certainly be much lower
        report = evaluate_holdout(
            holdout, [(config, 1000.0)], rules, 300, run_stress=False,
        )
        assert report.dev_vs_holdout_collapse is True


class TestEvaluateHoldoutRegimeClassified:
    def test_evaluate_holdout_regime_classified(self, sample_candles_500):
        dev, holdout = split_holdout(sample_candles_500)
        config = _make_config()
        rules = _make_rules()
        report = evaluate_holdout(
            holdout, [(config, 0.5)], rules, 300, run_stress=False,
        )
        assert report.regime.label != "unknown"
        assert report.regime.volatility in ("high_vol", "low_vol")
        assert report.regime.trend in ("trending", "ranging")


class TestEvaluateHoldoutStressOptional:
    def test_evaluate_holdout_stress_optional(self, sample_candles_500):
        dev, holdout = split_holdout(sample_candles_500)
        config = _make_config()
        rules = _make_rules()
        report = evaluate_holdout(
            holdout, [(config, 0.5)], rules, 300, run_stress=False,
        )
        for c in report.candidates:
            assert c.stress_report is None
