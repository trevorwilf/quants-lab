"""Local-perturbation robustness around the ensemble best (audit 2026-05-29 §14
/ Phase 5).

For each search-space dimension, perturb the ensemble best by -10%, -5%, +5%,
+10% (continuous) or -1/+1 step (integer), keeping every other dimension at the
ensemble value, and replay the validation folds (via an injected scorer). The
ensemble is "robust" along a dimension iff every perturbation produces a score
within ``ROBUSTNESS_TOLERANCE`` (default 0.10 absolute) of the ensemble score.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

ROBUSTNESS_TOLERANCE = 0.10
DEFAULT_CONTINUOUS_PCTS = (0.05, 0.10)


@dataclass(frozen=True)
class DimensionRobustness:
    param_name: str
    perturbations: list[dict]
    robust: bool


def _perturbed_values(name: str, anchor: float, spec: Any,
                      continuous_pcts: Sequence[float]) -> list[tuple[str, Any]]:
    kind = spec[0] if isinstance(spec, (tuple, list)) and spec else None
    out: list[tuple[str, Any]] = []
    if kind == "int":
        low, high = int(spec[1]), int(spec[2])
        for d in (-1, 1):
            v = int(round(anchor)) + d
            if low <= v <= high:
                out.append((f"{'+' if d > 0 else '-'}1step", v))
    elif kind in ("uniform", "log_uniform", "loguniform"):
        low, high = float(spec[1]), float(spec[2])
        for pct in continuous_pcts:
            for sign in (-1, 1):
                v = float(anchor) * (1.0 + sign * pct)
                if low <= v <= high:
                    out.append((f"{'+' if sign > 0 else '-'}{int(pct * 100)}%", v))
    return out


def perturbation_robustness(
    *,
    base_params: Mapping[str, Any],
    base_score: float,
    search_space: Mapping[str, Any],
    score_fn: Callable[[Mapping[str, Any]], float],
    tolerance: float = ROBUSTNESS_TOLERANCE,
    continuous_pcts: Sequence[float] = DEFAULT_CONTINUOUS_PCTS,
) -> dict[str, Any]:
    """``score_fn(params) -> objective``. Returns a robustness report."""
    dims: list[DimensionRobustness] = []
    for name, spec in search_space.items():
        anchor = base_params.get(name)
        if not isinstance(anchor, (int, float)):
            continue
        values = _perturbed_values(name, float(anchor), spec, continuous_pcts)
        if not values:
            continue
        perts: list[dict] = []
        robust = True
        for label, v in values:
            cand = dict(base_params)
            cand[name] = v
            score = float(score_fn(cand))
            deviation = abs(score - float(base_score))
            perts.append({"label": label, "value": v, "score": score,
                          "deviation": deviation})
            if deviation > tolerance:
                robust = False
        dims.append(DimensionRobustness(name, perts, robust))

    overall_robust = all(d.robust for d in dims) if dims else True
    robust_fraction = (
        sum(1 for d in dims if d.robust) / len(dims) if dims else 1.0
    )
    return {
        "tolerance": float(tolerance),
        "base_score": float(base_score),
        "dimensions": [
            {"param_name": d.param_name, "robust": d.robust,
             "perturbations": d.perturbations}
            for d in dims
        ],
        "fragile_dimensions": [d.param_name for d in dims if not d.robust],
        "overall_robust": overall_robust,
        "robust_fraction": robust_fraction,
        "n_dimensions": len(dims),
    }


def passes_robustness_gate(
    report: Mapping[str, Any], *, min_fraction: float = 0.8,
) -> tuple[bool, list[str]]:
    """>= ``min_fraction`` of dimensions must be robust for the paper tier."""
    n = int(report.get("n_dimensions", 0))
    if n == 0:
        return True, []
    fragile = list(report.get("fragile_dimensions") or [])
    ok_fraction = (n - len(fragile)) / n
    return (ok_fraction >= min_fraction, sorted(fragile))


def write_robustness_artifact(report: Mapping[str, Any], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return path


__all__ = [
    "ROBUSTNESS_TOLERANCE",
    "DimensionRobustness",
    "perturbation_robustness",
    "passes_robustness_gate",
    "write_robustness_artifact",
]
