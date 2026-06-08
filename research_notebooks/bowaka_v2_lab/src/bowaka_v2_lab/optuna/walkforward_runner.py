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
from ..data.adjustment import daily_adjustment_for_config
from ..data.lineage import resolve_lake_root
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
from .errors import (
    REASON_INCUMBENT_MAPPING_INCOMPLETE,
    OptunaStudyInvalidError,
    structural_exceptions,
)
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
        from ..data.lineage import _coerce_lake_root, resolve_lake_root
        from .pit_universe import plan_pit_symbol_union

        lake_root = _coerce_lake_root(resolve_lake_root(cfg))
        union = plan_pit_symbol_union(
            lake_root, feed=md.get("feed", "iex"),
            plan=plan, cfg=cfg, include_holdout=True,
        )
        if not union:
            # The lake was probed but the PIT union was empty — fall back to
            # the lake-available symbols. The preflight DQ check will surface
            # the underlying lake gap.
            from bowaka_common.marketdata import available_symbols

            from ..data.adjustment import daily_adjustment_for_config

            return available_symbols(
                lake_root, timeframe="1d", feed=md.get("feed", "iex"),
                adjustment=daily_adjustment_for_config(cfg),
            )
        return sorted(union)

    if is_lake:
        from ..data.lineage import _coerce_lake_root, resolve_lake_root
        from bowaka_common.marketdata import available_symbols

        from ..data.adjustment import daily_adjustment_for_config

        return available_symbols(
            _coerce_lake_root(resolve_lake_root(cfg)),
            timeframe="1d", feed=md.get("feed", "iex"),
            adjustment=daily_adjustment_for_config(cfg),
        )[:cap]
    return ["AAA", "BBB", "CCC"]


_SF = "exits.signal_fade.score_thresholds."


def _derived_strategy_fields(params: Mapping[str, Any]) -> dict[str, Any]:
    """Audit 2026-05-29 §6.8 — the actual-strategy fields derived from the
    gap/ratio search-space keys: ``...hard``, ``...critical``, ``target_pct``.

    Returns only the derived fields (empty when the gap/ratio keys are absent),
    clamped to the outer legal ranges of the pre-v3 search space so the derived
    values stay bounded regardless of how the gaps/ratio were sampled.
    """
    out: dict[str, Any] = {}
    soft = params.get(_SF + "soft")
    hard_gap = params.get(_SF + "hard_gap")
    critical_gap = params.get(_SF + "critical_gap")
    if soft is not None and hard_gap is not None:
        hard = min(0.70, float(soft) + float(hard_gap))
        out[_SF + "hard"] = hard
        if critical_gap is not None:
            out[_SF + "critical"] = min(0.90, hard + float(critical_gap))
    stop_pct = params.get("exits.stop_pct")
    ratio = params.get("exits.reward_risk_ratio")
    if stop_pct is not None and ratio is not None:
        out["exits.target_pct"] = min(0.40, float(stop_pct) * float(ratio))
    return out


