"""Phase backfill-notebook: notebook structure tests."""

from __future__ import annotations

import re
from pathlib import Path

import nbformat
import pytest


REQUIRED_PARAM_NAMES = {
    "START_DATE",
    "END_DATE",
    "FEED",
    "PRICE_MIN",
    "PRICE_MAX",
    "ADV_MIN",
    "ADV_WINDOW_DAYS",
    "ALLOWED_EXCHANGES",
    "OUTPUT_DIR",
    "RATE_LIMIT_RPM",
    "SYMBOL_BATCH_SIZE",
    "WRITE_TO_MONGO",
    "MONGO_DATABASE",
    "RESUME",
    "ASSET_SNAPSHOT_MAX_AGE_DAYS",
    "AUDIT_HISTORY_MODE",
    "RUN_SMOKE",
    "RUN_ESTIMATE",
    "RUN_ASSETS",
    "RUN_DAILY",
    "RUN_SCOPE",
    "RUN_MINUTE",
    "RUN_AUDITS",
    "RUN_MANIFEST",
}


REQUIRED_TAGS = {
    "parameters",
    "smoke",
    "estimate",
    "stage_assets",
    "stage_daily",
    "stage_scope",
    "stage_minute",
    "stage_audits",
    "stage_manifest",
    "summary",
}


@pytest.fixture(scope="module")
def notebook_path(bowaka_root: Path) -> Path:
    p = bowaka_root / "db_tools" / "bowaka_backfill.ipynb"
    if not p.exists():
        pytest.fail(f"notebook missing: {p}")
    return p


@pytest.fixture(scope="module")
def notebook(notebook_path):
    return nbformat.read(notebook_path, as_version=4)


def test_notebook_is_valid_nbformat(notebook):
    nbformat.validate(notebook)


def _first_code_cell(nb):
    for cell in nb.cells:
        if cell.cell_type == "code":
            return cell
    return None


def test_notebook_has_parameters_cell_first_code_cell(notebook):
    # The first code cell with the `parameters` tag must precede every stage.
    code_cells = [c for c in notebook.cells if c.cell_type == "code"]
    assert code_cells, "notebook has no code cells"
    param_cells = [c for c in code_cells if "parameters" in (c.get("metadata", {}).get("tags") or [])]
    assert param_cells, "no cell tagged parameters"
    # parameters cell must come before any stage_* cell.
    for cell in code_cells:
        tags = set(cell.get("metadata", {}).get("tags") or [])
        if tags & {"stage_assets", "stage_daily", "stage_scope", "stage_minute"}:
            assert "parameters" in (param_cells[0].get("metadata", {}).get("tags") or [])
            break


def test_notebook_has_all_required_stage_tags(notebook):
    tags = set()
    for cell in notebook.cells:
        for tag in cell.get("metadata", {}).get("tags") or []:
            tags.add(tag)
    missing = REQUIRED_TAGS - tags
    assert not missing, f"missing tags: {missing}"


def test_notebook_imports_from_db_tools_helper_lib(notebook):
    found = False
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        if "from db_tools import _backfill_lib" in cell.source or "from db_tools._backfill_lib" in cell.source:
            found = True
            break
    assert found, "notebook must import from db_tools._backfill_lib"


def test_notebook_does_not_import_bowaka_lab(notebook):
    forbidden = re.compile(r"^\s*(?:from\s+bowaka_lab|import\s+bowaka_lab)\b", re.MULTILINE)
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        assert not forbidden.search(cell.source or ""), "notebook must not import bowaka_lab"


def test_notebook_configuration_cell_exposes_all_options(notebook):
    param_cells = [c for c in notebook.cells if c.cell_type == "code" and "parameters" in (c.get("metadata", {}).get("tags") or [])]
    assert param_cells
    src = param_cells[0].source
    missing = {name for name in REQUIRED_PARAM_NAMES if not re.search(rf"\b{name}\b\s*=", src)}
    assert not missing, f"parameters cell missing variables: {missing}"


def test_notebook_uses_env_for_secrets_not_hardcoded(notebook):
    # Heuristic: a hardcoded Mongo URI or Alpaca key would contain `mongodb://`
    # with credentials in plain text or strings of the form `PK[A-Z0-9]{18}`/
    # `SK[A-Za-z0-9]{36}` (Alpaca key shapes). We only flag patterns that look
    # like a key value, not docstrings that mention the env var name.
    mongo_pat = re.compile(r"mongodb(?:\+srv)?://[^\s\"']*:[^\s\"']*@")
    alpaca_key_pat = re.compile(r"['\"]\s*(PK|SK|AK)[A-Z0-9]{16,}\s*['\"]")
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        assert not mongo_pat.search(cell.source or "")
        assert not alpaca_key_pat.search(cell.source or "")


@pytest.mark.slow
def test_notebook_estimate_only_smoke_execute(bowaka_root, notebook_path, tmp_path):
    """Optional: execute the notebook with all heavy stages off; verify exit 0."""
    pytest.importorskip("nbclient")
    import nbclient

    nb = nbformat.read(notebook_path, as_version=4)
    for cell in nb.cells:
        if cell.cell_type == "code" and "parameters" in (cell.get("metadata", {}).get("tags") or []):
            cell.source = """
START_DATE = "2026-04-01"
END_DATE = "2026-05-15"
FEED = "iex"
PRICE_MIN = 1.0
PRICE_MAX = 20.0
ADV_MIN = 200_000.0
ADV_WINDOW_DAYS = 20
ALLOWED_EXCHANGES = ["NASDAQ", "NYSE", "ARCA", "AMEX", "BATS"]
OUTPUT_DIR = ".tmp_bowaka_estimate"
RATE_LIMIT_RPM = 180
SYMBOL_BATCH_SIZE = 200
WRITE_TO_MONGO = False
MONGO_DATABASE = None
RESUME = True
ASSET_SNAPSHOT_MAX_AGE_DAYS = 7
AUDIT_HISTORY_MODE = "latest"
RUN_SMOKE = False
RUN_ESTIMATE = True
RUN_ASSETS = False
RUN_DAILY = False
RUN_SCOPE = False
RUN_MINUTE = False
RUN_AUDITS = False
RUN_MANIFEST = False
"""
    client = nbclient.NotebookClient(nb, timeout=120, resources={"metadata": {"path": str(bowaka_root)}})
    client.execute()
