"""Report renderer emits the exact paste-back sections expected by the prompt."""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

from bowaka_v2_lab.parity.metrics import compute_parity_metrics
from bowaka_v2_lab.parity.report import render_markdown_report
from bowaka_v2_lab.parity.schemas import NormalizedTrade


_REQUIRED_HEADERS = (
    "# Production-vs-lab parity report",
    "## Window",
    "## Counts",
    "## Parity metrics",
    "## Trades only in production",
    "## Trades only in lab",
    "## Largest fill-price diffs",
    "## Exit-reason mismatches",
    "## Daily PnL sign match",
    "## Overall",
)


def _t(symbol: str, *, minute: int, entry: float = 10.0) -> NormalizedTrade:
    return NormalizedTrade(
        session_date=_dt.date(2026, 5, 19), symbol=symbol,
        entry_ts_minute=_dt.datetime(2026, 5, 19, 14, minute, tzinfo=_dt.UTC),
        entry_price=entry, qty_filled=100,
        exit_ts_minute=_dt.datetime(2026, 5, 19, 15, minute, tzinfo=_dt.UTC),
        exit_price=entry * 1.05, exit_reason="target", pnl_dollars=5.0,
    )


def test_renderer_emits_all_required_sections_and_verdict(tmp_path: Path) -> None:
    # Use a partial-overlap report so every section has content.
    prod = [_t("A", minute=30), _t("B", minute=31), _t("C", minute=32, entry=10.0)]
    lab = [_t("A", minute=30), _t("C", minute=32, entry=10.05), _t("D", minute=33)]
    report = compute_parity_metrics(
        window_start=_dt.date(2026, 5, 19), window_end=_dt.date(2026, 5, 19),
        universe_size=4, prod_trades=prod, prod_candidates=[],
        lab_trades=lab, lab_candidates=[],
    )
    out_path = tmp_path / "out" / "parity_report.md"
    written = render_markdown_report(report, output_path=out_path)
    assert written == out_path
    assert out_path.is_file()
    md = out_path.read_text(encoding="utf-8")
    for h in _REQUIRED_HEADERS:
        assert h in md, f"missing section: {h}"
    # The Overall section carries a binary verdict.
    assert "PASSES AUDIT THRESHOLDS:" in md
    assert "no" in md.split("PASSES AUDIT THRESHOLDS:")[1].split()[0].lower()
    # Pass/fail column rendered for parity metrics.
    assert "FAIL" in md
    # Drill-down content present.
    assert "| B |" in md  # prod-only B row
    assert "| D |" in md  # lab-only D row


def test_renderer_full_agreement_marks_pass(tmp_path: Path) -> None:
    t = _t("A", minute=30)
    report = compute_parity_metrics(
        window_start=_dt.date(2026, 5, 19), window_end=_dt.date(2026, 5, 19),
        universe_size=1, prod_trades=[t], prod_candidates=[],
        lab_trades=[t], lab_candidates=[],
    )
    out_path = tmp_path / "parity_report.md"
    render_markdown_report(report, output_path=out_path)
    md = out_path.read_text(encoding="utf-8")
    assert "PASSES AUDIT THRESHOLDS: yes" in md
    assert "FAIL" not in md.split("## Parity metrics")[1].split("##")[0]
