"""Cross-seed parameter stability report (audit 2026-05-29 §14 / Phase 5).

For each search-space dimension, summarise the spread of the per-seed best
values and score stability in ``[0, 1]``:

    stability_score = clamp(1 - (max - min) / search_space_range, 0, 1)

A perfectly-agreeing dimension (every seed lands on the same value) scores 1.0;
a dimension whose per-seed winners span the full search-space range scores 0.0.
A "stable" dimension scores > 0.7; a "knife-edge" dimension scores < 0.3. The
report also records the IQR for inspection.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence


def _spread(values: Sequence[float]) -> dict[str, float]:
    vals = sorted(float(v) for v in values)
    n = len(vals)
    if n == 0:
        return {"min": 0.0, "p25": 0.0, "median": 0.0, "p75": 0.0, "max": 0.0, "iqr": 0.0}
    if n == 1:
        v = vals[0]
        return {"min": v, "p25": v, "median": v, "p75": v, "max": v, "iqr": 0.0}
    q = statistics.quantiles(vals, n=4, method="inclusive")
    p25, _p50, p75 = q[0], q[1], q[2]
    return {
        "min": vals[0], "p25": float(p25),
        "median": float(statistics.median(vals)), "p75": float(p75),
        "max": vals[-1], "iqr": float(p75 - p25),
    }


def _search_range(spec: Any) -> Optional[float]:
    if isinstance(spec, (tuple, list)) and len(spec) >= 3 and spec[0] in (
        "uniform", "log_uniform", "loguniform", "int",
    ):
        try:
            return float(spec[2]) - float(spec[1])
        except (TypeError, ValueError):
            return None
    return None


def compute_parameter_stability(
    seed_results: Sequence[Any],
    search_space: Mapping[str, Any],
    *,
    stable_threshold: float = 0.7,
    knife_edge_threshold: float = 0.3,
) -> dict[str, Any]:
    """Per-dimension stability across the per-seed best params.

    ``seed_results`` items expose ``best_params_internal`` (a flat dotted dict).
    Only numeric dimensions present in ``search_space`` with a finite range are
    scored.
    """
    by_dim: dict[str, list[float]] = {}
    for r in seed_results:
        params = getattr(r, "best_params_internal", None) or {}
        for k, v in params.items():
            if isinstance(v, (int, float)):
                by_dim.setdefault(k, []).append(float(v))

    dimensions: dict[str, Any] = {}
    for dim, values in by_dim.items():
        rng = _search_range(search_space.get(dim))
        spread = _spread(values)
        if rng is None or rng <= 0:
            score = 1.0 if (spread["max"] - spread["min"]) == 0 else 0.0
        else:
            score = max(0.0, min(1.0, 1.0 - (spread["max"] - spread["min"]) / rng))
        dimensions[dim] = {
            "stability_score": float(score),
            "spread": spread,
            "search_space_range": rng,
            "stable": score > stable_threshold,
            "knife_edge": score < knife_edge_threshold,
            "n_seeds": len(values),
        }
    scores = [d["stability_score"] for d in dimensions.values()]
    return {
        "dimensions": dimensions,
        "n_dimensions": len(dimensions),
        "mean_stability": float(statistics.mean(scores)) if scores else 1.0,
        "stable_fraction": (
            sum(1 for d in dimensions.values() if d["stable"]) / len(dimensions)
            if dimensions else 1.0
        ),
        "stable_threshold": stable_threshold,
        "knife_edge_threshold": knife_edge_threshold,
    }


def passes_stability_gate(
    report: Mapping[str, Any], *, min_score: float = 0.5, min_fraction: float = 0.8,
) -> tuple[bool, list[str]]:
    """At least ``min_fraction`` of dimensions must score >= ``min_score`` for
    the paper-candidate tier; otherwise the gate fails and names the offenders."""
    dims = report.get("dimensions") or {}
    if not dims:
        return True, []
    failing = [k for k, d in dims.items() if d["stability_score"] < min_score]
    ok_fraction = (len(dims) - len(failing)) / len(dims)
    return (ok_fraction >= min_fraction, sorted(failing))


def write_parameter_stability(report: Mapping[str, Any], base_path: Path) -> Path:
    base_path = Path(base_path)
    base_path.parent.mkdir(parents=True, exist_ok=True)
    json_path = base_path.with_suffix(".json")
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    lines = ["# Parameter stability (cross-seed)", ""]
    lines.append(f"- dimensions: {report.get('n_dimensions', 0)}")
    lines.append(f"- mean stability: {report.get('mean_stability', 0.0):.3f}")
    lines.append(f"- stable fraction: {report.get('stable_fraction', 0.0):.3f}")
    lines.append("")
    lines.append("| Dimension | stability | min | median | max | stable |")
    lines.append("|---|---:|---:|---:|---:|:--:|")
    for dim, d in (report.get("dimensions") or {}).items():
        sp = d["spread"]
        lines.append(
            f"| {dim} | {d['stability_score']:.3f} | {sp['min']:.4g} | "
            f"{sp['median']:.4g} | {sp['max']:.4g} | {'yes' if d['stable'] else 'no'} |"
        )
    base_path.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path


__all__ = [
    "compute_parameter_stability",
    "passes_stability_gate",
    "write_parameter_stability",
]