def _derive_strategy_params(params: Mapping[str, Any]) -> dict[str, Any]:
    """Return ``params`` with the gap/ratio internal keys replaced by the
    derived actual-strategy fields (the strategy has no gap/ratio fields).

    Idempotent: a params dict without gap/ratio keys is returned unchanged, so
    a neighbour set or an already-derived params dict is safe to pass.
    """
    derived = _derived_strategy_fields(params)
    if not derived:
        return dict(params)
    out = dict(params)
    out.pop(_SF + "hard_gap", None)
    out.pop(_SF + "critical_gap", None)
    out.pop("exits.reward_risk_ratio", None)
    out.update(derived)
    return out


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

    Audit 2026-05-29 §6.8 / Phase 2 — the search space samples gap/ratio keys
    (``...soft`` + ``...hard_gap`` + ``...critical_gap`` and
    ``exits.reward_risk_ratio``) so the constraints ``soft < hard < critical``
    and ``target_pct > stop_pct`` ALWAYS hold. Here those internal keys are
    converted to the actual-strategy fields the simulator reads
    (``...hard`` / ``...critical`` / ``exits.target_pct``) and the gap/ratio
    keys are dropped (the strategy has no such fields). The derived values are
    clamped to the OUTER legal ranges of the old search space (hard <= 0.70,
    critical <= 0.90, target_pct <= 0.40) so post-clamp samples stay bounded.
    """
    params = _derive_strategy_params(params)
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
            daily_adjustment=daily_adjustment_for_config(cfg),
        )
        quote_supplier = make_quote_supplier(
            lake_root, feed=feed,
            default_max_age_seconds=float(
                (cfg.get("execution") or {}).get("max_quote_age_seconds", 60)
            ),
        )
        forward_minute_supplier = make_forward_minute_supplier(lake_root, feed=feed)
        universe = build_pit_universe_for_sessions(sessions, cfg, MarketDataStore(lake_root))
        from ..data.adjustment import daily_adjustment_for_config

        daily_cache = {}
        for s in sessions:
            sess_syms = eligible_symbols(universe.get(s, {})) or symbols
            daily_cache[s] = build_daily_cache_from_lake(
                lake_root, sess_syms, s, feed=feed,
                daily_adjustment=daily_adjustment_for_config(cfg))
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
        # Speedup v2 §5.6 / Phase 3 — pass the cached invariant DQ report
        # when the context carries one (default None preserves legacy build).
        _cached_dq = (
            ctx.startup_dq_report if ctx is not None else None
        )
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
            startup_dq_report=_cached_dq,
            scan_matrix_store=(ctx.scan_matrix_store if ctx is not None else None),
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
            daily_adjustment=daily_adjustment_for_config(cfg),
        )
        quote_supplier = make_quote_supplier(
            lake_root, feed=feed,
            default_max_age_seconds=float(
                (cfg.get("execution") or {}).get("max_quote_age_seconds", 60)
            ),
        )
        forward_minute_supplier = make_forward_minute_supplier(lake_root, feed=feed)
        universe = build_pit_universe_for_sessions(sessions, cfg, MarketDataStore(lake_root))
        from ..data.adjustment import daily_adjustment_for_config

        daily_cache: dict[_dt.date, Any] = {}
        for s in sessions:
            sess_syms = eligible_symbols(universe.get(s, {})) or symbols
            daily_cache[s] = build_daily_cache_from_lake(
                lake_root, sess_syms, s, feed=feed,
                daily_adjustment=daily_adjustment_for_config(cfg))
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
        # Speedup v2 §5.6 / Phase 3 — pass the cached invariant DQ report
        # when the context carries one (default None preserves legacy build).
        _cached_dq = (
            ctx.startup_dq_report if ctx is not None else None
        )
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
            startup_dq_report=_cached_dq,
            scan_matrix_store=(ctx.scan_matrix_store if ctx is not None else None),
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
    one bad fold can never lift a trial's objective.

    Audit 2026-05-29 §A.5 / Phase 0 task 6: tagged ``fold_status="degraded"``
    so the valid-trial filter can reject any trial that contains one. A
    degraded fold is the swallowed-exception sentinel, NOT a real zero-trade
    backtest, and must never be accepted as a finite datapoint.
    """
    return FoldResult(
        fold_id=fold_id, net_return=-1.0, max_drawdown=1.0,
        turnover=0.0, concentration=0.0, n_trades=0,
        worst_day_loss=1.0, quote_coverage=0.0, fill_rate=0.0,
        fold_status="degraded",
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
    # Speedup report §6.2 / §11.2 Phase 7 — optional conservative pruning
    # hook. Called once after each completed fold with
    # ``(fold_index, running_score)``; raise ``optuna.TrialPruned`` to abort
    # the trial early. Default ``None`` preserves the legacy no-prune flow.
    prune_callback: Optional[Callable[[int, float], None]] = None,
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
            # StartupDataQualityError is a DataQualityError subclass (speedup
            # report §4 P0-A / Phase 0 task 1) — it propagates here and aborts
            # the study.
            raise
        except Exception as exc:  # noqa: BLE001 — non-structural strategy/eval error may degrade
            log.warning("fold %s failed non-structurally: %s", fold_id, exc)
            folds.append(_degraded_fold(fold_id))
        # Speedup §6.2 / Phase 7 — running-score pruning hook. Computed
        # AFTER the fold result is appended so the hook sees the partial
        # series. The callback (if supplied) is responsible for raising
        # ``optuna.TrialPruned`` when the conservative floor is breached.
        if prune_callback is not None and folds:
            try:
                running_score = compute_objective(folds).objective
            except Exception:  # noqa: BLE001 — never let scoring kill the trial
                running_score = _FAILED_TRIAL_SCORE
            prune_callback(i, running_score)
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


def build_validation_scorer(
    config_path: str | Path,
    *,
    objective_artifact_mode: str = "objective_minimal",
    log: Optional[logging.Logger] = None,
) -> Callable[..., tuple[float, list[FoldResult]]]:
    """Build a ``score_with_overrides(params, overrides) -> (objective, folds)``
    closure from a config (audit 2026-05-29 §8.5 / Phase 4a stress matrix).

    Mirrors the plan / supplier / holdout setup of
    :func:`make_walkforward_objective_for_worker`. ``params`` is the finalist's
    flat dotted trial params (run through :func:`apply_trial_params`, so
    gap/ratio derivation happens); ``overrides`` is a flat dotted-key dict
    applied to the config AFTER the params (e.g.
    ``{"backtest.slippage_bps_offset": 50}``) — it bypasses the search-space
    derivation so non-trial keys like ``backtest.*`` reach the right place.
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
    # Hotfix 2026-05-29: resolve via the standard chain (explicit override >
    # $MARKET_DATA_ROOT > in-repo default). The raw cfg lookup is None for
    # every shipping config, and Path(str(None)) == Path('None') downstream
    # false-positives the partition gates.
    lake_root = resolve_lake_root(cfg)
    symbols = _resolve_symbols(cfg, md, sim_mode=sim_cfg.mode, plan=plan)
    holdout_guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
    _log = log or logging.getLogger("bowaka_v2_lab.stress_matrix")

    def score_with_overrides(
        params: Mapping[str, Any], overrides: Optional[Mapping[str, Any]] = None,
    ) -> tuple[float, list[FoldResult]]:
        trial_cfg = apply_trial_params(cfg, dict(params))
        for dotted, val in (overrides or {}).items():
            parts = dotted.split(".")
            node: Any = trial_cfg
            for key in parts[:-1]:
                child = node.get(key)
                if not isinstance(child, dict):
                    child = {}
                    node[key] = child
                node = child
            node[parts[-1]] = val
        folds = _run_validation_folds(
            trial_cfg, plan, lake_root=lake_root, feed=feed, symbols=symbols,
            paths=paths, holdout_guard=holdout_guard, log=_log,
            objective_artifact_mode=objective_artifact_mode,
        )
        return compute_objective(folds).objective, folds

    return score_with_overrides


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
    # Hotfix 2026-05-29: resolve via the standard chain (explicit override >
    # $MARKET_DATA_ROOT > in-repo default). The raw cfg lookup is None for
    # every shipping config, and Path(str(None)) == Path('None') downstream
    # false-positives the partition gates.
    lake_root = resolve_lake_root(cfg)
    symbols = _resolve_symbols(cfg, md, sim_mode=sim_cfg.mode, plan=plan)
    holdout_guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
    assert_search_space_does_not_affect_context(search_space_overrides)
    # Speedup report v2 §5.8 / Phase 1 — time the worker-side context build
    # so the phase-profile JSON can attribute amortised cost. The counter
    # uses the existing ProfileCounters context (no-op when disabled).
    import time as _time

    _worker_ctx_start = _time.perf_counter()
    fold_contexts = build_fold_contexts(
        cfg, plan, lake_root=lake_root, feed=feed, symbols=symbols,
        paths=paths, holdout_guard=holdout_guard,
        cached_suppliers=bool(cached_suppliers),
    )
    _worker_ctx_end = _time.perf_counter()
    from ..utils.profile_counters import (
        counters_enabled as _ce,
        current_profile_counters as _cpc,
    )

    if _ce():
        try:
            _cpc().inc(worker_context_build_seconds=_worker_ctx_end - _worker_ctx_start)
        except LookupError:
            pass
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


def _write_trial_debug_artifact(
    *, paths: BowakaV2Paths, trial: Any, folds: list, result: Any,
    params: Mapping[str, Any], reason: str, log: logging.Logger,
) -> None:
    """Persist a per-trial debug telemetry record (audit 2026-05-29 §6.10 /
    Phase 3) under ``artifacts/optuna/debug/trial_<N>.json``, even under
    objective_minimal, so an escalated trial is diagnosable without re-running.
    """
    try:
        tn = int(getattr(trial, "number", -1))
        out = {
            "trial_number": tn,
            "escalation_reason": reason,
            "incumbent_trial": trial.user_attrs.get("incumbent_trial") is True,
            "params": dict(params),
            "objective": float(result.objective),
            "fold_scores": list(result.fold_scores),
            "fold_metrics": [
                {"fold_id": f.fold_id, "n_trades": int(f.n_trades),
                 "fold_status": f.fold_status, **f.metrics}
                for f in folds
            ],
            "penalty_breakdown": dict(result.penalty_breakdown),
        }
        dbg_dir = Path(paths.artifact_root) / "optuna" / "debug"
        dbg_dir.mkdir(parents=True, exist_ok=True)
        (dbg_dir / f"trial_{tn:04d}.json").write_text(
            json.dumps(out, indent=2, default=str), encoding="utf-8",
        )
    except Exception as exc:  # noqa: BLE001 — debug telemetry must never fail a trial
        log.warning("could not write trial debug artifact: %s", exc)


def make_constant_surface_escalation_callback(
    log: logging.Logger, *, n_startup_trials: int, epsilon: float = 1e-6,
) -> Callable[[Any, Any], None]:
    """Audit 2026-05-29 §6.10 / Phase 3 (b) — best-effort constant-surface
    escalation. An Optuna callback that logs when the last
    ``K = max(10, n_startup_trials)`` completed trial values are all within
    ``epsilon`` (a suspected constant_objective_surface), so the operator sees
    the escalation mid-run. Best-effort: under process-parallel mode children
    see a stale study view, so the log may lag by a trial or two.
    """
    K = max(10, int(n_startup_trials))
    state = {"last_logged_for": -1}

    def _cb(study: Any, trial: Any) -> None:
        try:
            import optuna as _optuna_mod

            completed = [
                t for t in study.get_trials(deepcopy=False)
                if t.state == _optuna_mod.trial.TrialState.COMPLETE
                and t.value is not None
            ]
            if len(completed) < K:
                return
            recent = [float(t.value) for t in completed[-K:]]
            v0 = recent[0]
            if all(abs(v - v0) <= epsilon for v in recent):
                next_trial = len(study.get_trials(deepcopy=False))
                if state["last_logged_for"] != next_trial:
                    state["last_logged_for"] = next_trial
                    log.info(
                        "objective_artifact_mode escalated to full_debug for "
                        "trial %d: last %d trial values within %g of each other "
                        "(suspect constant_objective_surface)",
                        next_trial, K, epsilon,
                    )
        except Exception:  # noqa: BLE001 — a callback must never abort the study
            pass

    return _cb


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

    # Speedup report §6.2 / §11.2 Phase 7 — conservative fold-level pruning.
    pruning_cfg = (base_cfg.get("optuna") or {}).get("pruning") or {}
    pruning_enabled = bool(pruning_cfg.get("enabled", False))
    min_completed_before_prune = int(
        pruning_cfg.get("min_completed_trials_before_pruning", 30)
    )
    catastrophic_floor = float(pruning_cfg.get("catastrophic_floor", -0.5))

    # Audit 2026-05-29 §6.10 / §P0-007 / Phase 3 — debug artifact escalation.
    # Trial 0 (incumbent), the first ``debug_first_n_trials`` sampled trials, and
    # any operator-forced trial number persist a per-trial debug telemetry record
    # even under objective_minimal, so a degenerate (all-tie / no-trade) run can
    # be diagnosed without re-running the study.
    _dbg_cfg = (base_cfg.get("optuna") or {})
    debug_first_n_trials = int(_dbg_cfg.get("debug_first_n_trials", 3))
    debug_trials_force = {int(x) for x in (_dbg_cfg.get("debug_trials_force") or [])}

    def objective(trial: Any) -> float:
        try:
            # Speedup report §4 P0-B / Phase 0 task 5 — every trial calls
            # ``suggest_params`` with the SAME resolved distributions. The
            # incumbent flag is set by ``study.enqueue_trial(..., user_attrs=
            # {"incumbent_trial": True})`` in ``run_walkforward_study`` so
            # trial 0 still records as the incumbent without changing the
            # search-space distribution.
            params = suggest_params(trial, overrides=search_space_overrides)

            def _prune_cb(fold_idx: int, running_score: float) -> None:
                if not pruning_enabled:
                    return
                # Honor the TPE startup window — never prune before the
                # configured floor of completed trials.
                try:
                    import optuna as _optuna_mod

                    n_complete = sum(
                        1 for t in trial.study.get_trials(deepcopy=False)
                        if t.state == _optuna_mod.trial.TrialState.COMPLETE
                    )
                except Exception:  # noqa: BLE001 — defensive (mock studies)
                    n_complete = 0
                if n_complete < min_completed_before_prune:
                    return
                # Report to Optuna so visualisers see the running score.
                try:
                    trial.report(float(running_score), step=int(fold_idx))
                except Exception:  # noqa: BLE001
                    pass
                if running_score <= catastrophic_floor:
                    trial.set_user_attr("pruned", True)
                    trial.set_user_attr("pruned_at_fold", int(fold_idx))
                    trial.set_user_attr("pruned_running_score", float(running_score))
                    import optuna as _optuna_mod
                    raise _optuna_mod.TrialPruned(
                        f"running_score={running_score:.6f} <= floor="
                        f"{catastrophic_floor:.6f} at fold {fold_idx}"
                    )

            folds = _run_validation_folds(
                apply_trial_params(base_cfg, params), plan,
                lake_root=lake_root, feed=feed, symbols=symbols, paths=paths,
                holdout_guard=holdout_guard, log=log,
                objective_artifact_mode=objective_artifact_mode,
                fold_contexts=fold_contexts,
                prune_callback=_prune_cb,
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
            # Audit 2026-05-29 §6.5 / §A.5 / Phase 0 — carry n_trades and
            # fold_status in every fold_metrics row, plus a flat fold_statuses
            # list, so the post-study validity gates (no-trade + degraded-fold
            # detection) can read them after study.optimize without re-running
            # any backtest. This is the per-fold-status threading the audit
            # requires for the process-parallel path (workers set their own
            # trial user_attrs, so the data must live on the trial, not in
            # parent-process closures).
            trial.set_user_attr(
                "fold_metrics",
                [
                    {
                        "fold_id": f.fold_id,
                        "n_trades": int(f.n_trades),
                        "fold_status": f.fold_status,
                        **f.metrics,
                    }
                    for f in folds
                ],
            )
            trial.set_user_attr("fold_statuses", [f.fold_status for f in folds])
            # Realism remediation 2 Phase 8 (audit §P1-005) — per-trial lineage.
            if dataset_hash is not None:
                trial.set_user_attr("dataset_hash", dataset_hash)
            if config_hash is not None:
                trial.set_user_attr("config_hash", config_hash)
            if code_hash is not None:
                trial.set_user_attr("code_hash", code_hash)
            # Debug escalation (audit 2026-05-29 §6.10 / Phase 3) — persist a
            # per-trial telemetry record for the incumbent, the first N sampled
            # trials, and any operator-forced trial number.
            _is_incumbent = trial.user_attrs.get("incumbent_trial") is True
            _tn = int(getattr(trial, "number", -1))
            if _is_incumbent or _tn < debug_first_n_trials or _tn in debug_trials_force:
                _reason = (
                    "incumbent" if _is_incumbent
                    else ("forced" if _tn in debug_trials_force else "first_n")
                )
                _write_trial_debug_artifact(
                    paths=paths, trial=trial, folds=folds, result=result,
                    params=params, reason=_reason, log=log,
                )
            return result.objective
        except structural:
            raise
        except Exception as exc:  # noqa: BLE001 — one bad trial must not abort the study
            # Speedup §6.2 / Phase 7 — TrialPruned must propagate so Optuna
            # records the trial as PRUNED (not COMPLETED, not FAILED).
            try:
                import optuna as _optuna_mod

                if isinstance(exc, _optuna_mod.TrialPruned):
                    raise
            except ImportError:  # pragma: no cover — optuna is a hard dep
                pass
            log.error("trial %s failed entirely: %s", getattr(trial, "number", "?"), exc)
            return _FAILED_TRIAL_SCORE

    return objective


def _suggest_incumbent_params(
    trial: Any,
    incumbent_params: Mapping[str, Any],
    *,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """DEPRECATED: pinned the incumbent by collapsing each search-space entry to a
    near-singleton dynamic distribution for trial 0.

    Speedup report §4 P0-B / Phase 0 task 5. The collapsed-range trick changed
    Optuna's resolved distribution on trial 0 only — every later trial reverted
    to the full search-space bounds. Optuna 3.x records the per-trial
    distribution on the trial, then asserts on subsequent trials that any
    repeated ``suggest_*`` call uses the SAME distribution; the resulting
    "CategoricalDistribution does not support dynamic value space" /
    "FloatDistribution does not match the previous trial" errors put every
    non-incumbent trial into the FAILED state. Replaced by
    :func:`_enqueue_incumbent_trial` (parent-side ``study.enqueue_trial``).
    """
    raise NotImplementedError(
        "Phase 0 task 5: replaced by _enqueue_incumbent_trial; the dynamic "
        "categorical/float distributions this function produced trigger "
        "Optuna's 'CategoricalDistribution does not support dynamic value "
        "space' error — see speedup report §4 P0-B."
    )


def _enqueue_incumbent_trial(
    study: "optuna.Study",
    incumbent_params: Mapping[str, Any],
    *,
    search_space_overrides: Optional[dict[str, Any]] = None,
) -> dict[str, dict[str, Any]]:
    """Enqueue trial 0 with the live-contract incumbent params.

    Speedup report §4 P0-B / Phase 0 task 5. The enqueue path delivers the
    incumbent value to Optuna without modifying the resolved search-space
    distribution, so trial 0's ``suggest_*`` calls see the same ``(lo, hi)``
    every trial.

    Validates each incumbent value against the resolved search-space spec:

    * ``uniform`` / ``log_uniform``: clamp into ``[lo, hi]``; record in the
      returned ``clamped`` dict on change.
    * ``int``: clamp into ``[lo, hi]``; record on change.
    * ``categorical``: REFUSE silent clamping (speedup report §5.2). A
      categorical value not in the choice list is an explicit operator error;
      raise :class:`OptunaStudyInvalidError` so the operator widens the search
      space or fixes the incumbent contract before tuning.

    Returns the per-param clamp dict (empty when no clamping was needed). The
    caller is responsible for recording the clamps on ``study.user_attrs``.
    """
    from .search_space import resolve_search_space

    spec = resolve_search_space(search_space_overrides)
    checked_params: dict[str, Any] = {}
    clamped: dict[str, dict[str, Any]] = {}
    for name, entry in spec.items():
        if name not in incumbent_params:
            raise OptunaStudyInvalidError(
                f"incumbent missing required search-space param: {name}"
            )
        target = incumbent_params[name]
        kind = entry[0]
        if kind in ("uniform", "log_uniform"):
            lo, hi = float(entry[1]), float(entry[2])
            t = float(target)
            clamped_val = float(min(hi, max(lo, t)))
            if clamped_val != t:
                clamped[name] = {"target": t, "clamped": clamped_val, "range": [lo, hi]}
            checked_params[name] = clamped_val
        elif kind == "int":
            lo, hi = int(entry[1]), int(entry[2])
            t = int(target)
            clamped_val = int(min(hi, max(lo, t)))
            if clamped_val != t:
                clamped[name] = {"target": t, "clamped": clamped_val, "range": [lo, hi]}
            checked_params[name] = clamped_val
        elif kind == "categorical":
            choices = list(entry[1])
            if target not in choices:
                raise OptunaStudyInvalidError(
                    f"incumbent value {target!r} for {name} not in choices "
                    f"{choices}; widen the search space or fix the incumbent "
                    f"contract before tuning (speedup report §5.2)"
                )
            checked_params[name] = target
        else:  # pragma: no cover — defensive against future kinds
            checked_params[name] = target
    study.enqueue_trial(
        checked_params,
        user_attrs={"incumbent_trial": True},
        skip_if_exists=True,
    )
    return clamped


_MISSING = object()

#: Search-space keys with NO actual-strategy equivalent in the mapped lab
#: config. Audit 2026-05-29 §6.7 requires that NOTHING is silently padded — any
#: key listed here is an explicit, justified exclusion from the incumbent
#: comparison. Empty today: every search-space key maps to the mapped contract
#: config (the gap/ratio keys are derived in import_config's mapping).
_LAB_ONLY_SEARCH_KEYS: set[str] = set()


def _dotted_lookup(d: Mapping[str, Any], dotted: str, default: Any = None) -> Any:
    node: Any = d
    for p in dotted.split("."):
        if isinstance(node, Mapping) and p in node:
            node = node[p]
        else:
            return default
    return node


def _incumbent_gap_ratio_from_config(cfg: Mapping[str, Any]) -> dict[str, Any]:
    """Audit 2026-05-29 §6.8 — the v3 gap/ratio incumbent values computed from
    the mapped config's RAW exits fields (the inverse of
    :func:`_derived_strategy_fields`).

    The config stores absolute thresholds (soft/hard/critical, stop/target);
    the search space samples soft + hard_gap + critical_gap and
    reward_risk_ratio. Computing these here (rather than storing them in the
    config) keeps the strict ``extra="forbid"`` exits schema clean.
    """
    out: dict[str, Any] = {}
    sf = _dotted_lookup(cfg, "exits.signal_fade.score_thresholds", default={}) or {}
    if isinstance(sf, Mapping) and {"soft", "hard", "critical"} <= set(sf):
        out[_SF + "hard_gap"] = float(sf["hard"]) - float(sf["soft"])
        out[_SF + "critical_gap"] = float(sf["critical"]) - float(sf["hard"])
    stop_pct = _dotted_lookup(cfg, "exits.stop_pct")
    target_pct = _dotted_lookup(cfg, "exits.target_pct")
    if stop_pct not in (None, 0, 0.0) and target_pct is not None:
        out["exits.reward_risk_ratio"] = float(target_pct) / float(stop_pct)
    return out


def _incumbent_baseline_params(
    *, lab_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Trial 0 incumbent built from the MAPPED actual lab config.

    Audit 2026-05-29 §6.7 / Appendix E.3: the previous implementation did a
    dotted lookup of search-space keys against the *raw frozen contract*, which
    nests keys like ``execution.quote_gate.max_quote_age_seconds``. The search
    space uses flat keys like ``execution.max_quote_age_seconds``, so the lookup
    failed and the caller padded with search-space midpoints (the WARNING in the
    pasted Notebook 10 output). That padding produced an incumbent that was NOT
    the actual strategy.

    The new implementation reads from the mapped lab config (the same shape the
    shipping configs use, via :func:`reference.import_config.build_config_from_contract`)
    where the nested ``execution.quote_gate.*`` has been folded into the flat
    ``execution.max_quote_age_seconds`` / ``execution.max_spread_bps`` and the
    signal-fade / reward-risk gap/ratio keys have been derived. NOTHING is
    padded: a search-space key missing from the mapped config raises
    :class:`OptunaStudyInvalidError` (``INCUMBENT_MAPPING_INCOMPLETE``) unless
    it is an explicit :data:`_LAB_ONLY_SEARCH_KEYS` exclusion.
    """
    from ..reference import contract_available, load_actual_contract
    from ..reference.import_config import build_config_from_contract
    from .search_space import SEARCH_SPACE_SPEC

    if lab_config is None:
        if not contract_available():
            return {}
        lab_config = build_config_from_contract(
            load_actual_contract(),
            feed="iex", mode="current_code_parity", feed_thresholds="actual",
        )
    # The v3 gap/ratio search keys are computed from the mapped config's raw
    # exits fields (the config stores absolute thresholds).
    gap_ratio = _incumbent_gap_ratio_from_config(lab_config)
    missing: list[str] = []
    out: dict[str, Any] = {}
    for name in SEARCH_SPACE_SPEC:
        if name in _LAB_ONLY_SEARCH_KEYS:
            continue
        if name in gap_ratio:
            out[name] = gap_ratio[name]
            continue
        value = _dotted_lookup(lab_config, name, default=_MISSING)
        if value is _MISSING or value is None:
            missing.append(name)
        else:
            out[name] = value
    if missing:
        raise OptunaStudyInvalidError(
            f"{REASON_INCUMBENT_MAPPING_INCOMPLETE}: search-space keys missing "
            f"from the mapped lab config: {sorted(missing)}. Either map the keys "
            f"in reference/import_config.build_config_from_contract, or list each "
            f"in _LAB_ONLY_SEARCH_KEYS with a comment explaining why it has no "
            f"actual-strategy equivalent."
        )
    return out


