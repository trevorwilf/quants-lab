# bowaka_v2_lab — realism & parity remediation (Claude Code prompt)

Single-prompt, multi-phase remediation of the validated findings from the Round-2 adversarial
verification. You (Claude Code) implement every phase in order, each on its own branch off `dev`,
each ending in comprehensive testing and an automatic merge back to `dev`. Do **not** stop for
approval between phases unless a phase's exit gate explicitly says PAUSE.

---
## 0. Context & authoritative spec

- **Repo root:** `quants-lab/`. **Lab root:** `quants-lab/research_notebooks/bowaka_v2_lab/`.
  Lab source: `…/src/bowaka_v2_lab/`. Live-strategy mirror: `…/reference/source_strategy/scripts/`.
  Shared lib: `quants-lab/research_notebooks/bowaka_common/src/bowaka_common/`.
- **Spec of record** (read both fully before Phase 0; they carry the file:line evidence and the
  finder/skeptic reproductions for every lead): `bowaka_v2_realism_roadmap.md` and
  `round2_verification.md`. Where this prompt cites `Lx` or `§x`, the full evidence is there.
- The findings were **independently re-validated against current code**; the file:line refs below
  are confirmed present. Treat them as the work list, not as suspicions to re-investigate.
- All line numbers are anchors, not guarantees of exact position — locate by symbol/pattern, then
  apply.

### Severity classes (drives what you do, not whether)
- **Confirmed (fix):** L1, L3, L5, L11, L14, L15.
- **Confirmed-bounded (fix; bites a narrow path):** L2, L7, L8, L17, L18.
- **Overstated (defensive hardening only — do NOT alter the working downstream guard):** L4, L6, L16.
- **L12 is intended, unit-tested design — NOT a bug.** Add a clarifying assertion + test only;
  do **not** change `max(touch, cap_shares)` semantics for the real-quote path, and **preserve**
  the `fast_realism` touch=0 branch (`strategy_consumer.py:633-636`).
- **Refuted — DO NOT TOUCH (verified non-defects):** **L10** (no change at all). **L9** (dead branch):
  add only a one-line regression tripwire (raise/assert on a non-string `scan_timestamp`) — a guard,
  not a behavior change.

---

## 1. GLOBAL DIRECTIVES (apply to every phase)

### 1.1 Branch model
- Work happens on `dev`. If `dev` does not exist, create it from `main` before Phase 0.
- Each phase: `git checkout dev && git pull --ff-only 2>/dev/null; git checkout -b <phase-branch>`.
- On a clean phase exit: merge `<phase-branch>` into `dev` (`--no-ff`), then proceed. No user prompt.

### 1.2 PHASE PROTOCOL (the loop every phase runs — defined once, referenced by each phase)
1. `/compact`
2. `/effort <level>` (the level named in the phase header).
3. Create the phase branch off `dev` (§1.1).
4. Implement the phase scope.
5. **Tests:** create or update tests covering every code change (skip only with a stated reason).
6. **Comprehensive testing:** run the full lab suite
   (`cd quants-lab/research_notebooks/bowaka_v2_lab && python -m pytest -q`), plus any enforced
   real-data lane wired in Phase 2.
