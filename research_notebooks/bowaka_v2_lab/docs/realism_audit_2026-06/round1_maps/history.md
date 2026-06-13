I now have everything needed. Let me compile the dense report.

## Timeline of audits & remediations

**2026-05-22 — first realism audit** (`docs/audits/2026-05-22_realism_audit.md`). Verdict: research/simulator-development only; "not safe as a production research backtester or optimizer." Found 11 P0 + 10 P1 (§5). Headline P0s: P0-001 active Optuna config claims `current_code_parity` but changes execution/sizing/risk/stop-target (§5 P0-001); P0-002 backtester processes **all scans then exits** — no intraday event loop (§5 P0-002); P0-003 no replayable bars in sample; P0-004 no historical quotes; P0-005 generated config omits `require_adjusted_daily_bars` (§5 P0-005); P0-006 marketable-limit fill uses forward minute-bar highs / fills at full limit (§5 P0-006); P0-007 OCO/protected-position lifecycle collapsed to `bracket_attached=True` (§5 P0-007); P0-008 signal-fade `telemetry_then_active_after_validation` treated as active immediately (§5 P0-008); P0-009 price-chase/halt gates unsimulated; P0-010/011 shallow DQ + parity permits bad data. Shipped: 9-phase plan (§11) — quarantine configs, event-driven sim, quote/fill/OCO realism, content-addressed lineage. Drove the `current_code_parity` vs `intended_realism` two-contract design (`docs/current_code_vs_intended_realism.md`).

**2026-05-23 — re-test after remediations 1&2** (`docs/audits/2026-05-23_realism_audit.md`). Found earlier defects still live: P0-001 broad `except Exception` swallows structural rejections → all-sentinel study reports `status:"ok"`; P0-002 HoldoutGuard closed-interval vs half-open splits; P0-003 preflight DQ/quote probes fail-open under IR; §6.6 preflight capped at 100 symbols. README "Active audit blockers (2026-05-23)" records remediation-3 closures. P1-005 (fill calibration) and P1-009 (paper reconciliation) deferred (need paper logs).

**2026-05-29 — revised audit after notebook-10 output** (`docs/audits/2026-05-29_…revised.md`). New failure mode: every trial scores constant **−1.5** (no-trade penalty = `low_trade_count 1.0 + fill_rate 0.5`, §2.4/§6.6) — "Optuna ran but did not optimize." P0-001 constant-objective surface accepted; P0-002 no-trade folds scored finite; P0-003 incumbent Trial-0 padded (`execution.max_quote_age_seconds`, `max_spread_bps`); P0-004 invalid param relations (`soft>hard`, `target<=stop`); P0-005 CCP skips full-fold preflight; P0-006 daily-adjustment read path defaults raw; P0-007 `objective_minimal` hides diagnostics; P0-008 promotion-evidence semantics unsafe. Memory: shipped as CC Phases 0-3 + Phases 4-7 (`verify-bayesian-fix` / `verify-realism-stress` CLIs).

**2026-05-29 — production_backtester_fix** (`docs/production_backtester_fix.md`): the mirrored prod `bowaka_v2_backtest.py` had a dead ternary (`x if args.synth else x` both → `_synth_*`), so it **always read synthetic $10→$11.95 data → 100% win rate**. Fixed in mirror; operator must apply patch to live source + re-mirror.

**2026-06-07 — intended_realism coverage findings** (`docs/audits/2026-06-07_…coverage_findings.md`, the live investigation). Diagnosed the 4 minute-coverage preflight failures as PIT-over-inclusion mis-attribution; A1 denominator-scoping fix (§10b), `audit_missing_sessions`/`coverage_missing`/`coverage_backfill_present` fixes (§10c, commit e6e3ae4), quote_coverage corrected to honest ~78–92% + gate lowered to 80% (§10g, Option A). Surfaced the **fill-model gap** (§10e–10f): T3 depth/impact fill shipped (§10f Phases 1-3); `fast_realism` mode added (§10j, `eae7b6f`+`eb878ed`); per-scan speed work (§10h matrix is THE lever 47×; §10i further opts).

