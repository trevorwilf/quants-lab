# Alpaca fill/sell-order realism — implementation plan

**Status:** PLAN ONLY — nothing here has been executed. Authored 2026-06-10.
**Goal:** download every fill-relevant data type Alpaca offers, then implement a
**symmetric, honest fill model (buys _and_ sells)** that uses both the data we
already store (Tier 1) and the newly downloaded data (Tier 2), moving the sim
materially closer to `intended_realism` (IR) on this universe.

**How to use this doc:** execute the phases in order. Each phase lists *goal ·
files · approach · study-safety · tests · acceptance*. Before any phase that
writes the lake, confirm **no study/notebook run is active** (see Guardrails).
Tick the checklist as you go.

```
[x] P0  pre-flight + golden baseline  (2026-06-11 — gate = deterministic suite; container golden deferred to PC1; see PHASE_NOTES/alpaca_fill_realism_phase0.md)
[x] PA1 surface already-written bar fields (no download)  (2026-06-11 — with_microstructure opt-in flag; default byte-identical)
[x] PA2 trades-tape producer (code)  (2026-06-11 — fetch_trades + trades/ slot + trades_between reader + --trades-only; default-off)
[x] PA3 finer-NBBO producer + exchange codes (code)  (2026-06-11 — fetch_quotes_fine -> quotes_fine/ sibling + exchange/tape coercion; canonical quotes/ byte-identical; default-off)
[x] PA4 run scoped backfills (operator)  (FULLY DONE 2026-06-12. TRADES: 27873 partitions, 70 GB, 5-way parallel + TRADE_FLUSH_EVERY_SESSIONS=2. FINE-QUOTES (4/min): all 11 months 2025-08..2026-06 done ~14:51, 27855 partitions / 4.5 GB, 441506 (symbol,session) writes, 1078 failed = 0.244% transient-network gaps (weekly refresh heals them). Parity across datasets: quotes_fine 27855 ≈ quotes 27876 ≈ trades 27873. Peak RAM during the 11-way fine fetch ~127 GB/157; no OOM. RAM released to 3 GB used after.)
[x] PB1 sell-side spread-crossing exits (Tier 1)  (2026-06-11 — exits.cross_spread default-off; fill=min(bracket, bid*(1-hs/1e4)); numpy==pandas parity via fuzzer; byte-identical off)
[x] PB2 sell-side size cap + impact (Tier 1)  (2026-06-11 — exits.participation_cap default-off; capped-participation sqrt-impact blended fill mirroring buy-side T3; numpy==pandas fuzzer parity; byte-identical off)
[x] PB3 exit quote-age / no-quote handling (Tier 1)  (2026-06-11 — exits.require_fresh_quote default-off; stale/absent NBBO widens give-up 2x half-spread; _XFill params refactor; numpy==pandas parity; byte-identical off)
[x] PB4 trade-tape fill oracle / tier (Tier 2)  (CORE 2026-06-11; HOOKS DONE + byte-identical 2026-06-12. SELL hooks: exits.py _XFill fill_model/trades_supplier/tape_window/tape_participation + _tape_replay_bracket + _bracket_fill kind=stop/target threaded through both walks/dispatcher/exit_driver/backtester. BUY hooks: fills._tape_replay_fill (market=no ceiling, marketable_limit=ask*(1+slip) ceiling) wired run_backtest→run_one_scan→consumer.consume→fills, lazy trades_supplier. Orchestration gate suppliers.make_trades_supplier_for_config (None unless fill_model=="tape_replay") in cli_runners+fold_context+walkforward. 10 routing tests (test_tape_replay_routing.py) PASS; v2 gate 313/4 = 0 regressions. SKIPPED byte-identical: parity/runner, backtest_runner, reconcile/replay.)
[x] PB5 fill-fidelity validation harness (Tier 2)  (DONE 2026-06-12 — scripts/_validate_fillmodel.py samples real (symbol,minute) points from the SIP lake + compares the legacy fill (100% at bar px, 0 bps) to replay_tape_fill over the REAL prints. MEASURED (artifacts/pb5_fill_fidelity.txt): $4k order SELL full-fill=82% slip median -2.4/p10 -24 bps, BUY full-fill=79% median +4.2/p90 +28 bps; $25k order SELL full-fill=33% (fill-frac 0.49!) — legacy over-fills ~2x. Size-sensitive + correct. Read-only.)
[x] PB6 dataset_hash + mode-lattice + suitability integration  (DONE 2026-06-12. Gated trades_partitions_hash (2026-06-11). Mode-lattice DECISION: tape_replay stays an OPT-IN knob (no new mode, not default-on in IR) — promote into IR after PB5. Suitability: decide_suitability caps a tape-consuming run at research_only regardless of mode/feed (manifest gains fill_model.consumes_trade_tape via build_run_manifest extras). derive_validation_config gains opt-in enable_tape_replay=True (sets execution+exits fill_model). Honesty guard: trades_partitions_available + loud warning when tape_replay requested on a lake with no trades/. 4 PB6 tests + 10 routing tests PASS; v2 gate 327/4 = 0 regressions.)
[x] PC1 parity / golden-diff / regression sweep  (DONE 2026-06-12 — broad host regression byte-identical: bowaka_v2_lab tests/unit+tests/parity = 1592 pass (1578 baseline + 14 new tape tests) / 8 PRE-EXISTING fail (4 contract-drift source_manifest/actual_contract + 2 prod_backtester mirror + 2 notebook_bootstrap nb10/13 — all untouched by this work) / 1 skip = 0 regressions. bowaka_common tests = 136 pass. Golden-diff/lab-vs-prod parity still blocked by the pre-existing prod-contract mirror drift, same as P0.2 — orthogonal.)
[x] PC2 docs + PHASE_NOTES  (DONE 2026-06-12 — data_lake_layout.md + fill_realism.md + sip_migration_runbook.md done 2026-06-11; fill_realism.md updated with PB5/PC3 measured results + the target-side optimism note; PHASE_NOTES/alpaca_fill_realism_phaseB.md added.)
[x] PC3 scoped end-to-end smoke study  (DONE 2026-06-12 — full-pipeline backtest A/B BLOCKED by an empty PIT universe on a scoped window (universe-screening issue ORTHOGONAL to the fill model; the CCP run completes cleanly, just emits 0 candidates). PIVOTED to scripts/_pc3_exit_pnl.py: drives the REAL engine exit path walk_lot_exit over real bars+tape, legacy vs tape_replay, ENTRY held fixed. MEASURED (artifacts/pc3_exit_pnl.txt): after the target-side clamp — $8k notional → tape PnL 27.6% WORSE than legacy; $30k → 38.1% worse (per-lot give-up mean -$7.39 → -$38.28). Confirms honest exits ≪ legacy + size-sensitive. TARGET CLAMP DONE 2026-06-12 (operator decision): a take-profit is a resting limit sell → _tape_replay_bracket fills kind="target" AT the limit (bracket price), not the ≥target through-VWAP; stops + marketable buys stay aggressor-VWAP. Removed the prior optimism (was 23/94 better) → now uniformly ≤ legacy (48 worse / 0 better / 96 equal).)
```

