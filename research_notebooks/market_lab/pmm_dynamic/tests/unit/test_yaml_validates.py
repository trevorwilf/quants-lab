"""Tests for pmm_lab.export.validate_export — YAML validation."""

import yaml
import math
import pytest
from pathlib import Path

from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.export.hb_yaml import sim_config_to_hb_dict, export_yaml, ExportParams
from pmm_lab.export.validate_export import validate_yaml_file, _validate_mirror


def _default_config():
    return SimConfig(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5],
        sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
    )


def _export_and_validate(config, tmp_path, **kwargs):
    path = str(tmp_path / "test.yml")
    export_yaml(config, path, **kwargs)
    return validate_yaml_file(path)


class TestYamlValidation:
    def test_valid_config_passes_mirror(self, tmp_path):
        result = _export_and_validate(_default_config(), tmp_path)
        assert result.valid
        assert result.mode == "mirror"

    def test_missing_required_key_fails(self, tmp_path):
        """Remove controller_name → validation fails."""
        d = sim_config_to_hb_dict(_default_config())
        del d["controller_name"]
        path = str(tmp_path / "bad.yml")
        with open(path, "w") as f:
            yaml.dump(d, f)
        result = validate_yaml_file(path)
        assert not result.valid
        assert any("controller_name" in e for e in result.errors)

    def test_wrong_controller_name_fails(self, tmp_path):
        d = sim_config_to_hb_dict(_default_config())
        d["controller_name"] = "pmm_static"
        path = str(tmp_path / "bad.yml")
        with open(path, "w") as f:
            yaml.dump(d, f)
        result = validate_yaml_file(path)
        assert not result.valid

    def test_amounts_not_summing_to_one_fails(self, tmp_path):
        d = sim_config_to_hb_dict(_default_config())
        d["buy_amounts_pct"] = [0.9, 0.9]  # too high
        path = str(tmp_path / "bad.yml")
        with open(path, "w") as f:
            yaml.dump(d, f)
        result = validate_yaml_file(path)
        assert not result.valid

    def test_mismatched_list_lengths_fails(self, tmp_path):
        d = sim_config_to_hb_dict(_default_config())
        d["buy_spreads"] = [1.0, 2.0, 3.0]  # 3 spreads but 2 amounts
        path = str(tmp_path / "bad.yml")
        with open(path, "w") as f:
            yaml.dump(d, f)
        result = validate_yaml_file(path)
        assert not result.valid

    def test_macd_fast_not_less_than_slow_fails(self, tmp_path):
        d = sim_config_to_hb_dict(_default_config())
        d["macd_fast"] = 50
        d["macd_slow"] = 30
        path = str(tmp_path / "bad.yml")
        with open(path, "w") as f:
            yaml.dump(d, f)
        result = validate_yaml_file(path)
        assert not result.valid

    def test_nan_value_fails(self, tmp_path):
        d = sim_config_to_hb_dict(_default_config())
        d["buy_spreads"] = [float("nan"), 2.0]
        path = str(tmp_path / "bad.yml")
        with open(path, "w") as f:
            yaml.dump(d, f)
        result = validate_yaml_file(path)
        assert not result.valid

    def test_validation_mode_is_mirror(self, tmp_path):
        """Hummingbot not installed → mode == 'mirror'."""
        result = _export_and_validate(_default_config(), tmp_path)
        assert result.mode == "mirror"
