"""Regression tests for determinism across code changes."""

import yaml
import numpy as np
import pytest

from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.metrics.metrics import compute_metrics
from pmm_lab.objective.objective import objective_v1
from pmm_lab.data.hashing import hash_candles
from pmm_lab.export.hb_yaml import export_yaml

# Golden values frozen from a known run
GOLDEN_HASH = "d275a72e19e3a8566f67619754f67ec9d395e529ef8da1367464cc07eac017e9"
GOLDEN_OBJECTIVE = -3.2686177585944725


@pytest.fixture
def fixed_config():
    return SimConfig(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5],
        sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
    )


@pytest.fixture
def fixed_pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


class TestDeterminismRegression:
    def test_known_fixture_known_objective(self, sample_candles_5m, fixed_config, fixed_pair_rules):
        """Known fixture + known config → golden objective score."""
        runner = CandleSimRunner(fixed_config, fixed_pair_rules)
        result = runner.run(sample_candles_5m)
        metrics = compute_metrics(result, 100.0, sample_candles_5m, 300)
        obj = objective_v1(metrics)
        assert abs(obj.raw_score - GOLDEN_OBJECTIVE) < 0.01, (
            f"Objective drifted: expected {GOLDEN_OBJECTIVE}, got {obj.raw_score}"
        )

    def test_dataset_hash_stable(self, sample_candles_5m):
        """Hash of sample_candles_5m matches frozen golden hash."""
        h = hash_candles(sample_candles_5m)
        assert h == GOLDEN_HASH, f"Hash drifted: expected {GOLDEN_HASH}, got {h}"

    def test_export_roundtrip(self, tmp_path, fixed_config):
        """Export SimConfig to YAML, load back, verify key values."""
        path = str(tmp_path / "roundtrip.yml")
        export_yaml(fixed_config, path)

        with open(path) as f:
            loaded = yaml.safe_load(f)

        assert loaded["buy_spreads"] == list(fixed_config.buy_spreads)
        assert loaded["sell_spreads"] == list(fixed_config.sell_spreads)
        assert loaded["total_amount_quote"] == fixed_config.total_amount_quote
        assert loaded["macd_fast"] == fixed_config.macd_fast
        assert loaded["macd_slow"] == fixed_config.macd_slow
        assert loaded["stop_loss"] == fixed_config.stop_loss
        assert loaded["take_profit"] == fixed_config.take_profit
        assert loaded["controller_name"] == "pmm_dynamic"
