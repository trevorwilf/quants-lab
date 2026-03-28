"""Comprehensive notebook wiring tests per quant expert review.

These tests verify that validation results computed in the sweep loop
are correctly forwarded to run_stop_ship_checks() and generate_report().
They also check for data leakage, holdout overlap, and objective version
consistency.
"""
import json
import re
import pytest
from pathlib import Path

NB_DIR = Path(__file__).resolve().parents[2] / "notebooks" / "pmm_dynamic"

SWEEP_NOTEBOOKS = [
    ("pmm_dynamic_multi_exchange_sweep_mexc_nonkyc.ipynb", 8),
    ("pmm_dynamic_multi_pair_sweep.ipynb", 8),
    ("pmm_dynamic_single_pair_sweep_mexc_xmr_usdt.ipynb", 7),
]


def _get_sweep_source(nb_name, cell_idx):
    path = NB_DIR / nb_name
    if not path.exists():
        pytest.skip(f"Notebook not found: {path}")
    with open(path, encoding="utf-8") as f:
        nb = json.load(f)
    return "".join(nb["cells"][cell_idx]["source"])


# ── Test group 1: run_stop_ship_checks receives all validation kwargs ──

REQUIRED_STOP_SHIP_KWARGS = [
    "dataset_audit=",
    "validation_result=",
    "holdout_report=",
    "sensitivity_penalty=",
    "recent_window_result=",
    "parity_result=",
    "cluster_report=",
    "long_parity_result=",
]

@pytest.mark.parametrize("nb_name,cell_idx", SWEEP_NOTEBOOKS)
def test_stop_ship_receives_all_validation_kwargs(nb_name, cell_idx):
    src = _get_sweep_source(nb_name, cell_idx)
    # Extract the run_stop_ship_checks call
    match = re.search(r'checks\s*=\s*run_stop_ship_checks\((.*?)\)', src, re.DOTALL)
    assert match, f"{nb_name}: run_stop_ship_checks call not found"
    call_text = match.group(1)
    missing = [kw for kw in REQUIRED_STOP_SHIP_KWARGS if kw not in call_text]
    assert not missing, f"{nb_name}: run_stop_ship_checks missing kwargs: {missing}"


# ── Test group 2: generate_report receives all validation kwargs ──

REQUIRED_REPORT_KWARGS = [
    "holdout_report=",
    "dataset_audit=",
    "sensitivity_report=",
    "recent_window_result=",
    "cluster_report=",
    "yaml_validation_result=",
    "dataset_slices=",
    "parity_result=",
    "long_parity_result=",
]

@pytest.mark.parametrize("nb_name,cell_idx", SWEEP_NOTEBOOKS)
def test_generate_report_receives_all_validation_kwargs(nb_name, cell_idx):
    src = _get_sweep_source(nb_name, cell_idx)
    # Find generate_report( and capture through its closing )
    idx = src.index("generate_report(")
    # Count parens to find matching close
    depth = 0
    for i, ch in enumerate(src[idx:], idx):
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                call_text = src[idx:i+1]
                break
    else:
        pytest.fail(f"{nb_name}: could not find closing paren for generate_report")
    missing = [kw for kw in REQUIRED_REPORT_KWARGS if kw not in call_text]
    assert not missing, f"{nb_name}: generate_report missing kwargs: {missing}"


# ── Test group 3: stress selection uses dev_candles, not candles ──

@pytest.mark.parametrize("nb_name,cell_idx", SWEEP_NOTEBOOKS)
def test_stress_selection_uses_dev_candles(nb_name, cell_idx):
    src = _get_sweep_source(nb_name, cell_idx)
    match = re.search(r'select_best_stressed_candidate\(\s*top_candidates,\s*(\w+),', src)
    assert match, f"{nb_name}: select_best_stressed_candidate call not found"
    data_arg = match.group(1)
    assert data_arg == "dev_candles", (
        f"{nb_name}: select_best_stressed_candidate uses '{data_arg}' instead of 'dev_candles' — "
        "this leaks future data into finalist selection"
    )


# ── Test group 4: holdout uses dataset_slices when available ──

@pytest.mark.parametrize("nb_name,cell_idx", SWEEP_NOTEBOOKS)
def test_holdout_uses_dataset_slices(nb_name, cell_idx):
    src = _get_sweep_source(nb_name, cell_idx)
    # Should reference dataset_slices.holdout_candles, not split_holdout(candles, ...)
    # The corrected code uses dataset_slices when available and falls back to split_holdout
    assert "dataset_slices.holdout_candles" in src or "dataset_slices is not None" in src, (
        f"{nb_name}: holdout should use dataset_slices.holdout_candles when release gating is enabled"
    )


# ── Test group 5: walk-forward passes objective_version ──

@pytest.mark.parametrize("nb_name,cell_idx", SWEEP_NOTEBOOKS)
def test_walkforward_passes_objective_version(nb_name, cell_idx):
    src = _get_sweep_source(nb_name, cell_idx)
    match = re.search(r'run_walk_forward\((.*?)\)', src, re.DOTALL)
    assert match, f"{nb_name}: run_walk_forward call not found"
    call_text = match.group(1)
    assert "objective_version=" in call_text, (
        f"{nb_name}: run_walk_forward must pass objective_version=OBJECTIVE_VERSION "
        "to ensure consistency with Phase 1 and stress evaluations"
    )


# ── Test group 6: walk-forward uses val_config (not best_config) ──

@pytest.mark.parametrize("nb_name,cell_idx", SWEEP_NOTEBOOKS)
def test_walkforward_uses_val_config(nb_name, cell_idx):
    src = _get_sweep_source(nb_name, cell_idx)
    match = re.search(r'run_walk_forward\((.*?)\)', src, re.DOTALL)
    assert match, f"{nb_name}: run_walk_forward call not found"
    call_text = match.group(1)
    assert "config=val_config" in call_text, (
        f"{nb_name}: run_walk_forward should use val_config (validation mode), "
        "not best_config (screening mode)"
    )


# ── Test group 7: validate_yaml_file is actually called ──

@pytest.mark.parametrize("nb_name,cell_idx", SWEEP_NOTEBOOKS)
def test_yaml_validation_is_called(nb_name, cell_idx):
    src = _get_sweep_source(nb_name, cell_idx)
    assert "validate_yaml_file(" in src and "validation_result" in src, (
        f"{nb_name}: validate_yaml_file must be called and result stored "
        "in validation_result for forwarding to checks/report"
    )


# ── Test group 8: generate_report receives run_provenance ──

@pytest.mark.parametrize("nb_name,cell_idx", SWEEP_NOTEBOOKS)
def test_generate_report_receives_provenance(nb_name, cell_idx):
    src = _get_sweep_source(nb_name, cell_idx)
    idx = src.index("generate_report(")
    depth = 0
    for i, ch in enumerate(src[idx:], idx):
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                call_text = src[idx:i+1]
                break
    assert "run_provenance=" in call_text, (
        f"{nb_name}: generate_report should include run_provenance for auditability"
    )


# ── Test group 9: config guard present at top of sweep cell ──

@pytest.mark.parametrize("nb_name,cell_idx", SWEEP_NOTEBOOKS)
def test_config_guard_present(nb_name, cell_idx):
    src = _get_sweep_source(nb_name, cell_idx)
    assert "_required_config" in src, (
        f"{nb_name}: sweep cell should have a config guard to catch missing configuration variables"
    )
