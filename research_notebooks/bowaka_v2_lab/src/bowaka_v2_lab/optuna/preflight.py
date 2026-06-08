"""Optuna study-start preflight checks (realism remediation Phase 9).

A walk-forward study is ``n_trials x n_folds`` real backtests — a multi-hour
job. Running it against a dataset that cannot support a research-grade objective
wastes that compute and, worse, produces a confidently-wrong "best" config.

:func:`run_preflight` is called once at study start (before any trial). It
REFUSES the study — raising :class:`PreflightError` — when:

1. ``simulation.mode == smoke_fixture`` and ``allow_smoke`` is not set
   (deterministic synthetic data is not a research objective);
2. the run is ``intended_realism`` and the dataset's data-quality report has a
   failing *required* check;
3. the run is ``intended_realism`` and historical quote coverage is below the
   configured threshold;
4. ``market_data.feed == "sip"`` and the lake has no SIP partitions (realism
   remediation 2 Phase 10 / audit §11 Phase 9).

Checks 2 and 3 gate **only ``intended_realism``** runs — mirroring the
data-quality contract (``data_quality.py``: "Only ``intended_realism`` runs are
gated; ``smoke_fixture`` and ``current_code_parity`` runs surface the same
report but are never failed by it"). For a ``current_code_parity`` study a
failing required DQ check or low quote coverage is recorded as a ``warn`` — it
is surfaced in the study metadata but does not refuse the run, because parity
mode reproduces the live code (which uses the zero-spread quote fallback).

Check 4 fires only for ``feed: sip``; an ``feed: iex`` run never inspects SIP
partitions, so there is no regression for the IEX path. It gates
``intended_realism`` (fail closed) and surfaces a warning on
``current_code_parity`` — parity mode against a SIP feed is a paper-recon
plumbing setup; SIP-less SIP partitions are still a defect there but not a
hard refusal.

The checks are skipped (with a recorded ``skipped`` status) when they cannot
apply — e.g. quote coverage is not meaningful for a ``smoke_fixture`` run that
was explicitly allowed via ``allow_smoke``.
"""
from __future__ import annotations

import datetime as _dt
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from bowaka_common.marketdata.store import (
    resolve_market_data_root as _resolve_market_data_root,
)


def _coerce_lake_root(lake_root: Any) -> Path:
    """Hotfix 2026-05-29 — defensive lake-root resolution.

    ``Path(str(None))`` becomes the literal directory ``None`` on disk and makes
    the partition gates false-positive. Always resolve via the standard chain
    (explicit > ``$MARKET_DATA_ROOT`` > in-repo default) so a ``None`` / empty /
    whitespace upstream value can never reach a glob / ``is_dir`` consumer.
    ``resolve_market_data_root`` treats a blank string as unset.
    """
    return _resolve_market_data_root(lake_root, create=False)


#: Pointer to the canonical data-lake layout doc; surfaced in every SIP-data
#: refusal so the operator knows exactly which partitions are missing.
_DATA_LAKE_LAYOUT_DOC = "docs/data_lake_layout.md"


class PreflightError(RuntimeError):
    """Raised when a study fails a study-start prerequisite and must not run."""


@dataclass
class PreflightCheck:
    name: str
    status: str  # "pass" | "fail" | "warn" | "skipped"
    detail: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class PreflightResult:
    passed: bool
    checks: list[PreflightCheck]
    #: Audit 2026-05-29 §5.4 / Phase 1 — non-blocking IEX/current_code_parity
    #: partial-tape limitations (e.g. ``missing_historical_quotes``,
    #: ``missing_sip``). Recorded in the run manifest so a reviewer can never
    #: mistake an IEX parity run for a SIP-grade run. Empty for intended_realism
    #: (where the same gaps are hard fails).
    iex_partial_tape_limitations: list[str] = field(default_factory=list)

    @property
    def failures(self) -> list[PreflightCheck]:
        return [c for c in self.checks if c.status == "fail"]

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": [
                {"name": c.name, "status": c.status, "detail": c.detail,
                 "evidence": c.evidence}
                for c in self.checks
            ],
            "iex_partial_tape_limitations": list(self.iex_partial_tape_limitations),
        }


#: Below this fraction (percent) of (symbol, scan_ts) quote coverage a study is
#: refused. Mirrors ``SimulationConfig.min_quote_coverage_pct`` but is read from
#: the config so a study can lower it for an explicitly-degraded research run.
DEFAULT_MIN_QUOTE_COVERAGE_PCT = 95.0

#: Audit 2026-05-29 §5.4 / Phase 1 — a fold whose point-in-time universe
#: resolves to fewer than this many eligible symbols cannot produce a
#: statistically meaningful objective; the full-fold preflight refuses it.
#: Overridable via ``cfg["preflight"]["min_pit_universe_per_fold"]``.
DEFAULT_MIN_PIT_UNIVERSE_PER_FOLD = 25


