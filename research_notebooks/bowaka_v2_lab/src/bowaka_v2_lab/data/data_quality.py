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
    }
)

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
) -> dict[str, Any]:
    """Build the full ``data_quality_report.json`` document for a run.

    ``lineage`` is the dict returned by :func:`bowaka_v2_lab.data.lineage.build_dataset_lineage`.
    Lake-backed runs get audit + coverage + adjustment + quote checks; synthetic
    runs get the labelled :func:`synthetic_data_quality_report`.
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

    return assemble_report(checks=checks, regime="lake", feed=feed, notes="")


__all__ = [
    "DATA_QUALITY_SCHEMA_VERSION",
    "build_data_quality_report",
    "build_audit_checks",
    "build_coverage_check",
    "build_adjustment_check",
    "build_split_adjustment_check",
    "build_quote_check",
    "build_quote_coverage_check",
    "historical_quote_coverage_pct",
    "find_latest_audit",
    "synthetic_data_quality_report",
    "assemble_report",
    "evaluate_startup_dq",
]
