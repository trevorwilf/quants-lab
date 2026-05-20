"""papermill executes notebook 10 on smoke config; exit 0."""
from __future__ import annotations

from pathlib import Path

import pytest


_NB = Path(__file__).resolve().parents[2] / "notebooks" / "10_optuna_walkforward.ipynb"


@pytest.mark.slow
def test_papermill_execute_notebook_10(tmp_path: Path, lab_root: Path) -> None:
    pm = pytest.importorskip("papermill")
    out = tmp_path / "10_out.ipynb"
    pm.execute_notebook(
        str(_NB),
        str(out),
        parameters={"CONFIG_PATH": str(lab_root / "configs" / "bowaka_v2_walkforward_optuna.yml"),
                     "N_TRIALS": 3},
        cwd=str(lab_root),
        kernel_name="python3",
    )
    assert out.is_file()
