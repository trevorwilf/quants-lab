"""Tests for Phase 2 taker_probability wiring through the pipeline."""

import json
import pytest
from dataclasses import replace

from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.metrics.metrics import Metrics
from pmm_lab.objective.objective import ObjectiveDecomposition


def _make_metrics(**overrides):
    defaults = dict(
        pnl_pct=5.0, net_pnl_quote=5.0, max_drawdown_pct=10.0, sharpe=1.5,
        trade_count=20, fill_count=40, n_winning=12, n_losing=8,
        gross_win_quote=30.0, gross_loss_quote=15.0, profit_factor=2.0,
        total_fees_quote=1.0, maker_fees_quote=0.5, taker_fees_quote=0.5,
        fee_drag_pct=1.0, inventory_exposure_mean=0.05, inventory_exposure_max=0.1,
        expected_shortfall_5pct=-0.001, volume_zero_bar_count=0,
        volume_zero_bar_fraction=0.0, median_trade_pnl_quote=0.5,
        inventory_exposure_p95=0.08,
    )
    defaults.update(overrides)
    return Metrics(**defaults)


def _make_obj():
    from pmm_lab.objective.objective import objective_v1
    return objective_v1(_make_metrics())


class TestObjectiveWrapperAcceptsTakerProbability:
    """Fix 1+2: create_objective accepts and threads taker_probability."""

    def test_create_objective_accepts_kwarg(self):
        """create_objective should accept taker_probability without error."""
        import inspect
        from pmm_lab.optuna.objective_wrapper import create_objective
        sig = inspect.signature(create_objective)
        assert "taker_probability" in sig.parameters

    def test_default_is_zero(self):
        import inspect
        from pmm_lab.optuna.objective_wrapper import create_objective
        sig = inspect.signature(create_objective)
        assert sig.parameters["taker_probability"].default == 0.0


class TestReportAutoPopulatesExecutionRealism:
    """Fix 5a: generate_report auto-populates execution_realism from best_params."""

    def test_auto_populate_when_none(self):
        from pmm_lab.report.report_md import generate_report

        report_text = generate_report(
            study_name="test",
            dataset_summary={"connector": "nonkyc"},
            best_params={"taker_probability": 0.10, "fill_participation_rate": 0.1},
            best_metrics=_make_metrics(),
            best_objective=_make_obj(),
            execution_realism=None,
        )
        assert "Execution Realism" in report_text
        assert "taker_probability" in report_text
        assert "0.1" in report_text

    def test_warning_for_nonkyc_zero_taker(self):
        from pmm_lab.report.report_md import generate_report

        report_text = generate_report(
            study_name="test",
            dataset_summary={"connector": "nonkyc"},
            best_params={"taker_probability": 0.0},
            best_metrics=_make_metrics(),
            best_objective=_make_obj(),
        )
        assert "WARNING" in report_text
        assert "post-only" in report_text.lower()


class TestStopShipTakerRealism:
    """Fix 7: run_stop_ship_checks has taker_realism advisory."""

    def test_fails_for_nonkyc_no_taker(self):
        from pmm_lab.report.report_md import run_stop_ship_checks

        checks = run_stop_ship_checks(
            best_metrics=_make_metrics(), best_objective=_make_obj(),
            execution_realism={
                "connector": "nonkyc",
                "taker_probability": 0.0,
                "supports_post_only": False,
            },
        )
        assert "taker_realism" in checks
        assert checks["taker_realism"] is False

    def test_passes_for_mexc(self):
        from pmm_lab.report.report_md import run_stop_ship_checks

        checks = run_stop_ship_checks(
            best_metrics=_make_metrics(), best_objective=_make_obj(),
            execution_realism={
                "connector": "mexc",
                "taker_probability": 0.0,
                "supports_post_only": True,
            },
        )
        assert checks["taker_realism"] is True

    def test_passes_for_nonkyc_with_taker_prob(self):
        from pmm_lab.report.report_md import run_stop_ship_checks

        checks = run_stop_ship_checks(
            best_metrics=_make_metrics(), best_objective=_make_obj(),
            execution_realism={
                "connector": "nonkyc",
                "taker_probability": 0.10,
                "supports_post_only": False,
            },
        )
        assert checks["taker_realism"] is True

    def test_backward_compat_no_execution_realism(self):
        from pmm_lab.report.report_md import run_stop_ship_checks

        checks = run_stop_ship_checks(best_metrics=_make_metrics(), best_objective=_make_obj())
        assert "taker_realism" not in checks


