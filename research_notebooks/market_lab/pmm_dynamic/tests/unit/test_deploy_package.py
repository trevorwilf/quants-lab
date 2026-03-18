"""Tests for deployment package creation, save/load roundtrip."""

import json
import yaml
import pytest
from datetime import datetime

from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.metrics.metrics import Metrics
from pmm_lab.objective.objective import objective_v1
from pmm_lab.deploy.package import (
    create_deployment_package,
    save_deployment_package,
    load_deployment_package,
    DeploymentPackage,
    ExpectedPerformance,
)


def _make_metrics():
    return Metrics(
        pnl_pct=5.0, net_pnl_quote=5.0, max_drawdown_pct=10.0, sharpe=1.5,
        trade_count=20, fill_count=40, n_winning=12, n_losing=8,
        gross_win_quote=30.0, gross_loss_quote=15.0, profit_factor=2.0,
        total_fees_quote=1.0, maker_fees_quote=0.5, taker_fees_quote=0.5,
        fee_drag_pct=1.0, inventory_exposure_mean=0.05, inventory_exposure_max=0.1,
        expected_shortfall_5pct=-0.001, volume_zero_bar_count=0,
        volume_zero_bar_fraction=0.0, median_trade_pnl_quote=0.5,
        inventory_exposure_p95=0.08,
    )


def _make_test_package(**overrides):
    config = SimConfig(
        buy_spreads=[1.0, 2.0], sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5], sell_amounts_pct=[0.5, 0.5],
    )
    metrics = _make_metrics()
    objective = objective_v1(metrics)
    package = create_deployment_package(
        config, metrics, objective,
        study_name="test", dataset_hash="abc123", dataset_bars=500,
        **overrides,
    )
    return package


class TestCreateDeploymentPackage:
    def test_create_deployment_package(self):
        package = _make_test_package()
        assert isinstance(package, DeploymentPackage)
        assert package.study_name == "test"
        assert package.dataset_hash == "abc123"
        assert package.dataset_bars == 500
        assert package.connector == "nonkyc"
        assert package.trading_pair == "BTC-USDT"
        assert package.interval == "5m"
        assert isinstance(package.config_dict, dict)
        assert isinstance(package.sim_config_params, dict)
        assert isinstance(package.expected, ExpectedPerformance)
        assert package.expected.pnl_pct == 5.0
        assert package.expected.trade_count == 20
        assert package.objective_score != 0.0


class TestSaveAndLoadRoundtrip:
    def test_save_and_load_roundtrip(self, tmp_path):
        package = _make_test_package()
        out_dir = str(tmp_path / "deploy")
        save_deployment_package(package, out_dir)
        loaded = load_deployment_package(out_dir)
        assert loaded.study_name == package.study_name
        assert loaded.dataset_hash == package.dataset_hash
        assert loaded.expected.pnl_pct == package.expected.pnl_pct
        assert loaded.expected.trade_count == package.expected.trade_count
        assert loaded.objective_score == package.objective_score


class TestPackageHasConfigYml:
    def test_package_has_config_yml(self, tmp_path):
        package = _make_test_package()
        out_dir = str(tmp_path / "deploy")
        save_deployment_package(package, out_dir)
        assert (tmp_path / "deploy" / "config.yml").exists()


class TestPackageHasExpectedMetrics:
    def test_package_has_expected_metrics(self, tmp_path):
        package = _make_test_package()
        out_dir = str(tmp_path / "deploy")
        save_deployment_package(package, out_dir)
        assert (tmp_path / "deploy" / "expected_metrics.json").exists()


class TestPackageHasPackageJson:
    def test_package_has_package_json(self, tmp_path):
        package = _make_test_package()
        out_dir = str(tmp_path / "deploy")
        save_deployment_package(package, out_dir)
        assert (tmp_path / "deploy" / "package.json").exists()


class TestConfigYmlIsValidYaml:
    def test_config_yml_is_valid_yaml(self, tmp_path):
        package = _make_test_package()
        out_dir = str(tmp_path / "deploy")
        save_deployment_package(package, out_dir)
        with open(tmp_path / "deploy" / "config.yml") as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict)
        assert "controller_name" in data
        assert data["controller_name"] == "pmm_dynamic"


class TestExpectedMetricsHasPnl:
    def test_expected_metrics_has_pnl(self, tmp_path):
        package = _make_test_package()
        out_dir = str(tmp_path / "deploy")
        save_deployment_package(package, out_dir)
        with open(tmp_path / "deploy" / "expected_metrics.json") as f:
            data = json.load(f)
        assert "pnl_pct" in data
        assert data["pnl_pct"] == 5.0


class TestPackageWithOptionalFields:
    def test_package_with_optional_fields(self):
        package = _make_test_package(
            wf_median_pnl=3.0,
            wf_median_sharpe=1.2,
            wf_fold_count=5,
            holdout_pnl_pct=2.5,
            holdout_score=0.8,
            stress_worst_score=-1.5,
            sensitivity_penalty=0.1,
            stop_ship_checks={"dataset_audit": True, "runtime_sanity": True},
            environment_hash="env123",
        )
        assert package.expected.wf_median_pnl_pct == 3.0
        assert package.expected.wf_median_sharpe == 1.2
        assert package.expected.wf_fold_count == 5
        assert package.expected.holdout_pnl_pct == 2.5
        assert package.expected.holdout_score == 0.8
        assert package.expected.stress_worst_score == -1.5
        assert package.expected.sensitivity_penalty == 0.1
        assert package.stop_ship_checks["dataset_audit"] is True
        assert package.environment_hash == "env123"


class TestPackageWithoutOptionalFields:
    def test_package_without_optional_fields(self):
        package = _make_test_package()
        assert package.expected.wf_median_pnl_pct is None
        assert package.expected.holdout_pnl_pct is None
        assert package.expected.stress_worst_score is None
        assert package.expected.sensitivity_penalty is None
        assert package.stop_ship_checks is None
        assert package.environment_hash is None
        # Still valid
        assert isinstance(package, DeploymentPackage)
        assert package.expected.pnl_pct == 5.0


class TestExpectedPerformanceMonitoringFields:
    """ExpectedPerformance must include monitoring-compatible fields."""

    def test_monitoring_fields_exist(self):
        from pmm_lab.deploy.package import ExpectedPerformance
        ep = ExpectedPerformance(
            pnl_pct=5.0, max_drawdown_pct=10.0, trade_count=50,
            sharpe=1.5, profit_factor=2.0, fee_drag_pct=1.0,
            median_trade_pnl_quote=0.5,
            evaluation_hours=168.0,
            total_volume_quote=5000.0,
            fee_rate_pct_of_volume=0.15,
            buy_fraction=0.55,
            sell_fraction=0.45,
        )
        assert ep.evaluation_hours == 168.0
        assert ep.fee_rate_pct_of_volume == 0.15
        assert ep.buy_fraction == 0.55


class TestPackageCreatedAtIsUtc:
    def test_package_created_at_is_utc(self):
        package = _make_test_package()
        # Should be a valid ISO timestamp
        dt = datetime.fromisoformat(package.created_at)
        assert dt.tzinfo is not None  # timezone-aware
