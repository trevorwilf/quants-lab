"""End-to-end acceptance tests for the full v2 pipeline."""

import os
import numpy as np
import pytest

from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.sim.generic_runner import GenericSimRunner
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.engine import SimEngine
from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.metrics.metrics import compute_metrics
from pmm_lab.objective.objective import objective_v1, objective_v2, REJECT_SCORE
from pmm_lab.objective.walkforward import run_walk_forward
from pmm_lab.objective.stress import run_stress_tests
from pmm_lab.objective.holdout import split_holdout, evaluate_holdout
from pmm_lab.features.regime import classify_regime
from pmm_lab.report.report_md import generate_report, run_stop_ship_checks
from pmm_lab.strategies.bollinger import BollingerStrategy, BollingerStrategyConfig
from pmm_lab.data.hashing import hash_candles
from pmm_lab.data.candles import validate_candles


def _default_config():
    return SimConfig(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5],
        sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
    )


def _default_rules():
    return PairRules(
        price_tick=0.01, amount_step=0.00001, min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )


class TestFullPipelineV1Objective:
    def test_full_pipeline_v1_objective(self, sample_candles_500, default_pair_rules):
        config = _default_config()
        runner = CandleSimRunner(config, default_pair_rules)
        result = runner.run(sample_candles_500)
        metrics = compute_metrics(result, 100.0, sample_candles_500, 300)
        obj = objective_v1(metrics)

        # Walk-forward
        dataset_hash_val = hash_candles(sample_candles_500)
        wf = run_walk_forward(
            sample_candles_500, config, default_pair_rules, 300,
            dataset_hash=dataset_hash_val,
            train_days=0.5, test_days=0.25, step_days=0.25,
        )

        # Stress
        stress = run_stress_tests(sample_candles_500, config, default_pair_rules, 300)

        # Report
        report = generate_report(
            study_name="acceptance_v1",
            dataset_summary={"bars": 500, "pair": "BTC-USDT"},
            best_params={"buy_spread_base": 1.0},
            best_metrics=metrics,
            best_objective=obj,
            walkforward_result=wf,
            stress_report=stress,
        )
        assert "acceptance_v1" in report
        assert "Walk-Forward" in report
        assert "Stress Test" in report
        assert "Best Metrics" in report


class TestFullPipelineV2Objective:
    def test_full_pipeline_v2_objective(self, sample_candles_500, default_pair_rules):
        config = _default_config()
        runner = CandleSimRunner(config, default_pair_rules)
        result = runner.run(sample_candles_500)
        metrics = compute_metrics(result, 100.0, sample_candles_500, 300)
        obj = objective_v2(metrics)

        # Holdout
        dev, holdout = split_holdout(sample_candles_500, holdout_fraction=0.20)
        holdout_report = evaluate_holdout(
            holdout, [(config, obj.raw_score)], default_pair_rules, 300,
            run_stress=False, objective_version=2,
        )

        # Regime
        regime = classify_regime(sample_candles_500)
        assert regime.label != "unknown"

        # Report with holdout
        report = generate_report(
            study_name="acceptance_v2",
            dataset_summary={"bars": 500},
            best_params={"buy_spread_base": 1.0},
            best_metrics=metrics,
            best_objective=obj,
            holdout_report=holdout_report,
        )
        assert "Holdout Validation" in report


class TestFullPipelineWithRebalance:
    def test_full_pipeline_with_rebalance(self, sample_candles_500, default_pair_rules):
        config = SimConfig(
            buy_spreads=[1.0, 2.0],
            sell_spreads=[1.0, 2.0],
            buy_amounts_pct=[0.5, 0.5],
            sell_amounts_pct=[0.5, 0.5],
            total_amount_quote=100.0,
            touch_through=True,
            entry_spread_bps=5.0,
            maker_fill_probability=0.8,
            initial_base_pct=0.5,
            position_rebalance_threshold_pct=0.1,
            skip_rebalance=False,
        )
        runner = CandleSimRunner(config, default_pair_rules)
        result = runner.run(sample_candles_500)
        metrics = compute_metrics(result, 100.0, sample_candles_500, 300)
        assert metrics.trade_count > 0


class TestFullPipelineBollinger:
    def test_full_pipeline_bollinger(self, sample_candles_500, default_pair_rules):
        strat = BollingerStrategy(BollingerStrategyConfig(
            buy_spreads=(1.0, 2.0),
            sell_spreads=(1.0, 2.0),
            buy_amounts_pct=(0.5, 0.5),
            sell_amounts_pct=(0.5, 0.5),
        ))
        engine_cfg = EngineConfig(
            total_amount_quote=100.0,
            executor_refresh_time=1500.0,
            fill_participation_rate=1.0,
            latency_bars=0,
        )
        result = SimEngine(engine_cfg, default_pair_rules).run(sample_candles_500, strat)
        metrics = compute_metrics(result, 100.0, sample_candles_500, 300)
        assert isinstance(metrics.pnl_pct, float)
        assert isinstance(metrics.trade_count, int)


