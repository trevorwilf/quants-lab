"""Tests for report quality: new sections, field mappings, and analysis gates."""

import json
import pytest
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from unittest.mock import MagicMock

from pmm_lab.metrics.metrics import Metrics
from pmm_lab.objective.objective import ObjectiveDecomposition
from pmm_lab.report.report_md import generate_report


# ── Fake dataclasses ──────────────────────────────────────────

def _make_metrics(**overrides) -> Metrics:
    defaults = dict(
        pnl_pct=5.0, net_pnl_quote=5.0, max_drawdown_pct=10.0, sharpe=1.5,
        trade_count=20, fill_count=40, n_winning=12, n_losing=8,
        gross_win_quote=30.0, gross_loss_quote=15.0, profit_factor=2.0,
        total_fees_quote=1.0, maker_fees_quote=0.5, taker_fees_quote=0.5,
        fee_drag_pct=1.0, inventory_exposure_mean=0.05, inventory_exposure_max=0.1,
        expected_shortfall_5pct=-0.001, volume_zero_bar_count=0, volume_zero_bar_fraction=0.0,
        median_trade_pnl_quote=0.5, inventory_exposure_p95=0.08,
    )
    defaults.update(overrides)
    return Metrics(**defaults)


def _make_objective(**overrides) -> ObjectiveDecomposition:
    defaults = dict(
        raw_score=5.0, pnl_component=3.0, sharpe_component=1.0,
        drawdown_component=0.5, fee_drag_component=0.2,
        inventory_component=0.1, trade_count_penalty=0.0,
        es_component=0.0, is_rejected=False,
    )
    defaults.update(overrides)
    return ObjectiveDecomposition(**defaults)


@dataclass
class FakeMetrics:
    pnl_pct: float = 5.0
    trade_count: int = 20


@dataclass
class FakeObjective:
    raw_score: float = 5.0
    is_rejected: bool = False


@dataclass
class FakeAuditResult:
    passed_strict: bool = True
    total_rows: int = 500
    expected_rows: int = 500
    missing_rows: int = 0
    forward_fill_count: int = 3
    forward_fill_fraction: float = 0.006
    longest_gap_seconds: int = 600
    failure_reasons: list = None

    def __post_init__(self):
        if self.failure_reasons is None:
            self.failure_reasons = []


@dataclass
class FakeRecentWindow:
    passed: bool = True
    reason: str = "ok"
    metrics: Optional[Any] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = FakeMetrics()


@dataclass
class FakeSensitivity:
    sensitivity_penalty: float = 0.1
    baseline_score: float = 5.0
    sign_flips: int = 0
    collapse_count: int = 0
    n_perturbations: int = 12
    n_rejected: int = 0
    perturbed_scores: Dict[str, List[float]] = None

    def __post_init__(self):
        if self.perturbed_scores is None:
            self.perturbed_scores = {"buy_spread_base": [4.5, 5.5]}


@dataclass
class FakeClustering:
    k: int = 5
    is_clustered: bool = True
    mean_cv: float = 0.2
    max_cv: float = 0.4
    clustered_params: list = None
    scattered_params: list = None
    param_ranges: dict = None
    param_cv: dict = None

    def __post_init__(self):
        if self.clustered_params is None:
            self.clustered_params = ["buy_spread_base"]
        if self.scattered_params is None:
            self.scattered_params = ["stop_loss"]
        if self.param_ranges is None:
            self.param_ranges = {
                "buy_spread_base": {"min": 0.001, "max": 0.005, "mean": 0.003, "std": 0.001},
            }
        if self.param_cv is None:
            self.param_cv = {"buy_spread_base": 0.15, "stop_loss": 0.7}


# ── Minimal helper ────────────────────────────────────────────

def _gen(**kwargs):
    """Generate report with minimal required args plus overrides."""
    defaults = dict(
        study_name="test_study",
        dataset_summary={"connector": "nonkyc", "trading_pair": "XMR-USDT", "bars": 500},
        best_params={"buy_spread_base": 0.003, "total_amount_quote": 100.0},
        best_metrics=_make_metrics(),
        best_objective=_make_objective(),
    )
    defaults.update(kwargs)
    return generate_report(**defaults)


# ── Test classes ──────────────────────────────────────────────

class TestAnalysisGate:
    def test_analysis_status_renders_report_status(self):
        report = _gen(analysis_status={
            "report_mode": "full",
            "preflight": "PASS",
            "score": "PASS",
            "analysis": "PASS",
        })
        assert "## Report Status" in report
        assert "full" in report
        assert "preflight" in report
        assert "score" in report
        assert "analysis" in report

    def test_no_analysis_status_omits_section(self):
        report = _gen()
        assert "## Report Status" not in report


