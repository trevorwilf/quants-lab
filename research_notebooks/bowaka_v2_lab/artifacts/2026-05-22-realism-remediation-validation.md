# Bowaka v2 Lab — Realism Remediation 2 — Final validation

**Driving audit:** `docs/audits/2026-05-22_realism_audit.md` (preserved verbatim).
**Plan:** `bowaka_v2_lab_realism_remediation_2_claude_code_prompt.md`.
**Date:** 2026-05-23.
**Status:** all 11 implementation phases (0–10) merged to `dev`; final validation phase complete.

The 2026-05-22 audit found that several P0 items the 2026-05-21 remediation marked GREEN were still defective in code. This second 12-phase remediation rebuilt the simulator event-driven, hardened the data-quality and execution paths, rebuilt Optuna on top of those, and shipped the SIP-migration scaffolding and IEX-caveat hardening. Each phase verified the audit's "verify first" defect-persistence checks before fixing; no fix was taken on faith of the prior remediation's claims.

## 1. Final test counts

The non-live test matrix has three segments. All three exit 0 on `dev`.

| Segment | Result |
|---|---|
| 1 — lab unit + parity (`-m "not live_alpaca and not slow and not live_paper"`) | **709 passed**, 4 warnings |
| 2 — lab integration + reconcile (`--timeout=120 --timeout-method=thread`) | **295 passed**, 1 skipped, 12 deselected, 15 warnings |
| 3 — `bowaka_common` shared-package tests | **97 passed** |

Test-count growth across the remediation: 537 (audit baseline pre-remediation) → 709 unit+parity / 295 integration+reconcile / 97 common at the end of Phase 10.

env-check exits 0 for every shipping config — see `artifacts/phase-11-env-check.json`:

- `bowaka_v2_actual_iex_current_code.yml`
- `bowaka_v2_actual_iex_intended_realism.yml`
- `bowaka_v2_actual_sip_intended_realism.yml`
- `bowaka_v2_actual_iex_current_code_optuna.yml`
- `bowaka_v2_actual_iex_intended_realism_optuna.yml`
- `bowaka_v2_actual_sip_intended_realism_optuna.yml`
- `bowaka_v2_backtest_smoke.yml`

## 2. Per-phase outcomes

Every phase ran the standard procedure: branch off `dev` → implement → run the 3-segment test matrix → merge with `--no-ff` on green; pre-existing unrelated failures documented, no phase merged on a fix-loop-exhausted blocker.

