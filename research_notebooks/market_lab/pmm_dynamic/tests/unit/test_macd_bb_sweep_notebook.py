"""Tests for the MACD-BB sweep notebook structure."""

import json
import pytest
from pathlib import Path


NOTEBOOK_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "notebooks" / "macd_bb" / "macd_bb_single_pair_sweep.ipynb"
)


@pytest.fixture
def notebook():
    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class TestNotebookStructure:
    def test_notebook_exists(self):
        assert NOTEBOOK_PATH.exists(), f"Notebook not found: {NOTEBOOK_PATH}"

    def test_has_14_cells(self, notebook):
        assert len(notebook["cells"]) == 14

    def test_cell_types_alternate(self, notebook):
        """Cells should follow md/code/md/code pattern."""
        expected_types = [
            "markdown", "code",     # 0-1: title, bootstrap
            "markdown", "code",     # 2-3: config header, config
            "code",                 # 4: preflight
            "markdown", "code",     # 5-6: discovery header, discovery
            "markdown", "code",     # 7-8: sweep header, main sweep
            "markdown", "code",     # 9-10: results header, summary
            "markdown", "code",     # 11-12: detail header, detail
            "markdown",             # 13: next steps
        ]
        actual_types = [c["cell_type"] for c in notebook["cells"]]
        assert actual_types == expected_types

    def test_nbformat(self, notebook):
        assert notebook["nbformat"] == 4


class TestNoFictionalImports:
    def test_no_fictional_loader(self, notebook):
        for i, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] == "code":
                src = "".join(cell["source"])
                assert "pmm_lab.data.loader" not in src, f"Cell {i} uses fictional pmm_lab.data.loader"

    def test_no_fictional_audit(self, notebook):
        for i, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] == "code":
                src = "".join(cell["source"])
                assert "audit_candle_quality" not in src, f"Cell {i} uses fictional audit_candle_quality"

    def test_uses_real_mongo_loader(self, notebook):
        discovery_cell = notebook["cells"][6]
        source = "".join(discovery_cell["source"])
        assert "MongoCandleLoader" in source


class TestConfigGuards:
    def test_config_cell_has_key_params(self, notebook):
        config_cell = notebook["cells"][3]
        source = "".join(config_cell["source"])
        for param in ["CONNECTOR", "TRADING_PAIR",
                       "SEARCH_CONTROLLER_COMPAT", "VALIDATION_CONTROLLER_COMPAT",
                       "OBJECTIVE_VERSION", "N_TRIALS"]:
            assert param in source, f"Missing config param: {param}"


class TestSweepCell:
    def test_sweep_cell_calls_validate(self, notebook):
        sweep_cell = notebook["cells"][8]
        source = "".join(sweep_cell["source"])
        assert "validate_yaml_file" in source

    def test_sweep_cell_uses_strategy_name(self, notebook):
        sweep_cell = notebook["cells"][8]
        source = "".join(sweep_cell["source"])
        assert 'strategy_name="macd_bb"' in source

    def test_sweep_cell_uses_macd_bb_canonicalizer(self, notebook):
        sweep_cell = notebook["cells"][8]
        source = "".join(sweep_cell["source"])
        assert "canonicalize_macd_bb_params" in source

    def test_sweep_cell_uses_generic_sim_runner(self, notebook):
        sweep_cell = notebook["cells"][8]
        source = "".join(sweep_cell["source"])
        assert "GenericSimRunner" in source

    def test_sweep_cell_uses_export_macd_bb(self, notebook):
        sweep_cell = notebook["cells"][8]
        source = "".join(sweep_cell["source"])
        assert "export_macd_bb_yaml" in source

    def test_sweep_cell_uses_validate_candles(self, notebook):
        sweep_cell = notebook["cells"][8]
        source = "".join(sweep_cell["source"])
        assert "validate_candles" in source

    def test_sweep_cell_uses_split_for_release_gate(self, notebook):
        sweep_cell = notebook["cells"][8]
        source = "".join(sweep_cell["source"])
        assert "split_for_release_gate" in source
