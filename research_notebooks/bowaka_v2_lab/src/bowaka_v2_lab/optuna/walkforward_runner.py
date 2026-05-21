"""Real walk-forward Optuna optimization against the shared market-data lake.

This replaces the smoke / toy objective. Each Optuna trial:

1. samples a parameter set from :data:`search_space.SEARCH_SPACE_SPEC`;
2. applies it to the config;
3. runs a **real backtest** over every walk-forward *validation* window, using
   data from the shared lake (``bowaka_common.marketdata``);
4. scores each window with :func:`objective.fold_score`; the trial's objective
   is the median fold score (:func:`objective.compute_objective`).

The final-holdout window is reserved at the tail and is **never read during
tuning** — :class:`HoldoutGuard` raises if a fold would overlap it.

Compute note: a real study is ``n_trials`` × ``n_folds`` real backtests. With the
config defaults (2500 trials, ~20 folds) that is tens of thousands of backtests —
a multi-day job. Lower ``optuna.n_trials``, set an explicit ``universe.symbols``,
or widen the walk-forward step for a faster first run.
"""
from __future__ import annotations

import copy
import datetime as _dt
import hashlib
import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from ..config import BowakaV2Paths, SimulationConfig, load_config
from ..data.suppliers import build_daily_cache_from_lake, make_lake_suppliers
from ..sim.backtester import run_backtest
from ..universe.builder import build_pit_universe_for_sessions, eligible_symbols
from .dispatcher import OptunaStudy
from .holdout_guard import HoldoutGuard
from .objective import FoldResult, compute_objective
from .search_space import suggest_params
from .walkforward import build_walkforward_splits

_REPO_ROOT = Path(__file__).resolve().parents[5]

#: Objective value returned when a whole trial fails — so one bad trial never
#: aborts a long study (Optuna keeps it as a completed, low-scoring trial).
_FAILED_TRIAL_SCORE = -1.0e9


def _log() -> logging.Logger:
    log = logging.getLogger("bowaka_v2_lab.optuna.walkforward_runner")
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(handler)
        log.setLevel(logging.INFO)
    return log


def _to_date(value: Any) -> _dt.date:
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    return pd.Timestamp(value).date()


def _xnys_sessions(start: _dt.date, end: _dt.date) -> list[_dt.date]:
    import exchange_calendars as xcals

    cal = xcals.get_calendar("XNYS")
    return [pd.Timestamp(s).date() for s in cal.sessions_in_range(pd.Timestamp(start), pd.Timestamp(end))]


def _resolve_symbols(cfg: dict, md: dict, *, cap: int = 100) -> list[str]:
    """Explicit ``universe.symbols`` > lake-derived (capped) > synthetic fallback."""
    explicit = (cfg.get("universe", {}) or {}).get("symbols")
    if explicit:
        return [str(s) for s in explicit]
    if str(md.get("minute_bar_source", "fixture")) in ("alpaca", "shared"):
        from bowaka_common.marketdata import available_symbols

        return available_symbols(
            md.get("shared_root"), timeframe="1d", feed=md.get("feed", "iex")
        )[:cap]
    return ["AAA", "BBB", "CCC"]


def apply_trial_params(base_cfg: dict, params: dict[str, Any]) -> dict:
    """Return a deep copy of ``base_cfg`` with dotted trial params applied.

    ``"signals.gap_pct_max": 0.1`` → ``cfg["signals"]["gap_pct_max"] = 0.1``.
    """
    cfg = copy.deepcopy(base_cfg)
    for dotted, value in params.items():
        section, _, key = dotted.partition(".")
        if not key:
            cfg[dotted] = value
            continue
        if not isinstance(cfg.get(section), dict):
            cfg[section] = {}
        cfg[section][key] = value
    return cfg


