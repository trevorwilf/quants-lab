"""Substantive data-quality report for v2 backtests (realism Phase 2).

Replaces the empty ``data_quality_report.json`` ``"checks": []`` with checks
derived from the lake's research-audit parquet plus per-run coverage / quote /
adjustment checks. In ``intended_realism`` mode a ``fail`` on any *required*
check fails the run closed (see :func:`evaluate_startup_dq`).

Check shape (every entry in ``checks``)::

    {"name": str,
     "status": "pass" | "fail" | "warn",
     "count": int,
     "threshold": Any,
     "source_file": str,
     "evidence": dict}

The report document::

    {"schema_version": 2,
     "regime": "lake" | "synthetic",
     "feed": str,
     "passed": int, "failed": int, "warned": int,
     "checks": [...],
     "per_symbol_failures": {symbol: [check_name, ...]},
     "required_failures": [check_name, ...],
     "notes": str}

Only ``intended_realism`` runs are gated; ``smoke_fixture`` and
``current_code_parity`` runs surface the same report but are never failed by it.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

import pandas as pd

from bowaka_common.marketdata import layout as _layout

DATA_QUALITY_SCHEMA_VERSION = 2


class DataQualityError(RuntimeError):
    """Raised when a data-quality required check fails and the caller asked for
    raise-on-fail behaviour.

    Audit 2026-05-23 §P0-001 / §P0-003. The default report-returning API is
    unchanged — :func:`build_data_quality_report` still returns a report
    document. This exception is the structural signal that the Optuna runner's
    ``except STRUCTURAL_EXCEPTIONS: raise`` block must not swallow into a
    sentinel score.
    """


class StartupDataQualityError(DataQualityError):
    """Raised at the start of :func:`bowaka_v2_lab.sim.backtester.run_backtest`
    when :func:`evaluate_startup_dq` rejects the run.

    Speedup report §4 P0-A / §5.1. The pre-remediation behaviour was a generic
    ``RuntimeError`` at the abort point in the backtester; the Optuna runner's
    ``_run_validation_folds`` then matched the broad ``except Exception`` clause
    and degraded the fold to ``_degraded_fold``, swallowing the structural
    rejection behind a numeric sentinel score. ``StartupDataQualityError`` is a
    subclass of :class:`DataQualityError`, so the runner's ``except structural:
    raise`` block (already bound to ``DataQualityError`` via
    :func:`bowaka_v2_lab.optuna.errors.structural_exceptions`) propagates it
    out of the trial and aborts the study with
    :class:`bowaka_v2_lab.optuna.errors.OptunaStudyInvalidError`.
    """

#: Per-symbol audit columns mapped to DQ checks. ``0`` is healthy for every
#: count column; any positive count is a defect of the labelled severity.
#: ``passed_research_audit`` is the audit's own boolean verdict.
_AUDIT_COUNT_CHECKS: tuple[tuple[str, str], ...] = (
    # (audit column, severity when count > 0)
    ("missing_sessions", "fail"),
    ("duplicate_sessions", "fail"),
    ("ohlc_violations", "fail"),
    ("zero_volume_sessions", "warn"),
    ("large_gap_flags", "warn"),
)

#: Checks that gate an ``intended_realism`` run when their status is ``fail``.
#: Audit-derived data-integrity checks plus the per-run coverage / adjustment /
#: quote checks. ``zero_volume_sessions`` / ``large_gap_flags`` are advisory
#: (``warn`` only) and never gate.
_REQUIRED_CHECK_NAMES: frozenset[str] = frozenset(
    {
        "audit_missing_sessions",
        "audit_duplicate_sessions",
        "audit_ohlc_violations",
        "audit_passed_research_audit",
        "coverage_missing",
        "adjustment_mismatch",
        "split_adjustment_mismatch",
        "quotes_required_but_absent",
        # Realism Phase 6 — finalize-step historical-quote-coverage gate.
        "quote_coverage",
        # Realism remediation 2 Phase 3 — multi-level DQ required checks
        # (audit §P0-010). Ingestion-level OHLC / schema / timestamp defects, the
        # deeper session / replay coverage checks, the feature-leakage check, and
        # the halt-status availability gate all gate an intended_realism run.
        "ingestion_schema",
        "ingestion_timestamps_sorted",
        "ingestion_duplicate_timestamps",
        "ingestion_ohlc_violation",
        "ingestion_nonpositive_price",
        "coverage_missing_late_session",
        "coverage_missing_exit_path",
        "session_minute_count_violation",
        "intraday_gap",
        "feature_leakage",
        "halt_data_unavailable_when_required",
        # Realism remediation 2 Phase 10 — SIP migration scaffolding (audit
        # §11 Phase 9). A ``feed: sip`` config against a SIP-less lake fails
        # closed; ``feed: iex`` runs never check SIP partitions (no regression).
        "sip_data_absent",
    }
)

#: Speedup report v2 §4 P4 / §5.6 / Phase 3 task 1 — invariance classification
#: of every DQ check. A check is **invariant** when its result depends only on
#: quantities held fixed for a study/fold context (``cfg.market_data``,
#: ``cfg.simulation.mode``, lineage, requested symbols, sessions,
#: ``daily_cache_by_session``, ``session_minute_supplier``). It is
#: **trial_dependent** when any tuned search-space parameter could change the
#: result. Examples: ``quote_coverage`` uses ``max_quote_age_seconds`` (in the
#: search space) → trial_dependent; ``coverage_missing_exit_path`` uses
#: ``exits.max_hold_days`` (in the search space) → trial_dependent. When in
#: doubt, mark trial_dependent (the cache then rebuilds; conservatism wins).
#:
#: Bump :data:`DQ_CHECK_INVARIANCE_VERSION` on EVERY change to this dict (or
#: when the search space starts tuning a previously-frozen knob). The cache
#: invalidation key includes the version so a bump force-rebuilds every
#: study's cached report.
DQ_CHECK_INVARIANCE_VERSION = 1
_DQ_CHECK_INVARIANCE: dict[str, str] = {
    # ---- audit-derived (lineage / lake state — never trial-tuned) ----------
    "audit_missing_sessions": "invariant",
    "audit_duplicate_sessions": "invariant",
    "audit_ohlc_violations": "invariant",
    "audit_zero_volume_sessions": "invariant",
    "audit_large_gap_flags": "invariant",
    "audit_passed_research_audit": "invariant",
    "audit_available": "invariant",
    # ---- coverage / adjustment / quote partitions (lake + config flags) ----
    # ``coverage_missing`` is per-(symbol, session). It IS invariant across
    # trials within the same fold — symbols are fixed (per-fold PIT
    # eligible union from ``universe_snapshot_by_session``); only strategy
    # params vary across trials. The fold-context stamper + the trial
    # reader both derive ``requested_symbols`` from the same per-fold
    # universe snapshot, so the cache key's ``symbols_hash`` matches and
    # the cached coverage_missing result is reused.
    "coverage_missing": "invariant",
    "adjustment_mismatch": "invariant",
    "split_adjustment_mismatch": "invariant",
    "quotes_partitions_available": "invariant",
    "quotes_required_but_absent": "invariant",
    # ``quote_coverage`` consumes ``max_quote_age_seconds`` (Optuna search-space
    # leaf) — trial_dependent.
    "quote_coverage": "trial_dependent",
    "sip_data_present": "invariant",
    "sip_data_absent": "invariant",
    "synthetic_data": "invariant",
    # ---- multi-level DQ (audit §P0-010 / realism remediation 2 Phase 3) ----
    "ingestion_schema": "invariant",
    "ingestion_timestamps_sorted": "invariant",
    "ingestion_duplicate_timestamps": "invariant",
    "ingestion_ohlc_violation": "invariant",
    "ingestion_nonpositive_price": "invariant",
    "ingestion_volume_anomaly": "invariant",
    "ingestion_level_error": "invariant",
    "session_minute_count_violation": "invariant",
    "intraday_gap": "invariant",
    "session_stale_segment": "invariant",
    "session_level_error": "invariant",
    "coverage_missing_late_session": "invariant",
    # ``coverage_missing_exit_path`` consumes ``exits.max_hold_days`` (in the
    # search space) — trial_dependent.
    "coverage_missing_exit_path": "trial_dependent",
    # ``replay_quote_age_violation`` consumes ``max_quote_age_seconds`` (in
    # the search space) — trial_dependent.
    "replay_quote_age_violation": "trial_dependent",
    "replay_level_error": "invariant",
    "feature_leakage": "invariant",
    "feature_split_unaware": "invariant",
    "feature_level_error": "invariant",
    "halt_data_unavailable_when_required": "invariant",
    "quote_status_level_error": "invariant",
}


def dq_check_invariance(name: str) -> str:
    """Return ``"invariant"`` / ``"trial_dependent"`` for a check name.

    Unknown names default to ``"trial_dependent"`` so a forgotten classification
    never poisons the cache silently — the conservative fallback forces a
    rebuild rather than reusing a possibly-stale row.
    """
    return _DQ_CHECK_INVARIANCE.get(name, "trial_dependent")


def merge_dq_reports(
    a: Mapping[str, Any], b: Mapping[str, Any],
) -> dict[str, Any]:
    """Merge two partial DQ reports (invariant + trial_dependent halves).

    Speedup report v2 §4 P4 / Phase 3 task 3. Concatenates ``checks``,
    deduplicates by ``name`` (the second mapping wins on collision — which
    should never happen for a clean split but is the conservative fallback),
    then rebuilds ``failed`` / ``required_failures`` /
    ``adjustment_gating_failures`` from the merged ``checks`` list. Other
    top-level fields are taken from ``a`` (the invariant half) with any
    additional keys from ``b`` layered on top.
    """
    by_name: dict[str, dict[str, Any]] = {}
    for c in (a.get("checks") or ()):
        by_name[c["name"]] = dict(c)
    for c in (b.get("checks") or ()):
        by_name[c["name"]] = dict(c)
    merged_checks = list(by_name.values())
    failed = [c["name"] for c in merged_checks if c.get("status") == "fail"]
    required_failures = [
        n for n in failed if n in _REQUIRED_CHECK_NAMES
    ]
    adjustment_gating_failures = [
        n for n in failed if n in _ADJUSTMENT_GATING_CHECK_NAMES
    ]
    merged = dict(a)
    for k, v in b.items():
        if k not in ("checks", "failed", "required_failures",
                     "adjustment_gating_failures", "passed", "warned"):
            merged.setdefault(k, v)
    merged["checks"] = merged_checks
    merged["failed"] = sum(1 for c in merged_checks if c.get("status") == "fail")
    merged["passed"] = sum(1 for c in merged_checks if c.get("status") == "pass")
    merged["warned"] = sum(1 for c in merged_checks if c.get("status") == "warn")
    merged["required_failures"] = sorted(set(required_failures))
    merged["adjustment_gating_failures"] = sorted(set(adjustment_gating_failures))
    return merged


#: Adjustment-enforcement checks (realism remediation 2 Phase 1, audit §P0-005).
#: Unlike the rest of :data:`_REQUIRED_CHECK_NAMES` — which gate only
#: ``intended_realism`` — these gate ANY non-smoke run: a ``current_code_parity``
#: run against a raw lake whose config requires adjusted daily bars must also
#: fail closed (raw daily baselines silently corrupt RVOL / ATR / EMA / split
#: gates). ``smoke_fixture`` runs are still never gated by data quality.
_ADJUSTMENT_GATING_CHECK_NAMES: frozenset[str] = frozenset(
    {
        "adjustment_mismatch",
        "split_adjustment_mismatch",
    }
)

#: Fraction of expected (symbol, session) pairs that may be missing before
#: ``coverage_missing`` fails a realism run.
COVERAGE_MISSING_FAIL_FRACTION = 0.01


# --------------------------------------------------------------------------
# Audit parquet
# --------------------------------------------------------------------------
def find_latest_audit(lake_root: Path, *, feed: str) -> Optional[Path]:
    """Most-recent ``_ingestion/audits/audit_*_<feed>.parquet`` for ``feed``.

    Audit files are named ``audit_<UTC-timestamp>_<feed>.parquet``; the
    timestamp sorts lexicographically, so the last match is the newest.
    """
    audits_dir = _layout.ingestion_dir(lake_root) / "audits"
    if not audits_dir.is_dir():
        return None
    matches = sorted(audits_dir.glob(f"audit_*_{feed}.parquet"))
    if matches:
        return matches[-1]
    # Fall back to any audit file if none carries this feed suffix.
    any_audit = sorted(audits_dir.glob("audit_*.parquet"))
    return any_audit[-1] if any_audit else None


def _check(
    name: str,
    status: str,
    count: int,
    threshold: Any,
    source_file: str,
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "count": int(count),
        "threshold": threshold,
        "source_file": source_file,
        "evidence": dict(evidence),
    }


def build_audit_checks(
    audit_path: Optional[Path],
    *,
    feed: str,
    requested_symbols: Optional[Iterable[str]] = None,
) -> list[dict[str, Any]]:
    """Build per-audit checks from the lake's research-audit parquet.

    One aggregate check per audit dimension (``missing_sessions``,
    ``duplicate_sessions``, ``ohlc_violations``, ``zero_volume_sessions``,
    ``large_gap_flags``, ``passed_research_audit``), each carrying per-symbol
    evidence for the offending symbols. When ``requested_symbols`` is given the
    audit is filtered to that universe so the checks reflect the run's selection.
    """
    if audit_path is None or not Path(audit_path).is_file():
        return []
    try:
        df = pd.read_parquet(audit_path)
    except Exception:  # noqa: BLE001 — an unreadable audit yields no checks, not a crash
        return []
    if df.empty:
        return []
    src = Path(audit_path).name
    # Restrict to this feed when the column is present.
    if "feed" in df.columns:
        df = df[df["feed"].astype(str) == str(feed)]
    if requested_symbols is not None:
        want = {str(s) for s in requested_symbols}
        if "symbol" in df.columns and want:
            df = df[df["symbol"].astype(str).isin(want)]
    if df.empty:
        return []

    checks: list[dict[str, Any]] = []
    for column, severity in _AUDIT_COUNT_CHECKS:
        if column not in df.columns:
            continue
        col = pd.to_numeric(df[column], errors="coerce").fillna(0).astype(int)
        offending = df[col > 0]
        total = int(col.sum())
        per_symbol = (
            {
                str(r["symbol"]): int(r[column])
                for _, r in offending.iterrows()
                if "symbol" in offending.columns
            }
            if not offending.empty
            else {}
        )
        status = severity if total > 0 else "pass"
        checks.append(
            _check(
                name=f"audit_{column}",
                status=status,
                count=total,
                threshold=0,
                source_file=src,
                evidence={
                    "audited_symbols": int(len(df)),
                    "offending_symbols": int(len(offending)),
                    "per_symbol": dict(sorted(per_symbol.items())[:50]),
                },
            )
        )

    # passed_research_audit — the audit's own boolean verdict.
    if "passed_research_audit" in df.columns:
        passed = df["passed_research_audit"].astype(bool)
        failed_rows = df[~passed]
        n_failed = int((~passed).sum())
        checks.append(
            _check(
                name="audit_passed_research_audit",
                status="fail" if n_failed > 0 else "pass",
                count=n_failed,
                threshold=0,
                source_file=src,
                evidence={
                    "audited_symbols": int(len(df)),
                    "failed_symbols": sorted(
                        str(s) for s in failed_rows.get("symbol", pd.Series(dtype=str))
                    )[:50],
                },
            )
        )
    return checks


# --------------------------------------------------------------------------
# Per-run coverage
# --------------------------------------------------------------------------
def build_coverage_check(
    *,
    requested_symbols: Iterable[str],
    sessions: Iterable[_dt.date],
    daily_bars_supplier,
    minute_bars_supplier,
    scan_times_per_session,
    source_file: str = "(per-run coverage probe)",
) -> dict[str, Any]:
    """Probe daily + minute bar coverage for every (symbol, session) pair.

    For each ``(symbol, session_date)`` it checks a daily bar exists, and that
    minute bars exist for the session's first scan timestamp. Absent pairs are
    recorded under ``coverage_missing``. ``status`` is ``fail`` when the missing
    fraction is at or above :data:`COVERAGE_MISSING_FAIL_FRACTION`, else ``warn``
    (when some are missing) or ``pass``.

    The realism gate (:func:`evaluate_startup_dq`) only acts on ``fail``.
    """
    symbols = [str(s) for s in requested_symbols]
    session_list = list(sessions)
    expected = len(symbols) * len(session_list)
    missing_daily: list[str] = []
    missing_minute: list[str] = []

    for session_date in session_list:
        try:
            scan_times = list(scan_times_per_session(session_date))
        except Exception:  # noqa: BLE001
            scan_times = []
        probe_ts = scan_times[0] if scan_times else None
        for sym in symbols:
            pair = f"{sym}@{session_date.isoformat()}"
            day_ok = False
            try:
                day = daily_bars_supplier(sym, session_date)
                day_ok = day is not None and len(day) > 0
            except Exception:  # noqa: BLE001 — a supplier error counts as missing
                day_ok = False
            if not day_ok:
                missing_daily.append(pair)
            if probe_ts is not None:
                minute_ok = False
                try:
                    minute = minute_bars_supplier(sym, probe_ts)
                    minute_ok = minute is not None and len(minute) > 0
                except Exception:  # noqa: BLE001
                    minute_ok = False
                if not minute_ok:
                    missing_minute.append(pair)

    missing_pairs = sorted(set(missing_daily) | set(missing_minute))
    n_missing = len(missing_pairs)
    frac = (n_missing / expected) if expected else 0.0
    if expected == 0:
        # A lake-backed run with zero (symbol, session) pairs to cover is
        # degenerate — there is no data to test. This is a coverage failure,
        # not a benign warning: a realism run must not silently pass on an
        # empty universe (e.g. a SIP-feed config against an IEX-only lake).
        status = "fail"
        empty_detail = (
            "the requested universe x date range resolved to ZERO "
            "(symbol, session) pairs — no market data to test"
        )
    elif frac >= COVERAGE_MISSING_FAIL_FRACTION:
        status = "fail"
        empty_detail = None
    elif n_missing > 0:
        status = "warn"
        empty_detail = None
    else:
        status = "pass"
        empty_detail = None
    evidence: dict[str, Any] = {
        "expected_pairs": expected,
        "missing_pairs": n_missing,
        "missing_fraction": round(frac, 6),
        "missing_daily": missing_daily[:50],
        "missing_minute": missing_minute[:50],
    }
    if empty_detail is not None:
        evidence["detail"] = empty_detail
    return _check(
        name="coverage_missing",
        status=status,
        count=n_missing if expected else 1,
        threshold={"fail_fraction": COVERAGE_MISSING_FAIL_FRACTION, "expected_pairs": expected},
        source_file=source_file,
        evidence=evidence,
    )


# --------------------------------------------------------------------------
# Adjustment / corporate actions
# --------------------------------------------------------------------------
def build_adjustment_check(
    *,
    require_adjusted: bool,
    lake_adjustment: str,
    source_file: str,
) -> dict[str, Any]:
    """Check the lake's adjustment policy against ``require_adjusted_daily_bars``.

    A config that requires adjusted daily bars against a ``raw`` lake produces
    ``adjustment_mismatch: fail`` (a required check). If the config does not
    require adjustment the check is informational (``pass``).
    """
    mismatch = bool(require_adjusted) and str(lake_adjustment) == "raw"
    detail = None
    if mismatch:
        detail = (
            "config requires adjusted daily bars "
            "(market_data.require_adjusted_daily_bars=true) but the lake declares "
            "adjustment=raw — raw daily baselines silently corrupt RVOL / ATR / "
            "EMA / split-sensitive price gates"
        )
    return _check(
        name="adjustment_mismatch",
        status="fail" if mismatch else "pass",
        count=1 if mismatch else 0,
        threshold={"require_adjusted_daily_bars": bool(require_adjusted)},
        source_file=source_file,
        evidence={
            "lake_adjustment": str(lake_adjustment),
            "require_adjusted_daily_bars": bool(require_adjusted),
            **({"detail": detail} if detail else {}),
        },
    )


def build_split_adjustment_check(
    *,
    require_split_adjustment: bool,
    split_adjustment_applied: Optional[bool],
    lake_adjustment: str,
    source_file: str,
) -> dict[str, Any]:
    """Check the lake's split-adjustment state against ``require_split_adjustment``.

    Realism remediation 2 Phase 1 (audit §P0-005). A config that requires
    split-adjusted daily bars produces ``split_adjustment_mismatch: fail`` (a
    required, adjustment-gating check) when the lake has NOT applied split
    adjustments. The lake's split-adjustment state is read from the manifest's
    ``split_adjustment_applied`` flag; when that flag is absent it is inferred
    from the adjustment policy (``split_adjusted`` / ``adjusted`` -> applied,
    ``raw`` -> not applied). If the config does not require split adjustment the
    check is informational (``pass``).
    """
    require = bool(require_split_adjustment)
    if split_adjustment_applied is None:
        # Infer from the adjustment policy when the manifest omits the flag.
        applied = str(lake_adjustment) in ("split_adjusted", "adjusted")
        applied_source = f"inferred from adjustment={lake_adjustment!r}"
    else:
        applied = bool(split_adjustment_applied)
        applied_source = "manifest.split_adjustment_applied"
    mismatch = require and not applied
    detail = None
    if mismatch:
        detail = (
            "config requires split-adjusted daily bars "
            "(market_data.require_split_adjustment=true) but the lake has not "
            "applied split adjustments — splits / reverse-splits in microcaps "
            "produce invalid price / ATR / gap / RVOL features"
        )
    return _check(
        name="split_adjustment_mismatch",
        status="fail" if mismatch else "pass",
        count=1 if mismatch else 0,
        threshold={"require_split_adjustment": require},
        source_file=source_file,
        evidence={
            "lake_adjustment": str(lake_adjustment),
            "require_split_adjustment": require,
            "split_adjustment_applied": applied,
            "split_adjustment_applied_source": applied_source,
            **({"detail": detail} if detail else {}),
        },
    )


# --------------------------------------------------------------------------
# Quote coverage (Phase 2 stub)
# --------------------------------------------------------------------------
def build_quote_check(
    *,
    quotes_available: bool,
    quote_fallback_policy: str,
    source_file: str,
) -> list[dict[str, Any]]:
    """Quote-coverage checks (Phase 6 wires the real quote supplier).

    Emits ``quotes_partitions_available`` (informational) and, when
    ``quote_fallback_policy == "require_real"`` and no ``quotes/`` tree exists,
    ``quotes_required_but_absent: fail`` — a required check that fails a realism
    run whose config demands real quotes the lake cannot supply.
    """
    available_check = _check(
        name="quotes_partitions_available",
        status="pass" if quotes_available else "warn",
        count=0 if quotes_available else 1,
        threshold=None,
        source_file=source_file,
        evidence={"quotes_partitions_available": bool(quotes_available)},
    )
    require_real = str(quote_fallback_policy) == "require_real"
    if require_real and not quotes_available:
        required_check = _check(
            name="quotes_required_but_absent",
            status="fail",
            count=1,
            threshold={"quote_fallback_policy": "require_real"},
            source_file=source_file,
            evidence={
                "quote_fallback_policy": str(quote_fallback_policy),
                "quotes_partitions_available": False,
                "detail": (
                    "config requires real quotes (quote_fallback_policy=require_real) "
                    "but the lake has no quotes/ partitions"
                ),
            },
        )
        return [available_check, required_check]
    return [available_check]


# --------------------------------------------------------------------------
# Quote coverage (Phase 6 — finalize-step gate)
# --------------------------------------------------------------------------
def historical_quote_coverage_pct(quote_coverage_rows: Iterable[Mapping[str, Any]]) -> float:
    """Percentage of (symbol, scan_ts) rows backed by a *historical* quote.

    ``quote_coverage_rows`` is the per-candidate coverage list the backtester
    accumulates — each row has ``quote_present: bool``. Returns ``100.0`` when
    there are no rows (no candidates to cover is not a coverage failure here;
    that degenerate case is caught by the separate ``coverage_missing`` check).
    """
    rows = list(quote_coverage_rows)
    if not rows:
        return 100.0
    present = sum(1 for r in rows if r.get("quote_present"))
    return 100.0 * present / len(rows)


def build_quote_coverage_check(
    *,
    quote_coverage_rows: Iterable[Mapping[str, Any]],
    min_quote_coverage_pct: float,
    simulation_mode: str,
    source_file: str = "(per-run quote-coverage probe)",
) -> dict[str, Any]:
    """Finalize-step quote-coverage check (Phase 6 Task 7).

    Marks ``quote_coverage`` ``fail`` when, in ``intended_realism`` mode, the
    fraction of (symbol, scan_ts) pairs backed by a historical quote is below
    ``min_quote_coverage_pct``. In other modes the check is informational
    (``pass``) — it still records the measured coverage.
    """
    rows = list(quote_coverage_rows)
    coverage = historical_quote_coverage_pct(rows)
    n_present = sum(1 for r in rows if r.get("quote_present"))
    is_realism = str(simulation_mode) == "intended_realism"
    below = coverage < float(min_quote_coverage_pct)
    if is_realism and below:
        status = "fail"
    elif below and rows:
        status = "warn"
    else:
        status = "pass"
    evidence: dict[str, Any] = {
        "historical_quote_coverage_pct": round(coverage, 4),
        "candidates_with_quote": n_present,
        "candidates_total": len(rows),
        "min_quote_coverage_pct": float(min_quote_coverage_pct),
    }
    if is_realism and below:
        evidence["detail"] = (
            f"historical quote coverage {coverage:.2f}% is below the required "
            f"{float(min_quote_coverage_pct):.2f}% — the lake has insufficient "
            f"historical quotes for an intended_realism run"
        )
    return _check(
        name="quote_coverage",
        status=status,
        count=len(rows) - n_present,
        threshold={"min_quote_coverage_pct": float(min_quote_coverage_pct)},
        source_file=source_file,
        evidence=evidence,
    )


# --------------------------------------------------------------------------
# SIP data availability (realism remediation 2 Phase 10, audit §11 Phase 9)
# --------------------------------------------------------------------------
def build_sip_data_check(
    *,
    feed: str,
    sip_partitions_present: Optional[bool],
    source_file: str = "(lake SIP partition probe)",
) -> dict[str, Any]:
    """Probe SIP-partition presence for ``feed: sip`` configs.

    Realism remediation 2 Phase 10 (audit §11 Phase 9). The SIP ingestion
    stage has not run yet, so a ``feed: sip`` config against the current lake
    must fail closed in ``intended_realism`` mode rather than silently
    degrading. ``feed: iex`` runs never invoke this check.

    Emits:

    - ``sip_data_present: pass`` when the lake carries SIP partitions, or the
      feed is not SIP (the check is non-applicable);
    - ``sip_data_absent: fail`` (a required check) when ``feed: sip`` and no
      SIP partitions exist. The check is keyed under
      ``sip_data_absent`` so it appears in ``_REQUIRED_CHECK_NAMES`` and
      fails an ``intended_realism`` run closed.

    ``sip_partitions_present`` may be ``None`` (the lake-root probe failed);
    in that case the check is recorded as ``warn`` rather than fail — DQ
    should never crash because of an environment issue with the lake.
    """
    if str(feed or "").lower() != "sip":
        return _check(
            name="sip_data_present",
            status="pass",
            count=0,
            threshold=None,
            source_file=source_file,
            evidence={"feed": feed, "detail": "non-SIP feed; SIP probe not applicable"},
        )
    if sip_partitions_present is None:
        return _check(
            name="sip_data_present",
            status="warn",
            count=0,
            threshold=None,
            source_file=source_file,
            evidence={
                "feed": feed,
                "detail": (
                    "could not probe SIP partition presence (lake root not provided "
                    "or probe failed) — gate skipped"
                ),
            },
        )
    if sip_partitions_present:
        return _check(
            name="sip_data_present",
            status="pass",
            count=0,
            threshold=None,
            source_file=source_file,
            evidence={"feed": feed, "sip_partitions_present": True},
        )
    return _check(
        name="sip_data_absent",
        status="fail",
        count=1,
        threshold={"feed": "sip"},
        source_file=source_file,
        evidence={
            "feed": feed,
            "sip_partitions_present": False,
            "detail": (
                "market_data.feed='sip' but the lake has no SIP partitions "
                "(bars/quotes). The SIP ingestion stage has not run; ingest "
                "the SIP feed or use feed='iex' (research-only). See "
                "docs/data_lake_layout.md."
            ),
            "remediation_pointer": "docs/data_lake_layout.md",
        },
    )


# --------------------------------------------------------------------------
# Synthetic regime
# --------------------------------------------------------------------------
def synthetic_data_quality_report(*, feed: str, note: str = "") -> dict[str, Any]:
    """A non-empty, clearly-labelled DQ report for runs with no lake audit.

    Used by smoke / fixture runs and direct ``run_backtest`` calls with
    synthetic suppliers. The single ``synthetic_data`` check is ``warn`` so the
    report is never empty and never silently passes as research-grade.
    """
    checks = [
        _check(
            name="synthetic_data",
            status="warn",
            count=0,
            threshold=None,
            source_file="(synthetic — no lake audit)",
            evidence={
                "detail": (
                    "run used synthetic / fixture market data; no lake "
                    "research-audit available. Not a research-grade dataset."
                )
            },
        )
    ]
    return assemble_report(checks=checks, regime="synthetic", feed=feed, notes=note)


# --------------------------------------------------------------------------
# Assembly + gating
# --------------------------------------------------------------------------
def assemble_report(
    *,
    checks: list[dict[str, Any]],
    regime: str,
    feed: str,
    notes: str = "",
) -> dict[str, Any]:
    """Assemble the ``data_quality_report.json`` document from a list of checks."""
    passed = sum(1 for c in checks if c["status"] == "pass")
    failed = sum(1 for c in checks if c["status"] == "fail")
    warned = sum(1 for c in checks if c["status"] == "warn")

    per_symbol_failures: dict[str, list[str]] = {}
    for c in checks:
        if c["status"] != "fail":
            continue
        per_symbol = (c.get("evidence") or {}).get("per_symbol") or {}
        for sym in per_symbol:
            per_symbol_failures.setdefault(str(sym), []).append(c["name"])
        failed_symbols = (c.get("evidence") or {}).get("failed_symbols") or []
        for sym in failed_symbols:
            per_symbol_failures.setdefault(str(sym), []).append(c["name"])

    required_failures = [
        c["name"]
        for c in checks
        if c["status"] == "fail" and c["name"] in _REQUIRED_CHECK_NAMES
    ]
    # Adjustment-enforcement failures gate ANY non-smoke run (audit §P0-005);
    # the rest of required_failures gate only intended_realism.
    adjustment_gating_failures = [
        c["name"]
        for c in checks
        if c["status"] == "fail" and c["name"] in _ADJUSTMENT_GATING_CHECK_NAMES
    ]
    return {
        "schema_version": DATA_QUALITY_SCHEMA_VERSION,
        "regime": regime,
        "feed": feed,
        "passed": passed,
        "failed": failed,
        "warned": warned,
        "checks": checks,
        "per_symbol_failures": {k: sorted(set(v)) for k, v in sorted(per_symbol_failures.items())},
        "required_failures": sorted(set(required_failures)),
        "adjustment_gating_failures": sorted(set(adjustment_gating_failures)),
        "notes": notes,
    }


def evaluate_startup_dq(report: Mapping[str, Any], *, simulation_mode: str) -> Optional[str]:
    """Decide whether a run must fail closed on data quality.

    Returns ``None`` when the run may proceed, or a human-readable rejection
    reason string when it must not. The gate is mode-tiered:

    - ``intended_realism`` — gated on EVERY required check (audit / coverage /
      adjustment / quote).
    - ``current_code_parity`` — gated ONLY on the adjustment-enforcement checks
      (``adjustment_mismatch`` / ``split_adjustment_mismatch``): a parity run
      against a raw lake whose config requires adjusted daily bars must still
      fail closed (audit §P0-005). Other DQ failures are tolerated — parity mode
      reproduces the live code warts and all.
    - ``smoke_fixture`` — never gated by data quality.

    See :data:`_ADJUSTMENT_GATING_CHECK_NAMES`.
    """
    if simulation_mode == "smoke_fixture":
        return None
    if simulation_mode == "intended_realism":
        gating_failures = list(report.get("required_failures") or [])
    elif simulation_mode == "current_code_parity":
        gating_failures = list(report.get("adjustment_gating_failures") or [])
    else:
        # Unknown mode — fail closed on the adjustment-enforcement checks only,
        # which is the most conservative interpretation that still runs.
        gating_failures = list(report.get("adjustment_gating_failures") or [])
    if not gating_failures:
        return None
    # Compose a precise reason from each failing gating check.
    by_name = {c["name"]: c for c in report.get("checks", [])}
    details: list[str] = []
    for name in gating_failures:
        c = by_name.get(name, {})
        evidence = c.get("evidence") or {}
        detail = evidence.get("detail")
        if detail:
            details.append(f"{name}: {detail}")
        else:
            details.append(f"{name}: count={c.get('count')}")
    return (
        f"{simulation_mode} run aborted: {len(gating_failures)} required "
        f"data-quality check(s) failed: " + "; ".join(details)
    )


def build_data_quality_report(
    *,
    cfg: Mapping[str, Any],
    lineage: Mapping[str, Any],
    requested_symbols: Iterable[str],
    sessions: Iterable[_dt.date],
    daily_bars_supplier,
    minute_bars_supplier,
    scan_times_per_session,
    daily_cache_by_session: Optional[Mapping[_dt.date, Any]] = None,
    session_minute_supplier=None,
    classify_filter: Optional[str] = None,
) -> dict[str, Any]:
    """Build the full ``data_quality_report.json`` document for a run.

    ``lineage`` is the dict returned by :func:`bowaka_v2_lab.data.lineage.build_dataset_lineage`.
    Lake-backed runs get audit + coverage + adjustment + quote checks plus the
    five multi-level DQ check sets (realism remediation 2 Phase 3, audit
    §P0-010); synthetic runs get the labelled :func:`synthetic_data_quality_report`.

    ``daily_cache_by_session`` (the per-session daily-feature cache) drives the
    feature-leakage check; ``session_minute_supplier(symbol, session)`` (the
    full regular-session minute frame) drives the session-level checks. Both are
    optional — when absent the dependent levels degrade to a clean ``pass``
    rather than failing.

    Speedup report v2 §4 P4 / §5.6 / Phase 3 task 3 — when
    ``classify_filter="invariant"`` only checks classified
    :data:`_DQ_CHECK_INVARIANCE` invariant are emitted; with
    ``classify_filter="trial_dependent"`` only the trial-dependent checks. The
    default ``None`` runs every check (legacy behaviour).
    """
    feed = str((cfg.get("market_data", {}) or {}).get("feed", "iex"))
    regime = str(lineage.get("regime", "synthetic"))
    md = cfg.get("market_data", {}) or {}
    sim = cfg.get("simulation", {}) or {}

    if regime != "lake":
        return synthetic_data_quality_report(
            feed=feed, note="synthetic / fixture run — DQ gating not applicable"
        )

    from .lineage import quotes_partitions_available

    lake_root = Path(lineage["lake_root"]) if lineage.get("lake_root") else None
    symbols = [str(s) for s in requested_symbols]
    checks: list[dict[str, Any]] = []

    # --- audit-derived checks ---
    audit_path = find_latest_audit(lake_root, feed=feed) if lake_root is not None else None
    audit_checks = build_audit_checks(
        audit_path, feed=feed, requested_symbols=symbols
    )
    if audit_checks:
        checks.extend(audit_checks)
    else:
        checks.append(
            _check(
                name="audit_available",
                status="warn",
                count=0,
                threshold=None,
                source_file=str(audit_path) if audit_path else "(no audit found)",
                evidence={
                    "detail": (
                        "no lake research-audit parquet matched this run's feed / "
                        "symbol universe; audit-derived checks were skipped"
                    )
                },
            )
        )

    # --- per-run coverage ---
    checks.append(
        build_coverage_check(
            requested_symbols=symbols,
            sessions=sessions,
            daily_bars_supplier=daily_bars_supplier,
            minute_bars_supplier=minute_bars_supplier,
            scan_times_per_session=scan_times_per_session,
        )
    )

    # --- adjustment / corporate actions ---
    from .lineage import lake_split_adjustment_applied

    require_adjusted = bool(md.get("require_adjusted_daily_bars", False))
    require_split = bool(md.get("require_split_adjustment", False))
    lake_adjustment_policy = str(lineage.get("adjustment", "raw"))
    manifest_source = (
        _layout.ingestion_manifest_path(lake_root).name
        if lake_root is not None
        else "(lake manifest)"
    )
    checks.append(
        build_adjustment_check(
            require_adjusted=require_adjusted,
            lake_adjustment=lake_adjustment_policy,
            source_file=manifest_source,
        )
    )
    checks.append(
        build_split_adjustment_check(
            require_split_adjustment=require_split,
            split_adjustment_applied=lake_split_adjustment_applied(
                lineage.get("lake_manifest")
            ),
            lake_adjustment=lake_adjustment_policy,
            source_file=manifest_source,
        )
    )

    # --- quote coverage (Phase 2 stub) ---
    quotes_ok = quotes_partitions_available(lake_root) if lake_root is not None else False
    # quote_fallback_policy is resolved from simulation.mode by SimulationConfig;
    # read the resolved value if present, else fall back to the raw config value.
    quote_policy = sim.get("quote_fallback_policy")
    checks.extend(
        build_quote_check(
            quotes_available=quotes_ok,
            quote_fallback_policy=str(quote_policy) if quote_policy else "",
            source_file="(lake quotes/ probe)",
        )
    )

    # --- SIP partition presence (realism remediation 2 Phase 10, audit §11 Phase 9) ---
    # When the config asks for SIP, refuse a SIP-less lake. The check emits
    # ``sip_data_present: pass`` for non-SIP feeds (no IEX regression) and
    # ``sip_data_absent: fail`` (a required check) for ``feed: sip`` against a
    # lake whose SIP ingestion has not run.
    sip_partitions_present: Optional[bool] = None
    if lake_root is not None and str(feed).lower() == "sip":
        try:
            from bowaka_common.marketdata.layout import sip_partitions_available

            sip_partitions_present = sip_partitions_available(lake_root)
        except Exception:  # noqa: BLE001 — probe failure leaves the check as a warn
            sip_partitions_present = None
    checks.append(
        build_sip_data_check(
            feed=feed,
            sip_partitions_present=sip_partitions_present,
        )
    )

    # --- multi-level DQ checks (realism remediation 2 Phase 3, audit §P0-010) ---
    checks.extend(
        _build_multi_level_checks(
            cfg=cfg,
            lineage=lineage,
            requested_symbols=symbols,
            sessions=list(sessions),
            daily_bars_supplier=daily_bars_supplier,
            minute_bars_supplier=minute_bars_supplier,
            session_minute_supplier=session_minute_supplier,
            scan_times_per_session=scan_times_per_session,
            daily_cache_by_session=daily_cache_by_session,
            lake_root=lake_root,
            lake_adjustment_policy=lake_adjustment_policy,
        )
    )

    # Speedup report v2 §4 P4 / §5.6 / Phase 3 — invariance filter.
    if classify_filter is not None:
        if classify_filter not in ("invariant", "trial_dependent"):
            raise ValueError(
                "classify_filter must be 'invariant', 'trial_dependent', or "
                f"None; got {classify_filter!r}"
            )
        checks = [
            c for c in checks
            if dq_check_invariance(c.get("name", "")) == classify_filter
        ]

    return assemble_report(checks=checks, regime="lake", feed=feed, notes="")


def _build_multi_level_checks(
    *,
    cfg: Mapping[str, Any],
    lineage: Mapping[str, Any],
    requested_symbols: list[str],
    sessions: list[_dt.date],
    daily_bars_supplier,
    minute_bars_supplier,
    session_minute_supplier,
    scan_times_per_session,
    daily_cache_by_session: Optional[Mapping[_dt.date, Any]],
    lake_root: Optional[Path],
    lake_adjustment_policy: str,
) -> list[dict[str, Any]]:
    """Append the five multi-level DQ check sets to a lake-backed run.

    Ingestion / session / replay / feature / quote-status. Never raises — a
    supplier or calendar error inside any level is contained so the rest of the
    report is still produced.
    """
    from .dq_levels import (
        build_feature_checks,
        build_ingestion_checks,
        build_quote_status_checks,
        build_replay_checks,
        build_session_checks,
        status_partitions_available,
    )

    md = cfg.get("market_data", {}) or {}
    sim = cfg.get("simulation", {}) or {}
    exits = cfg.get("exits", {}) or {}
    execution = cfg.get("execution", {}) or {}
    sim_mode = str(sim.get("mode", "intended_realism"))
    out: list[dict[str, Any]] = []

    # --- Level 1: ingestion — over each symbol's daily bars ---
    daily_frames: dict[str, pd.DataFrame] = {}
    for sym in requested_symbols:
        frames: list[pd.DataFrame] = []
        for session in sessions:
            try:
                d = daily_bars_supplier(sym, session)
            except Exception:  # noqa: BLE001
                d = None
            if d is not None and len(d) > 0:
                frames.append(d)
        if frames:
            try:
                daily_frames[sym] = pd.concat(frames, ignore_index=True).drop_duplicates(
                    subset=["timestamp"] if "timestamp" in frames[0].columns else None
                )
            except Exception:  # noqa: BLE001
                daily_frames[sym] = frames[0]
    try:
        out.extend(build_ingestion_checks(bar_frames=daily_frames))
    except Exception as exc:  # noqa: BLE001 — a level error must not lose the report
        out.append(
            _check("ingestion_level_error", "warn", 1, None,
                   "(ingestion-level probe)", {"detail": f"ingestion checks skipped: {exc}"})
        )

    # --- Level 2: session — over per-(symbol, session) minute frames ---
    minute_frames: dict[tuple[str, _dt.date], pd.DataFrame] = {}
    for session in sessions:
        for sym in requested_symbols:
            frame = None
            if session_minute_supplier is not None:
                try:
                    frame = session_minute_supplier(sym, session)
                except Exception:  # noqa: BLE001
                    frame = None
            if frame is None or len(frame) == 0:
                # Fall back to probing the minute supplier at the session close.
                try:
                    probe_ts = pd.Timestamp(session, tz="America/New_York") + pd.Timedelta(
                        hours=16
                    )
                    frame = minute_bars_supplier(sym, probe_ts.tz_convert("UTC"))
                except Exception:  # noqa: BLE001
                    frame = None
            if frame is not None and len(frame) > 0:
                minute_frames[(sym, session)] = frame
    try:
        out.extend(build_session_checks(minute_frames_by_session=minute_frames))
    except Exception as exc:  # noqa: BLE001
        out.append(
            _check("session_level_error", "warn", 1, None,
                   "(session-level probe)", {"detail": f"session checks skipped: {exc}"})
        )

    # --- Level 3: replay — late-session + exit-path coverage ---
    max_hold_days = int(exits.get("max_hold_days", 3) or 3)
    max_quote_age = float(
        md.get("max_quote_age_seconds", execution.get("max_quote_age_seconds", 15)) or 15
    )
    try:
        out.extend(
            build_replay_checks(
                requested_symbols=requested_symbols,
                sessions=sessions,
                minute_bars_supplier=minute_bars_supplier,
                scan_times_per_session=scan_times_per_session,
                max_hold_days=max_hold_days,
                quote_coverage_rows=None,
                max_quote_age_seconds=max_quote_age,
            )
        )
    except Exception as exc:  # noqa: BLE001
        out.append(
            _check("replay_level_error", "warn", 1, None,
                   "(replay-level probe)", {"detail": f"replay checks skipped: {exc}"})
        )

    # --- Level 4: feature — leakage + split-awareness ---
    from .lineage import quotes_partitions_available as _quotes_avail  # noqa: F401

    corp_actions_available = False
    if lake_root is not None:
        ca_root = lake_root / _layout.DS_CORPORATE_ACTIONS
        corp_actions_available = ca_root.is_dir() and any(ca_root.rglob("*.parquet"))
    try:
        out.extend(
            build_feature_checks(
                daily_cache_by_session=daily_cache_by_session or {},
                require_adjusted_daily_bars=bool(md.get("require_adjusted_daily_bars", False)),
                lake_adjustment=lake_adjustment_policy,
                corporate_actions_available=corp_actions_available,
            )
        )
    except Exception as exc:  # noqa: BLE001
        out.append(
            _check("feature_level_error", "warn", 1, None,
                   "(feature-level probe)", {"detail": f"feature checks skipped: {exc}"})
        )

    # --- Level 5: quote / status — distributions + halt gate ---
    statuses_ok = status_partitions_available(lake_root)
    halt_gate_enabled = bool((execution.get("halt_gate") or {}).get("enabled", True))
    try:
        out.extend(
            build_quote_status_checks(
                quote_coverage_rows=None,
                status_partitions_available=statuses_ok,
                halt_gate_enabled=halt_gate_enabled,
                simulation_mode=sim_mode,
            )
        )
    except Exception as exc:  # noqa: BLE001
        out.append(
            _check("quote_status_level_error", "warn", 1, None,
                   "(quote/status-level probe)", {"detail": f"quote/status checks skipped: {exc}"})
        )

    return out


__all__ = [
    "DATA_QUALITY_SCHEMA_VERSION",
    "DQ_CHECK_INVARIANCE_VERSION",
    "build_data_quality_report",
    "build_audit_checks",
    "build_coverage_check",
    "build_adjustment_check",
    "build_split_adjustment_check",
    "build_quote_check",
    "build_quote_coverage_check",
    "build_sip_data_check",
    "dq_check_invariance",
    "merge_dq_reports",
    "historical_quote_coverage_pct",
    "find_latest_audit",
    "synthetic_data_quality_report",
    "assemble_report",
    "evaluate_startup_dq",
    "_REQUIRED_CHECK_NAMES",
]
