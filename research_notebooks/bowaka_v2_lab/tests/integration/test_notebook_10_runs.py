"""papermill executes the real walk-forward notebook 10 against a tiny lake."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from .test_walkforward_runner import build_tiny_lake, write_test_config

_NB = Path(__file__).resolve().parents[2] / "notebooks" / "10_optuna_walkforward.ipynb"


@pytest.mark.slow
@pytest.mark.timeout(300)  # executes the notebook (the ~60-90s walk-forward study) — the
# 60s default would interrupt it; the slow Top-N sweep is gated off (RUN_TOPN_SWEEP=False).
def test_papermill_execute_notebook_10(tmp_path: Path, lab_root: Path) -> None:
    pm = pytest.importorskip("papermill")
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_test_config(
        lab_root / "configs" / "quarantined" / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf_nb.yml",
        lake=lake, symbols=["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=2,
    )
    out = tmp_path / "10_out.ipynb"
    # execution_timeout guards against a papermill-injection regression: if the
    # override did not take, the notebook would run the full real config.
    pm.execute_notebook(
        str(_NB),
        str(out),
        # MODE_OVERRIDE=None: the notebook default pins current_code_parity (IR is
        # infeasible on the real lake), but that runs the contract-parity gate, which a
        # synthetic smoke config can't satisfy. None lets FEED='synthetic' resolve to
        # smoke_fixture (the parity gate is skipped for smoke).
        parameters={"CONFIG_PATH": str(cfg_path), "N_TRIALS": 2, "FEED": "synthetic",
                    "RUN_TOPN_SWEEP": False, "MODE_OVERRIDE": None},
        cwd=str(lab_root),
        kernel_name="python3",
        execution_timeout=600,
    )
    assert out.is_file()
