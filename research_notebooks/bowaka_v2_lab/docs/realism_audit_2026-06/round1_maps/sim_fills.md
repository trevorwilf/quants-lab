I now have a comprehensive understanding. Let me do one final check on the `_t1_fill` cent-walk over-fill concern and the participation cap denominator (window_qty vs filled in tape_fill). I've read all of fills.py already. The cent-walk at lines 814-830 uses `int(size_at_touch * cap)` per level — meaning each successive penny level can fill another full ask_size worth. Let me verify the fast_realism degradation and the `usable_at_touch <= 0` fall-through to limit price. I have everything needed.

Let me compose the report.

## Purpose & data flow (how this subsystem fits the backtest pipeline)

`sim_fills` converts an accepted parent order + a `QuoteSnapshot` into a `FillResult` (price, qty, fees, slippage, tier) — the only place a backtest manufactures an execution price. Flow: a config sets `execution.fill_model`/`order_type`; `data/suppliers.make_trades_supplier_for_config` wires a `trades_supplier` only for `tape_replay` (else `None`, keeping legacy byte-identical). `strategy_consumer._consume_one` (`strategy_consumer.py:306-349`) resolves the quote via `quote_model.resolve_quote` (historical → else `quote_fallback_policy`), applies spread/age gates, then routes the BUY entry: tape-replay first (`fills._tape_replay_fill` → `tape_fill.replay_tape_fill`, `strategy_consumer.py:656-680`), else `simulate_market_fill` or `simulate_marketable_limit_fill` (`strategy_consumer.py:683-737`). Brackets are computed off the *actual fill price* (`strategy_consumer.py:780-782`). SELL/exit fills are formed separately in `exits._bracket_fill` (`exits.py:524-577`), with its own `tape_replay` path (`exits.py:471-521`). `cost_model.py` and `adv_buckets.py` supply slippage bps and ADV-bucket caps; `quote_model.py` supplies real/synthetic quotes. The backtester schedules a `PARENT_FILL_TIMEOUT` event (`backtester.py:1637-1644`) purely as a log marker — the synchronous fill already realized the no-fill.

## Behavioral spec

**Tier detection** (`fills.py:73-97`): order T4(calibration)→T3(nbbo_depth)→T0(if `quote.source != "historical"`)→T2(historical + minute `volume` col)→T1. A non-historical quote is *always* T0 regardless of `has_nbbo_depth=False`.

**Market fill `simulate_market_fill`** (`fills.py:431-532`): if `has_nbbo_depth` → routes to `_t3_depth_impact_fill` (`:470-482`). Else applies spread multiplier, resolves fill-rate cap, `usable = int(liquidity_proxy*cap)`, `filled = min(qty, usable)`. Price (buy) `= quote.ask*(1+bp/1e4)` where `bp = slippage_bps(base,...)*stress_mult` (`:498-504`). Partial below `min_order_notional` → no-fill `partial_below_min` (`:509`).

**Marketable-limit `simulate_marketable_limit_fill`** (`fills.py:943-1209`): late-day multiplier scales spread+offset (`:1000-1003`); `limit_price = ask*(1+slippage_pct)` buy / `bid*(1-…)` sell (`:1007-1010`); optional bar-range no-fill (`:1014-1023`); detect tier; T0→`_t0_fill`; T3→`_t3_depth_impact_fill`; else `_ask_runs_above_limit` timeout check (`:1088`) then `_t1_fill`; T2/T4 apply minute-dollar-volume participation cap (`:1109-1143`); T4 applies calibrator residual shift (`:1152-1201`); finalize with offset/adverse/spread (`:1202-1209`).

**T1 fill `_t1_fill`** (`fills.py:774-864`): fills `min(qty, int(ask_size*cap))` at the touch; remainder walks **one cent per level** up to `limit_price`, **taking `int(size_at_touch*cap)` shares at *each* penny level** (`:825`), loop bounded at 100 iters; VWAP = notional/filled. If `usable_at_touch<=0` (zero displayed size) → fills *entire* qty at `limit_price` (`:804-808`).

**T0 fill `_t0_fill`** (`fills.py:867-940`): `intended_realism` → no-fill `t0_no_quotes_disallowed…` (`:893-897`); timeout via `_ask_runs_above_limit`; fills at `limit_price`, capped by `liquidity_proxy*cap`; slippage bps = `offset*1e4*stress_mult` (`:914`, note: recorded but price is just `limit_price`).

**T3 depth impact `_t3_depth_impact_fill`** (`fills.py:583-658`): `fillable = min(qty, int(max(touch_size, cap_shares)))` where `cap_shares = participation_cap*minute_vol_shares` (`:621-622`). Price = `ask*(1 + (half_spread_bps + impact_bps)/1e4)`; `impact_bps = impact_coef_bps*frac*stress_mult`, `frac = sqrt(participation)` or linear (`:626-640`).

**Tape replay entry `_tape_replay_fill`** (`fills.py:661-719`): calls `replay_tape_fill`; BUY passes `max_price=limit`, SELL `min_price=limit`; tier tagged `T3_NBBO_DEPTH`; `None` on no-fill → caller falls back.