---

## Background (why this work)

Two separate price engines exist, and they are not equally realistic:

- **Buys** route through the tiered fill model `sim/fills.py`
  (`detect_execution_tier` → T0/T1/T2/T3). The honest **T3 depth+impact** tier
  already exists (real touch + `participation·minute_volume` cap + √-impact) but
  is **default-off in `current_code_parity` (CCP)** and **on in `fast_realism`/IR**.
  `has_nbbo_depth` is the fork (`sim/strategy_consumer.py:577-581`).
- **Sells/exits never touch the fill model.** `sim/exits.py:walk_lot_exit`
  (numpy `_walk_lot_exit_numpy` / pandas `_walk_lot_exit_pandas`) fills a stop at
  *exactly* `stop_price` and a target at *exactly* `target_price` — **0 bps
  slippage, no spread crossing, no size cap, always the full lot**. This is the
  single most optimistic assumption in the simulator.

`fast_realism` already made the **buy** side honest (non-blocking T3); the missing
symmetric half is the **sell** side. Separately, Alpaca offers data we don't yet
fetch (the **trades tape**, intra-minute **NBBO ticks**) that would let us *verify*
fills rather than only model them.

**In scope:** Tier 2 acquisition (download), then Tier 1 + Tier 2 modeling.
**Out of scope (cannot be closed with Alpaca data):** full depth-of-book/L2,
official halt/LULD + auction prints (needs another vendor), and the 95%
`quote_coverage` gate (a universe/ADV-floor decision, not data). See the
investigation summary / audit `docs/audits/2026-06-07_intended_realism_coverage_findings.md`.

