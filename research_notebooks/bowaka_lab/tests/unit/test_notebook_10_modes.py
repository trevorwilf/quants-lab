"""Phase optuna-3: notebook 10 has smoke + production modes."""

from __future__ import annotations

from pathlib import Path

import nbformat
import pytest


@pytest.fixture(scope="module")
def notebook_10(bowaka_root: Path):
    nb_path = bowaka_root / "notebooks" / "10_optuna_walkforward.ipynb"
    assert nb_path.exists(), f"notebook 10 missing: {nb_path}"
    return nbformat.read(nb_path, as_version=4)


def _all_code_sources(nb) -> str:
    return "\n".join(c.source for c in nb.cells if c.cell_type == "code")


def test_notebook_10_parameters_cell_has_MODE_field(notebook_10):
    src = _all_code_sources(notebook_10)
    assert "MODE = " in src


def test_notebook_10_parameters_cell_has_SMOKE_N_TRIALS_and_PROD_N_TRIALS(notebook_10):
    src = _all_code_sources(notebook_10)
    assert "SMOKE_N_TRIALS" in src
    assert "PROD_N_TRIALS" in src


def test_notebook_10_parameters_cell_has_SMOKE_N_JOBS_and_PROD_N_JOBS(notebook_10):
    src = _all_code_sources(notebook_10)
    assert "SMOKE_N_JOBS" in src
    assert "PROD_N_JOBS" in src


def test_notebook_10_imports_optimize_study_for_notebook(notebook_10):
    src = _all_code_sources(notebook_10)
    assert "optimize_study_for_notebook" in src


def test_notebook_10_imports_get_storage_url(notebook_10):
    src = _all_code_sources(notebook_10)
    assert "get_storage_url" in src


def test_notebook_10_branches_on_MODE(notebook_10):
    src = _all_code_sources(notebook_10)
    assert 'if MODE == "smoke"' in src
    assert 'elif MODE == "production"' in src


def test_notebook_10_uses_smoke_objective_factory_from_candidates_path(notebook_10):
    src = _all_code_sources(notebook_10)
    assert "smoke_objective_factory_from_candidates_path" in src


def test_notebook_10_does_not_hardcode_OPTUNA_STORAGE_value(notebook_10):
    """The notebook must not embed a literal postgresql:// URL.

    Storage URLs must come from ``get_storage_url()`` (which reads
    ``OPTUNA_STORAGE`` at runtime) so the same notebook works in the
    Jupyter container (URL injected by docker compose) and from the host.
    """
    src = _all_code_sources(notebook_10)
    assert "postgresql://" not in src
    assert "postgresql+psycopg2://" not in src
