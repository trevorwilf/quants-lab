"""Reconciliation reports.

Three report renderers live here:

- :func:`render_reconciliation_report` — the Phase-7 mismatch-category report
  (``reconciliation_report.md``) driven by the dict-based
  :class:`reconcile.comparator.ComparatorResult` objects. Unchanged.
- :func:`render_realism_reconciliation_report` /
  :func:`build_reconcile_report` — the Phase-10 realism-audit report. Built
  from the typed :class:`reconcile.schemas.ReconcileRow` records the
  :func:`reconcile.replay.replay_paper_session` path produces; emits markdown
  **and** JSON with per-stage matched / mismatched counts, the top systematic
  biases, residual distributions and operator-facing calibration suggestions.
- :func:`render_phase9_recon_report` / :func:`build_phase9_recon_report` — the
  realism remediation 2 **Phase 9** reconcile report. Built from the seven
  Phase-9 aggregate comparators (emission Jaccard, decision-reason confusion,
  fill residuals, fill latency, OCO attempt count, exit reason+timing, PnL
  residuals) and the per-run tolerance dict; emits
  ``artifacts/reconcile/<run_id>/report.{json,md}`` with per-day + aggregate
  metrics and flags every mismatch above tolerance.
"""
from __future__ import annotations

import json
import statistics
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

import pandas as pd

from .schemas import ReconcileReport, ReconcileRow


REPORT_CATEGORIES = (
    "candidate_miss",
    "entry_decision_miss",
    "broker_rejection_mismatch",
    "slippage_outlier",
)


def render_reconciliation_report(
    *,
    candidate_match,
    decision_match,
    broker_reject_mismatches: Iterable[dict] | None = None,
    slippage_residuals: pd.DataFrame | None = None,
    out_path: Path | None = None,
) -> str:
    lines = ["# Paper-vs-Sim Reconciliation Report", ""]
    # Candidates section
    lines.append("## Candidates")
    lines.append(f"- match: {candidate_match.n_match}")
    lines.append(f"- candidate_miss (paper without sim): {candidate_match.n_miss}")
    lines.append(f"- extra (sim without paper): {candidate_match.n_extra}")
    lines.append("")
    # Decisions section
    lines.append("## Entry Decisions")
    lines.append(f"- match: {decision_match.n_match}")
    lines.append(f"- entry_decision_miss: {decision_match.n_miss}")
    lines.append(f"- extra: {decision_match.n_extra}")
    lines.append("")
    # Broker rejection mismatches
    lines.append("## Broker Rejection Mismatches")
    n_brm = len(list(broker_reject_mismatches)) if broker_reject_mismatches is not None else 0
    lines.append(f"- broker_rejection_mismatch count: {n_brm}")
    lines.append("")
    # Slippage outliers
    lines.append("## Slippage")
    if slippage_residuals is not None and not slippage_residuals.empty:
        q99 = slippage_residuals["residual"].abs().quantile(0.99)
        outliers = slippage_residuals[slippage_residuals["residual"].abs() > q99]
        lines.append(f"- n trades compared: {len(slippage_residuals)}")
        lines.append(f"- residual abs p99: {q99:.5f}")
        lines.append(f"- slippage_outlier count: {len(outliers)}")
    else:
        lines.append("- (no slippage residuals provided)")
    lines.append("")
    content = "\n".join(lines) + "\n"
    if out_path is not None:
        Path(out_path).write_text(content, encoding="utf-8")
    return content


