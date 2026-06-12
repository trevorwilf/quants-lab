# Alpaca fill-realism — Phase 0 (pre-flight + baseline)

**Date:** 2026-06-11 · **Status:** COMPLETE. The Phase-0 before-picture / per-phase
gate is the **green deterministic suite** (`tests/parity` + `tests/unit/sim`); the
container CCP parity golden is **deferred to PC1** (operator decision 2026-06-11),
since it is blocked by pre-existing harness/contract drift and is orthogonal to
fill realism (see §P0.2c).
**Plan:** `docs/alpaca_fill_realism_implementation_plan.md`. Everything here is
read-only / additive; no lake write, no source edits, no study run.

This note is the P0.1 study-safety matrix + P0.2 baseline status + P0.3 scope
decision, plus plan-text corrections found while verifying claims against current
code (8-agent read-only audit).

---

## P0.1 — Study-safety matrix (verified against current code)

| Phase | Writes lake? | Drifts `dataset_hash`? | Invalidates matrix? | Run while study active? | Verified |
|---|---|---|---|---|---|
| P0 | no | no | no | yes | ✅ |
| PA1 (surface bar fields) | no | no | no | yes | ✅ |
| PA2 (trades producer, code) | no | no | no | yes (write code) | ✅ |
| PA3 (fine-NBBO producer, code) | no | no | no | yes (write code) | ✅ |
| PA4 (run backfills) | **yes** | trades=no / fine-quotes=no¹ | no | **NO — re-check guard** | ✅ |
| PB1–PB3 (sell-side exits) | no | no² | no | yes | ✅ |
| PB4 (tape-replay fills) | no | no² | no | yes | ✅ |
| PB5 (fidelity harness) | no | no | no | yes | ✅ |
| PB6 (hash + lattice) | no | **yes (gated, by design)** | no | yes | ✅ |
| PC1–PC2 | no | no | no | yes | ✅ |
| PC3 (smoke study) | **yes** | study only | no | **NO — re-check guard** | ✅ |

¹ Fine quotes **must** land on a path that is a *sibling* of `quotes/` (e.g.
`quotes_fine/`), NOT a new `feed=` under `quotes/`. `_quotes_partitions_hash`
(`lineage.py:247-256`) recursively `rglob`s the whole `quotes/` tree, so anything
written under `quotes/` would drift `quote_partitions_hash`.
² Default-off knobs leave `lab_config_hash` byte-identical (see below). The hash
only changes once PB6 deliberately wires trades consumption.

### Confirmed safety invariants (file:line)

- **Matrix-hash excludes fills/exits → Part B needs NO matrix rebuild.**
  `_MATRIX_HASH_SOURCE_FILES` (`scanner/scan_matrix.py:285-291`) = exactly
  `{features/forming_bar.py, data/suppliers.py, sim/schedule.py,
  universe/builder.py, scanner/event_builder.py}`. `sim/fills.py` / `sim/exits.py`
  are absent; `exits.*` tuned keys intentionally excluded (`scan_matrix.py:374-376`
  + the `compute_matrix_input_hash` docstring `:334-336`). Editing fills/exits
  changes neither the matrix-input hash (`:365`) nor manifest code_hashes (`:1146`).

- **`dataset_hash` composition.** `build_dataset_lineage` (`data/lineage.py:382-394`)
  = 11 components (`lake_manifest_hash, feed, adjustment, date_range,
  symbol_universe_hash, daily_partitions_hash, minute_partitions_hash,
  quote_partitions_hash, assets_snapshot_id, corp_actions_hash, lab_config_hash`).
  - **No trades component** → a `trades/`-only backfill is hash-invisible (PA4).
  - `quote_partitions_hash` = canonical `quotes/` tree only (see ¹).
  - `lab_config_hash` = `canonical_strategy_hash(cfg_dict)` over a strategy-key
    subset `{strategy_id, strategy_version, signals, execution, sizing, risk,
    exits, scanner, session, market_data, universe}` — the `simulation` block is
    **excluded**. A new default-off knob not written into existing YAMLs leaves
    every existing config byte-identical. ⚠️ Knobs under `exits`/`execution` **are**
    in the hashed subset, so a test/overlay YAML that *sets* the knob hashes
    distinctly (intended for new modes); existing configs (knob absent) are safe.

