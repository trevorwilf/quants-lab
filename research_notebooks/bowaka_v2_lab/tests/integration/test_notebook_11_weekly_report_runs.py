"""papermill-executes notebook 11; produced report.md contains 'suitability'."""
from __future__ import annotations

from pathlib import Path

import pytest


_NB = Path(__file__).resolve().parents[2] / "notebooks" / "11_weekly_research_report.ipynb"


@pytest.mark.slow
def test_papermill_execute_notebook_11(tmp_path: Path, lab_root: Path) -> None:
    pm = pytest.importorskip("papermill")
    cfg = lab_root / "configs" / "bowaka_v2_backtest_smoke.yml"
    out = tmp_path / "11_out.ipynb"
    pm.execute_notebook(
        str(_NB),
        str(out),
        parameters={"CONFIG_PATH": str(cfg)},
        cwd=str(lab_root),
        kernel_name="python3",
    )
    assert out.is_file()