def _check_smoke(sim_mode: str, allow_smoke: bool) -> PreflightCheck:
    """The smoke-mode gate: refuse ``smoke_fixture`` unless explicitly allowed."""
    if sim_mode != "smoke_fixture":
        return PreflightCheck(
            name="simulation_mode",
            status="pass",
            detail=f"simulation.mode={sim_mode!r} is a research mode",
            evidence={"simulation_mode": sim_mode},
        )
    if allow_smoke:
        return PreflightCheck(
            name="simulation_mode",
            status="pass",
            detail=(
                "simulation.mode is 'smoke_fixture' but --allow-smoke-optimization "
                "was passed; the study is permitted (NOT research-grade)"
            ),
            evidence={"simulation_mode": sim_mode, "allow_smoke": True},
        )
    return PreflightCheck(
        name="simulation_mode",
        status="fail",
        detail=(
            "simulation.mode is 'smoke_fixture' — optimizing against deterministic "
            "synthetic data produces a meaningless objective. Use a research config "
            "(intended_realism / current_code_parity) or pass "
            "--allow-smoke-optimization."
        ),
        evidence={"simulation_mode": sim_mode, "allow_smoke": False},
    )


def _check_data_quality(
    dq_report: Optional[Mapping[str, Any]],
    *,
    sim_mode: str,
    allow_smoke: bool,
) -> PreflightCheck:
    """Refuse the study when the dataset's DQ report has a failing required check.

    Audit 2026-05-23 §P0-003 — fail closed under ``intended_realism`` when the
    DQ report is missing: a research-grade study cannot run without a DQ
    report. ``current_code_parity`` and ``smoke_fixture`` retain the previous
    ``skipped`` semantics (parity / smoke runs surface the absence as a
    warning, not a refusal).
    """
    if dq_report is None:
        if sim_mode == "intended_realism":
            return PreflightCheck(
                name="data_quality",
                status="fail",
                detail=(
                    "intended_realism requires a data-quality report; none was "
                    "supplied to preflight. See docs/audits/2026-05-23_realism_audit.md "
                    "§P0-003."
                ),
                evidence={"simulation_mode": sim_mode},
            )
        return PreflightCheck(
            name="data_quality",
            status="skipped",
            detail="no data-quality report was supplied to preflight",
            evidence={},
        )
    regime = str(dq_report.get("regime", "unknown"))
    required_failures = list(dq_report.get("required_failures") or [])
    failed = int(dq_report.get("failed", 0) or 0)
    # A ``smoke_fixture`` run explicitly allowed via --allow-smoke-optimization
    # is, by construction, NOT a research-grade run — DQ gating does not apply
    # (the run is plumbing-only). The check is recorded as skipped, not failed,
    # so the smoke override clears every realism prerequisite. The same holds
    # for any synthetic-regime dataset under an explicit smoke override.
    if allow_smoke and (sim_mode == "smoke_fixture" or regime != "lake"):
        return PreflightCheck(
            name="data_quality",
            status="skipped",
            detail=(
                f"simulation.mode={sim_mode!r}, regime={regime!r} and smoke "
                f"optimization was explicitly allowed; DQ gating not applicable"
            ),
            evidence={"regime": regime, "simulation_mode": sim_mode},
        )
    adjustment_gating_failures = list(dq_report.get("adjustment_gating_failures") or [])
    if required_failures or adjustment_gating_failures:
        evidence = {
            "regime": regime,
            "failed": failed,
            "required_failures": sorted(required_failures),
            "adjustment_gating_failures": sorted(adjustment_gating_failures),
        }
        # Speedup report §4 P0-A / §5.1: the unified gate uses ``evaluate_startup_dq``
        # — the same predicate ``run_backtest`` consults — so a parity study
        # against a raw lake whose config requires adjusted daily bars fails the
        # preflight closed (the prior code silently surfaced this as a ``warn``
        # for ``current_code_parity``). ``evaluate_startup_dq`` returns ``None``
        # for any mode/check combination that does NOT gate; only those that
        # gate produce a non-None reason here, and we mark them as ``fail``.
        # Non-gating failures (e.g. non-adjustment required failures under
        # ``current_code_parity``) still surface as a ``warn`` so the historical
        # "report it, run it" parity behaviour is preserved for them.
        from ..data.data_quality import evaluate_startup_dq

        startup_dq_reason = evaluate_startup_dq(dq_report, simulation_mode=sim_mode)
        if startup_dq_reason is not None:
            return PreflightCheck(
                name="data_quality",
                status="fail",
                detail=startup_dq_reason,
                evidence=evidence,
            )
        return PreflightCheck(
            name="data_quality",
            status="warn",
            detail=(
                f"simulation.mode={sim_mode!r} is not data-quality-gated; the report "
                f"has {len(required_failures)} failing required check(s): "
                f"{sorted(required_failures)} — surfaced as a warning, study permitted"
            ),
            evidence=evidence,
        )
    return PreflightCheck(
        name="data_quality",
        status="pass",
        detail=(
            f"data-quality report has no failing required checks "
            f"(regime={regime!r}, failed={failed})"
        ),
        evidence={"regime": regime, "failed": failed},
    )


