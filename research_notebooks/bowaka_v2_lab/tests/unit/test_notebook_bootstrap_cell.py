"""Every notebook's first cell matches the bootstrap template."""
from __future__ import annotations

from pathlib import Path

import nbformat
import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "notebooks"))
from _notebook_common import BOOTSTRAP_CELL_SOURCE  # noqa: E402


_NOTEBOOK_DIR = Path(__file__).resolve().parents[2] / "notebooks"


def _notebooks() -> list[Path]:
    return sorted(p for p in _NOTEBOOK_DIR.glob("*.ipynb"))


@pytest.mark.parametrize("nb_path", _notebooks(), ids=lambda p: p.name)
def test_first_cell_is_bootstrap(nb_path: Path) -> None:
    nb = nbformat.read(str(nb_path), as_version=4)
    assert nb.cells, f"empty notebook: {nb_path}"
    first = nb.cells[0]
    assert first.cell_type == "code"
    assert first.source.strip() == BOOTSTRAP_CELL_SOURCE.strip()


@pytest.mark.parametrize("nb_path", _notebooks(), ids=lambda p: p.name)
def test_parameter_cell_is_tagged(nb_path: Path) -> None:
    """Cell 1 must carry the ``parameters`` tag, else papermill injects its
    overrides at the notebook top where the cell's own defaults clobber them."""
    nb = nbformat.read(str(nb_path), as_version=4)
    assert len(nb.cells) > 1, f"notebook has no parameter cell: {nb_path}"
    assert "parameters" in nb.cells[1].get("metadata", {}).get("tags", [])


def test_bootstrap_pins_repo_root_despite_stray_nested_research_notebooks(
    tmp_path: Path,
) -> None:
    """Regression (2026-05-29): the bootstrap must chdir to the REPO ROOT even
    when the lab dir itself carries a Makefile and a stray nested
    ``research_notebooks/`` — the confounders that made the old marker heuristic
    chdir one level too deep and break repo-root-relative CONFIG_PATH.
    """
    import subprocess

    repo = tmp_path / "myrepo"
    lab = repo / "research_notebooks" / "bowaka_v2_lab"
    (lab / "src" / "bowaka_v2_lab").mkdir(parents=True)
    (lab / "src" / "bowaka_v2_lab" / "__init__.py").write_text(
        '__version__ = "0.0.0-test"\n', encoding="utf-8")
    (lab / "Makefile").write_text("# lab makefile (confounder)\n", encoding="utf-8")
    (lab / "research_notebooks" / "bowaka_v2_lab").mkdir(parents=True)  # stray nest
    (repo / "research_notebooks" / "bowaka_common").mkdir(parents=True)  # repo marker
    (repo / "Makefile").write_text("# repo makefile\n", encoding="utf-8")
    nbdir = lab / "notebooks"
    nbdir.mkdir()

    script = BOOTSTRAP_CELL_SOURCE + "\nimport os\nprint('RESOLVED_CWD=' + os.getcwd())\n"
    r = subprocess.run(
        [sys.executable, "-c", script], cwd=str(nbdir),
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0, r.stderr
    line = next(ln for ln in r.stdout.splitlines() if ln.startswith("RESOLVED_CWD="))
    resolved = Path(line.split("=", 1)[1].strip()).resolve()
    assert resolved == repo.resolve(), (
        f"bootstrap chdir'd to {resolved}, expected the repo root {repo.resolve()}"
    )
