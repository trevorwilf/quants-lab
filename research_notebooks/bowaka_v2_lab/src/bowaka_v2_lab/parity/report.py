"""Paste-back Markdown report for a :class:`ParityReport`."""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Mapping

from .metrics import DEFAULT_THRESHOLDS, _LOWER_IS_BETTER, evaluate_thresholds
from .schemas import ParityReport


def _threshold_op(name: str) -> str:
    return "≤" if name in _LOWER_IS_BETTER else "≥"


def _fmt_n(v: float, digits: int = 4) -> str:
    return f"{float(v):.{digits}f}"


def _trade_row(t) -> str:
    return (
        f"| {t.session_date.isoformat()} | {t.symbol} | "
        f"{t.entry_ts_minute.isoformat()} | "
        f"{_fmt_n(t.entry_price)} | {t.qty_filled} | "
        f"{t.exit_reason or '-'} | {_fmt_n(t.pnl_dollars, digits=2)} |"
    )


def render_markdown_report(
    report: ParityReport,
    *,
    output_path: Path,
    thresholds: Mapping[str, float] = DEFAULT_THRESHOLDS,
) -> Path:
    """Write a paste-back Markdown report with the audit's grid shape.

    Returns ``output_path`` (parent created on demand). The body always
    includes every prompt-required section header so the consumer can scan it.
    """
    out: list[str] = []
    out.append("# Production-vs-lab parity report")
    out.append("")
    out.append(f"- generated_at: {_dt.datetime.now(_dt.UTC).isoformat()}")
    out.append("")

    out.append("## Window")
    out.append("")
    out.append("| Field | Value |")
    out.append("|---|---|")
    out.append(f"| window_start | {report.window_start.isoformat()} |")
    out.append(f"| window_end | {report.window_end.isoformat()} |")
    out.append(f"| universe_size | {report.universe_size} |")
    out.append(f"| n_sessions | {report.n_sessions} |")
    out.append(f"| n_trade_sessions | {report.n_trade_sessions} |")
    out.append("")

    out.append("## Counts")
    out.append("")
    out.append("| | Production | Lab |")
    out.append("|---|---:|---:|")
    out.append(f"| candidates | {report.prod_n_candidates} | {report.lab_n_candidates} |")
    out.append(f"| trades     | {report.prod_n_trades} | {report.lab_n_trades} |")
    out.append(
        f"| gross_pnl  | {_fmt_n(report.prod_gross_pnl, 2)} | "
        f"{_fmt_n(report.lab_gross_pnl, 2)} |"
    )
    out.append("")

    out.append("## Parity metrics")
    out.append("")
    out.append("| Metric | Actual | Threshold | Result |")
    out.append("|---|---:|---:|:--:|")
    passes, failing = evaluate_thresholds(report, thresholds=thresholds)
    failing_set = set(failing)
    for name, threshold in thresholds.items():
        raw = getattr(report, name)
        if raw is None:
            # Phase 0 (parity oracle): not-measured metric (e.g. candidate recall
            # when a side emits no candidate telemetry) -> N/A, never FAIL.
            out.append(
                f"| {name} | N/A | {_threshold_op(name)} {_fmt_n(threshold)} | N/A |"
            )
            continue
        value = float(raw)
        result = "FAIL" if name in failing_set else "PASS"
        out.append(
            f"| {name} | {_fmt_n(value)} | "
            f"{_threshold_op(name)} {_fmt_n(threshold)} | {result} |"
        )
    out.append("")

    out.append("## Trades only in production")
    out.append("")
    if report.prod_only_trades:
        out.append("| session_date | symbol | entry_ts_minute | entry_price | qty | exit_reason | pnl_dollars |")
        out.append("|---|---|---|---:|---:|---|---:|")
        for t in report.prod_only_trades:
            out.append(_trade_row(t))
    else:
        out.append("- (none)")
    out.append("")

    out.append("## Trades only in lab")
    out.append("")
    if report.lab_only_trades:
        out.append("| session_date | symbol | entry_ts_minute | entry_price | qty | exit_reason | pnl_dollars |")
        out.append("|---|---|---|---:|---:|---|---:|")
        for t in report.lab_only_trades:
            out.append(_trade_row(t))
    else:
        out.append("- (none)")
    out.append("")

    out.append("## Largest fill-price diffs")
    out.append("")
    if report.largest_fill_diffs:
        out.append("| session_date | symbol | entry_ts_minute | prod_entry_price | lab_entry_price | fill_diff_bps |")
        out.append("|---|---|---|---:|---:|---:|")
        for row in report.largest_fill_diffs:
            out.append(
                f"| {row['session_date']} | {row['symbol']} | {row['entry_ts_minute']} | "
                f"{_fmt_n(float(row['prod_entry_price']))} | "
                f"{_fmt_n(float(row['lab_entry_price']))} | "
                f"{_fmt_n(float(row['fill_diff_bps']), 2)} |"
            )
    else:
        out.append("- (none)")
    out.append("")

    out.append("## Exit-reason mismatches")
    out.append("")
    if report.exit_reason_mismatches:
        out.append("| session_date | symbol | entry_ts_minute | prod_exit_reason | lab_exit_reason |")
        out.append("|---|---|---|---|---|")
        for row in report.exit_reason_mismatches:
            out.append(
                f"| {row['session_date']} | {row['symbol']} | {row['entry_ts_minute']} | "
                f"{row.get('prod_exit_reason') or '-'} | {row.get('lab_exit_reason') or '-'} |"
            )
    else:
        out.append("- (none)")
    out.append("")

    out.append("## Daily PnL sign match")
    out.append("")
    if report.daily_pnl_per_session:
        out.append("| session_date | prod_pnl_dollars | lab_pnl_dollars | signs_agree |")
        out.append("|---|---:|---:|:--:|")
        for row in report.daily_pnl_per_session:
            out.append(
                f"| {row['session_date']} | {_fmt_n(float(row['prod_pnl_dollars']), 2)} | "
                f"{_fmt_n(float(row['lab_pnl_dollars']), 2)} | "
                f"{'yes' if row['signs_agree'] else 'no'} |"
            )
    else:
        out.append("- (no trades on either side)")
    out.append("")

    out.append("## Overall")
    out.append("")
    verdict = "yes" if passes else "no"
    out.append(f"**PASSES AUDIT THRESHOLDS: {verdict}**")
    if failing:
        out.append("")
        out.append("Failing metrics:")
        for name in failing:
            out.append(f"- {name}")
    out.append("")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(out), encoding="utf-8")
    return output_path


__all__ = ["render_markdown_report"]