| Phase | Title | Branch | Merge SHA | Tests added | Key acceptance |
|---|---|---|---|---|---|
| 0 | Audit landing, freeze, label, Optuna config quarantine | `phase-0-audit-freeze-and-labels` | `3fa193e` | 4 unit/parity | audit verbatim under `docs/audits/`; `bowaka_v2_walkforward_optuna.yml` quarantined; `simulation_contract` + `suitability_tier` on every artifact; `ParitySidecar` + `config-parity` CLI; Optuna refuses unannotated parity diffs |
| 1 | Actual config import + adjustment enforcement | `phase-1-config-import-and-adjustment` | `228ddcc` | 7 (new) | `MarketDataConfig.require_adjusted_daily_bars` required for realism / parity; `data:` block in frozen contract; three `actual_*` configs generated; `build_adjustment_check()` fails closed for any non-smoke mode |
| 2 | Test infrastructure stability | `phase-2-test-infrastructure` | `963e6b1` | 3 | `pytest-timeout` + default `timeout=60` in pyproject; Makefile test targets; `scripts/run_full_test_matrix.sh`; markers registered |
| 3 | Data-lake hardening — IEX fixture subset + multi-level DQ | `phase-3-data-lake-and-dq` | `3c6df88` | 9 | 1.3 MB real-IEX fixture (7 symbols, ≥20 sessions, real split case); five DQ levels (ingestion / session / replay / feature / quote-status); `dq-report` CLI; content-addressed dataset hash |
| 4 | Event-driven simulator rewrite | `phase-4-event-driven-simulator` | `1d0c31f` | 17 (10 unit + 7 integration) | event queue + dispatcher; portfolio state mutates per event; cadences decoupled; smoke path preserved; **parity-flipping test confirms audit P0-002** — old code did NOT block re-entry after an intraday stop; new code does |
| 5 | Execution / quote / fill realism + RNG + quote-timestamp | `phase-5-execution-realism` | `ea2ca47` | 11 + bowaka_common | sha256 RNG deterministic across processes (P1-001); QuoteRow timestamp (P1-002); price-chase + halt gates (P0-009); tiered fill model T0–T4, T0 hard-fails `intended_realism`; execution-quality report fields |
| 6 | OCO / protected-position lifecycle | `phase-6-oco-protection` | `1670076` | 7 | `Position.protection_state` enum + `ProtectionStateMachine`; `protection_stress` config knob; retry → fallback-stop → flatten paths; `entries_blocked` risk gate; protection metrics in run report |
| 7 | Exit semantics + signal fade + scanner counter | `phase-7-exit-semantics` | `f41ff60` | 8 (33 cases) | `telemetry_then_active_after_validation` now defaults to telemetry (P0-008) — exits never fire without an explicit activation artifact; scanner `signal_emits_per_symbol_today` renamed; portfolio drives a separate `entries_per_symbol_today`; gap-through / same-minute / halt-defer / max-hold edges covered |
| 8 | Optuna rebuild | `phase-8-optuna-rebuild` | `0c1ccc7` | 10 | three contract-parity Optuna configs; `--allow-current-code-parity-study --tier research_only` refusal gate; per-fold preflight with content-addressed cache (P1-006); holdout uses `report.json` metrics (P1-004); content-addressed dataset hash (P1-005); `MetricUnits` Pydantic validator (P1-008); incumbent baseline trial 0; promotion-evidence artifact |
| 9 | Paper-vs-sim reconciliation scaffolding | `phase-9-paper-recon-scaffolding` | `8203e09` | 7 (42 cases) | 10 paper-event Pydantic schemas; importer with strict/tolerant modes; replay in `current_code_parity`; 7 comparators (Jaccard emission, decision-reason confusion matrix, fill price/qty + latency, OCO attempts, exit reason+timing, PnL); per-(spread, ADV, vol) slippage residual calibrator; OCO attach-latency calibrator; opt-in T4 calibrated fill; synthetic fixture for the entire path |
| 10 | SIP scaffolding + IEX caveat hardening | `phase-10-sip-scaffolding-and-iex-caveats` | `cf3cfa2` | 6 (52 cases) | SIP partition path layout + `MarketDataStore` SIP reads; SIP preflight (`sip_data_absent` required DQ check); IEX banner in run report + `feed_caveat: partial_tape_features` on suitability artifacts; `iex__` Optuna study-name prefix + `partial_tape=true` study attr; `IEXPromotionBlocked`; feature-divergence framework |

## 3. P0 / P1 audit-finding closure

Every audit finding has been verified-and-closed in code OR documented as a known gap with explicit fail-closed behavior in the simulator.