---

## Guardrails (apply to EVERY phase)

1. **Study-safety is paramount.** A running study / notebook-10 reads the lake
   per-fold and keys on `dataset_hash`; mutating the lake mid-run corrupts it
   (see `[[bowaka-v2-weekly-refresh-scheduled-task]]`). Rules:
   - **Code edits** (producers, fill model) are always safe to *write*.
   - **Running a backfill** (PA4) or a **new-mode study** must wait until no
     study is active. Reuse the weekly-refresh guard pattern
     (`scripts/scheduled_weekly_refresh.ps1` study-idle check) before launching.
2. **`dataset_hash` composition** (`data/lineage.py:382-394`,
   `build_dataset_lineage`): `lake_manifest_hash · feed · adjustment · date_range
   · symbol_universe_hash · daily_partitions_hash · minute_partitions_hash ·
   quote_partitions_hash · assets_snapshot_id · corp_actions_hash ·
   lab_config_hash`. Consequences:
   - **A `trades/`-only backfill is INVISIBLE to the current hash** (no trades
     component; the `--quotes-only` pattern skips the shared manifest write so
     `lake_manifest_hash` is unchanged) → additive and study-safe to *land*.
   - **Re-writing `quotes/` drifts `quote_partitions_hash`** → corrupts running
     studies. **Finer quotes MUST go to a SEPARATE path** (e.g. `quotes_fine/`),
     never overwrite the canonical 1/min `quotes/` tree.
   - `lab_config_hash` is a component → **every new fill knob must default to
     current behavior** so existing resolved configs hash byte-identically.
   - **Correctness follow-up (PB6):** once the model *reads* trades/fine-quotes,
     `build_dataset_lineage` MUST add a `trades_partitions_hash` (gated so it only
     changes the hash when the resolved sim config actually consumes trades),
     else two runs over different trades share a hash.
3. **Scan-matrix hash is NOT affected by fill/exit edits.**
   `_MATRIX_HASH_SOURCE_FILES` (`scanner/scan_matrix.py:285-291`) =
   `features/forming_bar.py, data/suppliers.py, sim/schedule.py,
   universe/builder.py, scanner/event_builder.py`. `sim/fills.py` and
   `sim/exits.py` are excluded (and `exits.*` tuned keys are intentionally outside
   the hash, `scan_matrix.py:374-376`). **Part B needs no matrix rebuild.** Re-confirm in P0.
4. **Parity / byte-identical-at-base.** Each new behavior is a **new knob
   defaulting OFF**. CCP / `fast_realism` / IR existing results must stay
   byte-identical; the golden-diff fidelity gate (`scripts/verify_golden_diff.py`)
   and `tests/parity/*` + `tests/unit/sim/*` must stay green. Capture a golden
   baseline first (P0.2). Document any intentional golden change with a changelog
   comment (per CLAUDE.md).
5. **Suitability cap.** New research-fidelity modes are capped at `research_only`
   until validated under IR (mirror the `fast_realism` → `derive_validation_config`
   → IR-validate → deploy workflow).
6. **Determinism.** Certified/deployment runs stay `n_jobs=1`.
7. **Env.** Alpaca SIP creds in `/quants-lab/.env`. Native lake at
   `/opt/market_data_cache` via `MARKET_DATA_ROOT` (10× vs the 9p mount;
   per-month flush). Always **scope backfills** with `--start` / a symbol set
   (the trades tape is large). Run tests with `C:/Python312` +
   `PYTHONPATH="src;../bowaka_common/src"` (no `make`).

