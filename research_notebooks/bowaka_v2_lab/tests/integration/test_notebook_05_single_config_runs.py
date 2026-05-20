"""papermill-executes notebook 05 against the smoke config; exit 0."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest


_NB = Path(__file__).resolve().parents[2] / "notebooks" / "05_single_config_backtest.ipynb"


@pytest.mark.slow
def test_papermill_execute_notebook_05(tmp_path: Path, lab_root: Path) -> None:
    pm = pytest.importorskip("papermill")
    cfg = lab_root / "configs" / "bowaka_v2_backtest_smoke.yml"
    out = tmp_path / "05_out.ipynb"
    pm.execute_notebook(
        str(_NB),
        str(out),
        parameters={"CONFIG_PATH": str(cfg)},
        cwd=str(lab_root),
        kernel_name="python3",
    )
    assert out.is_file()
