"""Audit 2026-05-29 §A.5 / Appendix E — degraded folds invalidate the study.

``_run_validation_folds`` appends a ``_degraded_fold`` (fold_status="degraded")
when a fold's backtest raises a non-structural exception. Pre-remediation the
valid-trial filter accepted the degraded fold's finite sentinel score as a
real datapoint. Now: any trial with a degraded fold is rejected by the
per-trial filter, and the study-validity gate flags the whole study with
``DEGRADED_FOLDS_PRESENT`` and raises — even though every trial's value is
finite (not the _FAILED_TRIAL_SCORE sentinel).
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from bowaka_v2_lab.devtools.wf_lake import (
    build_tiny_lake,
    write_walkforward_test_config,
)
from bowaka_v2_lab.optuna import walkforward_runner
from bowaka_v2_lab.optuna.errors import REASON_DEGRADED_FOLDS_PRESENT, OptunaStudyInvalidError
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study


def _write_cfg(tmp_path: Path, lab_root: Path) -> Path:
    lake = tmp_path / "lake"
    build_tiny_lake(
        lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
    )
    return write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=2,
    )


def _read_failed_artifact(tmp_path: Path) -> dict:
    candidates = sorted(tmp_path.rglob("optuna/*.json"))
    failed = []
    for p in candidates:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if d.get("status") == "failed":
            failed.append(d)
    assert failed, f"no failed-status artifact among {[c.name for c in candidates]}"
    return failed[0]


def test_degraded_fold_invalidates_study_despite_finite_values(
    tmp_path, lab_root, monkeypatch,
):
    cfg = _write_cfg(tmp_path, lab_root)

    def _one_degraded(trial_cfg, plan, **kwargs):
        from bowaka_v2_lab.optuna.objective import FoldResult

        folds = []
        for i in range(len(plan.splits)):
            if i == 0:
                # degraded sentinel fold (fold_status="degraded"), finite score
                folds.append(walkforward_runner._degraded_fold(f"f{i}"))
            else:
                folds.append(
                    FoldResult(
                        fold_id=f"f{i}", net_return=0.03, max_drawdown=0.1,
                        turnover=1.0, concentration=0.2, n_trades=7, fill_rate=1.0,
                    )
                )
        return folds

    monkeypatch.setattr(walkforward_runner, "_run_validation_folds", _one_degraded)

    with pytest.raises(OptunaStudyInvalidError) as ei:
        run_walkforward_study(cfg, allow_smoke=True)
    assert REASON_DEGRADED_FOLDS_PRESENT in str(ei.value)

    failed = _read_failed_artifact(tmp_path)
    assert failed["status"] == "failed"
    assert REASON_DEGRADED_FOLDS_PRESENT in failed["invalid_reasons"]
    assert failed["best_params"] == {}
