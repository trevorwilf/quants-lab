"""Real walk-forward Optuna optimization against the shared market-data lake.

Realism remediation Phase 9 rebuilds this runner on top of the realistic
simulator. Each Optuna trial:

1. samples a parameter set from :data:`search_space.SEARCH_SPACE_SPEC` (with
   per-study ``cfg.optuna.search_space_overrides`` applied);
2. applies it to the config;
3. runs a **real backtest** over every walk-forward *validation* window — PIT
   universe (Phase 3), full intraday scan replay (Phase 4), multi-lot portfolio
   (Phase 5), realistic fills + quotes (Phase 6), minute-path exits (Phase 7);
4. scores each window from its ``report.json`` (Phase 8) with the realistic
   :func:`objective.fold_score` — the drawdown penalty uses the DAILY
   mark-to-market equity curve, not the closed-trade curve;
5. the trial objective is the median fold score minus a cross-fold
   metric-variance stability penalty (:func:`objective.compute_objective`).

The final-holdout window is reserved at the tail and is **never read during
tuning** — :class:`HoldoutGuard` raises if a fold would overlap it. It is scored
separately and once via :func:`optuna.holdout.score_final_holdout`
(CLI ``optuna --final-holdout``).

A study-start :func:`preflight.run_preflight` refuses to run when the dataset
cannot support a research-grade objective (DQ failure / low quote coverage /
``smoke_fixture`` without ``--allow-smoke-optimization``).

Compute note: a real study is ``n_trials`` x ``n_folds`` real backtests. With
the config defaults (thousands of trials, ~20 folds) that is tens of thousands
of backtests — a multi-day job. Lower ``optuna.n_trials``, set an explicit
``universe.symbols``, or widen the walk-forward step for a faster first run.
"""
from __future__ import annotations

import copy
import datetime as _dt
import hashlib
import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping

import pandas as pd

from ..config import BowakaV2Paths, SimulationConfig, load_config
from ..promotion.suitability import tier_for_simulation_contract
from ..data.suppliers import (
    build_daily_cache_from_lake,
    make_forward_minute_supplier,
    make_lake_suppliers,
    make_quote_supplier,
    resolve_intraday_window_policy,
)
from ..sim.backtester import run_backtest
from ..sim.schedule import scan_times_for_session
from ..universe.builder import build_pit_universe_for_sessions, eligible_symbols
from .dispatcher import OptunaStudy
from .holdout_guard import HoldoutGuard
from .objective import (
    DEFAULT_PENALTY_WEIGHTS,
    FoldResult,
    compute_objective,
    fold_result_from_report,
    fold_score,
)
from .preflight import probe_quote_coverage, run_preflight
from .search_space import SEARCH_SPACE_VERSION, resolve_search_space, suggest_params
from .stability import top_k_cluster_stability
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