def _check_quote_coverage(
    quote_coverage_pct: Optional[float],
    *,
    min_quote_coverage_pct: float,
    sim_mode: str,
    allow_smoke: bool,
) -> PreflightCheck:
    """Refuse the study when measured/declared quote coverage is below threshold."""
    # Quote coverage is not meaningful for an explicitly-allowed smoke run.
    if sim_mode == "smoke_fixture" and allow_smoke:
        return PreflightCheck(
            name="quote_coverage",
            status="skipped",
            detail=(
                "simulation.mode is 'smoke_fixture' with --allow-smoke-optimization; "
                "quote-coverage gating not applicable"
            ),
            evidence={},
        )
    if quote_coverage_pct is None:
        # Audit 2026-05-23 §P0-003 — intended_realism requires a measured
        # historical-quote coverage; a missing probe must fail closed (the
        # downstream realism simulator would otherwise silently fall back to
        # the zero-spread quote model). Parity / smoke continue to skip.
        if sim_mode == "intended_realism":
            return PreflightCheck(
                name="quote_coverage",
                status="fail",
                detail=(
                    "intended_realism requires measured historical quote coverage; "
                    "probe returned None. See docs/audits/2026-05-23_realism_audit.md "
                    "§P0-003."
                ),
                evidence={
                    "simulation_mode": sim_mode,
                    "min_quote_coverage_pct": float(min_quote_coverage_pct),
                },
            )
        return PreflightCheck(
            name="quote_coverage",
            status="skipped",
            detail="no quote-coverage probe was supplied to preflight",
            evidence={"min_quote_coverage_pct": float(min_quote_coverage_pct)},
        )
    coverage = float(quote_coverage_pct)
    if coverage < float(min_quote_coverage_pct):
        evidence = {
            "historical_quote_coverage_pct": round(coverage, 4),
            "min_quote_coverage_pct": float(min_quote_coverage_pct),
        }
        # Only intended_realism requires real historical quotes; current_code_parity
        # uses the zero-spread quote fallback (the live code's own behavior), so low
        # coverage is a surfaced warning, not a refusal.
        if sim_mode == "intended_realism":
            return PreflightCheck(
                name="quote_coverage",
                status="fail",
                detail=(
                    f"historical quote coverage {coverage:.2f}% is below the required "
                    f"{float(min_quote_coverage_pct):.2f}% — the lake has insufficient "
                    f"historical quotes for a research-grade optimization"
                ),
                evidence=evidence,
            )
        return PreflightCheck(
            name="quote_coverage",
            status="warn",
            detail=(
                f"historical quote coverage {coverage:.2f}% is below "
                f"{float(min_quote_coverage_pct):.2f}%, but simulation.mode={sim_mode!r} "
                f"uses the quote fallback — surfaced as a warning, study permitted"
            ),
            evidence=evidence,
        )
    return PreflightCheck(
        name="quote_coverage",
        status="pass",
        detail=(
            f"historical quote coverage {coverage:.2f}% meets the "
            f"{float(min_quote_coverage_pct):.2f}% threshold"
        ),
        evidence={
            "historical_quote_coverage_pct": round(coverage, 4),
            "min_quote_coverage_pct": float(min_quote_coverage_pct),
        },
    )


def _check_sip_data(
    *,
    feed: Optional[str],
    sim_mode: str,
    lake_root: Optional[Path] = None,
    sip_partitions_present: Optional[bool] = None,
) -> PreflightCheck:
    """Refuse a ``feed: sip`` study when the lake has no SIP partitions.

    Realism remediation 2 Phase 10 (audit §11 Phase 9). When the config's
    ``market_data.feed`` is ``"sip"``, the lake must carry at least one SIP
    bars / quotes partition; otherwise the run silently degrades to whatever
    fall-back the data layer produces. The check is skipped (``pass``) for
    ``feed: iex`` and other non-SIP feeds — there is no regression for IEX.

    ``sip_partitions_present`` is the probed result (``True``/``False``);
    when ``None`` the check probes ``lake_root`` via
    :func:`bowaka_common.marketdata.layout.sip_partitions_available`. If
    neither is provided the check is ``skipped`` — the caller can still launch
    the study but the SIP-data gate did not run.
    """
    if str(feed or "").lower() != "sip":
        return PreflightCheck(
            name="sip_data_present",
            status="pass",
            detail=f"market_data.feed={feed!r} is not SIP — SIP-data gate not applicable",
            evidence={"feed": feed},
        )
    present = sip_partitions_present
    probe_exception: Optional[str] = None
    if present is None and lake_root is not None:
        try:
            from bowaka_common.marketdata.layout import sip_partitions_available

            present = sip_partitions_available(lake_root)
        except Exception as exc:  # noqa: BLE001 — probe failure handling depends on mode
            present = None
            probe_exception = str(exc)
    if present is None:
        # Audit 2026-05-23 §P0-003 — intended_realism cannot tolerate an
        # unknown SIP-partition state; the run silently degrades otherwise.
        # Parity / smoke continue to skip the check.
        if sim_mode == "intended_realism":
            return PreflightCheck(
                name="sip_data_present",
                status="fail",
                detail=(
                    "intended_realism requires a probed SIP-partition presence "
                    "but the probe could not be performed (supply lake_root or "
                    "sip_partitions_present). See "
                    "docs/audits/2026-05-23_realism_audit.md §P0-003."
                ),
                evidence={"feed": feed, "probe_exception": probe_exception,
                          "simulation_mode": sim_mode},
            )
        return PreflightCheck(
            name="sip_data_present",
            status="skipped",
            detail=(
                "could not probe SIP partition presence — supply lake_root or "
                "sip_partitions_present to the preflight, or check the lake by hand"
            ),
            evidence={"feed": feed, "probe_exception": probe_exception},
        )
    if present:
        return PreflightCheck(
            name="sip_data_present",
            status="pass",
            detail="lake carries SIP partitions for the requested feed",
            evidence={"feed": feed, "sip_partitions_present": True},
        )
    # SIP feed but the lake has no SIP data. The required ``intended_realism``
    # gate is hard-fail; ``current_code_parity`` surfaces a warning (the audit
    # §11 Phase 9 view: a parity SIP run is plumbing, not research, so the
    # missing SIP data is a defect but not yet a refusal).
    evidence = {
        "feed": feed,
        "sip_partitions_present": False,
        "lake_root": str(lake_root) if lake_root else None,
        "remediation_pointer": _DATA_LAKE_LAYOUT_DOC,
    }
    if sim_mode == "intended_realism":
        return PreflightCheck(
            name="sip_data_absent",
            status="fail",
            detail=(
                "market_data.feed='sip' but the lake has no SIP partitions — "
                "the SIP ingestion stage has not run. The intended-realism "
                "contract requires real SIP bars + SIP quotes; ingest the SIP "
                f"feed or use feed='iex' (research-only). See {_DATA_LAKE_LAYOUT_DOC}."
            ),
            evidence=evidence,
        )
    return PreflightCheck(
        name="sip_data_absent",
        status="warn",
        detail=(
            f"market_data.feed='sip' but the lake has no SIP partitions; "
            f"simulation.mode={sim_mode!r} surfaces this as a warning, not a refusal. "
            f"See {_DATA_LAKE_LAYOUT_DOC}."
        ),
        evidence=evidence,
    )


