"""Phase 10 expanded robustness — top-K replays + sensitivity + stress.

Speedup report §9 / matrix doc N/A. Spends the compute Phase 1–5 saved
on stronger validation: re-runs top-K trials through full artifact mode,
sweeps each tuned param ±N steps to map the local response, and runs a
fold-local cost / quote-age / spread / delay stress matrix on the top-K
+ incumbent.

All four features are **default off** behind ``optuna.robustness``
config knobs. The replays write to
``artifacts/runs/study-<id>/top_k/k=<rank>/``; sensitivity / stress
reports land beside the per-candidate run dir.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence


@dataclass
class TopKReplayResult:
    rank: int
    trial_number: int
    params: dict[str, Any]
    fold_scores: list[float]
    objective: float
    holdout_score: Optional[float]
    artifact_dir: Optional[Path]


@dataclass
class SensitivityResult:
    param_name: str
    sweep_values: list[Any]
    fold_scores: list[float]
    delta_vs_baseline: list[float]


@dataclass
class StressMatrixResult:
    candidate_rank: int
    cost_stress_scores: dict[str, float]
    quote_age_stress_scores: dict[str, float]
    spread_stress_scores: dict[str, float]
    delay_stress_scores: dict[str, float]


def replay_top_k_candidates(
    *,
    completed_trials: Sequence[Any],
    top_k: int,
    score_param_set: Callable[[dict[str, Any]], tuple[float, list]],
    final_holdout_scorer: Optional[Callable[[dict[str, Any]], float]] = None,
    artifact_root: Path,
    write_artifacts: bool = True,
) -> list[TopKReplayResult]:
    """Re-run the top-K completed trials in FULL artifact mode.

    Speedup report §9 (Phase 10) — the per-trial optimizer path uses the
    fast objective_minimal flow; the top-K winners get a full forensic
    artifact re-run + (optionally) a final-holdout score. Default ``top_k``
    is 3.

    ``completed_trials`` should already be filtered to COMPLETED state
    AND non-sentinel. ``score_param_set(params) -> (objective, folds)`` is
    the per-trial full-mode scorer the runner already exposes.
    """
    ranked = sorted(
        completed_trials,
        key=lambda t: float(t.value if t.value is not None else float("-inf")),
        reverse=True,
    )[: int(max(0, top_k))]
    out: list[TopKReplayResult] = []
    artifact_root = Path(artifact_root)
    for rank_idx, trial in enumerate(ranked, start=1):
        params = dict(getattr(trial, "params", {}))
        try:
            objective, folds = score_param_set(params)
        except Exception as exc:  # noqa: BLE001 — one bad replay must not abort
            out.append(TopKReplayResult(
                rank=rank_idx,
                trial_number=int(getattr(trial, "number", -1)),
                params=params, fold_scores=[], objective=float("nan"),
                holdout_score=None, artifact_dir=None,
            ))
            continue
        fold_scores = [
            float(getattr(f, "objective", 0.0)) if hasattr(f, "objective")
            else float(getattr(f, "net_return", 0.0))
            for f in folds
        ]
        holdout_score: Optional[float] = None
        if final_holdout_scorer is not None:
            try:
                holdout_score = float(final_holdout_scorer(params))
            except Exception:  # noqa: BLE001
                holdout_score = None
        artifact_dir: Optional[Path] = None
        if write_artifacts:
            artifact_dir = artifact_root / "top_k" / f"k={rank_idx}"
            artifact_dir.mkdir(parents=True, exist_ok=True)
            (artifact_dir / "candidate.json").write_text(
                json.dumps({
                    "rank": rank_idx,
                    "trial_number": int(getattr(trial, "number", -1)),
                    "params": params,
                    "objective": float(objective),
                    "fold_scores": fold_scores,
                    "holdout_score": holdout_score,
                }, indent=2, default=str),
                encoding="utf-8",
            )
        out.append(TopKReplayResult(
            rank=rank_idx,
            trial_number=int(getattr(trial, "number", -1)),
            params=params, fold_scores=fold_scores, objective=float(objective),
            holdout_score=holdout_score, artifact_dir=artifact_dir,
        ))
    if write_artifacts and out:
        (artifact_root / "top_k_summary.json").parent.mkdir(parents=True, exist_ok=True)
        (artifact_root / "top_k_summary.json").write_text(
            json.dumps([{
                "rank": r.rank, "trial_number": r.trial_number,
                "objective": r.objective, "fold_scores": r.fold_scores,
                "holdout_score": r.holdout_score,
                "params": r.params,
            } for r in out], indent=2, default=str),
            encoding="utf-8",
        )
    return out


def param_sensitivity_for_candidate(
    *,
    base_params: dict[str, Any],
    search_space: Mapping[str, tuple],
    score_param_set: Callable[[dict[str, Any]], tuple[float, list]],
    n_steps: int = 5,
    artifact_dir: Optional[Path] = None,
) -> list[SensitivityResult]:
    """Sweep each tuned parameter ±n_steps within its search-space bounds.

    Returns one :class:`SensitivityResult` per tuned param. Each value
    is re-scored in objective_minimal mode (the caller supplies the
    scorer); a missing / non-tunable key is skipped.
    """
    base_objective, _ = score_param_set(base_params)
    results: list[SensitivityResult] = []
    for name, spec in search_space.items():
        if name not in base_params:
            continue
        if not isinstance(spec, tuple) or len(spec) < 3:
            continue
        kind = spec[0]
        if kind not in ("uniform", "log_uniform", "int", "loguniform"):
            continue
        low, high = float(spec[1]), float(spec[2])
        anchor = float(base_params[name]) if isinstance(base_params[name], (int, float)) else None
        if anchor is None:
            continue
        step_size = (high - low) / float(max(2, n_steps))
        sweep_values: list[Any] = []
        fold_scores: list[float] = []
        deltas: list[float] = []
        for i in range(-int(n_steps), int(n_steps) + 1):
            if i == 0:
                continue
            v = anchor + step_size * i
            if not (low <= v <= high):
                continue
            cand = dict(base_params)
            cand[name] = int(v) if kind == "int" else float(v)
            try:
                obj, _ = score_param_set(cand)
                sweep_values.append(cand[name])
                fold_scores.append(float(obj))
                deltas.append(float(obj - base_objective))
            except Exception:  # noqa: BLE001
                continue
        results.append(SensitivityResult(
            param_name=name, sweep_values=sweep_values,
            fold_scores=fold_scores, delta_vs_baseline=deltas,
        ))
    if artifact_dir is not None:
        Path(artifact_dir).mkdir(parents=True, exist_ok=True)
        (Path(artifact_dir) / "sensitivity.json").write_text(
            json.dumps([{
                "param": r.param_name,
                "sweep_values": r.sweep_values,
                "fold_scores": r.fold_scores,
                "delta_vs_baseline": r.delta_vs_baseline,
            } for r in results], indent=2, default=str),
            encoding="utf-8",
        )
    return results


def stress_matrix_for_candidate(
    *,
    candidate_rank: int,
    base_params: dict[str, Any],
    score_with_overrides: Callable[[dict[str, Any], dict[str, Any]], float],
    artifact_dir: Optional[Path] = None,
) -> StressMatrixResult:
    """Run a fold-local stress matrix on one candidate.

    Axes (each scored in objective_minimal mode via
    ``score_with_overrides(params, override_dict)``):

    * ``cost_stress``: ``backtest.cost_stress`` ∈
      {"conservative", "base", "aggressive"}.
    * ``quote_age``: ``execution.max_quote_age_seconds`` tightened by
      0%, -25%, -50%.
    * ``spread``: ``execution.max_spread_bps`` tightened by 0%, -25%, -50%.
    * ``delay``: ``backtest.entry_delay_minutes`` set to 0/1/2.
    """
    cost_scores: dict[str, float] = {}
    for stress in ("conservative", "base", "aggressive"):
        try:
            cost_scores[stress] = float(
                score_with_overrides(
                    base_params, {"backtest.cost_stress": stress},
                )
            )
        except Exception:  # noqa: BLE001
            cost_scores[stress] = float("nan")

    quote_scores: dict[str, float] = {}
    base_quote_age = float(base_params.get("execution.max_quote_age_seconds", 60))
    for pct in (1.0, 0.75, 0.50):
        key = f"{int(pct * 100)}pct"
        try:
            quote_scores[key] = float(score_with_overrides(
                base_params,
                {"execution.max_quote_age_seconds": base_quote_age * pct},
            ))
        except Exception:  # noqa: BLE001
            quote_scores[key] = float("nan")

    spread_scores: dict[str, float] = {}
    base_spread = float(base_params.get("execution.max_spread_bps", 200))
    for pct in (1.0, 0.75, 0.50):
        key = f"{int(pct * 100)}pct"
        try:
            spread_scores[key] = float(score_with_overrides(
                base_params,
                {"execution.max_spread_bps": base_spread * pct},
            ))
        except Exception:  # noqa: BLE001
            spread_scores[key] = float("nan")

    delay_scores: dict[str, float] = {}
    for delay in (0, 1, 2):
        key = f"{delay}min"
        try:
            delay_scores[key] = float(score_with_overrides(
                base_params, {"backtest.entry_delay_minutes": int(delay)},
            ))
        except Exception:  # noqa: BLE001
            delay_scores[key] = float("nan")

    out = StressMatrixResult(
        candidate_rank=int(candidate_rank),
        cost_stress_scores=cost_scores,
        quote_age_stress_scores=quote_scores,
        spread_stress_scores=spread_scores,
        delay_stress_scores=delay_scores,
    )
    if artifact_dir is not None:
        Path(artifact_dir).mkdir(parents=True, exist_ok=True)
        (Path(artifact_dir) / "stress_matrix.json").write_text(
            json.dumps({
                "candidate_rank": out.candidate_rank,
                "cost_stress": out.cost_stress_scores,
                "quote_age": out.quote_age_stress_scores,
                "spread": out.spread_stress_scores,
                "delay": out.delay_stress_scores,
            }, indent=2, default=str),
            encoding="utf-8",
        )
    return out


# ---- final-holdout rescored guard ----------------------------------------


def assert_holdout_not_rescored(
    *,
    study_user_attrs: Mapping[str, Any],
    set_user_attr: Callable[[str, Any], None],
) -> dict[str, Any]:
    """Flag re-scoring of an already-scored holdout (Phase 10 reporting guard).

    Sets ``final_holdout_first_scored_at_utc`` on the study the first
    time the holdout is scored. On any subsequent call also sets
    ``final_holdout_rescored=True`` so the operator can see the audit
    trail; an explicit acknowledgement is required before a second
    holdout score can be promoted.
    """
    import datetime as _dt

    first_scored = study_user_attrs.get("final_holdout_first_scored_at_utc")
    now_utc = _dt.datetime.utcnow().isoformat() + "Z"
    out: dict[str, Any] = {
        "first_scored_at_utc": first_scored,
        "rescored": False,
        "now_utc": now_utc,
    }
    if not first_scored:
        set_user_attr("final_holdout_first_scored_at_utc", now_utc)
        out["first_scored_at_utc"] = now_utc
    else:
        set_user_attr("final_holdout_rescored", True)
        set_user_attr("final_holdout_last_rescored_at_utc", now_utc)
        out["rescored"] = True
    return out


__all__ = [
    "TopKReplayResult",
    "SensitivityResult",
    "StressMatrixResult",
    "assert_holdout_not_rescored",
    "param_sensitivity_for_candidate",
    "replay_top_k_candidates",
    "stress_matrix_for_candidate",
]
