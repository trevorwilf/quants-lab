"""Tests for validation coverage reporting."""
import pytest
from unittest.mock import MagicMock
from pmm_lab.report.report_md import build_validation_coverage, ValidationCoverageItem


class TestValidationCoverage:
    def test_all_none_produces_all_skipped(self):
        items = build_validation_coverage()
        for item in items:
            assert item.status == "SKIPPED", f"{item.name} should be SKIPPED when input is None"

    def test_passing_audit_shows_pass(self):
        audit = MagicMock(passed_strict=True)
        items = build_validation_coverage(dataset_audit=audit)
        audit_items = [i for i in items if i.name == "dataset_audit"]
        assert len(audit_items) == 1
        assert audit_items[0].status == "PASS"

    def test_failing_yaml_shows_fail(self):
        vr = MagicMock(valid=False, errors=["missing field"], warnings=[], mode="mirror")
        items = build_validation_coverage(validation_result=vr)
        yaml_items = [i for i in items if i.name == "yaml_validation"]
        assert len(yaml_items) == 1
        assert yaml_items[0].status == "FAIL"

    def test_passing_yaml_shows_pass(self):
        vr = MagicMock(valid=True, errors=[], warnings=["minor"], mode="mirror")
        items = build_validation_coverage(validation_result=vr)
        yaml_items = [i for i in items if i.name == "yaml_validation"]
        assert yaml_items[0].status == "PASS"
        assert "mirror" in yaml_items[0].detail

    def test_all_populated_produces_no_skipped(self):
        items = build_validation_coverage(
            dataset_audit=MagicMock(passed_strict=True),
            validation_result=MagicMock(valid=True, errors=[], warnings=[], mode="mirror"),
            holdout_report=MagicMock(exported_holdout_passed=True, exported_holdout_score=1.5),
            sensitivity_report=MagicMock(sensitivity_penalty=0.1),
            recent_window_result=MagicMock(passed=True, reason="ok"),
            parity_result=MagicMock(passed=True),
            long_parity_result=MagicMock(passed=True),
            cluster_report=MagicMock(is_clustered=True, mean_cv=0.2),
            walkforward_result=MagicMock(folds=[1, 2, 3]),
            stress_report=MagicMock(worst_scenario="fees_2x", worst_score=-2.0),
        )
        skipped = [i for i in items if i.status == "SKIPPED"]
        assert len(skipped) == 0, f"Unexpected SKIPPED items: {[i.name for i in skipped]}"

    def test_coverage_item_fields(self):
        item = ValidationCoverageItem("test", "PASS", "some detail")
        assert item.name == "test"
        assert item.status == "PASS"
        assert item.detail == "some detail"

    def test_multi_window_coverage_rows(self):
        rw28 = MagicMock(passed=True, reason="ok", objective=MagicMock(raw_score=0.5), metrics=MagicMock(pnl_pct=1.0, trade_count=20))
        rw14 = MagicMock(passed=False, reason="pnl neg", objective=MagicMock(raw_score=-0.1), metrics=MagicMock(pnl_pct=-0.5, trade_count=10))
        rw7 = MagicMock(passed=True, reason="", objective=MagicMock(raw_score=0.2), metrics=MagicMock(pnl_pct=0.3, trade_count=5))
        items = build_validation_coverage(
            recent_window_result=rw28,
            recent_window_results={28: rw28, 14: rw14, 7: rw7},
            recent_blocking_window_days=28,
        )
        names = [i.name for i in items]
        assert "recent_28d" in names
        assert "recent_14d_info" in names
        assert "recent_7d_info" in names

    def test_info_coverage_detail_says_informational(self):
        rw14 = MagicMock(passed=False, reason="pnl neg", objective=MagicMock(raw_score=-0.1), metrics=MagicMock(pnl_pct=-0.5, trade_count=10))
        items = build_validation_coverage(
            recent_window_results={14: rw14},
            recent_blocking_window_days=28,
        )
        info_items = [i for i in items if i.name == "recent_14d_info"]
        assert len(info_items) == 1
        assert "informational only" in info_items[0].detail

    def test_no_duplicate_28d_in_info_rows(self):
        rw28 = MagicMock(passed=True, reason="ok")
        items = build_validation_coverage(
            recent_window_result=rw28,
            recent_window_results={28: rw28},
            recent_blocking_window_days=28,
        )
        names = [i.name for i in items]
        assert names.count("recent_28d") == 1
        assert "recent_28d_info" not in names
