"""Phase 1 (audit 2026-05-29 §8.5) — the stress-matrix CLI writes the artifact.

The CLI loads finalist params, replays the matrix via the validation scorer,
and writes ``stress_matrix.json`` with the conservative-floor row. The scorer
construction is stubbed here (fast + deterministic); its real construction is
covered by the base-point parity test.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from bowaka_v2_lab import cli
from bowaka_v2_lab.optuna import walkforward_runner


@dataclass
class _Fold:
    fold_id: str
    net_return: float
    n_trades: int
    fill_rate: float


def _fake_builder(config_path, **kwargs):
    def scorer(params, overrides=None):
        return 0.03, [_Fold("f0", 0.03, 12, 0.96), _Fold("f1", 0.02, 9, 0.94)]
    return scorer


def test_stress_matrix_cli_writes_artifact_with_conservative_floor(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(walkforward_runner, "build_validation_scorer", _fake_builder)
    bp = tmp_path / "best_params.json"
    bp.write_text(json.dumps({"exits.stop_pct": 0.02}), encoding="utf-8")
    out = tmp_path / "stress_matrix.json"
    args = argparse.Namespace(
        config="ignored.yml", best_params=str(bp), out=str(out), gate=False,
    )
    rc = cli._cmd_stress_matrix(args)
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert len(payload["matrix"]) == 48
    assert payload["conservative_floor"] is not None
    assert payload["conservative_floor"]["cost_stress"] == "conservative"
