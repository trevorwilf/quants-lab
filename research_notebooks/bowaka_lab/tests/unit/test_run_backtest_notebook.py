"""Structure tests for the end-to-end ``run_backtest.ipynb`` notebook."""

from __future__ import annotations

import re
from pathlib import Path

import nbformat
import pytest


REQUIRED_PARAM_NAMES = {
    "DATA_ROOT",
    "ARTIFACTS_DIR",
    "RUN_ID",
    "START_DATE",
    "END_DATE",
    "FEED",
    "PRICE_MIN",
    "PRICE_MAX",
    "AVG_DOLLAR_VOLUME_MIN",
    "LOOKBACK_DAYS",
    "ATR_DAYS",
    "EMA_DAYS",
    "EMA_SLOPE_LOOKBACK",
    "RVOL_MIN",
    "ATR_PCT_MIN",
    "RANGE_EXPANSION_MIN",
    "CLOSE_LOCATION_MIN",
    "EMA_DISTANCE_MIN",
    "EMA_SLOPE_MIN",
    "ENTRY_RULE",
    "SLIPPAGE_BPS",
    "STOP_PCT",
    "TARGET_PCT",
    "MAX_HOLD_DAYS",
    "PER_TRADE_NOTIONAL",
    "MAX_CONCURRENT_POSITIONS",
    "MAX_TOTAL_ENTRIES_PER_DAY",
}


REQUIRED_TAGS = {
    "parameters",
    "config",
    "load_daily",
    "replay",
    "backtest",
    "diagnostics",
    "report",
}


@pytest.fixture(scope="module")
def notebook_path(bowaka_root: Path) -> Path:
    p = bowaka_root / "notebooks" / "run_backtest.ipynb"
    if not p.exists():
        pytest.fail(f"notebook missing: {p}")
    return p


@pytest.fixture(scope="module")
def notebook(notebook_path):
    return nbformat.read(notebook_path, as_version=4)


def test_notebook_is_valid_nbformat(notebook):
    nbformat.validate(notebook)


def test_first_code_cell_is_bootstrap(notebook):
    code_cells = [c for c in notebook.cells if c.cell_type == "code"]
    assert code_cells, "no code cells"
    first = code_cells[0]
    for phrase in ("Notebook bootstrap cell", 'src_path = bowaka_project / "src"', "import bowaka_lab"):
        assert phrase in first.source, f"bootstrap missing {phrase!r}"


def test_all_required_stage_tags(notebook):
    tags = set()
    for cell in notebook.cells:
        for t in cell.get("metadata", {}).get("tags") or []:
            tags.add(t)
    missing = REQUIRED_TAGS - tags
    assert not missing, f"missing tags: {missing}"


def test_parameters_cell_exposes_all_options(notebook):
    param_cells = [
        c for c in notebook.cells
        if c.cell_type == "code" and "parameters" in (c.get("metadata", {}).get("tags") or [])
    ]
    assert param_cells, "no parameters-tagged cell"
    src = param_cells[0].source
    missing = {name for name in REQUIRED_PARAM_NAMES if not re.search(rf"\b{name}\b\s*=", src)}
    assert not missing, f"parameters cell missing: {missing}"


def test_notebook_imports_replay_helper(notebook):
    found = False
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        if "replay_prefilter_over_window" in cell.source:
            found = True
            break
    assert found, "notebook must use replay_prefilter_over_window"


def test_notebook_imports_backtester(notebook):
    found = False
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        if "BowakaPortfolioBacktester" in cell.source:
            found = True
            break
    assert found, "notebook must use BowakaPortfolioBacktester"


def test_notebook_writes_report(notebook):
    found = False
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        if "generate_weekly_report" in cell.source:
            found = True
            break
    assert found, "notebook must call generate_weekly_report"


def test_no_hardcoded_secrets(notebook):
    mongo_pat = re.compile(r"mongodb(?:\+srv)?://[^\s\"']*:[^\s\"']*@")
    alpaca_key_pat = re.compile(r"['\"]\s*(PK|SK|AK)[A-Z0-9]{16,}\s*['\"]")
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        assert not mongo_pat.search(cell.source or ""), "hardcoded Mongo URI"
        assert not alpaca_key_pat.search(cell.source or ""), "hardcoded Alpaca key"