7. **Fix loop:** if comprehensive testing fails on errors **caused by this phase's changes**
   (ignore pre-existing unrelated failures — record them, don't chase them), use `ultrathink` and
   make **up to 5** fix attempts, re-running comprehensive testing after each. 
8. If still failing after 5 attempts → **PAUSE and notify the software engineer** with: the failing
   tests, the diff, what each of the 5 attempts tried, and the suspected root cause. Do not merge.
9. If comprehensive testing passes → merge the branch into `dev` (§1.1) and continue to the next phase.

### 1.3 Parity-breaking phases (P1, P3, P4, P5 — flagged in each header)
These deliberately change backtest results. Therefore:
- Treat them as **versioned correctness fixes**: bump/stamp the relevant contract/source-manifest
  version, never a silent edit.
- **Regenerate fixtures/goldens as an implementation step, before step 6.** Fixture diffs that are
  the *expected consequence* of the fix are regenerated and committed — they are **not** "test
  failures" to chase in the §1.2 fix loop. Distinguish: a fixture value moving because the model
  changed = regenerate; a test erroring for an unrelated reason = fix loop.
- Each such phase ships a **regression test that pins the new, correct behavior** (not just "tests
  pass").
- After P1/P3/P4/P5, the production finalist **#3155 was selected under the old (buggy) model** — its
  selection basis is now invalid. P5 re-runs selection; do not treat #3155 as ground truth after P1.

### 1.4 External data / API keys (P6, P7)
- Phases needing Alpaca / Nasdaq data assume CC has API credentials on this desktop. **First step of
  each such phase: probe for credentials** (env/keychain/config). If absent → **PAUSE and notify the
  engineer** with the exact variables/endpoints needed; do not fabricate or synthesize data.
- Alpaca has **no historical halt/LULD** (streaming-only) — P7 ingests **Nasdaq Trader halt files**
  for that, per round2/roadmap §5.2.

### 1.5 No-synthetic-validation rule
Synthetic/fixture tests stay as unit coverage, but **no decisive realism/parity claim may rest on a
skip-guarded or synthetic-constant test**. Phase 2 wires the real lake+tape fixture the engineer
provides; subsequent phases assert against it.

---

## 2. EFFORT TABLE (set slider per phase; `/effort` is also emitted in each header)

| Phase | Effort | Parity-breaking | External data |
|---|---|---|---|
| P0 parity-golden recheck | medium* | no | no |
| P1 PIT lookahead (L1) | max | **yes** | no |
| P2 real-data test gates | max | no | uses real fixture |
| P3 scanner parity (L3, L5) | max | **yes** | no |
| P4 fill-model correctness (L2, L11, L12, §2.2/2.3) | max | **yes** | no |
| P5 tape-replay + honest selection (L18, §2.5/5.5) | max | **yes** | trade-conditions endpoint |
| P6 official prints + adjustment (§5.1, §3.5/3.6) | high* | no | auctions endpoint |
| P7 survivorship + IR unblock (§3.4/5.2/5.3) | max | no | corp-actions + Nasdaq halts |
| P8 sim↔live parity (L14, L15, §4) | max | partial | no |
| P9 methodology + fail-loud + dead code (L16, L17, §7, §8) | max | no | no |
| P10 paper reconciliation (gate to `main`) | high | no | needs real paper logs |

`*` deliberate deviation from the "unspecified ⇒ max" default: P0 is verification-only (escalate to
high only if the golden is red); P6 follows the roadmap's "medium" auctions hint, bumped to high for
the combined adjustment rework.

---

## PHASE P0 — Parity-golden baseline recheck  · `/effort medium`
**Branch:** `fix/p0-parity-golden-recheck` · not parity-breaking · establishes the pre-break baseline.

**Objective.** Confirm the lab↔prod parity golden actually runs *before* any later phase invalidates
fixtures, so a later red golden is unambiguously attributable.

**Scope (roadmap §1 recheck).**
- Run the 4 contract-drift tests green: `tests/parity/test_actual_contract_loaded.py` (×3 cases) and
  `tests/parity/test_source_manifest_unchanged.py`.
- Confirm `run_production_backtester --lake-root` works end-to-end. (The prod mirror
  `reference/source_strategy/scripts/bowaka_v2_backtest.py` now declares `--lake-root` at ~`:509` and
  resolves it at `_resolve_backtest_lake_root` ~`:418`; verify it threads through and the golden runs.)

**Implementation.** If green: no code change; record the baseline (commit hashes, golden output digest).
If red: fix the source-manifest mirror / argparse threading so the golden runs; this is the only case
that escalates effort to high (notify the engineer that you escalated).

**Tests.** No new tests if green (stated reason: verification gate). If a fix was needed, add a test
that the golden runs end-to-end with `--lake-root`.

**Exit.** 4 contract-drift tests green; `run_production_backtester --lake-root` produces the golden
end-to-end; baseline digest recorded in the phase commit message. → merge to `dev`.

---

## PHASE P1 — Fix the PIT look-ahead (L1)  · `/effort max`  · **PARITY-BREAKING · #1 priority**
**Branch:** `fix/p1-pit-lookahead`

**Objective.** Stop every scan from reading the in-progress (forming) minute. Lake minute bars are
**START-stamped** (empirically first=09:30, last=15:59 ET); the inclusive `<= scan_ts` cutoff consumes
the bar covering `[scan_ts, scan_ts+60s)` — a confirmed, reproduced look-ahead (+48.5% in a constructed
minute) biasing **every** scan/objective/walk-forward/holdout/stress result in all three evaluators.

**Scope — make the cutoff admit only fully-CLOSED bars** (strict-exclusive on the in-progress minute;
since bars are START-stamped, the last fully-closed bar is stamped `<= scan_ts - 60s`). All four sites
are byte-parity and **must change together**:
- `scanner/session_minute_window_cache.py:~196` — `np.searchsorted(..., side="right")` → `side="left"`
  (upper bound). Keep the lower-bound `side="left"` behavior intact.
- `scanner/scan_matrix.py:~685` — `full_bars[ts_col] <= scan_ts_obj` → strict `<` (or `<= scan_ts-60s`).
- `features/_numba_scan_features.py:~284` — `while bar_ts_ns[j] <= sc` → `< sc` (or `<= sc-60e9 ns`).
- Supplier/store upper bound: `data/suppliers.py:~157` `store.minute_bars(sym, start, ts)` and
  `bowaka_common/marketdata/store.py:~270` `df["timestamp"] <= end_ts` — pass a strict end
  (`scan_ts - 1ns`) or change to `<` so the supplier path matches the evaluators.
- Pick **one** convention (recommend `timestamp <= scan_ts - 60s`, documented inline) and apply it
  identically everywhere so the three evaluators remain byte-parity with each other.

**DQ assertion.** Add a DQ/preflight assertion pinning the lake minute-bar convention (regular-session
first=09:30 / last=15:59 START-stamp). Co-locate with existing minute-count DQ (`dq_levels.py:~47`).

**Implementation notes.** This breaks every golden/fixture (§1.3): regenerate fixtures, stamp a
versioned correctness bump. Verify byte-parity across the three evaluators is preserved post-fix.

**Tests (regression — required).**
- A no-look-ahead test: on a START-stamped frame with a large move inside the forming minute, assert
  the forming-bar `last_price`/`session_high` at `scan_ts` equals the **prior closed** bar, i.e. the
  Round-2 look-ahead delta now reads **0** (was +48.5%).
- A three-evaluator byte-parity test over the new cutoff.
- The DQ convention assertion test (lake first=09:30/last=15:59).

**Exit.** Cutoff excludes the in-progress minute on all four sites; look-ahead-delta test = 0; three
evaluators byte-parity; fixtures regenerated; DQ convention test green. → merge to `dev`.

---

## PHASE P2 — Real-data test gates that actually run (§6)  · `/effort max`
**Branch:** `fix/p2-real-data-test-gates` · not parity-breaking · **uses the engineer-provided real lake+tape fixture**

**Objective.** Close the core §6 gap: ~510/538 tests are synthetic and the ~15-20 real-lake tests are
skip-guarded to **zero assertions** in CI. Stand up an **enforced** real-data lane so later
parity-breaking phases have a true safety net.

**Scope.**
- **Wire the real lake + tape fixture** the engineer provides into a dedicated, enforced pytest lane
  (e.g. a CI marker / a non-skipping conftest fixture rooted at the provided fixture path). This lane
  must **fail, not skip**, if the fixture is missing on a machine that declares it present.
- Stand up the §6.1 cross-cut tests that don't depend on later fixes:
  1. Lab `run_backtest` trade prices/PnL **vs the live strategy on real bars** (currently the parity
     runner skips).
  2. Tape-replay fill **fidelity vs the real trade tape** — promote the ad-hoc
     `_validate_fillmodel.py` into a committed, enforced test (the absent PB.5 fidelity test).
  3. Minute-supplier **real-lake byte-parity** — un-skip the module-level `pytest.skip`.
  7. `intended_realism` coverage on **interior folds**, not just the first 5 sessions.
  8. Committed IEX subset is **real, not synthetic** — assert `synthetic_fallback == False`
     (today `build_iex_subset.main()` / `load_iex_subset(auto)` fall back to synthetic and return green).
- Convert the "fixture lakes labelled real but flat `close=10.0`" (`iex_short_run_lake.py`,
  `adjustment_lake.py`) so any test trusting them as "real" instead points at the real fixture; or
  rename them unambiguously as synthetic and assert nothing realism-grade against them.
- Replace the config-parity **masking `pytest.xfail`** with a real assertion (a contract not mirrored
  must FAIL, not xfail).
- (Tests 4 PIT no-look-ahead, 5 matrix-vs-policy, 6 T1≤displayed land in P1/P3/P4 with their fixes.)

**Tests.** This phase *is* tests; additionally assert the lane is non-skipping (a guard test that the
real-data lane raises if the declared fixture is absent).

**Exit.** A default run executes **≥1 real-bar fidelity assertion and ≥1 real-tape fidelity assertion**;
no decisive parity/realism test is skip-guarded into a no-op; the committed-subset-real test passes. →
merge to `dev`.

---

## PHASE P3 — Scanner-feature parity (L3, L5)  · `/effort max`  · **PARITY-BREAKING**
**Branch:** `fix/p3-scanner-feature-parity` · combined so fixtures regenerate once for both.

**Objective.** Two confirmed scanner-feature divergences that change which symbols pass gates and their
scores.

**L3 — matrix bakes 04:00 premarket vs the 09:45 policy window.**
- `scanner/scan_matrix.py:~605/609` hardcodes the bar window `04:00…16:00`; `intraday_window_policy` is
  only recorded/hashed (`:359/:383`), never applied as a bound; the per-scan slice `:685` is
  upper-bound only; the numba prep `:636` and `_numba_scan_features.py:~273-295` cumulate from j=0.
- **Fix:** set the matrix session start from `intraday_window_start(scan_date, resolve_intraday_window_policy(cfg))`
  (or apply a policy lower-bound filter `full_bars[ts >= policy_lo]` before **both** the pandas slice
  `:685` and the numba prep `:636`) so the matrix window equals the supplier's policy window
  (default `scanner_start_to_scan` = 09:45). 
- Fix the rigged parity guard: the runtime debug-assert (`scan_matrix_runtime.py:~367`) can't fire in
  prod (supplier is `None` at `backtester.py:~1413`), and the parity fixture
  (`scan_matrix_parity.py:~61-119`) feeds 04:00 to **both** sides. Make the parity test drive the
  legacy side with the real 09:45 policy window so it can actually detect divergence.

**L5 — two `ema_slope_prior` definitions.**
- Production cache `data/suppliers.py:~367 _daily_cache_row_from_prior` uses `(ema_prior-ema_lag3)/3.0`
  (abs/3); `features/forming_bar.py:~124` and the **live** contract
  `reference/source_strategy/scripts/bowaka_v2_features.py:~109` use the ratio `ema_prior/ema_lag3 - 1`.
  The production daily-cache path (`build_daily_cache_from_lake` `:413`, `daily_cache_batch.py:~170`)
  feeds the abs/3 form into `cache_by_sym` → the `ema_slope_gate` and the `es` score term diverge from
  live (reproduced gate-flip; abs/3 also scales with price level).
- **Fix:** change `suppliers.py:~367` to the dimensionless ratio with the same div-by-zero guard as
  `forming_bar.py:124-125`. One edit fixes both production cache builders.
- Note for P5/P8: the exported `ema_slope_min` in `bowaka_v2_actual_iex_current_code.yml` was tuned
  against abs/3 slopes; after this fix the live threshold and lab tuning are finally on the same scale,
  which re-tightens selection — flag this in the P5 re-score.

**Implementation.** Parity-breaking (§1.3): regenerate matrix/daily-cache fixtures & goldens; version-stamp.

**Tests (required).**
- §6.1 #5 matrix-vs-policy-window parity: legacy side uses the **real 09:45 policy window**, assert the
  five session fields (open/high/low/volume/range) match the matrix at the production-default policy.
- A daily-cache parity test: `_daily_cache_row_from_prior` `ema_slope_prior` equals the live/forming
  **ratio** form (not abs/3) on a deterministic series; gate-outcome agreement with the live contract.

**Exit.** Matrix cumulation window == supplier policy window; the parity test detects (and now passes
on) the production-default policy; supplier `ema_slope_prior` == live ratio; daily-cache fixtures
regenerated. → merge to `dev`.

---

## PHASE P4 — Fill-model correctness (L2, L11, L12, §2.2/§2.3)  · `/effort max`  · **PARITY-BREAKING**
**Branch:** `fix/p4-fill-model-correctness`

**Objective.** Remove the legacy fill model's manufactured liquidity and zero-cost exits — the path the
production finalist was scored under.

**L11 — default exit fills at exact bracket, zero slip.** `sim/exits.py:~553`
`if not xf.cross_spread and not xf.participation_cap: return float(bracket_price), None`. All four
realism levers default OFF (`config/models.py:~421/427/433/438`); `_mk_exit` then sets `slip_bps=0.0`
for stop/target. The closure also charges **no sell-side fee** (`portfolio.py:~437` pnl is pure
`(exit-entry)*qty`; fees are entry-side only `:123-124`).
- **Fix:** for `current_code_parity` and `intended_realism`, stop defaulting to the cost-free exact-bracket
  exit. Either (a) the sim-mode resolver injects a non-zero exit cost (half-spread give-up + impact) into
  the `exits` block for non-smoke modes, or (b) default `cross_spread=True` (half-spread give-up) /
  `fill_model="tape_replay"` where a trades supplier is wired. Targets stay clamped to the resting limit
  (no improvement); the cost concentrates on marketable **stop** exits. Add explicit sell-side fees.

**L2 — T1 cent-walk + zero-size over-fill.** `sim/fills.py`
- `:825` `take = min(remainder, int(size_at_touch * cap))` re-consumes the **full original** displayed
  size at **every** penny level (`for _ in range(100)` `:818`) → 6×–50× over-fill. **Fix:** cap
  cumulative T1 fill at the displayed touch (draw each walked level from *remaining* displayed depth, do
  not re-add `size_at_touch`); or always route T1 through a participation/volume cap.
- `:804-808` zero displayed size → fills the **entire** `requested_qty` at `limit_price`,
  `is_partial=False`. **Fix:** no-fill (or fill 0, `is_partial=True`) when displayed size is 0.

**§2.2 further fabrication.**
- Missing-ADV unconstrained fill `fills.py:~491-493` (`liquidity_proxy_shares=None` → full qty; tiny
  proxy floors to 0). Make symmetric/bounded for microcaps.
- Synthetic quotes carry fabricated sizes `quote_model.py:~124` (`synthetic_calibrated` hardcodes
  `bid_size=ask_size=10_000`; `zero_spread` size 0.0) that then drive T1/T3 under CCP/smoke. Stop
  treating fabricated sizes as accessible depth.

**L12 — T3 `max(touch, cap_shares)` (NOT a bug — intended, unit-tested design).** `fills.py:~622`.
- **Do not** change the real-quote semantics and **preserve** the `fast_realism` touch=0 branch. Only:
  add a clarifying assertion/comment that displayed NBBO touch is the floor and the cap bounds
  consumption *beyond* it, and a test pinning the documented behavior (`test_fills_t3_depth_impact.py`,
  `test_fast_realism_fill.py` already lock it — extend, don't contradict).

**§2.3 latency / fill timing.**
- Execution latency is hardcoded `0.0` (`fills.py:~863/939 fill_time_seconds`). Add a basic
  decision→fill latency model (the live bot is a ~5s REST poller).
- `entry_timestamp = scan_ts` not the actual fill minute (`strategy_consumer.py:~822/836`); the exit
  walk then skips the early adverse path of a late fill. Set `entry_timestamp` to the real fill minute.

**Implementation.** Parity-breaking (§1.3): regenerate fixtures/goldens; version-stamp.

**Tests (required).**
- §6.1 #6: assert **total T1 fill ≤ displayed touch size**; zero-displayed-size → no-fill.
- Default-exit now pays spread+impact on marketable stops (non-zero `slip_bps`, sell-side fee applied);
  targets still clamp to the limit.
- Missing-ADV and synthetic-size fills are bounded, not unlimited.
- L12 documented-behavior test (extended, not contradicted).
- Latency + real fill-minute entry-timestamp regression tests.

**Exit.** No fill path manufactures depth or zero-cost exits at defaults for CCP/IR; T1≤displayed test
green; latency/entry-timestamp pinned; fixtures regenerated. → merge to `dev`.

---

## PHASE P5 — Tape-replay realism + honest selection contract (L18, §2.5/§5.5)  · `/effort max`  · **PARITY-BREAKING**
**Branch:** `fix/p5-tape-replay-and-selection` · **uses Alpaca trade-conditions endpoint (key probe per §1.4)**

**Objective.** Make the most-honest fill path faithful, then make it (not the legacy model) the
**selection** contract, and measure how the finalists move.

**L18 — tape-replay ignores trade conditions.** `sim/tape_fill.py:~86-92` selects only
`[timestamp,price,size]`; producer keeps a `conditions` column (`backfill.py:~829-841`) but never
filters; reader/supplier pass everything through. Raw SIP prints include odd-lot (`I`), avg-price
(`B`/`W`), derivatively-priced (`4`), out-of-sequence (`Z`/`L`), auction (`O`/`M`/`Q`) — **not**
continuous executable liquidity. Reproduced: a 100-share no-fill became a full 600/600 fill.
- **Fix:** add an eligibility filter to `replay_tape_fill` — include `@`/space; drop
  `I,B,W,4,Z,L,O,M,Q` (per `alpaca_micro.md:32`); read the `conditions` column when present with a safe
  fallback when absent; add `conditions` to the projection. Decode via
  `/v2/stocks/meta/conditions/trade` (key probe per §1.4). Optionally honor the `u` cancel/correct flag.
- `tape_participation` defaults `1.0` (one print absorbs 100% of a trade's size) — set a realistic cap.

**§2.3/§5.5 — round-lot vs odd-lot NBBO.** SIP `bs`/`as` include sub-100 odd-lot/BOLO sizes that are
**not** protected round-lot depth. When modeling protected/marketable fills, filter `bs`/`as` < 100 as
odd-lot; stop treating displayed size as full accessible depth (compounds with the P4 fill fixes).

**Honest selection contract.**
- Wire the selection path: `fast_realism` search → `derive_validation_config` → **tape-replay finalist
  validation** (the honest participation/depth model from P4 + this phase). Confirm the
  `research_only` suitability cap still fires for tape-consuming runs (it should — that is correct).
- **Re-score the existing finalists under the honest fill contract** and **compare ranks to #3155**.
  Account for the P3 `ema_slope` rescale effect on selection. Emit a **rank-shift report**
  (old-vs-new rank, metric deltas) as a committed artifact.

**Implementation.** Parity-breaking (§1.3): regenerate fixtures; version-stamp. The rank-shift report is
the headline deliverable, not just green tests.

**Tests (required).**
- Tape eligibility filter: ineligible prints excluded; the Round-2 600-share over-fill scenario now
  yields the correct no-fill/partial.
- Odd-lot filter: sub-100 displayed sizes are not counted as protected depth.
- Selection-contract wiring: a finalist is produced under the honest contract; suitability caps it
  `research_only`.

**Exit.** Tape oracle filters ineligible conditions and odd-lot; a finalist is selected under the honest
fill contract; the **rank shift vs the legacy-model #3155 selection is measured and documented**. →
merge to `dev`.

---

## PHASE P6 — Official prints & adjustment realism (§5.1, §3.5, §3.6)  · `/effort high`
**Branch:** `fix/p6-official-prints-adjustment` · **uses Alpaca auctions endpoint (key probe per §1.4)**

**Objective.** Use official auction prints and apply true split+dividend adjustment.

**Scope.**
- **Auctions producer (§5.1):** add a producer + lake partition consuming `GET /v2/stocks/auctions`
  (SIP) for official open/close. Use official open/close for the EOD mark, gap logic, and any MOO/MOC
  logic; **fix the EOD daily-vs-minute mark divergence** (`sim_core.md:53`). Today the lab uses daily-bar
  O/C (first/last *continuous* trade), which differ from the auction price.
- **Adjustment (§3.5):** `require_adjusted_daily_bars` collapses to `split_adjusted`
  (`adjustment.py:~22-26`) so **dividend adjustment is never applied**. Use Alpaca `adjustment=all`
  (split+dividend) for daily bars. Resolve the raw-minute/adjusted-daily mixing: minute bars are always
  RAW (`backfill.py:~333`) while daily features may be split-adjusted → mixed adjustment within one
  decision on in-window split days. Ensure `daily_adjustment_for_config(cfg)` is threaded (the
  `daily_adjustment="raw"` default across suppliers is a silent trap).
- **§3.6 (low):** `objective.py` stores a decimal in a field named `net_return_pct`. Rename/document so a
  future "×100 fix" can't silently 100×-inflate or trip `MetricUnitsError`. No behavior change.

**Tests (required).** A test pinning official-print (auction) usage for open/close & EOD mark; a test
that dividend adjustment is actually applied under `adjustment=all`; a test that one decision never
mixes raw-minute with adjusted-daily on a split day; `net_return_pct` units test.

**Exit.** Open/close come from auctions; dividend adjustment applied; mixed-adjustment resolved; units
documented. → merge to `dev`.

---

## PHASE P7 — Survivorship + intended_realism unblock (§3.4, §5.2, §5.3)  · `/effort max`
**Branch:** `fix/p7-survivorship-ir-unblock` · **uses Alpaca corporate-actions + Nasdaq Trader halt files (key probe per §1.4)**

**Objective.** A real PIT/survivorship master, and the data that lets `intended_realism` run end-to-end.

**Scope.**
- **Corporate actions → real PIT master (§5.3/§3.4):** ingest `GET /v1beta1/corporate-actions` (splits,
  dividends, mergers, spinoffs, `name_change`, `worthless_removal`, ex/record/payable, old/new symbols).
  Build a real PIT/survivorship asset master with listing/delisting dates + symbol-change handling
  (replaces the single future-dated 2026-06-05 snapshot). Enforce `min_history_trading_days: 45`
  (unenforced today, `builder.py:~276`). Fix `_status_active("")` (`builder.py:~447`) treating
  blank/missing status as active (silent no-op survivorship gate). **Flag the CA announcement-time PIT
  hazard loudly** — Alpaca gives no guarantee on announcement creation time, so this is *effective* date,
  not point-in-time-known; snapshot the CA table daily or accept ex-date-only adjustment, documented.
- **Halts / LULD (§5.2):** Alpaca serves no historical halt/LULD. Ingest **Nasdaq Trader halt files**
  into a `statuses/` partition with the schema + DQ wiring the halt gate needs, so `intended_realism`
  stops failing closed at the DQ preflight. Resume can be inferred from reopening auctions (P6); onset +
  LULD bands come from the halt feed.
- After the data lands, **confirm IR coverage on interior folds**, not just the first 5 sessions
  (ties to P2 #7).

**Tests (required).** PIT master drives the universe (listing/delisting/symbol-change respected,
`min_history_trading_days` enforced, `_status_active("")` no longer active); halt/`statuses/` partition
present and consumed by the halt gate; an `intended_realism` walk-forward completes end-to-end with halt
data on interior folds.

**Exit.** A real PIT master drives the universe; `intended_realism` completes a real walk-forward study
with halt data present; CA PIT hazard documented. → merge to `dev`.

---

## PHASE P8 — Sim↔live parity divergences (L14, L15, §4)  · `/effort max`
**Branch:** `fix/p8-sim-live-parity`

**Objective.** Make the sim reproduce the **live** strategy, not a more-sophisticated idealization.
For each divergence: **either wire the missing behavior into live, or disable it in the parity sim** —
explicitly, and tested. (Default recommendation: disable-in-sim for the parity contract unless the
behavior is genuinely intended for production, since live is the ground truth.)

**Scope.**
- **L14 — live has no intraday time-stop / signal-fade; sim has both.** Live `run_time_stop_pass_v2`
  exits only on `_trading_days_since >= max_hold_days`; zero `signal_fade`/intraday `exit_time` in the
  live module. Sim `exits.py` fires an always-on 15:30 time-stop (`:911-915`) and signal-fade
  (`:874-908`). All run configs set `time_stop.enabled:true` → the sim force-closes at 15:30 **every**
  trial while live holds to bracket/max_hold. **Fix:** disable the sim intraday time-stop (and keep
  signal-fade telemetry-only, matching live's `telemetry_then_active_after_validation`) for the parity
  contract, OR implement both passes in live. Tested either way.
- **L15 — live ignores 3 risk caps the sim enforces.** Sim `risk_gates.py` enforces
  `max_stopouts_per_day` (`:129`, default 4), `stop_trading_after_consecutive_stopouts` (`:133`,
  default 3), `strategy_slice_loss_pct` (`:157`); live references none. The two stopout caps fire via
  hard-coded defaults even when a config omits them. **Fix:** for the parity sim, gate the two stopout
  caps behind key presence (drop the hard-coded 4/3 defaults so an absent key = no gate) and confirm
  CCP configs omit them; OR implement the three caps in live `_risk_gates` with stopout counters. Tested.
- **`daily_loss` kill divergence (`sim_core.md:57`).** Live only refuses new entries on daily-loss (no
  mid-day flatten); the sim reads `daily_unrealized_pnl` refreshed only at EOD/`update_mtm`, so intraday
  SCANs see stale (often 0) PnL → kill under-fires intraday. Reconcile to live's "refuse new entries"
  behavior (no mid-day flatten).
- **Prod-backtester parity oracle hardening.** The mirror `bowaka_v2_backtest.py` takes only the
  **top-1** candidate per scan (`:~174`), uses bar low/high as bid/ask when no quote supplier (lake runs
  wire `quote_supplier=None`, `:~489`), and a fixed synthetic ±0.1% exit spread → the "production parity"
  reference itself manufactures fills. Harden so the oracle's verdicts are meaningful (consume real
  quotes; don't fabricate top-1-only breadth).
- **Contract→config mapper omits universe filters.** `import_config.py:~177-183` does not map
  `allowed_exchanges`, `exclude_otc`, `ticker_blocklist`, `exclude_etf/etn/...`; the PIT builder uses
  hardcoded defaults and `config_diff` only diffs shared keys → the omission is invisible to the parity
  gate. Map them; surface the `score:`/`historical_features:` contract sections in lab config.
- **Live offline-quote fabrication must not be inherited.** Live `strategy:~872-876`
  (`quote_supplier=None` → bid==ask==signal_price, spread 0, age 0) makes quote/price-chase gates always
  pass. The sim must not replicate this perfect-quote fallback.
- **Fees/slippage on close.** Live `close_position_v2` realized PnL is pure `(exit-entry)*qty`
  (`strategy:~1402`); OCO prices round to 2 decimals (materially shifts stops/targets on $1–3 microcaps).
  Model fees/commissions explicitly on **both** sides (sim and the close path) rather than zero.

**Tests (required).** A parity test per divergence asserting sim and live agree on which exits/caps fire
under the shipped configs; mapper round-trip test (universe filters now mapped & diffed); the sim does
not inherit the perfect-quote fallback; fees applied on both legs.

**Exit.** Sim and live agree on which exits/caps fire; the prod-backtester oracle no longer manufactures
fills; universe filters are mapped and diff-visible. → merge to `dev`.

---

## PHASE P9 — Walk-forward methodology, fail-loud debt, dead code (L16, L17, §4.1, §7, §8)  · `/effort max`
**Branch:** `fix/p9-methodology-failloud-cleanup`

**Objective.** Tidy methodology, convert silent degradations to fail-loud where they mask defects, and
delete dead code that inflates the parity-diff surface.

**Scope.**
- **L16 methodology (overstated — do the cheap, correct wirings; do not over-engineer).** `walkforward.py`:
  wire `step_months` through all five `build_walkforward_splits` call sites + add the config key
  (currently dead, always steps by `val_months`). Add a configurable embargo/purge gap option
  (`val_start = add_months(train_end, embargo)`); default 0 to preserve current behavior but make it
  available. Wire `run.seed` to the sampler (today hard-coded `1337`). Fix parallel determinism
  (`WorkerSpec.sampler_seed`/`n_startup_trials` passed but unused; workers race on shared TPE storage;
  per-worker trial-delta double-counts). Add a minimum-fold gate (single-fold plans get a zero variance
  penalty → over-trust). *(Note: the skeptic showed there is no per-fold training, so this is research
  hygiene, not a leakage fix — keep it proportionate.)*
- **L17 reconcile/parity vacuous PASS.** `parity/metrics.py`: `_trade_intersection_rate:~111`,
  `exit_reason_match_rate:~189`, `_per_session_pnl_signs:~131` return `1.0` on empty sets and
  `evaluate_thresholds` skips only `None` → both-sides-empty stamps `passes_audit_thresholds=True`.
  `reconcile/comparators.py`: `emission_jaccard`/`decision_reason_confusion` PASS on empty union /
  empty shared set; `report.py:build_phase9_recon_report` has no `union_size==0`/`comparable==0` guard.
  **Fix:** gate on observable coverage — fail (or mark NOT-MEASURED/None) when
  `prod_n_trades==0 AND lab_n_trades==0` (and per-metric on matched/sessions==0), mirroring the existing
  Phase-0 `None`-exclusion for candidate metrics; for reconcile, expose `passes=None`/sentinel on empty.
- **§7 silent fallbacks — triage.** Convert **must-fail-loud** ones to structural errors: the
  supplier-exception swallows that silently substitute synthetic quotes / legacy fills / skip the halt
  deferral (the highest-value ones); lake-read-error → empty universe with no warning
  (`builder.py:~355/434`); DQ-level crash → warn-never-fail (`data_quality.py:~1509`). Convert the rest
  to **report counters** that surface in the run report. **L4 and L6 are overstated — add only a
  one-line hardening each** (L4: treat `preflight_coverage_fraction is None` as a refusal under IR; L6:
  route the lake branch through `_coerce_lake_root` + an `is_dir()` assertion for lake-backed configs)
  and **do not** remove the working downstream guards that already prevent them biting.
- **§8 dead / scaffold code — delete (shrinks parity-diff surface).** `oco_latency_calibrator.py`
  (unreferenced; sim still uses the hardcoded 0.5s attach latency); `_retighten_oco_at_market_open.py`
  (stale 2026-05-27 one-shot, hardcoded `target_pct=0.15` ≠ config 0.4); `bowaka_v2_stream.py` (unwired
  websocket scaffold, `falled_back_to_polling` typo); `preload_session_events_lazy` /
  `next_tick_at_or_after` (lazy cadence runtime-refused); legacy `scanner/universe_builder.py` with stale
  defaults (`max_price=1000`, `min_adv=1_000_000`) still called by `data/universe_pit.py` — remove or
  repoint; prod `replay.py` `bars_supplier=lambda: pd.DataFrame()` stub. Resolve the conflicting
  Phase-7/9/10 reconcile "match" tolerances into one.

**Tests (required).** Methodology: `step_months`/embargo/seed wired and effective; min-fold gate fires on
1-fold. Vacuous-PASS: both-sides-empty now FAILs / NOT-MEASURED (the Round-2 reproductions flip).
Fail-loud: a supplier exception now raises a structural error instead of silently degrading. Dead-code
removal leaves the suite green (no live references).

**Exit.** `step_months`/embargo/seed/determinism/min-fold wired; vacuous-PASS closed; must-fail-loud
fallbacks raise; dead code removed; reconcile tolerances unified. → merge to `dev`.

---

## PHASE P10 — Paper reconciliation (promotion gate to `main`)  · `/effort high`
**Branch:** `fix/p10-paper-reconciliation` · **needs real bowaka v2 paper logs (P1-005/P1-009)**

**Objective.** Wire the standing promotion gate so a real paper session can reconcile against the sim.

**Scope.**
- Implement `orchestrator._default_reconcile_one` (currently `raise NotImplementedError`).
- Give lab fills a real `fill_timestamp` (today `LabFill.fill_timestamp=None`, `replay.py:~360`, makes
  latency reconciliation vacuously pass).
- Reconcile the conflicting Phase-7/9/10 "match" tolerances into the single set defined in P9.
- Run paper-vs-sim on real sessions.

**Blocking dependency (§1.4-style).** This phase **needs real paper logs**, which may not exist on this
machine. **First step: probe for the paper logs.** If absent → implement the wiring + `fill_timestamp`
+ tolerance reconciliation (the code that can be unit-tested against fixtures), then **PAUSE and notify
the engineer** that the live paper-vs-sim run is blocked on real logs (do not synthesize logs to fake a
pass). Do **not** merge to `main`; merge the code wiring to `dev` only.

**Tests (required).** `_default_reconcile_one` reconciles a fixture session within declared tolerances;
lab fills carry a real `fill_timestamp`; latency reconciliation is no longer vacuous.

**Exit.** Code wiring complete and unit-tested → merge to `dev`. The promotion to `main` is gated on a
**real** paper session reconciling within tolerances (engineer-run once logs exist).

---

## 3. END-OF-RUN comprehensive validation

After P9 merges to `dev` (P10 may be paused on paper logs):
1. `/compact`; on `dev`, run the **full** suite + the enforced real-data lane from P2.
2. Confirm the headline regressions read correct: PIT look-ahead-delta = 0 (P1); matrix==policy window
   (P3); supplier `ema_slope_prior` == live ratio (P3); T1 fill ≤ displayed, default exits pay
   cost (P4); tape excludes ineligible conditions (P5); vacuous-PASS closed (P9).
3. Produce a short **`dev` validation digest**: per-phase branch merged, parity-breaking version stamps,
   the P5 finalist rank-shift vs #3155, and any phases PAUSED (P7 if no keys, P10 if no paper logs).
4. Do not promote `dev` → `main`; that is the engineer's gated decision (P10 paper recon).

## 4. Refuted findings — DO NOT remediate
- **L10** (`derive_validation_config` tape cap): the cap fires as designed; **no change**.
- **L9** (`entry_date = date.today()` else-branch): dead on every real path (`scan_timestamp` is always a
  string from `build_candidate_event`). **Only** add a one-line tripwire (raise/assert on a non-string
  `scan_timestamp` at `strategy_consumer.py:~594-599`) so a future refactor fails loud — not a behavior
  change. Add a one-line test for the tripwire.
