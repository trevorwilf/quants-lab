"""Tests for strengthened mirror validation (checks 14-19)."""

import os
import yaml
import pytest

from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.export.hb_yaml import export_yaml
from pmm_lab.export.validate_export import validate_yaml_file, ValidationResult


def _export_and_validate(config, tmp_path, overrides=None):
    """Export config to YAML, optionally patch fields, then validate."""
    path = str(tmp_path / "test.yaml")
    export_yaml(config, path)

    if overrides:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        data.update(overrides)
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    return validate_yaml_file(path)


def _default_config():
    return SimConfig(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5],
        sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
    )


class TestValidConfigPassesAllChecks:
    def test_valid_config_passes_all_checks(self, tmp_path):
        result = _export_and_validate(_default_config(), tmp_path)
        assert result.valid, f"Errors: {result.errors}"
        assert len(result.errors) == 0


class TestIntegerFieldTypeCheck:
    def test_integer_field_type_check(self, tmp_path):
        # Set macd_fast to a float
        result = _export_and_validate(_default_config(), tmp_path, {"macd_fast": 21.0})
        # Should produce a warning (float that equals int)
        assert any("macd_fast" in w for w in result.warnings)


class TestNumericFieldTypeCheck:
    def test_numeric_field_type_check(self, tmp_path):
        result = _export_and_validate(_default_config(), tmp_path, {"stop_loss": "bad"})
        assert not result.valid
        assert any("stop_loss" in e for e in result.errors)


class TestBooleanFieldTypeCheck:
    def test_boolean_field_type_check(self, tmp_path):
        result = _export_and_validate(_default_config(), tmp_path, {"skip_rebalance": "yes"})
        assert not result.valid
        assert any("skip_rebalance" in e for e in result.errors)


class TestStringFieldTypeCheck:
    def test_string_field_type_check(self, tmp_path):
        result = _export_and_validate(_default_config(), tmp_path, {"connector_name": 123})
        assert not result.valid
        assert any("connector_name" in e for e in result.errors)


class TestNonAscendingSpreadsWarning:
    def test_non_ascending_spreads_warning(self, tmp_path):
        result = _export_and_validate(
            _default_config(), tmp_path, {"buy_spreads": [2.0, 1.0]}
        )
        # Descending spreads -> warning (not error)
        assert any("buy_spreads" in w and "ascending" in w for w in result.warnings)
        # Should still be valid (warning, not error)
        assert result.valid


class TestV2FieldsMissingWarning:
    def test_v2_fields_missing_warning(self, tmp_path):
        path = str(tmp_path / "test.yaml")
        export_yaml(_default_config(), path)

        with open(path, "r") as f:
            data = yaml.safe_load(f)
        # Remove v2 fields
        data.pop("skip_rebalance", None)
        data.pop("position_rebalance_threshold_pct", None)
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

        result = validate_yaml_file(path)
        assert any("skip_rebalance" in w for w in result.warnings)
        assert any("position_rebalance_threshold_pct" in w for w in result.warnings)


class TestAllTypesCorrectNoWarnings:
    def test_all_types_correct_no_warnings(self, tmp_path):
        result = _export_and_validate(_default_config(), tmp_path)
        assert result.valid
        assert len(result.errors) == 0
        # Filter out the "not strictly ascending" warnings (spreads [1.0, 2.0] are ascending)
        assert len(result.warnings) == 0, f"Unexpected warnings: {result.warnings}"