class TestReportStatus:
    def test_report_mode_banner(self):
        report = _gen(analysis_status={"report_mode": "lite", "preflight": "SKIP"})
        assert "lite" in report
        assert "## Report Status" in report

    def test_gate_statuses_in_table(self):
        report = _gen(analysis_status={
            "report_mode": "full",
            "preflight": "PASS",
            "score": "FAIL",
            "analysis": "PASS",
        })
        assert "FAIL" in report
        assert "PASS" in report


class TestValidationCoverage:
    def test_json_sidecar_includes_validation_coverage(self, tmp_path):
        out = str(tmp_path / "test_report.md")
        _gen(output_path=out, dataset_audit=FakeAuditResult())
        # test_report.md ends with _report.md -> test_report.json
        json_path = str(tmp_path / "test_report.json")
        assert (tmp_path / "test_report.json").exists()
        with open(json_path) as f:
            data = json.load(f)
        assert "validation_coverage" in data
        assert isinstance(data["validation_coverage"], list)
        assert len(data["validation_coverage"]) > 0

    def test_json_sidecar_report_suffix(self, tmp_path):
        out = str(tmp_path / "my_report.md")
        _gen(output_path=out)
        # my_report.md ends with _report.md -> my_report.json
        json_path = str(tmp_path / "my_report.json")
        assert (tmp_path / "my_report.json").exists()

    def test_json_sidecar_report_md_suffix(self, tmp_path):
        out = str(tmp_path / "my_study_report.md")
        _gen(output_path=out)
        # Ends in _report.md -> replace with _report.json
        json_path = str(tmp_path / "my_study_report.json")
        assert (tmp_path / "my_study_report.json").exists()


class TestDatasetAudit:
    def test_audit_uses_correct_field_names(self):
        audit = FakeAuditResult(
            total_rows=1000, expected_rows=1010, missing_rows=10,
            forward_fill_count=5, forward_fill_fraction=0.005,
            longest_gap_seconds=900,
        )
        report = _gen(dataset_audit=audit)
        assert "## Dataset Audit" in report
        assert "Total rows" in report
        assert "1000" in report
        assert "Expected rows" in report
        assert "1010" in report
        assert "Missing rows" in report
        assert "Forward-fill count" in report
        assert "Forward-fill fraction" in report
        assert "Longest gap" in report
        assert "900" in report

    def test_audit_does_not_use_old_field_names(self):
        audit = FakeAuditResult()
        report = _gen(dataset_audit=audit)
        assert "Gap count" not in report
        assert "Total bars" not in report or "Total rows" in report

    def test_audit_failure_reasons_shown(self):
        audit = FakeAuditResult(failure_reasons=["too many gaps", "bad data"])
        report = _gen(dataset_audit=audit)
        assert "too many gaps" in report


class TestRecentWindow:
    def test_recent_window_uses_metrics_accessor(self):
        rw = FakeRecentWindow(passed=True, reason="score above threshold")
        report = _gen(recent_window_result=rw)
        assert "## Recent 28-Day Window" in report
        assert "score above threshold" in report
        assert "5.0" in report  # pnl_pct from FakeMetrics
        assert "20" in report  # trade_count from FakeMetrics

    def test_recent_window_no_direct_pnl_access(self):
        """Ensure we access metrics.pnl_pct not recent_window_result.pnl_pct."""
        rw = FakeRecentWindow()
        # FakeRecentWindow has no pnl_pct directly - should still work
        report = _gen(recent_window_result=rw)
        assert "## Recent 28-Day Window" in report

    def test_multi_window_renders_all_sections(self):
        rw28 = FakeRecentWindow(passed=True, reason="ok")
        rw14 = FakeRecentWindow(passed=False, reason="pnl negative")
        rw7 = FakeRecentWindow(passed=True, reason="")
        report = _gen(
            recent_window_result=rw28,
            recent_window_results={28: rw28, 14: rw14, 7: rw7},
            recent_blocking_window_days=28,
        )
        assert "## Recent 28-Day Window" in report
        assert "## Recent 14-Day Window (Informational Only)" in report
        assert "## Recent 7-Day Window (Informational Only)" in report

    def test_informational_window_has_disclaimer(self):
        rw28 = FakeRecentWindow(passed=True, reason="ok")
        rw14 = FakeRecentWindow(passed=False, reason="pnl negative")
        report = _gen(
            recent_window_result=rw28,
            recent_window_results={28: rw28, 14: rw14},
            recent_blocking_window_days=28,
        )
        assert "Informational only" in report
        assert "does not affect stop-ship gating" in report

    def test_backward_compat_single_result_still_renders(self):
        rw = FakeRecentWindow(passed=True, reason="ok")
        report = _gen(recent_window_result=rw)
        assert "## Recent 28-Day Window" in report
        assert "(Informational Only)" not in report


