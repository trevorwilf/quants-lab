# Bowaka v2 Lab — Implementation Summary

## Phases completed

| Phase | Branch | Status |
|---|---|---|
| 0 | `phase-0-freeze-v1-baseline` | merged |
| 1 | `phase-1-v2-skeleton` | merged |
| 2 | `phase-2-bowaka-common` | merged |
| 3 | `phase-3-port-features-schemas-scanner` | merged |
| 4 | `phase-4-comprehensive-simulator` | merged |
| 5 | `phase-5-reporting-diagnostics` | merged |
| 6 | `phase-6-optuna-walkforward` | merged |
| 7 | `phase-7-paper-recon-prep` | merged |
| 8 | `phase-8-scheduler-integration` | merged |
| 9 | `phase-9-review-promotion-gate` | merged |

All phases merged to `dev`. No phase required the 5-cycle failure protocol; per-phase fix loops were small (≤3 cycles each) and applied during the
single-session implementation.

## Tests added per phase (counts incremental)

| Phase | New tests | Cumulative v2 | Cumulative common | v1 regression |
|---|---|---|---|---|
| 0 | 6 (tests/repo) | — | — | 708 (baseline) |
| 1 | 38 v2 unit/integration | 38 | — | 708 |
| 2 | 37 common + 27 v1 shim + 3 repo | 38 | 37 | 735 (708 + 27) |
| 3 | +55 v2 (features, schemas, scanner) | 93 | 37 | 735 |
| 4 | +40 v2 (sim) | 133 | 37 | 735 |
| 5 | +36 v2 (reports + notebooks) | 169 | 37 | 735 |
| 6 | +27 v2 (optuna) | 196 | 37 | 735 |
| 7 | +14 v2 (reconcile) | 210 | 37 | 735 |
| 8 | +7 repo | 210 | 37 | 735 |
| 9 | +15 v2 (promotion) | 225 | 37 | 735 |

**Final pytest counts:**

- `bowaka_v2_lab` tests: **225 passed, 4 deselected** (live_alpaca / slow / live_paper)
- `bowaka_common` tests: **37 passed**
- `bowaka_lab` (v1) tests: **735 passed, 3 skipped, 3 deselected** (Hummingbot Postgres + live)
- `tests/repo/` tests: **16 passed**

## v1 baseline preservation evidence

- **Pre-phase v1 collection:** 711/714 tests collected (3 live_alpaca / slow deselected); **708 passed, 3 skipped**.
- **Post-phase v1 collection:** 738/741 tests collected (3 deselected); **735 passed, 3 skipped**.
- **Delta:** +27 tests from Phase 2's shim-identity regression suite
  (`tests/unit/test_bowaka_common_reexport.py`) which asserts every v1 module
  that was extracted to bowaka_common still resolves and that the imported
  objects are byte-identical (id() match) to their canonical counterparts.
- All 708 pre-existing v1 tests pass without modification.

## Promotion verdict

Mechanical verdict from this lab's evidence alone: **`backtesting_only`** (capped per Report §1.2 / §21).

The verdict is intentionally bounded:

- IEX runs are capped at `research_only`.
- SIP runs without walk-forward holdout artifacts AND paper-vs-sim reconciliation are capped at `backtesting_only`.
- The `decide_suitability` function in `bowaka_v2_lab.promotion.suitability`
  enforces that even with both artifacts present, this lab returns
  `backtesting_only` — promotion to `paper_candidate` or `live_candidate`
  requires an operator decision outside this codebase.

## Known limitations (from [Report §1.2, §15.3 P2])

- The lab does not produce live or paper trades. Promotion to paper / live
  requires SIP-validated walk-forward + paper-vs-sim reconciliation, both of
  which need fresh operator data outside this codebase.
- Reconciliation against real paper logs requires `BOWAKA_V2_PAPER_LOGS_ROOT`
  to be set in the environment; the `live_paper`-marked test is skipped when
  it's absent.
- Phase 3 parity test against the v2 source archive runs only when
  `BOWAKA_V2_SOURCE_ROOT` is set (supports either the parent of `scripts/`
  or the `scripts/` directory itself).
- The simulator's fill model is single-bar deterministic; multi-fill latency
  modelling is left to a Phase 5+ extension.

## §15 remediations applied during port

1. **§8.3** — `CANDIDATE_EVENT_REQUIRED_FIELDS` now includes
   `projected_rvol_gate`, `max_rvol_gate`, `max_range_expansion_gate`.
2. **§8.5** — `_et_minute_of_day` rejects naive timestamps via
   `require_aware_timestamp` (archive silently localised to UTC).
3. **§8.6** — `instrument_gate` fail-closed by default; opt-in via
   `allow_unknown_for_research=True`.
4. **§8.3 (decision)** — `validate_entry_decision` requires
   `reason == "all_gates_passed"` for accepted decisions.
5. **§15.1 P0 (sim/stale-bar)** — stale-bar enforcement runs BEFORE feature
   compute in `scanner.scan_loop`.
6. **§15.1 P0 (sim/portfolio)** — `begin_session` recomputes
   `gross_exposure_dollars` from `open_positions`.
7. **§15.2 P1 (sim/portfolio)** — `gross_exposure_pct = dollars / bankroll`
   (archive returned 0).
8. **§15.1 P0 (sim/broker)** — sim emits canonical broker_reject record via
   `schemas.decisions.build_broker_reject_record`.
9. **§15.2 P1 (sim/strategy_consumer)** — reads `signal_strength` from
   `features.signal_strength` (archive read a non-existent top-level key).
10. **§15.2 P1 (sim/exits)** — `_trading_days_since` uses exchange-calendars
    XNYS sessions, not `pd.bdate_range`.
11. **§15.2 P1 (volume_curve)** — builder excludes current session via an
    explicit assertion.
12. **§15.1 P0 (scanner/state)** — state path resolves via `BowakaV2Paths`.
13. **§15.2 P1 (scanner)** — `max_entries_per_scan` policy caps emitted
    candidates.
14. **§15.3 P2 (hashing)** — strategy-vs-run hash separation in
    `config.hashing`.

## One-line MVP status

`research-grade backtesting platform; paper-trading promotion requires SIP walk-forward + paper-vs-sim reconciliation; live promotion blocked per [Report §21]`
