"""Conservative fold-level pruning is configured + behaves at the floor.

Walk-forward scan-matrix speedup Phase 3. The base workstation config AND the
matrix overlay both carry an ``optuna.pruning`` block:

    enabled: true
    min_completed_trials_before_pruning: 30   # respects the 25 TPE startup
    catastrophic_floor: -1.40

The floor is conservative on purpose: the incumbent objective is ~ -1.05 and a
no-trade / degenerate fold scores ~ -1.5, so -1.40 prunes a trial ONLY once its
running score is already in the no-trade neighbourhood after a fold — never a
trial that is plausibly promotable. These tests pin the configured values AND
that the existing ``_prune_cb`` honours that floor (the generic mechanism is
covered by tests/integration/test_pruning_catastrophic_floor.py; here we use
the SHIPPING floor value).
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import optuna
import pytest
import yaml

from bowaka_v2_lab.optuna.objective import FoldResult

_CONFIGS_DIR = Path(__file__).resolve().parents[3] / "configs"  # tests/unit/optuna -> lab root
_SHIPPING = [
    "bowaka_v2_actual_iex_current_code_optuna.workstation.yml",
    "bowaka_v2_actual_iex_current_code_optuna.workstation.matrix.yml",
]


@pytest.mark.parametrize("cfg_name", _SHIPPING)
def test_shipping_config_has_conservative_pruning(cfg_name):
    doc = yaml.safe_load((_CONFIGS_DIR / cfg_name).read_text(encoding="utf-8"))
    pruning = (doc.get("optuna") or {}).get("pruning") or {}
    assert pruning.get("enabled") is True, f"{cfg_name}: pruning must be enabled"
    assert int(pruning.get("min_completed_trials_before_pruning")) == 30, (
        f"{cfg_name}: must not prune inside the TPE startup window (>=30)"
    )
    floor = float(pruning.get("catastrophic_floor"))
    assert floor == pytest.approx(-1.40), f"{cfg_name}: floor must be -1.40"
    # Conservative band: below the incumbent (~-1.05) but at/above the
    # no-trade floor (~-1.5) so only doomed trials are killed.
    assert -1.5 <= floor < -1.05, (
        f"{cfg_name}: floor {floor} must sit between the no-trade floor (~-1.5) "
        "and the incumbent neighbourhood (~-1.05)"
    )


def _objective_with_floor(*, fold_results, n_completed, monkeypatch):
    """Build the walk-forward objective with the SHIPPING pruning block and a
    fake fold runner that drives ``_prune_cb`` over ``fold_results``."""
    import bowaka_v2_lab.optuna.walkforward_runner as wf_mod
    from bowaka_v2_lab.optuna.objective import compute_objective
    from bowaka_v2_lab.optuna.walkforward_runner import make_walkforward_objective

    def fake_run_validation_folds(*args, **kwargs):
        cb = kwargs.get("prune_callback")
        out = []
        for i, fr in enumerate(fold_results):
            out.append(fr)
            if cb is not None:
                cb(i, compute_objective(out).objective)
        return out

    monkeypatch.setattr(wf_mod, "_run_validation_folds", fake_run_validation_folds)

    plan = MagicMock()
    plan.splits = [MagicMock(val_start=None, val_end=None) for _ in fold_results]
    obj = make_walkforward_objective(
        {"optuna": {"pruning": {
            "enabled": True, "min_completed_trials_before_pruning": 30,
            "catastrophic_floor": -1.40,
        }}},
        plan, lake_root=None, feed="iex", symbols=["AAA"],
        paths=MagicMock(), holdout_guard=MagicMock(), log=MagicMock(),
    )
    trial = MagicMock()
    trial.number = 7
    trial.report = MagicMock()
    trial.study = MagicMock()
    trial.study.get_trials = MagicMock(return_value=[
        MagicMock(state=optuna.trial.TrialState.COMPLETE) for _ in range(n_completed)
    ])
    return obj, trial


def _no_trade_fold(i: int) -> FoldResult:
    # A zero-trade fold -> objective lands in the ~-1.5 no-trade neighbourhood,
    # i.e. below the -1.40 floor.
    return FoldResult(
        fold_id=f"f{i}", net_return=-1.0, max_drawdown=1.0,
        turnover=0.0, concentration=0.0, n_trades=0,
    )


def _incumbent_like_fold(i: int) -> FoldResult:
    # A healthy fold (many trades, small positive return) -> well above -1.40.
    return FoldResult(
        fold_id=f"f{i}", net_return=0.05, max_drawdown=0.02,
        turnover=0.0, concentration=0.0, n_trades=40,
    )


def test_prune_fires_below_configured_floor(monkeypatch):
    obj, trial = _objective_with_floor(
        fold_results=[_no_trade_fold(0), _no_trade_fold(1)],
        n_completed=40, monkeypatch=monkeypatch,
    )
    with pytest.raises(optuna.TrialPruned):
        obj(trial)


def test_prune_spares_incumbent_neighbourhood(monkeypatch):
    obj, trial = _objective_with_floor(
        fold_results=[_incumbent_like_fold(0), _incumbent_like_fold(1)],
        n_completed=40, monkeypatch=monkeypatch,
    )
    obj(trial)  # must NOT raise — a promotable trial is never pruned


def test_prune_noop_inside_startup_window(monkeypatch):
    # Even a no-trade trial is spared before 30 completed trials.
    obj, trial = _objective_with_floor(
        fold_results=[_no_trade_fold(0)],
        n_completed=10, monkeypatch=monkeypatch,
    )
    obj(trial)  # must NOT raise
    trial.report.assert_not_called()
