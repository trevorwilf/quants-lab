"""Phase 5 — per-finalist parameter sensitivity table in the report."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bowaka_v2_lab.optuna.evaluate_finalists import (
    FinalistEvaluationConfig,
    evaluate_finalists,
)


@dataclass
class _StubFold:
    fold_id: str
    objective: float
    net_return: float = 0.0
    n_trades: int = 5


@dataclass
class _StubTrial:
    number: int
    value: float
    params: dict[str, Any]
    user_attrs: dict[str, Any] = field(default_factory=dict)


def _score(params):
    return float(params.get("exits.stop_pct", 0.025)), [_StubFold("f0", 1.0)]


def _sensitivity_scorer(params):
    """One row per tuned param with +5/-5 and +10/-10 deltas."""
    out = {}
    for name, base in params.items():
        if not isinstance(base, (int, float)):
            continue
        out[name] = {
            "+5%": 0.01, "-5%": -0.01, "+10%": 0.02, "-10%": -0.03,
            "median_delta": 0.0, "worst_delta": -0.03,
        }
    return out


def test_sensitivity_table_present_per_finalist(tmp_path: Path) -> None:
    trials = [
        _StubTrial(number=i, value=10.0 - i,
                   params={"exits.stop_pct": 0.025 + 0.001 * i,
                           "signals.rvol_so_far_min": 1.0 + 0.05 * i})
        for i in range(3)
    ]
    result = evaluate_finalists(
        completed_trials=trials,
        finalist_cfg=FinalistEvaluationConfig(top_k=3, include_incumbent=False),
        score_param_set=_score,
        sensitivity_scorer=_sensitivity_scorer,
        output_dir=tmp_path / "f",
    )
    fe = result.report["finalist_evaluation"]
    assert "sensitivity" in fe
    for row in result.finalists:
        sens = row["sensitivity"]
        # One entry per tuned numeric param, with both ±5% and ±10% deltas.
        for name in row["params"]:
            assert name in sens
            assert "+5%" in sens[name] and "-5%" in sens[name]
            assert "+10%" in sens[name] and "-10%" in sens[name]