**`replay_tape_fill`** (`tape_fill.py:52-132`): consumes prints in `[start_ts, start_ts+window]`, taking `participation*size` of each, time-ordered, until qty met; VWAP = notional/filled; `filled=True` only if whole qty absorbed; `min_price`/`max_price` filter eligible prints.

**Exit bracket `_bracket_fill`** (`exits.py:524-577`): tape_replay first; else legacy `(bracket_price, None)` exact-fill; `cross_spread` sells at `min(bracket, bid*(1-half_spread_bps/1e4))`; stale/absent NBBO under `require_fresh_quote` widens give-up by 2×half-spread (`:563-566`); `participation_cap` applies sqrt impact (`:568-574`). Exit tape (`exits.py:508-516`): TARGET fills *at* the limit (PC.3 clamp), STOP pays swept VWAP.

**Cost stress** (`fills.py:99-114`): slippage ×{1,2,3.5}; legacy fill-rate cap {1,0.85,0.60}. Adverse-selection tiers, spread multipliers, slippage offsets, late-day ramp all opt-in, no-op at base.

## Knobs

- `execution.fill_model` (`legacy`/`tape_replay`, default `legacy`; models.py:319) — tape_replay only fires if supplier wired *and* tape non-empty; else byte-identical fallback. Threaded via suppliers→strategy_consumer:656.
- `execution.order_type` (`marketable_limit`/`market`/`limit`, default `marketable_limit`; models.py:304) — `limit` treated as marketable_limit (`strategy_consumer.py:703`).
- `marketable_limit_slippage_pct` (0.005; consumer:707) — limit offset over ask.
- `marketable_limit_timeout_seconds` (30; consumer:711) — seconds-resolution timeout.
- `max_quote_age_seconds` (5, models.py:306) — entry stale-quote reject (`strategy_consumer.py:341`).
- `max_spread_bps` (50, models.py:307) — wide-spread reject (`strategy_consumer.py:332`).
- `minute_volume_participation_frac` (0.10, models.py:314) — T2/T3 cap.
- `market_impact_coef_bps` (10.0), `market_impact_model` (`sqrt`/`linear`) — T3 impact.
- `liquidity_proxy_adv_frac` (0.05; consumer:605) — liquidity proxy shares.
- `commission_per_share` (0.0), `regulatory_fee_bps` (0.0) — fees default $0.
- `tape_window_seconds` (300.0), `tape_participation` (1.0) — both entries+exits.
- `exits.cross_spread`/`participation_cap`/`require_fresh_quote`/`impact_coef_bps`/`max_quote_age_seconds`(15) — sell-side (models.py:421-434).
- `simulation.quote_fallback_policy` (`zero_spread`/`synthetic_calibrated`/`require_real`) — quote_model:222.
- `cost_stress`, `adv_dollar` (ADV-bucket cap opt-in), `spread_multiplier`, `slippage_bps_offset`, `*_active` stress flags.

## Invariants & guards

- `intended_realism` + T0 → hard no-fill (`fills.py:893-897`); honest fail-loud.
- `require_real` policy + no historical quote → `missing_quote` reject (`quote_model.py:242`, `strategy_consumer.py:318`).
- `_t1_fill`: `touch<=0` → no-fill (`fills.py:800`).
- Tape supplier honesty warning when `tape_replay` requested but lake has no `trades/` partitions (`suppliers.py:299-317`) — **WARN only, not fatal: every fill silently falls back to legacy.** Flagged silent fallback.
- **Silent fallback:** `trades_supplier` exception → `_fwd_trades=None`, falls to legacy tier (`strategy_consumer.py:669-670`); same in exit (`exits.py:493`).
- **Silent fallback:** empty/no-qualifying tape → legacy bracket / tier (tape_fill returns no-fill, callers fall through).
- **Silent fallback:** T4 calibrator import failure swallowed `except Exception` (`fills.py:1159`) → tier stays T4 but no residual applied.
- **Silent fallback:** late-day minutes-to-close computation `except Exception → None` disables late-day silently (`strategy_consumer.py:626-627`).
- `_apply_spread_multiplier`/offset/adverse all return unchanged at defaults (parity anchor).
- `adv_buckets`: base cap=1.0 every bucket (parity anchor, adv_buckets.py:34-39); below-floor ADV → most-liquid bucket (no penalty, `:42-53`).
- `cost_model.get_params` raises on unknown stress (`cost_model.py:29`) — fail-loud.
- `replay_tape_fill` requires `timestamp/price/size` cols else no-fill (`tape_fill.py:79`).

## Leads

