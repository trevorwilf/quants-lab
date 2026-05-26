"""``_run_validation_folds`` propagates ``StartupDataQualityError`` (does NOT degrade).

Speedup report §4 P0-A / §5.1 / Phase 0 task 4. The pre-remediation code
matched the bare ``RuntimeError`` against the broad ``except Exception`` and
returned ``_degraded_fold`` for every fold — masking the structural rejection
behind a numeric sentinel score. The runner's existing structural-exception
handler (``except structural: raise``) already binds ``DataQualityError``; the
new ``StartupDataQualityError`` is a subclass, so it propagates.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
import datetime as dt
from pathlib import Path

import pytest

import bowaka_v2_lab.optuna.walkforward_runner as runner
from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.data.data_quality import StartupDataQualityError
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard


@dataclass
class _StubSplit:
    train_start: dt.date
    train_end: dt.date
    val_start: dt.date
    val_end: dt.date


@dataclass
class _StubPlan:
    splits: list


def test_run_validation_folds_reraises_startup_dq_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Forcing the inner fold runner to raise ``StartupDataQualityError`` propagates."""
    log = logging.getLogger("test_phase0")
    plan = _StubPlan(splits=[
        _StubSplit(
            train_start=dt.date(2024, 1, 1), train_end=dt.date(2024, 2, 1),
            val_start=dt.date(2024, 2, 1), val_end=dt.date(2024, 3, 1),
        )
    ])
    paths = BowakaV2Paths(
        lab_root=tmp_path / "lab", data_root=tmp_path / "lab" / "data",
        artifact_root=tmp_path / "lab" / "artifacts", config_path=Path(""),
    )
    holdout_guard = HoldoutGuard(dt.date(2024, 4, 1), dt.date(2024, 5, 1))

    def _raise_startup_dq(*args, **kwargs):
        raise StartupDataQualityError(
            "current_code_parity run aborted: 2 required "
            "data-quality check(s) failed: adjustment_mismatch: ..."
        )

    monkeypatch.setattr(runner, "_run_fold_backtest_objective", _raise_startup_dq)
    monkeypatch.setattr(runner, "_run_fold_backtest", _raise_startup_dq)

    with pytest.raises(StartupDataQualityError, match="adjustment_mismatch"):
        runner._run_validation_folds(
            trial_cfg={"market_data": {"feed": "iex"}, "simulation": {"mode": "current_code_parity"}},
            plan=plan,
            lake_root=tmp_path / "lake", feed="iex",
            symbols=["AAA"], paths=paths, holdout_guard=holdout_guard, log=log,
            objective_artifact_mode="objective_minimal",
        )


def test_run_validation_folds_full_artifact_mode_also_reraises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The full-artifact path uses ``_run_fold_backtest`` — also propagates."""
    log = logging.getLogger("test_phase0_full")
    plan = _StubPlan(splits=[
        _StubSplit(
            train_start=dt.date(2024, 1, 1), train_end=dt.date(2024, 2, 1),
            val_start=dt.date(2024, 2, 1), val_end=dt.date(2024, 3, 1),
        )
    ])
    paths = BowakaV2Paths(
        lab_root=tmp_path / "lab", data_root=tmp_path / "lab" / "data",
        artifact_root=tmp_path / "lab" / "artifacts", config_path=Path(""),
    )
    holdout_guard = HoldoutGuard(dt.date(2024, 4, 1), dt.date(2024, 5, 1))

    def _raise(*args, **kwargs):
        raise StartupDataQualityError("structural fail")

    monkeypatch.setattr(runner, "_run_fold_backtest_objective", _raise)
    monkeypatch.setattr(runner, "_run_fold_backtest", _raise)

    with pytest.raises(StartupDataQualityError):
        runner._run_validation_folds(
            trial_cfg={"market_data": {"feed": "iex"}, "simulation": {"mode": "current_code_parity"}},
            plan=plan,
            lake_root=tmp_path / "lake", feed="iex",
            symbols=["AAA"], paths=paths, holdout_guard=holdout_guard, log=log,
            objective_artifact_mode="full",
        )