**2026-06-10/12 — Alpaca fill realism** (`docs/alpaca_fill_realism_implementation_plan.md`, `fill_realism.md`, `PHASE_NOTES/alpaca_fill_realism_phase{0,B}.md`). Closes the **sell-side optimism** (`walk_lot_exit` filled at exact bracket price, 0 bps). PA1-4 data (trades tape 70GB + fine NBBO), PB1-6 sell+buy honest fills + tape-replay oracle, PB5/PC3 measured on real tape, all default-off byte-identical. **Status COMPLETE 2026-06-12**.

## CLOSED items (do not re-litigate)

- **Active Optuna config not parity** (2026-05-22 P0-001): `bowaka_v2_walkforward_optuna.yml` quarantined under `configs/quarantined/`; loader refuses it (README "Active audit blockers 2026-05-22").
- **All-sentinel study reports `status:ok`** (2026-05-23 P0-001): runner raises `OptunaStudyInvalidError` on zero valid trials (README).
- **HoldoutGuard closed-interval** (2026-05-23 P0-002): guard now half-open `[start,end)` (README).
- **Preflight DQ/quote probes fail-open under IR** (2026-05-23 P0-003): now fail-closed.
- **§6.6 100-symbol preflight cap** (2026-05-23): expanded to full per-fold PIT-union (`pit_universe.plan_pit_symbol_union`, uncapped).
- **Frozen contract hashes only YAML** (2026-05-23 P1-002): source_manifest hashes strategy/scanner/features/schemas/backtest.
- **Constant −1.5 objective / no-trade study accepted** (2026-05-29 P0-001/002): shipped Phases 0-3 + `verify-bayesian-fix` CLI (memory `bowaka-v2-bayesian-optimization-fix`).
- **Daily-adjustment read path defaults raw** (2026-05-29 P0-006): `daily_adjustment_for_config` threaded; prod-backtester fix mirrors it.
- **Incumbent Trial-0 padding** (2026-05-29 P0-003): incumbent built from mapped lab config (Phase 2 per memory).
- **Invalid param relations** (2026-05-29 P0-004): search-space v3.
- **CCP skips full-fold preflight** (2026-05-29 P0-005): CCP full-fold preflight added.
- **Production backtester always-synth** (`production_backtester_fix.md`): fixed in mirror; `--lake-root` added; regression test `test_prod_backtester_default_uses_lake.py`.
- **Coverage preflight failures (late_session 35.65%, exit_path 14.96%, audit_missing 1762, coverage_missing)** (2026-06-07 §10b/10c): A1 denominator-scoping shipped (e6e3ae4); `data_quality` preflight now PASSES.
- **quote_coverage gate** (2026-06-07 §10g/Option A): corrected to ~87.8% eligible; gate lowered to 80% in `$2M` config → PASSES.
- **Fill model manufactures liquidity** (2026-06-07 §10e/10f): T3_NBBO_DEPTH fill shipped + validated (§10f Phases 1-3).
- **Sell-side exits fill at exact bracket, 0 bps** (alpaca plan PB1-6): COMPLETE 2026-06-12, default-off byte-identical.
- **Per-scan controller_compat slowness** (2026-06-07 §10h): scan_matrix is the 47× lever (made tractable, not optimized).

## OPEN/DEFERRED items (with stated reason)

