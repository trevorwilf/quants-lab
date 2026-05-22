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
   configured threshold.

Checks 2 and 3 gate **only ``intended_realism``** runs — mirroring the
data-quality contract (``data_quality.py``: "Only ``intended_realism`` runs are
gated; ``smoke_fixture`` and ``current_code_parity`` runs surface the same
report but are never failed by it"). For a ``current_code_parity`` study a
failing required DQ check or low quote coverage is recorded as a ``warn`` — it
is surfaced in the study metadata but does not refuse the run, because parity
mode reproduces the live code (which uses the zero-spread quote fallback).

The checks are skipped (with a recorded ``skipped`` status) when they cannot
apply — e.g. quote coverage is not meaningful for a ``smoke_fixture`` run that
was explicitly allowed via ``allow_smoke``.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional


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
        }


#: Below this fraction (percent) of (symbol, scan_ts) quote coverage a study is
#: refused. Mirrors ``SimulationConfig.min_quote_coverage_pct`` but is read from
#: the config so a study can lower it for an explicitly-degraded research run.
DEFAULT_MIN_QUOTE_COVERAGE_PCT = 95.0


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
    """Refuse the study when the dataset's DQ report has a failing required check."""
    if dq_report is None:
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
    if required_failures:
        evidence = {
            "regime": regime,
            "failed": failed,
            "required_failures": sorted(required_failures),
        }
        # The data-quality contract gates ONLY intended_realism runs;
        # current_code_parity surfaces the same report but is never failed by it.
        if sim_mode == "intended_realism":
            return PreflightCheck(
                name="data_quality",
                status="fail",
                detail=(
                    f"the dataset's data-quality report has {len(required_failures)} "
                    f"failing required check(s): {sorted(required_failures)} — the lake "
                    f"cannot support a research-grade optimization"
                ),
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


def run_preflight(
    *,
    sim_mode: str,
    allow_smoke: bool,
    dq_report: Optional[Mapping[str, Any]] = None,
    quote_coverage_pct: Optional[float] = None,
    min_quote_coverage_pct: float = DEFAULT_MIN_QUOTE_COVERAGE_PCT,
    raise_on_fail: bool = True,
) -> PreflightResult:
    """Run every study-start preflight check.

    ``dq_report`` is the dataset's ``data_quality_report.json`` document (or the
    output of :func:`bowaka_v2_lab.data.data_quality.build_data_quality_report`).
    ``quote_coverage_pct`` is the measured historical-quote coverage percentage,
    when known. Either may be ``None`` — the corresponding check is then
    ``skipped`` rather than failed.

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


__all__ = [
    "PreflightError",
    "PreflightCheck",
    "PreflightResult",
    "DEFAULT_MIN_QUOTE_COVERAGE_PCT",
    "run_preflight",
    "probe_quote_coverage",
]