class TestExportValidates:
    def test_export_validates(self, sample_candles_500, default_pair_rules, tmp_path):
        import optuna
        from pmm_lab.optuna.objective_wrapper import create_objective
        from pmm_lab.optuna.study import create_study, run_optimization
        from pmm_lab.data.hashing import hash_candles
        from pmm_lab.export.hb_yaml import export_yaml
        from pmm_lab.export.validate_export import validate_yaml_file

        optuna.logging.set_verbosity(optuna.logging.WARNING)
        dataset_hash = hash_candles(sample_candles_500)
        reference_price = float(np.median(sample_candles_500["close"]))
        db_path = str(tmp_path / "accept.db")
        storage_url = f"sqlite:///{db_path}"

        objective = create_objective(
            candles=sample_candles_500,
            pair_rules=default_pair_rules,
            bar_interval_seconds=300,
            dataset_hash=dataset_hash,
            reference_price=reference_price,
            train_days=0.5, test_days=0.25, step_days=0.25,
            embargo_bars=10, run_stress=False,
        )
        study = create_study("accept_test", seed=42, storage_url=storage_url, n_startup_trials=3)
        run_optimization(study, objective, n_trials=3)

        # Export best
        best = study.best_trial
        from pmm_lab.optuna.canonicalizer import canonicalize_params
        config, _ = canonicalize_params(best.params, default_pair_rules, reference_price)
        assert config is not None

        yaml_path = str(tmp_path / "best.yaml")
        export_yaml(config, yaml_path)
        result = validate_yaml_file(yaml_path)
        assert result.valid, f"Validation failed: {result.errors}"


class TestFrozenFixtureRegression:
    def test_frozen_fixture_regression(self, sample_candles_5m, tmp_path):
        from pmm_lab.parity.fixtures import generate_frozen_fixture, load_frozen_fixture
        from pmm_lab.parity.feature_parity import check_feature_parity_frozen

        params = {
            "macd_fast": 21, "macd_slow": 42, "macd_signal": 9, "natr_length": 14,
            "buy_n_levels": 2, "sell_n_levels": 2,
            "buy_spread_base": 1.0, "buy_spread_ratio": 2.0,
            "sell_spread_base": 1.0, "sell_spread_ratio": 2.0,
            "buy_side_weight": 0.5, "amount_skew": 1.0,
            "total_amount_quote": 100.0,
            "executor_refresh_time": 3120.0, "cooldown_time": 3120.0,
            "stop_loss": 0.03, "take_profit": 0.015, "time_limit": 43200,
            "trailing_stop_activation": 0.0, "trailing_stop_delta": 0.001,
        }
        fixture_dir = generate_frozen_fixture(
            sample_candles_5m, params, name="regression", output_dir=str(tmp_path),
        )
        fixture = load_frozen_fixture(fixture_dir)
        result = check_feature_parity_frozen(
            fixture.candles, fixture.expected_features, fixture.config_params,
        )
        assert result.passed, f"Mismatches: {result.mismatches}"


class TestReplayAfterOptimization:
    def test_replay_after_optimization(self, sample_candles_500, default_pair_rules, tmp_path):
        import optuna
        from pmm_lab.optuna.objective_wrapper import create_objective
        from pmm_lab.optuna.study import create_study, run_optimization
        from pmm_lab.data.hashing import hash_candles
        from pmm_lab.utils.replay import extract_trial_records, save_trial_records, replay_and_verify

        optuna.logging.set_verbosity(optuna.logging.WARNING)
        dataset_hash = hash_candles(sample_candles_500)
        reference_price = float(np.median(sample_candles_500["close"]))
        db_path = str(tmp_path / "replay.db")
        storage_url = f"sqlite:///{db_path}"

        objective = create_objective(
            candles=sample_candles_500,
            pair_rules=default_pair_rules,
            bar_interval_seconds=300,
            dataset_hash=dataset_hash,
            reference_price=reference_price,
            train_days=0.5, test_days=0.25, step_days=0.25,
            embargo_bars=10, run_stress=False,
        )
        study = create_study("replay_test", seed=42, storage_url=storage_url, n_startup_trials=5)
        run_optimization(study, objective, n_trials=5)

        records = extract_trial_records(study)
        records_path = str(tmp_path / "trials.jsonl")
        save_trial_records(records, records_path)

        diffs = replay_and_verify(
            records_path, sample_candles_500, default_pair_rules, 300, reference_price,
            train_days=0.5, test_days=0.25, step_days=0.25, embargo_bars=10,
        )
        assert len(diffs) == 0, f"Replay mismatches: {diffs}"


class TestStopShipChecksIntegrated:
    def test_stop_ship_checks_integrated(self, sample_candles_500, default_pair_rules):
        config = _default_config()
        runner = CandleSimRunner(config, default_pair_rules)
        result = runner.run(sample_candles_500)
        metrics = compute_metrics(result, 100.0, sample_candles_500, 300)
        obj = objective_v1(metrics)

        dataset_hash_val = hash_candles(sample_candles_500)
        wf = run_walk_forward(
            sample_candles_500, config, default_pair_rules, 300,
            dataset_hash=dataset_hash_val,
            train_days=0.5, test_days=0.25, step_days=0.25,
        )
        stress = run_stress_tests(sample_candles_500, config, default_pair_rules, 300)

        audit = validate_candles(sample_candles_500, "5m", strict=False)
        checks = run_stop_ship_checks(
            best_metrics=metrics,
            best_objective=obj,
            walkforward_result=wf,
            stress_report=stress,
            dataset_audit=audit,
        )

        expected_keys = {
            "dataset_audit", "runtime_sanity", "objective_not_degenerate",
            "stress_not_collapsed", "yaml_validates",
            "walkforward_robust", "walkforward_positive_majority",
            "holdout_passed", "holdout_no_collapse", "sensitivity_stable",
            "recent_28d_passed", "frozen_parity", "top_k_clustered",
        }
        assert set(checks.keys()) == expected_keys
        # Core checks should pass
        assert checks["dataset_audit"] is True
        assert checks["runtime_sanity"] is True
        assert checks["objective_not_degenerate"] is True
