"""Verify sweep notebooks are wired for strict validation."""
import json
import ast
import pytest
from pathlib import Path

NB_DIR = Path(__file__).resolve().parents[2] / "notebooks" / "pmm_dynamic"
SWEEP_NOTEBOOKS = [
    "pmm_dynamic_multi_pair_sweep.ipynb",
    "pmm_dynamic_single_pair_sweep_mexc_xmr_usdt.ipynb",
    "pmm_dynamic_multi_exchange_sweep_mexc_nonkyc.ipynb",
]

def _load_nb(name):
    path = NB_DIR / name
    if not path.exists():
        pytest.skip(f"Notebook not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _all_code_source(nb):
    return "".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")

@pytest.mark.parametrize("nb_name", SWEEP_NOTEBOOKS)
def test_objective_version_defined(nb_name):
    nb = _load_nb(nb_name)
    src = _all_code_source(nb)
    assert "OBJECTIVE_VERSION" in src, f"{nb_name} must define OBJECTIVE_VERSION"

@pytest.mark.parametrize("nb_name", SWEEP_NOTEBOOKS)
def test_candles_config_absent(nb_name):
    nb = _load_nb(nb_name)
    src = _all_code_source(nb)
    assert "candles_config" not in src, f"{nb_name} must not reference candles_config"

@pytest.mark.parametrize("nb_name", SWEEP_NOTEBOOKS)
def test_all_cells_compile(nb_name):
    nb = _load_nb(nb_name)
    errors = []
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] == "code":
            try:
                compile("".join(cell["source"]), f"{nb_name}:cell{i}", "exec")
            except SyntaxError as e:
                errors.append(f"Cell {i}, line {e.lineno}: {e.msg}")
    assert not errors, f"Syntax errors:\n" + "\n".join(errors)
