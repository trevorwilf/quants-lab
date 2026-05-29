"""Phase 1 (audit 2026-05-29 §8.5) — ``stress-matrix --gate`` exits non-zero.

A sub-floor conservative result makes the gate fail; the CLI returns 1.
"""
from __future__ import annotations

import argparse
import json

from bowaka_v2_lab import cli
from bowaka_v2_lab.optuna import stress_matrix as sm_mod
from bowaka_v2_lab.optuna import walkforward_runner
from bowaka_v2_lab.optuna.stress_matrix import StressPoint, StressResult


def _sub_floor(*, best_params, score_with_overrides, **kwargs):
    return [StressResult(
        point=StressPoint(50, 2.0, "conservative"), fold_metrics=[],
        score=-0.01, n_trades_total=5, fill_rate_total=0.8,
    )]


def test_gate_exits_nonzero_when_conservative_floor_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        walkforward_runner, "build_validation_scorer",
        lambda *a, **k: (lambda p, o=None: (0.0, [])),
    )
    monkeypatch.setattr(sm_mod, "replay_stress_matrix", _sub_floor)
    bp = tmp_path / "bp.json"
    bp.write_text(json.dumps({"a": 1}), encoding="utf-8")
    out = tmp_path / "sm.json"
    args = argparse.Namespace(
        config="x.yml", best_params=str(bp), out=str(out), gate=True,
    )
    rc = cli._cmd_stress_matrix(args)
    assert rc == 1


def test_gate_exits_zero_when_floor_holds(tmp_path, monkeypatch) -> None:
    def _ok(*, best_params, score_with_overrides, **kwargs):
        return [StressResult(
            point=StressPoint(50, 2.0, "conservative"), fold_metrics=[],
            score=0.02, n_trades_total=20, fill_rate_total=0.95,
        )]

    monkeypatch.setattr(
        walkforward_runner, "build_validation_scorer",
        lambda *a, **k: (lambda p, o=None: (0.0, [])),
    )
    monkeypatch.setattr(sm_mod, "replay_stress_matrix", _ok)
    bp = tmp_path / "bp.json"
    bp.write_text(json.dumps({"a": 1}), encoding="utf-8")
    args = argparse.Namespace(
        config="x.yml", best_params=str(bp), out=str(tmp_path / "sm.json"), gate=True,
    )
    rc = cli._cmd_stress_matrix(args)
    assert rc == 0
