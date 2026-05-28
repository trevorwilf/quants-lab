"""Phase 5 — finalist report end-to-end with every expanded section enabled.

Speedup report v2 §11 task 8. Assembles a full finalist report with all the
Phase-5 section providers wired (stress, sensitivity, recent-window, DQ,
trade diagnostics, final-holdout audit) and asserts the resulting report's
``finalist_evaluation`` block carries every new top-level key + the
stop-ship decision.
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


pytestmark = pytest.mark.slow


@dataclass
class _Fold:
    fold_id: str
    objective: float
    net_return: float = 0.05
    max_drawdown: float = 0.02
    n_trades: int = 20
    fill_rate: float = 1.0
    quote_coverage: float = 1.0
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class _Trial:
    number: int
    value: float
    params: dict[str, Any]
    user_attrs: dict[str, Any] = field(default_factory=dict)


def _score(params):
    obj = float(params.get("exits.stop_pct", 0.025)) * 10.0
    return obj, [_Fold(f"f{i}", obj + 0.01 * i) for i in range(2)]


def _holdout(params):
    return [_Fold("holdout", float(params.get("exits.stop_pct", 0.025)) * 10.0 - 0.05)]


def _stress(params, overrides):
    return [_Fold("stress", 0.3), _Fold("stress1", 0.25)]


def _sensitivity(params):
    return {
        name: {"+5%": 0.01, "-5%": -0.01, "+10%": 0.02, "-10%": -0.03,
               "median_delta": 0.0, "worst_delta": -0.03}
        for name, v in params.items() if isinstance(v, (int, float))
    }


def _recent_window(params):
    return {"objective": 0.5, "n_trades": 14, "window_days": 28}


def _trade_diag(params):
    return {"total_trades": 60, "max_symbol_share": 0.12,
            "top_symbols": [{"symbol": "AAA", "share": 0.12}],
            "exit_type_counts": {"stop": 20, "target": 25, "time_stop": 15}}


def test_finalist_report_has_all_phase5_sections(tmp_path: Path) -> None:
    trials = [
        _Trial(number=i, value=10.0 - i,
               params={"exits.stop_pct": 0.025 + 0.001 * i,
                       "signals.rvol_so_far_min": 1.0 + 0.05 * i})
        for i in range(4)
    ]
    cfg = FinalistEvaluationConfig(
        top_k=4, include_incumbent=False, score_final_holdout=True,
        stress_scenarios=[
            {"name": "cost", "overrides": {"backtest.cost_stress": "aggressive"}},
            {"name": "spread", "overrides": {"execution.max_spread_bps": 50}},
        ],
    )
    result = evaluate_finalists(
        completed_trials=trials,
        finalist_cfg=cfg,
        score_param_set=_score,
        holdout_scorer=_holdout,
        stress_scorer=_stress,
        sensitivity_scorer=_sensitivity,
        recent_window_scorer=_recent_window,
        trade_diagnostics_provider=_trade_diag,
        data_quality_report={
            "feed": "sip", "checks": [{"name": "coverage", "status": "ok"}],
            "partial_tape_caveat": False,
            "per_fold": [{"fold_id": "f0", "quote_coverage_pct": 99.0}],
        },
        final_holdout_audit={"declare_finalist_read": "2026-05-27T00:00:00Z"},
        output_dir=tmp_path / "f",
    )
    payload = json.loads(result.report_path.read_text(encoding="utf-8"))
    fe = payload["finalist_evaluation"]
    for key in (
        "fold_local_stress_matrix", "top_k_clustering", "sensitivity",
        "recent_window", "data_quality", "trade_diagnostics",
        "final_holdout_audit", "stop_ship", "partial_tape_caveat",
    ):
        assert key in fe, f"finalist_evaluation missing {key!r}"
    # The stress matrix has the worst-case extracted.
    assert "worst_case_objective" in fe["fold_local_stress_matrix"]
    # Stop-ship ran and produced a decision dict.
    assert "passed" in fe["stop_ship"]
    # Recent window present (scorer returned metrics).
    assert fe["recent_window"].get("skipped") is not True
    # Final-holdout audit carries per-finalist drift.
    assert "per_finalist_drift" in fe["final_holdout_audit"]