def _git_head() -> str:
    """Short-lived ``git rev-parse HEAD`` for study lineage; ``"unknown"`` on failure."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=str(Path(__file__).resolve().parent),
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:  # noqa: BLE001 — lineage is best-effort, never fatal
        pass
    return "unknown"


class OptunaParityError(RuntimeError):
    """Raised when an Optuna config diverges from the frozen contract undeclared."""


def assert_optuna_config_parity(cfg: Mapping[str, Any]) -> None:
    """Refuse an Optuna study whose config diverges from the contract undeclared.

    Realism remediation 2 Phase 0 (audit §P0-001). A study may start only when
    EITHER the config↔contract diff is clean for every strategy-contract leaf,
    OR every diverging leaf is declared in the config's
    ``<stem>.parity_sidecar.yaml``. Any *undeclared* divergence raises
    :class:`OptunaParityError` — Bayesian optimization must never silently tune a
    different strategy than the one the config claims.

    Scoped to ``current_code_parity`` / ``intended_realism``: a ``smoke_fixture``
    study runs synthetic plumbing data and is never a parameter-recommendation
    run (and is already gated behind ``allow_smoke``), so the contract-parity
    requirement does not apply to it.

    A no-op when the frozen contract is unavailable on the host (parity cannot be
    computed) — that is surfaced by the data-quality / preflight gates instead.
    """
    from ..config.parity_sidecar import classify_config_parity, load_parity_sidecar
    from ..reference import contract_available, load_actual_contract

    sim = cfg.get("simulation") or {}
    if (sim.get("mode") if isinstance(sim, dict) else None) == "smoke_fixture":
        return
    if not contract_available():
        return
    source_path = cfg.get("_source_path")
    sidecar = load_parity_sidecar(source_path) if source_path else []
    result = classify_config_parity(
        {k: v for k, v in cfg.items() if k != "_source_path"},
        load_actual_contract(),
        sidecar=sidecar,
    )
    undeclared = result["undeclared"]
    if undeclared:
        raise OptunaParityError(
            f"Optuna study refused: the config diverges from the frozen contract "
            f"on {len(undeclared)} undeclared field(s): {undeclared}. Reconcile the "
            f"config to the contract, or declare each divergence in "
            f"<config-stem>.parity_sidecar.yaml (field_path / actual_value / "
            f"lab_value / reason / risk_classification). "
            f"See docs/audits/2026-05-22_realism_audit.md §P0-001."
        )


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
    """A BOUNDED symbol sample for study-start preflight probing — NOT the
    trading universe.

    The walk-forward folds trade the per-session **point-in-time universe**
    built by ``universe.builder.build_pit_universe_for_sessions`` (rebuilt every
    session from the lake's asset master + filters — daily, uncapped, exactly
    like the live scanner). This capped list is used only to keep the preflight
    data-quality / quote-coverage probes fast, to seed the dataset-lineage hash,
    and as a daily-cache fallback for a session whose PIT universe is empty.

    Explicit ``universe.symbols`` > lake-derived (capped at ``cap``) > synthetic.
    """
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

    Dotted keys nest to ANY depth, so the realistic search space's nested live
    parameters all reach the right place::

        "signals.gap_pct_max": 0.1
            -> cfg["signals"]["gap_pct_max"] = 0.1
        "exits.time_stop.exit_time": "15:45"
            -> cfg["exits"]["time_stop"]["exit_time"] = "15:45"
        "exits.signal_fade.score_thresholds.hard": 0.5
            -> cfg["exits"]["signal_fade"]["score_thresholds"]["hard"] = 0.5
    """
    cfg = copy.deepcopy(base_cfg)
    for dotted, value in params.items():
        parts = dotted.split(".")
        node: Any = cfg
        for key in parts[:-1]:
            child = node.get(key)
            if not isinstance(child, dict):
                child = {}
                node[key] = child
            node = child
        node[parts[-1]] = value
    return cfg


def _run_fold_backtest(
    cfg: dict,
    *,
    val_start: _dt.date,
    val_end: _dt.date,
    lake_root: Any,
    feed: str,
    symbols: list[str],
    paths: BowakaV2Paths,
    return_report: bool = False,
) -> dict:
    """Run one real backtest over a walk-forward validation window.

    Returns the run ``summary`` dict; when ``return_report`` is set the
    substantive Phase-8 ``report.json`` document is attached under the
    ``"_report"`` key (so the objective can use the DAILY mark-to-market
    drawdown rather than the closed-trade ``summary.max_drawdown_pct``).

    Realism Phase 3: the walk-forward objective consumes the point-in-time
    universe built per session from the lake — never the synthetic fixture.
    """
    sessions = _xnys_sessions(val_start, val_end)
    if not sessions:
        return {}
    from bowaka_common.marketdata import MarketDataStore

    minute_supplier, daily_supplier = make_lake_suppliers(
        lake_root, feed=feed,
        intraday_window_policy=resolve_intraday_window_policy(cfg),
    )
    # Realism Phase 6: each fold uses the lake's historical-quote supplier and
    # the forward-minute supplier (marketable-limit timeout detection).
    quote_supplier = make_quote_supplier(
        lake_root, feed=feed,
        default_max_age_seconds=float(
            (cfg.get("execution") or {}).get("max_quote_age_seconds", 60)
        ),
    )
    forward_minute_supplier = make_forward_minute_supplier(lake_root, feed=feed)
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
        # Realism Phase 4: each walk-forward fold replays the full intraday
        # scan cadence (was one hard-coded 14:00-UTC scan per session).
        result = run_backtest(
            cfg=cfg,
            sessions=sessions,
            scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
            universe_snapshot_by_session=universe,
            daily_cache_by_session=daily_cache,
            minute_bars_supplier=minute_supplier,
            daily_bars_supplier=daily_supplier,
            quote_supplier=quote_supplier,
            forward_minute_supplier=forward_minute_supplier,
            initial_bankroll=100_000.0,
            paths=paths,
            run_dir=run_dir,
        )
        summary = dict(result.summary)
        if return_report:
            # Realism Phase 8: read the substantive report.json before cleanup.
            report_path = run_dir / "report.json"
            if report_path.is_file():
                try:
                    summary["_report"] = json.loads(
                        report_path.read_text(encoding="utf-8")
                    )
                except Exception:  # noqa: BLE001 — a corrupt report degrades to summary-only
                    summary["_report"] = {}
            else:
                summary["_report"] = {}
        return summary
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def _fold_result(fold_id: str, summary: dict) -> FoldResult:
    """Build a realistic :class:`FoldResult` from a fold's run summary.

    When the substantive ``report.json`` is attached (``summary["_report"]``)
    the drawdown is taken from the DAILY mark-to-market equity curve. Without
    it (a degraded fold) the closed-trade ``max_drawdown_pct`` is used as a
    fallback so the trial still completes.
    """
    report = summary.get("_report")
    if isinstance(report, dict) and report:
        return fold_result_from_report(fold_id, report, summary)
    # Fallback path — no report.json (e.g. a fold that produced no sessions).
    return FoldResult(
        fold_id=fold_id,
        net_return=float(summary.get("net_return_pct", 0.0) or 0.0),
        max_drawdown=float(summary.get("max_drawdown_pct", 0.0) or 0.0),
        turnover=float(summary.get("turnover", 0.0) or 0.0),
        concentration=float(summary.get("concentration", 0.0) or 0.0),
        n_trades=int(summary.get("n_trades", 0) or 0),
        ambiguous_bar_count=int(summary.get("ambiguous_bar_count", 0) or 0),
        missing_quote_count=int(summary.get("missing_quote_count", 0) or 0),
        worst_day_loss=0.0,
        quote_coverage=float(summary.get("historical_quote_coverage_pct", 100.0) or 0.0) / 100.0,
        fill_rate=float(summary.get("fill_rate", 1.0) if summary.get("fill_rate") is not None else 1.0),
    )


