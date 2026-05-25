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
import statistics
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

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
from .calendar_sessions import calendar_sessions_half_open
from ..utils.memory_guard import MemoryBudget
from .dispatcher import OptunaStudy, run_bowaka_optimization_dispatch
from .errors import OptunaStudyInvalidError, structural_exceptions
from .fold_context import (
    FoldRuntimeContext,
    assert_search_space_does_not_affect_context,
    build_fold_contexts,
    build_holdout_context,
)
from .holdout_guard import HoldoutGuard
from .objective import (
    DEFAULT_PENALTY_WEIGHTS,
    FoldResult,
    compute_objective,
    fold_result_from_backtest_result,
    fold_result_from_report,
    fold_score,
)
from .preflight import PreflightError, probe_quote_coverage, run_preflight
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


class CurrentCodeParityStudyRefused(RuntimeError):
    """Raised when an Optuna study against ``current_code_parity`` runs without the
    explicit ``--allow-current-code-parity-study --tier research_only`` opt-in.

    Realism remediation 2 Phase 8 (audit §P0-011). Bayesian optimization on a
    config that reproduces the live code's *warts* (zero-spread quote fallback,
    no halt gate) optimizes the simulator's artifacts, not the strategy's edge.
    The gate forces the operator to explicitly acknowledge this is a paper-
    reconciliation study, not a parameter recommendation.
    """


class IntendedRealismDataInsufficient(RuntimeError):
    """Raised when an ``intended_realism`` Optuna study would run against a lake
    that does not meet the realism prerequisites (real quote coverage,
    adjusted/split-adjusted daily bars).

    Realism remediation 2 Phase 8 (audit §P0-011). Optimizing on
    ``intended_realism`` against a lake without the data the contract needs would
    silently fall back to synthetic quotes / unadjusted bars — exactly the
    failure mode the audit calls out.
    """


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


_AUDIT_PTR = "docs/audits/2026-05-22_realism_audit.md §P0-011"


def assert_simulation_contract_admissible(
    cfg: Mapping[str, Any],
    *,
    allow_current_code_parity_study: bool,
    tier: str | None,
) -> None:
    """Refuse a study whose simulation contract is not admissible (audit §P0-011).

    Realism remediation 2 Phase 8 — the contract-cap rule is mechanical:

    - ``current_code_parity`` is refused unless the operator passes
      ``--allow-current-code-parity-study --tier research_only`` (CLI) /
      ``allow_current_code_parity_study=True, tier="research_only"`` (in-process).
    - ``intended_realism`` and ``smoke_fixture`` are admissible at this gate (the
      ``intended_realism`` data-prerequisite gate runs separately, after dataset
      probing in :func:`run_walkforward_study`).

    Raises :class:`CurrentCodeParityStudyRefused` with a pointer to the audit
    section. Never lowers the cap on a properly-opted-in study — that cap is
    enforced by :func:`tier_for_simulation_contract` (Phase 0).
    """
    sim = cfg.get("simulation") or {}
    mode = sim.get("mode") if isinstance(sim, dict) else None
    if mode != "current_code_parity":
        return
    if allow_current_code_parity_study and str(tier) == "research_only":
        return
    raise CurrentCodeParityStudyRefused(
        "Optuna study refused: simulation.mode is 'current_code_parity'. "
        "Bayesian optimization on the live-code-with-warts contract is "
        "paper-reconciliation-only — pass --allow-current-code-parity-study "
        "--tier research_only (CLI) or "
        "allow_current_code_parity_study=True, tier='research_only' "
        f"(in-process) to opt in explicitly. See {_AUDIT_PTR}."
    )


def assert_intended_realism_data_prerequisites(
    cfg: Mapping[str, Any],
    *,
    dq_report: Optional[Mapping[str, Any]],
    quote_coverage_pct: Optional[float],
    min_quote_coverage_pct: float,
) -> None:
    """Refuse an ``intended_realism`` study when the lake cannot support it.

    Realism remediation 2 Phase 8 (audit §P0-011) — three mechanical prereqs:

    1. ``market_data.require_adjusted_daily_bars`` is ``True`` in the config
       (the contract value; without it the DQ stack cannot fail closed on raw
       daily bars).
    2. Coverage gates pass — the dataset's DQ report has no failing required
       check (the existing :func:`preflight.run_preflight` already gates this for
       ``intended_realism``; this gate makes the refusal explicit + early).
    3. Real historical quote coverage is at or above the threshold (default
       95%); below it the realism simulator falls back to a degraded quote model.

    A ``None`` DQ report / quote-coverage measurement does NOT fail this gate —
    the cheaper preflight already records a ``skipped`` check and the new
    per-fold preflight (Task 5) gates it for real before any trial runs. This
    gate is the hard early-fail when we *have* measured the lake and it is
    insufficient. Raises :class:`IntendedRealismDataInsufficient`.
    """
    sim = cfg.get("simulation") or {}
    mode = sim.get("mode") if isinstance(sim, dict) else None
    if mode != "intended_realism":
        return
    md = cfg.get("market_data") or {}
    require_adjusted = bool(md.get("require_adjusted_daily_bars", False))
    if not require_adjusted:
        raise IntendedRealismDataInsufficient(
            "Optuna study refused: simulation.mode is 'intended_realism' but "
            "market_data.require_adjusted_daily_bars is not True. The intended-"
            "realism contract requires adjusted daily bars (see actual contract "
            "data.require_adjusted_daily_bars). Set the field to True (the "
            "import-actual-config mapper does this by default) or use "
            f"current_code_parity instead. See {_AUDIT_PTR}."
        )
    if dq_report is not None:
        required_failures = list(dq_report.get("required_failures") or [])
        if required_failures:
            raise IntendedRealismDataInsufficient(
                "Optuna study refused: simulation.mode is 'intended_realism' but "
                f"the dataset's data-quality report has {len(required_failures)} "
                f"failing required check(s): {sorted(required_failures)}. The lake "
                "cannot support a research-grade optimization. Fix the lake or use "
                f"current_code_parity. See {_AUDIT_PTR}."
            )
    if quote_coverage_pct is not None:
        if float(quote_coverage_pct) < float(min_quote_coverage_pct):
            raise IntendedRealismDataInsufficient(
                "Optuna study refused: simulation.mode is 'intended_realism' but "
                f"real historical quote coverage is {float(quote_coverage_pct):.2f}% "
                f", below the required {float(min_quote_coverage_pct):.2f}%. "
                "Backfill SIP / NBBO quotes for the requested universe or use "
                f"current_code_parity. See {_AUDIT_PTR}."
            )


def _to_date(value: Any) -> _dt.date:
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    return pd.Timestamp(value).date()


def _xnys_sessions(start: _dt.date, end: _dt.date) -> list[_dt.date]:
    """Half-open ``[start, end)`` XNYS sessions (speedup report §3, audit §P0-002).

    Delegates to :func:`calendar_sessions_half_open` so the walk-forward
    runner and :mod:`.pit_universe` cannot drift. ``val_end ==
    final_holdout_start`` no longer leaks the holdout's first session.
    """
    return calendar_sessions_half_open(start, end)


