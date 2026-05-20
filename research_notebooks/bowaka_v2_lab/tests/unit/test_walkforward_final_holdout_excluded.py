"""Training and validation windows never overlap the final holdout."""
from __future__ import annotations

import datetime as _dt

from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits


def test_holdout_disjoint_from_all_splits() -> None:
    plan = build_walkforward_splits(
        full_start=_dt.date(2023, 1, 1), full_end=_dt.date(2024, 12, 31),
        train_months=9, val_months=1, final_holdout_months=2,
    )
    for s in plan.splits:
        assert s.val_end <= plan.final_holdout_start
        assert s.train_end <= plan.final_holdout_start