- **`fills.py:825` — T1 cent-walk fills `int(size_at_touch*cap)` shares at EVERY penny level**, so a single quote's displayed `ask_size` is treated as available repeatedly (up to 100×) as the price walks to the limit. This manufactures liquidity far beyond the one displayed top-of-book size — the central over-fill realism gap. Matches MEMORY "the sim FILL model manufactures liquidity."
- **`fills.py:804-808` — zero displayed `ask_size` (or `bid_size`) fills the ENTIRE requested qty at `limit_price`** with `is_partial=False`. A quote with no size becomes unlimited liquidity at the limit — opposite of conservative.
- **`fills.py:622` — T3 `fillable = min(qty, int(max(touch_size, cap_shares)))`** uses `max`, so even when participation cap is *tiny*, the full displayed `touch_size` is always fillable; and when `cap_shares` huge, fills far beyond the touch. `max` (not `min`) means the cap can't tighten below the touch — questionable as a "depth" model.
- **`fills.py:914` — T0 records `slippage_bps_total = offset*1e4*stress_mult` but the fill price is plain `limit_price`**; the recorded slippage and the price are inconsistent (slippage metric doesn't match realized price vs ask/mid). Misleading attribution.
- **No latency modeling anywhere** — fill is synchronous at `scan_ts`; `fill_time_seconds` is hard-coded `0.0` (`fills.py:863,939`). Quote age gates entry but no execution latency between decision and fill. Realism gap.
- **`fills.py:206` / `_forward_window`** uses minute bars *at/after* `scan_ts` including the scan bar itself for slippage/timeout — `_ask_runs_above_limit` reads `fwd[col].min()` over the whole window; potential look-ahead into the scan minute's full high/low which isn't yet known at decision time.
- **`fills.py:753` semantics contradiction:** docstring (`:738-741`) claims "FIRST bar high above limit → timeout" but code returns `fwd[col].min() > limit_price` (ALL bars above). Documented intent ≠ behavior; flagged.
- **`tape_fill.py:103` `window_qty` computed but `filled=True` only requires `filled_qty>=req`** — participation is applied per-print but a single huge print lets `take=remaining` consume up to `participation*size`; if `participation=1.0` (default) the order can consume an entire print, i.e. 100% of one trade's size — unrealistic for a marketable order vs tape.
- **`exits.py:516` TARGET tape fill clamps to bracket price** but STOP pays VWAP — asymmetric optimism control; fine, but the legacy default `_bracket_fill` (`:553-554`) still fills *exactly at bracket with zero slip* when `cross_spread`/`participation_cap`/`tape` all off — the dominant default path has **zero exit slippage**. Major realism gap at defaults.
- **`fills.py:1118` T2 cap** `cap_qty = int(cap_notional/price)` then `min(cap_qty, filled_qty)` — but the T1 fill it caps was *already* an over-filled cent-walk VWAP; capping notional after over-filling doesn't fix the manufactured depth.
- **`quote_model.py:124` synthetic_calibrated quote hard-codes `bid_size=ask_size=10_000`** and zero_spread sets size `0.0` — synthetic quotes carry fabricated/zero sizes that then drive T1/T3 fill logic.
- **`fills.py:488` `int(liquidity_proxy*cap)` floors to 0 for tiny proxies** → `no_liquidity` reject; but `liquidity_proxy_shares=None` (no ADV) → unconstrained full fill (`:491-493`). Missing-ADV = unlimited liquidity.
- **`cost_model.py:21` commission folded into `commission_bps` of notional** AND separately `commission_per_share` exists in fills — potential double-counting if both wired.
- **`adv_buckets.py:35` micro bucket floor 2.5e5** but MEMORY notes the universe is $250k-ADV illiquid; base cap 1.0 means *no* partial-fill protection at base stress for microcaps.
- Dead/scaffold: `simulate_fill` back-compat shim (`fills.py:1212-1254`) only used by legacy tests; T4 calibrator path requires both flags + artifact, likely never exercised in production runs.

## Test coverage hooks

Covered: `test_fill_market_full.py`, `test_fill_partial_below_min.py`, `test_fill_marketable_limit_timeout.py` (+integration sub-minute timeout, T1 immediate/partial), `test_fills_t3_depth_impact.py`, `test_t0_no_quotes_fails_intended_realism.py`, `test_cost_stress_severity.py`, `test_adv_bucket_cap_*` (2), all stress dims (`test_stress_*` ×5), `test_tape_fill.py`/`test_tape_replay_pb6.py`/`test_tape_replay_routing.py`, `test_quote_fallback_synthetic_calibrated.py`, `test_slippage_calibrator_roundtrip.py`, `test_fast_realism_fill.py`, `test_forward_window_parity.py`.

**No dedicated test for:** the T1 cent-walk per-level `size_at_touch*cap` over-fill (the core realism bug — no test asserts total fill ≤ displayed size); the zero-`ask_size`→full-fill-at-limit branch (`fills.py:804-808`); T0 slippage-vs-price inconsistency (`:914`); exit `_bracket_fill` default zero-slip path; the `_ask_runs_above_limit` doc-vs-code `min()` contradiction; `simulate_market_fill` with `liquidity_proxy_shares=None` unconstrained-fill; latency (none exists to test); `_minute_dollar_volume` fallback column chain. `simulate_fill` shim has no listed test beyond legacy callers.