def _resolve_symbols(
    cfg: dict,
    md: dict,
    *,
    cap: int = 100,
    sim_mode: Optional[str] = None,
    plan: Any = None,
) -> list[str]:
    """A symbol sample for study-start preflight probing — NOT the trading universe.

    Audit 2026-05-23 §6.6 / Phase 1 — under ``intended_realism`` the preflight
    must probe the *full per-fold PIT eligible-universe union* (no cap). The
    capped 100-symbol sample silently underreported coverage. Other modes
    (parity / smoke / research_only with an explicit waiver) keep the capped
    behaviour because their preflight is plumbing, not coverage proof.

    Explicit ``universe.symbols`` > full PIT union (intended_realism) >
    lake-derived (capped at ``cap``) > synthetic.

    The walk-forward folds themselves trade the per-session PIT universe
    rebuilt at fold-time from the lake asset master + filters — daily,
    uncapped, exactly like the live scanner. This helper produces the
    *preflight probe* symbol set only.
    """
    explicit = (cfg.get("universe", {}) or {}).get("symbols")
    if explicit:
        return [str(s) for s in explicit]

    preflight_cfg = (cfg.get("optuna") or {}).get("preflight") or {}
    research_waiver = bool(preflight_cfg.get("research_waiver_capped_symbols", False))
    is_lake = str(md.get("minute_bar_source", "fixture")) in ("alpaca", "shared")

    if sim_mode == "intended_realism" and plan is not None and is_lake and not research_waiver:
        from .pit_universe import plan_pit_symbol_union

        union = plan_pit_symbol_union(
            md.get("shared_root"), feed=md.get("feed", "iex"),
            plan=plan, cfg=cfg, include_holdout=True,
        )
        if not union:
            # The lake was probed but the PIT union was empty — fall back to
            # the lake-available symbols. The preflight DQ check will surface
            # the underlying lake gap.
            from bowaka_common.marketdata import available_symbols

            return available_symbols(
                md.get("shared_root"), timeframe="1d",
                feed=md.get("feed", "iex"),
            )
        return sorted(union)

    if is_lake:
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
    ctx: Optional[FoldRuntimeContext] = None,
) -> dict:
    """Run one real backtest over a walk-forward validation window.

    Returns the run ``summary`` dict; when ``return_report`` is set the
    substantive Phase-8 ``report.json`` document is attached under the
    ``"_report"`` key (so the objective can use the DAILY mark-to-market
    drawdown rather than the closed-trade ``summary.max_drawdown_pct``).

    Speedup report §5.2 / §11.2 Phase 2: when ``ctx`` is supplied the
    sessions / PIT universe / daily cache / supplier callables are read
    from the precomputed :class:`FoldRuntimeContext` rather than rebuilt
    here. The legacy (no-ctx) code path is preserved for callers that
    haven't been migrated yet — it is semantically identical, only slower.
    """
    if ctx is None:
        sessions = _xnys_sessions(val_start, val_end)
        if not sessions:
            return {}
        from bowaka_common.marketdata import MarketDataStore

        minute_supplier, daily_supplier = make_lake_suppliers(
            lake_root, feed=feed,
            intraday_window_policy=resolve_intraday_window_policy(cfg),
        )
        quote_supplier = make_quote_supplier(
            lake_root, feed=feed,
            default_max_age_seconds=float(
                (cfg.get("execution") or {}).get("max_quote_age_seconds", 60)
            ),
        )
        forward_minute_supplier = make_forward_minute_supplier(lake_root, feed=feed)
        universe = build_pit_universe_for_sessions(sessions, cfg, MarketDataStore(lake_root))
        daily_cache = {}
        for s in sessions:
            sess_syms = eligible_symbols(universe.get(s, {})) or symbols
            daily_cache[s] = build_daily_cache_from_lake(lake_root, sess_syms, s, feed=feed)
        scan_times_callable = lambda d: scan_times_for_session(d, cfg)  # noqa: E731
    else:
        sessions = list(ctx.sessions)
        if not sessions:
            return {}
        universe = ctx.universe_by_session
        daily_cache = dict(ctx.daily_cache_by_session)
        minute_supplier = ctx.suppliers.minute
        daily_supplier = ctx.suppliers.daily
        quote_supplier = ctx.suppliers.quote
        forward_minute_supplier = ctx.suppliers.forward_minute
        _scan_times = dict(ctx.scan_times_by_session)
        scan_times_callable = lambda d: list(_scan_times.get(d, ()))  # noqa: E731

    run_dir = Path(tempfile.mkdtemp(prefix="bowaka_wf_fold_"))
    try:
        # Realism Phase 4: each walk-forward fold replays the full intraday
        # scan cadence (was one hard-coded 14:00-UTC scan per session).
        result = run_backtest(
            cfg=cfg,
            sessions=sessions,
            scan_times_per_session=scan_times_callable,
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


def _run_fold_backtest_objective(
    cfg: dict,
    *,
    val_start: _dt.date,
    val_end: _dt.date,
    lake_root: Any,
    feed: str,
    symbols: list[str],
    paths: BowakaV2Paths,
    ctx: Optional[FoldRuntimeContext] = None,
) -> Optional[Any]:
    """Run one fold backtest in ``artifact_mode="objective_minimal"`` and
    return the in-memory :class:`BacktestResult` (or ``None`` for an empty
    session window). Speedup report §5.1–§5.2 / §11.2 Phases 1 & 2.

    When ``ctx`` is supplied the sessions / PIT universe / daily cache /
    supplier callables are read from the precomputed
    :class:`FoldRuntimeContext` rather than rebuilt here (the Phase 2
    fast path). The legacy (no-ctx) code path is preserved for callers
    that haven't been migrated yet — it is semantically identical, only
    slower.
    """
    if ctx is None:
        sessions = _xnys_sessions(val_start, val_end)
        if not sessions:
            return None
        from bowaka_common.marketdata import MarketDataStore

        minute_supplier, daily_supplier = make_lake_suppliers(
            lake_root, feed=feed,
            intraday_window_policy=resolve_intraday_window_policy(cfg),
        )
        quote_supplier = make_quote_supplier(
            lake_root, feed=feed,
            default_max_age_seconds=float(
                (cfg.get("execution") or {}).get("max_quote_age_seconds", 60)
            ),
        )
        forward_minute_supplier = make_forward_minute_supplier(lake_root, feed=feed)
        universe = build_pit_universe_for_sessions(sessions, cfg, MarketDataStore(lake_root))
        daily_cache: dict[_dt.date, Any] = {}
        for s in sessions:
            sess_syms = eligible_symbols(universe.get(s, {})) or symbols
            daily_cache[s] = build_daily_cache_from_lake(lake_root, sess_syms, s, feed=feed)
        scan_times_callable = lambda d: scan_times_for_session(d, cfg)  # noqa: E731
    else:
        sessions = list(ctx.sessions)
        if not sessions:
            return None
        universe = ctx.universe_by_session
        daily_cache = dict(ctx.daily_cache_by_session)
        minute_supplier = ctx.suppliers.minute
        daily_supplier = ctx.suppliers.daily
        quote_supplier = ctx.suppliers.quote
        forward_minute_supplier = ctx.suppliers.forward_minute
        _scan_times = dict(ctx.scan_times_by_session)
        scan_times_callable = lambda d: list(_scan_times.get(d, ()))  # noqa: E731

    run_dir = Path(tempfile.mkdtemp(prefix="bowaka_wf_fold_min_"))
    try:
        result = run_backtest(
            cfg=cfg,
            sessions=sessions,
            scan_times_per_session=scan_times_callable,
            universe_snapshot_by_session=universe,
            daily_cache_by_session=daily_cache,
            minute_bars_supplier=minute_supplier,
            daily_bars_supplier=daily_supplier,
            quote_supplier=quote_supplier,
            forward_minute_supplier=forward_minute_supplier,
            initial_bankroll=100_000.0,
            paths=paths,
            run_dir=run_dir,
            artifact_mode="objective_minimal",
        )
        return result
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
    objective_artifact_mode: str = "full",
    fold_contexts: Optional[tuple[Optional[FoldRuntimeContext], ...]] = None,
) -> list[FoldResult]:
    """Run a real backtest over every walk-forward validation window.

    The single fold-execution path shared by the per-trial objective and the
    best-trial neighbourhood robustness sweep. The :class:`HoldoutGuard` is
    asserted per fold so tuning can never read the final-holdout window; a fold
    that raises degrades to :func:`_degraded_fold` rather than aborting.

    Speedup report §5.1 / §11.2 Phase 1: when ``objective_artifact_mode ==
    "objective_minimal"`` the per-fold backtest skips every disk artifact
    write and the converter is :func:`fold_result_from_backtest_result`.
    Default ``"full"`` preserves the legacy ``report.json``-reading path,
    so neighbor reruns and any non-objective caller stay byte-stable.
    """
    folds: list[FoldResult] = []
    # Audit 2026-05-23 §P0-001: structural exceptions (HoldoutGuardError,
    # PreflightError, DataQualityError, MissingLakePartitionError,
    # ConfigParityError, OptunaStudyInvalidError) MUST NOT be swallowed as a
    # degraded fold — they indicate a bug in the lab plumbing, not a noisy
    # strategy/eval error, and the broad ``except Exception`` would mask them
    # behind a sentinel score. They propagate out of the trial; the study
    # runner then aborts with OptunaStudyInvalidError.
    structural = structural_exceptions()
    for i, split in enumerate(plan.splits):
        holdout_guard.assert_can_read(split.val_start, split.val_end)
        fold_id = f"f{i}_{split.val_start.isoformat()}"
        ctx = fold_contexts[i] if (fold_contexts is not None and i < len(fold_contexts)) else None
        try:
            if objective_artifact_mode == "objective_minimal":
                result = _run_fold_backtest_objective(
                    trial_cfg,
                    val_start=split.val_start, val_end=split.val_end,
                    lake_root=lake_root, feed=feed, symbols=symbols, paths=paths,
                    ctx=ctx,
                )
                if result is None:
                    # An empty session window — legacy path returns empty
                    # summary; build a zero-trade degraded result so the
                    # fold still records in the trial.
                    folds.append(_fold_result(fold_id, {}))
                else:
                    folds.append(fold_result_from_backtest_result(fold_id, result))
            else:
                summary = _run_fold_backtest(
                    trial_cfg,
                    val_start=split.val_start, val_end=split.val_end,
                    lake_root=lake_root, feed=feed, symbols=symbols, paths=paths,
                    return_report=True, ctx=ctx,
                )
                folds.append(_fold_result(fold_id, summary))
        except structural:
            raise
        except Exception as exc:  # noqa: BLE001 — non-structural strategy/eval error may degrade
            log.warning("fold %s failed non-structurally: %s", fold_id, exc)
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
    fold_contexts: Optional[tuple[Optional[FoldRuntimeContext], ...]] = None,
) -> tuple[float, list[FoldResult]]:
    """Run every validation fold for ``params``; return ``(objective, folds)``."""
    folds = _run_validation_folds(
        apply_trial_params(base_cfg, params), plan,
        lake_root=lake_root, feed=feed, symbols=symbols, paths=paths,
        holdout_guard=holdout_guard, log=log,
        fold_contexts=fold_contexts,
    )
    return compute_objective(folds).objective, folds