def _fold_result(fold_id: str, summary: dict) -> FoldResult:
    return FoldResult(
        fold_id=fold_id,
        net_return=float(summary.get("net_return_pct", 0.0)),
        max_drawdown=float(summary.get("max_drawdown_pct", 0.0)),
        turnover=float(summary.get("turnover", 0.0)),
        concentration=float(summary.get("concentration", 0.0)),
        n_trades=int(summary.get("n_trades", 0)),
        ambiguous_bar_count=int(summary.get("ambiguous_bar_count", 0)),
        missing_quote_count=int(summary.get("missing_quote_count", 0)),
    )


def _run_fold_backtest(
    cfg: dict,
    *,
    val_start: _dt.date,
    val_end: _dt.date,
    lake_root: Any,
    feed: str,
    symbols: list[str],
    paths: BowakaV2Paths,
) -> dict:
    """Run one real backtest over a walk-forward validation window; return its summary.

    Realism Phase 3: the walk-forward objective consumes the point-in-time
    universe built per session from the lake — never the synthetic fixture.
    """
    sessions = _xnys_sessions(val_start, val_end)
    if not sessions:
        return {}
    from bowaka_common.marketdata import MarketDataStore

    minute_supplier, daily_supplier = make_lake_suppliers(lake_root, feed=feed)
    universe = build_pit_universe_for_sessions(sessions, cfg, MarketDataStore(lake_root))
    # Build the daily-feature cache from each session's PIT-eligible symbols —
    # the exact set the scanner iterates — so a cache entry exists for every
    # symbol the universe admits. An empty PIT universe (no lake asset master)
    # falls back to the explicit ``symbols`` list so the fold still runs.
    daily_cache = {}
    for s in sessions:
        sess_syms = eligible_symbols(universe.get(s, {})) or symbols
        daily_cache[s] = build_daily_cache_from_lake(lake_root, sess_syms, s, feed=feed)
    run_dir = Path(tempfile.mkdtemp(prefix="bowaka_wf_fold_"))
    try:
        result = run_backtest(
            cfg=cfg,
            sessions=sessions,
            scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
            universe_snapshot_by_session=universe,
            daily_cache_by_session=daily_cache,
            minute_bars_supplier=minute_supplier,
            daily_bars_supplier=daily_supplier,
            initial_bankroll=100_000.0,
            paths=paths,
            run_dir=run_dir,
        )
        return dict(result.summary)
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def make_walkforward_objective(
    base_cfg: dict,
    plan,
    *,
    lake_root: Any,
    feed: str,
    symbols: list[str],
    paths: BowakaV2Paths,
    holdout_guard: HoldoutGuard,
    log: logging.Logger,
) -> Callable[[Any], float]:
    """Build the Optuna objective: median fold score over real per-fold backtests."""

    def objective(trial: Any) -> float:
        try:
            params = suggest_params(trial)
            trial_cfg = apply_trial_params(base_cfg, params)
            folds: list[FoldResult] = []
            for i, split in enumerate(plan.splits):
                # Causality: tuning must never read the final-holdout window.
                holdout_guard.assert_can_read(split.val_start, split.val_end)
                fold_id = f"f{i}_{split.val_start.isoformat()}"
                try:
                    summary = _run_fold_backtest(
                        trial_cfg,
                        val_start=split.val_start,
                        val_end=split.val_end,
                        lake_root=lake_root,
                        feed=feed,
                        symbols=symbols,
                        paths=paths,
                    )
                    folds.append(_fold_result(fold_id, summary))
                except Exception as exc:  # noqa: BLE001 — one bad fold must not kill the trial
                    log.warning("trial %s fold %s failed: %s", trial.number, fold_id, exc)
                    folds.append(
                        FoldResult(
                            fold_id=fold_id, net_return=-1.0, max_drawdown=1.0,
                            turnover=0.0, concentration=0.0, n_trades=0,
                            ambiguous_bar_count=0, missing_quote_count=0,
                        )
                    )
            result = compute_objective(folds)
            trial.set_user_attr("fold_scores", result.fold_scores)
            trial.set_user_attr("n_folds", len(folds))
            return result.objective
        except Exception as exc:  # noqa: BLE001 — one bad trial must not abort the study
            log.error("trial %s failed entirely: %s", getattr(trial, "number", "?"), exc)
            return _FAILED_TRIAL_SCORE

    return objective