| Finding | Title | Status | Closed by |
|---|---|---|---|
| **P0-001** | Active Optuna config is not actual Bowaka v2 parity | **GREEN** | Phase 0 quarantines the old file; Phase 1 generates contract-parity configs; Phase 8 generates the new Optuna configs + refusal gate |
| **P0-002** | Simulator processes exits only after all scans for the day | **GREEN** | Phase 4 event-driven rewrite — verified by the parity-flipping `test_intraday_stop_before_later_scan_blocks_daily_loss_entries` (old behavior wrong, new behavior correct) |
| **P0-003** | Current market-data sample does not contain replayable bars | **GREEN** | Phase 3 commits a 1.3 MB real-IEX 7-symbol fixture subset with manifest + audit + corporate-action partition; deterministic replay snapshot baseline |
| **P0-004** | Real historical quotes are missing, so execution realism is blocked | **AMBER (operator backfill required)** | Phase 5: T0 (no quotes) hard-fails `intended_realism`; `current_code_parity` retains the documented live zero-spread fallback; Phase 9 T4 calibration scaffolding is in place. The mechanics correctly fail closed when realism is requested without quotes; quotes data still absent in the lake |
| **P0-005** | Adjusted daily bar requirement not enforced by generated config | **GREEN** | Phase 1: `require_adjusted_daily_bars` required for realism / parity; contract `data:` block; `build_adjustment_check()` fails closed for any non-smoke mode |
| **P0-006** | Marketable-limit fill model is not realistic | **GREEN** | Phase 5 tiered fill model (T0–T4); T1 fills at touch with ask-size partials and step-up to limit; sub-minute timeout via `PARENT_FILL_TIMEOUT` event; T2 minute-volume participation cap |
| **P0-007** | Protected-position / OCO lifecycle materially simplified | **GREEN** | Phase 6 state machine driven by `OCO_ATTACH_ATTEMPT` / `PROTECTION_CHECK` / `CHILD_FILL`; `protection_stress` knob; fallback-stop + flatten + entries-blocked; metrics in the run report |
| **P0-008** | Signal fade `telemetry_then_active_after_validation` treated as active | **GREEN** | Phase 7: `activation_state` field defaults to `telemetry`; activation requires explicit config OR a signed activation artifact in `artifacts/promotion/` |
| **P0-009** | Price-chase + halt / LULD gates are not fully simulated | **GREEN** (price-chase) / **AMBER** (halt) | Phase 5: price-chase gate at PARENT_ACK, non-tunable. Halt gate is wired but real halt/status partitions are absent — `intended_realism` fails closed with `halt_data_unavailable`; `current_code_parity` matches the live fail-open wart (documented) |
| **P0-010** | Data-quality coverage checks too shallow | **GREEN** | Phase 3 five DQ levels (ingestion / session / replay / feature / quote-status); new required checks added to `_REQUIRED_CHECK_NAMES`; `dq-report` CLI |
| **P0-011** | `current_code_parity` permits bad data by design — must not be optimized | **GREEN** | Phase 8 dispatcher refuses `current_code_parity` Optuna studies unless `--allow-current-code-parity-study --tier research_only` is set; promotion-evidence records the explicit opt-in |
| **P1-001** | Synthetic-quote RNG nondeterministic across processes | **GREEN** | Phase 5: sha256-derived seed over `(run_seed, symbol, scan_ts)`; deterministic-across-subprocesses test added |
| **P1-002** | Quote supplier records request timestamp, not actual quote timestamp | **GREEN** | Phase 5: `QuoteRow.timestamp` added in `bowaka_common.marketdata.store`; supplier returns the row's actual timestamp + correct quote age |
| **P1-003** | Scanner counter incremented on emission rather than fill | **GREEN** | Phase 7: scanner `signal_emits_per_symbol_today` (emit-counter) renamed; portfolio drives a new `entries_per_symbol_today` on PARENT_FILL; both reported |
| **P1-004** | Holdout scoring does not use full report metrics | **GREEN** | Phase 8 holdout uses `report.json` via `fold_result_from_report()` (identical to validation folds); fails closed on missing/corrupt report |
| **P1-005** | Walk-forward dataset hash not content-addressed | **GREEN** | Phase 3 `data/lineage.py` `content_addressed_dataset_hash()` (manifest ‖ sorted partition paths ‖ footer hashes ‖ asset snapshot ‖ adjustment policy ‖ config hash ‖ code manifest hash); Phase 8 wires it into the runner |
| **P1-006** | Walk-forward preflight probes only a small sample | **GREEN** | Phase 8 full-fold preflight evaluates every val/holdout window with content-addressed `(dataset_hash, fold_window, config_hash)` cache; study refuses on any fold missing required coverage |
| **P1-007** | Full integration/reconcile suite needs deterministic CI handling | **GREEN** | Phase 2 default `timeout=60` + `--timeout-method=thread`; `scripts/run_full_test_matrix.sh` matrix driver; Makefile targets |
| **P1-008** | Objective scale and penalty units need validation | **GREEN** | Phase 8 `MetricUnits` Pydantic model rejects mixed units; all terms in decimal returns; `trial.user_attrs["objective_terms"]` breakdown |
| **P1-009** | Actual scanner / live cadence mismatch | **GREEN** | Phase 4 decoupled cadences — `scan_interval_seconds`, `fill_poll_interval_seconds`, `protection_poll_interval_seconds`, `time_stop_check_interval_seconds`; contract `loop_interval_seconds: 5` as default poll cadence |
| **P1-010** | IEX-only optimization should be feed-specific and non-portable | **GREEN** | Phase 10 IEX banner in run report; `feed_caveat: partial_tape_features` on suitability artifacts; `iex__` Optuna study-name prefix + `partial_tape=true` study attr; `IEXPromotionBlocked` |

**Summary:** 21 of 21 P0/P1 findings closed (19 fully green, 2 amber due to data the operator has not yet backfilled — both with code that correctly fails closed).

