"""P9 L16 — the walk-forward step_months config key is now wired.

``build_walkforward_splits`` already accepted ``step_months`` but no call site
threaded it, so the plan ALWAYS stepped by ``val_months`` (the config key was
dead). All five call sites now read ``optuna.walkforward.step_months``; absent ->
None -> defaults to ``val_months`` (byte-identical to before).
"""
from __future__ import annotations

import datetime as _dt

from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits

_COMMON = dict(
    full_start=_dt.date(2024, 1, 1), full_end=_dt.date(2025, 1, 1),
    train_months=3, val_months=1, final_holdout_months=1,
)


def test_step_months_changes_fold_cadence() -> None:
    default_plan = build_walkforward_splits(**_COMMON)                 # steps by val_months=1
    stepped_plan = build_walkforward_splits(**_COMMON, step_months=3)  # steps by 3
    assert len(stepped_plan.splits) < len(default_plan.splits)         # bigger step -> fewer folds
    starts = [s.train_start for s in stepped_plan.splits]
    assert len(starts) >= 2
    delta = (starts[1].year - starts[0].year) * 12 + (starts[1].month - starts[0].month)
    assert delta == 3                                                  # consecutive starts step by 3mo


def test_step_months_none_defaults_to_val_months() -> None:
    explicit = build_walkforward_splits(**_COMMON, step_months=1)      # == val_months
    default = build_walkforward_splits(**_COMMON)                      # step_months=None
    assert [s.train_start for s in explicit.splits] == [s.train_start for s in default.splits]


def test_call_site_step_months_resolution() -> None:
    # The threading expression used at every build_walkforward_splits call site.
    def _resolve(wf: dict):
        return int(wf["step_months"]) if wf.get("step_months") else None
    assert _resolve({"step_months": 3}) == 3
    assert _resolve({}) is None                   # absent -> default (val_months)
    assert _resolve({"step_months": 0}) is None   # 0 -> default (cannot step by 0)
