# Phase 8 summary — Reporting, promotion, run artifacts

**Branch:** `phase-8-realism-reporting-and-promotion` (off `dev`)
**Audit refs:** P0-015, §11 Phase 8, Ticket 12.
**Status:** complete, merged to `dev`.

## What shipped

- **Substantive report renderer** — `reports/render_run_report.py` rewritten as a
  14-section renderer drawing from the Phase 0-7 artifacts (header / data quality
  / universe funnel / scan replay / gate funnel / entry-decision funnel /
  execution quality / portfolio & risk / trade performance / exit analysis /
  regime analysis / config diff & lineage / known limitations / promotion
  checklist). No stub language — a genuinely missing section renders a labelled
  `Not available because: …` paragraph.
- **`report.json`** — machine-readable companion to `report.md` (every metric in
  tabular form); added to `_REQUIRED_ARTIFACTS`. Rendered after the
  quote-coverage finalize gate.
- **Content-inspecting promotion checklist** — `qr.04`–`qr.10` now inspect
  content, not file existence: non-empty DQ checks with no `fail`; non-placeholder
  dataset hash + real provider; realism quote-coverage ≥ threshold; no stub
  strings in `report.md`; clean config-parity diff; `n_trades ≥
  promotion.min_trade_count` (default 30, new `PromotionConfig` field);
  walkforward-holdout structural check. Every check returns
  `(status, evidence: dict)`.
- **Suitability cap preserved** — `promotion/suitability.py` unchanged; the
  mechanical `backtesting_only` cap (operator decision for paper/live) intact.

## Files

Code: `reports/render_run_report.py`, `reports/__init__.py`, `sim/backtester.py`,
`promotion/checklist.py`, `config/models.py` (`PromotionConfig.min_trade_count`).
Tests: 7 added (`test_report_no_stub_strings.py`,
`test_report_json_completeness.py`, `test_promotion_checklist_evidence_shape.py`,
`test_promotion_inspects_dq_checks.py`, `test_promotion_inspects_dataset_hash.py`,
`test_promotion_quote_coverage_check.py`, `test_promotion_min_trade_count.py`).
Updated: `test_promotion_gate_end_to_end.py`, `test_manifest_mode_present.py`,
`test_promotion_checklist_results_shape.py`, `test_report_renderer_required_sections.py`.

**Result:** 564 passed, 1 skipped, 12 deselected (slow/live), 0 failed.
env-check passes on all 5 shipping configs.

## Acceptance criteria

| Criterion | Status |
|---|---|
| Reports are no longer stubs; `report.json` written and complete | PASS |
| Promotion fails on missing realism evidence (content), not just files | PASS |
| Every promotion check carries `evidence: dict` | PASS |
| Operator-only `backtesting_only` cap preserved | PASS |
| env-check passes on all shipping configs | PASS (5/5) |

## Notes

- `qr.07_no_stub_report`'s id literally contains "stub"; the renderer sanitizes
  quoted check ids in `report.md` so the report never trips its own gate.
- A thin synthetic SIP run now correctly resolves to `research_only` (fails
  `qr.09_min_trade_count` with 3 trades vs 30) — the intended Phase-8 behavior of
  content-inspecting checks.
- The lab has no per-trade market-regime classifier, so the regime-analysis
  section renders the dataset regime + per-exit-reason PnL split plus a labelled
  `Not available because: …` paragraph.