---

## Phase 0 — Pre-flight + golden baseline  *(no data, no study impact; safe anytime)*

**Goal:** lock the guardrails empirically before touching anything.

- **P0.1 — Hash audit.** Confirm (read-only) that `_MATRIX_HASH_SOURCE_FILES`
  excludes `sim/fills.py`/`sim/exits.py`, and enumerate the `dataset_hash`
  components. Produce a one-page "study-safety matrix" (which ops drift the hash /
  invalidate matrices). *(Most of this is already established above — verify it
  still holds against current code.)*
- **P0.2 — Golden baseline.** Use the existing golden harness
  (`scripts/phase0_capture_golden.py` → `scripts/verify_golden_diff.py`) to freeze
  the current fill+exit behavior for **CCP, fast_realism, IR** on a small fixture
  (the synthetic SIP lake, `tests/fixtures/build_sip_synthetic_lake.py`). This is
  the regression oracle for every Part-B change.
- **P0.3 — Data scope decision.** Fix the symbol set (= the walk-forward PIT
  universe for the active study config) and date range (train+val+holdout span)
  for trades + fine quotes. Estimate row counts / parquet size / fetch time
  (trades tape is ~orders of magnitude larger than quotes; AAPL ≈ 11k NBBO
  ticks/3min, trades larger still).

**Acceptance:** safety matrix written; golden baseline captured + committed
(gitignored artifacts backed up); scope + size estimate recorded.
**Effort:** S.

---

## PART A — Tier 2 data acquisition ("download it first")

> Code in PA1–PA3 is safe to write anytime. **PA4 writes the lake → run only with
> no active study.** All producers mirror the existing `--quotes-only` parallel
> pattern (`marketdata/runner.py:214-261`).

### PA.1 — Surface already-written bar fields  *(NO download; study-safe)*

**Goal:** expose `vwap` + `trade_count`, which are already written to parquet but
not returned by the read API — a free minute-level volume signal for the impact model.

- **Files:** `bowaka_common/marketdata/store.py` (`_BAR_COLUMNS:19`,
  `minute_bars`/`daily_bars:175-201`); `_coerce_bar_row` already coerces them
  (`backfill.py:375-402`).