class TestSensitivity:
    def test_sensitivity_uses_correct_fields(self):
        sens = FakeSensitivity(
            baseline_score=4.2, sign_flips=1, collapse_count=2,
            n_perturbations=14, n_rejected=1,
            perturbed_scores={"buy_spread_base": [3.8, 4.6]},
        )
        report = _gen(sensitivity_report=sens)
        assert "## Sensitivity Analysis" in report
        assert "Baseline score" in report
        assert "4.2" in report
        assert "Sign flips" in report
        assert "Collapse count" in report
        assert "Perturbations" in report
        assert "14" in report
        assert "buy_spread_base" in report

    def test_sensitivity_no_old_field_names(self):
        sens = FakeSensitivity()
        report = _gen(sensitivity_report=sens)
        assert "Worst parameter" not in report
        assert "Worst delta" not in report


class TestClustering:
    def test_clustering_uses_correct_fields(self):
        cl = FakeClustering(
            k=5, is_clustered=True, mean_cv=0.2, max_cv=0.4,
            clustered_params=["buy_spread_base"],
            scattered_params=["stop_loss"],
            param_cv={"buy_spread_base": 0.15, "stop_loss": 0.7},
            param_ranges={
                "buy_spread_base": {"min": 0.001, "max": 0.005, "mean": 0.003, "std": 0.001},
                "stop_loss": {"min": 0.01, "max": 0.05, "mean": 0.03, "std": 0.02},
            },
        )
        report = _gen(cluster_report=cl)
        assert "## Top-K Clustering" in report
        assert "K" in report
        assert "Is clustered" in report
        assert "Mean CV" in report
        assert "Max CV" in report
        assert "Clustered params" in report
        assert "Scattered params" in report
        assert "buy_spread_base" in report
        assert "stop_loss" in report

    def test_clustering_no_old_field_names(self):
        cl = FakeClustering()
        report = _gen(cluster_report=cl)
        assert "Cluster count" not in report


class TestCapitalDiagnostics:
    def test_capital_section_renders(self):
        report = _gen(dataset_summary={
            "connector": "nonkyc",
            "total_amount_quote_search_min": 50,
            "total_amount_quote_search_max": 500,
            "total_amount_quote_ideal": 200,
        })
        assert "## Capital/Budget Analysis" in report
        assert "50" in report
        assert "500" in report
        assert "200" in report

    def test_capital_section_omitted_without_keys(self):
        report = _gen(dataset_summary={"connector": "nonkyc"})
        assert "## Capital/Budget Analysis" not in report

    def test_capital_boundary_warning_low(self):
        report = _gen(
            dataset_summary={
                "connector": "nonkyc",
                "total_amount_quote_search_min": 50,
                "total_amount_quote_search_max": 500,
                "total_amount_quote_ideal": 200,
            },
            best_params={"total_amount_quote": 52.0},  # within 5% of min
        )
        assert "within 5% of search minimum" in report

    def test_capital_boundary_warning_high(self):
        report = _gen(
            dataset_summary={
                "connector": "nonkyc",
                "total_amount_quote_search_min": 50,
                "total_amount_quote_search_max": 500,
                "total_amount_quote_ideal": 200,
            },
            best_params={"total_amount_quote": 498.0},  # within 5% of max
        )
        assert "within 5% of search maximum" in report


class TestQuotePreservation:
    def test_total_amount_quote_in_best_params(self):
        report = _gen(best_params={"total_amount_quote": 150.0, "buy_spread_base": 0.003})
        assert "150.0" in report

    def test_score_summary_renders(self):
        report = _gen(score_summary={"phase1": 3.5, "robust": 2.8, "worst": 1.2})
        assert "## Selection Score Summary" in report
        assert "3.5000" in report
        assert "2.8000" in report
        assert "1.2000" in report

    def test_run_provenance_renders(self):
        report = _gen(run_provenance={"study_name": "test", "seed": 42, "version": "0.1.0"})
        assert "## Run Provenance" in report
        assert "study_name" in report
        assert "42" in report

    def test_preflight_dict_renders(self):
        report = _gen(preflight_report={"data_ok": True, "exchange_ok": True})
        assert "## Preflight" in report
        assert "data_ok" in report

    def test_preflight_object_renders(self):
        @dataclass
        class PF:
            status: str = "ok"
            detail: str = "all good"
        report = _gen(preflight_report=PF())
        assert "## Preflight" in report
        assert "ok" in report


class TestSensitivityParams:
    def test_total_amount_quote_in_perturbable(self):
        from pmm_lab.optuna.sensitivity import PERTURBABLE_PARAMS
        assert "total_amount_quote" in PERTURBABLE_PARAMS


class TestClusteringParams:
    def test_total_amount_quote_in_cluster_params(self):
        from pmm_lab.optuna.clustering import CLUSTER_PARAMS
        assert "total_amount_quote" in CLUSTER_PARAMS


class TestMetricsRename:
    def test_metrics_section_renamed(self):
        report = _gen()
        assert "## Selected Candidate Single-Run Diagnostics" in report
        assert "## Best Metrics" not in report

    def test_objective_section_renamed(self):
        report = _gen()
        assert "## Selected Candidate Single-Run Objective" in report
        assert "## Objective Decomposition" not in report
