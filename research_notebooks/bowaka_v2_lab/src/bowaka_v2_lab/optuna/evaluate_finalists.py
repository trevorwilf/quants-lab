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


def _build_top_k_clustering(
    finalist_rows: Sequence[Mapping[str, Any]], *, cv_threshold: float = 0.15,
) -> dict[str, Any]:
    """Per-parameter CV across the top-K finalists (speedup report v2 §11 Phase 5).

    Returns ``stable_params`` (CV <= threshold), ``unstable_params`` (CV >
    threshold), the top-3 drifting params by absolute CV, and the unstable
    fraction. Excludes the incumbent row so the clustering reflects the
    optimizer's top-K, not the incumbent anchor.
    """
    from .stability import top_k_cluster_stability

    top_k_params = [
        dict(r.get("params") or {})
        for r in finalist_rows
        if not r.get("is_incumbent")
    ]
    if len(top_k_params) < 2:
        return {
            "stable_params": [], "unstable_params": [],
            "top_drifting": [], "param_cvs": {}, "max_cv": 0.0,
            "unstable_fraction": 0.0, "cv_threshold": float(cv_threshold),
            "n_finalists": len(top_k_params),
        }
    res = top_k_cluster_stability(
        top_k_params, relative_spread_threshold=float(cv_threshold),
    )
    param_cvs: dict[str, float] = dict(res.get("param_cvs", {}))
    stable = sorted(k for k, cv in param_cvs.items() if cv <= cv_threshold)
    unstable = sorted(k for k, cv in param_cvs.items() if cv > cv_threshold)
    top_drifting = [
        {"param": k, "cv": float(cv)}
        for k, cv in sorted(param_cvs.items(), key=lambda kv: -abs(kv[1]))[:3]
    ]
    total = len(param_cvs)
    return {
        "stable_params": stable,
        "unstable_params": unstable,
        "top_drifting": top_drifting,
        "param_cvs": {k: float(v) for k, v in param_cvs.items()},
        "max_cv": float(res.get("max_cv", 0.0)),
        "unstable_fraction": (len(unstable) / total) if total else 0.0,
        "cv_threshold": float(cv_threshold),
        "n_finalists": len(top_k_params),
    }


