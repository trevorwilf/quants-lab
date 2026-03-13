"""Tests for pmm_lab.export.hb_yaml — Hummingbot YAML export."""

import yaml
import pytest
from pathlib import Path

from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.export.hb_yaml import (
    sim_config_to_hb_dict, export_yaml, export_top_n, ExportParams,
)


def _default_config(**overrides):
    defaults = dict(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5],
        sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
    )
    defaults.update(overrides)
    return SimConfig(**defaults)


class TestSimConfigToHbDict:
    def test_export_produces_valid_yaml(self, tmp_path):
        """Export to temp file, load back → dict with expected keys."""
        config = _default_config()
        path = str(tmp_path / "test.yml")
        export_yaml(config, path)
        with open(path) as f:
            loaded = yaml.safe_load(f)
        assert isinstance(loaded, dict)
        assert "controller_name" in loaded
        assert "buy_spreads" in loaded

    def test_controller_name_pmm_dynamic(self):
        d = sim_config_to_hb_dict(_default_config())
        assert d["controller_name"] == "pmm_dynamic"

    def test_controller_type_market_making(self):
        d = sim_config_to_hb_dict(_default_config())
        assert d["controller_type"] == "market_making"

    def test_take_profit_order_type_integer(self):
        """take_profit_order_type exported as Hummingbot OrderType enum int (LIMIT=2)."""
        d = sim_config_to_hb_dict(_default_config())
        assert isinstance(d["take_profit_order_type"], int)
        assert d["take_profit_order_type"] == 2  # LIMIT

    def test_take_profit_order_type_market(self):
        """MARKET → 1."""
        config = _default_config(take_profit_order_type="MARKET")
        d = sim_config_to_hb_dict(config)
        assert d["take_profit_order_type"] == 1

    def test_manual_kill_switch_false(self):
        d = sim_config_to_hb_dict(_default_config())
        assert d["manual_kill_switch"] is False

    def test_trailing_stop_nested_dict(self):
        d = sim_config_to_hb_dict(_default_config())
        assert isinstance(d["trailing_stop"], dict)
        assert "activation_price" in d["trailing_stop"]
        assert "trailing_delta" in d["trailing_stop"]

    def test_candles_config_empty_list(self):
        d = sim_config_to_hb_dict(_default_config())
        assert d["candles_config"] == []

    def test_amounts_renormalized(self):
        """buy_side_weight=0.7 → sum(buy_amounts_pct) + sum(sell_amounts_pct) ≈ 1.0."""
        config = _default_config(buy_side_weight=0.7)
        d = sim_config_to_hb_dict(config)
        total = sum(d["buy_amounts_pct"]) + sum(d["sell_amounts_pct"])
        assert abs(total - 1.0) < 0.001

    def test_asymmetric_list_lengths(self):
        """3 buy levels, 5 sell levels → correct lengths."""
        config = _default_config(
            buy_spreads=[1.0, 2.0, 4.0],
            sell_spreads=[1.0, 2.0, 3.0, 4.0, 5.0],
            buy_amounts_pct=[0.33, 0.33, 0.34],
            sell_amounts_pct=[0.2, 0.2, 0.2, 0.2, 0.2],
        )
        d = sim_config_to_hb_dict(config)
        assert len(d["buy_spreads"]) == 3
        assert len(d["sell_spreads"]) == 5
        assert len(d["buy_amounts_pct"]) == 3
        assert len(d["sell_amounts_pct"]) == 5

    def test_keys_sorted_alphabetically(self, tmp_path):
        """YAML keys appear in alphabetical order."""
        config = _default_config()
        path = str(tmp_path / "sorted.yml")
        export_yaml(config, path)
        with open(path) as f:
            content = f.read()
        # Extract top-level keys from YAML (lines that start at column 0 with a key)
        keys = []
        for line in content.split("\n"):
            if line and not line.startswith(" ") and not line.startswith("-") and ":" in line:
                keys.append(line.split(":")[0])
        assert keys == sorted(keys)

    def test_metadata_file_created(self, tmp_path):
        """Export with metadata → .meta.yml exists."""
        config = _default_config()
        path = str(tmp_path / "with_meta.yml")
        export_yaml(config, path, metadata={"study": "test", "score": 1.5})
        meta_path = Path(path).with_suffix(".meta.yml")
        assert meta_path.exists()

    def test_export_top_n(self, tmp_path):
        """Export 3 configs → 3 YAML files."""
        configs = [
            (_default_config(), {"objective_score": 1.0}),
            (_default_config(), {"objective_score": 0.8}),
            (_default_config(), {"objective_score": 0.6}),
        ]
        paths = export_top_n(configs, str(tmp_path), study_name="test_study")
        assert len(paths) == 3
        for p in paths:
            assert Path(p).exists()
