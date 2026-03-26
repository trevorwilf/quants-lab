"""Lightweight structural tests for pmm_lab.deploy.finalist_validation."""

import inspect

import pytest


class TestFinalistValidationStructure:
    """Verify the module is importable and has the expected API surface."""

    def test_validate_finalist_importable(self):
        """validate_finalist should be importable."""
        from pmm_lab.deploy.finalist_validation import validate_finalist
        assert callable(validate_finalist)

    def test_validate_finalist_signature(self):
        """validate_finalist should have the key keyword-only parameters."""
        from pmm_lab.deploy.finalist_validation import validate_finalist
        sig = inspect.signature(validate_finalist)
        required_params = [
            "study_name", "full_candles", "study", "best_trial",
            "connector", "trading_pair", "interval", "dataset_hash",
            "pair_rules", "bar_interval_seconds", "ranked_trials",
            "reference_price",
        ]
        param_names = set(sig.parameters.keys())
        for name in required_params:
            assert name in param_names, f"Missing parameter: {name}"
        # All should be keyword-only
        for name in required_params:
            kind = sig.parameters[name].kind
            assert kind == inspect.Parameter.KEYWORD_ONLY, (
                f"{name} should be keyword-only, got {kind}"
            )

    def test_finalist_result_dataclass(self):
        """FinalistValidationResult should have expected fields."""
        from pmm_lab.deploy.finalist_validation import FinalistValidationResult
        import dataclasses
        assert dataclasses.is_dataclass(FinalistValidationResult)
        field_names = {f.name for f in dataclasses.fields(FinalistValidationResult)}
        expected = {
            "config", "dev_metrics", "dev_objective", "stop_ship_checks",
            "all_passed", "yaml_path", "report_path", "output_dir",
        }
        assert expected.issubset(field_names), (
            f"Missing fields: {expected - field_names}"
        )
