"""Staged finalist evaluation pipeline (speedup report v2 §1.4 / §8.3 / §9 /
§11.2 Phase 5).

Post-study Stage B: spends the compute saved by the per-trial
``objective_artifact_mode="objective_minimal"`` flow on stronger
validation of the top-K candidates + the incumbent baseline:

* Re-runs each finalist in **full artifact mode** for forensic depth.
* Optionally scores each finalist on the **final holdout** (the ONE
  post-tuning read of that window — guarded by
  :meth:`HoldoutGuard.declare_finalist_read`).
* Runs a small **stress matrix** (spread / quote-age / cost / fill /
  delay) over the validation folds for each finalist.
* Runs a **local parameter-neighborhood sweep** for each finalist.

Stage C (deterministic-promotion rerun) lives in
:func:`run_promotion_candidate`. Both stages write JSON / parquet
artifacts the operator inspects before promoting a candidate.

This module is intentionally written so the heavy lifting (scoring
callables, holdout / stress / perturbation runners) is **injectable**.
The CLI subcommand wires real scorers via the existing
``_score_param_set`` /  ``apply_trial_params`` infrastructure; tests
pass cheap stubs. The decoupling keeps the module testable without a
full Optuna study + lake.
"""
from __future__ import annotations

import datetime as _dt
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence


# --------------------------------------------------------------------------
# Result + config dataclasses
# --------------------------------------------------------------------------


@dataclass
class FinalistEvaluationConfig:
    """Operator-facing knobs for the finalist evaluation pipeline.

    Loaded from ``finalist_evaluation:`` in the run config.
    """

    top_k: int = 15
    include_incumbent: bool = True
    full_artifacts: bool = True
    score_final_holdout: bool = True
    stress_scenarios: list[dict[str, Any]] = field(default_factory=list)
    local_parameter_perturbation: dict[str, Any] = field(default_factory=dict)


@dataclass
class FinalistEvaluationResult:
    finalists: list[dict[str, Any]]
    incumbent: Optional[dict[str, Any]]
    report_path: Path
    report: dict[str, Any]


# --------------------------------------------------------------------------
# Stress / perturbation helpers
# --------------------------------------------------------------------------


