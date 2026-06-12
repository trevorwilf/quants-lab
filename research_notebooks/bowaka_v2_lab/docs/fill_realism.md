# Fill realism — symmetric honest fills (buys *and* sells)

**Status (2026-06-12): COMPLETE.** PB1–PB3 (sell-side exit spread/size/freshness),
PB4 (trade-tape oracle + sell **and** buy hooks), PB5 (real-tape fidelity harness),
PB6 (gated hash + suitability cap + opt-in `derive_validation`), PC1 (regression),
PC3 (end-to-end exit-PnL) all shipped + tested. Every knob below is
**default-off / byte-identical** — turning none on reproduces the legacy engine
exactly (the v2 gate stays at the pre-existing 4-fail contract-drift baseline; the
broad suite is 1592 pass / 8 pre-existing fail, 0 regressions). See
`docs/alpaca_fill_realism_implementation_plan.md` for the phase plan,
`PHASE_NOTES/alpaca_fill_realism_phase0.md` (safety) and
`PHASE_NOTES/alpaca_fill_realism_phaseB.md` (hooks + measured results).

## The gap this closes

The simulator had two unequal price engines:

- **Buys** route through the tiered fill model (`sim/fills.py`,
  `detect_execution_tier` → T0–T3). The honest **T3 depth+impact** tier (real
  touch + `participation·minute_volume` cap + √-impact) is on under
  `fast_realism` / `intended_realism` (`has_nbbo_depth`).
- **Sells/exits never touched the fill model.** `sim/exits.py:walk_lot_exit`
  filled a stop at *exactly* `stop_price` and a target at *exactly* `target_price`
  — **0 bps slippage, no spread crossing, no size cap, always the full lot** — the
  single most optimistic assumption in the sim.

This work makes the **sell side symmetric with the buy side**, and adds a
trade-tape replay oracle that prices fills off the *actual* prints.

## The knobs (all on `ExitsConfig`, default off → byte-identical)

| Knob | Default | Behavior when set |
|---|---|---|
| `exits.cross_spread` | `false` | **PB.1** — a stop/target SELL fills at the marketable bid, not the bracket price: `fill = min(bracket, bid·(1 − half_spread_bps/1e4))`. The realized give-up is recorded in `exit_slippage_bps`. Half-spread from the cost model (`base` 2 / `conservative` 5 / `severe` 15 bps). |
| `exits.participation_cap` | `null` (off) | **PB.2** — the lot can't all print into one thin minute: participation is capped at `cap·minute_volume` and the blended fill pays a √-impact give-up, mirroring the buy-side T3 (`fill = base·(1 − impact_bps/1e4)`, `impact = impact_coef_bps·√(min(qty/vol, cap))·stress_mult`). One blended-VWAP exit (the lot still exits once). |
| `exits.impact_coef_bps` / `exits.impact_model` | `10.0` / `sqrt` | PB.2 impact tuning; defaults match the buy-side `ExecutionConfig` so the two sides are symmetric. |
| `exits.require_fresh_quote` / `exits.max_quote_age_seconds` | `false` / `15` | **PB.3** — IR-consistent freshness: the bid lookup uses `max_quote_age_seconds`; a stale/absent NBBO **widens the give-up by an extra half-spread** instead of filling cleanly. |
| `exits.fill_model` (`legacy` \| `tape_replay`) | `legacy` | **PB.4** — replay the actual trade tape for the realized sell VWAP (see below). Falls back to the bracket fill when no trades are present. `tape_window_seconds` (300) / `tape_participation` (1.0) tune it. |

`ExecutionConfig` carries the symmetric **buy-side** toggle
`execution.fill_model` (`legacy` | `tape_replay`) + the same `tape_*` knobs.

Implementation (sell): the per-lot fill parameters are bundled into an `_XFill`
object built once per walk and threaded into `sim/exits._bracket_fill` (the new
`_tape_replay_bracket` branch handles `fill_model="tape_replay"`); the numpy and
pandas exit walks share the call sites, so a differential parity fuzzer
(`tests/parity/test_walk_lot_exit_numpy_parity.py`, 400 cases exercising all the
knobs together) proves they stay byte-identical.

Implementation (buy): `sim/fills._tape_replay_fill` builds a `FillResult` from
the tape VWAP for a marketable buy (no price ceiling) or a marketable-limit buy
(ceiling `ask·(1+slip)`). It is threaded `run_backtest → run_one_scan →
StrategyConsumer.consume → fills` as a **lazy** `trades_supplier` (fetched only
when `execution.fill_model == "tape_replay"`). Every `run_backtest` call site
gets its supplier from the single gate `data/suppliers.make_trades_supplier_for_
config(cfg, …)`, which returns `None` unless the config selects `tape_replay`
(so legacy runs never construct it → byte-identical). Routing is covered by
`tests/unit/sim/test_tape_replay_routing.py` (stub-supplier wiring tests).

## Trade-tape replay oracle (PB.4)

