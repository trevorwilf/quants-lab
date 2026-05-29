"""Audit 2026-05-29 §6.5 / Appendix E.2 — constant-objective study fails closed.

When every completed trial ties at the same objective value (the -1.5
no-signal surface from the pasted Notebook 10 run), the runner must write a
``status: "failed"`` artifact with empty ``best_params`` / null
``best_value`` and ``invalid_reasons: ["CONSTANT_OBJECTIVE_SURFACE"]``, and
raise :class:`OptunaStudyInvalidError`. It must NOT report a "best trial".

The objective is forced to a constant value with non-empty trades so the
no-trade gate does not also fire — this isolates the constant-surface gate.
The study runs >= 10 trials because the constant-surface detector requires
>= 10 finite values before it will call a study degenerate (the same
insufficient-evidence floor asserted in the unit tests).
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
from bowaka_v2_lab.optuna.errors import REASON_CONSTANT_OBJECTIVE_SURFACE, OptunaStudyInvalidError
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study


def _write_cfg(tmp_path: Path, lab_root: Path, n_trials: int) -> Path:
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
        n_trials=n_trials,
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


def test_constant_objective_study_writes_failed_artifact_and_raises(
    tmp_path, lab_root, monkeypatch,
):
    import yaml

    cfg = _write_cfg(tmp_path, lab_root, n_trials=12)
    # The smoke-config helper opts OUT of the constant-surface gate (the
    # synthetic lake is constant by nature). This test is specifically
    # asserting that gate FIRES, so flip it back on.
    doc = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    doc["optuna"]["allow_constant_objective_surface"] = False
    cfg.write_text(yaml.safe_dump(doc), encoding="utf-8")

    def _ok_folds(trial_cfg, plan, **kwargs):
        from bowaka_v2_lab.optuna.objective import FoldResult

        return [
            FoldResult(
                fold_id=f"f{i}", net_return=0.0, max_drawdown=0.1,
                turnover=1.0, concentration=0.2, n_trades=7, fill_rate=1.0,
            )
            for i in range(len(plan.splits))
        ]

    def _const_objective(folds):
        from bowaka_v2_lab.optuna.objective import ObjectiveResult

        n = len(folds)
        return ObjectiveResult(
            objective=-1.5, median_fold_score=-1.5, fold_scores=[-1.5] * n,
            penalty_breakdown={}, fold_variance=0.0, objective_terms={},
        )

    monkeypatch.setattr(walkforward_runner, "_run_validation_folds", _ok_folds)
    monkeypatch.setattr(walkforward_runner, "compute_objective", _const_objective)

    with pytest.raises(OptunaStudyInvalidError) as ei:
        run_walkforward_study(cfg, allow_smoke=True)
    assert REASON_CONSTANT_OBJECTIVE_SURFACE in str(ei.value)

    failed = _read_failed_artifact(tmp_path)
    assert failed["status"] == "failed"
    assert failed["best_params"] == {}
    assert failed["best_value"] is None
    assert failed["invalid_reasons"] == [REASON_CONSTANT_OBJECTIVE_SURFACE]
