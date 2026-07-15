# Ladder Lab v11 — engine notes (`recycle_v11`)

> **v11.1 update (post first-full-run fixes).** The first NonKYC run (102
> markets, 0 CONFIRMED) validated the holdout design (median holdout edge
> +0.07%, 52% positive — the typical optimizer pick honestly shows ~zero OOS
> edge) and exposed four things, all fixed:
> 1. **Crypto-quoted pairs were inert.** Fund, min-order and the volume
>    budget were denominated in *quote units*, so a BTC-quoted market ran a
>    "1000 BTC" fund against ~0.001 BTC/bar volume and the cap crushed every
>    fill to dust (edge=0.000 rows). v11.1 converts fund and min-order into
>    quote units via the universe's USD rate; exports now carry
>    `max_fund_value_quote` **in quote units** (what the controller takes)
>    plus `max_fund_value_usd` and `quote_usd_rate` for the human.
> 2. **Finalize re-sampled the order book**, so a spread that moved between
>    the engine's sample and finalize fired spurious "live half-spread
>    exceeds charged slip" gates (5 markets). Finalize now reuses the exact
>    snapshot `evaluate_market` sampled (`spread_pct_sampled`,
>    `depth_usd_sampled` ride along in the eval dict).
> 3. **The block two-sided gate structurally punishes re-anchored ladders in
>    trending regimes** (XMR: candidate failed two_sided 0.36 while the live
>    YAML passed 0.73 on the same data — a today-anchored band is one-sided
>    against a −40% past by construction). New `rc_gate_two_sided_mode`:
>    `'blocks'` (v10), `'holdout'`, or `'either'` (default — the block gate
>    is waived when the *holdout* was two-sided, recorded as
>    `two_sided_waived_by_holdout`). The holdout is anchored and judged on
>    its own unseen window, so it carries no such bias.
> 4. **~90% of engine time went to dust markets** (91/102 thin-book gates,
>    95/102 at the $200 fund floor). Default `min_vol_usd=10000` now filters
>    the universe at the source; and because the thin-book gate is
>    load-bearing yet single-sampled, there is a new **Cell 10 book
>    verification**: `verify_books()` polls the shortlist's order books
>    several times and reports median/min/max spread and depth, a
>    thin/flaky verdict, and a size suggestion
>    (`{prefix}_book_verification.csv`).
> The JSONL calibration moved to **Cell 11**. All v11.0 fields/artifacts are
> unchanged; new final-summary columns: `max_fund_quote`, `quote_usd_rate`,
> `two_sided_waived_by_holdout`. Test suite: 71 offline checks.

**Files in this drop**

| File | Role |
|---|---|
| `ladder_lab_recycle_v11.py` | New v11 engine. Imports `ladder_lab.py` (adapters) and `ladder_lab_recycle.py` (v10) — **both must stay installed, unchanged**. |
| `test_recycle_v11.py` | Offline test suite (51 checks, no network). **Run this first on your box**, and after any edit. |
| `NONKYC_Crypto_oscillator_finder_v11.ipynb` | NonKYC pipeline on the v11 engine. |
| `KRAKEN_Crypto_oscillator_finder_v9.ipynb` | Kraken pipeline on the v11 engine. |
| `LadderLab_v11_notes_claude_code.md` | This document. |

