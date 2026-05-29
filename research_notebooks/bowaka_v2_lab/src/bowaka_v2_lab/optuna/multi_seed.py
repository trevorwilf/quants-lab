"""Multi-seed Optuna sweep + ensemble best (audit 2026-05-29 §14.1 / Phase 5).

Runs N independent walk-forward studies that differ ONLY in the sampler seed.
The ensemble best is the parameter set whose MEDIAN fold score across the seeds
is highest, tie-broken on lowest cross-seed variance.

The study runner is injectable (``study_runner``) so tests use a cheap stub; the
default writes a per-seed config (``optuna.seed`` + a ``__seed=<n>`` study-name
suffix) and calls :func:`walkforward_runner.run_walkforward_study`. Seeds are
explicit — never clock-based — so the sweep is deterministic per seed.
"""
from __future__ import annotations

import statistics
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence


@dataclass(frozen=True)
class SeedResult:
    seed: int
    study_name: str
    best_params_internal: dict   # gap/ratio search keys
    best_params_derived: dict    # actual-strategy keys
    best_value: float
    fold_scores: list[float]


@dataclass(frozen=True)
class EnsembleBest:
    params_internal: dict
    params_derived: dict
    median_score: float
    score_std_across_seeds: float
    contributing_seeds: list[int]
    per_seed_results: list[SeedResult] = field(default_factory=list)


def _default_seed_study_runner(
    *, cfg_path: str, seed: int, n_trials: int, study_name: str, **wf_kwargs: Any,
) -> dict:
    """Write a per-seed config variant and run a real walk-forward study."""
    import yaml

    from ..config.loader import load_config
    from .walkforward_runner import run_walkforward_study

    cfg = load_config(cfg_path)
    cfg.pop("_source_path", None)
    optuna_cfg = dict(cfg.get("optuna") or {})
    optuna_cfg["seed"] = int(seed)
    optuna_cfg["study_name_prefix"] = study_name
    cfg["optuna"] = optuna_cfg
    with tempfile.NamedTemporaryFile(
        "w", suffix=f"__seed_{seed}.yml", delete=False, encoding="utf-8",
    ) as fh:
        yaml.safe_dump(cfg, fh)
        seed_cfg_path = fh.name
    return run_walkforward_study(seed_cfg_path, n_trials=n_trials, **wf_kwargs)


def _seed_result(seed: int, study_name: str, result: Mapping[str, Any]) -> SeedResult:
    best = result.get("best_params") or result.get("best_params_internal") or {}
    derived = result.get("best_params_derived") or result.get("best_params_export") or best
    fold_scores = [float(x) for x in (result.get("fold_scores") or [])]
    value = result.get("best_value")
    if value is None:
        value = float(statistics.median(fold_scores)) if fold_scores else float("nan")
    return SeedResult(
        seed=int(seed), study_name=study_name,
        best_params_internal=dict(best), best_params_derived=dict(derived),
        best_value=float(value), fold_scores=fold_scores,
    )


def run_multi_seed_sweep(
    *,
    seeds: Sequence[int],
    n_trials_per_seed: int,
    cfg_path: str,
    study_runner: Optional[Callable[..., Mapping[str, Any]]] = None,
    study_name_base: Optional[str] = None,
    **wf_kwargs: Any,
) -> list[SeedResult]:
    """Run one study per seed; return a :class:`SeedResult` per seed."""
    runner = study_runner or _default_seed_study_runner
    base = study_name_base or Path(str(cfg_path)).stem
    out: list[SeedResult] = []
    for seed in seeds:
        study_name = f"{base}__seed={seed}"
        result = runner(
            cfg_path=str(cfg_path), seed=int(seed),
            n_trials=int(n_trials_per_seed), study_name=study_name, **wf_kwargs,
        )
        out.append(_seed_result(int(seed), study_name, result or {}))
    return out


def _signature(params: Mapping[str, Any], *, ndigits: int = 6) -> tuple:
    sig = []
    for k in sorted(params):
        v = params[k]
        if isinstance(v, (int, float)):
            sig.append((k, round(float(v), ndigits)))
        else:
            sig.append((k, v))
    return tuple(sig)


def select_ensemble_best(seed_results: Sequence[SeedResult]) -> EnsembleBest:
    """Group by rounded param signature; pick the group with the highest median
    ``best_value`` (tie-break: lowest cross-seed stdev)."""
    if not seed_results:
        return EnsembleBest({}, {}, float("nan"), 0.0, [], [])
    groups: dict[tuple, list[SeedResult]] = {}
    for r in seed_results:
        groups.setdefault(_signature(r.best_params_internal), []).append(r)

    def _group_key(item: tuple[tuple, list[SeedResult]]) -> tuple[float, float]:
        members = item[1]
        values = [m.best_value for m in members]
        median = float(statistics.median(values))
        std = float(statistics.stdev(values)) if len(values) > 1 else 0.0
        # higher median is better; lower std breaks ties.
        return (median, -std)

    best_sig, best_members = max(groups.items(), key=_group_key)
    values = [m.best_value for m in best_members]
    median = float(statistics.median(values))
    std = float(statistics.stdev(values)) if len(values) > 1 else 0.0
    exemplar = best_members[0]
    return EnsembleBest(
        params_internal=dict(exemplar.best_params_internal),
        params_derived=dict(exemplar.best_params_derived),
        median_score=median,
        score_std_across_seeds=std,
        contributing_seeds=[m.seed for m in best_members],
        per_seed_results=list(seed_results),
    )


__all__ = [
    "SeedResult",
    "EnsembleBest",
    "run_multi_seed_sweep",
    "select_ensemble_best",
]
