"""Structure tests for notebooks 03_prefilter_replay and 04_single_config_backtest."""

from __future__ import annotations

import re
from pathlib import Path

import nbformat
import pytest


def _read(p: Path):
    return nbformat.read(p, as_version=4)


def _src(nb) -> str:
    """Concat all code-cell sources for grep-style assertions."""
    return "\n".join(c.source or "" for c in nb.cells if c.cell_type == "code")


def _param_cell_src(nb) -> str:
    for c in nb.cells:
        if c.cell_type == "code" and "parameters" in (c.get("metadata", {}).get("tags") or []):
            return c.source or ""
    return ""


# ---------------------------------------------------------------------------
# Notebook 03
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def nb_03(bowaka_root):
    p = bowaka_root / "notebooks" / "03_prefilter_replay.ipynb"
    assert p.exists()
    return _read(p)


def test_notebook_03_has_parameters_cell_with_RUN_ID_REBUILD_DATA_ROOT(nb_03):
    src = _param_cell_src(nb_03)
    for name in ("RUN_ID", "REBUILD", "DATA_ROOT", "ARTIFACTS_ROOT",
                 "START_DATE", "END_DATE", "FEED",
                 "LOOKBACK_DAYS", "RVOL_MIN", "ATR_PCT_MIN"):
        assert re.search(rf"\b{name}\b\s*=", src), f"03 parameters missing {name}"


def test_notebook_03_imports_replay_prefilter_over_window(nb_03):
    assert "replay_prefilter_over_window" in _src(nb_03)


def test_notebook_03_imports_aggregate_prefilter_funnel(nb_03):
    assert "aggregate_prefilter_funnel" in _src(nb_03)


def test_notebook_03_imports_artifact_paths(nb_03):
    src = _src(nb_03)
    assert "ArtifactPaths" in src
    # Also reads/writes through the helpers.
    assert "save_parquet" in src
    assert "save_json" in src


def test_notebook_03_saves_candidates_artifact(nb_03):
    src = _src(nb_03)
    assert "paths.candidates" in src


def test_notebook_03_saves_funnel_artifact(nb_03):
    src = _src(nb_03)
    assert "paths.funnel" in src


def test_notebook_03_supports_fast_path(nb_03):
    """Fast-path: if REBUILD is False and artifacts exist, skip recomputation."""
    src = _src(nb_03)
    assert "REBUILD" in src
    assert "artifact_exists" in src


# ---------------------------------------------------------------------------
# Notebook 04
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def nb_04(bowaka_root):
    p = bowaka_root / "notebooks" / "04_single_config_backtest.ipynb"
    assert p.exists()
    return _read(p)


def test_notebook_04_has_parameters_cell_with_required_options(nb_04):
    src = _param_cell_src(nb_04)
    for name in ("RUN_ID", "DATA_ROOT", "ARTIFACTS_ROOT", "FEED", "REBUILD",
                 "ENTRY_RULE", "SLIPPAGE_BPS", "STOP_PCT", "TARGET_PCT",
                 "MAX_HOLD_DAYS", "PER_TRADE_NOTIONAL",
                 "MAX_CONCURRENT_POSITIONS", "MAX_TOTAL_ENTRIES_PER_DAY"):
        assert re.search(rf"\b{name}\b\s*=", src), f"04 parameters missing {name}"


def test_notebook_04_imports_BowakaPortfolioBacktester(nb_04):
    assert "BowakaPortfolioBacktester" in _src(nb_04)


def test_notebook_04_loads_candidates_from_notebook_03(nb_04):
    src = _src(nb_04)
    assert "paths.candidates" in src
    # Must use load_parquet (not bare pd.read_parquet which would be inconsistent).
    assert "load_parquet" in src


def test_notebook_04_saves_trades_summary_config_artifacts(nb_04):
    src = _src(nb_04)
    assert "paths.trades" in src
    assert "paths.summary" in src
    assert "paths.config" in src


def test_notebook_04_asserts_candidates_exist_before_running(nb_04):
    src = _src(nb_04)
    # The notebook must guard against running before notebook 03.
    assert "paths.candidates.exists()" in src or 'artifact_exists(paths, "candidates")' in src


def test_notebook_04_prints_funnel_for_sanity(nb_04):
    src = _src(nb_04)
    assert "paths.funnel" in src