- **Exits never touch the fill model** (the optimistic assumption Part B attacks):
  `exits.py` does not import `fills.py`; a stop fills at exactly `float(stop_price)`
  and a target at exactly `float(target_price)` — 0 bps, full lot, no spread/size
  cap — in BOTH `_walk_lot_exit_pandas` (returns `:611-628`) and
  `_walk_lot_exit_numpy` (returns `:951-968`); `_mk_exit` (`:1122-1166`) leaves
  bracket `slip_bps = 0.0`. `quote_supplier` is already threaded into
  `walk_lot_exit` but consumed only by `_next_bid` (`:337-364`) for discretionary
  exits, never brackets — the PB1 injection point.

- **Buy-side T3 honest tier is reusable for sells.** `_t3_depth_impact_fill`
  (`fills.py:582-657`) is keyword-only and already side-symmetric (sell branch:
  `quote.bid`/`bid_size`, prices down). `has_nbbo_depth` fork at
  `strategy_consumer.py:577-581`, off in CCP, on in fast_realism (always) / IR
  (when `quote.is_historical`).

### Plan-text corrections (claims hold; references to fix)

1. **4 sim modes, not 3** — `smoke_fixture` is the 4th and the **default**
   (`config/models.py:29-62, 85-87`). Suitability caps:
   `smoke_fixture/CCP/fast_realism → research_only`, `IR → backtesting_only`
   (`promotion/suitability.py:131-136`).
2. **Two `max_quote_age_seconds`** — `MarketDataConfig:174` (=15, the one PB.3
   wants) vs `ExecutionConfig:298` (=5). `quote_model.resolve_quote` also defaults 5.
3. **`fill_model` is a brand-new field** — no `fill_model` exists on any config
   model today (PB.4 adds it; it is not an extension of an existing enum).
4. **`ExitsConfig` is `extra='forbid'`** (`models.py:18-19`) → new knobs
   (`cross_spread`, `participation_cap`, `require_fresh_quote`) MUST be declared
   fields with current-behavior defaults.
5. **Stale exit line numbers** — real: `_walk_lot_exit_pandas:377-709`,
   `_walk_lot_exit_numpy:756-1044`, `walk_lot_exit:1047-1094`, `_mk_exit:1122-1166`,
   `_next_bid:337-364`.
6. **Weekly-refresh path** — wrapper is at repo root `scheduled_weekly_refresh.ps1`
   (not `scripts/`); the idle probe is `scripts/check_study_active.py`.

---

## P0.2 — Baseline ("before-picture") status

The plan's P0.2 ("freeze CCP/fast_realism/IR fill+exit on the synthetic SIP lake
via the existing harness") does not match reality on two counts, both measured:

### (a) Synthetic SIP fixture is NON-VIABLE as a fill/exit oracle — measured
Running the lab backtester (`run_lab_backtester`) over the committed synthetic SIP
fixture (`tests/fixtures/sip_synthetic_lake`) per mode yields:
`current_code_parity → 0 candidates / 0 trades`; `fast_realism → 0 / 0`;
`intended_realism → StartupDataQualityError (zero-universe DQ gate)`. The fixture
was built for cutover-gate tests (preflight/NBBO/halt/divergence), not signal
generation — the integration test itself says "synthetic bars need not find
alpha." A per-mode end-to-end golden here would freeze nothing and guard no exit.

### (b) The real before-picture = the GREEN deterministic test suite (host)
Every code path Part B touches is already pinned by deterministic unit/parity
tests that DO exercise stops/targets/per-mode fills:

- **Exit fills:** `tests/parity/test_walk_lot_exit_numpy_parity.py`,
  `test_close_lots_until_window_boundary.py`,
  `tests/integration/test_gap_through_stop_fills_at_open.py`.
- **Bracket pricing:** `tests/parity/test_bracket_pricing_actual_fill.py`.
- **Per-mode entry fills:** `tests/unit/sim/test_fast_realism_fill.py`,
  `tests/unit/test_fills_t3_depth_impact.py` (incl. sell branch + **default-off
  byte-identity**).