def make_walkforward_objective_for_worker(
    config_path: str,
    *,
    search_space_overrides: Optional[dict[str, Any]] = None,
    incumbent_params: Optional[dict[str, Any]] = None,
    dataset_hash: Optional[str] = None,
    config_hash: Optional[str] = None,
    code_hash: Optional[str] = None,
    objective_artifact_mode: str = "objective_minimal",
    cached_suppliers: bool = True,
) -> Callable[[Any], float]:
    """Worker-side objective factory (speedup report §6.1 / §11.3 Phase 5).

    The parallel dispatcher imports this via the dotted reference
    ``bowaka_v2_lab.optuna.walkforward_runner:make_walkforward_objective_for_worker``
    and calls it inside each worker subprocess with ``factory_kwargs``.
    The worker rebuilds the per-fold runtime contexts from scratch
    (one-shot cost amortized over the worker's trial slice) so the parent
    process's closures (which capture large pandas frames) do NOT have to
    be pickled across the process boundary.
    """
    cfg = load_config(config_path)
    repo_root = Path(__file__).resolve().parents[5]
    paths = BowakaV2Paths.from_config(cfg, repo_root=repo_root)

    sim_cfg = SimulationConfig.model_validate(cfg.get("simulation") or {})
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
    lake_root = md.get("shared_root")
    symbols = _resolve_symbols(cfg, md, sim_mode=sim_cfg.mode, plan=plan)
    holdout_guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
    assert_search_space_does_not_affect_context(search_space_overrides)
    fold_contexts = build_fold_contexts(
        cfg, plan, lake_root=lake_root, feed=feed, symbols=symbols,
        paths=paths, holdout_guard=holdout_guard,
        cached_suppliers=bool(cached_suppliers),
    )
    return make_walkforward_objective(
        cfg, plan, lake_root=lake_root, feed=feed, symbols=symbols,
        paths=paths, holdout_guard=holdout_guard, log=_log(),
        search_space_overrides=search_space_overrides,
        incumbent_params=incumbent_params,
        dataset_hash=dataset_hash,
        config_hash=config_hash,
        code_hash=code_hash,
        objective_artifact_mode=objective_artifact_mode,
        fold_contexts=fold_contexts,
    )


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
    incumbent_params: Optional[Mapping[str, Any]] = None,
    dataset_hash: Optional[str] = None,
    config_hash: Optional[str] = None,
    code_hash: Optional[str] = None,
    # Speedup report §5.1 / §11.2 Phase 1 — opt-in fast path: skip every
    # disk artifact write in the per-trial fold backtests. Default ``"full"``
    # preserves the legacy ``report.json``-reading flow until Phase 5 (where
    # the actual optuna configs flip the flag on after the Phase 1 parity
    # tests prove identical FoldResults).
    objective_artifact_mode: str = "full",
    # Speedup report §5.2 / §11.2 Phase 2 — precomputed per-fold context
    # (sessions, scan_times, PIT universe, daily cache, suppliers). When
    # supplied, the per-trial folds skip rebuilding any of these. ``None``
    # preserves the legacy per-trial path so callers that haven't been
    # migrated still work.
    fold_contexts: Optional[tuple[Optional[FoldRuntimeContext], ...]] = None,
) -> Callable[[Any], float]:
    """Build the Optuna objective: median fold score over real per-fold backtests.

    Realism remediation 2 Phase 8: ``incumbent_params``, when supplied, pins
    trial 0 to that parameter set (the ``--incumbent-trial`` flag reads it from
    the frozen contract). ``dataset_hash`` / ``config_hash`` / ``code_hash`` are
    persisted as per-trial user_attrs so a study's lineage is queryable on the
    Optuna side (audit §P1-005).
    """

    # Audit 2026-05-23 §P0-001 — structural exceptions escape the trial so the
    # study runner can abort with OptunaStudyInvalidError; only non-structural
    # strategy/eval errors degrade to ``_FAILED_TRIAL_SCORE``.
    structural = structural_exceptions()

    def objective(trial: Any) -> float:
        try:
            # Realism remediation 2 Phase 8 (incumbent baseline): trial 0 with
            # incumbent_params runs the actual-contract parameter set verbatim
            # so the optimizer's best can be compared against the live config.
            if incumbent_params and getattr(trial, "number", -1) == 0:
                params = _suggest_incumbent_params(
                    trial, incumbent_params,
                    overrides=search_space_overrides,
                )
                trial.set_user_attr("incumbent_trial", True)
            else:
                params = suggest_params(trial, overrides=search_space_overrides)
            folds = _run_validation_folds(
                apply_trial_params(base_cfg, params), plan,
                lake_root=lake_root, feed=feed, symbols=symbols, paths=paths,
                holdout_guard=holdout_guard, log=log,
                objective_artifact_mode=objective_artifact_mode,
                fold_contexts=fold_contexts,
            )
            result = compute_objective(folds)
            trial.set_user_attr("fold_scores", result.fold_scores)
            trial.set_user_attr("n_folds", len(folds))
            trial.set_user_attr("fold_variance", result.fold_variance)
            trial.set_user_attr("median_fold_score", result.median_fold_score)
            trial.set_user_attr("penalty_breakdown", result.penalty_breakdown)
            # Realism remediation 2 Phase 8 (audit §P1-008) — explicit term
            # breakdown for every trial; downstream tooling can read the
            # contribution of every objective term.
            trial.set_user_attr("objective_terms", result.objective_terms)
            trial.set_user_attr(
                "fold_metrics", [{"fold_id": f.fold_id, **f.metrics} for f in folds]
            )
            # Realism remediation 2 Phase 8 (audit §P1-005) — per-trial lineage.
            if dataset_hash is not None:
                trial.set_user_attr("dataset_hash", dataset_hash)
            if config_hash is not None:
                trial.set_user_attr("config_hash", config_hash)
            if code_hash is not None:
                trial.set_user_attr("code_hash", code_hash)
            return result.objective
        except structural:
            raise
        except Exception as exc:  # noqa: BLE001 — one bad trial must not abort the study
            log.error("trial %s failed entirely: %s", getattr(trial, "number", "?"), exc)
            return _FAILED_TRIAL_SCORE

    return objective