## 4. Phase-11 verification specifics

- **3-segment test matrix:** `bash scripts/run_full_test_matrix.sh` ran all three segments with JUnit + per-segment logs persisted under `artifacts/test-runs/<utc-iso>/`.
- **env-check 7-config sweep:** all configs exit 0; see `artifacts/phase-11-env-check.json`.
- **Optuna refusal end-to-end:** `cli optuna --config bowaka_v2_actual_iex_current_code_optuna.yml --n-trials 1` *without* the explicit opt-in returned exit 2 and the precise refusal:
  > `Optuna study refused: simulation.mode is 'current_code_parity'. Bayesian optimization on the live-code-with-warts contract is paper-reconciliation-only — pass --allow-current-code-parity-study --tier research_only … See docs/audits/2026-05-22_realism_audit.md §P0-011.`
- **Optuna "with flag" mechanics:** verified by Phase 8 integration tests on synthetic tiny lakes (`test_run_walkforward_study_pins_trial_zero_to_incumbent`, `test_dataset_hash_content_addressed`, `test_objective_term_breakdown_in_user_attrs`, `test_full_fold_preflight_blocks_study_on_missing_coverage`, `test_holdout_uses_report_metrics`). A real-lake 50-trial run against `bowaka_v2_actual_iex_current_code_optuna.yml` is impractical in our Docker-bind-mount environment (estimated 30–60 min for even a single trial × N folds at 100-symbol lake-derived universe); documented limitation, not a defect.
- **Synthetic reconciliation:** `cli reconcile --paper-logs-root tests/fixtures/paper_logs --session-date 2024-09-03` exits 0 and writes `artifacts/reconcile/2024-09-03/report.{json,md}` (scaffolding-only when no `--config` is supplied; the comparators are verified end-to-end by Phase 9 integration tests).

## 5. Phase-11 incidental fixes (committed in this phase)

- `scripts/run_full_test_matrix.sh` auto-detects `/opt/conda/envs/quants-lab/bin/python` when `$PATH python` lacks pytest. Previously the matrix ran against the dependency-free base conda interpreter and exited 1 on every segment.
- `reference/import_config.py` widens the `optuna` purpose's `backtest.start_date` / `end_date` to `2024-01-01..2025-12-31` so the default `train_months=6 + val_months=1 + final_holdout_months=1 = 8` walk-forward plan actually produces splits. The previous 4-month range produced zero splits and `ValueError: walk-forward plan has no splits`. The three `*_optuna.yml` configs were regenerated.

## 6. Known gaps and the suitability cap

The mechanical suitability cap remains **`research_only`** for:

- any `feed: iex` artifact (Phase 10 — IEX is partial-tape; consolidated-tape parameters cannot be inferred);
- any `simulation.mode: current_code_parity` artifact (Phase 1 + Phase 8 — parity reproduces live warts and is paper-reconciliation-only).

Operator-required backfills before any promotion above `research_only`:

1. **SIP-feed bars + SIP quotes**: `intended_realism` SIP currently fails preflight on `sip_data_absent`. With SIP data the existing realism gates (quote coverage, adjusted dailies, full-fold preflight) become satisfiable.
2. **Halt / LULD / status partitions**: `statuses/vendor=alpaca/symbol=…/date=…/…` partitions are absent. `intended_realism` correctly fails on `halt_data_unavailable_when_required`; `current_code_parity` matches the live fail-open wart.
3. **Real paper-trade logs**: only synthetic fixtures exist today. Once real logs land, `cli reconcile --paper-logs-root … --config …` runs the full Phase-9 comparison stack and persists residuals into the slippage / OCO-latency calibrators.

Promotion to `paper_candidate` or `live_candidate` is gated by human-operator review of this validation report, plus signed validation artifacts for SIP-validated walk-forward and paper-vs-sim reconciliation.

## 7. Bottom line

A realism-mode backtest now either runs end-to-end against the real data and produces a substantive, non-stub report, or **fails closed with a precise startup reason** — never a silent stub or a quietly-degraded result. The simulator is event-driven (intraday risk feeds back into later same-day entries), exit / fill / OCO / signal-fade lifecycles match the live contract or correctly fail closed when data is absent, and Bayesian optimization runs only on contract-parity configs with the explicit opt-in. Strategy tuning at validation grade is unblocked the moment a SIP + quotes + halt-status lake is available.
