# Ladder Lab v10 — `recycle` engine notes

> **v10.2 update (post first-live-run fixes):** the first full NonKYC run exposed
> three model defects, all fixed:
> 1. **Spread-bounce harvesting** — thin-book 5m candles are alternating bid/ask
>    prints; the sim was harvesting every flip at 0.3% costs (DOGS/USDT printed
>    +30,691,563%). Per-side slippage is now `max(slip_floor, Roll-estimator
>    half-spread from the candles themselves)`, applied in the search, WF, and
>    reports alike, capped at `rc_slip_cap` (6%). A per-round-trip plausibility
>    gate (`rc_gate_max_cycle_edge_pct/_x`) backstops residual bad data and sets
>    `data_suspect=True`.
> 2. **Dormant-block gate poisoning** — blocks where price never visited the
>    (today-anchored) band scored `edge=0, trades=0` and dragged every rate,
>    failing even the live profitable ladders. Gates are now **band-aware**:
>    blocks get `in_band_pct`; activity gates (trades/two-sided/abs-profit)
>    judge ACTIVE blocks only, `edge_pos_rate` skips neutral (|edge|<0.25%)
>    blocks, a new `n_active_blocks ≥ 4` gate requires the band be visited, and
>    `worst_block_edge` (recalibrated to −12.5%) still judges everything —
>    dormant inventory beta is risk you actually hold.
> 3. **NonKYC native candles omit trade-less periods** — bars are now snapped to
>    a fixed grid with flat gap-fill (`regularize_bars`; flat bars can't fill but
>    restore correct cooldown/refresh timing and block spans). Degenerate <1-day
>    tail blocks are dropped.
> New summary fields: `slip_used_pct`, `candle_gap_fill`, `n_active_blocks`,
> `data_suspect`. The notebook needs no changes — just replace the module and rerun.

> **v10.1 update (5-minute bars):** live API tests confirmed NonKYC's native
> `/market/candles` serves the **full 180 days of 5m in a single call** (timestamps
> in ms) and MEXC honors 5m pagination back 180d (~104 pages). The engine now runs a
> **hybrid**: candidate search + walk-forward on hourly (geometry doesn't need 5m,
> 12× cheaper), while the frozen block reports, YAML evaluation, and JSONL calibration
> run on **5m** (`CFG['rc_report_interval']='5m'`) — so event refresh and the 1h
> cooldowns resolve at near-live latency (cooldown = 12 bars instead of 1). Set
> `'60m'` to revert. New: `fetch_intraday` / `prefetch_intraday` /
> `mexc_klines_interval` (correct sub-hourly interval map), and `df_to_markdown`
> — a tabulate-free pipe-table renderer fixing the `to_markdown` ImportError.

## Files

| File | Role |
|---|---|
| `ladder_lab_recycle.py` | **New v10 engine.** Drop next to your existing `ladder_lab.py` (unchanged, still required — adapters/cache/screener come from it). `ladder_lab_robust.py` is retired; nothing imports it anymore. |
| `NONKYC_Crypto_oscillator_finder_v10_recycle.ipynb` | New pipeline notebook. `EXCHANGE='kraken'` in Cell 1 runs the Kraken variant — no separate notebook needed. |
| `test_recycle.py` | 51-check offline test suite (no network). `python3 test_recycle.py` → `ALL TESTS PASSED`. Rerun after any edit to the module. |

## Why v9 failed everything (root causes fixed in v10)