def run_preflight(
    *,
    sim_mode: str,
    allow_smoke: bool,
    dq_report: Optional[Mapping[str, Any]] = None,
    quote_coverage_pct: Optional[float] = None,
    min_quote_coverage_pct: float = DEFAULT_MIN_QUOTE_COVERAGE_PCT,
    feed: Optional[str] = None,
    lake_root: Optional[Path] = None,
    sip_partitions_present: Optional[bool] = None,
    raise_on_fail: bool = True,
) -> PreflightResult:
    """Run every study-start preflight check.

    ``dq_report`` is the dataset's ``data_quality_report.json`` document (or the
    output of :func:`bowaka_v2_lab.data.data_quality.build_data_quality_report`).
    ``quote_coverage_pct`` is the measured historical-quote coverage percentage,
    when known. Either may be ``None`` — the corresponding check is then
    ``skipped`` rather than failed.

    ``feed`` is the run's ``market_data.feed`` value; when set to ``"sip"`` the
    SIP-data gate runs (realism remediation 2 Phase 10 / audit §11 Phase 9).
    ``lake_root`` is the lake root used by the SIP probe; alternatively the
    caller can pass ``sip_partitions_present`` directly. Other feed values
    (``"iex"`` etc.) skip the gate — no regression for the IEX path.

    Raises :class:`PreflightError` (when ``raise_on_fail``) if any check fails.
    """
    checks = [
        _check_smoke(sim_mode, allow_smoke),
        _check_data_quality(dq_report, sim_mode=sim_mode, allow_smoke=allow_smoke),
        _check_quote_coverage(
            quote_coverage_pct,
            min_quote_coverage_pct=min_quote_coverage_pct,
            sim_mode=sim_mode,
            allow_smoke=allow_smoke,
        ),
        _check_sip_data(
            feed=feed,
            sim_mode=sim_mode,
            lake_root=lake_root,
            sip_partitions_present=sip_partitions_present,
        ),
    ]
    result = PreflightResult(
        passed=all(c.status != "fail" for c in checks), checks=checks
    )
    if raise_on_fail and not result.passed:
        reasons = "; ".join(f"[{c.name}] {c.detail}" for c in result.failures)
        raise PreflightError(
            f"optuna study refused by preflight: {len(result.failures)} "
            f"prerequisite check(s) failed: {reasons}"
        )
    return result