def assert_search_space_version_compatible(
    study_user_attrs: Mapping[str, Any],
    *,
    study_name: str = "",
    current_version: int = SEARCH_SPACE_VERSION,
) -> None:
    """Audit 2026-05-29 §6.8 — refuse reuse of a study created under a different
    search-space version.

    Optuna's ``load_if_exists`` reuses a study by name; its trials were sampled
    from a DIFFERENT bound set, so mixing them with current-version trials is
    meaningless. A fresh study (no stored ``search_space_version``) passes.
    """
    prior = study_user_attrs.get("search_space_version")
    if prior is not None and int(prior) != int(current_version):
        raise OptunaStudyInvalidError(
            f"SEARCH_SPACE_HASH_MISMATCH: study {study_name!r} was created under "
            f"search_space_version={prior} but the current version is "
            f"{current_version}; a study created under a different search space "
            f"must not be reused — start a new study."
        )


def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _stub_parent_objective_for_parallel(trial: Any) -> float:
    """In process-parallel mode the parent's objective MUST NOT be called.

    Speedup report v2 §1.3 / §5.4 / Phase 2 task 1. The dispatcher's
    ``run_parallel_bowaka_optimization`` reconstructs the objective inside
    each worker via the dotted factory; the in-parent ``objective`` argument
    is only consulted in serial fallback. If the dispatcher ever calls this
    stub something has gone wrong (a process_parallel decision was made but
    the dispatcher took the serial branch).
    """
    raise RuntimeError(
        "process_parallel mode: parent objective must not be called; "
        "the dispatcher should be using the dotted factory entrypoint. "
        "See speedup report v2 §1.3 / §5.4."
    )


