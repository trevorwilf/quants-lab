"""Every v2 notebook executes end-to-end via papermill (synthetic / fixture path).

Notebooks 05/10/11 have dedicated tests; this covers the rest. Each is papermilled
with a 3-day pinned config so the run is fast and independent of edits to the
shared smoke config.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_NB_DIR = Path(__file__).resolve().parents[2] / "notebooks"

_NOTEBOOKS = [
    "01_shared_data_inventory.ipynb",
    "02_universe_backfill_and_snapshot.ipynb",
    "03_volume_curve_build.ipynb",
    "04_intraday_event_replay.ipynb",
    "06_execution_cost_and_liquidity_study.ipynb",
    "07_ablation_and_delay_sensitivity.ipynb",
    "08_counterfactual_exits_and_holds.ipynb",
    "09_paper_vs_backtest_reconciliation.ipynb",
]


def _short_config(lab_root: Path, tmp_path: Path) -> Path:
    """The smoke config pinned to a 3-day range (fast, synthetic path)."""
    raw = yaml.safe_load((lab_root / "configs" / "bowaka_v2_backtest_smoke.yml").read_text(encoding="utf-8"))
    raw["backtest"]["start_date"] = "2024-10-01"
    raw["backtest"]["end_date"] = "2024-10-03"
    out = tmp_path / "nb_config.yml"
    out.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return out


@pytest.mark.slow
@pytest.mark.parametrize("nb_name", _NOTEBOOKS)
def test_notebook_executes(nb_name: str, tmp_path: Path, lab_root: Path) -> None:
    pm = pytest.importorskip("papermill")
    cfg = _short_config(lab_root, tmp_path)
    out = tmp_path / ("out_" + nb_name)
    pm.execute_notebook(
        str(_NB_DIR / nb_name),
        str(out),
        parameters={"CONFIG_PATH": str(cfg)},
        cwd=str(lab_root),
        kernel_name="python3",
        execution_timeout=600,
    )
    assert out.is_file()
