"""Integration tests — full pipeline: candles → features → sim → metrics → objective."""

import numpy as np
import pytest

from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.metrics.metrics import compute_metrics
from pmm_lab.objective.objective import objective_v1
from pmm_lab.objective.walkforward import run_walk_forward
from pmm_lab.objective.stress import run_stress_tests, load_stress_scenarios
from pmm_lab.data.hashing import hash_candles

CANDLE_DTYPE = np.dtype([
    ("timestamp", "int64"),
    ("open", "float64"),
    ("high", "float64"),
    ("low", "float64"),
    ("close", "float64"),
    ("volume", "float64"),
    ("is_forward_fill", "bool"),
])


def _make_candles(n: int, seed: int = 42) -> np.ndarray:
    """Create n-bar candle array with random walks."""
    rng = np.random.default_rng(seed=seed)
    start_ts = 1756833000
    interval = 300
    price = 100000.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 50)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 20))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 20))
        open_p = max(open_p, 1.0)
        close_p = max(close_p, 1.0)
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = rng.uniform(0.05, 2.0)
        rows.append((start_ts + i * interval, open_p, high_p, low_p, close_p, vol, False))
        price = close_p
    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def default_config():
    return SimConfig(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5],
        sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
    )


@pytest.fixture
def default_pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


class TestFullPipeline:
    def test_full_pipeline_deterministic(self, default_config, default_pair_rules):
        """Run full pipeline twice → identical Metrics and objective decomposition."""
        candles = _make_candles(100)

        results = []
        for _ in range(2):
            runner = CandleSimRunner(default_config, default_pair_rules)
            sim_result = runner.run(candles)
            metrics = compute_metrics(sim_result, 100.0, candles, 300)
            obj = objective_v1(metrics)
            results.append((metrics, obj))

        m1, o1 = results[0]
        m2, o2 = results[1]

        # Metrics must be identical
        assert m1.pnl_pct == m2.pnl_pct
        assert m1.sharpe == m2.sharpe
        assert m1.max_drawdown_pct == m2.max_drawdown_pct
        assert m1.trade_count == m2.trade_count
        assert m1.profit_factor == m2.profit_factor

        # Objective must be identical
        assert o1.raw_score == o2.raw_score
        assert o1.pnl_component == o2.pnl_component
        assert o1.sharpe_component == o2.sharpe_component

    def test_walk_forward_on_sample(self, default_config, default_pair_rules):
        """Walk-forward on 1500 bars → >= 2 folds, finite aggregate_score."""
        candles = _make_candles(1500)
        dataset_hash = hash_candles(candles)

        result = run_walk_forward(
            candles, default_config, default_pair_rules, 300, dataset_hash,
            train_days=1.0, test_days=0.5, step_days=0.5, embargo_bars=10,
        )

        assert len(result.folds) >= 2
        assert np.isfinite(result.aggregate_score)

    def test_stress_on_sample(self, default_config, default_pair_rules):
        """Stress tests on 100-bar sample → StressReport with baseline + scenarios."""
        candles = _make_candles(100)

        report = run_stress_tests(
            candles, default_config, default_pair_rules, 300,
        )

        assert report.baseline_metrics is not None
        assert report.baseline_objective is not None
        assert len(report.scenario_results) >= 10

        # At least some scenarios should produce different scores
        baseline_score = report.baseline_objective.raw_score
        different = sum(
            1 for sr in report.scenario_results
            if sr.objective.raw_score != baseline_score
        )
        assert different > 0
