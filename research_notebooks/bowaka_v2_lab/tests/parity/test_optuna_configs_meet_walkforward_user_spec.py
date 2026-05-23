"""Every shipping ``*_optuna.yml`` honours the operator walk-forward spec.

Realism remediation 2 Phase 12 (CLAUDE conversation 2026-05-23). The operator
spec for walk-forward sizing is:

    final_holdout_months == 5     (fixed)
    train_months         >= 18    (minimum)
    val_months           >= 1
    holdout end          == lake max date

Plus the planner must actually produce at least one split for the configured
date range (the lake snapshot used by the Phase-12 generator gives 3 folds).

These tests pin the user spec to the committed YAML so a future regeneration
that silently regresses ``train_months`` below 18 or changes ``final_holdout``
fails CI loudly.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pytest
import yaml

from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits

_LAB_ROOT = Path(__file__).resolve().parents[2]

#: Operator-supplied minimums and fixed values (2026-05-23 conversation).
_USER_TRAIN_MIN = 18
_USER_FINAL_HOLDOUT = 5
_USER_VAL_MIN = 1
#: The lake snapshot the Phase-12 generator targets; the date range can only
#: be updated by re-running ``import-actual-config --purpose optuna`` after a
#: backfill (also bump the generator's hard-coded ``_OPTUNA_HEADER_SUFFIX``).
_LAKE_END_DATE = "2026-05-20"

_OPTUNA_CONFIGS = (
    "bowaka_v2_actual_iex_current_code_optuna.yml",
    "bowaka_v2_actual_iex_intended_realism_optuna.yml",
    "bowaka_v2_actual_sip_intended_realism_optuna.yml",
)


def _load(name: str) -> dict:
    return yaml.safe_load((_LAB_ROOT / "configs" / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", _OPTUNA_CONFIGS)
def test_walkforward_train_months_meets_user_minimum(name: str) -> None:
    cfg = _load(name)
    train = int(cfg["optuna"]["walkforward"]["train_months"])
    assert train >= _USER_TRAIN_MIN, (
        f"{name}: walkforward.train_months={train} is below the operator-"
        f"specified minimum of {_USER_TRAIN_MIN}. Raise it (and the lake "
        f"date range if needed) and regenerate via import-actual-config."
    )


@pytest.mark.parametrize("name", _OPTUNA_CONFIGS)
def test_walkforward_final_holdout_is_user_fixed_5(name: str) -> None:
    cfg = _load(name)
    holdout = int(cfg["optuna"]["walkforward"]["final_holdout_months"])
    assert holdout == _USER_FINAL_HOLDOUT, (
        f"{name}: walkforward.final_holdout_months={holdout}; the operator "
        f"spec pins this at {_USER_FINAL_HOLDOUT}."
    )


@pytest.mark.parametrize("name", _OPTUNA_CONFIGS)
def test_walkforward_val_months_at_least_one(name: str) -> None:
    cfg = _load(name)
    val = int(cfg["optuna"]["walkforward"]["val_months"])
    assert val >= _USER_VAL_MIN, (
        f"{name}: walkforward.val_months={val} (must be >= {_USER_VAL_MIN})"
    )


@pytest.mark.parametrize("name", _OPTUNA_CONFIGS)
def test_backtest_end_date_is_lake_max(name: str) -> None:
    """The holdout end is pinned to the lake max date (user spec: as close to
    the current date as the data set will allow)."""
    cfg = _load(name)
    assert str(cfg["backtest"]["end_date"]) == _LAKE_END_DATE, (
        f"{name}: backtest.end_date={cfg['backtest']['end_date']!r}; the "
        f"operator spec pins this at the lake max date ({_LAKE_END_DATE}). "
        f"After a backfill, update _OPTUNA_HEADER_SUFFIX in import_config.py "
        f"and this test, then regenerate via import-actual-config."
    )


@pytest.mark.parametrize("name", _OPTUNA_CONFIGS)
def test_walkforward_plan_has_at_least_one_split(name: str) -> None:
    """The configured date range + walk-forward sizing must produce >=1 fold.

    This is the failure that triggered the Phase-12 fix: the prior Phase-11
    dates (2024-01-01..2025-12-31, 24 months) plus the prior walkforward
    defaults (6+1+1) produced 0 splits at notebook-10 runtime.
    """
    cfg = _load(name)
    bt = cfg["backtest"]
    wf = cfg["optuna"]["walkforward"]
    plan = build_walkforward_splits(
        full_start=_dt.date.fromisoformat(str(bt["start_date"])),
        full_end=_dt.date.fromisoformat(str(bt["end_date"])),
        train_months=int(wf["train_months"]),
        val_months=int(wf["val_months"]),
        final_holdout_months=int(wf["final_holdout_months"]),
    )
    assert len(plan.splits) >= 1, (
        f"{name}: walk-forward plan has 0 splits "
        f"(backtest={bt['start_date']}..{bt['end_date']}, "
        f"train={wf['train_months']}, val={wf['val_months']}, "
        f"final_holdout={wf['final_holdout_months']}). "
        f"Widen the date range or shrink train/val/holdout."
    )
