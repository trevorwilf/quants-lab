# bowaka_v2_lab — Realism & Completeness Roadmap (2026-06)

> **What this is.** A consolidated, actionable roadmap for making `bowaka_v2_lab` as
> close to live-trading reality as possible, plus a completeness evaluation of what the
> lab tests today and what Alpaca data could still be incorporated. It answers the
> discovery brief: *evaluate the lab vs the live bowaka v2 strategy, find realism gaps /
> bugs / invalid tests, and lay out a phased plan.*
>
> **Provenance / how it was produced.** This synthesizes a 16-agent read-only audit
> ("Round 1 maps", 2026-06-12) covering every lab subsystem, the three live-strategy
> contract mirrors, the test tree, the audit history, and two Alpaca data-catalog
> research passes. The raw per-subsystem maps live in
> [`round1_maps/`](./round1_maps/) and are the evidence base for every claim below
> (file:line refs throughout trace back to them).
>
> **Verification status.** The Round-1 maps were produced by reading the *actual current
> code end-to-end*, so the behavioral specs are high-confidence. The **Leads** (suspected
> bugs / realism gaps) are code-grounded but were **not yet adversarially re-verified** —
items below are tagged accordingly:
> - `✔verified` — read directly from code in a Round-1 map; behavior is as stated.
> - `⚠lead` — code-grounded suspicion; verify before acting.
> - `↑note` — design/data fact (e.g. an Alpaca API property) carried from research.
>
> **Round 2 (adversarial verification) is now DONE (2026-06-13).** The planned finder +
> skeptic pass ran over the §9 lead shortlist (17 leads, 34 read-only agents, each
> reproduced against the real code/lake where possible). Verdicts are folded into §9 and
> the full evidence is in [`round2_verification.md`](./round2_verification.md). Net: the
> critical PIT lookahead and the fill/parity gaps were **confirmed and reproduced**, while
> **6 suspicions were cleared** (4 overstated → the lab's fail-closed gates actually hold,
> 2 refuted → the design is correct). Round-2 verdict tags:
> - `✅confirmed` — reproduced; real and bites a real run.
> - `🟡bounded` — real, but only bites a narrow path (mode/config) — see note.
> - `🟠overstated` — mechanism real but a downstream guard prevents it biting; defense-in-depth only.
> - `❌refuted` — not a real defect on any reachable path.
>
> **Scope guardrail.** Discovery only — no code was changed to produce this. Nothing
> here is implemented yet.

---

## 0. Verdict (executive summary)

`bowaka_v2_lab` is, structurally, a **serious and unusually disciplined** backtester:
event-driven intraday loop, content-addressed dataset lineage, holdout guards, a
two-contract realism model (`current_code_parity` vs `intended_realism`), fail-loud DQ
gating, and an enormous test tree (538 files). A long sequence of prior audits
(2026-05-22 → 2026-06-12) closed most of the original P0 defects (see §1).

**`✅` Round-2 added a 4th, and arguably the most serious, confirmed truth:**

0. **The scanner reads one full minute of *future* price into every entry decision.**
   Alpaca minute bars are START-of-interval stamped (empirically 09:30…15:59 on the real
   lake), and the forming-bar cutoff is inclusive (`<= scan_ts`), so the bar stamped *at*
   `scan_ts` — which covers `[scan_ts, scan_ts+60s)` — is consumed at decision time.
   Reproduced on real code: a +49% intrabar move inside the forming minute flows straight
   into `last_price`/`ema_distance`/`current_return`/`close_location`. This is a genuine
   **lookahead that inflates every backtest, in every mode**, and it is biased toward the
   high-velocity minutes this momentum screen selects. **New #1 priority.** (§3.1, §9 L1)

But three further structural truths cap how much you can currently trust a result:

1. **The default fill model still manufactures liquidity.** `✅confirmed` The honest fill
   paths (tape-replay, T3 depth/impact, cross-spread exits) are all **default-OFF and
   capped at `research_only`**; the legacy engine fills far beyond displayed
   book depth and exits at the *exact* bracket price with zero slippage (both reproduced —
   §9 L2, L11). The production winner (trial #3155) was selected under
   `current_code_parity`, i.e. the liquidity-manufacturing model. (§2)

2. **`intended_realism` is infeasible on the current lake**, because the strategy's
   halt gate needs halt/LULD data and **Alpaca serves no historical halt/LULD at all**,
   and because genuine ≥95% NBBO coverage is impossible on a $250k-ADV microcap
   universe. The lab correctly fails closed — but that means the most realistic mode
   cannot run end-to-end today. (§2.4, §5.2)

3. **Real-data fidelity is essentially untested.** ~510 of 538 tests are synthetic or
   pure-math; the ~15–20 real-lake tests are nearly all skip-guarded and contribute
   **zero assertions** on this machine / CI. There is **no executing test** that
   compares lab fills/PnL to the live strategy on real bars, nor any real-tape
   fidelity test for the tape-replay model. The operator's standing distrust of
   synthetic validation is fully borne out by the census. (§6)

Everything else is either already-closed (§1), a correctness lead to verify (§9),
a parity divergence between sim and the live strategy (§4), unused Alpaca data that
would raise realism (§5), or masking/silent-fallback debt (§7) and dead code (§8).

The phased plan is in **§10**.

---

## 1. Already closed — do NOT re-litigate

From the audit history (`round1_maps/history.md`). These were real P0/P1 findings in
earlier audits and have shipped fixes; treat them as settled background:

- **Active Optuna config not parity** → `bowaka_v2_walkforward_optuna.yml` quarantined;
  loader refuses `quarantined/` paths. `✔verified` (loader.py).
- **All-sentinel study reported `status:ok`** → runner raises `OptunaStudyInvalidError`
  on zero valid trials.
- **HoldoutGuard closed-interval leak** → now half-open `[start,end)`.
- **Preflight DQ/quote probes fail-open under IR** → now fail-closed.
- **§6.6 100-symbol preflight cap** → expanded to full per-fold PIT-union (uncapped).
- **Frozen contract hashed YAML only** → `source_manifest` now hashes
  strategy/scanner/features/schemas/backtest.
- **Constant −1.5 / no-trade study accepted** → Phases 0-3 + `verify-bayesian-fix` CLI.
- **Daily-adjustment read path defaulted raw** → `daily_adjustment_for_config` threaded.
- **Incumbent Trial-0 padding** → incumbent built from mapped lab config.
- **Invalid param relations (`soft>hard`, `target<=stop`)** → search-space v3.
- **CCP skipped full-fold preflight** → CCP full-fold preflight added.
- **Production backtester always read synthetic** (dead `if args.synth` ternary →
  100% win rate) → fixed in mirror + `--lake-root` + regression test.
- **Coverage preflight failures (late_session/exit_path/audit_missing)** →
  denominator-scoping fix (A1) shipped; data_quality preflight passes.
- **Sell-side exits filled at exact bracket, 0 bps** → Alpaca fill-realism plan PB1-6
  shipped (default-off, byte-identical at base) — *the mechanism exists but is dormant;
  see §2.1*.

> ⚠ **Recheck (claimed but verify):** the lab-vs-prod **parity golden is currently
> non-functional** — `run_production_backtester` passes `--lake-root` but the frozen prod
> `bowaka_v2_backtest.py` argparse historically didn't accept it (the 4 pre-existing
> `test_actual_contract_loaded` / `test_source_manifest_unchanged` failures). Commit
> `3b260b0` ("re-mirror contract source-manifest after prod backtester lake fix") may have
> closed this — **confirm the 4 tests are green and the golden runs** before trusting any
> byte-identity claim. (history.md "Claimed-but-worth-rechecking")