- **Approach:** add `vwap`,`trade_count` to the read column set behind an opt-in
  arg (don't change the default tuple shape that downstream code unpacks); add a
  typed accessor. No re-fetch.
- **Tests:** `tests/unit/...` read-API returns the new columns; existing readers
  unaffected.
- **Acceptance:** `minute_bars(..., with_microstructure=True)` returns vwap/tc;
  default call unchanged.  **Effort:** S.

### PA.2 — Trades-tape producer  *(code only; study-safe to write)*

**Goal:** fetch + store the per-trade tape (the single biggest untapped fill-realism lever).

- **Files (new + edits):**
  - `backfill.py`: `fetch_trades` (mirror `fetch_quotes`,
    `StockTradesRequest`/`get_stock_trades` — currently absent),
    `_coerce_trade_row` (price, size, conditions, exchange, tape, timestamp),
    `make_alpaca_trades_fetcher`.
  - `layout.py`: a `trades/` slot —
    `trades/vendor=alpaca/feed=sip/symbol=<S>/year=<Y>/month=<M>/part.parquet`
    (mirror `quotes_path:184-203`).
  - `store.py`: `store_trades` + a `trades_between(symbol, t0, t1)` reader.
  - `runner.py`: a `trades_cfg = config.get("trades", {})` stage + a `--trades` /
    `--trades-only` flag with its own `run_id` (mirror `quotes_only:214-261`);
    **default-disabled** in `config/marketdata_backfill.yml`.
- **Approach:** parallelized (GIL-bound fetch, like the quote backfill); per-month
  flush; resume-skip covered (symbol, month). Decide storage granularity: raw
  trades vs a session-bounded subset (raw is most faithful for the oracle; size↑).
- **Tests:** schema/coercion; reader empty-when-absent (mirror
  `test_store_quotes_returns_empty_when_no_partition.py`); parallel-matches-serial;
  runner stage wiring; `--trades-only` skips daily/minute + shared manifest write.
- **Acceptance:** `bowaka-v2-lab`/runner `--trades-only` writes a `trades/`
  partition + reader round-trips, all default-off.  **Effort:** M.

### PA.3 — Finer-NBBO producer + exchange codes  *(code only; study-safe to write)*

**Goal:** optionally store sub-minute NBBO + capture per-quote exchange/tape codes,
**without drifting the canonical `quotes/` hash**.

- **Files:** `backfill.py` `_sample_session_nbbo:576-594` (add an N-samples/min or
  raw-tick option), `_coerce_quote_row:496-524` (also keep `bid_exchange`,
  `ask_exchange`, `tape` — currently dropped); `layout.py` (a **separate**
  `quotes_fine/` slot or a `granularity=` partition dim — DO NOT overwrite
  `quotes/`); `store.py` reader for the fine path.
- **Approach:** canonical 1/min `quotes/` tree stays byte-identical (so
  `quote_partitions_hash`/running studies are unaffected); fine data is additive
  in a new path. Exchange/tape codes are additive columns.
- **Tests:** fine-path round-trip; canonical `quotes/` byte-identical (hash a
  fixture before/after); coercer keeps new columns.
- **Acceptance:** fine quotes land in a separate path; `quote_partitions_hash`
  on the canonical tree unchanged.  **Effort:** M.

### PA.4 — Run the scoped backfills  *(OPERATOR step — NO active study)*

**Goal:** actually download trades (PA2) + fine quotes (PA3) for the P0.3 scope.

- **Approach:** verify no study active → run `--trades-only` and the fine-quote
  backfill scoped to the universe/date range → verify counts in the manifest +
  add a `catalog.py` entry → record runtime/size in `PHASE_NOTES`.
- **Study-safety:** trades-only is additive (hash-invisible) but still heavy;
  fine quotes go to the separate path. Prefer running during a study lull anyway.
- **Acceptance:** `trades/` (+ `quotes_fine/`) partitions present for the scope;
  catalog/manifest updated; spot-check a symbol-day round-trips.  **Effort:** M (mostly wall-clock).

---

## PART B — Tier 1 + Tier 2 implementation ("use the data we now have")

> All Part B is **default-off + parity-guarded** and needs **no matrix rebuild**
> (Guardrail 3). Code is safe to write while a study runs; running a *new-mode
> study* is a separate, study-gated step.

### PB.1 — Sell-side spread-crossing exits  *(Tier 1; stored 1/min NBBO)*

**Goal:** a sell stop/target fills at the **marketable bid**, not magically at the
bracket price. Highest ROI — attacks the most optimistic assumption with data
already in the lake.

- **Files:** `sim/exits.py` (`walk_lot_exit`, `_walk_lot_exit_pandas` ~`:578-684`,
  `_walk_lot_exit_numpy`, `_mk_exit` ~`:1141-1153`, `_next_bid`); a new knob
  `exits.cross_spread` in `config/models.py` (**default off**). The quote supplier
  is already wired into exits in quote-aware modes.
- **Approach:** stop fill = `min(stop_price, bid·(1−half_spread_bps))` (sell-side
  analog of the buy T3 touch); set `exit_slippage_bps` to the realized give-up
  instead of 0. Off → byte-identical bracket fills.
- **Tests:** new behavior unit tests; `tests/parity/test_walk_lot_exit_numpy_parity.py`
  + `test_close_lots_until_window_boundary.py` stay green; golden-diff unchanged
  with knob off.
- **Acceptance:** knob-off byte-identical to P0.2 golden; knob-on stops fill at the
  bid with non-zero slippage.  **Effort:** M.

### PB.2 — Sell-side size cap + impact  *(Tier 1)*

**Goal:** a full-lot sell can't all print into one thin minute — cap + walk it down.

- **Files:** `sim/exits.py` (partial-lot, multi-bar liquidation path — exits are
  currently single-fill full-lot); reuse the buy-side impact helper from
  `sim/fills.py` `_t3_depth_impact_fill` (`participation_cap·minute_volume` +
  √-impact); knob `exits.participation_cap` / share `minute_volume_participation_frac`
  (default 0.10). New knob gates the whole behavior **off**.
- **Approach:** liquidate `min(remaining, cap·minute_vol)` per bar, carry the
  remainder forward, apply impact per slice. Decide linear vs √ (buy uses √).
- **Tests:** partial-liquidation unit tests; numpy/pandas parity preserved;
  golden-diff unchanged off.
- **Acceptance:** knob-on produces multi-bar partial exits with impact; off
  unchanged.  **Effort:** L (exit engine currently assumes atomic full-lot fills).

### PB.3 — Exit quote-age / no-quote handling  *(Tier 1)*

**Goal:** exits behave consistently with IR when there's no fresh NBBO at the exit
minute (today they still fill cleanly).

- **Files:** `sim/exits.py` + the exit quote supplier; reuse `max_quote_age_seconds`
  (`models.py:174`). Knob `exits.require_fresh_quote` (default off).
- **Approach:** stale/absent bid → widen the give-up, defer, or fall back to
  bar-low per a documented policy (match the buy-side `quote_fallback_policy`
  semantics). 
- **Tests:** stale-quote exit unit test; golden-diff off unchanged.
- **Acceptance:** documented, knob-gated stale-quote exit behavior.  **Effort:** S–M.

### PB.4 — Trade-tape fill oracle / tier  *(Tier 2; needs PA.2/PA.4)*

**Goal:** replay the **actual trades** to compute the achievable VWAP + fill
fraction for a given size at a given time — the most faithful fill obtainable
without L2. Applies to **entries and exits**.

- **Files:** new `sim/tape_fill.py` (consume `store.trades_between`); hook into
  `sim/fills.py` (`detect_execution_tier` → a new `tape_replay` route) and the
  PB.1/PB.2 exit path; `config/models.py` `fill_model="tape_replay"` (or a new sim
  sub-mode). Default unchanged.
- **Approach:** for a marketable order of `q` shares at `t`, accumulate trades in
  `[t, t+window]` until `q` filled (or window expires → partial/no-fill); fill
  price = size-weighted VWAP of consumed prints; for a sell-stop, only count
  prints at/through the trigger. Decide the absorption window.
- **Tests:** synthetic-trades fixture → deterministic VWAP/fraction; falls back
  cleanly when trades absent.
- **Acceptance:** tape-replay fills reproduce a hand-computed VWAP on a fixture;
  default modes unaffected.  **Effort:** L.

### PB.5 — Fill-fidelity validation harness  *(Tier 2)*

**Goal:** quantify how much closer each change brings us to reality. *(The earlier
`scripts/_validate_fillmodel.py` scratch script is gone — rebuild it.)*

- **Files:** new `scripts/_validate_fillmodel.py` (mirror the §10f study: N real
  $X first-emit orders, conservative stress).
- **Approach:** for each real order, compare modeled fill (CCP / T3 / PB.1-2
  sell-side / PB.4 tape-replay) vs the **actual trades tape** ground truth; report
  fill-fraction, slippage, impact distributions per model. This is the
  "instrument → measure → adversarially verify" evidence (`[[deep-dive-rigor-approach]]`).
- **Acceptance:** a fidelity report table (modeled vs tape-actual) the operator
  can read to choose the production fill model.  **Effort:** M.

### PB.6 — dataset_hash + mode-lattice + suitability integration  *(correctness)*

**Goal:** make the new realism a first-class, correctly-hashed, deployable mode.

- **Files:** `data/lineage.py` (add `trades_partitions_hash` / fine-quote hash to
  `components`, **gated** so it only changes the hash when the resolved sim config
  consumes trades — Guardrail 2 follow-up); `config/models.py` + the mode lattice
  (decide: a new mode vs extending `fast_realism`/IR with sell-side honesty);
  `derive_validation_config`; suitability caps; optional new DQ check
  (`data_quality.py`/`dq_levels.py`) for trades-tape coverage if IR should require it.
- **Open decision:** does sell-side honesty become *default-on within IR*
  (changing IR's golden — document it) or stay an opt-in knob? Recommend opt-in
  first, then promote into IR once PB.5 validates it.
- **Tests:** lineage hash changes only when trades consumed; mode-resolution +
  suitability tests; `derive_validation_config` round-trip.
- **Acceptance:** a run using the new fills hashes distinctly; `research_only`
  cap holds until IR-validated.  **Effort:** M.

---

## PART C — Integration, parity, docs

- **PC.1 — Parity sweep.** Full `tests/parity/*` + golden-diff + the lab-vs-prod
  parity notebook (`notebooks/13_lab_vs_production_parity.ipynb`) + regression;
  confirm every default-off path is byte-identical to P0.2.  **S–M.**
- **PC.2 — Docs.** [~ 2026-06-11: data_lake_layout.md (trades/+quotes_fine/), new fill_realism.md, sip_migration_runbook.md producers section, memory all DONE; consolidated PHASE_NOTES at plan-end.] Update `docs/sip_migration_runbook.md` (new producers),
  `docs/data_lake_layout.md` (`trades/`, `quotes_fine/`), a new
  `docs/fill_realism.md` (the sell-side + tape model), and a `PHASE_NOTES/`
  entry; update memory `[[bowaka-v2-fok-fill-model-gap]]`.  **S.**
- **PC.3 — Scoped smoke study.** Run a small end-to-end study under the new mode
  on the synthetic SIP lake first (`tests/fixtures/build_sip_synthetic_lake.py`),
  then one scoped real-lake fold (no active study) — confirm honest fills produce
  sane PnL **≪ CCP** and the report's optimistic-fills caveat is no longer needed
  for that mode.  **M.**

---

## Open design decisions (settle during execution)

1. **New mode vs extend IR/fast_realism** with sell-side honesty (recommend opt-in
   knob first → promote into IR after PB.5).
2. **Impact model** for exits: linear vs √ (buy uses √); participation-cap value.
3. **Tape-replay absorption window** (seconds/minutes to fill a marketable order).
4. **Finer-quote storage:** N-samples/min vs raw ticks (fidelity vs size).
5. **Trades-tape DQ gate:** make IR require trades coverage, or keep trades as
   pure opt-in fidelity?
6. **Storage budget** for the trades tape across the full universe/date span.

## Dependency / study-safety matrix

| Phase | Depends on | Writes lake? | Drifts dataset_hash? | Invalidates matrix? | Run while study active? |
|---|---|---|---|---|---|
| P0 | — | no | no | no | yes |
| PA1 | — | no | no | no | yes |
| PA2 | — | no (code) | no | no | yes (write) |
| PA3 | — | no (code) | no | no | yes (write) |
| PA4 | PA2,PA3 | **yes** | trades=no / fine-quotes=no (separate path) | no | **no** |
| PB1–PB3 | P0,(PA4 opt) | no | no¹ | no | yes (write) |
| PB4 | PA4 | no | no¹ | no | yes (write) |
| PB5 | PA4,PB1-4 | no | no | no | yes |
| PB6 | PB1-5 | no | **yes (gated, by design)** | no | yes (write) |
| PC1–PC3 | all | PC3 only | PC3 study only | no | **PC3: no** |

¹ default-off knobs leave `lab_config_hash` unchanged; the hash only changes once
PB6 wires trades consumption (intentional).

---

## Recommended execution order (sessions)

`P0 → PA1 → PA2 → PA3 → PA4(operator) → PB1 → PB5(first pass, Tier-1 only) →
PB2 → PB3 → PB4 → PB5(full) → PB6 → PC1 → PC2 → PC3`.

PB5 runs **twice** — once after PB1 to validate the cheap Tier-1 sell-side win in
isolation (highest ROI, fastest evidence), then again after PB4 with the tape oracle.