`sim/tape_fill.replay_tape_fill(trades, qty, start_ts, window_seconds, …)` is a
pure function over the raw per-print tape (`MarketDataStore.trades_between`, PA.2).
For a marketable order of `qty` shares at `start_ts` it consumes eligible prints
in `[start_ts, start_ts+window]` in time order, taking `participation` of each
print's size until filled, and returns the **size-weighted VWAP + fill fraction**.
`min_price` / `max_price` honour the trigger (a sell-stop fills at/through the
trigger → `max_price=stop`; a target → `min_price=target`). An absent/empty tape
yields an honest no-fill, so the caller falls back to the existing fill model.

This is the most faithful fill obtainable without L2 depth-of-book, and the
ground-truth model the fidelity harness (PB.5) compares the cheaper models against.

## Data dependencies

| Phase | Needs |
|---|---|
| PB.1–PB.3 | the 1/min NBBO already in `quotes/` (Tier 1 — no new download) |
| PB.4 / PB.5 | the raw `trades/` tape (Tier 2 — `--trades-only` backfill, PA.4) |

## dataset_hash + suitability

- **Hashing (PB.6):** the trade tape enters `dataset_hash` **only** when a run
  consumes it (`execution.fill_model` or `exits.fill_model == "tape_replay"`), via
  the gated `trades_partitions_hash` in `data/lineage.build_dataset_lineage`.
  Legacy runs are byte-identical; two tape-replay runs over different trades hash
  distinctly. `trades/` and `quotes_fine/` are siblings of `quotes/`, so a backfill
  never drifts the canonical `quote_partitions_hash` (Guardrail 2).
- **Suitability:** `tape_replay` stays an **opt-in knob** (not a new mode, not
  default-on in IR). `promotion/suitability.decide_suitability` caps any run that
  consumed the tape at `research_only` regardless of mode/feed (the manifest
  carries `fill_model.consumes_trade_tape`), until the model is deliberately
  promoted — mirror the `fast_realism` → `derive_validation_config(enable_tape_
  replay=True)` → IR-validate → deploy workflow. A config that requests
  `tape_replay` on a lake with no `trades/` logs a loud warning (every fill would
  otherwise silently fall back to legacy).

## Validation — measured on the real tape (PB.5 / PC.3)

Sell-side fills and the tape oracle are validated against the **real trade tape**,
not synthetic fixtures. Pure-function unit tests cover the math
(`tests/unit/sim/test_tape_fill.py`, `tests/parity/test_walk_lot_exit_numpy_parity.py`)
and the engine routing (`tests/unit/sim/test_tape_replay_routing.py`,
`tests/unit/sim/test_tape_replay_pb6.py`).

**PB.5 fill fidelity** (`scripts/_validate_fillmodel.py`, SIP lake, artifact
`artifacts/pb5_fill_fidelity.txt`) samples real `(symbol, minute)` points and
compares the legacy fill (100 % at the bar price, 0 bps) to `replay_tape_fill`
over the actual prints:

| order | SELL full-fill | SELL slippage (median / p10) | BUY full-fill | BUY slippage (median / p90) |
|---|---|---|---|---|
| $4 000 | 82 % | −2.4 / −24 bps | 79 % | +4.2 / +28 bps |
| $25 000 | **33 %** (fill-frac 0.49) | −5.9 / −31 bps | 33 % | +8.2 / +37 bps |

Legacy assumed every order fills 100 % at 0 slippage; the real tape shows partial
fills (a $25 k order fills *half*) and a real give-up that **grows with size** —
exactly the optimism PB.1–4 remove.

**PC.3 end-to-end exit PnL** (`scripts/_pc3_exit_pnl.py`, artifact
`artifacts/pc3_exit_pnl.txt`) drives the real `walk_lot_exit` over real bars+tape,
legacy vs `tape_replay`, entry held fixed: tape realized PnL is **27.6 % worse at
$8 k / 38.1 % worse at $30 k** than the legacy bracket fills (all of the delta is
on the lots that hit a stop/target; every tape lot is ≤ legacy — 0 fill better).
The legacy backtest overstates PnL by that much from exit-fill optimism alone.

> The full-pipeline backtest A/B was attempted but the scanner emits 0 candidates
> on a scoped window (the PIT universe screens to empty — a universe issue
> orthogonal to the fill model), so PC.3 drives the exit engine directly instead.

**Target-side fill (resting limit, not through-VWAP).** A take-profit is a
*resting* limit sell, so `_tape_replay_bracket` fills a `kind="target"` exit **at
the limit** (the bracket/target price) — the ≥target tape volume governs only
whether it fills, not the price (a passive limit never gets price improvement
above its price). A triggered STOP and a marketable BUY are *aggressors* that
sweep liquidity, so they correctly pay the realized VWAP and are NOT clamped.
(Before this clamp the target used the ≥target VWAP, which made ~25 % of bracket
lots fill *better* than legacy; PC.3 above confirms the clamped model is uniformly
≤ legacy.)

## See also

- `docs/data_lake_layout.md` — the `trades/` + `quotes_fine/` partitions.
- `docs/alpaca_fill_realism_implementation_plan.md` — the phase plan + guardrails.
- `sim/exits.py` (sell side) · `sim/fills.py` (`_t3_depth_impact_fill`, buy side) ·
  `sim/tape_fill.py` (oracle).