def apply_stress_overrides(
    cfg: Mapping[str, Any], overrides: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply dotted-path stress overrides to a copy of ``cfg``.

    Each key is either an absolute override (``"execution.max_spread_bps":
    50``) or a ``*_multiplier`` form (``"execution.max_spread_bps_multiplier":
    1.5``) that multiplies the resolved value. Unknown ``_multiplier`` keys
    raise ``KeyError`` so the operator sees a clear error rather than a
    silently-ignored stress.
    """
    out = json.loads(json.dumps(dict(cfg)))  # deep copy via JSON
    for path, value in overrides.items():
        if path.endswith("_multiplier"):
            target_path = path[: -len("_multiplier")]
            current = _get_dotted(out, target_path)
            if current is None:
                raise KeyError(
                    f"stress override {path}: target {target_path!r} not in cfg"
                )
            _set_dotted(out, target_path, type(current)(float(current) * float(value)))
        else:
            _set_dotted(out, path, value)
    return out


def _get_dotted(d: Mapping[str, Any], path: str) -> Any:
    node: Any = d
    for p in path.split("."):
        if not isinstance(node, dict) or p not in node:
            return None
        node = node[p]
    return node


def _set_dotted(d: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    node: Any = d
    for p in parts[:-1]:
        if p not in node or not isinstance(node[p], dict):
            node[p] = {}
        node = node[p]
    node[parts[-1]] = value


# --------------------------------------------------------------------------
# Top-K replay + holdout scoring
# --------------------------------------------------------------------------


def _summarise_folds(folds: Sequence[Any]) -> dict[str, Any]:
    """Aggregate per-fold scores into the schema row (validation OR holdout)."""
    fold_scores = [
        float(getattr(f, "objective", 0.0)) if hasattr(f, "objective")
        else float(getattr(f, "net_return", 0.0))
        for f in folds
    ]
    out: dict[str, Any] = {
        "objective": float(sum(fold_scores) / max(1, len(fold_scores))),
        "fold_scores": fold_scores,
        "fold_metrics": [
            {"fold_id": getattr(f, "fold_id", str(i)), **getattr(f, "metrics", {})}
            for i, f in enumerate(folds)
        ],
    }
    for k in ("net_return", "max_drawdown", "worst_day_loss", "n_trades",
             "fill_rate", "quote_coverage", "turnover", "concentration"):
        vals = [getattr(f, k, None) for f in folds]
        vals = [v for v in vals if v is not None]
        out[k] = float(sum(vals) / max(1, len(vals))) if vals else 0.0
    return out


def evaluate_finalists(
    *,
    completed_trials: Sequence[Any],
    finalist_cfg: FinalistEvaluationConfig,
    score_param_set: Callable[[dict[str, Any]], tuple[float, list]],
    holdout_scorer: Optional[Callable[[dict[str, Any]], list]] = None,
    stress_scorer: Optional[
        Callable[[dict[str, Any], dict[str, Any]], list]
    ] = None,
    perturbation_scorer: Optional[
        Callable[[dict[str, Any], str, float], tuple[float, dict[str, Any]]]
    ] = None,
    output_dir: Optional[Path] = None,
    log: Optional[logging.Logger] = None,
) -> FinalistEvaluationResult:
    """Run the finalist-evaluation pipeline.

    ``completed_trials`` is the post-filter list of COMPLETE Optuna trials
    (sentinel + DQ-degraded already removed by the caller). Each scoring
    callable is injectable so tests can use cheap stubs.

    The four scoring callbacks:

    * ``score_param_set(params) -> (objective, folds)`` — validation
      replay in full artifact mode (the existing ``_score_param_set``).
    * ``holdout_scorer(params) -> folds`` (optional) — runs a single
      backtest over the final-holdout window. Caller is responsible for
      calling :meth:`HoldoutGuard.declare_finalist_read` before invoking
      this.
    * ``stress_scorer(params, overrides) -> folds`` (optional) — runs
      validation folds with ``apply_stress_overrides(cfg, overrides)``.
    * ``perturbation_scorer(params, name, delta) -> (objective,
      neighbour_params)`` (optional) — perturbs ``params[name]`` by
      ``delta`` and re-scores via ``score_param_set``.

    Returns a :class:`FinalistEvaluationResult` with the finalists list,
    the optional incumbent row, and the path to the written
    ``finalist_report.json``.
    """
    log = log or logging.getLogger("bowaka_v2_lab.evaluate_finalists")
    # 1. Sort by Optuna value; drop sentinel-score and Nones (defensive).
    valid = [
        t for t in completed_trials
        if getattr(t, "value", None) is not None
    ]
    ranked = sorted(valid, key=lambda t: float(t.value), reverse=True)
    top_n = max(0, int(finalist_cfg.top_k))
    finalists = list(ranked[:top_n])

    # 2. Append incumbent if requested + not already in top_k.
    incumbent: Optional[Any] = None
    if finalist_cfg.include_incumbent:
        incumbent = next(
            (t for t in valid
             if (getattr(t, "user_attrs", {}) or {}).get("incumbent_trial") is True),
            None,
        )
        if incumbent is not None and incumbent not in finalists:
            finalists.append(incumbent)

    # 3. Per-finalist replay + holdout + stress + perturbation.
    finalist_rows: list[dict[str, Any]] = []
    for trial in finalists:
        params = dict(getattr(trial, "params", {}))
        objective, folds = score_param_set(params)
        validation_row = _summarise_folds(folds)
        validation_row["objective"] = float(objective)
        row: dict[str, Any] = {
            "trial_number": int(getattr(trial, "number", -1)),
            "params": params,
            "is_incumbent": (
                (getattr(trial, "user_attrs", {}) or {}).get("incumbent_trial") is True
            ),
            "validation": validation_row,
        }
        # Holdout.
        if finalist_cfg.score_final_holdout and holdout_scorer is not None:
            try:
                holdout_folds = holdout_scorer(params)
                row["holdout"] = _summarise_folds(holdout_folds)
            except Exception as exc:  # noqa: BLE001 — one bad holdout must not abort
                log.warning(
                    "finalist trial #%d holdout scoring failed: %s",
                    row["trial_number"], exc,
                )
                row["holdout"] = {"error": str(exc)}
        else:
            row["holdout"] = None
        # Stress.
        if finalist_cfg.stress_scenarios and stress_scorer is not None:
            row["stress"] = {}
            for scenario in finalist_cfg.stress_scenarios:
                name = str(scenario.get("name", ""))
                overrides = dict(scenario.get("overrides") or {})
                try:
                    s_folds = stress_scorer(params, overrides)
                    row["stress"][name] = {
                        "validation": _summarise_folds(s_folds),
                    }
                except Exception as exc:  # noqa: BLE001
                    row["stress"][name] = {"error": str(exc)}
        else:
            row["stress"] = {}
        # Perturbation.
        perturb_cfg = finalist_cfg.local_parameter_perturbation or {}
        if perturb_cfg.get("enabled") and perturbation_scorer is not None:
            rel_delta = float(perturb_cfg.get("relative_delta", 0.05))
            max_neighbours = int(perturb_cfg.get("max_neighbors_per_param", 2))
            row["perturbation"] = {}
            for name in list(params.keys())[: max_neighbours * 4]:
                row["perturbation"][name] = []
                for sign in (-1.0, 1.0)[:max_neighbours]:
                    try:
                        obj, neigh_params = perturbation_scorer(
                            params, name, sign * rel_delta,
                        )
                        row["perturbation"][name].append(
                            {"delta": sign * rel_delta,
                             "validation_objective": float(obj),
                             "neighbor_params": neigh_params}
                        )
                    except Exception:  # noqa: BLE001
                        continue
        else:
            row["perturbation"] = {}
        finalist_rows.append(row)

    # 4. Build the report.
    incumbent_row = next((r for r in finalist_rows if r["is_incumbent"]), None)
    report: dict[str, Any] = {
        "finalists": finalist_rows,
        "incumbent": incumbent_row,
        "captured_at_utc": _dt.datetime.utcnow().isoformat() + "Z",
    }
    if finalist_rows:
        report["best_by_validation"] = max(
            finalist_rows, key=lambda r: r["validation"]["objective"],
        )["trial_number"]
        if any(r.get("holdout") and isinstance(r["holdout"], dict)
               and "objective" in r["holdout"] for r in finalist_rows):
            report["best_by_holdout"] = max(
                (r for r in finalist_rows
                 if r.get("holdout") and "objective" in (r["holdout"] or {})),
                key=lambda r: r["holdout"]["objective"],
            )["trial_number"]
    # Per-finalist incumbent_comparison deltas.
    if incumbent_row is not None:
        incumbent_obj = incumbent_row["validation"]["objective"]
        for r in finalist_rows:
            r.setdefault("incumbent_comparison", {})
            r["incumbent_comparison"]["validation"] = {
                "objective_delta": float(r["validation"]["objective"]) - float(incumbent_obj),
            }
            if r.get("holdout") and "objective" in (r["holdout"] or {}) \
                    and incumbent_row.get("holdout") and "objective" in incumbent_row["holdout"]:
                r["incumbent_comparison"]["holdout"] = {
                    "objective_delta": float(r["holdout"]["objective"])
                    - float(incumbent_row["holdout"]["objective"]),
                }

    # 5. Write to disk.
    output_dir = output_dir or Path("artifacts") / "runs" / "finalists"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "finalist_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8",
    )
    log.info("finalist report -> %s (%d finalists)", report_path, len(finalist_rows))
    return FinalistEvaluationResult(
        finalists=finalist_rows,
        incumbent=incumbent_row,
        report_path=report_path,
        report=report,
    )


# --------------------------------------------------------------------------
# Stage C — deterministic promotion rerun
# --------------------------------------------------------------------------


def run_promotion_candidate(
    *,
    params: Mapping[str, Any],
    base_cfg: Mapping[str, Any],
    score_param_set: Callable[[dict[str, Any]], tuple[float, list]],
    holdout_scorer: Optional[Callable[[dict[str, Any]], list]] = None,
    dataset_hash: str,
    config_hash: str,
    code_hash: str,
    output_dir: Path,
    log: Optional[logging.Logger] = None,
) -> Path:
    """Stage C — deterministic-promotion rerun for ONE selected candidate.

    Re-runs the selected ``params`` in serial / deterministic mode (the
    caller is responsible for setting ``n_jobs=1`` + a fixed sampler seed
    on its scoring callables) and writes a ``promotion_artifact.json``
    carrying every hash and the full result. Operator-driven.
    """
    log = log or logging.getLogger("bowaka_v2_lab.run_promotion_candidate")
    objective, folds = score_param_set(dict(params))
    holdout_summary: Optional[dict[str, Any]] = None
    if holdout_scorer is not None:
        try:
            holdout_summary = _summarise_folds(holdout_scorer(dict(params)))
        except Exception as exc:  # noqa: BLE001
            log.warning("promotion holdout scoring failed: %s", exc)
            holdout_summary = {"error": str(exc)}
    import platform as _platform

    out: dict[str, Any] = {
        "captured_at_utc": _dt.datetime.utcnow().isoformat() + "Z",
        "params": dict(params),
        "objective": float(objective),
        "validation": _summarise_folds(folds),
        "holdout": holdout_summary,
        "dataset_hash": dataset_hash,
        "config_hash": config_hash,
        "code_hash": code_hash,
        "platform": {
            "node": _platform.node(),
            "system": _platform.system(),
            "release": _platform.release(),
            "python": _platform.python_version(),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    p = output_dir / "promotion_artifact.json"
    p.write_text(json.dumps(out, indent=2, default=str, sort_keys=True), encoding="utf-8")
    log.info("promotion artifact -> %s", p)
    return p


__all__ = [
    "FinalistEvaluationConfig",
    "FinalistEvaluationResult",
    "apply_stress_overrides",
    "evaluate_finalists",
    "run_promotion_candidate",
]