def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def run_walkforward_study(
    config_path: str | Path,
    *,
    n_trials: int | None = None,
    n_jobs: int | None = None,
    n_startup_trials: int | None = None,
    allow_smoke: bool = False,
    log: logging.Logger | None = None,
) -> dict:
    """Run a real walk-forward Optuna study driven entirely by the config.

    ``n_trials`` / ``n_jobs`` / ``n_startup_trials`` override the config's
    ``optuna`` section when given. ``n_startup_trials`` is the number of random-
    sampling trials run before TPE-guided search begins.

    A config whose ``simulation.mode`` is ``smoke_fixture`` is **refused** —
    deterministic synthetic data is not a research-grade objective — unless
    ``allow_smoke`` is set (CLI ``--allow-smoke-optimization``).
    """
    log = log or _log()
    cfg = load_config(config_path)
    sim_cfg = SimulationConfig.model_validate(cfg.get("simulation") or {})
    if sim_cfg.mode == "smoke_fixture" and not allow_smoke:
        raise RuntimeError(
            "walk-forward optimization refused: simulation.mode is 'smoke_fixture'. "
            "Optimizing against deterministic synthetic data produces a meaningless "
            "objective. Use a research config (intended_realism / current_code_parity), "
            "or pass --allow-smoke-optimization (CLI) / allow_smoke=True to override."
        )
    paths = BowakaV2Paths.from_config(cfg, repo_root=_REPO_ROOT)
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
    if not plan.splits:
        raise ValueError(
            "walk-forward plan has no splits — widen backtest.start_date/end_date "
            "or shrink optuna.walkforward.{train,val}_months"
        )

    feed = str(md.get("feed", "iex"))
    lake_root = md.get("shared_root")
    symbols = _resolve_symbols(cfg, md)
    holdout_guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)

    trials = int(n_trials if n_trials is not None else optuna_cfg.get("n_trials", 20))
    jobs = int(n_jobs if n_jobs is not None else optuna_cfg.get("n_jobs", 1))
    startup = int(
        n_startup_trials if n_startup_trials is not None else optuna_cfg.get("n_startup_trials", 10)
    )

    study = OptunaStudy(
        feed=feed,
        cost_stress=str(bt.get("cost_stress", "conservative")),
        dataset_hash=_hash([symbols, feed, str(plan.splits[0].train_start), str(plan.splits[-1].val_end)]),
        config_hash=_hash({k: v for k, v in cfg.items() if k != "_source_path"}),
        storage_uri=optuna_cfg.get("storage") or None,
        n_trials=trials,
        n_jobs=jobs,
        n_startup_trials=startup,
    )
    study.create()
    log.info(
        "walk-forward study %s: %d trials (%d random startup) x %d folds, %d symbols, feed=%s",
        study.study.study_name, trials, startup, len(plan.splits), len(symbols), feed,
    )
    objective = make_walkforward_objective(
        cfg, plan, lake_root=lake_root, feed=feed, symbols=symbols,
        paths=paths, holdout_guard=holdout_guard, log=log,
    )
    study.optimize(objective)

    import optuna

    completed = [t for t in study.study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    best = max(completed, key=lambda t: t.value) if completed else None
    out = {
        "status": "ok",
        "study_name": study.study.study_name,
        "simulation_mode": sim_cfg.mode,
        "feed": feed,
        "n_trials_requested": trials,
        "n_trials_completed": len(completed),
        "n_startup_trials": startup,
        "n_folds": len(plan.splits),
        "symbols": len(symbols),
        "final_holdout": [
            plan.final_holdout_start.isoformat(),
            plan.final_holdout_end.isoformat(),
        ],
        "best_value": (best.value if best else None),
        "best_params": (dict(best.params) if best else {}),
    }
    results_path = Path(paths.artifact_root) / "optuna" / f"{study.study.study_name}.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    out["results_path"] = str(results_path)
    log.info("walk-forward study done: %d/%d trials completed, best=%s",
             len(completed), trials, out["best_value"])
    return out