---

## 2. The central realism gap — the fill / liquidity model

This is where the lab is furthest from reality and where a fix most changes results.

### 2.1 Honest fills exist but are dormant (`research_only`, default-off)
`✔verified` (sim_fills.md, history.md, tests.md)

The realism machinery built across §10f and the Alpaca fill-realism plan is real, but:
- `execution.fill_model` / `exits.fill_model` default **`legacy`**; `tape_replay` only
  fires if a trades supplier is wired *and* the tape is non-empty, else silently falls
  back to legacy (byte-identical).
- `exits.cross_spread` / `participation_cap` / `require_fresh_quote` all default **off**;
  the default exit `_bracket_fill` returns `(bracket_price, None)` — **exact bracket,
  zero slippage** (`exits.py:553-554`).
- T3 honest depth/impact fill only fires when `has_nbbo_depth=True`, i.e. under
  `intended_realism`/`fast_realism`. **CCP / IEX / smoke stay on the legacy
  liquidity-manufacturing path.**
- Any tape-consuming run is capped at `research_only` by `decide_suitability`.

**Consequence:** the production finalist (#3155), chosen under `current_code_parity`,
was scored with the liquidity-manufacturing legacy model. The honest model has never
gated a shipped result.

**Action:** decide the intended operating contract for *selection* (not just
validation). Options: (a) make `fast_realism` (honest participation/depth, non-blocking)
the **search** default and validate finalists under a tape-replay pass; (b) re-score the
existing finalists under honest fills and compare ranks. See §10 Phase 2.

### 2.2 The legacy fill model fabricates depth — specific bugs
`⚠lead` (sim_fills.md, sim_core.md) — **highest-value leads to verify first**

- **T1 cent-walk over-fill** (`fills.py:825`): the marketable-limit fill walks one
  cent per level toward the limit and takes `int(size_at_touch*cap)` shares **at every
  penny level** (loop bound 100). A single quote's displayed `ask_size` is thus treated
  as re-available up to 100×. **No test asserts total fill ≤ displayed size.** This is
  the core over-fill bug and matches the prior `fok-fill-model-gap` memory (577sh filled
  vs 5sh book).
- **Zero displayed size → unlimited fill** (`fills.py:804-808`): when `ask_size`/`bid_size`
  is 0, the fill takes the **entire** requested qty at `limit_price`, `is_partial=False`.
  No-size becomes infinite liquidity.
- **T3 `max` not `min`** (`fills.py:622`): `fillable = min(qty, int(max(touch_size,
  cap_shares)))` — using `max` means the participation cap can never tighten the fill
  *below* the displayed touch size; "depth" can't actually constrain.
- **Missing-ADV → unconstrained fill** (`fills.py:491-493`): `liquidity_proxy_shares=None`
  fills the full qty; tiny proxies floor to 0 → `no_liquidity`. Asymmetric and wrong for
  microcaps.
- **Synthetic quotes carry fabricated sizes** (`quote_model.py:124`): `synthetic_calibrated`
  hard-codes `bid_size=ask_size=10_000`; `zero_spread` sets size 0.0 — both then drive
  the T1/T3 fill logic under CCP/smoke.

### 2.3 Quote/depth realism vs Alpaca's actual SIP microstructure
`↑note + ⚠lead` (alpaca_micro.md, data.md)

- **Odd-lot contamination of NBBO size.** On SIP, `bs`/`as` are **share-denominated and
  include odd-lot / BOLO quotes** — sub-100 sizes are routine and are *not*
  protected-NBBO depth. Any model that treats displayed size as accessible round-lot
  depth **over-estimates liquidity**. The lab's 1-quote-per-minute prevailing-NBBO sample
  (`backfill.py:590-608`) inherits this: median ask_size ≈ 100sh kills realistic
  $4k orders (prior finding). **Action:** when modeling protected fills, filter to
  round-lot quotes / treat sub-100 as odd-lot, and stop treating displayed size as full
  depth.
- **1/min quote resolution loses intrabar spread + size at the fill instant**
  (`backfill.py:590-608`). The fine-quote producer (`quotes_fine/`, 4/min) exists; decide
  whether the fill model should consume fine quotes at the actual fill timestamp instead
  of the prevailing-minute sample.
- **No execution latency anywhere** (`fills.py:863,939`): `fill_time_seconds` hard-coded
  `0.0`; the fill is synchronous at `scan_ts`. Quote age gates the *entry* but there is no
  decision→fill latency. The live strategy is a 5s wall-clock REST poller — fills land
  seconds later. `⚠lead`.
- **Entry timestamp = scan_ts, not the actual fill minute** (`strategy_consumer.py:822,
  836`): the exit walk then skips bars up to the scan minute, ignoring the early adverse
  path of a fill that lands minutes later. `⚠lead`.

### 2.4 `intended_realism` is blocked by missing halt data
`✔verified` (history.md, alpaca_micro.md)

The strategy's halt gate is enabled; `intended_realism` fails closed at the DQ preflight
because the lake has **no `statuses/` partitions** — and **Alpaca exposes no historical
halt/LULD endpoint at all** (`statuses`/`lulds` are streaming-only; Alpaca's own FAQ
points users to the Nasdaq website for halt history). The notebook pins
`MODE_OVERRIDE='current_code_parity'` for exactly this reason. **Until halt history is
imported from an external source (Nasdaq Trader halt files), IR cannot run end-to-end.**
See §5.2 and §10 Phase 4.

### 2.5 Tape-replay eligibility — does it filter trade conditions?
`⚠lead` (sim_fills.md, alpaca_micro.md)

`replay_tape_fill` (`tape_fill.py:52-132`) consumes prints requiring only
`timestamp/price/size` columns and applies a participation fraction; **no trade-condition
filter is described.** Raw SIP trades include odd-lot (`I`), average-price (`B`/`W`),
derivatively-priced (`4`), out-of-sequence (`Z`/`L`), and auction (`O`/`M`/`Q`) prints
that are **not executable continuous liquidity**. If the oracle counts them, it
**over-fills** against the tape. Also `tape_participation` defaults `1.0`, letting a
single large print absorb 100% of one trade's size. **Action:** decode conditions via
`/v2/stocks/meta/conditions/trade` and exclude ineligible prints before VWAP/size
accounting (see §5.4). **Verify** whether the producer already drops these.

---

## 3. Data realism & point-in-time correctness

### 3.1 PIT bar-stamping convention is unasserted (lookahead risk)
`⚠lead` — **high priority** (scanner.md, prod_scanner.md)

The forming-bar aggregation is inclusive: it consumes every minute bar with
`timestamp <= scan_ts` (`session_minute_window_cache.py:194`, `scan_matrix.py:685`,
`_numba_scan_features.py:284`). **Nothing anywhere asserts the stamping convention.**
If Alpaca minute bars are **interval-START stamped** (their documented convention is
start-of-interval labels), then the bar stamped at `scan_ts` covers
`[scan_ts, scan_ts+60s)` — i.e. the scanner sees a full minute of **future** price
action at decision time. This would silently inflate every backtest. **Action:** pin the
convention with a dedicated test and, if start-stamped, exclude the in-progress bar
(`< scan_ts`, not `<=`) or shift the cutoff. This is the most dangerous single
correctness question in the lab.

### 3.2 Matrix bakes premarket bars vs the policy window
`⚠lead` (scanner.md)

The scan-matrix builder fetches from **04:00 ET with no policy lower bound** and
cumulates session open/high/low/volume from bar 0, while the live/legacy `scan_loop`
supplier starts at `intraday_window_start` (09:45 ET default). The matrix's cumulative
features therefore include premarket, **diverging from the non-matrix path** — and the
runtime debug-assert re-fetches via the *raw* supplier, so it would **not catch** this.
Since the matrix is the 47× perf lever the real studies depend on, a silent
matrix-vs-legacy divergence here would taint results. **Verify** with a policy-windowed
parity test.

### 3.3 Two `ema_slope_prior` definitions
`⚠lead` (scanner.md, data.md, prod_scanner.md)

`forming_bar.py:123` computes `ema_slope_prior = ema_prior/ema_lag3 - 1` (ratio) while
`suppliers._daily_cache_row_from_prior:367` computes `(ema_prior - ema_lag3)/3` (absolute
÷3). Whichever populates `cache_by_sym` decides the `ema_slope_gate` and the score's `es`
term. The live `bowaka_v2_features.py:107` uses the **ratio** form — so the supplier path
may diverge from the live contract. **Verify** which path feeds the scanner and reconcile
to the live definition.

### 3.4 Survivorship / PIT asset master is not real PIT
`✔verified + ⚠lead` (config_universe.md, history.md)

- The asset master is a **single future-dated snapshot** (2026-06-05), `status=active`
  for all rows, **no listing/delisting dates** → "not-yet-listed" is inferred from
  `no_prior_bar`, not confirmed. Ticker-reuse / SPAC identity (a 2023 symbol ≠ the 2026
  symbol) is unhandled.
- `_status_active("")` treats blank/missing status as **active** (`builder.py:447`) →
  the delisting/survivorship gate is a silent no-op when status is absent.
- `min_history_trading_days: 45` (live contract) is **not enforced** in the PIT builder;
  ADV averages whatever <20 prior bars exist with no minimum-history guard
  (`builder.py:276`).

**Action:** ingest Alpaca corporate-actions + per-date asset snapshots to build a real
PIT/survivorship master (see §5.3); enforce the 45-day minimum.

### 3.5 Adjustment correctness
`✔verified + ⚠lead` (data.md, config_universe.md)

- **Minute bars are always RAW** (`backfill.py:333`) even when the run needs split
  adjustment; the $1–$20 price gate and intrabar stops run on raw minute prices while
  daily features may be split-adjusted → **mixed adjustment within one decision** on
  in-window split days. `⚠lead`.
- **Dividend adjustment is never actually applied**: `require_adjusted_daily_bars`
  collapses to `split_adjusted` (`adjustment.py:22-26`); the two contract flags map to the
  same string. Alpaca *does* offer `adjustment=all` (split+dividend) — the lab just
  doesn't use it. `✔verified`.
- `daily_adjustment="raw"` is the default across suppliers (`suppliers.py:127`,
  `cached_suppliers.py:88`, …); a caller that forgets `daily_adjustment_for_config(cfg)`
  silently computes ATR/EMA/RVOL on raw daily bars. Only the separate DQ gate catches it.

### 3.6 `net_return_pct` is a decimal, not a percent
`✔verified` (optuna_core.md)

`objective.py` names the field `_pct` but stores `(final-init)/init` (decimal). Correct
today, but a future "×100 fix" would silently 100×-inflate the objective or trip
`MetricUnitsError`. Rename / document. Low severity, high trap value.

---

## 4. Sim ↔ live-strategy parity divergences

The sim must reproduce the **live** strategy (`bowaka_v2_strategy.py`), not an idealized
one. Round-1 found several places where the sim is *more* sophisticated than live — which
is itself a realism error (the backtest credits behavior the live bot doesn't have).

`⚠lead` unless noted (prod_strategy.md, prod_execution.md, strategy_consumer/sim_exits maps)

- **Live has no intraday time-stop and no signal-fade.** `exits.time_stop.exit_time=15:30`
  and the whole `signal_fade` block are **config-declared but unwired** in the live
  strategy — it only does `max_hold_days`. The **sim implements both** time-stop and
  signal-fade exits. → The backtest exits positions the live bot would hold. **Decide:**
  either wire these live, or disable them in the parity sim. `✔verified` (live side).
- **Live ignores three risk caps the sim enforces.** `risk.strategy_slice_loss_pct`,
  `max_stopouts_per_day`, `stop_trading_after_consecutive_stopouts` are declared in YAML
  but **consumed nowhere** in the live strategy; the sim enforces them via
  `risk_gates.py`. → The sim is more risk-constrained than live. `✔verified`.
- **`daily_loss` kill behaves differently.** Live only **refuses new entries** when the
  daily-loss threshold trips (no mid-day flatten); the sim's `daily_loss` kill reads
  `daily_unrealized_pnl` which is only refreshed at EOD/`update_mtm`, so intraday SCANs
  see stale (often 0) unrealized PnL → the kill **under-fires intraday**. Two different
  behaviors, neither matching a true mid-day risk stop. (sim_core.md:57)
- **Prod backtester ≠ live entry breadth.** The mirrored `bowaka_v2_backtest.py` (the
  parity oracle's prod side) takes only the **top-1 candidate per scan** (`backtest:174`),
  uses **bar low/high as the bid/ask** when no quote supplier (and lake runs wire
  `quote_supplier=None`, `backtest:489`), and uses a fixed synthetic `±0.1%` exit spread.
  So the "production parity" reference itself manufactures fills and enters one name per
  scan. **The parity oracle's prod side needs hardening before its verdicts mean much.**
  `✔verified`.
- **Contract→config mapper omits universe filters.** `allowed_exchanges`, `exclude_otc`,
  `ticker_blocklist`, and all `exclude_etf/etn/...` flags are **not mapped** from the live
  contract into the lab config (`import_config.py:177-183`); the PIT builder uses its own
  hardcoded defaults instead, and `config_diff` only diffs keys present on both sides, so
  the omission is **invisible to the parity gate**. The entire `score:` and
  `historical_features:` contract sections aren't modeled in lab config at all. `⚠lead`.
- **Live sizing/closure uses no fees or slippage.** `close_position_v2` realized PnL is
  pure `(exit-entry)*qty` (`strategy:1402`); OCO prices round to 2 decimals (materially
  shifts effective stop/target on $1–3 microcaps). The sim must match (or both are
  unrealistic — better: model fees/commissions on both sides explicitly). `✔verified`.
- **Live offline quote fallback fabricates a perfect quote** (`strategy:872-876`):
  `quote_supplier=None` → bid==ask==signal_price, spread 0, age 0 → quote/price-chase
  gates always pass. The sim must **not** inherit this. `⚠lead`.

### 4.1 Walk-forward methodology
`⚠lead` (optuna_core.md)

- **No embargo/purge gap**: `val_start == train_end` exactly; prior-day ATR/EMA baselines
  carry into validation day 1 (standard WF leakage concern, unaddressed).
- **`step_months` is dead**: the parameter exists but is never wired from config; folds
  always step by `val_months`, so train windows overlap heavily → folds are highly
  correlated, which **inflates apparent stability and deflates the fold-variance penalty**.
- **Sampler seed hard-coded `1337`** ignoring `run.seed` (read but only stored in
  metadata) → no config-driven multi-seed robustness.
- **Parallel runs are nondeterministic**: `WorkerSpec.sampler_seed`/`n_startup_trials`
  are passed but unused; workers race on shared TPE storage; per-worker trial-delta
  counts double-count. Contradicts the determinism focus.
- **Single-fold plans get a zero variance penalty** → over-trust a 1-fold result.

---

## 5. Completeness — Alpaca data not yet used (and what each buys)

The lab today consumes Alpaca **bars** (1m raw, 1d raw/split), **prevailing-NBBO quotes**
(1/min + 4/min fine), and **trades** (raw tape, 70GB). The catalog research
(`alpaca_catalog.md`, `alpaca_micro.md`) surfaces these unused / under-used products:

### 5.1 Auctions endpoint — official open/close prints `↑note`
`GET /v2/stocks/auctions` (SIP only) returns the **official opening/closing auction
prices** per primary exchange. The lab currently uses daily-bar O/C, which are the
first/last *continuous* trades and **differ from the auction price**. **Buys:** realistic
MOO/MOC fill modeling, correct official open/close for gap and EOD-mark logic
(addresses the EOD_MARK daily-vs-minute mark divergence in sim_core.md:53). **Effort:**
new producer + lake partition; medium.

### 5.2 Halts / LULD — the `intended_realism` unblocker `↑note` **(external data)**
Alpaca has **no historical halt/LULD** (streaming-only). To run IR end-to-end you must
import **Nasdaq Trader halt files** (or a third-party feed) into a `statuses/` partition.
Resume can be partially inferred from reopening-auction prints, but **onset and LULD bands
cannot** be derived from trades/quotes. **Buys:** the entire `intended_realism` mode
becomes feasible (today it fail-closes). **Effort:** external ingestion + schema + DQ
wiring; high but high-value. This is the gating dependency for the most realistic mode.

### 5.3 Corporate actions — survivorship & adjustment `↑note + ⚠`
`GET /v1beta1/corporate-actions` (market data) gives splits, dividends, mergers,
spinoffs, `name_change`, `worthless_removal`, with ex/record/payable dates and old/new
symbols. **Buys:** (a) real split+dividend adjustment (`adjustment=all` on bars closes
§3.5); (b) a real PIT/survivorship asset master with listing/delisting + symbol-change
handling (closes §3.4). **PIT hazard ⚠:** Alpaca explicitly gives **no guarantee on
announcement creation time** — entries can appear after the event, so this feed gives
the *effective* date, not what was *known* on a historical date. For PIT correctness you
must snapshot the CA table daily yourself or accept ex-date-only adjustment. **Effort:**
medium; flag the look-ahead caveat loudly.

### 5.4 Trade & quote condition codes — tape-replay eligibility `↑note`
`GET /v2/stocks/meta/conditions/{trade,quote}` decode the `c` condition arrays. **Buys:**
correct tape-replay eligibility (exclude odd-lot/avg-price/derivative/out-of-sequence/
auction prints — §2.5), correct per-field bar reconstruction (Open/Close/High/Low exclude
different condition sets; Volume includes odd lots), and detection of **crossed/locked
NBBO** quote states to skip when modeling marketable fills. **Effort:** low-medium
(reference tables + a filter in the producer/oracle); directly improves fill fidelity.

### 5.5 Round-lot vs odd-lot NBBO `↑note`
Already covered in §2.3 — filter `bs`/`as` < 100 as odd-lot for protected-depth logic.
**Buys:** stops the sim over-estimating accessible depth. **Effort:** low.

### 5.6 Short-sale / borrow — likely out of scope `↑note`
No SSR (Reg SHO) flag and no historical borrow data exist in Alpaca; `shortable`/
`easy_to_borrow` are current-state Trading-API booleans only. The strategy is long-only,
so this is **low priority** — note it as a known unmodeled axis rather than a task.

### 5.7 News / options / overnight (`boats`) — out of scope `↑note`
Available (news 2015+, options 2024+, Blue Ocean overnight) but orthogonal to a
regular-session long equity strategy. Record as "not pursued."

### 5.8 Data-plan reality `↑note`
Real-time SIP, OPRA, and the 10,000 calls/min ceiling require **Algo Trader Plus**; the
free tier is 200 calls/min, IEX-only real-time, 15-min SIP embargo. All historical
backfill here assumes the paid SIP plan. No action — just a cost/constraint to record.

---

## 6. Testing validity — the operator's core concern

`✔verified` census from `tests.md`:

- **538 test files; ~510 are synthetic or pure-math.** ~15–20 touch the real lake and
  **nearly all are skip-guarded** (`BOWAKA_V2_SOURCE_ROOT` / `BOWAKA_RUN_REAL_LAKE_*` /
  `MARKET_DATA_ROOT` env gates, or module-level `pytest.skip`). On CI / this machine they
  contribute **zero assertions.**
- **No executing test compares lab `run_backtest` fills/PnL to the live strategy on real
  bars.** 74 files import `run_backtest` — all feed synthetic suppliers.
- **No real-tape fidelity test for tape-replay.** `test_tape_replay_routing.py` is
  explicitly dispatch-only ("NOT a fidelity claim"); the PB.5 real-tape fidelity test is
  **absent from the tree** (it was run as an ad-hoc script `_validate_fillmodel.py`, not a
  committed test).
- **The one real-lake byte-parity test** (minute-supplier) `pytest.skip`s at module level
  when the lake probe is missing → the realism guard it advertises does not run.
- **Fixture lakes labelled "real IEX-shaped" are synthetic** flat `close=10.0`
  (`iex_short_run_lake.py`, `adjustment_lake.py`). Any test trusting them as "real" is
  validating against constants.
- **Silent synthetic fallbacks return green:** `build_iex_subset.main()` and
  `load_iex_subset(auto)` fall back to synthetic and return success; **no test asserts the
  committed subset is non-synthetic.**
- **Vacuous-pass guards:** `if trades:` / `if len(decisions)` / triple-guarded "must look
  different from synthetic" assertions pass when the fixture produces no trades.
- **Masking xfail:** config-parity `pytest.xfail`s when the contract isn't mirrored → a
  real drift-detection gap reads as xfail, not fail.
- **Notebook tests are file-exists / rc==0 smokes** — no numerical-output assertions, so
  a silent numerical regression in notebook-10 wouldn't be caught.

**This aligns exactly with the standing `no-synthetic-testing` guidance.** The fix is not
"more synthetic tests" — it's a small number of **real-data fidelity gates that actually
run** (committed, with a real-lake/tape fixture in CI or a gated-but-enforced lane). See
§10 Phase 1 + Phase 5.

### 6.1 Highest-value missing tests (cross-cut from every map's "no test for")
1. Lab `run_backtest` trade prices/PnL vs the live strategy on **real bars** (the one
   that matters; currently the parity runner skips).
2. Tape-replay fill **fidelity vs the real trade tape** (promote `_validate_fillmodel.py`
   into a committed, enforced test).
3. Minute-supplier byte-parity on the **real lake** (un-skip / provide a CI fixture).
4. **PIT bar-stamping** convention (§3.1) — assert no in-progress-minute lookahead.
5. **Matrix-vs-policy-window** parity (§3.2) — policy-windowed, not raw-supplier, assert.
6. T1 cent-walk: assert **total fill ≤ displayed size** (§2.2).
7. `intended_realism` coverage on **interior folds** (not just the first 5 sessions).
8. A test that the committed IEX subset is **real, not synthetic** (`synthetic_fallback==False`).

---

## 7. Silent fallbacks & fail-loud debt

Every Round-1 map flagged bare `except Exception → degrade` paths. Individually small;
collectively they **mask real defects and undercut the fail-loud realism contract.**
Representative, high-impact ones (`✔verified` from the maps):

- **Lake read error → empty universe, no warning** (`builder.py:355-356, 434-438`): a
  transient lake outage silently shrinks/empties the tradable universe; the diagnostic
  "no prior bar" warning is bypassed when the asset master itself errored.
- **Lake config silently degraded to synthetic regime** (`lineage.py:415-419`): an
  unreadable lake produces a *valid-looking synthetic* `dataset_hash` — a real run with a
  broken lake hashes as if it were synthetic. Forensics/realism hazard.
- **DQ level crash → warn, never fail** (`data_quality.py:1509-1606`): a crashing DQ
  level can never fail the run.
- **IR coverage gate bypassed on telemetry exception** (`walkforward_runner.py:1980→1983`):
  a telemetry `except` sets coverage `None`, and the gate only fires when coverage is
  not None → a silent escape hatch from the full-PIT-union requirement.
- **Quote/trade/status supplier exceptions → "no data"** (many sites): a supplier *bug*
  is swallowed as a missing-data condition → synthetic quote / legacy fill / no halt
  deferral, silently.
- **Reconcile vacuous PASS** (`comparators.py:295,368`; `metrics.py:93,111`): empty /
  zero-overlap candidate sets yield `jaccard=1.0`, recall 1.0, match 1.0 → a degenerate
  run that emitted nothing **reports full agreement.**

**Action:** triage these into (a) legitimately-tolerant (document the fallback + emit a
counter that surfaces in the report), vs (b) must-fail-loud (convert to a structural
error). **Round 2 note:** the two examples flagged loudest here — the lineage
synthetic-degrade (L6) and the IR coverage bypass (L4) — were both **downgraded to
defense-in-depth**: a downstream guard (store `create=True` / the unconditional full-fold
preflight) prevents each from biting a real run (§9). They're still worth a one-line
hardening, but they are *not* priorities. The highest-value items in this list are the
supplier-exception swallows that silently substitute synthetic quotes / legacy fills.

---

## 8. Dead / scaffold code (cleanup, reduces parity-diff noise)

`✔verified` (reconcile_reports.md, prod_*.md, scanner.md, sim_*.md):

- `oco_latency_calibrator.py` — entirely unreferenced; the sim still uses the hard-coded
  0.5s attach latency it was meant to replace.
- `orchestrator._default_reconcile_one` — raises `NotImplementedError`; the Phase-9
  multi-session reconcile only ever runs against injected test stubs. Three reconcile
  generations (Phase-7/9/10) coexist with **conflicting "match" tolerances**.
- Lab `LabFill.fill_timestamp=None` hard-coded (`replay.py:360`) → lab fill latency is
  structurally uncomputable → latency reconciliation vacuously passes.
- `preload_session_events_lazy` / `next_tick_at_or_after` — dead (lazy cadence is
  runtime-refused).
- Signal-fade `feed`/`activation_artifact_dir` never threaded into the real run loop →
  the activation path is effectively unreachable; fade stays telemetry.
- Legacy `scanner/universe_builder.py` with **stale pre-remediation defaults**
  (`max_price=1000`, `min_adv=1_000_000`) still called by `data/universe_pit.py` — could
  screen the wrong universe if used.
- `bowaka_v2_stream.py` — unwired websocket scaffold (`falled_back_to_polling` typo).
- `_retighten_oco_at_market_open.py` — stale 2026-05-27 incident one-shot, hard-coded
  paths and `target_pct=0.15` (≠ config 0.4).
- Prod `replay.py` — `bars_supplier=lambda: pd.DataFrame()`; never reads bars (stub).

---

## 9. Correctness bug leads — **Round 2 verified ledger**

Adversarial finder + skeptic ran over the shortlist (2026-06-13). Full evidence +
reproductions in [`round2_verification.md`](./round2_verification.md). Ordered by
final, post-skeptic severity.

### ✅ Confirmed — real and bites a real run (act on these)

| Lead | Where | Final sev | Verified outcome |
|------|-------|-----------|------------------|
| **L1** PIT bar-stamping leaks the in-progress minute | scanner/`session_minute_window_cache.py:196`, `scan_matrix.py:685`, `_numba_scan_features.py:284` | **high** | Lake bars empirically START-stamped (09:30…15:59); inclusive `<=` cutoff consumes the bar at `scan_ts`. **Reproduced +48.5% lookahead** in `last_price` on a constructed forming minute. Affects **every** scan/mode (all 3 evaluators byte-parity). Fix = strict-exclusive cutoff (only fully-closed bars) + a DQ convention assertion — **parity-breaking, needs fixture regen**. |
| **L3** Matrix bakes 04:00 premarket vs 09:45 policy window | `scan_matrix.py:604-685` | **high** | Confirmed: matrix cumulates from 04:00 with no policy lower bound; debug-assert uses the raw supplier so it can't catch it. Taints the matrix (perf) path the real studies use. |
| **L5** Two `ema_slope_prior` definitions (ratio vs abs/3) | `forming_bar.py:123` vs `suppliers.py:367` (live `features.py:107` = ratio) | **high** | Confirmed the supplier path can feed the scanner a definition that diverges from the live contract's ratio form → wrong `ema_slope` gate/score. |
| **L11** Default exit fills at exact bracket, zero slip | `exits.py:524-577` | **high** | Confirmed & reproduced: with all exit-realism knobs off (the defaults), exits return exactly the bracket price. #3155 ran with these defaults. |
| **L14** Live has NO intraday time-stop / signal-fade; sim has both | `bowaka_v2_strategy.py` vs `sim/exits.py` | **high** | Confirmed: live only does `max_hold_days`; sim exits positions the live bot would hold → backtest credits exits that don't happen live. |
| **L15** Live ignores 3 risk caps the sim enforces | live strategy vs `sim/risk_gates.py` | **medium** | Confirmed: `strategy_slice_loss_pct` / `max_stopouts_per_day` / `consecutive_stopouts` declared but unused live; sim enforces them → sim more risk-constrained than live. |

### 🟡 Confirmed but bounded — real on a narrow path (fix opportunistically)

| Lead | Final sev | Bound (why it's narrow) |
|------|-----------|-------------------------|
| **L2** T1 cent-walk / zero-size over-fill | medium | Reproduced 6×–50× over-fill (and full-fill on zero size), and the T2 cap does **not** save it. BUT reachable **only on `current_code_parity` with a real historical quote**; `intended_realism`/`fast_realism` route to honest T3, and the synthetic-fallback majority routes to T0 (which honors the liquidity proxy). It's a test-pinned parity wart. Matters for any CCP-selected finalist (incl. #3155 if it saw historical quotes). |
| **L8** NaN minute close → NaN exit price → NaN PnL | medium | Reproduced (NaN exit price, NaN PnL, mis-counted as non-loss). BUT on the Optuna path the NaN trial dies **loudly** via `MetricUnitsError` → sentinel → discarded (not silent corruption). Trigger is rare (needs a null/corrupt OHLC row; not observed in the lake). Still worth a guard in `_mk_exit`. |
| **L7** caps>1 same-symbol count uses only open lots | low | Real unit bug, reproduced. BUT `same_symbol_entries_per_day=1` in the default + **every shipped config** and is not Optuna-tuned, and the scanner upstream-masks it (entries ≤ emits ≤ cap). Dormant; fix as defensive hardening only. |
| **L18** Tape-replay oracle/producer don't filter ineligible trade conditions | low | Confirmed the oracle takes all prints; matters **only when tape-replay is actually enabled** (today dormant). Fold into the Phase-2 tape work (§5.4). |
| **L17** Reconcile comparators vacuous-PASS on empty sets | low | Confirmed empty/zero-overlap → `jaccard=1.0`/pass. Low because the reconcile path is unwired scaffolding (`_default_reconcile_one` raises) — it has no real data to mis-pass yet, but fix before paper-recon (Phase 6). |

### 🟠 Overstated — mechanism real, but a downstream guard prevents it biting (defense-in-depth only)

| Lead | Why it does **not** bite a real run |
|------|------------------------------------|
| **L4** IR coverage gate bypassed on telemetry exception | The same PIT-build surface is re-exercised by the study-start preflight **and** the unconditional `run_full_fold_preflight._probe_fold`, both of which fail closed under IR before `study.create()`. Residual is cosmetic (logs "unknown" instead of the specific refusal). One-line hardening optional. |
| **L6** Lineage degrades broken lake → synthetic hash | Every real caller constructs `MarketDataStore` first (`create=True` mkdir): a creatable path stays `regime='lake'`; a non-creatable mount **crashes loudly** upstream; the surviving empty-lake path is caught fail-closed by the IR coverage gate. Latent fragility, not run-affecting. |
| **L12** T3 `max(touch, cap_shares)` can't tighten below touch | This is the **documented, unit-tested design**: displayed NBBO size is real liquidity a marketable order can hit; the cap bounds consumption *beyond* the touch. For illiquid names the fill **is** bounded down to the small touch (reproduced). Not a defect — the real over-fill is the separate L2 path. |
| **L16** No embargo + `step_months` dead → correlated folds | There is **no per-fold training** — the train window is never used to fit anything; the same global trial params apply to every fold, and validation windows are disjoint+adjacent, so the fold-variance penalty isn't inflated. Day-1 baselines are strictly causal (matches live). Soft research-hygiene note, no leakage mechanism. |

### ❌ Refuted — not a real defect on any reachable path

| Lead | Why |
|------|-----|
| **L9** `entry_date = date.today()` fallback | `scan_timestamp` is **always** a string from `build_candidate_event`; all 3 producers and the sole `consume()` caller preserve it → the `else` branch is dead. Latent only (a future refactor could wake it). |
| **L10** `derive_validation_config` evades the tape `research_only` cap | `suitability` derives `consumes_trade_tape` **independently** from `fill_model` (via `lineage._resolved_consumes_trades`), reproduced to cap at `research_only`. The cap fires as designed; no evasion. |

(Each subsystem map has more leads not in this shortlist; this is the verified cross-cut.)

---

## 10. Phased roadmap

Phases are ordered by **dependency and realism leverage**. Phase 0 is cheap and gates
everything (you must know which leads are real before you build on them). Phases 1–2 are
the realism core. Phases 3–5 broaden data realism and lock in real-data testing. Each
phase lists exit criteria.

### Phase 0 — Verify the leads `✅ DONE (2026-06-13)`
The adversarial Round-2 (finder + skeptic per lead, reproduced against real code/lake) is
complete — see §9 and [`round2_verification.md`](./round2_verification.md). Outcome:
6 confirmed (L1, L3, L5, L11, L14, L15), 5 confirmed-but-bounded (L2, L7, L8, L17, L18),
4 overstated/defense-in-depth (L4, L6, L12, L16), 2 refuted (L9, L10). The **PIT lookahead
(L1)** is the new top-priority correctness defect.
- **Still open from Phase 0's exit:** the §1 parity-golden recheck — confirm the 4
  contract-drift tests (`test_actual_contract_loaded` ×3, `test_source_manifest_unchanged`)
  are green after the `3b260b0` re-mirror, and that `run_production_backtester --lake-root`
  works end-to-end. (Cheap; do alongside Phase 1.)

### Phase 0.5 — Fix the PIT lookahead (NEW #1, correctness) `realism core`
L1 is confirmed and inflates every backtest, so it gates the value of every later phase
(re-scoring finalists, real-data gates, IR). Change the forming-bar cutoff to admit only
fully-CLOSED bars (since bars are START-stamped: `timestamp <= scan_ts - 60s`, i.e.
strict-exclusive on the in-progress minute) across all three evaluators
(`session_minute_window_cache.py`, `scan_matrix.py`, `_numba_scan_features.py`) and the
supplier; add a DQ/preflight assertion pinning the lake's 09:30…15:59 START-stamp
convention. **This is parity-breaking** — it must be a versioned correctness fix with full
fixture/golden regeneration and a regression test, not a silent edit.
- **Exit:** the cutoff excludes the in-progress minute; a regression test proves no
  forming-bar feature reads price ≥ `scan_ts`; fixtures regenerated; the lookahead-delta
  test from Round 2 now reads 0.

### Phase 1 — Real-data test gates that actually run `testing`
Stand up the small set of **enforced** real-data fidelity tests (§6.1 1–8). At minimum:
lab-vs-live on real bars, tape-replay fidelity vs the real tape (promote
`_validate_fillmodel.py`), minute-supplier real-lake parity (un-skip), PIT-stamping,
matrix-vs-policy-window, and "committed subset is real". Decide a CI lane that has a real
(or faithfully-captured) lake/tape fixture so these don't silently skip.
- **Exit:** a default test run executes ≥1 real-bar fidelity assertion and ≥1 real-tape
  fidelity assertion; no decisive parity test is skip-guarded into a no-op.

### Phase 2 — Make the honest fill model the selection contract `realism core`
With the fill leads verified (Phase 0) and gated (Phase 1):
- Fix the legacy over-fill bugs (§2.2) or retire the legacy path for selection.
- Add trade-condition filtering + round-lot/odd-lot handling to the tape-replay oracle
  and the quote model (§2.5, §5.4, §5.5).
- Add a basic execution-latency model and fix `entry_timestamp` to the real fill minute
  (§2.3).
- Choose and wire the **selection** contract: e.g. `fast_realism` search →
  `derive_validation_config` → tape-replay finalist validation. Re-score the existing
  finalists under honest fills and compare ranks to #3155.
- **Exit:** a finalist is selected under an honest fill contract; the rank shift vs the
  legacy-model selection is measured and documented.

### Phase 3 — Official prints & adjustment realism `data realism`
- Add the **auctions** producer (§5.1); use official open/close for EOD mark, gaps, and
  any MOO/MOC logic; fix the EOD daily-vs-minute mark divergence (sim_core.md:53).
- Use `adjustment=all` for true split+dividend daily bars; resolve the
  raw-minute/adjusted-daily mixing (§3.5).
- **Exit:** open/close come from auctions; dividend adjustment is actually applied;
  a test pins official-print usage.

### Phase 4 — Survivorship + the `intended_realism` unblock `data realism (external)`
- Ingest **corporate actions** → real PIT/survivorship asset master (listing/delisting,
  symbol changes), enforce `min_history_trading_days:45`, fix `_status_active("")`
  (§3.4, §5.3). Flag the CA announcement-time PIT hazard loudly.
- Import **Nasdaq halt/LULD history** into a `statuses/` partition so the halt gate has
  real data and `intended_realism` can run end-to-end (§2.4, §5.2). Then confirm IR
  coverage on **interior folds**, not just the first 5 sessions.
- **Exit:** a real PIT master drives the universe; `intended_realism` completes a real
  walk-forward study with halt data present.

### Phase 5 — Parity hardening + methodology + cleanup `correctness`
- Resolve every sim↔live divergence in §4: either wire the missing live behavior (intraday
  time-stop, signal-fade, the three risk caps) or disable it in the parity sim — explicitly
  and tested. Map the omitted universe filters from the contract (§4). Harden the prod
  backtester's top-1/low-high-quote behavior so the parity oracle is meaningful.
- Walk-forward methodology (§4.1): add an embargo/purge gap, wire `step_months`, wire
  `run.seed` to the sampler, fix parallel determinism, add a minimum-fold gate.
- Triage silent fallbacks (§7): convert must-fail-loud ones to structural errors; surface
  the rest as report counters. Delete the dead/scaffold code (§8) to shrink the parity-diff
  surface.
- **Exit:** sim and live agree on which exits/caps fire; the parity golden runs; the
  silent-fallback list is triaged; dead code removed.

### Phase 6 — Paper reconciliation (the standing promotion gate) `validation`
Still blocked on real bowaka v2 paper logs (the long-open P1-005/P1-009). Once logs exist,
wire `orchestrator._default_reconcile_one` (currently `NotImplementedError`), give lab
fills a real `fill_timestamp`, reconcile the conflicting Phase-7/9/10 tolerances, and run
paper-vs-sim on real sessions. This is the §12 gate for promotion to `main`.
- **Exit:** a real paper session reconciles against the sim within declared tolerances.

---

## Appendix — evidence index

**Round 2 verification** (finder + skeptic per lead, reproductions):
[`round2_verification.md`](./round2_verification.md) — the verified basis for §9.

Per-subsystem Round-1 maps (the evidence base; each has full file:line refs):

| Map | Subsystem |
|-----|-----------|
| [`round1_maps/sim_core.md`](./round1_maps/sim_core.md) | event-driven engine, run-mode router, EOD mark, risk kills |
| [`round1_maps/sim_fills.md`](./round1_maps/sim_fills.md) | entry fill tiers T0–T4, tape replay, over-fill leads |
| [`round1_maps/sim_exits.md`](./round1_maps/sim_exits.md) | exit walk (numpy/pandas), brackets, gap/time/max-hold/fade |
| [`round1_maps/scanner.md`](./round1_maps/scanner.md) | forming bar, gates, score, scan-matrix, PIT stamping |
| [`round1_maps/data.md`](./round1_maps/data.md) | lake loaders/suppliers, lineage, DQ gating, backfill |
| [`round1_maps/optuna_core.md`](./round1_maps/optuna_core.md) | walk-forward, objective, folds, caching |
| [`round1_maps/optuna_validation.md`](./round1_maps/optuna_validation.md) | preflight, holdout, stress, promotion, suitability |
| [`round1_maps/config_universe.md`](./round1_maps/config_universe.md) | contract→config mapper, PIT universe builder |
| [`round1_maps/reconcile_reports.md`](./round1_maps/reconcile_reports.md) | parity oracle + paper reconciliation + reports |
| [`round1_maps/prod_strategy.md`](./round1_maps/prod_strategy.md) | live entry/exit/risk/OCO contract |
| [`round1_maps/prod_scanner.md`](./round1_maps/prod_scanner.md) | live universe builder + intraday scanner + features |
| [`round1_maps/prod_execution.md`](./round1_maps/prod_execution.md) | OpenAlgo broker client, cost model, prod backtester |
| [`round1_maps/tests.md`](./round1_maps/tests.md) | 538-file test census, synthetic-vs-real, untested surfaces |
| [`round1_maps/history.md`](./round1_maps/history.md) | audit timeline; closed / open / recheck ledger |
| [`round1_maps/alpaca_catalog.md`](./round1_maps/alpaca_catalog.md) | full Alpaca stock data-product catalog |
| [`round1_maps/alpaca_micro.md`](./round1_maps/alpaca_micro.md) | microstructure realism reference (halts, conditions, auctions, CA, borrow) |