# ==========================================================================
# Phase 10 — realism-audit paper-vs-lab reconciliation report.
# ==========================================================================
def _distribution(values: Sequence[float]) -> dict[str, float]:
    """Summary stats of a residual series (empty -> all zeros)."""
    vals = [float(v) for v in values if v is not None]
    if not vals:
        return {"n": 0, "mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "abs_p95": 0.0}
    abs_sorted = sorted(abs(v) for v in vals)
    p95_idx = min(len(abs_sorted) - 1, int(round(0.95 * (len(abs_sorted) - 1))))
    return {
        "n": len(vals),
        "mean": round(statistics.fmean(vals), 6),
        "median": round(statistics.median(vals), 6),
        "min": round(min(vals), 6),
        "max": round(max(vals), 6),
        "abs_p95": round(abs_sorted[p95_idx], 6),
    }


def build_reconcile_report(
    session_date: str,
    rows: Sequence[ReconcileRow],
    *,
    scaffolding_only: bool = False,
    note: Optional[str] = None,
) -> ReconcileReport:
    """Aggregate per-candidate :class:`ReconcileRow` records into a report.

    Computes the per-stage matched / mismatched / comparable counts, detects the
    top systematic biases (directional, not just magnitude) and derives the
    operator-facing calibration suggestions. Pure aggregation — no I/O.
    """
    report = ReconcileReport(
        session_date=session_date, scaffolding_only=scaffolding_only, note=note
    )

    # Candidate-set buckets.
    report.n_both = sum(1 for r in rows if r.presence == "both")
    report.n_paper_only = sum(1 for r in rows if r.presence == "paper_only")
    report.n_lab_only = sum(1 for r in rows if r.presence == "lab_only")
    report.n_paper_candidates = sum(
        1 for r in rows if r.paper_candidate is not None
    )
    report.n_lab_candidates = sum(1 for r in rows if r.lab_candidate is not None)

    # Per-stage counts. ``comparable`` = rows where the stage could be compared.
    decision_rows = [r for r in rows if r.decision_reason_match is not None]
    order_rows = [r for r in rows if r.order_size_delta is not None]
    fill_rows = [r for r in rows if r.fill_price_delta_bps is not None]
    exit_rows = [r for r in rows if r.exit_reason_match is not None]
    pnl_rows = [r for r in rows if r.pnl_delta is not None]

    report.stage_counts = {
        "candidate_set": {
            "both": report.n_both,
            "paper_only": report.n_paper_only,
            "lab_only": report.n_lab_only,
        },
        "decision_reason": {
            "comparable": len(decision_rows),
            "matched": sum(1 for r in decision_rows if r.decision_reason_match),
            "mismatched": sum(1 for r in decision_rows if not r.decision_reason_match),
        },
        "order_size": {
            "comparable": len(order_rows),
            "matched": sum(1 for r in order_rows if r.order_size_delta == 0.0),
            "mismatched": sum(1 for r in order_rows if r.order_size_delta != 0.0),
        },
        "fill": {
            "comparable": len(fill_rows),
            "matched": sum(1 for r in fill_rows if abs(r.fill_price_delta_bps or 0.0) < 1e-9),
            "mismatched": sum(1 for r in fill_rows if abs(r.fill_price_delta_bps or 0.0) >= 1e-9),
        },
        "exit_reason": {
            "comparable": len(exit_rows),
            "matched": sum(1 for r in exit_rows if r.exit_reason_match),
            "mismatched": sum(1 for r in exit_rows if not r.exit_reason_match),
        },
        "pnl": {
            "comparable": len(pnl_rows),
            "matched": sum(1 for r in pnl_rows if abs(r.pnl_delta or 0.0) < 1e-6),
            "mismatched": sum(1 for r in pnl_rows if abs(r.pnl_delta or 0.0) >= 1e-6),
        },
    }

    # Residual distributions.
    report.residual_distributions = {
        "order_size_delta": _distribution([r.order_size_delta for r in order_rows]),
        "fill_price_delta_bps": _distribution([r.fill_price_delta_bps for r in fill_rows]),
        "fill_qty_delta": _distribution(
            [r.fill_qty_delta for r in rows if r.fill_qty_delta is not None]
        ),
        "pnl_delta": _distribution([r.pnl_delta for r in pnl_rows]),
    }

    # Systematic biases — directional, derived from the buckets / residual means.
    biases: list[str] = []
    if report.n_lab_only > report.n_paper_only and report.n_lab_only > 0:
        biases.append(
            f"lab emits more candidates than paper "
            f"({report.n_lab_only} lab-only vs {report.n_paper_only} paper-only)"
        )
    elif report.n_paper_only > report.n_lab_only and report.n_paper_only > 0:
        biases.append(
            f"paper emits more candidates than lab "
            f"({report.n_paper_only} paper-only vs {report.n_lab_only} lab-only)"
        )
    fill_mean = report.residual_distributions["fill_price_delta_bps"]["mean"]
    if report.residual_distributions["fill_price_delta_bps"]["n"] and abs(fill_mean) >= 1.0:
        biases.append(
            f"lab fills {'above' if fill_mean > 0 else 'below'} paper by "
            f"{abs(fill_mean):.2f} bps on average"
        )
    qty_mean = report.residual_distributions["fill_qty_delta"]["mean"]
    if report.residual_distributions["fill_qty_delta"]["n"] and abs(qty_mean) >= 1e-9:
        biases.append(
            f"lab {'over' if qty_mean > 0 else 'under'}-fills paper by "
            f"{abs(qty_mean):.4g} shares on average"
        )
    rejected_paper = sum(
        1 for r in decision_rows
        if r.paper_decision is not None and r.paper_decision.decision == "rejected"
    )
    rejected_lab = sum(
        1 for r in decision_rows
        if r.lab_decision is not None and r.lab_decision.decision == "rejected"
    )
    if rejected_paper > rejected_lab:
        biases.append(
            f"paper rejects more candidates than lab "
            f"({rejected_paper} paper rejects vs {rejected_lab} lab rejects)"
        )
    elif rejected_lab > rejected_paper:
        biases.append(
            f"lab rejects more candidates than paper "
            f"({rejected_lab} lab rejects vs {rejected_paper} paper rejects)"
        )
    report.systematic_biases = biases

    # Calibration suggestions.
    suggestions: list[str] = []
    if scaffolding_only:
        suggestions.append(
            "no paper logs supplied — provide a paper-log directory to compute "
            "real calibration adjustments (Phase 10 is scaffolding only)"
        )
    if report.residual_distributions["fill_price_delta_bps"]["n"] and abs(fill_mean) >= 1.0:
        suggestions.append(
            f"adjust the fill / slippage model by {-fill_mean:+.2f} bps to centre "
            f"the lab fill price on paper"
        )
    decision_mismatch = report.stage_counts["decision_reason"]["mismatched"]
    if decision_mismatch:
        suggestions.append(
            f"{decision_mismatch} decision-reason mismatch(es) — review gate "
            f"ordering / thresholds against the live decision log"
        )
    exit_mismatch = report.stage_counts["exit_reason"]["mismatched"]
    if exit_mismatch:
        suggestions.append(
            f"{exit_mismatch} exit-reason mismatch(es) — review the OCO / "
            f"same-minute resolution policy against the live exit log"
        )
    if not suggestions:
        suggestions.append("no calibration adjustment indicated by this session")
    report.calibration_suggestions = suggestions

    report.rows = list(rows)
    return report


def _stage_line(name: str, counts: dict[str, int]) -> str:
    parts = ", ".join(f"{k}={v}" for k, v in counts.items())
    return f"- {name}: {parts}"


def render_realism_reconciliation_report(
    report: ReconcileReport,
    *,
    out_dir: Path | None = None,
    out_md_path: Path | None = None,
    out_json_path: Path | None = None,
) -> tuple[str, dict]:
    """Render the Phase-10 realism reconciliation report as markdown + JSON.

    Returns ``(markdown, json_dict)``. When ``out_dir`` is given, writes
    ``reconciliation_report.md`` and ``reconciliation_report.json`` into it;
    ``out_md_path`` / ``out_json_path`` override the individual paths.
    """
    lines: list[str] = ["# Paper-vs-Lab Reconciliation Report", ""]
    lines.append(f"- session_date: {report.session_date}")
    lines.append(f"- scaffolding_only: {report.scaffolding_only}")
    if report.note:
        lines.append(f"- note: {report.note}")
    lines.append("")

    lines.append("## Candidate Set")
    lines.append(f"- paper candidates: {report.n_paper_candidates}")
    lines.append(f"- lab candidates: {report.n_lab_candidates}")
    lines.append(f"- both: {report.n_both}")
    lines.append(f"- paper_only: {report.n_paper_only}")
    lines.append(f"- lab_only: {report.n_lab_only}")
    lines.append("")

    lines.append("## Stage Match Counts")
    for stage in ("decision_reason", "order_size", "fill", "exit_reason", "pnl"):
        if stage in report.stage_counts:
            lines.append(_stage_line(stage, report.stage_counts[stage]))
    lines.append("")

    lines.append("## Systematic Biases")
    if report.systematic_biases:
        for b in report.systematic_biases:
            lines.append(f"- {b}")
    else:
        lines.append("- none detected")
    lines.append("")

    lines.append("## Residual Distributions")
    for name, dist in report.residual_distributions.items():
        lines.append(
            f"- {name}: n={dist['n']}, mean={dist['mean']}, median={dist['median']}, "
            f"min={dist['min']}, max={dist['max']}, abs_p95={dist['abs_p95']}"
        )
    lines.append("")

    lines.append("## Suggested Calibration Adjustments")
    for s in report.calibration_suggestions:
        lines.append(f"- {s}")
    lines.append("")

    markdown = "\n".join(lines) + "\n"
    json_dict = report.model_dump(mode="json")

    md_path = out_md_path or (Path(out_dir) / "reconciliation_report.md" if out_dir else None)
    json_path = out_json_path or (
        Path(out_dir) / "reconciliation_report.json" if out_dir else None
    )
    if md_path is not None:
        Path(md_path).parent.mkdir(parents=True, exist_ok=True)
        Path(md_path).write_text(markdown, encoding="utf-8")
    if json_path is not None:
        Path(json_path).parent.mkdir(parents=True, exist_ok=True)
        Path(json_path).write_text(
            json.dumps(json_dict, indent=2, sort_keys=True, default=str), encoding="utf-8"
        )
    return markdown, json_dict


# ==========================================================================
# Realism remediation 2 Phase 9 — paper-vs-sim reconcile report.
# ==========================================================================
def _dataclass_to_dict(obj: Any) -> Any:
    """Recursively convert dataclasses (and nested ones) into JSON-friendly dicts.

    Bare values, dicts and lists pass through untouched. Pydantic models are
    expanded via ``.model_dump()`` so the Phase-9 paper / lab event records on
    nested comparator fields render cleanly.
    """
    if obj is None:
        return None
    if is_dataclass(obj):
        return {k: _dataclass_to_dict(v) for k, v in asdict(obj).items()}
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, list):
        return [_dataclass_to_dict(v) for v in obj]
    if isinstance(obj, dict):
        return {str(k): _dataclass_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, tuple):
        return [_dataclass_to_dict(v) for v in obj]
    return obj


