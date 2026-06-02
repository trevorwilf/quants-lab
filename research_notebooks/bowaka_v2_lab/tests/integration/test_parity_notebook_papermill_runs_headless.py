"""End-to-end: papermill executes notebook 13 against the operator's real lake.

Skip-guarded: pyarrow + papermill + production script + real lake. Does NOT
assert thresholds pass — just that the executed notebook runs to completion
and writes ``parity_report.md`` into the run-root.
"""
from __future__ import annotations

import datetime as _dt
import subprocess
import sys
from pathlib import Path

import pytest

_LAB = Path(__file__).resolve().parents[2]
_REPO_ROOT = _LAB.parents[1]
_NOTEBOOK = _LAB / "notebooks" / "13_lab_vs_production_parity.ipynb"
_PROD_SCRIPT = _LAB / "reference" / "source_strategy" / "scripts" / "bowaka_v2_backtest.py"

pytestmark = pytest.mark.integration


@pytest.mark.timeout(900)
@pytest.mark.parametrize("workers, end_date", [(1, "2026-05-19"), (2, "2026-05-20")])
def test_papermill_executes_notebook_and_writes_report(
    tmp_path: Path, workers: int, end_date: str,
) -> None:
    pytest.importorskip("pyarrow")
    pytest.importorskip("papermill")
    if not _NOTEBOOK.is_file():
        pytest.skip(f"notebook 13 missing at {_NOTEBOOK}")
    if not _PROD_SCRIPT.is_file():
        pytest.skip(f"production script not at {_PROD_SCRIPT} (run mirror)")
    try:
        from bowaka_common.marketdata.catalog import available_symbols
        from bowaka_common.marketdata.store import resolve_market_data_root
    except ImportError:
        pytest.skip("bowaka_common not importable")
    lake_root = resolve_market_data_root(None, create=False)
    syms = available_symbols(
        lake_root, timeframe="1d", vendor="alpaca",
        feed="iex", adjustment="split_adjusted",
    )
    if "AAPL" not in syms:
        pytest.skip("real lake not present (AAPL not in available symbols)")

    label = f"papermill_smoke_w{workers}_" + _dt.datetime.now(_dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    out_nb = tmp_path / "out.ipynb"
    # Run papermill from inside the lab dir so the notebook bootstrap can
    # walk UP from cwd to find ``src/bowaka_v2_lab/__init__.py``. The
    # bootstrap then chdirs to the repo root before any CONFIG_PATH
    # resolution, so the repo-root-relative defaults still work.
    proc = subprocess.run(
        [sys.executable, "-m", "papermill",
         str(_NOTEBOOK), str(out_nb),
         "-p", "START_DATE", "2026-05-19",
         "-p", "END_DATE", end_date,
         "-p", "MAX_UNIVERSE_SIZE", "5",
         "-p", "PARALLEL_WORKERS", str(workers),
         "-p", "RUN_LABEL", label],
        cwd=str(_LAB),
        capture_output=True, text=True, timeout=720, check=False,
    )
    assert proc.returncode == 0, (
        f"papermill failed.\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    assert out_nb.is_file()
    md_path = (
        _LAB / "artifacts" / "parity" / "lab_vs_production" / label
        / "parity_report.md"
    )
    assert md_path.is_file(), f"missing parity_report.md at {md_path}"