- **P1-005 fill calibration / P1-009 paper-vs-sim reconciliation** (2026-05-23/2026-05-29 Phase 6): deferred — require real Bowaka v2 paper logs (README; 2026-05-22 §11 Phase 8). Still the §12 promotion gate for `main`.
- **`intended_realism` infeasible on the `$2M` small-cap universe** (2026-06-07 §10d.1): genuine 95% NBBO coverage needs a ~$50M–$100M ADV floor (25–50× jump → 80–160 large-caps). "No floor gives both the small-cap universe and 95% real quotes." Operator must choose strategy-design path (a/b/c). Memory `intended_realism-denominator-fix`, `fok-fill-model-gap`.
- **Strict FOK ⇒ universe ~0.1–1% executable** (2026-06-07 §10e (3)): the strategy is untradeable as literal FOK; recommendation is `walk_the_book` with a **real depth model the sim lacks** (§10e (5), §10f deferred). Operator decision open.
- **`intended_realism` not yet declared green lake-wide** (2026-06-07 §10, cons #1): 3.42% coverage established only on first 5 sessions; interior-fold confirmation still required (thin 1.6pp headroom).
- **Non-PIT / survivorship-free asset master** (2026-06-07 §10 cons #4): single future-dated 2026-06-05 snapshot, `status=active` for all rows, no listing/delisting dates → `no_daily_history`→"not-yet-listed" attribution is inferential, not PIT-confirmed. Deferred.
- **Ticker-reuse / SPAC identity** (2026-06-07 §10c Check 2 adversarial): 2023 bars may be a different entity than 2026 bars under same symbol — flagged for the survivorship/PIT asset-master work, separate item.
- **SIP migration / halt-LULD feed** (2026-05-22 Phase 9, `sip_migration_runbook.md`): Alpaca exposes no halt/LULD/status endpoint; halt gate disabled via parity sidecar (`2026-06-07_ir2m.parity_sidecar.yaml`, `execution.halt_gate.enabled=false`, risk=scoped). Out of scope — needs another vendor.
- **Full-depth L2 / queue / adverse-selection** (alpaca plan "Out of scope"; 2026-05-22 §8.5): cannot be closed with Alpaca data.
- **Event-driven intraday OCO lifecycle full state machine** (2026-05-22 P0-007): the audit-specified `parent_submitted→oco_attach→unprotected_violation→fallback` machine; unclear how fully shipped — see Claimed-but-worth-rechecking.
- **interior-fold + quote_coverage + survivorship pass** (2026-06-07 §10c net): three explicit "still required before declaring IR green lake-wide."

## Claimed-but-worth-rechecking (partial / default-off / waived fixes)

- **All Alpaca fill-realism knobs are default-off / byte-identical** (`fill_realism.md`; phaseB): tape_replay, `exits.cross_spread/participation_cap/require_fresh_quote`, `execution.fill_model` all default off → legacy engine reproduced exactly. So the **realism improvement does nothing unless a config opts in**, and tape-consuming runs are capped at `research_only` (suitability cap). Recheck: are any production/study configs actually enabling them, or is the honest sell-side still dormant?
- **T3 depth/impact fill only fires when `has_nbbo_depth=True`** (2026-06-07 §10f / §10j): active under `intended_realism` (quote.is_historical) and `fast_realism`; **CCP/IEX/smoke stay legacy "manufactures liquidity" (577 vs 5-share book)**. The dominant realism gap persists in the validated CCP finalist. Recheck which mode any shipped finalist used.
- **quote_coverage "fix" is honesty-lowered, not met** (2026-06-07 §10d adversarial `fix_unsafe`; §10g): gate dropped 95%→80% as a deliberate small-cap floor. The adversary flagged the lower-threshold path (option c) as gaming risk; documented but it means IR runs on a universe where ~22% of signals are unexecutable.
- **Target-side tape clamp** (`fill_realism.md` "See also"; phaseB): before the clamp ~25% of bracket lots filled *better* than legacy. Now uniformly ≤ legacy (PC.3 48 worse/0 better/96 equal) — recheck the clamp didn't over-correct (resting limits never get improvement, but stop aggressors should).
- **Container CCP lab-vs-prod parity golden deferred to PC1, then PC1 still blocked** (phase0 §P0.2c, phaseB PC.1): the golden-diff fidelity gate (Guardrail 4) is **currently non-functional** — `run_production_backtester` appends `--lake-root` but the prod argparse has no such arg → the 4 pre-existing contract-drift test failures (`test_actual_contract_loaded`×3, `test_source_manifest_unchanged`). The byte-identity claim rests on the deterministic suite, not the prod parity golden. Recheck: is the prod-contract re-mirror done?
- **PC.3 full-pipeline A/B never ran** (plan PC3; phaseB): empty PIT universe on scoped window → pivoted to `_pc3_exit_pnl.py` driving the exit engine directly. The end-to-end honest-fill-≪-CCP claim is from a direct-engine probe, not a completed study.
- **§6.6 reconciliation for A1** (2026-06-07 §6.1, §9 Claim C): A1 (denominator-only) shipped and claimed §6.6-compatible (no waiver); literal A2 explicitly NOT green-lit. Recheck the shipped form is A1, not A2.
- **`audit_missing_sessions` 6-ticker decomposition** (2026-06-07 §5.2 provenance caveat): not reproducible from `_pair_dataset.csv`; asserted from a separate lake-audit query.
- **trades-only backfill hash-invisibility** (alpaca plan Guardrail 2; PB6): `trades/` only enters `dataset_hash` when consumed — gated by design. Two tape runs over different trades hash distinctly only after PB6 wiring; recheck the gate is correct.

## Realism mode matrix (per these docs)

Source: `docs/current_code_vs_intended_realism.md`, 2026-06-07 §10j table, phase0 §P0.1, `fill_realism.md`.

| Axis | `current_code_parity` (CCP) | `fast_realism` | `intended_realism` (IR) | `smoke_fixture` |
|---|---|---|---|---|
| Purpose | live code as-written, warts | fast SEARCH (IR semantics, non-blocking) | faithful minute replay, fail-closed | synthetic plumbing |
| Quote fallback (no NBBO) | `zero_spread` synthetic → T0 manufactured | synthetic → participation cap | `require_real` → reject `missing_quote` | `synthetic_calibrated` |
| Fill model | legacy (manufactures liquidity, 577 vs 5-share book) | **T3** honest size+impact | **T3** | legacy |
| Coverage/quote/halt gates | none (warn only) | none (never blocks) | fail-closed (DQ, NBBO, halt) | fail-open |
| Intraday window | `scanner_start_to_scan` (09:45) | `regular_open_to_scan` (09:30) | `regular_open_to_scan` (09:30) | `regular_open_to_scan` |
| Accepted-event sequencing | `pre_submit` (live wart) | `post_submit` | `post_submit` | `pre_submit` |
| Unknown instrument class | `fail_open` | — | `fail_closed` | `fail_open` |
| Halt gate, no status data | fail-open + warn | non-blocking | reject `halt_data_unavailable` | fail-open |
| Startup DQ gate | adjustment-only | invariant adjustment only | all required checks | none |
| Suitability cap | `research_only` | `research_only` | `backtesting_only` | `research_only` |

Notes: `smoke_fixture` is the **default** and the 4th mode (phase0 plan-correction #1). `tape_replay` is an **opt-in knob, NOT a mode** (PB6 decision) layered on any mode, capping the run at `research_only`. Mode behaviors are table-driven via `_SIMULATION_MODE_DEFAULTS` (4 policy fields/mode); a config can pin a single axis explicitly (current_code_vs_intended §intro). Operator workflow: SEARCH under `fast_realism` → `derive_validation_config(validation_mode="intended_realism")` → finalist validate under IR → deploy IR survivors (§10j).

Key file refs (read-only live source line numbers from current_code_vs_intended §1-8): scanner window `bowaka_intraday_scanner.py:671-714`; quote fallback `bowaka_v2_strategy.py:743-748`; accepted-pre-submit `:791-846`; instrument fail-open `bowaka_v2_features.py:473-477`; halt fail-open `:421-430`. Lab fill/exit: `sim/fills.py` (`_t3_depth_impact_fill:582-657`, `simulate_market_fill:394-472`); `sim/exits.py` (`_walk_lot_exit_pandas:377-709`, `_walk_lot_exit_numpy:756-1044`, `walk_lot_exit:1047-1094`, `_mk_exit:1122-1166`); `sim/tape_fill.py` (oracle). DQ gates: `dq_levels.py:346-488,72,80`; `data_quality.py:391,421,442,259`. Preflight: `preflight.py:570,2198`; `walkforward_runner.py:315-381,1899,2198`; `pit_universe.py:5-7,108-109`.