class TestExportMetadataTakerProbability:
    """Fix 6: export metadata includes execution realism fields."""

    def test_metadata_contains_taker_probability(self, tmp_path):
        import yaml
        from pmm_lab.export.hb_yaml import export_yaml, ExportParams

        config = SimConfig(
            buy_spreads=[1.0], sell_spreads=[1.0],
            buy_amounts_pct=[0.5], sell_amounts_pct=[0.5],
            taker_probability=0.10,
            touch_through=True,
            maker_fill_probability=0.8,
            refresh_close_mode="market_close",
            initial_base_balance=5.0,
        )
        out_path = str(tmp_path / "test_export.yaml")
        metadata = {"connector": "nonkyc", "trading_pair": "XMR-USDT"}

        export_yaml(config, out_path, ExportParams(
            connector_name="nonkyc",
            trading_pair="XMR-USDT",
        ), metadata=metadata)

        meta_path = str(tmp_path / "test_export.meta.yml")
        with open(meta_path) as f:
            meta = yaml.safe_load(f)

        assert meta["taker_probability"] == 0.10
        assert meta["touch_through"] is True
        assert meta["maker_fill_probability"] == 0.8
        assert meta["refresh_close_mode"] == "market_close"
        assert meta["initial_base_balance"] == 5.0

        # Main YAML should NOT contain taker_probability
        with open(out_path) as f:
            main_yaml = yaml.safe_load(f)
        assert "taker_probability" not in main_yaml


class TestNotebookTakerProbabilityWiring:
    """Fix 3+4+8: Notebooks have all taker_probability wiring."""

    @pytest.fixture(params=[
        "notebooks/pmm_dynamic/pmm_dynamic_multi_exchange_sweep_mexc_nonkyc.ipynb",
        "notebooks/pmm_dynamic/pmm_dynamic_retest_sweep.ipynb",
    ])
    def notebook_source(self, request):
        import os
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        nb_path = os.path.join(base, request.param)
        with open(nb_path, encoding="utf-8") as f:
            nb = json.load(f)
        cell3 = "".join(nb["cells"][3]["source"])
        cell8 = "".join(nb["cells"][8]["source"])
        return cell3, cell8

    def test_cell3_defines_taker_probability_by_connector(self, notebook_source):
        cell3, _ = notebook_source
        assert "TAKER_PROBABILITY_BY_CONNECTOR" in cell3
        assert "DEFAULT_TAKER_PROBABILITY" in cell3

    def test_cell3_prints_taker_prob(self, notebook_source):
        cell3, _ = notebook_source
        assert "Taker prob" in cell3

    def test_cell8_resolves_taker_prob(self, notebook_source):
        _, cell8 = notebook_source
        assert "taker_prob = TAKER_PROBABILITY_BY_CONNECTOR.get(" in cell8

    def test_cell8_factory_kwargs_has_taker_probability(self, notebook_source):
        _, cell8 = notebook_source
        assert "taker_probability=taker_prob" in cell8

    def test_cell8_stop_ship_has_execution_realism(self, notebook_source):
        _, cell8 = notebook_source
        assert 'execution_realism=' in cell8

    def test_cell8_all_pass_skips_taker_realism(self, notebook_source):
        _, cell8 = notebook_source
        assert 'taker_realism' in cell8
        assert 'all(checks.values())' not in cell8

    def test_cell8_generate_report_has_execution_realism(self, notebook_source):
        _, cell8 = notebook_source
        # Check that execution_realism is passed to generate_report
        idx = cell8.find("generate_report(")
        # Skip import line
        while idx >= 0 and "import" in cell8[max(0, idx-30):idx]:
            idx = cell8.find("generate_report(", idx + 1)
        assert idx > 0
        block = cell8[idx:idx+2000]
        assert "execution_realism" in block
