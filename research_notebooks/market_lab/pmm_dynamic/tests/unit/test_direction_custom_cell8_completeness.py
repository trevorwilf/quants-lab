"""Cell-8 completeness tests for the four direction-custom sweep notebooks.

Per the full-parity prompt Section 5E: each notebook's cell 8 must be at
least 400 lines and mention every phase name of the PMM reference
lifecycle. These are content tests — they verify the SWEEP-LOOP CELL
contains the expected calls, not that it runs end-to-end (E2E execution
requires live Mongo and is covered elsewhere).
"""

import json
from pathlib import Path

import pytest

NB_DIR = Path(__file__).resolve().parents[2] / "notebooks" / "direction-custom"

NOTEBOOKS = [
    "mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb",
    "mean_reversion_bb_rsi_retest_sweep.ipynb",
    "ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb",
    "ema_regime_hold_retest_sweep.ipynb",
]

REQUIRED_PHASE_NAMES = [
    "validate_candles",
    "split_for_release_gate",
    "optimize_study_for_notebook",
    "select_best_stressed_candidate",
    "evaluate_recent_window",
    "evaluate_holdout",
    "compute_sensitivity",
    "analyze_top_k",
    "check_feature_parity_frozen",
    "run_walk_forward",
    "run_stop_ship_checks",
    "generate_report",
    "TqdmProgressCallback",
]


def _cell8_source(nb_name: str) -> str:
    with open(NB_DIR / nb_name, encoding="utf-8") as f:
        nb = json.load(f)
    src = nb["cells"][8]["source"]
    if isinstance(src, list):
        src = "".join(src)
    return src


@pytest.mark.parametrize("nb_name", NOTEBOOKS)
def test_cell8_at_least_400_lines(nb_name):
    src = _cell8_source(nb_name)
    assert len(src.splitlines()) >= 400, (
        f"{nb_name}: cell 8 has only {len(src.splitlines())} lines; expected >= 400"
    )


@pytest.mark.parametrize("nb_name", NOTEBOOKS)
@pytest.mark.parametrize("phase_name", REQUIRED_PHASE_NAMES)
def test_cell8_mentions_phase_name(nb_name, phase_name):
    src = _cell8_source(nb_name)
    assert phase_name in src, f"{nb_name}: missing phase name {phase_name!r}"


@pytest.mark.parametrize("nb_name", NOTEBOOKS)
def test_cell8_imports_tqdm(nb_name):
    src = _cell8_source(nb_name)
    assert "tqdm" in src, f"{nb_name}: cell 8 does not import tqdm"


@pytest.mark.parametrize("nb_name", NOTEBOOKS)
def test_cell8_uses_to_fingerprint(nb_name):
    src = _cell8_source(nb_name)
    assert "to_fingerprint" in src, f"{nb_name}: missing to_fingerprint dedup"


@pytest.mark.parametrize("nb_name", [
    "ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb",
    "ema_regime_hold_retest_sweep.ipynb",
])
def test_ema_cell8_passes_regime_candles(nb_name):
    """EMA notebooks must load regime_candles and pass them through the pipeline."""
    src = _cell8_source(nb_name)
    assert "regime_candles" in src, f"{nb_name}: EMA cell 8 missing regime_candles"
    assert "regime_interval" in src, f"{nb_name}: EMA cell 8 missing regime_interval"


def test_all_cells_still_parse_as_python():
    """The concatenated code cells of each notebook must still be valid Python."""
    import ast
    for nb_name in NOTEBOOKS:
        with open(NB_DIR / nb_name, encoding="utf-8") as f:
            nb = json.load(f)
        concat_lines = []
        for cell in nb["cells"]:
            if cell["cell_type"] != "code":
                continue
            src = cell["source"]
            if isinstance(src, list):
                src = "".join(src)
            concat_lines.append(src)
        concat = "\n\n".join(concat_lines)
        try:
            ast.parse(concat)
        except SyntaxError as e:
            pytest.fail(f"{nb_name}: concatenated code cells do not parse: {e}")
