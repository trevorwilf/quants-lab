# Phase 10 summary — Paper-vs-sim reconciliation framework (scaffolding only)

**Branch:** `phase-10-realism-reconciliation-scaffold` (off `dev`)
**Audit refs:** §11 Phase 10. Operator decision: scaffolding only — no paper logs.
**Status:** complete, merged to `dev`.

## What shipped

Per the operator constraint, this is the reconciliation **framework** — the full
data path, schemas, comparators, report, and CLI — exercised end-to-end against a
frozen SYNTHETIC paper-log fixture. No real paper-log reconciliation is attempted.

- **`reconcile/schemas.py`** — Pydantic models: `PaperCandidate/Decision/Order/
  Fill/Exit`, `LabCandidate/Decision/Order/Fill/Exit`, `ReconcileRow`,
  `ReconcileReport`.
- **`reconcile/comparators.py`** — `diff_candidate_sets` (paper-only / lab-only /
  both), `compare_decision_reason`, `compare_order_size`, `compare_fill` (signed
  bps + qty delta), `compare_exit_reason`, `compare_pnl` — all keyed on
  `candidate_event_id`.
- **`reconcile/replay.py`** — `replay_paper_session(session_date,
  paper_logs_root, lab_cfg)` runs the lab in `simulation.mode ==
  current_code_parity` on the same lake/universe/date and joins side-by-side
  records into a `ReplayResult`.
- **`reconcile/report.py`** — extended with `build_reconcile_report` +
  `render_realism_reconciliation_report` (markdown + JSON): matched/mismatched
  counts per stage, top systematic biases, residual distributions, suggested
  calibration adjustments. The earlier-phase renderer is untouched.
- **`reconcile` CLI command** — `bowaka-v2-lab reconcile --paper-logs-root … 
  --session-date …`; with no paper logs it exits 0 and writes a scaffolding-only
  report.
- **Synthetic fixture** — `tests/fixtures/paper_logs_synthetic/` (frozen fake
  paper logs) + `tests/reconcile/` so the whole path is testable without real
  paper data.

## Files

Code: `reconcile/schemas.py` (new), `reconcile/comparators.py` (new),
`reconcile/replay.py` (new), `reconcile/report.py`, `reconcile/__init__.py`,
`cli.py`. Fixture: `tests/fixtures/paper_logs_synthetic/`. Tests: `tests/reconcile/`
(7 modules) + `tests/integration/test_reconcile_cli_missing_paper_logs.py`.

**Result:** 677 passed, 1 skipped, 12 deselected (slow/live), 0 failed.
env-check passes on all 5 shipping configs.

## Acceptance criteria

| Criterion | Status |
|---|---|
| Reconciliation path wired end-to-end against synthetic fixtures | PASS |
| `reconcile` CLI command exists; no-logs → scaffolding-only report, exit 0 | PASS |
| No actual paper-log reconciliation attempted (operator constraint) | PASS |
| env-check passes on all shipping configs | PASS (5/5) |

## Notes

- The pre-existing Phase-7 `reconcile/` package (`importer`, `comparator`,
  `paper_log_schema`, `slippage_residuals`) is untouched — its tests stay green.
  Phase 10's modules sit alongside it: `replay.py` reuses `importer` for JSONL
  ingestion; the new realism report is a named addition to `report.py`. Phase-7
  matches by `(symbol, timestamp-window)`; Phase 10 keys strictly on
  `candidate_event_id`.
