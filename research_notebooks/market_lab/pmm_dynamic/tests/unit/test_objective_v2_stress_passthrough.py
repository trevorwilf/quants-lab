"""Tests for v2 objective stress passthrough in the Optuna objective wrapper."""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from pmm_lab.objective.objective import ObjectiveWeights, ObjectiveWeightsV2
from pmm_lab.objective.stress import run_fold_local_stress, load_stress_scenarios


class TestV2StressPassthrough:
    """Verify that objective_version and weights propagate into fold-local stress."""

    def test_fold_local_stress_uses_v2_scoring(self, sample_candles_500, default_pair_rules):
        """v2 fold-local stress produces different scores than v1."""
        from pmm_lab.sim.executor_model import SimConfig

        config = SimConfig(
            buy_spreads=[1.0], sell_spreads=[1.0],
            buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
            total_amount_quote=100.0,
            controller_compat=False,
        )
        scenarios = load_stress_scenarios()

        scores_v1 = run_fold_local_stress(
            sample_candles_500, config, default_pair_rules, 300,
            fold_test_start_idx=200, fold_test_end_idx=350,
            scenarios=scenarios,
            objective_version=1,
            objective_weights=ObjectiveWeights(),
        )

        scores_v2 = run_fold_local_stress(
            sample_candles_500, config, default_pair_rules, 300,
            fold_test_start_idx=200, fold_test_end_idx=350,
            scenarios=scenarios,
            objective_version=2,
            objective_weights=ObjectiveWeightsV2(),
        )

        # Scores must exist and be different (v1 and v2 have different formulas)
        assert len(scores_v1) == len(scenarios)
        assert len(scores_v2) == len(scenarios)
        assert scores_v1 != scores_v2

    def test_fold_local_stress_v1_uses_v1_weights(self, sample_candles_500, default_pair_rules):
        """v1 fold-local stress uses ObjectiveWeights."""
        from pmm_lab.sim.executor_model import SimConfig

        config = SimConfig(
            buy_spreads=[1.0], sell_spreads=[1.0],
            buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
            controller_compat=False,
        )
        scenarios = load_stress_scenarios()

        # Default weights
        scores_default = run_fold_local_stress(
            sample_candles_500, config, default_pair_rules, 300,
            fold_test_start_idx=200, fold_test_end_idx=350,
            scenarios=scenarios, objective_version=1,
        )

        # Custom v1 weights with different emphasis
        custom_weights = ObjectiveWeights(w_pnl=5.0)
        scores_custom = run_fold_local_stress(
            sample_candles_500, config, default_pair_rules, 300,
            fold_test_start_idx=200, fold_test_end_idx=350,
            scenarios=scenarios, objective_version=1,
            objective_weights=custom_weights,
        )

        assert len(scores_default) == len(scenarios)
        assert len(scores_custom) == len(scenarios)
        # Custom weights should produce different scores
        assert scores_default != scores_custom

    def test_wrong_weight_type_raises_in_wrapper(self):
        """Passing ObjectiveWeights for v2 raises AssertionError in create_objective."""
        from pmm_lab.optuna.objective_wrapper import create_objective

        candles = np.zeros(100, dtype=[
            ("timestamp", "int64"), ("open", "float64"), ("high", "float64"),
            ("low", "float64"), ("close", "float64"), ("volume", "float64"),
            ("is_forward_fill", "bool"),
        ])

        from pmm_lab.config.params import PairRules, FeeConfig
        pair_rules = PairRules(
            price_tick=0.01, amount_step=0.00001, min_notional_quote=1.0,
            fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
        )

        with pytest.raises(AssertionError, match="ObjectiveWeightsV2"):
            create_objective(
                candles=candles,
                pair_rules=pair_rules,
                bar_interval_seconds=300,
                dataset_hash="test",
                reference_price=100.0,
                objective_version=2,
                objective_weights=ObjectiveWeights(),  # WRONG type for v2
            )

    def test_wrong_weight_type_v1_raises_in_wrapper(self):
        """Passing ObjectiveWeightsV2 for v1 raises AssertionError in create_objective."""
        from pmm_lab.optuna.objective_wrapper import create_objective

        candles = np.zeros(100, dtype=[
            ("timestamp", "int64"), ("open", "float64"), ("high", "float64"),
            ("low", "float64"), ("close", "float64"), ("volume", "float64"),
            ("is_forward_fill", "bool"),
        ])

        from pmm_lab.config.params import PairRules, FeeConfig
        pair_rules = PairRules(
            price_tick=0.01, amount_step=0.00001, min_notional_quote=1.0,
            fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
        )

        with pytest.raises(AssertionError, match="ObjectiveWeights"):
            create_objective(
                candles=candles,
                pair_rules=pair_rules,
                bar_interval_seconds=300,
                dataset_hash="test",
                reference_price=100.0,
                objective_version=1,
                objective_weights=ObjectiveWeightsV2(),  # WRONG type for v1
            )
