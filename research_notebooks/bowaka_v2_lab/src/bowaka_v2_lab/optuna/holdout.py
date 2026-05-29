"""Final-holdout scoring (realism remediation Phase 9, Task 6).

The walk-forward study NEVER reads the final-holdout window — :class:`HoldoutGuard`
raises if a tuning fold would overlap it. Holdout is scored exactly once, here,
*after* tuning is complete, against a fixed parameter set (the study's best
params, or an operator-supplied set).

This is the honest out-of-sample number: the holdout never influenced
hyperparameter selection, so its score is not inflated by the search.

:func:`score_final_holdout` is the library entry point; the ``optuna`` CLI
subcommand exposes it via ``--final-holdout``.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Mapping

from ..config import BowakaV2Paths, SimulationConfig, load_config
from ..data.lineage import resolve_lake_root
from .objective import (
    FoldResult,
    compute_objective,
    fold_result_from_report,
    fold_score,
)
from .holdout_guard import HoldoutGuard
from .walkforward import build_walkforward_splits


def _log() -> logging.Logger:
    log = logging.getLogger("bowaka_v2_lab.optuna.holdout")
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(handler)
        log.setLevel(logging.INFO)
    return log


def score_final_holdout(
    config_path: str | Path,
    params: Mapping[str, Any],
    *,
    allow_smoke: bool = False,
    out_path: str | Path | None = None,
    log: logging.Logger | None = None,
) -> dict:
    """Score a fixed parameter set against the untouched final-holdout window.

    Runs ONE real backtest over the walk-forward plan's final-holdout window
    (the same plan the study used) with ``params`` applied to the config. The
    :class:`HoldoutGuard` is explicitly put into ``final_eval`` phase first —
    this is the *only* sanctioned read of the holdout window.

    Returns a result dict (also written to ``out_path`` / the artifact root)
    carrying the holdout fold's metrics and its objective score.
    """
    # Imported here to avoid a circular import at module load
    # (walkforward_runner imports objective/holdout symbols at the top level).
    from .fold_context import build_holdout_context
    from .walkforward_runner import (
        _resolve_symbols,
        _run_fold_backtest,
        _to_date,
        apply_trial_params,
    )

    log = log or _log()
    cfg = load_config(config_path)
    sim_cfg = SimulationConfig.model_validate(cfg.get("simulation") or {})
    if sim_cfg.mode == "smoke_fixture" and not allow_smoke:
        raise RuntimeError(
            "final-holdout scoring refused: simulation.mode is 'smoke_fixture'. "
            "Pass --allow-smoke-optimization / allow_smoke=True to override."
        )

    repo_root = Path(__file__).resolve().parents[5]
    paths = BowakaV2Paths.from_config(cfg, repo_root=repo_root)
    paths.assert_strategy_isolation()

    optuna_cfg = cfg.get("optuna", {}) or {}
    wf = optuna_cfg.get("walkforward", {}) or {}
    bt = cfg.get("backtest", {}) or {}
    md = cfg.get("market_data", {}) or {}

    plan = build_walkforward_splits(
        full_start=_to_date(bt["start_date"]),
        full_end=_to_date(bt["end_date"]),
        train_months=int(wf.get("train_months", 6)),
        val_months=int(wf.get("val_months", 1)),
        final_holdout_months=int(wf.get("final_holdout_months", 1)),
    )
    feed = str(md.get("feed", "iex"))
    # Hotfix 2026-05-29: resolve via the standard chain (md.get("shared_root")
    # is None for every shipping config -> Path(str(None)) false-positives).
    lake_root = resolve_lake_root(cfg)
    symbols = _resolve_symbols(cfg, md)

    # The holdout guard is created in tuning phase and explicitly switched to
    # final_eval — the audited transition that sanctions the holdout read.
    guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
    guard.enter_final_eval()

    holdout_cfg = apply_trial_params(cfg, dict(params))
    log.info(
        "scoring final holdout %s..%s with %d params, %d symbols, feed=%s",
        plan.final_holdout_start, plan.final_holdout_end, len(params), len(symbols), feed,
    )
    # Realism remediation 2 Phase 8 (audit §P1-004): the holdout MUST be scored
    # against the same substantive metrics the validation folds use — daily MTM
    # drawdown, worst-day loss, quote coverage, fill rate, missing-quote counts.
    # Pass return_report=True and build the FoldResult identically to validation.
    # Speedup §5.2 / §11.2 Phase 2 — precompute the holdout context once for
    # this single backtest (the supplier-creation cost is unchanged; the
    # PIT-universe / daily-cache cost is moved out of the inner call so a
    # future re-run path reuses it).
    cached_suppliers_flag = bool((cfg.get("optuna") or {}).get("cached_suppliers", False))
    holdout_ctx = build_holdout_context(
        cfg, plan, lake_root=lake_root, feed=feed, symbols=symbols,
        paths=paths, holdout_guard=guard,
        cached_suppliers=cached_suppliers_flag,
    )
    summary = _run_fold_backtest(
        holdout_cfg,
        val_start=plan.final_holdout_start,
        val_end=plan.final_holdout_end,
        lake_root=lake_root,
        feed=feed,
        symbols=symbols,
        paths=paths,
        return_report=True,
        ctx=holdout_ctx,
    )
    guard.exit_final_eval()

    fold_id = f"holdout_{plan.final_holdout_start.isoformat()}"
    report = summary.get("_report") if isinstance(summary, dict) else None
    if not isinstance(report, dict) or not report:
        # Fail closed (audit §P1-004): the holdout is the ONLY honest out-of-
        # sample number; a missing/corrupt report cannot be silently degraded.
        raise RuntimeError(
            f"final-holdout scoring failed: report.json missing or empty for "
            f"holdout window {plan.final_holdout_start}..{plan.final_holdout_end}. "
            "The holdout MUST be scored on the same substantive metrics as "
            "validation folds (audit §P1-004). Re-run with a config / lake "
            "that produces a valid report."
        )
    fold = fold_result_from_report(fold_id, report, summary)
    score = fold_score(fold)
    objective = compute_objective([fold])

    # Strip the report (huge / not for the small holdout JSON) but keep the
    # rest of summary alongside the richer fold metrics for downstream tooling.
    holdout_summary = {k: v for k, v in summary.items() if k != "_report"}
    result = {
        "status": "ok",
        "kind": "final_holdout",
        "simulation_mode": sim_cfg.mode,
        "feed": feed,
        "final_holdout": [
            plan.final_holdout_start.isoformat(),
            plan.final_holdout_end.isoformat(),
        ],
        "params": dict(params),
        "holdout_score": score,
        "holdout_objective": objective.objective,
        # Realism remediation 2 Phase 8 (audit §P1-004) — surface the same
        # metrics validation folds carry, including the DAILY MTM drawdown and
        # worst-day loss from the report's daily equity curve.
        "holdout_metrics": {
            "net_return_pct": fold.net_return,
            "mtm_max_drawdown_pct": fold.max_drawdown,
            "worst_day_loss_pct": fold.worst_day_loss,
            "n_trades": fold.n_trades,
            "fill_rate": fold.fill_rate,
            "historical_quote_coverage_pct": fold.quote_coverage * 100.0,
            "missing_quote_count": fold.missing_quote_count,
        },
        "holdout_summary": holdout_summary,
    }

    if out_path is None:
        out_path = (
            Path(paths.artifact_root) / "optuna"
            / f"final_holdout_{plan.final_holdout_start.isoformat()}.json"
        )
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    result["results_path"] = str(out_path)
    log.info(
        "final-holdout score=%.6f net_return=%.4f n_trades=%d",
        score, fold.net_return, fold.n_trades,
    )
    return result


def _load_params(
    *,
    params_json: str | Path | None = None,
    params_inline: Mapping[str, Any] | None = None,
    study_results_json: str | Path | None = None,
) -> dict[str, Any]:
    """Resolve the parameter set to score against the holdout.

    Precedence: explicit ``params_inline`` > ``params_json`` file >
    ``best_params`` in a study results JSON.
    """
    if params_inline:
        return dict(params_inline)
    if params_json is not None:
        doc = json.loads(Path(params_json).read_text(encoding="utf-8"))
        # Accept either a bare params dict or a {"best_params": {...}} wrapper.
        return dict(doc.get("best_params", doc))
    if study_results_json is not None:
        doc = json.loads(Path(study_results_json).read_text(encoding="utf-8"))
        best = doc.get("best_params")
        if not best:
            raise ValueError(
                f"study results JSON {study_results_json} has no 'best_params'"
            )
        return dict(best)
    raise ValueError(
        "no parameter set supplied — pass --params-json or --study-results"
    )


__all__ = ["score_final_holdout", "_load_params"]
