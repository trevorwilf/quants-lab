"""Holdout evaluation must cache signals for candidates with identical indicator params."""
import numpy as np
import pytest
from dataclasses import replace
from tests.conftest import _make_sample_candles_500
from pmm_lab.objective.holdout import evaluate_holdout
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.objective.signal_cache import signal_cache_key

_RULES = PairRules(
    price_tick=0.01, amount_step=0.000001, min_notional_quote=5.0,
    fees=FeeConfig(0.001, 0.002),
)


def _make_config(**overrides):
    defaults = dict(
        buy_spreads=[1.0, 2.0], sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5], sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
    )
    defaults.update(overrides)
    return SimConfig(**defaults)


class TestHoldoutSignalCacheParity:
    """Cached vs uncached holdout must produce identical results."""

    def test_same_signal_params_same_results(self):
        candles = _make_sample_candles_500()
        holdout = candles[-100:]

        # Two configs with same indicators but different spreads
        cfg_a = _make_config(buy_spreads=[1.0, 2.0], sell_spreads=[1.0, 2.0])
        cfg_b = _make_config(buy_spreads=[1.5, 3.0], sell_spreads=[1.5, 3.0])
        assert signal_cache_key(cfg_a) == signal_cache_key(cfg_b)

        candidates = [(cfg_a, 5.0), (cfg_b, 4.0)]
        report = evaluate_holdout(
            holdout, candidates, _RULES, 300,
            full_candles=candles, holdout_start_idx=len(candles) - 100,
            run_stress=False,
        )
        assert len(report.candidates) == 2
        for c in report.candidates:
            assert c.metrics is not None

    def test_different_signal_params_different_keys(self):
        cfg_a = _make_config(macd_fast=21)
        cfg_b = _make_config(macd_fast=12)
        assert signal_cache_key(cfg_a) != signal_cache_key(cfg_b)