class _PhaseProfile:
    """Lightweight phase timer for the speedup-v2 phase-profile JSON.

    Speedup report v2 §5.8 / Phase 1 task 5. Tracks per-phase wall-clock
    seconds via :func:`time.perf_counter` deltas; phases are named by the
    caller (``resolve_config``, ``preflight``, ``fold_context_precompute``,
    ``optuna_optimize``, ``finalize``). A single phase can be re-entered;
    the helper accumulates time across re-entries.
    """

    def __init__(self) -> None:
        import time as _t
        self._t = _t
        self._times: dict[str, float] = {}
        self._current: Optional[str] = None
        self._current_start: float = 0.0

    def begin(self, name: str) -> None:
        if self._current:
            self.end()
        self._current = name
        self._current_start = self._t.perf_counter()

    def end(self) -> None:
        if self._current:
            elapsed = self._t.perf_counter() - self._current_start
            self._times[self._current] = self._times.get(self._current, 0.0) + elapsed
            self._current = None

    def snapshot(self) -> dict[str, float]:
        if self._current:
            self.end()
        return dict(self._times)


def _rss_peak_gib() -> float:
    """Best-effort peak resident-set size in GiB (current process).

    On POSIX uses ``resource.getrusage(RUSAGE_SELF).ru_maxrss`` (Linux: KiB,
    macOS: bytes); otherwise falls back to ``psutil.Process(...).memory_info()
    .rss`` which is a current — not peak — sample. Returns 0.0 when neither
    is available.
    """
    import os
    try:
        import resource  # POSIX only

        ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # Linux: KiB; macOS: bytes. Heuristic: > 2 GiB-in-bytes (~2e9) → macOS;
        # otherwise KiB → bytes via *1024.
        if ru > 2_000_000_000:
            return float(ru) / (2 ** 30)
        return float(ru * 1024) / (2 ** 30)
    except ImportError:
        pass
    try:
        import psutil  # type: ignore

        rss = psutil.Process(os.getpid()).memory_info().rss
        return float(rss) / (2 ** 30)
    except Exception:  # noqa: BLE001 — psutil import / probe error is non-fatal
        return 0.0