Nothing was removed from the v10 reports. Every v10 column, CSV, and the
`*_copy_paste_ladders.md` format are preserved (the copy/paste file is rendered
by v10's own renderer — byte-identical format, including the header text).
v11 only **adds**: holdout columns, clean-block columns, harvest columns,
`vol_capped_fills`, `book_half_spread_pct`, `fit_score_gap`, `fill_model`,
and one new artifact: `*_holdout_summary.csv`.

---

## Why v11 exists — the five defects it closes

### 1. The frozen report's last 60 days were in-sample (worst: the recent ones)
v10 fitted the deploy ladder on the last 60d, then reported a 180d frozen run
that *included* those 60d — about a third of the blocks, and precisely the ones
your eye lands on, were training data. Two fixes, both active:

- **True holdout.** `deploy_fit_with_holdout()` fits on data that *excludes the
  last `rc_holdout_days` (15)*. The fitted ladder — geometry, anchor, weights all
  frozen before the holdout began — is scored once on that unseen tail.
  `holdout_edge_pct` is the only number in the pipeline that is fully
  out-of-sample **for the ladder you deploy**, and it gates deployment
  (`rc_gate_holdout_min_edge`, default −2%). A *dormant* holdout (price never
  visited the band, nothing traded) is flagged as "no evidence", not passed.
- **Clean-block gating.** The block table now tags `in_fit` blocks; the v10
  band-aware gates must pass on **all** blocks (v10 semantics, kept) *and* on
  the clean subset (`rc_gate_min_clean_blocks`, default 4). Clean failures are
  prefixed `clean:` in the gates string.

The deployed ladder is the *same relative geometry re-anchored at the current
price* (`rebuild_candidate_at_anchor`), so you deploy at today's level while the
evidence comes from a pre-holdout anchor. `deploy_anchor` and
`reanchored_from` are recorded in the deploy JSON.

### 2. Touch fills
Real passive orders need price to trade **through** them (queue position). v11
fills require penetration of `max(1 tick, price × rc_fill_penetration_pct)`
beyond the rung (defaults: 1 tick + 5 bps). Fills still execute at the rung
price. Tick size comes from the market's `pdec`.

### 3. Volume-blind fills (the thin-book failure mode)
Bars are now **Nx6 with quote volume**. Per bar, total filled notional is capped
at `rc_volume_cap_frac` (default 0.25) of the bar's quote volume, shared by both
sides, with **partial fills** — the remainder stays open, exactly like a live
partial. Bars with unknown volume are uncapped (and flagged:
`vol_known=False` per market in Cell 5). `vol_capped_fills` in every
report/fold tells you when the *book*, not the price path, was the constraint —
that's a "size down", not a "pair is bad" signal.

Note on trade counts: partial fills mean the fill *count* can be higher than
v10 while notional is much lower. Your live JSONL counts partials the same way,
so Cell-10 calibration remains apples-to-apples.

### 4. Slippage asymmetry between search and finalize
v10 searched under `max(floor, Roll)` slip — 0 Roll on healthy books — and only
*checked* the measured book spread at finalize, after candidates were already
selected under optimistic slip. v11 threads the measured live half-spread into
`effective_slip_v11()` used by the **search, the WF folds, and the report
alike** (`rc_book_spread_in_slip=True`). Candidates that only work at floor
slip never get selected in the first place.

### 5. Pair selection had no model-free evidence
`grid_harvest()` counts zig-zag swings at gaps of 1.5×/2×/3× the round-trip
cost and converts them to "harvestable %/month net of costs". Zero parameters
are fitted, so it cannot overfit; it ranks *markets*, not ladders. Cell 4
blends it into the review pick (`rc_harvest_rank_weight`, default 0.5), and
`harvest_best_pct_mo` appears in the final summary. If it's ~0, no ladder
tuning will save the pair.

### Also fixed
- **Kraken deep history**: MEXC proxy now tries a **quote alias**
  (USD/USDC→USDT), guarded by the existing last-price check — XMR/USD gets
  months of real hourly/5m depth instead of Kraken's 720-candle (~30d) cap.
- **Collision-safe grid snap**: `regularize_bars6` aggregates bars that snap to
  the same slot (max high / min low / last close / summed volume) instead of
  silently dropping one; gap bars carry zero volume so they can never fill.
- **Overfit telemetry**: `fit_score_gap` = best minus median stage-1 score.
  A huge gap means the winner is likelier a lucky draw among 240 candidates.
- **v10 equivalence, proven**: with penetration off and the volume cap off, the
  v11 kernel reproduces v10 **bit-for-bit** (`recycle_v11_parity_check()`
  asserts it; the notebook asserts it in Cell 1 on every run). Set
  `rc_v11_fill_model=False` for a byte-identical v10 A/B on any market.

---

## The evidence hierarchy (how to read a run)

1. **`holdout_edge_pct`** — clean OOS for the deployed geometry. The decider.
2. **`clean_edge_pos_rate` / `clean_worst_block_edge`** — frozen-report
   consistency *outside* the fit window. The headline `edge_pct` still includes
   the fit window (kept for v10 comparability) — prefer the clean columns.
3. **Live YAML table (Cell 6)** — ground truth for the fill model. If sim
   trades/block ≠ your JSONL fills, calibrate (Cell 10) before believing anything.
4. **`wf_pass`** — the *process* tends to generalize on this pair. A wf_pass
   with a bad holdout = good process, unlucky fit: refit later, don't force it.
5. **`harvest_best_pct_mo`** — the model-free ceiling.

A pair worth deploying looks like: positive two-sided holdout **and** clean
blocks passing **and** wf_pass **and** harvest clearly > 0, with
`vol_capped_fills` telling you the honest size.

## New knobs (defaults are the recommendation)

```
rc_holdout_days=15            rc_gate_holdout_min_edge=-2.0
rc_gate_holdout_require_active=True
rc_gate_min_clean_blocks=4
rc_fill_penetration_pct=0.0005   rc_fill_penetration_ticks=1.0
rc_volume_cap_frac=0.25          (0 disables)
rc_book_spread_in_slip=True
rc_harvest_gap_mults=(1.5,2.0,3.0)   rc_harvest_rank_weight=0.5
rc_quote_alias={'USD':'USDT','USDC':'USDT'}
rc_v11_fill_model=True           (False = exact v10 fills, A/B only)
```

## Honest caveats (what v11 still does not solve)

- The holdout is **one** 15-day window — real evidence, but high variance.
  The first live/paper block remains the final gate; the closing markdown in
  both notebooks spells out that discipline.
- The volume cap assumes your orders would have captured at most a fixed share
  of what traded through the level; it does not model queue priority within
  the level. Calibrate `rc_volume_cap_frac` against Cell-10 JSONL ratios.
- `rc_target_trades_per_15d=40` is still uncalibrated until you run Cell 10 —
  before that, the trade bonus mildly steers selection.
- Hourly search bars keep the intrabar o→l→h→c path assumption; the 5m report,
  holdout and YAML eval largely neutralize it, and stress (body-only) bounds it.
- MEXC-proxy candles are a different venue's microstructure. The last-price
  guard catches level disagreement, not spread disagreement — which is exactly
  why the live book half-spread now participates in the slip everywhere.

## First run on your box

```
python3 test_recycle.py        # v10 suite (should still pass, 2 YAML checks need your YAMLs)
python3 test_recycle_v11.py    # v11 suite — must print ALL TESTS PASSED
```
Then run the NonKYC notebook end-to-end with defaults, and send the Cell-10
JSONL comparison for XMR/USDT — that single number (sim/live fill ratio under
the new fill model) is what sets `rc_volume_cap_frac` and
`rc_fill_penetration_pct` from measurement instead of my priors.
