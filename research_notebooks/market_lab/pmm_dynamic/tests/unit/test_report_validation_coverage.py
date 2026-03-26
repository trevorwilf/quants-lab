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