def _write_phase_profile_json(
    *,
    paths: "BowakaV2Paths",
    study_name: str,
    profile: _PhaseProfile,
    counters: Mapping[str, Any],
    config_hash: Optional[str],
    dataset_hash: Optional[str],
    code_hash: Optional[str],
    log: logging.Logger,
) -> Path:
    """Write the speedup-v2 phase-profile JSON next to the main study artifact.

    Speedup report v2 §5.8 / Phase 1 task 5. Schema::

        {
          "phase_seconds": {<phase>: <float>, ...},
          "counters": {<name>: <value>, ...},
          "memory": {"rss_peak_gib": <float>},
          "config_hash": "...",
          "dataset_hash": "...",
          "code_hash": "..."
        }
    """
    payload = {
        "phase_seconds": profile.snapshot(),
        "counters": dict(counters),
        "memory": {"rss_peak_gib": _rss_peak_gib()},
        "config_hash": config_hash or "",
        "dataset_hash": dataset_hash or "",
        "code_hash": code_hash or "",
    }
    out_path = Path(paths.artifact_root) / "optuna" / f"{study_name}__phase_profile.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    log.info("phase profile written: %s", out_path)
    return out_path


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
    invalid_reasons: Optional[list[str]] = None,
    validity_detail: Optional[dict[str, Any]] = None,
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
        # Audit 2026-05-29 §6.5 / Appendix E — study-validity reason codes (e.g.
        # CONSTANT_OBJECTIVE_SURFACE, NO_TRADE_STUDY, INCUMBENT_MAPPING_INCOMPLETE,
        # DEGRADED_FOLDS_PRESENT) + supporting detail. Empty for the §P0-001
        # all-sentinel failure path (which sets only ``failure_reason``).
        "invalid_reasons": list(invalid_reasons or []),
        "validity_detail": dict(validity_detail or {}),
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
    skip_best_trial_report: bool = False,
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
    # Speedup report v2 §5.8 / Phase 1 task 5 — phase profile JSON.
    # Track per-phase wall-clock from the very top so the profile attributes
    # config-load + parity-check cost too. Also bind a ProfileCounters context
    # so counter increments inside the study land somewhere readable.
    from ..utils.profile_counters import (
        ProfileCounters as _PC,
        profile_counters_context as _pcc,
    )

    _phase_profile = _PhaseProfile()
    _phase_profile.begin("resolve_config")
    _counters_inst = _PC()
    _counters_cm = _pcc(_counters_inst, enable=True)
    _counters_cm.__enter__()
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
    # Hotfix 2026-05-29: resolve via the standard chain (explicit override >
    # $MARKET_DATA_ROOT > in-repo default). The raw cfg lookup is None for
    # every shipping config, and Path(str(None)) == Path('None') downstream
    # false-positives the partition gates.
    lake_root = resolve_lake_root(cfg)
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
            daily_adjustment=daily_adjustment_for_config(cfg),
        )
        lineage = build_dataset_lineage(
            cfg=cfg, symbols=symbols,
            start=probe_sessions[0] if probe_sessions else None,
            end=probe_sessions[-1] if probe_sessions else None,
            lab_config_hash=_hash({k: v for k, v in cfg.items() if k != "_source_path"}),
        )
        # Audit 2026-06-07 §6.6-compatible "denominator-only" fix: gate the
        # study-start coverage checks on the per-session PIT-eligible set (the
        # full symbol union is still PROBED for telemetry). This is the call site
        # the ``intended_realism`` abort actually reaches first — the per-fold
        # ``run_full_fold_preflight`` gating is downstream of this gate, so it
        # must be threaded here too or the run aborts at the ungated fraction.
        from .pit_universe import eligible_per_session_map

        eligible_per_session = eligible_per_session_map(
            lake_root, probe_sessions, cfg=cfg
        )
        dq_report = build_data_quality_report(
            cfg=cfg, lineage=lineage, requested_symbols=symbols,
            sessions=probe_sessions, daily_bars_supplier=daily_supplier,
            minute_bars_supplier=minute_supplier,
            scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
            eligible_per_session=eligible_per_session,
        )
        quote_supplier = make_quote_supplier(lake_root, feed=feed)
        quote_cov_pct = probe_quote_coverage(
            symbols=symbols, sessions=probe_sessions, quote_supplier=quote_supplier,
            scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
            # Option A (audit §10d) — scope the quote-coverage estimate to the
            # PIT-eligible universe (removes the ~32pp PIT-over-inclusion drag).
            eligible_per_session=eligible_per_session,
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

    # Speedup report §4 P0-A / Phase 0 task 3: run the preflight checks
    # WITHOUT immediate raise so a failed check can be turned into a written
    # failed-status study artifact BEFORE ``build_fold_contexts`` is called.
    # This is the structural short-circuit: the broad ``except Exception`` in
    # the trial objective never sees a preflight failure, so the failed
    # artifact must land here.
    _phase_profile.begin("preflight")
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
        raise_on_fail=False,
    )
    if not preflight.passed:
        # Synthesize a placeholder study_name for the failed artifact (the
        # real study has not been created yet at this point; ``dataset_hash``
        # is computed below). The placeholder uses ``build_study_name`` with
        # an 8-char content hash of the inputs available pre-preflight so the
        # file is reproducible.
        from .dispatcher import build_study_name as _build_study_name
        from ..promotion.suitability import feed_caveat_for as _feed_caveat_for

        _placeholder_dataset_hash = _hash([
            str(config_path), feed, sim_cfg.mode,
            [s.isoformat() for s in (probe_sessions or [])],
        ])[:16]
        _placeholder_study_name = _build_study_name(
            feed=feed,
            cost_stress=str(bt.get("cost_stress", "conservative")),
            dataset_hash=_placeholder_dataset_hash,
        )
        _first_fail = next(
            (c for c in preflight.checks if c.status == "fail"),
            None,
        )
        if _first_fail is not None:
            failure_reason = (
                f"preflight {_first_fail.name} failed: {_first_fail.detail}"
            )
        else:  # pragma: no cover — defensive (passed=False with no fail check)
            failure_reason = "preflight failed (no failing check recorded)"
        _suitability_tier = tier_for_simulation_contract(sim_cfg.mode)
        if feed == "iex" and _suitability_tier != "research_only":
            _suitability_tier = "research_only"
        _trials_for_artifact = int(
            n_trials if n_trials is not None
            else optuna_cfg.get("n_trials", 20)
        )
        _startup_for_artifact = int(
            n_startup_trials if n_startup_trials is not None
            else optuna_cfg.get("n_startup_trials", 10)
        )
        _write_failed_study_artifact(
            paths=paths,
            study_name=_placeholder_study_name,
            study_metadata={"preflight": preflight.as_dict()},
            failure_reason=failure_reason,
            sim_cfg=sim_cfg,
            simulation_contract=sim_cfg.mode,
            suitability_tier=_suitability_tier,
            feed=feed,
            partial_tape=(str(feed).lower() == "iex"),
            feed_caveat=_feed_caveat_for(feed),
            plan=plan,
            trials_requested=_trials_for_artifact,
            startup=_startup_for_artifact,
            universe_pit_sample=None,
            preflight_symbol_count=len(symbols),
            log=log,
            pit_union_symbol_count=pit_union_symbol_count,
            preflight_coverage_fraction=preflight_coverage_fraction,
            research_waiver_capped_symbols=research_waiver_capped_symbols,
        )
        # Speedup report v2 §5.8 — phase profile lands even on preflight-fail
        # exit so the operator sees how long the failed run cost.
        try:
            _write_phase_profile_json(
                paths=paths, study_name=_placeholder_study_name,
                profile=_phase_profile, counters=_counters_inst.snapshot(),
                config_hash=None, dataset_hash=None, code_hash=None,
                log=log,
            )
        finally:
            _counters_cm.__exit__(None, None, None)
        raise OptunaStudyInvalidError(failure_reason)
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
    # Audit 2026-05-29 §5.4 / Phase 1 — the full per-fold preflight now runs for
    # current_code_parity too (not just intended_realism). It proves daily
    # adjustment is satisfiable, minute coverage + PIT universe exist per fold,
    # and the folds never touch the holdout — BEFORE a multi-hour study starts.
    # Under current_code_parity the IEX partial-tape gaps (missing quotes / SIP)
    # are recorded as non-blocking limitations rather than hard failures.
    iex_partial_tape_limitations: list[str] = []
    if sim_cfg.mode in ("intended_realism", "current_code_parity"):
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
            mode=sim_cfg.mode,
        )
        iex_partial_tape_limitations = list(
            getattr(full_fold_preflight_result, "iex_partial_tape_limitations", []) or []
        )
        log.info(
            "full per-fold preflight passed (mode=%s): %d folds, %d checks, "
            "%d partial-tape limitation(s): %s",
            sim_cfg.mode, len(fold_windows),
            len(full_fold_preflight_result.checks),
            len(iex_partial_tape_limitations), iex_partial_tape_limitations,
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
    # Audit 2026-05-29 §5.4 / §13.1 / Phase 1 — record the daily-bar adjustment
    # the readers actually used (resolved from config) alongside what the lake's
    # ingestion manifest declares, so a reviewer can confirm the run read
    # split-adjusted bars when the contract required them. The full-fold
    # preflight already hard-failed if the required partition was absent.
    effective_daily_adjustment = daily_adjustment_for_config(cfg)
    manifest_daily_adjustment = effective_daily_adjustment
    try:
        from bowaka_common.marketdata import layout as _layout

        from .preflight import _coerce_lake_root

        _mp = _layout.ingestion_manifest_path(_coerce_lake_root(lake_root))
        if _mp.is_file():
            manifest_daily_adjustment = str(
                json.loads(_mp.read_text(encoding="utf-8")).get(
                    "adjustment", effective_daily_adjustment
                )
            )
    except Exception:  # noqa: BLE001 — a missing/unreadable manifest is non-fatal
        pass

    # Audit 2026-05-29 §7 / §8.1 / Phase 3 — persist the RESOLVED config under
    # artifacts (not volatile /tmp) so the run's exact inputs are reproducible,
    # and record its SHA-256 in the manifest. The resolved config is the
    # in-memory cfg minus the loader's ``_source_path`` annotation.
    import yaml as _yaml

    _resolved_cfg = {k: v for k, v in cfg.items() if k != "_source_path"}
    _resolved_bytes = _yaml.safe_dump(_resolved_cfg, sort_keys=True).encode("utf-8")
    resolved_config_sha256 = hashlib.sha256(_resolved_bytes).hexdigest()
    resolved_config_path = (
        Path(paths.artifact_root) / "resolved_configs"
        / f"{study.study.study_name}__resolved.yml"
    )
    try:
        resolved_config_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_config_path.write_bytes(_resolved_bytes)
    except Exception as exc:  # noqa: BLE001 — persistence is best-effort lineage
        log.warning("could not persist resolved config: %s", exc)

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
        "effective_daily_adjustment": effective_daily_adjustment,
        "manifest_daily_adjustment": manifest_daily_adjustment,
        "iex_partial_tape_limitations": iex_partial_tape_limitations,
        "resolved_config_sha256": resolved_config_sha256,
        "resolved_config_path": str(resolved_config_path),
        "preflight": preflight.as_dict(),
        "penalty_weights": vars(DEFAULT_PENALTY_WEIGHTS),
        "search_space_overrides": search_space_overrides,
        # Audit 2026-05-29 §9 Phase 5 task 6 — holdout isolation was in force
        # during tuning (per-fold HoldoutGuard.assert_can_read). Flows into the
        # study user_attrs (loop below) so the validity gate can read it.
        "holdout_guard_active": True,
    }
    if feed_caveat is not None:
        study_metadata["feed_caveat"] = feed_caveat
    # Audit 2026-05-29 §6.8 / Appendix E.6 — refuse to reuse a study created
    # under a DIFFERENT search-space version. Runs BEFORE the user_attr loop
    # below overwrites the stored version with the current one.
    assert_search_space_version_compatible(
        study.study.user_attrs, study_name=study.study.study_name,
    )
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
    # Speedup report §4 P0-B / Phase 0 task 5 — incumbent baseline. When opted
    # in, the actual-contract parameter set is enqueued as trial 0 via
    # ``study.enqueue_trial``; the resolved search-space distributions are NOT
    # collapsed (the legacy ``_suggest_incumbent_params`` path triggered Optuna
    # "dynamic value space" errors on every subsequent trial).
    incumbent_params: Optional[dict[str, Any]] = None
    if incumbent_trial:
        # Audit 2026-05-29 §6.7 — _incumbent_baseline_params reads the MAPPED
        # actual lab config and raises INCUMBENT_MAPPING_INCOMPLETE if any
        # search-space key is missing (NO silent padding — the old midpoint
        # padding produced a Trial 0 that was NOT the actual strategy). An empty
        # dict means the frozen contract is unavailable (e.g. a smoke run with
        # no generated contract); trial 0 then falls back to a TPE-startup
        # sample.
        incumbent_params = _incumbent_baseline_params()
        if incumbent_params:
            clamped = _enqueue_incumbent_trial(
                study.study, incumbent_params,
                search_space_overrides=search_space_overrides,
            )
            if clamped:
                study.study.set_user_attr("incumbent_clamped", clamped)
                log.warning(
                    "incumbent enqueue clamped %d param(s) into search-space "
                    "bounds: %s",
                    len(clamped), sorted(clamped.keys()),
                )
            log.info(
                "incumbent baseline: enqueued trial 0 with %d params "
                "(all from the mapped actual contract; no padding)",
                len(incumbent_params),
            )
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

    # Speedup report v2 §1.3 / §4 P2 / §5.4 / Phase 2 — parallel preflight
    # runs BEFORE ``build_fold_contexts`` so a strict-parallel run against
    # SQLite, or with a memory budget that cannot fit the requested worker
    # count, fails closed BEFORE the parent pays the context-build cost. In
    # process-parallel mode the parent skips the parent-side context build
    # entirely — workers rebuild contexts inside each subprocess via the
    # dotted factory.
    assert_search_space_does_not_affect_context(search_space_overrides)
    cached_suppliers_flag = bool((cfg.get("optuna") or {}).get("cached_suppliers", False))
    parallel_cfg = (cfg.get("optuna") or {}).get("parallel") or {}
    strict_parallel_flag = bool(parallel_cfg.get("strict_parallel", False))
    mem_budget = MemoryBudget.from_system(
        reserve_system_gib=float(parallel_cfg.get("memory_reserve_gib", 32.0)),
        max_optuna_workers=int(parallel_cfg.get("max_workers", 8)),
    )
    from .parallel import (
        ParallelDecision as _ParallelDecision,
        preflight_parallel_dispatch as _preflight_parallel_dispatch,
    )
    from ..utils.profile_counters import (
        counters_enabled as _ce2,
        current_profile_counters as _cpc2,
    )
    import time as _time

    _pp_start = _time.perf_counter()
    try:
        parallel_decision = _preflight_parallel_dispatch(
            study.study, n_jobs=jobs,
            storage_uri=resolved_storage_uri,
            mem_budget=mem_budget,
            strict_parallel=strict_parallel_flag,
        )
    except OptunaStudyInvalidError as struct_exc:
        failure_reason = f"parallel preflight: {struct_exc}"
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
        try:
            _write_phase_profile_json(
                paths=paths, study_name=study.study.study_name,
                profile=_phase_profile, counters=_counters_inst.snapshot(),
                config_hash=lab_config_hash, dataset_hash=dataset_hash,
                code_hash=code_hash, log=log,
            )
        finally:
            _counters_cm.__exit__(None, None, None)
        raise OptunaStudyInvalidError(failure_reason) from struct_exc
    finally:
        _pp_end = _time.perf_counter()
        if _ce2():
            try:
                _cpc2().inc(parallel_preflight_seconds=_pp_end - _pp_start)
            except LookupError:
                pass
    study.study.set_user_attr("dispatch_mode", parallel_decision.mode)
    study.study.set_user_attr("dispatch_reason", parallel_decision.reason)
    study.study.set_user_attr("dispatch_n_workers", parallel_decision.n_workers)
    log.info(
        "parallel preflight: mode=%s n_workers=%d reason=%s",
        parallel_decision.mode, parallel_decision.n_workers,
        parallel_decision.reason,
    )

    # Speedup report §5.2 / §11.2 Phase 2 — build the per-fold runtime
    # context ONCE, before constructing the objective. The search-space
    # guard refuses any tuned parameter that would invalidate the cache.
    # Speedup report §5.3 / §11.2 Phase 3 — opt-in cached supplier adapter.
    # NB: strict-parallel skips the parent context build (workers rebuild
    # via the dotted factory) — speedup v2 §1.3 / §5.4 / Phase 2.
    fold_contexts: Optional[tuple] = None
    if parallel_decision.mode == "process_parallel":
        log.info(
            "process_parallel mode — parent skips build_fold_contexts; "
            "workers rebuild via the dotted factory (speedup v2 §5.4)"
        )
        objective = _stub_parent_objective_for_parallel
    else:
        _phase_profile.begin("fold_context_precompute")
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

    # Audit 2026-05-23 §P0-001 — a structural exception escaping the trial
    # must abort the study with a written failed-status artifact rather than
    # being swallowed by Optuna's loop. The artifact preserves the study
    # metadata (forensic) and the structural failure reason; the runner then
    # re-raises ``OptunaStudyInvalidError``.
    structural = structural_exceptions()
    _phase_profile.begin("optuna_optimize")
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
            # Audit 2026-05-29 §6.10 / Phase 3 (b) — best-effort constant-surface
            # escalation log (serial path only; harmless under parallel).
            callbacks=[
                make_constant_surface_escalation_callback(
                    log, n_startup_trials=startup,
                )
            ],
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
        try:
            _write_phase_profile_json(
                paths=paths, study_name=study.study.study_name,
                profile=_phase_profile, counters=_counters_inst.snapshot(),
                config_hash=lab_config_hash, dataset_hash=dataset_hash,
                code_hash=code_hash, log=log,
            )
        finally:
            _counters_cm.__exit__(None, None, None)
        raise OptunaStudyInvalidError(failure_reason) from struct_exc

    import optuna

    # Speedup §6.2 / Phase 7 — pruned trials are recorded but NEVER part of
    # the completed-trial pool. ``optuna.trial.TrialState.COMPLETE`` already
    # filters them out (pruned trials hold state ``PRUNED``); record the
    # count for visibility regardless of ``allow_pruned_in_promotion``.
    pruned = [t for t in study.study.trials if t.state == optuna.trial.TrialState.PRUNED]
    if pruned:
        study.study.set_user_attr("n_pruned_trials", len(pruned))
        log.info("study has %d pruned trial(s) (excluded from best-trial selection)", len(pruned))
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
        # Audit 2026-05-29 §A.5 / Phase 0 task 6 — a trial with ANY degraded
        # fold is not a valid datapoint. ``_run_validation_folds`` appends a
        # ``_degraded_fold`` (fold_status="degraded") on broad non-structural
        # exceptions; previously the filter accepted its finite sentinel score.
        # Read the per-fold status threaded through trial user_attrs (works in
        # the process-parallel path, where workers set their own attrs).
        fold_statuses = t.user_attrs.get("fold_statuses") or [
            str(fm.get("fold_status", "ok")) for fm in fold_metrics
        ]
        if any(s != "ok" for s in fold_statuses):
            invalid_trials.append((t, "degraded_fold"))
            continue
        valid_trials.append(t)

    # Audit 2026-05-29 §6.5 / Appendix E — post-study validity gates. Runs
    # BEFORE the §P0-001 zero-valid check below so the specific audit reason
    # (e.g. DEGRADED_FOLDS_PRESENT) surfaces even when the per-trial filter
    # already emptied ``valid_trials``. A study can have finite, non-sentinel
    # "valid" trials and STILL be scientifically invalid: every trial tied at
    # the same penalty (no TPE signal — the constant -1.5 surface from the
    # pasted Notebook 10 run), no trial generated a single trade, the incumbent
    # baseline was silently padded with search-space midpoints (fixed at the
    # root in Phase 2), or a fold degraded. These fail closed: write a failed
    # artifact and raise so Notebook 10 sees an exception, never a "best trial"
    # recommendation built on no signal. Opt-out flags
    # (optuna.allow_constant_objective_surface / allow_no_trade_study /
    # allow_padded_incumbent) exist for diagnostic runs only.
    from .study_validity import evaluate_study_validity as _evaluate_study_validity

    _validity = _evaluate_study_validity(
        trial_values=[float(t.value) for t in completed if t.value is not None],
        fold_metrics_per_trial=[
            list(t.user_attrs.get("fold_metrics") or []) for t in completed
        ],
        fold_status_per_trial=[
            list(
                t.user_attrs.get("fold_statuses")
                or [
                    str(fm.get("fold_status", "ok"))
                    for fm in (t.user_attrs.get("fold_metrics") or [])
                ]
            )
            for t in completed
        ],
        study_user_attrs=dict(study.study.user_attrs),
        cfg_optuna=(cfg.get("optuna") or {}),
    )
    if not _validity.valid:
        failure_reason = "study_invalid"
        log.error(
            "walk-forward study %s INVALID: %s (detail=%s)",
            study.study.study_name,
            ", ".join(_validity.invalid_reasons),
            _validity.detail,
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
            invalid_reasons=list(_validity.invalid_reasons),
            validity_detail=dict(_validity.detail),
        )
        try:
            _write_phase_profile_json(
                paths=paths, study_name=study.study.study_name,
                profile=_phase_profile, counters=_counters_inst.snapshot(),
                config_hash=lab_config_hash, dataset_hash=dataset_hash,
                code_hash=code_hash, log=log,
            )
        finally:
            _counters_cm.__exit__(None, None, None)
        raise OptunaStudyInvalidError(
            f"study_invalid: {', '.join(_validity.invalid_reasons)}"
        )

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
        try:
            _write_phase_profile_json(
                paths=paths, study_name=study.study.study_name,
                profile=_phase_profile, counters=_counters_inst.snapshot(),
                config_hash=lab_config_hash, dataset_hash=dataset_hash,
                code_hash=code_hash, log=log,
            )
        finally:
            _counters_cm.__exit__(None, None, None)
        raise OptunaStudyInvalidError(failure_reason)
    # Speedup report v2 §5.8 / Phase 1 task 5 — kick off the finalize phase
    # for the success path (best-trial reporting, neighbour evaluation,
    # promotion evidence assembly, results-JSON write).
    _phase_profile.begin("finalize")

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
    # ``skip_best_trial_report`` skips ONLY the single-best neighbour/robustness
    # sweep (which re-runs folds in FULL artifact mode — DQ not cached, ~minutes
    # per neighbour). The ranking, best_params, top-k clustering and promotion
    # evidence below are cheap (no backtests) and still produced. Callers that
    # do their own finalist evaluation (the top-N robustness sweep cell/tool)
    # pass ``skip_best_trial_report=True`` to return as soon as the trials are in.
    best_report: dict[str, Any] = {}
    if best is not None and skip_best_trial_report:
        best_report = {
            "skipped": "single-best neighbour sweep skipped (skip_best_trial_report=True); "
                       "evaluate finalists with the top-N robustness sweep "
                       "(scripts/topn_robustness_sweep.py / notebook cell)",
        }
    elif best is not None:
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

    # Audit 2026-05-29 §6.8 / Phase 2 — export BOTH the internal (gap/ratio)
    # search-space keys AND the derived actual-strategy fields (hard / critical
    # / target_pct) in best_params, so downstream tooling can consume either
    # shape. ``derived_keys`` lists the derived names.
    _best_internal = (dict(best.params) if best else {})
    _best_derived = _derived_strategy_fields(_best_internal) if _best_internal else {}
    best_params_export = {**_best_internal, **_best_derived}
    best_derived_keys = sorted(_best_derived.keys())

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
        "best_params": best_params_export,
        "derived_keys": best_derived_keys,
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

    # Audit 2026-05-29 §6.8 / §10.4 — structured promotion evidence. Separate
    # booleans so a reviewer can never mistake a valid IEX research run (or a
    # completed-but-invalid study) for a parameter recommendation. This is a
    # success-path study (study_valid=True); IEX caps recommendation at
    # research_only regardless.
    from .promotion_gates import evaluate_promotion_evidence as _eval_evidence

    _evidence = _eval_evidence(
        study_valid=True,
        invalid_reasons=[],
        feed=feed,
        simulation_mode=sim_cfg.mode,
        risk_control_drift=bool(promotion_decision["risk_policy_experiment"]),
        # Paper-reconciliation evidence is produced by a later phase; absent here.
        paper_reconciliation_artifact_present=False,
        best_params=best_params_export,
        requested_tier=str(promotion_decision["requested_tier"]),
    )

    promotion_evidence: dict[str, Any] = {
        "schema_version": 3,
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
        "best_params": best_params_export,
        "derived_keys": best_derived_keys,
        # Audit 2026-05-29 §6.8 / §10.4 — structured promotion booleans (flat so
        # a reviewer / the verification CLI reads them directly). These are the
        # authoritative answers; ``promotable`` below is a back-compat alias.
        "study_execution_completed": _evidence.study_execution_completed,
        "study_valid": _evidence.study_valid,
        "invalid_reasons": list(_evidence.invalid_reasons),
        "reviewable_for_research": _evidence.reviewable_for_research,
        "parameter_recommendation_allowed": _evidence.parameter_recommendation_allowed,
        "promotable_to_paper": _evidence.promotable_to_paper,
        "promotable_to_live": _evidence.promotable_to_live,
        "caps_applied": list(_evidence.caps_applied),
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
    # Speedup report v2 §5.8 / Phase 1 task 5 — phase profile JSON.
    try:
        _phase_profile_path = _write_phase_profile_json(
            paths=paths, study_name=study.study.study_name,
            profile=_phase_profile, counters=_counters_inst.snapshot(),
            config_hash=lab_config_hash, dataset_hash=dataset_hash,
            code_hash=code_hash, log=log,
        )
        out["phase_profile_path"] = str(_phase_profile_path)
    finally:
        _counters_cm.__exit__(None, None, None)
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
