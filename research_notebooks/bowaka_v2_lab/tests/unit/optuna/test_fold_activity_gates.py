"""Phase 3 (audit 2026-05-29 §9 Phase 5) — fold-level activity gates."""
from __future__ import annotations

from bowaka_v2_lab.optuna.objective import FoldActivityGates, fold_is_active_enough


def test_gate_flags_low_activity_folds() -> None:
    gates = FoldActivityGates(min_trades_per_fold=5, min_active_days_per_fold=3)
    folds = [
        {"n_trades": 10, "n_active_days": 5},   # active
        {"n_trades": 2, "n_active_days": 5},    # too few trades
        {"n_trades": 10, "n_active_days": 1},   # too few active days
        {"n_trades": 3, "n_active_days": 2},    # both below
        {"n_trades": 7, "n_active_days": 4},    # active
    ]
    actives = [fold_is_active_enough(f, gates) for f in folds]
    assert actives == [True, False, False, False, True]
    assert sum(1 for a in actives if not a) == 3


def test_default_gates() -> None:
    assert fold_is_active_enough({"n_trades": 5, "n_active_days": 3}) is True
    assert fold_is_active_enough({"n_trades": 4, "n_active_days": 3}) is False