def probe_quote_coverage(
    *,
    symbols: list[str],
    sessions: list[_dt.date],
    quote_supplier: Optional[Callable[..., Any]],
    scan_times_per_session: Callable[[_dt.date], list[Any]],
    max_probe: int = 200,
) -> Optional[float]:
    """Cheaply estimate historical-quote coverage before launching the study.

    Probes up to ``max_probe`` ``(symbol, scan_ts)`` pairs across the supplied
    sessions and returns the percentage backed by a historical quote. Returns
    ``None`` when there is no quote supplier or nothing to probe — the caller
    then records the quote-coverage check as ``skipped``.
    """
    if quote_supplier is None or not symbols or not sessions:
        return None
    probed = 0
    present = 0
    for session in sessions:
        try:
            scan_times = list(scan_times_per_session(session))
        except Exception:  # noqa: BLE001 — a scheduling error means no probe for this session
            scan_times = []
        if not scan_times:
            continue
        probe_ts = scan_times[len(scan_times) // 2]
        for sym in symbols:
            if probed >= max_probe:
                break
            probed += 1
            try:
                quote = quote_supplier(sym, probe_ts)
            except Exception:  # noqa: BLE001 — a supplier error counts as a missing quote
                quote = None
            if quote is not None:
                present += 1
        if probed >= max_probe:
            break
    if probed == 0:
        return None
    return 100.0 * present / probed


# --------------------------------------------------------------------------
# Full per-fold preflight (realism remediation 2 Phase 8 / audit §P1-006).
#
# The cheap study-start preflight above probes only the first validation
# window's first few sessions; that is fine as a fast early warning but is not
# enough to launch a multi-hour study with confidence. The full preflight
# evaluates EVERY validation / holdout window once at study start so a fold
# missing required daily/minute/quote/exit-path coverage blocks the run before
# any trial costs are paid.
#
# Cached by ``(dataset_hash, fold_window, config_hash)``: a study that pays the
# preflight cost for a (lake, config) pair never pays it again for the same
# fold even across re-runs in the same process.
# --------------------------------------------------------------------------
#: Process-local cache: ``(dataset_hash, fold_id, config_hash) -> PreflightResult``.
_FULL_FOLD_PREFLIGHT_CACHE: dict[tuple[str, str, str], "PreflightResult"] = {}


@dataclass
class FoldWindow:
    """A single (validation / holdout) window probed by the full per-fold preflight."""

    fold_id: str               # ``"val_<start>"`` / ``"holdout_<start>"``
    kind: str                  # ``"validation"`` | ``"holdout"``
    start: _dt.date
    end: _dt.date


def _probe_fold(
    *,
    cfg: Mapping[str, Any],
    fold: FoldWindow,
    symbols: list[str],
    lake_root: Any,
    feed: str,
    scan_times_per_session: Callable[[_dt.date], list[Any]],
    min_quote_coverage_pct: float,
    min_pit_universe: int = DEFAULT_MIN_PIT_UNIVERSE_PER_FOLD,
) -> "PreflightResult":
    """Build a DQ report + probe quote coverage for ``fold`` and run preflight."""
    # Local imports avoid a circular import — these modules consume optuna
    # symbols at module load.
    from ..data.adjustment import daily_adjustment_for_config
    from ..data.data_quality import build_data_quality_report
    from ..data.lineage import build_dataset_lineage
    from ..data.suppliers import (
        make_lake_suppliers,
        make_quote_supplier,
        resolve_intraday_window_policy,
    )

    # Bound the per-fold session probe so a very long fold doesn't blow up
    # the preflight cost — the cheap preflight already probed the first 5
    # sessions; the goal here is to PROVE coverage across every fold, not
    # to be exhaustive.
    sim_mode = ((cfg.get("simulation") or {}).get("mode") or "smoke_fixture")
    md = cfg.get("market_data") or {}
    try:
        # Half-open ``[fold.start, fold.end)`` to match the planner — a fold
        # whose ``end == final_holdout_start`` must NOT include the holdout's
        # first session (speedup report §3 / audit §P0-002).
        from .calendar_sessions import calendar_sessions_half_open

        sessions = calendar_sessions_half_open(fold.start, fold.end)
    except Exception as exc:  # noqa: BLE001 — calendar load failure handling depends on mode
        # Audit 2026-05-23 §P0-003 — intended_realism cannot tolerate a silent
        # calendar load failure; it must fail closed. Parity / smoke continue
        # to skip the fold (the cheaper preflight already noted the gap).
        if sim_mode == "intended_realism":
            return PreflightResult(
                passed=False,
                checks=[PreflightCheck(
                    name=f"fold:{fold.fold_id}",
                    status="fail",
                    detail=(
                        f"fold {fold.fold_id} calendar load failed under intended_realism: {exc}. "
                        "See docs/audits/2026-05-23_realism_audit.md §P0-003."
                    ),
                    evidence={"kind": fold.kind, "exception": str(exc),
                              "simulation_mode": sim_mode},
                )],
            )
        sessions = []
    if not sessions:
        return PreflightResult(
            passed=True,
            checks=[PreflightCheck(
                name=f"fold:{fold.fold_id}",
                status="skipped",
                detail=f"fold {fold.fold_id} has no XNYS sessions in [{fold.start}, {fold.end})",
                evidence={"kind": fold.kind, "start": fold.start.isoformat(), "end": fold.end.isoformat()},
            )],
        )

    try:
        minute_supplier, daily_supplier = make_lake_suppliers(
            lake_root, feed=feed,
            intraday_window_policy=resolve_intraday_window_policy(cfg),
            daily_adjustment=daily_adjustment_for_config(cfg),
        )
        lineage = build_dataset_lineage(
            cfg=cfg, symbols=symbols,
            start=sessions[0], end=sessions[-1],
            lab_config_hash="full_fold_preflight",
        )
        # Audit 2026-06-07 §6.6-compatible "denominator-only" fix: build the
        # per-session PIT-eligible set so the coverage gates score their
        # PASS/FAIL fraction over only the (symbol, session) pairs the live
        # scanner would actually evaluate (the full union is still PROBED, so the
        # audit-2026-05-23 §6.6 uncapped-union telemetry invariant is preserved).
        # ``eligible_per_session_map`` degrades to ``None`` (legacy full-union
        # gate) on any failure and NEVER crashes the preflight.
        from .pit_universe import eligible_per_session_map

        eligible_per_session: Optional[Mapping[_dt.date, set[str]]] = (
            eligible_per_session_map(lake_root, sessions, cfg=cfg)
        )
        dq_report = build_data_quality_report(
            cfg=cfg, lineage=lineage, requested_symbols=symbols,
            sessions=sessions, daily_bars_supplier=daily_supplier,
            minute_bars_supplier=minute_supplier,
            scan_times_per_session=scan_times_per_session,
            eligible_per_session=eligible_per_session,
        )
    except Exception as exc:  # noqa: BLE001 — DQ probe failure handling depends on mode
        # Audit 2026-05-23 §P0-003 — under intended_realism a DQ probe
        # exception is the structural signal that the lake cannot support a
        # research-grade objective. Fail closed; the runner's outer
        # ``try/except STRUCTURAL_EXCEPTIONS`` will not catch a PreflightError
        # raised by ``run_full_fold_preflight``'s caller, but the failed-status
        # study artifact is still written by that path.
        if sim_mode == "intended_realism":
            return PreflightResult(
                passed=False,
                checks=[PreflightCheck(
                    name=f"fold:{fold.fold_id}",
                    status="fail",
                    detail=(
                        f"fold {fold.fold_id} DQ probe failed under intended_realism: {exc}. "
                        "See docs/audits/2026-05-23_realism_audit.md §P0-003."
                    ),
                    evidence={"kind": fold.kind, "exception": str(exc),
                              "simulation_mode": sim_mode},
                )],
            )
        return PreflightResult(
            passed=True,
            checks=[PreflightCheck(
                name=f"fold:{fold.fold_id}",
                status="skipped",
                detail=f"fold {fold.fold_id} DQ probe failed: {exc}",
                evidence={"kind": fold.kind, "exception": str(exc)},
            )],
        )
    quote_cov_pct: Optional[float] = None
    quote_probe_exception: Optional[str] = None
    try:
        quote_supplier = make_quote_supplier(lake_root, feed=feed)
        quote_cov_pct = probe_quote_coverage(
            symbols=symbols, sessions=sessions, quote_supplier=quote_supplier,
            scan_times_per_session=scan_times_per_session, max_probe=200,
        )
    except Exception as exc:  # noqa: BLE001 — quote probe failure handling depends on mode
        # Audit 2026-05-23 §P0-003 — under intended_realism a quote-probe
        # exception must fail closed (the downstream realism simulator would
        # otherwise silently fall back to the zero-spread quote model).
        quote_cov_pct = None
        quote_probe_exception = str(exc)
        if sim_mode == "intended_realism":
            return PreflightResult(
                passed=False,
                checks=[PreflightCheck(
                    name=f"fold:{fold.fold_id}",
                    status="fail",
                    detail=(
                        f"fold {fold.fold_id} quote probe failed under intended_realism: {exc}. "
                        "See docs/audits/2026-05-23_realism_audit.md §P0-003."
                    ),
                    evidence={"kind": fold.kind, "exception": str(exc),
                              "simulation_mode": sim_mode},
                )],
            )

    result = run_preflight(
        sim_mode=str(sim_mode),
        allow_smoke=(str(sim_mode) == "smoke_fixture"),
        dq_report=dq_report,
        quote_coverage_pct=quote_cov_pct,
        min_quote_coverage_pct=float(min_quote_coverage_pct),
        feed=feed,
        lake_root=lake_root,
        raise_on_fail=False,
    )
    # Rename the checks so the caller can attribute them to this fold; preserve
    # statuses, detail strings, and evidence verbatim.
    relabeled: list[PreflightCheck] = []
    for c in result.checks:
        relabeled.append(PreflightCheck(
            name=f"fold:{fold.fold_id}:{c.name}",
            status=c.status, detail=c.detail,
            evidence={**c.evidence, "kind": fold.kind,
                      "start": fold.start.isoformat(), "end": fold.end.isoformat()},
        ))
    fold_passed = result.passed

    # Audit 2026-05-29 §5.4 / Phase 1 — extra hard-fail gates that apply to BOTH
    # intended_realism AND current_code_parity (skipped for smoke_fixture). The
    # legacy run_preflight is quote/DQ-centric and is tolerant under parity; a
    # parity study against a fold with NO minute bars or an empty PIT universe
    # is still un-runnable, so these gates fail closed regardless of mode.
    if str(sim_mode) in ("intended_realism", "current_code_parity"):
        # (a) Minute coverage — does a minute partition exist for any
        # (sampled symbol, fold-month)? A partition-existence probe (not an
        # in-window supplier call) is robust to the forming-window policy and
        # DST shifts, and matches the audit's "missing minute bars for the
        # entire fold window" intent: no minute data at all for the fold.
        saw_minute = True  # default to present; only fail on a clean negative
        try:
            from bowaka_common.marketdata import MarketDataStore as _MDS
            from bowaka_common.marketdata import layout as _layout

            _store = lake_root if isinstance(lake_root, _MDS) else _MDS(lake_root)
            months = sorted({(s.year, s.month) for s in sessions})
            saw_minute = False
            for sym in symbols[:25]:
                for (yr, mo) in months:
                    if _layout.minute_bars_path(
                        _store.root, sym, yr, mo, feed=feed
                    ).is_file():
                        saw_minute = True
                        break
                if saw_minute:
                    break
        except Exception:  # noqa: BLE001 — a probe error must not false-fail the fold
            saw_minute = True
        if not saw_minute:
            fold_passed = False
            relabeled.append(PreflightCheck(
                name=f"fold:{fold.fold_id}:missing_minute_coverage",
                status="fail",
                detail=(
                    f"fold {fold.fold_id} has no forming-session minute bars for "
                    f"any probed (symbol, scan_ts) in [{fold.start}, {fold.end}); "
                    "the scanner cannot evaluate candidates."
                ),
                evidence={"kind": fold.kind, "simulation_mode": str(sim_mode)},
            ))

        # (b) PIT universe — refuse a fold whose point-in-time universe resolves
        # to fewer than ``min_pit_universe`` eligible symbols on its best session.
        pit_count = 0
        try:
            from bowaka_common.marketdata import MarketDataStore as _MDS

            from ..universe.builder import (
                build_pit_universe_for_sessions as _bpit,
                eligible_symbols as _elig,
            )

            pit = _bpit(list(sessions), dict(cfg), _MDS(lake_root))
            for s in sessions:
                n_elig = len(_elig(pit.get(s, {})) or ())
                if n_elig > pit_count:
                    pit_count = n_elig
        except Exception as exc:  # noqa: BLE001 — a PIT build error is itself a fold failure
            fold_passed = False
            relabeled.append(PreflightCheck(
                name=f"fold:{fold.fold_id}:pit_universe_error",
                status="fail",
                detail=f"fold {fold.fold_id} PIT universe build failed: {exc}",
                evidence={"kind": fold.kind, "simulation_mode": str(sim_mode)},
            ))
        else:
            if pit_count < int(min_pit_universe):
                fold_passed = False
                relabeled.append(PreflightCheck(
                    name=f"fold:{fold.fold_id}:empty_pit_universe",
                    status="fail",
                    detail=(
                        f"fold {fold.fold_id} PIT universe has {pit_count} eligible "
                        f"symbol(s) on its best session, below the required "
                        f"minimum {int(min_pit_universe)}."
                    ),
                    evidence={"kind": fold.kind, "pit_universe_count": pit_count,
                              "min_pit_universe": int(min_pit_universe)},
                ))

    return PreflightResult(passed=fold_passed, checks=relabeled)


def run_full_fold_preflight(
    *,
    cfg: Mapping[str, Any],
    folds: list[FoldWindow],
    symbols: list[str],
    lake_root: Any,
    feed: str,
    dataset_hash: str,
    config_hash: str,
    scan_times_per_session: Callable[[_dt.date], list[Any]],
    min_quote_coverage_pct: float,
    mode: Optional[str] = None,
    raise_on_fail: bool = True,
) -> "PreflightResult":
    """Run preflight against EVERY validation + holdout window (audit §P1-006).

    Cached by ``(dataset_hash, fold_id, config_hash)``: re-running with identical
    inputs is free. Raises :class:`PreflightError` (when ``raise_on_fail``) when
    any fold fails its preflight.

    Audit 2026-05-29 §5.4 / Phase 1 — also runs under ``current_code_parity``
    (not just ``intended_realism``). Adds study-level hard fails for a
    config-required split-adjusted partition the lake lacks and for
    validation/holdout window overlap, and — under ``current_code_parity`` only
    — records non-blocking IEX partial-tape limitations (missing quotes / SIP)
    instead of failing on them (those remain hard fails under intended_realism).
    """
    sim_mode = str(mode or (cfg.get("simulation") or {}).get("mode") or "intended_realism")
    _min_pit_cfg = (cfg.get("preflight") or {}).get("min_pit_universe_per_fold")
    # NB: use an is-None check, not ``or`` — an explicit 0 (disable the floor)
    # is falsy and must not silently fall back to the default.
    min_pit = int(
        DEFAULT_MIN_PIT_UNIVERSE_PER_FOLD if _min_pit_cfg is None else _min_pit_cfg
    )
    aggregated: list[PreflightCheck] = []
    limitations: list[str] = []
    all_passed = True

    # ---- study-level gate 1: required daily-adjustment partition exists -------
    # Hard-fail (both modes) when the config requires split_adjusted daily bars
    # but the lake has no split_adjusted daily partition on disk. This runs
    # BEFORE any fold probe so a multi-hour study never starts on a lake that
    # cannot satisfy the strategy's adjustment contract.
    from ..data.adjustment import daily_adjustment_for_config

    required_adj = daily_adjustment_for_config(cfg)
    if required_adj and required_adj != "raw":
        from .autoconfig import probe_lake_capability

        cap = probe_lake_capability(
            _coerce_lake_root(lake_root), feed, required_adjustment=required_adj,
        )
        if not cap.has_required_daily_adjustment:
            all_passed = False
            aggregated.append(PreflightCheck(
                name="daily_adjustment_partition",
                status="fail",
                detail=(
                    f"config requires {required_adj} daily bars but the lake has "
                    f"no {required_adj} daily partition on disk for feed={feed!r}. "
                    "Re-ingest the adjusted partition or correct "
                    "market_data.require_*_adjustment."
                ),
                evidence={"required_adjustment": required_adj, "feed": feed,
                          "has_required_daily_adjustment": False},
            ))

    # ---- study-level gate 2: validation windows must not touch the holdout ----
    holdouts = [f for f in folds if f.kind == "holdout"]
    for ho in holdouts:
        for vf in folds:
            if vf.kind != "validation":
                continue
            # half-open overlap test on [start, end)
            if vf.start < ho.end and ho.start < vf.end:
                all_passed = False
                aggregated.append(PreflightCheck(
                    name=f"holdout_overlap:{vf.fold_id}",
                    status="fail",
                    detail=(
                        f"validation fold {vf.fold_id} [{vf.start}, {vf.end}) "
                        f"overlaps the final-holdout window [{ho.start}, {ho.end}); "
                        "tuning must never read the holdout."
                    ),
                    evidence={"validation_fold": vf.fold_id, "holdout_fold": ho.fold_id},
                ))

    # ---- study-level gate 3 (current_code_parity only): IEX partial-tape -----
    # Record (do NOT fail on) the limitations that make an IEX parity run a
    # research-only run. Under intended_realism the per-fold quote gate fails
    # on these instead (preserved below).
    if sim_mode == "current_code_parity":
        from .autoconfig import lake_has_quotes

        if not lake_has_quotes(_coerce_lake_root(lake_root), feed):
            limitations.append("missing_historical_quotes")
        if str(feed) != "sip":
            limitations.append("missing_sip")

    for fold in folds:
        cache_key = (str(dataset_hash), fold.fold_id, str(config_hash))
        cached = _FULL_FOLD_PREFLIGHT_CACHE.get(cache_key)
        if cached is None:
            cached = _probe_fold(
                cfg=cfg, fold=fold, symbols=symbols, lake_root=lake_root,
                feed=feed, scan_times_per_session=scan_times_per_session,
                min_quote_coverage_pct=min_quote_coverage_pct,
                min_pit_universe=min_pit,
            )
            _FULL_FOLD_PREFLIGHT_CACHE[cache_key] = cached
        if not cached.passed:
            all_passed = False
        aggregated.extend(cached.checks)
    result = PreflightResult(
        passed=all_passed, checks=aggregated,
        iex_partial_tape_limitations=limitations,
    )
    if raise_on_fail and not result.passed:
        failures = [c for c in aggregated if c.status == "fail"]
        reasons = "; ".join(f"[{c.name}] {c.detail}" for c in failures)
        raise PreflightError(
            f"optuna study refused by full per-fold preflight: "
            f"{len(failures)} fold(s) failed required check(s): {reasons}"
        )
    return result


def _clear_full_fold_preflight_cache() -> None:
    """Test hook: clear the per-fold preflight cache (used by per-fold tests)."""
    _FULL_FOLD_PREFLIGHT_CACHE.clear()


@dataclass
class NbboCoverageResult:
    """Outcome of :func:`check_nbbo_quote_coverage` (audit 2026-05-29 §9 Phase 7)."""

    mode: str
    feed: str
    coverage_pct: float
    passed: bool
    limitations: list


def check_nbbo_quote_coverage(
    *,
    sim_mode: str,
    feed: str,
    lake_root,
    universe,
    fold_windows,
    min_coverage_pct: float,
) -> "NbboCoverageResult":
    """NBBO (SIP top-of-book quote) coverage gate (audit 2026-05-29 §9 Phase 7).

    Behaviour by (mode, feed):
      - ``intended_realism`` + ``sip`` — hard-fail (PreflightError) if mean
        per-fold coverage < ``min_coverage_pct``.
      - ``intended_realism`` + ``iex`` — hard-fail with NBBO_NOT_AVAILABLE_ON_IEX
        (IEX is a partial tape and cannot provide NBBO).
      - ``current_code_parity`` — warn only; records the IEX partial-tape
        limitation ``"missing_historical_quotes"`` on the result.
      - ``smoke_fixture`` — skipped (always passes).
    """
    mode = str(sim_mode)
    fd = str(feed).lower()
    if mode == "smoke_fixture":
        return NbboCoverageResult(mode, fd, 100.0, True, [])
    if mode == "intended_realism" and fd == "iex":
        raise PreflightError(
            "NBBO_NOT_AVAILABLE_ON_IEX: intended_realism requires SIP NBBO "
            "quotes; feed='iex' is a partial tape and cannot provide them"
        )

    from bowaka_common.marketdata import MarketDataStore

    store = MarketDataStore(str(lake_root))
    total = 0
    covered = 0
    for fw in fold_windows:
        for sym in universe:
            total += 1
            try:
                q = store.quotes(sym, fw.start, fw.end, feed="sip")
            except Exception:  # noqa: BLE001 — a missing partition is no-coverage
                q = None
            if q is not None and not getattr(q, "empty", True):
                covered += 1
    coverage_pct = (100.0 * covered / total) if total else 0.0

    if mode == "intended_realism" and fd == "sip":
        if coverage_pct < float(min_coverage_pct):
            raise PreflightError(
                f"NBBO quote coverage {coverage_pct:.2f}% < required "
                f"{float(min_coverage_pct):.2f}% under intended_realism+sip"
            )
        return NbboCoverageResult(mode, fd, coverage_pct, True, [])

    # current_code_parity (and any other research mode) — warn, never block.
    limitations: list = []
    if coverage_pct < float(min_coverage_pct):
        limitations.append("missing_historical_quotes")
    return NbboCoverageResult(mode, fd, coverage_pct, True, limitations)


__all__ = [
    "PreflightError",
    "PreflightCheck",
    "PreflightResult",
    "FoldWindow",
    "_coerce_lake_root",
    "NbboCoverageResult",
    "check_nbbo_quote_coverage",
    "DEFAULT_MIN_QUOTE_COVERAGE_PCT",
    "run_preflight",
    "run_full_fold_preflight",
    "probe_quote_coverage",
    "_check_sip_data",
]