def build_phase9_recon_report(
    *,
    run_id: str,
    session_dates: Sequence[str],
    tolerances: Mapping[str, float],
    emission: Any = None,
    decision_reason: Any = None,
    fills: Any = None,
    fill_latency: Any = None,
    oco_attempts: Any = None,
    exit_reason_timing: Any = None,
    pnl: Any = None,
    per_day: Optional[Mapping[str, Mapping[str, Any]]] = None,
    scaffolding_only: bool = False,
    note: Optional[str] = None,
) -> dict[str, Any]:
    """Build the Phase-9 reconcile report dict (aggregated + per-day).

    Each of the seven keyword arguments is the corresponding Phase-9 comparator
    dataclass (``EmissionJaccard``, ``DecisionReasonConfusion``,
    ``FillResidualSummary``, ``FillLatencySummary``, ``OCOAttemptCountDiff``,
    ``ExitReasonTimingSummary``, ``PnLResidualSummary``). ``per_day`` is an
    optional ``{session_date: {comparator_name: comparator_result}}`` mapping;
    when given, the report has both an aggregate block and a per-day block.

    The returned dict is JSON-serialisable, sorted-by-key on write.
    """
    aggregate: dict[str, Any] = {
        "emission_jaccard": _dataclass_to_dict(emission),
        "decision_reason_confusion": _dataclass_to_dict(decision_reason),
        "fill_residuals": _dataclass_to_dict(fills),
        "fill_latency": _dataclass_to_dict(fill_latency),
        "oco_attempt_count": _dataclass_to_dict(oco_attempts),
        "exit_reason_timing": _dataclass_to_dict(exit_reason_timing),
        "pnl_residuals": _dataclass_to_dict(pnl),
    }
    # Per-stage pass/fail booleans, useful for a quick CI-style check.
    passes_by_stage: dict[str, Optional[bool]] = {}
    for stage, payload in aggregate.items():
        if isinstance(payload, dict) and "passes" in payload:
            passes_by_stage[stage] = bool(payload["passes"])
        else:
            passes_by_stage[stage] = None
    overall = (
        all(v for v in passes_by_stage.values() if v is not None)
        if any(v is not None for v in passes_by_stage.values())
        else True
    )
    mismatch_flags: list[str] = []
    if (
        isinstance(aggregate["emission_jaccard"], dict)
        and aggregate["emission_jaccard"].get("passes") is False
    ):
        mismatch_flags.append(
            f"emission Jaccard {aggregate['emission_jaccard']['jaccard']:.3f} "
            f"< tolerance {aggregate['emission_jaccard']['threshold']:.2f}"
        )
    if (
        isinstance(aggregate["decision_reason_confusion"], dict)
        and aggregate["decision_reason_confusion"].get("passes") is False
    ):
        mismatch_flags.append(
            f"decision-reason match {aggregate['decision_reason_confusion']['match']:.3f} "
            f"< tolerance {aggregate['decision_reason_confusion']['threshold']:.2f}"
        )
    if (
        isinstance(aggregate["fill_residuals"], dict)
        and aggregate["fill_residuals"].get("passes") is False
    ):
        mismatch_flags.append(
            f"fill residuals: {aggregate['fill_residuals']['n_flagged']} flagged "
            f"(price tol {aggregate['fill_residuals']['price_tolerance_bps']} bps, "
            f"qty tol {aggregate['fill_residuals']['qty_tolerance_shares']} shares)"
        )
    if (
        isinstance(aggregate["fill_latency"], dict)
        and aggregate["fill_latency"].get("passes") is False
    ):
        mismatch_flags.append(
            f"fill latency p95 {aggregate['fill_latency']['p95_abs_delta_ms']} ms "
            f"> tolerance {aggregate['fill_latency']['tolerance_p95_ms']} ms"
        )
    if (
        isinstance(aggregate["oco_attempt_count"], dict)
        and aggregate["oco_attempt_count"].get("passes") is False
    ):
        mismatch_flags.append(
            f"OCO attempt-count mismatch: {aggregate['oco_attempt_count']['mismatched']} candidates differ"
        )
    if (
        isinstance(aggregate["exit_reason_timing"], dict)
        and aggregate["exit_reason_timing"].get("passes") is False
    ):
        mismatch_flags.append(
            f"exit reason / timing mismatch: "
            f"reason matches {aggregate['exit_reason_timing']['reason_matches']} / "
            f"{aggregate['exit_reason_timing']['comparable']}, "
            f"{aggregate['exit_reason_timing']['timing_flagged']} timing-flagged"
        )
    if (
        isinstance(aggregate["pnl_residuals"], dict)
        and aggregate["pnl_residuals"].get("passes") is False
    ):
        mismatch_flags.append(
            f"PnL residuals: {aggregate['pnl_residuals']['n_flagged']} flagged "
            f"(tol ${aggregate['pnl_residuals']['pnl_tolerance_dollars']:.2f})"
        )
    return {
        "run_id": str(run_id),
        "session_dates": list(session_dates),
        "tolerances": {k: float(v) for k, v in tolerances.items()},
        "scaffolding_only": bool(scaffolding_only),
        "note": note,
        "aggregate": aggregate,
        "per_day": _dataclass_to_dict(per_day or {}),
        "passes_by_stage": passes_by_stage,
        "overall_passed": bool(overall and not mismatch_flags),
        "mismatch_flags": mismatch_flags,
    }


