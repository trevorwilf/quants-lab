"""Phase 3 (audit 2026-05-29 §6.10 b) — constant-surface escalation logs mid-run.

When the last K = max(10, n_startup_trials) completed trial values are all
within 1e-6, the runner logs an escalation message (best-effort) so the
operator sees the suspected constant_objective_surface during the run.
"""
from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path

import yaml

from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake, write_walkforward_test_config
from bowaka_v2_lab.optuna import walkforward_runner
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study


def test_constant_surface_logs_escalation(tmp_path, lab_root, monkeypatch, caplog) -> None:
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=12,
    )
    doc = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    doc["optuna"]["n_startup_trials"] = 5  # -> K = max(10, 5) = 10
    cfg_path.write_text(yaml.safe_dump(doc), encoding="utf-8")

    def _ok_folds(trial_cfg, plan, **kwargs):
        from bowaka_v2_lab.optuna.objective import FoldResult

        return [
            FoldResult(fold_id=f"f{i}", net_return=0.0, max_drawdown=0.1,
                       turnover=1.0, concentration=0.2, n_trades=7, fill_rate=1.0)
            for i in range(len(plan.splits))
        ]

    def _const_objective(folds):
        from bowaka_v2_lab.optuna.objective import ObjectiveResult

        n = len(folds)
        return ObjectiveResult(objective=-1.5, median_fold_score=-1.5,
                               fold_scores=[-1.5] * n, penalty_breakdown={},
                               fold_variance=0.0, objective_terms={})

    monkeypatch.setattr(walkforward_runner, "_run_validation_folds", _ok_folds)
    monkeypatch.setattr(walkforward_runner, "compute_objective", _const_objective)

    with caplog.at_level(logging.INFO, logger="bowaka_v2_lab.optuna.walkforward_runner"):
        # smoke helper opts out of the constant-surface VALIDITY gate, so the
        # study completes; the escalation LOG still fires mid-run.
        run_walkforward_study(cfg_path, allow_smoke=True, incumbent_trial=False)

    assert "escalated to full_debug" in caplog.text