1. **No proceeds recycling.** v9's kernel froze order quantities at t=0 and re-armed rungs only on a *daily close* crossing. Your live `range_inventory_ladder` redeploys proceeds via event refresh within an hour. v10's kernel models it: passive rungs, sizes drawn from the current ledger, opposite-side refresh after every fill, per-side cooldown re-placement, 12 h global refresh, min-notional — on **hourly** bars.
2. **Score miscalibration.** v9 subtracted absolute penalties (inventory-vs-50% alone ≈ −5.9 pts on a typical one-sided fold) that exceeded any achievable 15-day return; your empirically profitable XMR fold (+2.2%, beat hold, 0.8% dd) scored −3.52. v10 scores **edge = pnl% − hold%** with three small terms; that same fold now scores **+2.27**. The 50%-inventory penalty is gone — your XMR ladder deliberately runs ~86% base and that is respected via the YAML's seed intent (`quote_frac` derived from `claimed_base_value_quote / total_amount_quote`).
3. **Anti-churn stress.** v9's stress capped the whole ladder at 1 fill/day — punishing exactly the many-small-trades behaviour you want. v10's conservative pass = body-only candles (wick-only touches don't fill) + extra slippage. Fair, and doesn't scale with trade count.
4. **Nothing deployable was ever validated.** v9 re-optimized per fold (RNG salted by fold index, guaranteeing instability) and never tested your YAMLs. v10's **primary** evidence is `frozen_ladder_report`: one fixed ladder run continuously over ~180 d, sliced into 15-day blocks vs a same-seed hold. Gates: ≥65% of blocks beat hold, ≥50% positive outright, worst block ≥ −6% edge, median ≥10 trades/block, ≥60% two-sided. Your four live YAMLs are parsed (prices, weights, cooldowns, refresh, fee, min order, seed mix) and run through the same report in Cell 6 — genuinely out-of-sample.
5. **Export bugs.** `round(x, 8)` produced zero prices (DOGS/ETH) and duplicate rungs (BELLS/BTC). v10 formats with the exchange's `pdec` (falling back to 10 significant figures) and hard-validates the *formatted* ladder (positive, unique, monotonic, uncrossed) before anything reaches the copy/paste markdown. Other fixed bugs: min-qty check now uses the **last** price, stable/stable pairs (USDC/USDT, FUSD/…) are dropped, candidate RNG is deterministic per market (not per fold).

## Validation layers (read them together)

- **Primary — Cell 9 / `final_summary`:** `CONFIRMED` / `GATED` / `SUSPECT` from the block-consistency gates + deploy gates (depth, min-qty, precision, WF, daily-only-data flags). `edge_pos_rate` + `med_trades_per_block` = your "consistent 3–4 week profit from many small trades" metric.
- **Secondary — Cell 8:** leakage-safe rolling walk-forward (60 d train → 15 d unseen, step 15 d) of the *fitting process*, gated on hold-relative edge.
- **Ground truth — Cell 6:** your live YAMLs. If these disagree with your real PnL, run **Cell 10** (diagnostic JSONL replay) and recalibrate `rc_target_trades_per_15d` before trusting the optimizer. If `extract_fills_from_jsonl` returns nothing, paste me the `summarize_diagnostic_jsonl` output and I'll tighten the extractor to your schema.

## Honest caveats

- The deploy fit trains on the last 60 d, so its frozen report overlaps its training there. The WF table and the YAML reports are the untainted evidence.
- Hourly candles still can't see sub-hour ping-pong; if Cell 10 shows the sim under-filling vs live, your real edge is likely *better* than reported (and vice versa).
- Without numba the hourly engine is ~50–100× slower; Cell 1 auto-installs it. If you must run pure-Python, set `rc_n_candidates≈80` and `rc_top_n_from_screen≈15`.

## Knobs (all in `recycle_default_config`, prefix `rc_`)

`rc_eval_days=180`, `rc_block_days=15`, `rc_cooldown_seconds=3600`, `rc_refresh_seconds=43200`, `rc_n_candidates=240`, `rc_target_trades_per_15d=40` (calibrate!), gate thresholds `rc_gate_*`, WF windows `rc_train_days/rc_test_days/rc_step_days`, stress `rc_stress_body_only`/`rc_stress_extra_slip`, and v10.1: `rc_report_interval='5m'`, `rc_intraday_days=185`, `rc_min_intraday_days=45`.