def _build_fold_local_stress_matrix(
    finalist_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Reshape the per-finalist stress data into a (finalist, fold, axis) matrix.

    Reads the ``stress`` block each finalist row already carries
    (``row["stress"][axis]["validation"]["fold_scores"]``) and emits the
    matrix plus the global ``worst_case_objective`` across every cell.
    """
    matrix: list[dict[str, Any]] = []
    worst = None
    n_axes = 0
    n_folds = 0
    for r in finalist_rows:
        stress = r.get("stress") or {}
        per_axis: dict[str, list[float]] = {}
        for axis, payload in stress.items():
            val = (payload or {}).get("validation") or {}
            fold_scores = [float(x) for x in (val.get("fold_scores") or [])]
            per_axis[axis] = fold_scores
            n_axes = max(n_axes, 1)
            n_folds = max(n_folds, len(fold_scores))
            for sc in fold_scores:
                worst = sc if worst is None else min(worst, sc)
        matrix.append({
            "trial_number": r.get("trial_number"),
            "is_incumbent": r.get("is_incumbent", False),
            "by_axis": per_axis,
        })
    return {
        "matrix": matrix,
        "n_finalists": len(finalist_rows),
        "n_axes": n_axes,
        "n_folds": n_folds,
        "worst_case_objective": worst,
    }


def _build_data_quality_summary(
    data_quality_report: Optional[Mapping[str, Any]],
) -> dict[str, Any]:
    """Per-fold DQ summary + a top-level partial_tape_caveat flag."""
    if not data_quality_report:
        return {"available": False, "any_gate_failed": False,
                "partial_tape_caveat": False, "per_fold": []}
    checks = data_quality_report.get("checks") or data_quality_report.get("results") or []
    any_failed = False
    if isinstance(checks, list):
        for c in checks:
            if isinstance(c, Mapping) and str(c.get("status", "")).lower() in ("fail", "failed", "error"):
                any_failed = True
                break
    partial_tape = bool(
        data_quality_report.get("partial_tape_caveat")
        or data_quality_report.get("partial_tape")
    )
    return {
        "available": True,
        "any_gate_failed": bool(any_failed),
        "partial_tape_caveat": partial_tape,
        "feed": data_quality_report.get("feed"),
        "per_fold": data_quality_report.get("per_fold", []),
    }


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
    # Speedup report v2 §11 / Phase 5 — additional Stage-B sections. All
    # optional; absent providers degrade their section to "skipped"/empty so
    # the report stays stable and the existing schema is preserved.
    sensitivity_scorer: Optional[
        Callable[[dict[str, Any]], dict[str, Any]]
    ] = None,
    recent_window_scorer: Optional[
        Callable[[dict[str, Any]], Optional[dict[str, Any]]]
    ] = None,
    trade_diagnostics_provider: Optional[
        Callable[[dict[str, Any]], dict[str, Any]]
    ] = None,
    data_quality_report: Optional[Mapping[str, Any]] = None,
    final_holdout_audit: Optional[Mapping[str, Any]] = None,
    cluster_cv_threshold: float = 0.15,
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
        # Speedup report v2 §11 / Phase 5 — per-finalist ±5%/±10% parameter
        # sensitivity table.
        if sensitivity_scorer is not None:
            try:
                row["sensitivity"] = sensitivity_scorer(params)
            except Exception as exc:  # noqa: BLE001
                row["sensitivity"] = {"error": str(exc)}
        else:
            row["sensitivity"] = {}
        # Per-finalist trade-distribution diagnostics.
        if trade_diagnostics_provider is not None:
            try:
                row["trade_diagnostics"] = trade_diagnostics_provider(params)
            except Exception as exc:  # noqa: BLE001
                row["trade_diagnostics"] = {"error": str(exc)}
        else:
            row["trade_diagnostics"] = {}
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

    # 4b. Speedup report v2 §11 / Phase 5 — assemble the expanded Stage-B
    # ``finalist_evaluation`` block (fold-local stress matrix, top-K cluster
    # stability, DQ summary, recent-window, trade diagnostics, final-holdout
    # audit) and run the stop-ship checklist over it.
    from .stop_ship_checklist import evaluate_stop_ship

    # The exported candidate is finalists[0] (the best by Optuna value).
    exported_row = finalist_rows[0] if finalist_rows else None
    trade_diags_block: dict[str, Any] = {}
    if exported_row is not None and isinstance(exported_row.get("trade_diagnostics"), Mapping):
        trade_diags_block["exported"] = dict(exported_row["trade_diagnostics"])
    trade_diags_block["per_finalist"] = [
        {"trial_number": r.get("trial_number"),
         "is_incumbent": r.get("is_incumbent", False),
         **(r.get("trade_diagnostics") or {})}
        for r in finalist_rows
    ]

    recent_window_block: dict[str, Any]
    if recent_window_scorer is not None and exported_row is not None:
        try:
            rw = recent_window_scorer(dict(exported_row.get("params") or {}))
            recent_window_block = (
                rw if rw is not None
                else {"skipped": True,
                      "reason": "no recent slice available beyond final_holdout"}
            )
        except Exception as exc:  # noqa: BLE001
            recent_window_block = {"skipped": True, "reason": str(exc)}
    else:
        recent_window_block = {
            "skipped": True,
            "reason": "no recent-window scorer provided",
        }

    final_holdout_audit_block: dict[str, Any] = {}
    if final_holdout_audit is not None:
        final_holdout_audit_block = dict(final_holdout_audit)
    # Per-finalist holdout-vs-validation drift (positive = holdout worse).
    final_holdout_audit_block["per_finalist_drift"] = []
    for r in finalist_rows:
        h = r.get("holdout")
        v = r.get("validation") or {}
        if isinstance(h, Mapping) and "objective" in h and "objective" in v:
            final_holdout_audit_block["per_finalist_drift"].append({
                "trial_number": r.get("trial_number"),
                "holdout_objective": float(h["objective"]),
                "validation_objective": float(v["objective"]),
                "drift": float(v["objective"]) - float(h["objective"]),
            })

    dq_summary = _build_data_quality_summary(data_quality_report)
    finalist_evaluation: dict[str, Any] = {
        "fold_local_stress_matrix": _build_fold_local_stress_matrix(finalist_rows),
        "top_k_clustering": _build_top_k_clustering(
            finalist_rows, cv_threshold=cluster_cv_threshold,
        ),
        "sensitivity": {
            r.get("trial_number"): r.get("sensitivity", {})
            for r in finalist_rows
        },
        "recent_window": recent_window_block,
        "data_quality": dq_summary,
        "trade_diagnostics": trade_diags_block,
        "final_holdout_audit": final_holdout_audit_block,
        "partial_tape_caveat": dq_summary.get("partial_tape_caveat", False),
    }
    report["finalist_evaluation"] = finalist_evaluation
    if dq_summary.get("feed"):
        report.setdefault("feed", dq_summary["feed"])
    decision = evaluate_stop_ship(
        report, cluster_cv_threshold=cluster_cv_threshold,
    )
    finalist_evaluation["stop_ship"] = decision.to_dict()

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
    "_build_top_k_clustering",
    "_build_fold_local_stress_matrix",
    "_build_data_quality_summary",
]