**Baseline run (2026-06-11):** `tests/unit/sim` + `tests/unit/test_fills_t3_depth_impact.py`
+ `tests/parity` → **299 passed, 4 failed in 54.4s**. All 4 failures are
**pre-existing, orthogonal contract-mirror drift** (`test_actual_contract_loaded`
×3 + `test_source_manifest_unchanged`): the frozen prod contract
(`bowaka_v2_config.yaml`, `bowaka_v2_strategy.py`) diverges from live source —
nothing to do with fill/exit. `git status` confirms `reference/` is untouched by
this work. **Per-phase gate going forward:** these same 299 stay green and no NEW
failure appears (the 4 drift failures are the known red baseline until a deliberate
contract re-mirror).

### (c) Container CCP lab-vs-prod parity golden — BLOCKED (pre-existing)
Attempted `phase0_capture_golden.py` in `ql-jupyter` (lake `/opt/market_data_cache`,
study idle). It fails immediately: `run_production_backtester` (`parity/runner.py:175-176`)
unconditionally appends `--lake-root`, but the prod script
`reference/source_strategy/scripts/bowaka_v2_backtest.py` (argparse `:416-428`) has
no such argument →
`bowaka_v2_backtest.py: error: unrecognized arguments: --lake-root /opt/market_data_cache`.
`/quants-lab` is a bind-mount of the host repo (`compose:123 - ./:/quants-lab`), so
container code == host code. This is the same drift the 4 failing tests flag, and
it makes the `verify_golden_diff.py` fidelity gate (Guardrail 4) currently
non-functional — independent of this plan. **DECISION (2026-06-11): DEFER to PC1.**
The container parity golden is not captured in P0; the **green deterministic suite**
(§P0.2b) is the Phase-0 before-picture and the per-phase byte-identity gate. The
prod-contract drift (these 4 tests + the `--lake-root` gap) is to be resolved as a
separate maintenance task (re-mirror) before PC1 re-enables the parity golden.

---

## P0.3 — Data-scope decision (for PA2/PA3/PA4)

- **Active study config:** `configs/_local_container_matrix.yml` (notebook-10 pins
  it; `MODE_OVERRIDE=current_code_parity`, scan-matrix on, n_jobs=16,
  `shared_root=/opt/market_data_cache`). Span **2023-11-27 → 2026-05-20** (~29.8 mo),
  walk-forward train=21 / val=1 / holdout=5 → 3 folds.
- **Universe:** per-session PIT build (`universe/builder.py`), no fixed list —
  `min_adv_dollars=250000`, price `$1–$20`, `operating_equity`. The operational
  ceiling = **~3677 symbols** that actually have minute + quote data.
- **⚠️ Feasibility blocker:** intraday SIP data (minute bars AND quotes) exists only
  for **2025-08 → 2026-06 (~11 months)** — daily bars span the full range, but
  **trades/fine-quotes can only be fetched for the recent ~11 months × ~3677
  symbols**, not the full 29.8-month study window.
- **Size estimate (PA4):** combined trades + fine-quotes ≈ **70 GB (low) / 265 GB
  (mid) / 800 GB (high)** on `/opt/market_data_cache` — a 13–50× lake-size increase
  vs. the current ~5.3 GB intraday footprint. No committed fetch-time baseline →
  **PA4 must MEASURE on a single-symbol/single-month scoped `--start` probe** before
  any full-scope download, and verify disk headroom first.
- **Lake location:** the real lake is container-only (`/opt/market_data_cache`); the
  host `research_notebooks/market_data` is empty (1.1 MB). All PA4 work runs in the
  container.
- **PA2 precondition confirmed:** `fetch_trades` / a `trades/` layout slot /
  `store_trades` / a runner `--trades` stage are genuinely absent today — PA2 is
  purely additive.

### Study-safety NOW: **NO STUDY ACTIVE**
`scripts/check_study_active.py` → IDLE / rc=1 (repeated); only a ~492 MB idle
Jupyter kernel; overnight study + Top-N sweep finished (artifacts 02:21 / 04:36);
no lake write since 2026-06-07. PA4 / PC3 must re-run the guard immediately before
they write.