def render_phase9_recon_report(
    *,
    run_id: str,
    session_dates: Sequence[str],
    tolerances: Mapping[str, float],
    out_dir: Path | str,
    emission: Any = None,
    decision_reason: Any = None,
    fills: Any = None,
    fill_latency: Any = None,
    oco_attempts: Any = None,
    exit_reason_timing: Any = None,
    pnl: Any = None,
    per_day: Optional[Mapping[str, Mapping[str, Any]]] = None,
    scaffolding_only: bool = False,
    note: Optional[str] = None,
) -> tuple[Path, Path]:
    """Render the Phase-9 reconcile report to ``out_dir/{report.json, report.md}``.

    Returns the ``(json_path, md_path)`` written. ``out_dir`` is treated as
    ``artifacts/reconcile/<run_id>`` by the CLI but any directory works for
    tests. Every mismatch above tolerance is enumerated under the report's
    "Mismatch flags" section.
    """
    report = build_phase9_recon_report(
        run_id=run_id,
        session_dates=session_dates,
        tolerances=tolerances,
        emission=emission,
        decision_reason=decision_reason,
        fills=fills,
        fill_latency=fill_latency,
        oco_attempts=oco_attempts,
        exit_reason_timing=exit_reason_timing,
        pnl=pnl,
        per_day=per_day,
        scaffolding_only=scaffolding_only,
        note=note,
    )
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "report.json"
    md_path = out / "report.md"
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    lines: list[str] = []
    lines.append(f"# Paper-vs-Sim Reconciliation Report — run {run_id}")
    lines.append("")
    lines.append(f"- session_dates: {', '.join(report['session_dates']) or '(none)'}")
    lines.append(f"- scaffolding_only: {report['scaffolding_only']}")
    if report.get("note"):
        lines.append(f"- note: {report['note']}")
    lines.append(f"- overall_passed: {report['overall_passed']}")
    lines.append("")
    lines.append("## Tolerances")
    for k, v in sorted(report["tolerances"].items()):
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Aggregate Comparator Outcomes")
    for stage, payload in report["aggregate"].items():
        if payload is None:
            lines.append(f"- {stage}: not computed")
            continue
        passes = payload.get("passes") if isinstance(payload, dict) else None
        if stage == "emission_jaccard" and isinstance(payload, dict):
            lines.append(
                f"- emission_jaccard: jaccard={payload['jaccard']}, "
                f"intersection={payload['intersection']}, union_size={payload['union_size']}, "
                f"paper_only={payload['paper_only']}, lab_only={payload['lab_only']}, "
                f"passes={passes}"
            )
        elif stage == "decision_reason_confusion" and isinstance(payload, dict):
            lines.append(
                f"- decision_reason: comparable={payload['comparable']}, "
                f"matched={payload['matched']}, match_rate={payload['match']}, passes={passes}"
            )
        elif stage == "fill_residuals" and isinstance(payload, dict):
            lines.append(
                f"- fill_residuals: comparable={payload['comparable']}, "
                f"flagged={payload['n_flagged']}, "
                f"median_bps={payload['median_price_delta_bps']}, "
                f"p95_abs_bps={payload['p95_abs_price_delta_bps']}, passes={passes}"
            )
        elif stage == "fill_latency" and isinstance(payload, dict):
            lines.append(
                f"- fill_latency: comparable={payload['comparable']}, "
                f"median_delta_ms={payload['median_delta_ms']}, "
                f"p95_abs_delta_ms={payload['p95_abs_delta_ms']}, passes={passes}"
            )
        elif stage == "oco_attempt_count" and isinstance(payload, dict):
            lines.append(
                f"- oco_attempt_count: comparable={payload['comparable']}, "
                f"matched={payload['matched']}, mismatched={payload['mismatched']}, "
                f"paper_total={payload['paper_total_attempts']}, "
                f"lab_total={payload['lab_total_attempts']}, passes={passes}"
            )
        elif stage == "exit_reason_timing" and isinstance(payload, dict):
            lines.append(
                f"- exit_reason_timing: comparable={payload['comparable']}, "
                f"reason_matches={payload['reason_matches']}, "
                f"timing_flagged={payload['timing_flagged']}, "
                f"median_delta_s={payload['median_timing_delta_seconds']}, passes={passes}"
            )
        elif stage == "pnl_residuals" and isinstance(payload, dict):
            lines.append(
                f"- pnl_residuals: comparable={payload['comparable']}, "
                f"flagged={payload['n_flagged']}, "
                f"median_delta=${payload['median_delta_dollars']}, "
                f"p95_abs_delta=${payload['p95_abs_delta_dollars']}, passes={passes}"
            )
        else:
            lines.append(f"- {stage}: {payload}")
    lines.append("")

    lines.append("## Mismatch Flags")
    if report["mismatch_flags"]:
        for f in report["mismatch_flags"]:
            lines.append(f"- {f}")
    else:
        lines.append("- (no mismatches above tolerance)")
    lines.append("")

    if report["per_day"]:
        lines.append("## Per-Day Outcomes")
        for day, day_payload in sorted(report["per_day"].items()):
            lines.append(f"### {day}")
            if isinstance(day_payload, dict):
                for stage, val in day_payload.items():
                    if isinstance(val, dict) and "passes" in val:
                        lines.append(f"- {stage}: passes={val['passes']}")
                    else:
                        lines.append(f"- {stage}: {val}")
            else:
                lines.append(f"- {day_payload}")
            lines.append("")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


__all__ = [  # noqa: F405 — appended to the existing __all__-less module
    "REPORT_CATEGORIES",
    "render_reconciliation_report",
    "build_reconcile_report",
    "render_realism_reconciliation_report",
    "build_phase9_recon_report",
    "render_phase9_recon_report",
]
