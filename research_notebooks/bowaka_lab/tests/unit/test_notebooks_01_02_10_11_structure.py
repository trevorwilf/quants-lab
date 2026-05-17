"""Structure tests for the supporting notebooks (01, 02, 10, 11)."""

from __future__ import annotations

import re
from pathlib import Path

import nbformat
import pytest


def _read(p: Path):
    return nbformat.read(p, as_version=4)


def _src(nb) -> str:
    return "\n".join(c.source or "" for c in nb.cells if c.cell_type == "code")


def _param_cell_src(nb) -> str:
    for c in nb.cells:
        if c.cell_type == "code" and "parameters" in (c.get("metadata", {}).get("tags") or []):
            return c.source or ""
    return ""


# ---------------------------------------------------------------------------
# Notebook 01
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def nb_01(bowaka_root):
    p = bowaka_root / "notebooks" / "01_alpaca_asset_universe.ipynb"
    assert p.exists()
    return _read(p)


def test_notebook_01_has_parameters_with_MONGO_URI(nb_01):
    src = _param_cell_src(nb_01)
    assert re.search(r"\bMONGO_URI\b\s*=", src)
    assert re.search(r"\bDATA_ROOT\b\s*=", src)


def test_notebook_01_loads_asset_snapshot(nb_01):
    """Must read the snapshot from Parquet (and optionally Mongo)."""
    src = _src(nb_01)
    assert "snapshot_id" in src
    assert "assets.parquet" in src or "bowaka_asset_snapshots" in src


def test_notebook_01_includes_survivorship_bias_section(nb_01):
    src = _src(nb_01)
    assert "Survivorship" in src or "survivorship" in src


def test_notebook_01_does_NOT_call_alpaca_apis(nb_01):
    """01 is read-only — it must not call the Alpaca client."""
    src = _src(nb_01)
    for forbidden in ("TradingClient", "StockHistoricalDataClient", "AlpacaClient"):
        assert forbidden not in src, f"01 must be read-only; found {forbidden}"


# ---------------------------------------------------------------------------
# Notebook 02
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def nb_02(bowaka_root):
    p = bowaka_root / "notebooks" / "02_daily_bar_backfill.ipynb"
    assert p.exists()
    return _read(p)


def test_notebook_02_is_read_only(nb_02):
    """02 must not invoke the Alpaca fetcher API surface."""
    src = _src(nb_02)
    for forbidden in ("fetch_daily_bars(", "AlpacaClient(", "StockHistoricalDataClient(",
                      "TradingClient("):
        assert forbidden not in src, f"02 must be read-only; found {forbidden}"


def test_notebook_02_has_coverage_and_audit_sections(nb_02):
    src = _src(nb_02)
    assert "session_date" in src
    assert "bowaka_daily_bar_audits" in src


def test_notebook_02_documents_use_db_tools_for_fetching(nb_02):
    """The title or a markdown cell must direct the operator to db_tools."""
    sources = "\n".join(c.source or "" for c in nb_02.cells)
    assert "db_tools/bowaka_backfill" in sources


# ---------------------------------------------------------------------------
# Notebook 10
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def nb_10(bowaka_root):
    p = bowaka_root / "notebooks" / "10_optuna_walkforward.ipynb"
    assert p.exists()
    return _read(p)


def test_notebook_10_defaults_to_small_n_trials(nb_10):
    src = _param_cell_src(nb_10)
    # Pull the right-hand side of N_TRIALS = ...
    m = re.search(r"\bN_TRIALS\b\s*=\s*(\d+)", src)
    assert m, "10 parameters missing N_TRIALS"
    n = int(m.group(1))
    assert n <= 50, f"10 default N_TRIALS={n} too large for smoke; production runs go through run-task"


def test_notebook_10_warns_about_smoke_vs_production_use(nb_10):
    sources = "\n".join(c.source or "" for c in nb_10.cells)
    assert "smoke" in sources.lower()
    assert "production" in sources.lower() or "run-task" in sources.lower()


def test_notebook_10_saves_optuna_trials_and_best(nb_10):
    src = _src(nb_10)
    assert "paths.optuna_trials" in src
    assert "paths.optuna_best" in src


# ---------------------------------------------------------------------------
# Notebook 11
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def nb_11(bowaka_root):
    p = bowaka_root / "notebooks" / "11_weekly_research_report.ipynb"
    assert p.exists()
    return _read(p)


def test_notebook_11_aggregates_all_artifacts(nb_11):
    """Every artifact name must appear as paths.<name> reference."""
    src = _src(nb_11)
    for name in ("candidates", "trades", "summary", "funnel", "cf_entry",
                 "cf_exit", "signal_fade", "liquidity", "reconciliation",
                 "optuna_trials", "optuna_best"):
        assert f"paths.{name}" in src, f"11 missing paths.{name} reference"


def test_notebook_11_generates_weekly_report(nb_11):
    src = _src(nb_11)
    assert "generate_weekly_report" in src


def test_notebook_11_handles_missing_optional_artifacts_gracefully(nb_11):
    """Existence checks before every load."""
    src = _src(nb_11)
    assert "artifact_exists" in src
    # The notebook distinguishes required vs optional and only asserts on the
    # required set.
    assert "required" in src.lower()
    assert "optional" in src.lower()
