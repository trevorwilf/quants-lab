"""``run_promotion_candidate`` produces byte-equal artifacts on repeat runs.

Speedup report v2 §1.4 / §8.3 / Phase 5 task 5. The Stage C
deterministic-promotion rerun must produce a byte-equal
``promotion_artifact.json`` across runs — modulo the
``captured_at_utc`` timestamp (which is replaced with a placeholder
before comparison).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bowaka_v2_lab.optuna.evaluate_finalists import run_promotion_candidate


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


def _score(params):
    return 7.5, [_StubFold("f0", 7.5), _StubFold("f1", 7.6)]


def _holdout(params):
    return [_StubFold("holdout", 7.0)]


def _strip_timestamp(payload: dict) -> dict:
    if "captured_at_utc" in payload:
        payload["captured_at_utc"] = "PLACEHOLDER"
    # platform.node may vary across CI containers — normalise too.
    if isinstance(payload.get("platform"), dict):
        payload["platform"] = {k: "PLACEHOLDER" for k in payload["platform"]}
    return payload


def test_promotion_artifact_is_byte_equal_across_runs(tmp_path: Path) -> None:
    out1 = run_promotion_candidate(
        params={"x": 0.5, "y": 1.2},
        base_cfg={"market_data": {"feed": "iex"}},
        score_param_set=_score, holdout_scorer=_holdout,
        dataset_hash="DATASET", config_hash="CFG", code_hash="CODE",
        output_dir=tmp_path / "run1",
    )
    out2 = run_promotion_candidate(
        params={"x": 0.5, "y": 1.2},
        base_cfg={"market_data": {"feed": "iex"}},
        score_param_set=_score, holdout_scorer=_holdout,
        dataset_hash="DATASET", config_hash="CFG", code_hash="CODE",
        output_dir=tmp_path / "run2",
    )
    a = _strip_timestamp(json.loads(out1.read_text(encoding="utf-8")))
    b = _strip_timestamp(json.loads(out2.read_text(encoding="utf-8")))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
