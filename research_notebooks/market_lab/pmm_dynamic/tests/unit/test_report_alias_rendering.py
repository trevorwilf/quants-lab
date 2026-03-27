"""Tests that generate_report() renders correctly with both old and new key formats."""
import pytest
from unittest.mock import MagicMock
from pmm_lab.report.report_md import generate_report

def _mock_metrics():
    m = MagicMock()
    m.pnl_pct = 5.0; m.sharpe = 1.5; m.max_drawdown_pct = 10.0
    m.trade_count = 100; m.total_fees_quote = 2.0; m.profit_factor = 2.5
    m.fee_drag_pct = 0.5; m.fill_count = 200; m.net_pnl_quote = 50.0
    m.maker_fees_quote = 1.0; m.taker_fees_quote = 1.0
    return m

def _mock_obj():
    o = MagicMock()
    o.raw_score = 1.5; o.is_rejected = False
    o.pnl_component = 1.0; o.sharpe_component = 0.0
    o.drawdown_component = 0.2; o.fee_drag_component = 0.1
    o.inventory_component = 0.05; o.trade_count_penalty = 0.0
    o.es_component = 0.0
    return o

def test_new_keys_render():
    report = generate_report(
        study_name="test", dataset_summary={"connector": "t", "trading_pair": "B", "interval": "5m"},
        best_params={}, best_metrics=_mock_metrics(), best_objective=_mock_obj(),
        analysis_status={"report_mode": "validated", "preflight": "PASS", "score": "PASS", "analysis": "PASS"},
        score_summary={"phase1": 1.0, "robust": 1.5, "worst": 0.5},
    )
    assert "validated" in report
    assert "| preflight | PASS |" in report
    assert "| phase1 | 1.0000 |" in report

def test_old_keys_render_via_alias():
    report = generate_report(
        study_name="test", dataset_summary={"connector": "t", "trading_pair": "B", "interval": "5m"},
        best_params={}, best_metrics=_mock_metrics(), best_objective=_mock_obj(),
        analysis_status={"preflight_passed": True, "score_gate_passed": True, "analysis_gate_passed": True},
        score_summary={"phase1_best": 1.0, "robust_score": 1.5, "worst_score": 0.5},
    )
    assert "| preflight | PASS |" in report
    assert "| phase1 | 1.0000 |" in report

def test_auto_build_coverage():
    report = generate_report(
        study_name="test", dataset_summary={"connector": "t", "trading_pair": "B", "interval": "5m"},
        best_params={}, best_metrics=_mock_metrics(), best_objective=_mock_obj(),
        validation_coverage=None,
    )
    assert "Validation Coverage" in report
    assert "SKIPPED" in report
