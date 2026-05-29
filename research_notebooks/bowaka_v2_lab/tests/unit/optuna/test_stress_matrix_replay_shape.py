"""Phase 1 (audit 2026-05-29 §8.5) — stress-matrix replay shape + artifact."""
from __future__ import annotations

import json
from dataclasses import dataclass

from bowaka_v2_lab.optuna.stress_matrix import (
    build_stress_matrix_payload,
    conservative_floor_result,
    replay_stress_matrix,
    write_stress_matrix_artifact,
)


@dataclass
class _FoldStub:
    fold_id: str
    net_return: float
    n_trades: int
    fill_rate: float


def _scorer(params, overrides):
    # Score degrades with slippage offset so the matrix has spread.
    offset = float(overrides.get("backtest.slippage_bps_offset", 0))
    nr = 0.05 - offset / 10_000.0
    folds = [
        _FoldStub("f0", nr, 12, 0.98),
        _FoldStub("f1", nr + 0.01, 10, 0.97),
    ]
    return nr, folds


def test_replay_has_48_points_and_artifact_validates(tmp_path) -> None:
    results = replay_stress_matrix(
        best_params={"exits.stop_pct": 0.02}, score_with_overrides=_scorer,
    )
    assert len(results) == 4 * 4 * 3 == 48

    cf = conservative_floor_result(results)
    assert cf is not None
    assert cf.point.slippage_bps_offset == 50
    assert cf.point.spread_multiplier == 2.0
    assert cf.point.cost_stress == "conservative"

    payload = build_stress_matrix_payload(results, best_params={"exits.stop_pct": 0.02})
    assert len(payload["matrix"]) == 48
    assert payload["conservative_floor"] is not None

    out = write_stress_matrix_artifact(
        results, tmp_path / "stress_matrix.json", best_params={"exits.stop_pct": 0.02},
    )
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert len(loaded["matrix"]) == 48
    assert loaded["best_params"] == {"exits.stop_pct": 0.02}
