"""Structure tests for the analysis notebooks (07, 08, 09)."""

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
# Notebook 07
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def nb_07(bowaka_root):
    p = bowaka_root / "notebooks" / "07_signal_fade_study.ipynb"
    assert p.exists()
    return _read(p)


def test_notebook_07_has_parameters_with_EXECUTE_THRESHOLDS(nb_07):
    src = _param_cell_src(nb_07)
    assert re.search(r"\bEXECUTE_THRESHOLDS\b\s*=", src)
    assert re.search(r"\bRTH_EVAL_TIME\b\s*=", src)
    assert re.search(r"\bAFTER_CLOSE_EVAL_TIME\b\s*=", src)


def test_notebook_07_imports_compute_signal_fade_score(nb_07):
    assert "compute_signal_fade_score" in _src(nb_07)


def test_notebook_07_saves_signal_fade_artifact(nb_07):
    assert "paths.signal_fade" in _src(nb_07)


def test_notebook_07_loads_trades_from_notebook_04(nb_07):
    src = _src(nb_07)
    assert "paths.trades" in src
    assert "load_parquet" in src


def test_notebook_07_includes_after_close_log_only(nb_07):
    """Both 15:45 and 16:05 ET should be evaluated; the 16:05 pass is log-only."""
    src = _src(nb_07)
    assert "after_close" in src or "AFTER_CLOSE_EVAL_TIME" in src


# ---------------------------------------------------------------------------
# Notebook 08
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def nb_08(bowaka_root):
    p = bowaka_root / "notebooks" / "08_liquidity_and_execution_quality.ipynb"
    assert p.exists()
    return _read(p)


def test_notebook_08_has_parameters_with_ADV_BUCKETS_and_SPREAD_BUCKETS(nb_08):
    src = _param_cell_src(nb_08)
    assert re.search(r"\bADV_BUCKETS\b\s*=", src)
    assert re.search(r"\bSPREAD_BUCKETS_BPS\b\s*=", src)


def test_notebook_08_includes_gap_through_analysis_section(nb_08):
    src = _src(nb_08)
    assert "stop_gap" in src
    assert "gap_through" in src or "gap_through_pct" in src


def test_notebook_08_saves_liquidity_artifact(nb_08):
    assert "paths.liquidity" in _src(nb_08)


def test_notebook_08_joins_candidates_for_adv(nb_08):
    src = _src(nb_08)
    assert "paths.candidates" in src
    assert "avg_dollar_volume" in src


# ---------------------------------------------------------------------------
# Notebook 09
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def nb_09(bowaka_root):
    p = bowaka_root / "notebooks" / "09_paper_vs_backtest_reconciliation.ipynb"
    assert p.exists()
    return _read(p)


def test_notebook_09_checks_BOWAKA_PAPER_LOGS_ROOT_env_var(nb_09):
    src = _src(nb_09)
    assert "BOWAKA_PAPER_LOGS_ROOT" in src


def test_notebook_09_imports_replay_comparator(nb_09):
    src = _src(nb_09)
    # The reconcile() function is the public reconciler.
    assert "from bowaka_lab.reconcile.replay_comparator import" in src
    assert "reconcile" in src


def test_notebook_09_saves_reconciliation_artifact(nb_09):
    assert "paths.reconciliation" in _src(nb_09)


def test_notebook_09_handles_missing_env_var_gracefully(nb_09):
    """Early-exit pattern: skip remaining cells when PAPER_LOGS_ROOT is None."""
    src = _src(nb_09)
    # The notebook prints a clear instruction when the env var is unset and
    # subsequent cells gate on a flag (skip_remaining).
    assert "skip_remaining" in src