def _degraded_fold(fold_id: str) -> FoldResult:
    """The worst-possible fold result — used when a fold's backtest raises, so
    one bad fold can never lift a trial's objective."""
    return FoldResult(
        fold_id=fold_id, net_return=-1.0, max_drawdown=1.0,
        turnover=0.0, concentration=0.0, n_trades=0,
        worst_day_loss=1.0, quote_coverage=0.0, fill_rate=0.0,
    )


def _run_validation_folds(
    trial_cfg: dict,
    plan,
    *,
    lake_root: Any,
    feed: str,
    symbols: list[str],
    paths: BowakaV2Paths,
    holdout_guard: HoldoutGuard,
    log: logging.Logger,
) -> list[FoldResult]:
    """Run a real backtest over every walk-forward validation window.

    The single fold-execution path shared by the per-trial objective and the
    best-trial neighbourhood robustness sweep. The :class:`HoldoutGuard` is
    asserted per fold so tuning can never read the final-holdout window; a fold
    that raises degrades to :func:`_degraded_fold` rather than aborting.
    """
    folds: list[FoldResult] = []
    for i, split in enumerate(plan.splits):
        holdout_guard.assert_can_read(split.val_start, split.val_end)
        fold_id = f"f{i}_{split.val_start.isoformat()}"
        try:
            summary = _run_fold_backtest(
                trial_cfg,
                val_start=split.val_start, val_end=split.val_end,
                lake_root=lake_root, feed=feed, symbols=symbols, paths=paths,
                return_report=True,
            )
            folds.append(_fold_result(fold_id, summary))
        except Exception as exc:  # noqa: BLE001 — one bad fold must not kill the trial
            log.warning("fold %s failed: %s", fold_id, exc)
            folds.append(_degraded_fold(fold_id))
    return folds