def _suggest_incumbent_params(
    trial: Any,
    incumbent_params: Mapping[str, Any],
    *,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pin every search-space parameter to its incumbent value for trial 0.

    Calls ``trial.suggest_*`` for every name in the resolved search space so
    Optuna records the incumbent params in the trial (otherwise Optuna would
    not know about them). Each suggestion is constrained to the incumbent
    value: ``suggest_float`` low/high collapsed to the value, ``suggest_int``
    likewise, ``suggest_categorical`` with a singleton choice. Out-of-range
    incumbents are clamped to the search-space bounds so the suggest call
    succeeds (the incumbent is the live config; clamping is rare and reported
    via trial.user_attrs["incumbent_clamped"]).
    """
    from .search_space import resolve_search_space

    spec = resolve_search_space(overrides)
    out: dict[str, Any] = {}
    clamped: dict[str, dict[str, Any]] = {}
    for name, entry in spec.items():
        if name not in incumbent_params:
            # Fall back to a regular suggestion for any param the incumbent
            # doesn't declare — the optimizer can still sample it.
            kind = entry[0]
            if kind == "uniform":
                out[name] = trial.suggest_float(name, entry[1], entry[2])
            elif kind == "int":
                out[name] = trial.suggest_int(name, entry[1], entry[2])
            elif kind == "log_uniform":
                out[name] = trial.suggest_float(name, entry[1], entry[2], log=True)
            elif kind == "categorical":
                out[name] = trial.suggest_categorical(name, list(entry[1]))
            continue
        target = incumbent_params[name]
        kind = entry[0]
        if kind == "uniform" or kind == "log_uniform":
            lo, hi = float(entry[1]), float(entry[2])
            clamped_val = float(min(hi, max(lo, float(target))))
            if clamped_val != float(target):
                clamped[name] = {"target": target, "clamped": clamped_val, "range": [lo, hi]}
            # Optuna requires lo < hi to make a "fixed" suggestion;
            # use suggest_float with the exact range and let TPE record the value.
            # We can't pin to a single point; instead pass a tiny range around it.
            eps = max(abs(clamped_val) * 1e-9, 1e-12)
            lo_p = max(lo, clamped_val - eps)
            hi_p = min(hi, clamped_val + eps)
            if hi_p <= lo_p:
                hi_p = lo_p + eps  # safety
            log_flag = (kind == "log_uniform")
            if log_flag and (lo_p <= 0 or hi_p <= 0):
                # log_uniform requires strictly positive; fall back to non-log
                log_flag = False
            out[name] = trial.suggest_float(name, lo_p, hi_p, log=log_flag)
        elif kind == "int":
            lo, hi = int(entry[1]), int(entry[2])
            clamped_val = int(min(hi, max(lo, int(target))))
            if clamped_val != int(target):
                clamped[name] = {"target": target, "clamped": clamped_val, "range": [lo, hi]}
            out[name] = trial.suggest_int(name, clamped_val, clamped_val)
        elif kind == "categorical":
            choices = list(entry[1])
            chosen = target if target in choices else (choices[0] if choices else target)
            if chosen != target:
                clamped[name] = {"target": target, "clamped": chosen, "choices": choices}
            out[name] = trial.suggest_categorical(name, [chosen])
        else:
            out[name] = target
    if clamped:
        trial.set_user_attr("incumbent_clamped", clamped)
    return out


def _incumbent_baseline_params() -> dict[str, Any]:
    """Read the actual-contract parameter set used as trial 0 (the incumbent).

    Reads the frozen contract via :mod:`bowaka_v2_lab.reference` and projects
    every search-space key to the equivalent contract value (dotted-path lookup).
    A parameter not present in the contract (e.g. a lab-only knob) is omitted
    from the returned dict — the optimizer will sample it normally for trial 0.
    """
    from ..reference import contract_available, load_actual_contract
    from .search_space import SEARCH_SPACE_SPEC

    if not contract_available():
        return {}
    contract = load_actual_contract()
    out: dict[str, Any] = {}
    for name in SEARCH_SPACE_SPEC:
        parts = name.split(".")
        node: Any = contract
        ok = True
        for p in parts:
            if isinstance(node, dict) and p in node:
                node = node[p]
            else:
                ok = False
                break
        if ok and node is not None:
            out[name] = node
    return out


def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _write_failed_study_artifact(
    *,
    paths: BowakaV2Paths,
    study_name: str,
    study_metadata: dict[str, Any],
    failure_reason: str,
    sim_cfg: SimulationConfig,
    simulation_contract: str,
    suitability_tier: str,
    feed: str,
    partial_tape: bool,
    feed_caveat: Any,
    plan,
    trials_requested: int,
    startup: int,
    universe_pit_sample: dict | None,
    preflight_symbol_count: int,
    log: logging.Logger,
    n_trials_completed: int = 0,
    n_invalid_trials: int = 0,
    pit_union_symbol_count: Optional[int] = None,
    preflight_coverage_fraction: Optional[float] = None,
    research_waiver_capped_symbols: bool = False,
) -> Path:
    """Write a study results JSON with ``status: "failed"`` for forensic review.

    Audit 2026-05-23 §P0-001. Called when either (a) a structural exception
    escaped ``study.optimize`` or (b) every completed trial was invalid (sentinel
    score / missing fold metrics). Writes the same artifact path the success
    path would have used, but with empty ``best_params`` and a
    ``best_trial_report`` carrying the error reason — so the runner's caller
    sees the same artifact contract regardless of outcome, and the file exists
    on disk before the exception is re-raised.
    """
    out = {
        "status": "failed",
        "failure_reason": failure_reason,
        "study_name": study_name,
        "simulation_mode": sim_cfg.mode,
        "simulation_contract": simulation_contract,
        "suitability_tier": suitability_tier,
        "feed": feed,
        "partial_tape": partial_tape,
        **({"feed_caveat": feed_caveat} if feed_caveat is not None else {}),
        "search_space_version": SEARCH_SPACE_VERSION,
        "n_trials_requested": trials_requested,
        "n_trials_completed": n_trials_completed,
        "n_invalid_trials": n_invalid_trials,
        "n_startup_trials": startup,
        "n_folds": len(plan.splits),
        "universe": {
            "selection": "daily_point_in_time",
            "preflight_probe_symbols": preflight_symbol_count,
            "pit_sample": universe_pit_sample,
            "preflight_symbol_count": preflight_symbol_count,
            "pit_union_symbol_count": pit_union_symbol_count,
            "preflight_coverage_fraction": preflight_coverage_fraction,
            "research_waiver_capped_symbols": research_waiver_capped_symbols,
        },
        "final_holdout": [
            plan.final_holdout_start.isoformat(),
            plan.final_holdout_end.isoformat(),
        ],
        "final_holdout_scored": False,
        "best_value": None,
        "best_params": {},
        "best_trial_report": {"error": failure_reason},
        "study_metadata": study_metadata,
    }
    results_path = Path(paths.artifact_root) / "optuna" / f"{study_name}.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    log.error(
        "walk-forward study FAILED: %s — failed artifact written to %s",
        failure_reason, results_path,
    )
    return results_path


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
    # Speedup report §5.2 / §11.2 Phase 2 — neighbor reruns reuse the
    # study's precomputed fold contexts. Stays on full artifact mode (the
    # neighbor reruns are part of the audit trail).
    fold_contexts: Optional[tuple[Optional[FoldRuntimeContext], ...]] = None,
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
                fold_contexts=fold_contexts,
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
    allow_current_code_parity_study: bool = False,
    tier: str | None = None,
    incumbent_trial: bool = False,
    log: logging.Logger | None = None,
) -> dict:
    """Run a real walk-forward Optuna study driven entirely by the config.

    ``n_trials`` / ``n_jobs`` / ``n_startup_trials`` override the config's
    ``optuna`` section when given. ``n_startup_trials`` is the number of random-
    sampling trials run before TPE-guided search begins.

    ``allow_current_code_parity_study`` + ``tier="research_only"`` together are
    the explicit opt-in required to run an Optuna study against a
    ``current_code_parity`` config (realism remediation 2 Phase 8 / audit
    §P0-011). The mechanical suitability cap (Phase 0) remains in effect.

    ``incumbent_trial=True`` pins trial 0 to the actual-contract parameter set
    (read via :func:`_incumbent_baseline_params` from the frozen contract) so
    every study has a baseline against which the optimizer's best is judged.

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

    # Realism remediation 2 Phase 8 (audit §P0-011): refuse current_code_parity
    # studies unless explicitly opted in. Chains AFTER the parity gate so a
    # divergent config still raises OptunaParityError first.
    assert_simulation_contract_admissible(
        cfg,
        allow_current_code_parity_study=allow_current_code_parity_study,
        tier=tier,
    )

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
    # Audit 2026-05-23 §6.6 / Phase 1 — under ``intended_realism`` resolve
    # the preflight symbol set against the full per-fold PIT union (not the
    # 100-symbol cap). Parity / smoke / explicit-waiver runs keep the cap.
    symbols = _resolve_symbols(cfg, md, sim_mode=sim_cfg.mode, plan=plan)
    holdout_guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)

    # Audit 2026-05-23 §6.6 + P1-001 — coverage telemetry. ``pit_union_*`` is
    # the full PIT eligible-symbol union across every fold's sessions;
    # ``preflight_symbol_count`` is the actual probe set; ``coverage_fraction``
    # is the ratio. Under ``intended_realism`` without an explicit
    # ``research_waiver_capped_symbols: true`` the runner fails closed when
    # the fraction is < 1.0.
    pit_union_symbol_count: Optional[int] = None
    preflight_coverage_fraction: Optional[float] = None
    research_waiver_capped_symbols = bool(
        ((cfg.get("optuna") or {}).get("preflight") or {}).get(
            "research_waiver_capped_symbols", False
        )
    )
    try:
        if str(md.get("minute_bar_source", "fixture")) in ("alpaca", "shared"):
            from .pit_universe import plan_pit_symbol_union

            pit_union = plan_pit_symbol_union(
                lake_root, feed=feed, plan=plan, cfg=cfg, include_holdout=True,
            )
            pit_union_symbol_count = len(pit_union)
            if pit_union_symbol_count > 0:
                preflight_coverage_fraction = (
                    len(set(symbols) & pit_union) / pit_union_symbol_count
                )
    except Exception as exc:  # noqa: BLE001 — coverage telemetry must never crash the study
        log.warning("PIT-union coverage telemetry failed (%s); coverage unknown", exc)

    if (
        sim_cfg.mode == "intended_realism"
        and not research_waiver_capped_symbols
        and preflight_coverage_fraction is not None
        and preflight_coverage_fraction < 1.0 - 1e-9
    ):
        delta = (pit_union_symbol_count or 0) - len(symbols)
        raise PreflightError(
            f"optuna study refused by preflight: intended_realism requires the "
            f"FULL per-fold PIT eligible-universe union but the probe covers "
            f"{len(symbols)}/{pit_union_symbol_count} symbols "
            f"({preflight_coverage_fraction:.2%}; delta={delta}). Pass an "
            f"explicit ``optuna.preflight.research_waiver_capped_symbols: true`` "
            f"to opt into research-only with the capped sample. "
            f"See docs/audits/2026-05-23_realism_audit.md §6.6."
        )

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
    except Exception as exc:  # noqa: BLE001 — probe failure handling depends on mode
        # Audit 2026-05-23 §P0-003 — leave dq_report / quote_cov_pct as None;
        # the updated preflight ``_check_data_quality`` / ``_check_quote_coverage``
        # will FAIL CLOSED on missing values under ``intended_realism`` (with a
        # clear pointer back to the audit). For ``current_code_parity`` / smoke
        # the previous warn-then-continue semantics are preserved (the preflight
        # records ``skipped`` for the missing inputs).
        log.warning(
            "preflight probe failed (%s); preflight will fail closed under "
            "intended_realism and skip the affected checks under parity / smoke",
            exc,
        )

    preflight = run_preflight(
        sim_mode=sim_cfg.mode,
        allow_smoke=allow_smoke,
        dq_report=dq_report,
        quote_coverage_pct=quote_cov_pct,
        min_quote_coverage_pct=float(sim_cfg.min_quote_coverage_pct),
        # Realism remediation 2 Phase 10 / audit §11 Phase 9 — when the config
        # asks for SIP, gate on lake SIP-partition presence; no regression for
        # the IEX path (the SIP check is a no-op for any non-SIP feed).
        feed=feed,
        lake_root=Path(lake_root) if lake_root else None,
    )
    log.info("preflight passed: %d checks", len(preflight.checks))

    # Realism remediation 2 Phase 8 (audit §P0-011): the explicit
    # intended_realism data-prerequisite gate. Run after the cheaper preflight
    # so its evidence is on hand; raises before any (expensive) trial.
    assert_intended_realism_data_prerequisites(
        cfg,
        dq_report=dq_report,
        quote_coverage_pct=quote_cov_pct,
        min_quote_coverage_pct=float(sim_cfg.min_quote_coverage_pct),
    )

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
    # Realism remediation 2 Phase 8 (audit §P1-005): the dataset hash is now
    # content-addressed when a real lake is available — SHA-256 over the lake
    # manifest, every bars/quotes/CA parquet's footer hash, asset snapshot id,
    # adjustment policy, config hash, and code hash. Editing one parquet byte
    # changes the dataset hash. A lake-less / synthetic run falls back to the
    # legacy logical hash (still stable, but obviously not content-addressed).
    dataset_hash_components: dict[str, Any] | None = None
    try:
        from ..data.lineage import (
            content_addressed_dataset_hash,
            resolve_lake_root,
            uses_lake,
        )

        if uses_lake(cfg):
            _lake = resolve_lake_root(cfg)
            if _lake.is_dir():
                ca = content_addressed_dataset_hash(
                    lake_root=_lake,
                    config_hash=lab_config_hash,
                    code_manifest_hash=code_hash,
                )
                dataset_hash = str(ca["dataset_hash"])
                dataset_hash_components = ca["components"]
            else:
                dataset_hash = _hash(
                    [symbols, feed, str(plan.splits[0].train_start),
                     str(plan.splits[-1].val_end), lab_config_hash, code_hash]
                )
        else:
            dataset_hash = _hash(
                [symbols, feed, str(plan.splits[0].train_start),
                 str(plan.splits[-1].val_end), lab_config_hash, code_hash]
            )
    except Exception as exc:  # noqa: BLE001 — content-addressed hashing must never crash a study
        log.warning("content-addressed dataset hash failed (%s); falling back to logical hash", exc)
        dataset_hash = _hash(
            [symbols, feed, str(plan.splits[0].train_start),
             str(plan.splits[-1].val_end), lab_config_hash, code_hash]
        )

    # Realism remediation 2 Phase 8 (audit §P1-006) — full per-fold preflight.
    # Probe EVERY validation + holdout window once (cached by (dataset_hash,
    # fold_window, config_hash)) so a fold missing required daily/minute/quote
    # /exit-path coverage blocks the run before any trial costs are paid. Only
    # gates intended_realism — current_code_parity / smoke_fixture are not data
    # -prerequisite-failure-modes (the cheap preflight already records warnings).
    full_fold_preflight_result: Optional[Any] = None
    if sim_cfg.mode == "intended_realism":
        from .preflight import FoldWindow, run_full_fold_preflight

        fold_windows = [
            FoldWindow(
                fold_id=f"val_{s.val_start.isoformat()}",
                kind="validation",
                start=s.val_start, end=s.val_end,
            )
            for s in plan.splits
        ] + [
            FoldWindow(
                fold_id=f"holdout_{plan.final_holdout_start.isoformat()}",
                kind="holdout",
                start=plan.final_holdout_start, end=plan.final_holdout_end,
            )
        ]
        full_fold_preflight_result = run_full_fold_preflight(
            cfg=cfg, folds=fold_windows, symbols=symbols, lake_root=lake_root,
            feed=feed, dataset_hash=dataset_hash, config_hash=lab_config_hash,
            scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
            min_quote_coverage_pct=float(sim_cfg.min_quote_coverage_pct),
        )
        log.info(
            "full per-fold preflight passed: %d folds, %d checks",
            len(fold_windows), len(full_fold_preflight_result.checks),
        )

    # Audit 2026-05-23 §P1-006 — relative ``sqlite:///`` URIs resolve against
    # the lab root, not the launch CWD. PostgreSQL URIs are unchanged.
    raw_storage_uri = optuna_cfg.get("storage") or None
    resolved_storage_uri = None
    if raw_storage_uri:
        from .storage_path import resolve_storage_uri

        resolved_storage_uri = resolve_storage_uri(raw_storage_uri, paths=paths)

    study = OptunaStudy(
        feed=feed,
        cost_stress=str(bt.get("cost_stress", "conservative")),
        dataset_hash=dataset_hash,
        config_hash=lab_config_hash,
        storage_uri=resolved_storage_uri,
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
    # Realism remediation 2 Phase 10 (audit §P1-010) — IEX is partial-tape;
    # every IEX artifact carries ``feed_caveat: partial_tape_features`` AND a
    # ``partial_tape: true`` flag. Both fields are surfaced as study user_attrs
    # by ``OptunaStudy.create`` (above); we also persist them here in
    # ``study_metadata`` so they appear in the study results JSON.
    from ..promotion.suitability import feed_caveat_for as _feed_caveat_for

    feed_caveat = _feed_caveat_for(feed)
    partial_tape = (str(feed).lower() == "iex")
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
        "partial_tape": partial_tape,
        "preflight": preflight.as_dict(),
        "penalty_weights": vars(DEFAULT_PENALTY_WEIGHTS),
        "search_space_overrides": search_space_overrides,
    }
    if feed_caveat is not None:
        study_metadata["feed_caveat"] = feed_caveat
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
    # Realism remediation 2 Phase 8 — incumbent baseline. When opted in,
    # trial 0 is pinned to the actual-contract parameter set (read from the
    # frozen contract).
    incumbent_params: Optional[dict[str, Any]] = None
    if incumbent_trial:
        incumbent_params = _incumbent_baseline_params()
        if incumbent_params:
            log.info("incumbent baseline: trial 0 pinned to %d contract params",
                     len(incumbent_params))
        else:
            log.warning("incumbent baseline requested but no contract available; "
                        "trial 0 will be a regular TPE-startup sample")

    # Speedup report §5.1 / §11.2 Phase 1 — config-driven opt-in flag for the
    # objective-minimal (no disk artifact) fold path. Default ``"full"``
    # preserves byte-stable behaviour; Phase 5 flips the actual-IEX/SIP
    # configs to ``"objective_minimal"`` after parity is proven.
    objective_artifact_mode = str(
        (cfg.get("optuna") or {}).get("objective_artifact_mode", "full")
    )
    if objective_artifact_mode not in ("full", "objective_minimal"):
        raise OptunaStudyInvalidError(
            f"optuna.objective_artifact_mode must be 'full' or 'objective_minimal', "
            f"got {objective_artifact_mode!r}"
        )
    if objective_artifact_mode == "objective_minimal":
        log.info(
            "objective_artifact_mode=objective_minimal — per-trial fold "
            "backtests skip disk artifact writes (speedup §5.1 / §11.2 Phase 1)"
        )

    # Speedup report §5.2 / §11.2 Phase 2 — build the per-fold runtime
    # context ONCE, before constructing the objective. The search-space
    # guard refuses any tuned parameter that would invalidate the cache.
    # Speedup report §5.3 / §11.2 Phase 3 — opt-in cached supplier adapter.
    assert_search_space_does_not_affect_context(search_space_overrides)
    cached_suppliers_flag = bool((cfg.get("optuna") or {}).get("cached_suppliers", False))
    fold_contexts = build_fold_contexts(
        cfg, plan, lake_root=lake_root, feed=feed, symbols=symbols,
        paths=paths, holdout_guard=holdout_guard,
        cached_suppliers=cached_suppliers_flag,
    )
    log.info(
        "precomputed %d fold runtime context(s) for the study "
        "(speedup §5.2 / §11.2 Phase 2)%s",
        sum(1 for c in fold_contexts if c is not None),
        " [cached_suppliers=True — §5.3 / §11.2 Phase 3]" if cached_suppliers_flag else "",
    )

    objective = make_walkforward_objective(
        cfg, plan, lake_root=lake_root, feed=feed, symbols=symbols,
        paths=paths, holdout_guard=holdout_guard, log=log,
        search_space_overrides=search_space_overrides,
        incumbent_params=incumbent_params,
        dataset_hash=dataset_hash,
        config_hash=lab_config_hash,
        code_hash=code_hash,
        objective_artifact_mode=objective_artifact_mode,
        fold_contexts=fold_contexts,
    )
    # Speedup report §6.1 / §11.3 Phase 5 — process-parallel Optuna against
    # PostgreSQL storage. ``n_jobs <= 1`` keeps the serial in-process loop;
    # ``n_jobs > 1`` spawns workers (capped at MemoryBudget.max_optuna_workers,
    # default 8). Workers each set BLAS threads to 1 before importing NumPy
    # and rebuild their own objective via the dotted factory so the parent's
    # heavy closures do not have to be pickled.
    parallel_cfg = (cfg.get("optuna") or {}).get("parallel") or {}
    strict_parallel_flag = bool(parallel_cfg.get("strict_parallel", False))
    mem_budget = MemoryBudget.from_system(
        reserve_system_gib=float(parallel_cfg.get("memory_reserve_gib", 32.0)),
        max_optuna_workers=int(parallel_cfg.get("max_workers", 8)),
    )

    # Audit 2026-05-23 §P0-001 — a structural exception escaping the trial
    # must abort the study with a written failed-status artifact rather than
    # being swallowed by Optuna's loop. The artifact preserves the study
    # metadata (forensic) and the structural failure reason; the runner then
    # re-raises ``OptunaStudyInvalidError``.
    structural = structural_exceptions()
    try:
        run_bowaka_optimization_dispatch(
            study=study.study, study_name=study.study.study_name,
            objective=objective,
            objective_factory_dotted=(
                "bowaka_v2_lab.optuna.walkforward_runner"
                ":make_walkforward_objective_for_worker"
            ),
            factory_kwargs={
                "config_path": str(config_path),
                "search_space_overrides": search_space_overrides,
                "incumbent_params": incumbent_params,
                "dataset_hash": dataset_hash,
                "config_hash": lab_config_hash,
                "code_hash": code_hash,
                "objective_artifact_mode": objective_artifact_mode,
                "cached_suppliers": cached_suppliers_flag,
            },
            n_trials=trials,
            n_jobs=int(study.n_jobs),
            storage_url=study.storage_uri,
            memory_budget=mem_budget,
            sampler_seed=1337,
            n_startup_trials=startup,
            strict_parallel=strict_parallel_flag,
        )
    except structural as struct_exc:
        failure_reason = (
            f"structural exception escaped optimize: "
            f"{type(struct_exc).__name__}: {struct_exc}"
        )
        _write_failed_study_artifact(
            paths=paths,
            study_name=study.study.study_name,
            study_metadata=study_metadata,
            failure_reason=failure_reason,
            sim_cfg=sim_cfg,
            simulation_contract=simulation_contract,
            suitability_tier=suitability_tier,
            feed=feed,
            partial_tape=partial_tape,
            feed_caveat=feed_caveat,
            plan=plan,
            trials_requested=trials,
            startup=startup,
            universe_pit_sample=universe_pit_sample,
            preflight_symbol_count=len(symbols),
            log=log,
            pit_union_symbol_count=pit_union_symbol_count,
            preflight_coverage_fraction=preflight_coverage_fraction,
            research_waiver_capped_symbols=research_waiver_capped_symbols,
        )
        raise OptunaStudyInvalidError(failure_reason) from struct_exc

    import optuna

    completed = [t for t in study.study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    # Audit 2026-05-23 §P0-001 — validate the completed-trial set. A trial
    # whose ``value`` is the sentinel score (or whose user_attrs lack fold
    # metrics) is structurally invalid; if every completed trial is invalid
    # the study did not produce a usable best, and emitting ``status: "ok"``
    # with non-empty ``best_params`` would silently recommend a sentinel
    # parameter set. The runner instead writes a failed artifact and raises.
    _FAILED_EPS = 1e-6
    valid_trials: list = []
    invalid_trials: list[tuple[Any, str]] = []
    for t in completed:
        value = float(t.value) if t.value is not None else float("-inf")
        if value <= _FAILED_TRIAL_SCORE + _FAILED_EPS:
            invalid_trials.append((t, "sentinel_score"))
            continue
        fold_scores = t.user_attrs.get("fold_scores") or []
        fold_metrics = t.user_attrs.get("fold_metrics") or []
        if len(fold_scores) != len(plan.splits) or len(fold_metrics) != len(plan.splits):
            invalid_trials.append((t, "missing_fold_metrics"))
            continue
        valid_trials.append(t)

    if completed and not valid_trials:
        failures = ", ".join(
            f"trial#{t.number}:{reason}" for t, reason in invalid_trials
        )
        failure_reason = (
            f"study produced zero valid non-sentinel trials; "
            f"completed={len(completed)}, invalid={len(invalid_trials)} ({failures}); "
            f"see docs/audits/2026-05-23_realism_audit.md §P0-001"
        )
        _write_failed_study_artifact(
            paths=paths,
            study_name=study.study.study_name,
            study_metadata=study_metadata,
            failure_reason=failure_reason,
            sim_cfg=sim_cfg,
            simulation_contract=simulation_contract,
            suitability_tier=suitability_tier,
            feed=feed,
            partial_tape=partial_tape,
            feed_caveat=feed_caveat,
            plan=plan,
            trials_requested=trials,
            startup=startup,
            universe_pit_sample=universe_pit_sample,
            preflight_symbol_count=len(symbols),
            log=log,
            n_trials_completed=len(completed),
            n_invalid_trials=len(invalid_trials),
            pit_union_symbol_count=pit_union_symbol_count,
            preflight_coverage_fraction=preflight_coverage_fraction,
            research_waiver_capped_symbols=research_waiver_capped_symbols,
        )
        raise OptunaStudyInvalidError(failure_reason)

    # Explicit ranked list — never study.best_trial (a zero-completed study would raise).
    ranked = sorted(
        valid_trials,
        key=lambda t: float(t.value),
        reverse=True,
    )
    best = ranked[0] if ranked else None
    # Realism remediation 2 Phase 8 — overridden selection: median fold score
    # minus a stability penalty (std across folds, scaled by
    # ``DEFAULT_PENALTY_WEIGHTS.fold_variance``). The trial's recorded
    # ``value`` is already this number by construction; this branch keeps the
    # name in the artifact even if the objective formula changes in the future.
    def _median_minus_stability(t) -> float:
        med = t.user_attrs.get("median_fold_score")
        var = t.user_attrs.get("fold_variance")
        if med is None:
            return float(t.value) if t.value is not None else _FAILED_TRIAL_SCORE
        v = float(med)
        if var is not None:
            v -= float(DEFAULT_PENALTY_WEIGHTS.fold_variance) * float(var)
        return v

    ranked_by_median_minus_stability = sorted(
        valid_trials, key=_median_minus_stability, reverse=True,
    )
    best_by_median_minus_stability = (
        ranked_by_median_minus_stability[0]
        if ranked_by_median_minus_stability else None
    )
    # The incumbent trial is recorded for forensic value even when it landed
    # in ``invalid_trials`` — operators want to see the incumbent's outcome
    # alongside the optimizer's best, including when the incumbent failed.
    incumbent_baseline_trial = next(
        (t for t in completed if t.user_attrs.get("incumbent_trial") is True),
        None,
    )

    # ---- best-trial reporting (Phase 9, Task 5) --------------------------
    best_report: dict[str, Any] = {}
    if best is not None:
        try:
            best_report = build_best_trial_report(
                best, cfg, plan, lake_root=lake_root, feed=feed, symbols=symbols,
                paths=paths, holdout_guard=holdout_guard, log=log,
                search_space_overrides=search_space_overrides,
                fold_contexts=fold_contexts,
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
        # Realism remediation 2 Phase 10 (audit §P1-010): IEX caveat + partial-
        # tape flag surfaced at the top level so downstream tooling can refuse
        # SIP-portable claims on IEX studies without re-deriving feed semantics.
        "partial_tape": partial_tape,
        **({"feed_caveat": feed_caveat} if feed_caveat is not None else {}),
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
            # Audit 2026-05-23 §6.6 / P1-001 — full-PIT-union coverage telemetry.
            # The runner refuses ``intended_realism`` runs with coverage < 1.0
            # unless the operator passes ``research_waiver_capped_symbols: true``.
            "preflight_symbol_count": len(symbols),
            "pit_union_symbol_count": pit_union_symbol_count,
            "preflight_coverage_fraction": preflight_coverage_fraction,
            "research_waiver_capped_symbols": research_waiver_capped_symbols,
        },
        "final_holdout": [
            plan.final_holdout_start.isoformat(),
            plan.final_holdout_end.isoformat(),
        ],
        "final_holdout_scored": False,  # Phase 9: only `--final-holdout` scores it.
        "best_value": (best.value if best else None),
        "best_params": (dict(best.params) if best else {}),
        # Realism remediation 2 Phase 8 — the overridden median-minus-stability
        # best, kept alongside Optuna's best_trial for reference. They normally
        # agree (the objective IS median-minus-stability); they diverge only if
        # the objective formula is ever changed without updating this selector.
        "best_by_median_minus_stability": (
            {
                "trial_number": best_by_median_minus_stability.number,
                "value": best_by_median_minus_stability.value,
                "params": dict(best_by_median_minus_stability.params),
                "median_fold_score": best_by_median_minus_stability.user_attrs.get(
                    "median_fold_score"
                ),
                "fold_variance": best_by_median_minus_stability.user_attrs.get(
                    "fold_variance"
                ),
            }
            if best_by_median_minus_stability is not None else None
        ),
        "best_trial_report": best_report,
        "top_k_clustering": clustering,
        "study_metadata": study_metadata,
    }
    # Realism remediation 2 Phase 8 (audit §P0-001 / §P0-011 / §P1-005) —
    # promotion_evidence.json: the gating artifact for any operator decision to
    # promote the study's parameter set. Carries the simulation contract, the
    # mechanical suitability tier, dataset/config/code hashes, fold dispersion,
    # the worst fold, parameter stability, and a comparison to the incumbent
    # baseline (if trial 0 was the incumbent). NEVER raises the tier above the
    # contract cap — that is enforced by ``tier_for_simulation_contract``.
    fold_scores = list((best.user_attrs.get("fold_scores") if best else []) or [])
    fold_metrics_list = list((best.user_attrs.get("fold_metrics") if best else []) or [])
    worst_fold: dict | None = None
    if fold_metrics_list:
        # Worst = lowest net_return (the principal metric); ties broken by id.
        try:
            worst_fold = min(
                fold_metrics_list,
                key=lambda f: float(f.get("net_return_pct", 0.0) or 0.0),
            )
        except Exception:  # noqa: BLE001 — worst-fold extraction is best-effort
            worst_fold = None
    fold_dispersion: dict[str, Any] = {}
    if fold_scores:
        try:
            fold_dispersion = {
                "n_folds": len(fold_scores),
                "min": float(min(fold_scores)),
                "median": float(statistics.median(fold_scores)) if (
                    len(fold_scores) >= 1) else None,
                "max": float(max(fold_scores)),
                "stdev": (
                    float(statistics.stdev(fold_scores))
                    if len(fold_scores) > 1 else 0.0
                ),
            }
        except Exception:  # noqa: BLE001 — dispersion is best-effort
            fold_dispersion = {"n_folds": len(fold_scores)}
    incumbent_comparison: dict[str, Any] | None = None
    if incumbent_baseline_trial is not None:
        incumbent_comparison = {
            "incumbent_trial_number": incumbent_baseline_trial.number,
            "incumbent_value": incumbent_baseline_trial.value,
            "incumbent_median_fold_score": incumbent_baseline_trial.user_attrs.get(
                "median_fold_score"
            ),
            "incumbent_params": dict(incumbent_baseline_trial.params),
            "incumbent_clamped": incumbent_baseline_trial.user_attrs.get(
                "incumbent_clamped", {}
            ),
            "best_vs_incumbent_delta": (
                (float(best.value) - float(incumbent_baseline_trial.value))
                if best is not None
                   and best.value is not None
                   and incumbent_baseline_trial.value is not None
                else None
            ),
        }
    # Audit 2026-05-23 §P1-004 — risk-control promotion gate. Evaluate the
    # winning trial's risk-control parameters against the incumbent baseline;
    # any drift past epsilon labels the run a risk_policy_experiment and caps
    # the effective tier at research_only.
    from .promotion_gates import evaluate_promotion

    # Build the incumbent baseline from the contract; the per-trial incumbent
    # may be absent (incumbent_trial=False), so use the contract directly.
    incumbent_for_gate = (
        dict(incumbent_baseline_trial.params)
        if incumbent_baseline_trial is not None
        else _incumbent_baseline_params()
    )
    candidate_for_gate = dict(best.params) if best is not None else {}
    promotion_decision = evaluate_promotion(
        incumbent_params=incumbent_for_gate,
        candidate_params=candidate_for_gate,
        requested_tier=str(suitability_tier),
        feed=feed,
    )
    effective_tier = promotion_decision["effective_tier"]
    # Cap the suitability tier to the gate's effective tier — never raise it.
    if effective_tier != suitability_tier:
        log.warning(
            "promotion gate capped suitability_tier %s -> %s; reasons: %s",
            suitability_tier, effective_tier,
            "; ".join(promotion_decision["refusal_reasons"]) or "n/a",
        )
        suitability_tier = effective_tier
        out["suitability_tier"] = suitability_tier

    promotion_evidence: dict[str, Any] = {
        "schema_version": 2,
        "study_name": study.study.study_name,
        "simulation_contract": simulation_contract,
        "suitability_tier": suitability_tier,
        "feed": feed,
        # Realism remediation 2 Phase 10 (audit §P1-010): the IEX caveat
        # travels with the promotion artifact so a downstream review can't
        # promote an IEX result without explicitly accepting the partial-tape
        # warning. ``feed_caveat`` is only emitted when one applies (today, IEX).
        "partial_tape": partial_tape,
        **({"feed_caveat": feed_caveat} if feed_caveat is not None else {}),
        "dataset_hash": dataset_hash,
        "config_hash": lab_config_hash,
        "code_hash": code_hash,
        "best_trial_number": (best.number if best is not None else None),
        "best_value": (best.value if best is not None else None),
        "best_params": (dict(best.params) if best is not None else {}),
        "fold_dispersion": fold_dispersion,
        "worst_fold": worst_fold,
        "parameter_stability": clustering,
        "incumbent_comparison": incumbent_comparison,
        # The audit-required "is this a parameter-recommendation study?" answer.
        # By construction (Phase 0): current_code_parity is paper-reconciliation
        # only; intended_realism on IEX is research_only; only SIP + paper-recon
        # evidence (gated elsewhere) ever raises the cap.
        "is_parameter_recommendation_study": (
            simulation_contract == "intended_realism"
            and suitability_tier in ("backtesting_only", "paper_candidate", "live_candidate")
        ),
        # Audit 2026-05-23 §P1-004 — risk-control promotion gate decision.
        # ``promotable`` is the gate's verdict; ``refusal_reasons`` lists the
        # caps that fired; ``risk_policy_experiment`` flags runs where the
        # optimizer materially changed a risk-control parameter from the
        # incumbent (a paper-recon prerequisite, not a parameter-recommendation).
        "promotable": promotion_decision["promotable"],
        "effective_tier": promotion_decision["effective_tier"],
        "requested_tier": promotion_decision["requested_tier"],
        "refusal_reasons": promotion_decision["refusal_reasons"],
        "risk_policy_experiment": promotion_decision["risk_policy_experiment"],
        "risk_drift": promotion_decision["risk_drift"],
        "feed_cap_applied": promotion_decision["feed_cap_applied"],
    }
    promo_dir = Path(paths.artifact_root) / "optuna" / study.study.study_name
    promo_dir.mkdir(parents=True, exist_ok=True)
    promo_path = promo_dir / "promotion_evidence.json"
    promo_path.write_text(
        json.dumps(promotion_evidence, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    out["promotion_evidence_path"] = str(promo_path)
    out["promotion_evidence"] = promotion_evidence

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
    "assert_simulation_contract_admissible",
    "assert_intended_realism_data_prerequisites",
    "OptunaParityError",
    "CurrentCodeParityStudyRefused",
    "IntendedRealismDataInsufficient",
    "OptunaStudyInvalidError",
    "_incumbent_baseline_params",
]
