# Bowaka v2 lab — final realism-remediation validation

**Branch:** `phase-z-final-realism-validation` (off `dev`)
**Date:** 2026-05-21
**Status:** all closing checks pass; remediation complete.

The 11-phase realism remediation (audit 2026-05-21) is complete and merged to
`dev`. This is the consolidated post-Phase-10 validation — verification only, no
code changes.

## 1. Full test suite

`pytest tests -m "not live_alpaca and not slow and not live_paper"`:

**677 passed, 1 skipped, 12 deselected, 0 failed.**

- 1 skipped: the Hummingbot-PostgreSQL test (no DB in the test env).
- 12 deselected: `slow` / `live_*`-marked tests (notebook papermill, live-data).
- bowaka_common: 84 passed; repo-level tests: 20 passed (verified in Phase 6).

Test-count growth per phase: 314 (P0) → 377 (P1) → 392 (P2) → 413 (P3) →
452 (P4) → 482 (P5) → 522 (P6) → 541 (P7) → 564 (P8) → 634 (P9) → 677 (P10).

## 2. env-check on every shipping config

All 5 `configs/bowaka_v2_*.yml` pass (`status: ok`, exit 0):
`bowaka_v2_backtest_smoke.yml`, `bowaka_v2_intended_realism.yml`,
`bowaka_v2_research_iex_plumbing.yml`, `bowaka_v2_research_sip.yml`,
`bowaka_v2_walkforward_optuna.yml`.

## 3. Realism backtest end-to-end

`run-backtest --config configs/bowaka_v2_intended_realism.yml` →
**exit code 2**, with the precise startup reason:

> `intended_realism run aborted: 1 required data-quality check(s) failed:
> coverage_missing: the requested universe x date range resolved to ZERO
> (symbol, session) pairs — no market data to test`

This is the **correct, accepted Phase-Z outcome**: a realism-mode run either
produces a substantive report or fails closed with a precise DQ/coverage/parity
reason. The realism config is `feed: sip`; the in-repo lake holds only
`feed: iex` bars, so the SIP universe resolves to zero symbols and the Phase-2
data-quality gate fails the run closed — exactly as designed. It never produces
a silent stub.

## 4. import-actual-config round-trip

`import-actual-config --out /tmp/regen.yml --feed sip` →
**byte-identical** to `configs/bowaka_v2_intended_realism.yml`.

## 5. Phases merged to `dev`

| Phase | Branch | What | Merge |
|---|---|---|---|
| 0 | phase-0-realism-contract-and-modes | Simulation-mode contract, frozen strategy contract, Optuna quarantine | 994db21 |
| 1 | phase-1-realism-config-parity | Config-schema parity with live Bowaka v2 | 6376a8f |
| 2 | phase-2-realism-data-lineage-and-dq | Content-derived dataset lineage, data-quality gate | f6a73f4 |
| 3 | phase-3-realism-pit-universe | Point-in-time universe builder | 3738d22 |
| 4 | phase-4-realism-intraday-replay | Full calendar-aware intraday scanner replay | 17cc442 |
| 5 | phase-5-realism-portfolio-and-risk | Position-id multi-lot portfolio, risk-gate parity | 30d814f |
| 6 | phase-6-realism-fills-and-quotes | Historical quotes, realistic fill model | b965ba4 |
| 7 | phase-7-realism-intraday-exits | Minute-path per-lot exit lifecycle | ebc97f2 |
| 8 | phase-8-realism-reporting-and-promotion | Substantive report + content-inspecting promotion gate | 790bbcc |
| 9 | phase-9-realism-optuna-rebuild | Optuna rebuilt on the realistic simulator | 4c72a88 |
| 10 | phase-10-realism-reconciliation-scaffold | Paper-vs-lab reconciliation framework (scaffolding) | 07a19ef |

## 6. Audit P0 status

| P0 | Item (per remediation-prompt phase mapping) | Phase | Status |
|---|---|---|---|
| P0-001 | Stop-ship trigger / mode contract | 0, 1 | GREEN |
| P0-002 | Config schema parity | 1 | GREEN |
| P0-003 | One-scan-per-day → full intraday replay | 4 | GREEN |
| P0-004 | (not assigned to a phase in the remediation prompt) | — | AMBER |
| P0-005 | Synthetic universe → point-in-time universe | 3 | GREEN |
| P0-006 | Scanner bar-window / cadence | 4 | GREEN |
| P0-007 | Symbol-keyed portfolio → multi-lot | 5 | GREEN |
| P0-008 | Execution / fill realism | 6 | GREEN |
| P0-009 | Daily-bar-only exits → intraday lifecycle | 7 | GREEN |
| P0-010 | Risk-state parity | 5 | GREEN |
| P0-011 | Placeholder dataset lineage / data-quality | 2 | GREEN |
| P0-012 | Quote realism | 6 | GREEN |
| P0-013 | Broken Optuna search space / config | 1, 9 | GREEN |
| P0-014 | Risk-gate parity (`max_concurrent` from sizing, ADV aggregate) | 5 | GREEN |
| P0-015 | Stub report / promotion-by-file-existence | 8 | GREEN |

**14 of 15 P0 items GREEN. P0-004 AMBER:** the remediation prompt does not map a
P0-004 to any phase, and the source audit file (`bowaka_v2_lab_realism_audit.md`)
is not present in this repo, so its exact text could not be verified here. By
elimination it is most plausibly the paper-vs-live reconciliation item — which is
deliberately delivered as **scaffolding only** (Phase 10) per the binding
operator constraint (no paper logs supplied). The operator should cross-check
P0-004 against the audit document.

## 7. Operator-facing next steps

The realism machinery is complete and green, but **realism-grade runs need data
the in-repo lake does not yet hold**:

1. **Backfill a SIP-feed lake.** The lake currently holds only `feed: iex` bars.
   `intended_realism` / `current_code_parity` runs fail closed on coverage until
   SIP daily + minute bars are ingested. (`smoke_fixture` runs work today on
   synthetic data — plumbing only.)
2. **Backfill quotes.** There is no `quotes/` partition tree; Phase 6 wired the
   reader + synthetic fallback but (per operator constraint) added no quote
   ingestion job. Realism-mode quote-coverage gating will fail until quotes are
   backfilled.
3. **Paper reconciliation (Phase 10) is scaffolding only.** Once real paper-trade
   logs exist, `cli reconcile --paper-logs-root <path> --session-date <date>`
   runs the full compare against a `current_code_parity` replay.
4. **Promotion cap.** The mechanical suitability cap remains `backtesting_only`;
   promotion to `paper_candidate` / `live_candidate` requires an operator
   decision plus SIP-validated walk-forward + paper-recon evidence.
5. **Working-tree note:** `configs/bowaka_v2_walkforward_optuna.yml` carries an
   uncommitted 1-line edit (`optuna.walkforward.final_holdout_months: 1 → 5`)
   that predates Phase 10 and was authored outside the remediation — left
   uncommitted for the operator to keep or revert.

## 8. Bottom line

A realism-mode backtest now either runs to completion with a substantive,
non-stub `report.md` + `report.json`, or fails closed with a precise startup
reason — never a silent stub. The lab simulates the *intended* Bowaka v2 strategy
(`intended_realism`) and can reproduce the *live code as written*
(`current_code_parity`) for reconciliation. Strategy tuning at realism grade is
unblocked the moment a SIP + quotes lake is available.
