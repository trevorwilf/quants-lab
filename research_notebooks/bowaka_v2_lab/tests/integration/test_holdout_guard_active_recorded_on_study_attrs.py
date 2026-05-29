"""Phase 3 (audit 2026-05-29 §9 Phase 5) — a completed study records
holdout_guard_active=True in its metadata / user_attrs.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake, write_walkforward_test_config
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study


def test_smoke_study_records_holdout_guard_active(tmp_path: Path, lab_root: Path) -> None:
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=3,
    )
    result = run_walkforward_study(cfg, allow_smoke=True, incumbent_trial=False)
    assert result.get("study_metadata", {}).get("holdout_guard_active") is True