def _score_param_set(
    base_cfg: dict,
    params: dict[str, Any],
    plan,
    *,
    lake_root: Any,
    feed: str,
    symbols: list[str],
    paths: BowakaV2Paths,
    holdout_guard: HoldoutGuard,
    log: logging.Logger,
) -> tuple[float, list[FoldResult]]:
    """Run every validation fold for ``params``; return ``(objective, folds)``."""
    folds = _run_validation_folds(
        apply_trial_params(base_cfg, params), plan,
        lake_root=lake_root, feed=feed, symbols=symbols, paths=paths,
        holdout_guard=holdout_guard, log=log,
    )
    return compute_objective(folds).objective, folds


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
    search_space_overrides: dict[str, Any] | None = None,
) -> Callable[[Any], float]:
    """Build the Optuna objective: median fold score over real per-fold backtests."""

    def objective(trial: Any) -> float:
        try:
            params = suggest_params(trial, overrides=search_space_overrides)
            folds = _run_validation_folds(
                apply_trial_params(base_cfg, params), plan,
                lake_root=lake_root, feed=feed, symbols=symbols, paths=paths,
                holdout_guard=holdout_guard, log=log,
            )
            result = compute_objective(folds)
            trial.set_user_attr("fold_scores", result.fold_scores)
            trial.set_user_attr("n_folds", len(folds))
            trial.set_user_attr("fold_variance", result.fold_variance)
            trial.set_user_attr("median_fold_score", result.median_fold_score)
            trial.set_user_attr("penalty_breakdown", result.penalty_breakdown)
            trial.set_user_attr(
                "fold_metrics", [{"fold_id": f.fold_id, **f.metrics} for f in folds]
            )
            return result.objective
        except Exception as exc:  # noqa: BLE001 — one bad trial must not abort the study
            log.error("trial %s failed entirely: %s", getattr(trial, "number", "?"), exc)
            return _FAILED_TRIAL_SCORE

    return objective


def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# best-trial reporting (Phase 9, Task 5)
# --------------------------------------------------------------------------
def _neighbour_param_sets(
    best_params: dict[str, Any],
    spec: dict[str, tuple],
    *,
    n_neighbours: int = 5,
    rel_step: float = 0.10,
) -> list[dict[str, Any]]:
    """Sample ``n_neighbours`` parameter sets around ``best_params``.

    Each neighbour perturbs every numeric parameter by a deterministic
    ``+/- rel_step`` fraction of its search range, clamped to the bounds.
    Categorical / int parameters are nudged by one step. Deterministic so a
    re-run of a study reports the same robustness summary.
    """
    import random

    rng = random.Random(20260521)
    neighbours: list[dict[str, Any]] = []
    for _ in range(n_neighbours):
        cand: dict[str, Any] = {}
        for name, value in best_params.items():
            entry = spec.get(name)
            if entry is None:
                cand[name] = value
                continue
            kind = entry[0]
            if kind in ("uniform", "log_uniform"):
                lo, hi = float(entry[1]), float(entry[2])
                span = hi - lo
                delta = rng.uniform(-rel_step, rel_step) * span
                cand[name] = min(hi, max(lo, float(value) + delta))
            elif kind == "int":
                lo, hi = int(entry[1]), int(entry[2])
                step = rng.choice([-1, 0, 1])
                cand[name] = min(hi, max(lo, int(value) + step))
            elif kind == "categorical":
                choices = list(entry[1])
                cand[name] = rng.choice(choices) if choices else value
            else:
                cand[name] = value
        neighbours.append(cand)
    return neighbours


