"""Stress-matrix replay over the finalist parameters of a completed study.

Audit 2026-05-29 §8.5 / Phase 4a. Given a study's finalist ``best_params``,
replay the validation folds once per stress combination:

    slippage_bps_offset ∈ {0, 25, 50, 100}
    spread_multiplier   ∈ {1.0, 1.5, 2.0, 3.0}
    cost_stress         ∈ {base, conservative, severe}   (drives the ADV cap)

Total: 4 × 4 × 3 = 48 combinations. Each combination runs the EXISTING
simulator — the stress is applied entirely through the ``backtest.*`` config
keys threaded into the fill model (``slippage_bps_offset`` / ``spread_multiplier``
/ ``use_adv_bucket_caps``), so the base point ``(0, 1.0, "base")`` reproduces
the unstressed backtest byte-for-byte.

The replay is decoupled from the walk-forward plumbing via an injected
``score_with_overrides(params, overrides) -> (objective, folds)`` callable —
the same pattern :mod:`bowaka_v2_lab.optuna.robustness` uses. The walk-forward
runner exposes :func:`build_validation_scorer` to construct one from a config.
"""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

#: Default stress axes (audit §8.5).
DEFAULT_SLIPPAGE_OFFSETS: tuple[int, ...] = (0, 25, 50, 100)
DEFAULT_SPREAD_MULTIPLIERS: tuple[float, ...] = (1.0, 1.5, 2.0, 3.0)
DEFAULT_COST_STRESS_LEVELS: tuple[str, ...] = ("base", "conservative", "severe")

#: The conservative-floor point the paper-candidate gate keys on.
CONSERVATIVE_FLOOR = (50, 2.0, "conservative")


@dataclass(frozen=True)
class StressPoint:
    slippage_bps_offset: int
    spread_multiplier: float
    cost_stress: str

    def as_overrides(self) -> dict[str, Any]:
        """Config overrides that materialise this stress point in the sim."""
        return {
            "backtest.slippage_bps_offset": int(self.slippage_bps_offset),
            "backtest.spread_multiplier": float(self.spread_multiplier),
            "backtest.cost_stress": str(self.cost_stress),
            # The ADV-bucket partial-fill cap engages only under the matrix; at
            # cost_stress="base" every bucket caps at 1.0 so the base point is
            # still byte-identical to the unstressed run.
            "backtest.use_adv_bucket_caps": True,
        }

    @property
    def is_base(self) -> bool:
        return (
            self.slippage_bps_offset == 0
            and self.spread_multiplier == 1.0
            and self.cost_stress == "base"
        )


@dataclass(frozen=True)
class StressResult:
    point: StressPoint
    fold_metrics: list[Mapping[str, Any]]
    score: float                # median fold net return
    n_trades_total: int
    fill_rate_total: float

    def matches(self, slippage_bps_offset: int, spread_multiplier: float,
                cost_stress: str) -> bool:
        return (
            self.point.slippage_bps_offset == slippage_bps_offset
            and self.point.spread_multiplier == spread_multiplier
            and self.point.cost_stress == cost_stress
        )


def iter_stress_points(
    *,
    slippage_offsets: Sequence[int] = DEFAULT_SLIPPAGE_OFFSETS,
    spread_multipliers: Sequence[float] = DEFAULT_SPREAD_MULTIPLIERS,
    cost_stress_levels: Sequence[str] = DEFAULT_COST_STRESS_LEVELS,
) -> list[StressPoint]:
    return [
        StressPoint(int(s), float(m), str(c))
        for s, m, c in product(slippage_offsets, spread_multipliers, cost_stress_levels)
    ]


def _fold_metrics(folds: Sequence[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for f in folds:
        out.append({
            "fold_id": getattr(f, "fold_id", None),
            "net_return": float(getattr(f, "net_return", 0.0) or 0.0),
            "n_trades": int(getattr(f, "n_trades", 0) or 0),
            "fill_rate": float(getattr(f, "fill_rate", 0.0) or 0.0),
        })
    return out


def _summarise(folds: Sequence[Any]) -> tuple[float, int, float]:
    metrics = _fold_metrics(folds)
    if not metrics:
        return 0.0, 0, 0.0
    score = float(statistics.median(m["net_return"] for m in metrics))
    n_trades = int(sum(m["n_trades"] for m in metrics))
    fill_rate = float(statistics.mean(m["fill_rate"] for m in metrics))
    return score, n_trades, fill_rate


def replay_stress_matrix(
    *,
    best_params: Mapping[str, Any],
    score_with_overrides: Callable[[Mapping[str, Any], Mapping[str, Any]], tuple[float, Sequence[Any]]],
    slippage_offsets: Sequence[int] = DEFAULT_SLIPPAGE_OFFSETS,
    spread_multipliers: Sequence[float] = DEFAULT_SPREAD_MULTIPLIERS,
    cost_stress_levels: Sequence[str] = DEFAULT_COST_STRESS_LEVELS,
) -> list[StressResult]:
    """Replay the validation folds once per stress point.

    ``score_with_overrides(params, overrides)`` returns ``(objective, folds)``
    where each fold exposes ``net_return`` / ``n_trades`` / ``fill_rate``. The
    StressResult ``score`` is the median fold net return at that point.
    """
    results: list[StressResult] = []
    for point in iter_stress_points(
        slippage_offsets=slippage_offsets,
        spread_multipliers=spread_multipliers,
        cost_stress_levels=cost_stress_levels,
    ):
        _objective, folds = score_with_overrides(dict(best_params), point.as_overrides())
        score, n_trades, fill_rate = _summarise(folds)
        results.append(StressResult(
            point=point, fold_metrics=_fold_metrics(folds),
            score=score, n_trades_total=n_trades, fill_rate_total=fill_rate,
        ))
    return results


def conservative_floor_result(results: Sequence[StressResult]) -> StressResult | None:
    s, m, c = CONSERVATIVE_FLOOR
    return next((r for r in results if r.matches(s, m, c)), None)


def build_stress_matrix_payload(
    results: Sequence[StressResult], *, best_params: Mapping[str, Any],
) -> dict[str, Any]:
    cf = conservative_floor_result(results)
    return {
        "best_params": dict(best_params),
        "matrix": [
            {
                "slippage_bps_offset": r.point.slippage_bps_offset,
                "spread_multiplier": r.point.spread_multiplier,
                "cost_stress": r.point.cost_stress,
                "score": r.score,
                "n_trades": r.n_trades_total,
                "fill_rate": r.fill_rate_total,
            }
            for r in results
        ],
        "conservative_floor": (
            None if cf is None else {
                "slippage_bps_offset": cf.point.slippage_bps_offset,
                "spread_multiplier": cf.point.spread_multiplier,
                "cost_stress": cf.point.cost_stress,
                "score": cf.score,
                "robust": cf.score >= 0.0,
            }
        ),
    }


def write_stress_matrix_artifact(
    results: Sequence[StressResult], artifact_path: Path,
    *, best_params: Mapping[str, Any],
) -> Path:
    artifact_path = Path(artifact_path)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_stress_matrix_payload(results, best_params=best_params)
    artifact_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return artifact_path


__all__ = [
    "DEFAULT_SLIPPAGE_OFFSETS",
    "DEFAULT_SPREAD_MULTIPLIERS",
    "DEFAULT_COST_STRESS_LEVELS",
    "CONSERVATIVE_FLOOR",
    "StressPoint",
    "StressResult",
    "iter_stress_points",
    "replay_stress_matrix",
    "conservative_floor_result",
    "build_stress_matrix_payload",
    "write_stress_matrix_artifact",
]
