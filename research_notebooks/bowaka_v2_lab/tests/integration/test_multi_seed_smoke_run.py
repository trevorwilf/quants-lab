"""Phase 3 (audit 2026-05-29 §14.1) — multi-seed smoke run (opt-in, slow).

Runs two real walk-forward studies (one per seed) over a tiny synthetic lake
and selects the ensemble best. Opt-in via ``BOWAKA_RUN_MULTISEED_SMOKE=1``
because two full studies exceed the default per-test budget; it runs on the
operator's box (and gets a 600s budget there).
"""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

import pytest

from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake, write_walkforward_test_config
from bowaka_v2_lab.optuna.multi_seed import run_multi_seed_sweep, select_ensemble_best

pytestmark = pytest.mark.skipif(
    os.environ.get("BOWAKA_RUN_MULTISEED_SMOKE") != "1",
    reason="multi-seed smoke runs two full studies; opt-in via BOWAKA_RUN_MULTISEED_SMOKE=1",
)


@pytest.mark.timeout(600)
def test_multi_seed_sweep_selects_ensemble(tmp_path: Path, lab_root: Path) -> None:
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=2,
    )
    results = run_multi_seed_sweep(
        seeds=(1, 2), n_trials_per_seed=2, cfg_path=str(cfg),
        allow_smoke=True, incumbent_trial=False,
    )
    assert len(results) == 2
    ensemble = select_ensemble_best(results)
    assert ensemble.contributing_seeds
