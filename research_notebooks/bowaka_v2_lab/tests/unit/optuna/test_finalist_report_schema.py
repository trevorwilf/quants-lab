"""``evaluate_finalists`` writes a report carrying the required schema keys.

Speedup report v2 §9 / Phase 5 task 2. Required per-finalist keys:
``trial_number`` / ``params`` / ``is_incumbent`` / ``validation`` /
``holdout`` / ``stress`` / ``perturbation``. Top-level: ``finalists`` /
``incumbent``.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from bowaka_v2_lab.optuna.evaluate_finalists import (
    FinalistEvaluationConfig,
    evaluate_finalists,
)


@dataclass
class _StubFold:
    fold_id: str
    objective: float
    net_return: float = 0.0
    max_drawdown: float = 0.0
    worst_day_loss: float = 0.0
    fill_rate: float = 1.0
    quote_coverage: float = 1.0
    n_trades: int = 0
    turnover: float = 0.0
    concentration: float = 0.0
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class _StubTrial:
    number: int
    value: float
    params: dict[str, Any]
    user_attrs: dict[str, Any] = field(default_factory=dict)


def _make_trials() -> list[_StubTrial]:
    """4 stub trials with descending Optuna values + trial #0 as incumbent."""
    trials = [
        _StubTrial(
            number=i,
            value=10.0 - i,
            params={"signals.rvol_so_far_min": 1.0 + 0.1 * i},
        )
        for i in range(4)
    ]
    trials[0].user_attrs = {"incumbent_trial": True}
    return trials


def _score_param_set(params: dict[str, Any]) -> tuple[float, list]:
    """Return a deterministic ``(objective, folds)``."""
    objective = float(params.get("signals.rvol_so_far_min", 1.0))
    folds = [
        _StubFold(fold_id=f"f{i}", objective=objective + 0.01 * i)
        for i in range(2)
    ]
    return objective, folds


def _holdout_scorer(params: dict[str, Any]) -> list:
    return [_StubFold(fold_id="holdout", objective=float(params.get("signals.rvol_so_far_min", 1.0)) - 0.5)]


def _stress_scorer(params: dict[str, Any], overrides: dict[str, Any]) -> list:
    obj = float(params.get("signals.rvol_so_far_min", 1.0)) - 0.1
    return [_StubFold(fold_id="stress", objective=obj)]


def test_finalist_report_has_required_keys(tmp_path: Path) -> None:
    cfg = FinalistEvaluationConfig(
        top_k=2, include_incumbent=True, score_final_holdout=True,
        stress_scenarios=[{"name": "wider_spreads", "overrides": {}}],
    )
    result = evaluate_finalists(
        completed_trials=_make_trials(),
        finalist_cfg=cfg,
        score_param_set=_score_param_set,
        holdout_scorer=_holdout_scorer,
        stress_scorer=_stress_scorer,
        output_dir=tmp_path / "finalists",
    )
    assert result.report_path.is_file()
    payload = json.loads(result.report_path.read_text(encoding="utf-8"))
    assert "finalists" in payload
    assert isinstance(payload["finalists"], list)
    assert len(payload["finalists"]) >= 2  # top_k=2

    for row in payload["finalists"]:
        for key in ("trial_number", "params", "is_incumbent",
                    "validation", "holdout", "stress", "perturbation"):
            assert key in row, f"finalist row missing key {key!r}: {row}"
        # Validation sub-schema.
        v = row["validation"]
        for k in ("objective", "fold_scores", "net_return", "max_drawdown",
                  "n_trades", "fill_rate", "quote_coverage"):
            assert k in v, f"validation missing {k!r}"


def test_incumbent_appended_when_outside_top_k(tmp_path: Path) -> None:
    """``include_incumbent=True`` with ``top_k=2`` where incumbent is rank 4
    appends it as the third (or later) finalist with ``is_incumbent=True``.
    """
    trials = _make_trials()
    # Move incumbent flag to the LOWEST-value trial (so it's outside top_k=2).
    trials[0].user_attrs = {}
    trials[3].user_attrs = {"incumbent_trial": True}

    result = evaluate_finalists(
        completed_trials=trials,
        finalist_cfg=FinalistEvaluationConfig(top_k=2, include_incumbent=True),
        score_param_set=_score_param_set,
        output_dir=tmp_path / "f",
    )
    inc = [r for r in result.finalists if r["is_incumbent"]]
    assert len(inc) == 1
    assert inc[0]["trial_number"] == 3


def test_incumbent_not_appended_when_already_in_top_k(tmp_path: Path) -> None:
    """When the incumbent IS in top_k, it appears exactly once with the
    incumbent flag — not duplicated."""
    trials = _make_trials()
    # trial #0 is incumbent AND the best by value → it's in top_k=3.
    result = evaluate_finalists(
        completed_trials=trials,
        finalist_cfg=FinalistEvaluationConfig(top_k=3, include_incumbent=True),
        score_param_set=_score_param_set,
        output_dir=tmp_path / "f",
    )
    inc_rows = [r for r in result.finalists if r["is_incumbent"]]
    assert len(inc_rows) == 1
    assert inc_rows[0]["trial_number"] == 0
