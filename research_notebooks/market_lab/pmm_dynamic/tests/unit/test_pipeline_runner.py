"""Tests for the full pipeline runner."""

import os
import pytest
from unittest.mock import patch, MagicMock

from pmm_lab.deploy.runner import PipelineResult, run_full_pipeline


class TestPipelineResultFields:
    def test_pipeline_result_fields(self):
        result = PipelineResult(
            study_name="test_study",
            connector="nonkyc", trading_pair="XMR-USDT", interval="5m",
            started_at="2025-01-01T00:00:00+00:00",
            completed_at="2025-01-01T00:01:00+00:00",
            elapsed_seconds=60.0,
            total_bars=1000, dev_bars=800, holdout_bars=200,
            dataset_hash="abc123",
            n_trials=50, best_trial_number=10, best_score=0.5,
            objective_version=2,
            wf_aggregate_score=0.4, wf_fold_count=5,
            holdout_score=0.3, holdout_passed=True,
            stress_worst_score=-1.0, sensitivity_penalty=0.05,
            top_k_clustered=True,
            stop_ship_checks={"dataset_audit": True, "feature_parity": True},
            stop_ship_passed=True,
            package_dir="/tmp/deploy",
            report_path="/tmp/report.md",
            yaml_path="/tmp/config.yml",
        )
        assert result.study_name == "test_study"
        assert result.total_bars == 1000
        assert result.n_trials == 50
        assert result.best_score == 0.5
        assert result.holdout_passed is True
        assert result.package_dir == "/tmp/deploy"


class TestPipelineResultStopShipDerived:
    def test_pipeline_result_stop_ship_derived(self):
        # All checks pass
        result = PipelineResult(
            study_name="t", connector="c", trading_pair="p", interval="5m",
            started_at="", completed_at="", elapsed_seconds=0,
            total_bars=0, dev_bars=0, holdout_bars=0, dataset_hash="",
            n_trials=0, best_trial_number=0, best_score=0, objective_version=1,
            wf_aggregate_score=0, wf_fold_count=0, holdout_score=0,
            holdout_passed=True, stress_worst_score=0, sensitivity_penalty=0,
            top_k_clustered=True,
            stop_ship_checks={"a": True, "b": True},
            stop_ship_passed=True,
        )
        assert result.stop_ship_passed is True

        # One check fails
        result2 = PipelineResult(
            study_name="t", connector="c", trading_pair="p", interval="5m",
            started_at="", completed_at="", elapsed_seconds=0,
            total_bars=0, dev_bars=0, holdout_bars=0, dataset_hash="",
            n_trials=0, best_trial_number=0, best_score=0, objective_version=1,
            wf_aggregate_score=0, wf_fold_count=0, holdout_score=0,
            holdout_passed=False, stress_worst_score=0, sensitivity_penalty=0,
            top_k_clustered=False,
            stop_ship_checks={"a": True, "b": False},
            stop_ship_passed=False,
        )
        assert result2.stop_ship_passed is False


class TestRunFullPipelineMini:
    def test_run_full_pipeline_mini(self, sample_candles_500, default_pair_rules, tmp_path):
        """Run a minimal pipeline on synthetic data with monkey-patched loader."""
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)

        # Monkey-patch MongoCandleLoader to return synthetic data
        mock_loader = MagicMock()
        mock_loader.load_range.return_value = sample_candles_500
        mock_loader.ping.return_value = True

        with patch("pmm_lab.deploy.runner.MongoCandleLoader", return_value=mock_loader), \
             patch("pmm_lab.deploy.runner.load_exchange_rules", return_value={}), \
             patch("pmm_lab.deploy.runner.resolve_pair_rules", return_value=default_pair_rules):
            result = run_full_pipeline(
                connector="test",
                trading_pair="BTC-USDT",
                interval="5m",
                n_trials=5,
                n_jobs=1,
                output_dir=str(tmp_path),
                study_name="mini_test",
                holdout_fraction=0.30,
                objective_version=1,
                train_days=0.5,
                test_days=0.15,
                step_days=0.15,
                top_k=2,
                run_stress=False,
                run_sensitivity=False,
            )

        assert isinstance(result, PipelineResult)
        assert result.study_name == "mini_test"
        assert result.total_bars == 500
        assert result.n_trials == 5
        assert result.best_score is not None
        assert result.wf_fold_count >= 2

        # Verify output files exist
        assert result.yaml_path is not None
        assert os.path.isfile(result.yaml_path)
        assert result.report_path is not None
        assert os.path.isfile(result.report_path)
        assert result.package_dir is not None
        assert os.path.isdir(result.package_dir)
        assert os.path.isfile(os.path.join(result.package_dir, "package.json"))

        # Verify output directory structure
        study_dir = tmp_path / "mini_test"
        assert (study_dir / "config.yml").exists()
        assert (study_dir / "report.md").exists()
        # Package goes to deploy/ if stop-ship passes, rejected/ otherwise
        if result.deployable:
            assert (study_dir / "deploy" / "package.json").exists()
        else:
            assert (study_dir / "rejected" / "package.json").exists()
            assert (study_dir / "rejected" / "STOP_SHIP_FAILED.txt").exists()


class TestPipelineCreatesEnvironmentSnapshot:
    def test_pipeline_creates_environment_snapshot(self, sample_candles_500, default_pair_rules, tmp_path):
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)

        mock_loader = MagicMock()
        mock_loader.load_range.return_value = sample_candles_500
        mock_loader.ping.return_value = True

        with patch("pmm_lab.deploy.runner.MongoCandleLoader", return_value=mock_loader), \
             patch("pmm_lab.deploy.runner.load_exchange_rules", return_value={}), \
             patch("pmm_lab.deploy.runner.resolve_pair_rules", return_value=default_pair_rules):
            result = run_full_pipeline(
                connector="test",
                trading_pair="BTC-USDT",
                interval="5m",
                n_trials=3,
                n_jobs=1,
                output_dir=str(tmp_path),
                study_name="env_test",
                holdout_fraction=0.30,
                objective_version=1,
                train_days=0.5,
                test_days=0.15,
                step_days=0.15,
                top_k=2,
                run_stress=False,
                run_sensitivity=False,
            )

        env_path = tmp_path / "env_test" / "environment.json"
        assert env_path.exists()