def build_best_trial_report(
    best,
    base_cfg: dict,
    plan,
    *,
    lake_root: Any,
    feed: str,
    symbols: list[str],
    paths: BowakaV2Paths,
    holdout_guard: HoldoutGuard,
    log: logging.Logger,
    search_space_overrides: dict[str, Any] | None = None,
    n_neighbours: int = 5,
) -> dict[str, Any]:
    """Build the best-trial report: fold-by-fold metrics + neighbourhood robustness.

    Re-scores ``n_neighbours`` parameter sets sampled around the best params so
    the report shows whether the best score sits on a robust plateau or a
    fragile spike. The stability rank is the stdev of the best trial's fold
    scores (lower = more stable).
    """
    spec = resolve_search_space(search_space_overrides)
    fold_scores = list(best.user_attrs.get("fold_scores") or [])
    fold_metrics = list(best.user_attrs.get("fold_metrics") or [])
    fold_variance = best.user_attrs.get("fold_variance")
    if fold_variance is None and len(fold_scores) > 1:
        import statistics

        fold_variance = float(statistics.stdev(fold_scores))

    # Parameter-neighbourhood robustness: re-score 5 neighbours.
    neighbours = _neighbour_param_sets(
        dict(best.params), spec, n_neighbours=n_neighbours
    )
    neighbour_results: list[dict[str, Any]] = []
    for idx, params in enumerate(neighbours):
        try:
            score, folds = _score_param_set(
                base_cfg, params, plan,
                lake_root=lake_root, feed=feed, symbols=symbols,
                paths=paths, holdout_guard=holdout_guard, log=log,
            )
        except Exception as exc:  # noqa: BLE001 — a bad neighbour must not abort the report
            log.warning("neighbour %d failed: %s", idx, exc)
            score = _FAILED_TRIAL_SCORE
        neighbour_results.append({"neighbour": idx, "params": params, "score": score})

    valid_scores = [
        r["score"] for r in neighbour_results if r["score"] > _FAILED_TRIAL_SCORE / 2
    ]
    best_value = best.value if best.value is not None else 0.0
    robustness = {
        "n_neighbours": len(neighbour_results),
        "neighbour_scores": [r["score"] for r in neighbour_results],
        "neighbour_score_min": min(valid_scores) if valid_scores else None,
        "neighbour_score_max": max(valid_scores) if valid_scores else None,
        "neighbour_score_mean": (
            sum(valid_scores) / len(valid_scores) if valid_scores else None
        ),
        # The best score is robust when neighbours do not collapse far below it.
        "best_vs_neighbour_mean_delta": (
            best_value - (sum(valid_scores) / len(valid_scores))
            if valid_scores else None
        ),
        "neighbours": neighbour_results,
    }
    return {
        "best_trial_number": best.number,
        "best_value": best.value,
        "best_params": dict(best.params),
        "fold_by_fold": {
            "fold_scores": fold_scores,
            "fold_metrics": fold_metrics,
            "median_fold_score": best.user_attrs.get("median_fold_score"),
            "penalty_breakdown": best.user_attrs.get("penalty_breakdown") or {},
        },
        "stability": {
            "fold_score_variance": fold_variance,
            "n_folds": len(fold_scores),
        },
        "robustness": robustness,
    }


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

    A study-start preflight (:func:`preflight.run_preflight`) refuses the run
    when realism prerequisites fail — a ``smoke_fixture`` config without
    ``allow_smoke``, a failing required data-quality check, or quote coverage
    below the configured threshold.

    The final-holdout window is reserved at the tail; it is NEVER scored here.
    Score it once, after tuning, via :func:`optuna.holdout.score_final_holdout`.
    """
    log = log or _log()
    cfg = load_config(config_path)
    sim_cfg = SimulationConfig.model_validate(cfg.get("simulation") or {})

    # Realism remediation 2 Phase 0: refuse to start a study whose config
    # diverges from the frozen contract without a declared parity sidecar.
    assert_optuna_config_parity(cfg)

    # Fast-fail the smoke-mode refusal before any expensive plan building /
    # dataset probing. The full preflight below re-asserts it (and the DQ /
    # quote-coverage gates) so the study metadata records the complete result.
    if sim_cfg.mode == "smoke_fixture" and not allow_smoke:
        run_preflight(sim_mode=sim_cfg.mode, allow_smoke=allow_smoke)

    paths = BowakaV2Paths.from_config(cfg, repo_root=_REPO_ROOT)
    paths.assert_strategy_isolation()

    optuna_cfg = cfg.get("optuna", {}) or {}
    wf = optuna_cfg.get("walkforward", {}) or {}
    bt = cfg.get("backtest", {}) or {}
    md = cfg.get("market_data", {}) or {}
    search_space_overrides = dict(optuna_cfg.get("search_space_overrides") or {})

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

    # ---- study-start preflight (Phase 9, Task 3) --------------------------
    # Build the dataset's data-quality report and probe quote coverage, then
    # refuse the study if a realism prerequisite fails. This runs BEFORE any
    # trial — a multi-hour study must not start against an un-usable dataset.
    dq_report = None
    quote_cov_pct = None
    probe_sessions: list[_dt.date] = []
    try:
        from ..data.data_quality import build_data_quality_report
        from ..data.lineage import build_dataset_lineage

        # Probe the first validation window — representative + cheap.
        first = plan.splits[0]
        probe_sessions = _xnys_sessions(first.val_start, first.val_end)[:5]
        minute_supplier, daily_supplier = make_lake_suppliers(
            lake_root, feed=feed,
            intraday_window_policy=resolve_intraday_window_policy(cfg),
        )
        lineage = build_dataset_lineage(
            cfg=cfg, symbols=symbols,
            start=probe_sessions[0] if probe_sessions else None,
            end=probe_sessions[-1] if probe_sessions else None,
            lab_config_hash=_hash({k: v for k, v in cfg.items() if k != "_source_path"}),
        )
        dq_report = build_data_quality_report(
            cfg=cfg, lineage=lineage, requested_symbols=symbols,
            sessions=probe_sessions, daily_bars_supplier=daily_supplier,
            minute_bars_supplier=minute_supplier,
            scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
        )
        quote_supplier = make_quote_supplier(lake_root, feed=feed)
        quote_cov_pct = probe_quote_coverage(
            symbols=symbols, sessions=probe_sessions, quote_supplier=quote_supplier,
            scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
        )
    except Exception as exc:  # noqa: BLE001 — a probe failure must not silently skip preflight
        log.warning("preflight probe degraded (%s); checks run on available signals", exc)

    preflight = run_preflight(
        sim_mode=sim_cfg.mode,
        allow_smoke=allow_smoke,
        dq_report=dq_report,
        quote_coverage_pct=quote_cov_pct,
        min_quote_coverage_pct=float(sim_cfg.min_quote_coverage_pct),
    )
    log.info("preflight passed: %d checks", len(preflight.checks))

    # Report the ACTUAL per-fold trading universe — the daily point-in-time set
    # each fold builds, NOT the capped preflight-probe sample. A representative
    # single-session count; the eligible set changes day to day.
    universe_pit_sample = None
    try:
        from bowaka_common.marketdata import MarketDataStore

        if probe_sessions:
            _pit = build_pit_universe_for_sessions(
                probe_sessions[:1], cfg, MarketDataStore(lake_root)
            )
            _ps = probe_sessions[0]
            universe_pit_sample = {
                "session": _ps.isoformat(),
                "eligible_symbols": len(eligible_symbols(_pit.get(_ps, {}))),
            }
    except Exception as exc:  # noqa: BLE001 — a universe-sample probe is non-fatal
        log.warning("PIT universe sample probe failed: %s", exc)

    trials = int(n_trials if n_trials is not None else optuna_cfg.get("n_trials", 20))
    jobs = int(n_jobs if n_jobs is not None else optuna_cfg.get("n_jobs", 1))
    startup = int(
        n_startup_trials if n_startup_trials is not None else optuna_cfg.get("n_startup_trials", 10)
    )
    seed = int((cfg.get("run") or {}).get("seed", 1337))
    code_hash = _git_head()
    lab_config_hash = _hash({k: v for k, v in cfg.items() if k != "_source_path"})
    dataset_hash = _hash(
        [symbols, feed, str(plan.splits[0].train_start), str(plan.splits[-1].val_end)]
    )

    study = OptunaStudy(
        feed=feed,
        cost_stress=str(bt.get("cost_stress", "conservative")),
        dataset_hash=dataset_hash,
        config_hash=lab_config_hash,
        storage_uri=optuna_cfg.get("storage") or None,
        n_trials=trials,
        n_jobs=jobs,
        n_startup_trials=startup,
    )
    study.create()

    # ---- study metadata (Phase 9, Task 4) --------------------------------
    fold_definitions = [
        {
            "fold_index": i,
            "train_start": s.train_start.isoformat(),
            "train_end": s.train_end.isoformat(),
            "val_start": s.val_start.isoformat(),
            "val_end": s.val_end.isoformat(),
        }
        for i, s in enumerate(plan.splits)
    ]
    holdout_definition = {
        "final_holdout_start": plan.final_holdout_start.isoformat(),
        "final_holdout_end": plan.final_holdout_end.isoformat(),
    }
    sampler = study.study.sampler
    pruner = study.study.pruner
    # Realism remediation 2 Phase 0: every study artifact declares the simulation
    # contract (== the simulation mode) and the mechanical suitability tier. The
    # tier is the contract cap, further capped to research_only for the IEX feed.
    simulation_contract = sim_cfg.mode
    suitability_tier = tier_for_simulation_contract(simulation_contract)
    if feed == "iex" and suitability_tier != "research_only":
        suitability_tier = "research_only"
    study_metadata = {
        "dataset_hash": dataset_hash,
        "lab_config_hash": lab_config_hash,
        "code_hash": code_hash,
        "seed": seed,
        "sampler": type(sampler).__name__,
        "sampler_config": {
            "n_startup_trials": startup,
            "multivariate": True,
            "seed": 1337,
        },
        "pruner": type(pruner).__name__,
        "fold_definitions": fold_definitions,
        "holdout_definition": holdout_definition,
        "search_space_version": SEARCH_SPACE_VERSION,
        "simulation_mode": sim_cfg.mode,
        "simulation_contract": simulation_contract,
        "suitability_tier": suitability_tier,
        "feed": feed,
        "preflight": preflight.as_dict(),
        "penalty_weights": vars(DEFAULT_PENALTY_WEIGHTS),
        "search_space_overrides": search_space_overrides,
    }
    for key, value in study_metadata.items():
        study.study.set_user_attr(key, value)

    log.info(
        "walk-forward study %s: %d trials (%d random startup) x %d folds, feed=%s, "
        "search_space_version=%d; per-fold universe = daily point-in-time set%s "
        "(preflight probe sampled %d symbols)",
        study.study.study_name, trials, startup, len(plan.splits), feed,
        SEARCH_SPACE_VERSION,
        (
            f" (~{universe_pit_sample['eligible_symbols']} eligible on "
            f"{universe_pit_sample['session']})"
            if universe_pit_sample else ""
        ),
        len(symbols),
    )
    objective = make_walkforward_objective(
        cfg, plan, lake_root=lake_root, feed=feed, symbols=symbols,
        paths=paths, holdout_guard=holdout_guard, log=log,
        search_space_overrides=search_space_overrides,
    )
    study.optimize(objective)

    import optuna

    completed = [t for t in study.study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    # Explicit ranked list — never study.best_trial (a zero-completed study would raise).
    ranked = sorted(
        (t for t in completed if t.value is not None),
        key=lambda t: t.value, reverse=True,
    )
    best = ranked[0] if ranked else None

    # ---- best-trial reporting (Phase 9, Task 5) --------------------------
    best_report: dict[str, Any] = {}
    if best is not None:
        try:
            best_report = build_best_trial_report(
                best, cfg, plan, lake_root=lake_root, feed=feed, symbols=symbols,
                paths=paths, holdout_guard=holdout_guard, log=log,
                search_space_overrides=search_space_overrides,
            )
        except Exception as exc:  # noqa: BLE001 — reporting failure must not lose the study
            log.warning("best-trial report failed: %s", exc)
            best_report = {"error": str(exc)}

    # Top-k parameter clustering across the best trials (stability rank input).
    top_k = [dict(t.params) for t in ranked[:5]]
    clustering = top_k_cluster_stability(top_k) if len(top_k) >= 2 else {
        "stable": True, "max_cv": 0.0, "param_cvs": {},
    }

    out = {
        "status": "ok",
        "study_name": study.study.study_name,
        "simulation_mode": sim_cfg.mode,
        # Realism remediation 2 Phase 0: top-level run/study labels.
        "simulation_contract": simulation_contract,
        "suitability_tier": suitability_tier,
        "feed": feed,
        "search_space_version": SEARCH_SPACE_VERSION,
        "n_trials_requested": trials,
        "n_trials_completed": len(completed),
        "n_startup_trials": startup,
        "n_folds": len(plan.splits),
        "universe": {
            "selection": "daily_point_in_time",
            "note": (
                "each fold rebuilds the per-session PIT universe from the lake "
                "(exchange / price-band / ADV / exclusion / blocklist filters) — "
                "the trading universe is NOT capped and changes daily, like the "
                "live scanner"
            ),
            "preflight_probe_symbols": len(symbols),
            "pit_sample": universe_pit_sample,
        },
        "final_holdout": [
            plan.final_holdout_start.isoformat(),
            plan.final_holdout_end.isoformat(),
        ],
        "final_holdout_scored": False,  # Phase 9: only `--final-holdout` scores it.
        "best_value": (best.value if best else None),
        "best_params": (dict(best.params) if best else {}),
        "best_trial_report": best_report,
        "top_k_clustering": clustering,
        "study_metadata": study_metadata,
    }
    results_path = Path(paths.artifact_root) / "optuna" / f"{study.study.study_name}.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    out["results_path"] = str(results_path)
    log.info("walk-forward study done: %d/%d trials completed, best=%s",
             len(completed), trials, out["best_value"])
    return out


__all__ = [
    "apply_trial_params",
    "make_walkforward_objective",
    "build_best_trial_report",
    "run_walkforward_study",
    "assert_optuna_config_parity",
    "OptunaParityError",
]
