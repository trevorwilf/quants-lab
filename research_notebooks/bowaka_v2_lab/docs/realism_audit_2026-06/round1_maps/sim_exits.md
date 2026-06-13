The only cooldown/reentry references in strategy_consumer.py are the docstring mentions; the actual `same_symbol_entries_per_day` / `max_lots_per_symbol` are the re-entry governors. I have enough to write the report.

## Purpose & data flow (how this subsystem fits the backtest pipeline)

`strategy_consumer.py` is the **entry-side** adapter: the backtester feeds it one candidate event at a time via `StrategyConsumer.consume()`. It runs the gate chain (signal-strength → quote build → spread/age → PARENT_ACK price-chase/halt → multi-lot/same-symbol → compounding-floor → risk gates → sizing), then simulates the entry fill (`simulate_market_fill` / `simulate_marketable_limit_fill` / `_tape_replay_fill`), and on a real fill constructs a `Position` with brackets priced off the **actual fill price**. Output is a `StrategyConsumerResult` (decisions, positions, parent orders, fill records).

`exits.py` is the **exit-side** engine. `walk_lot_exit()` is the live dispatcher: it walks the per-lot minute path from the bar *after* the fill minute and returns the earliest `ExitEvent` (stop/target/gap/time/max-hold/fade/halt). It dispatches to a numpy fast path (`_walk_lot_exit_numpy`) or the pandas reference oracle (`_walk_lot_exit_pandas`), which must be byte-identical. `evaluate_exits()` is the legacy daily-bar evaluator used only in `smoke_fixture` mode. The two files are joined by the backtester's event dispatcher (not in scope here), which threads quote/trades/status suppliers.

## Behavioral spec

**Exits — minute walk (both numpy & pandas paths mirror each other):**
- Bracket priced lazily: if `pos.stop_price`/`target_price` is `None`, computed from `entry_price*(1±pct)` (exits.py:670-675, 1039-1044).
- Bars at/before `fill_minute` skipped; never exits on fill bar (766-767, 1139-1140).
- `until_ts` bounds the walk; bars past it `break` and lot stays open, NO max-hold fallback (768-769, 933-934 / 1141-1142, 1298-1299).
- Bars past `exit_session` (max-hold horizon) `break` (771-772, 1144-1145).
- MFE/MAE excursion accumulated per bar via `max`/`min` (pandas 781-782) vs `if h>peak`/`if l<trough` (numpy 1154-1157) — claimed equivalent incl. NaN.
- **Intrabar ordering per bar:** halt-resume → venue-status defer → gap-through (open) → stop/target/same-minute → signal-fade → time-stop → max-hold (785-925 / 1160-1294).
- **Gap-through** (Task 2): minute `open<=stop` → `gap_stop` at open; `open>=target` → `gap_target` at open; checked before intrabar low/high (816-832 / 1185-1201). Gap fills at the open price, NOT via `_bracket_fill` (no spread/impact/tape applied to gaps — see Leads).
- **Same-minute both-touched**: `_resolve_same_minute` (322-337); conservative→stop, optimistic→target, random_with_seed→seeded coin flip on `seed|position_id|ts`. `exits.same_minute_tie` (`stop_first`/`target_first`) overrides `simulation.same_minute_resolution` (705-714 / 1063-1071).
- **Stop/target fills** go through `_bracket_fill` (859-869 / 1228-1238) which applies PB.1 spread / PB.2 impact / PB.3 freshness / PB.4 tape.
- **Signal fade** (Task 5): at first bar with `clock>=eval_time` per session date, re-score via `signal_score_fn`; `_fade_trip` returns tightest `exit_on` threshold the score is below (`score<value`). If `fade_active`→exit at `_next_bid`; else append `FadeTelemetry`, lot stays open (874-908 / 1240-1275).
- **Time stop** (Task 3): `clock>=exit_time` (default 15:45 ET) → exit at `_next_bid` (911-915 / 1277-1284). Default `enabled=True` when a `time_stop` block exists, but `False` when the block is absent (`{}` is falsy) (682, 1051) — see Leads.
- **Max hold** (Task 4): on/after `exit_session` with `clock>=15:59` → exit at close (919-925 / 1287-1294). End-of-walk fallback closes at last bar's close on/before exit_session (935-949 / 1300-1313).
- **Severe-stress halt** (Task 7): first bracket trip under `cost_stress=="severe"` sets `halt_until=ts+60s` and `continue`s; first bar at/after `halt_until` force-exits at `_next_bid` as `halt_resume_exit` (789-842 / 1161-1209).
- **Venue-status defer** (Task 3 robustness): status in {halted,pending_review,luld_pause} → `continue` (skip bar) (802-812 / 1171-1182).
- `_next_bid` is quote-aware (bid) else minute close (340-367). `_exit_bid` returns `None` when no quote (no close fallback) (370-404).
- **Tape-replay target clamp** (PC.3): a target fills AT the limit price, not the ≥target VWAP; a stop fills at swept VWAP (508-518). PB.4 falls back to PB.1-3/legacy when no tape (548-552).
- `_mk_exit` computes slippage: bracket override if given; else discretionary exits measured vs entry price, gap exits vs bracket ref (1420-1432).
- **Daily evaluator** `evaluate_exits` (smoke only): stop/target at exact bracket price, `time_stop` via `trading_days_since>=max_hold_days` (1453-1499).

**Entry consumer:**
- Reject `signal_strength<min_signal_strength` as `lost_signal_before_entry` (277-284).
- Quote via `resolve_quote`; missing→`missing_quote` reject + counter (318-326). Spread/age rejects (330-349).
- PARENT_ACK price-chase band (sig×[1-0.03, 1+0.10]) and halt gate; in `intended_realism`, supplier `None`→`halt_data_unavailable`; else silent fail-open (193-230).
- Same-symbol/day cap (scanner-first, risk fallback), max-lots cap (388-426).
- Compounding overlay: floor-halt refuses entries; otherwise grows equal-slice bankroll (432-445).
- Sizing equal_slice/fixed_dollar (64-102); `size_quantity` floor-div; qty==0→`lost_signal_before_entry` (477-486).
- `pre_submit`/`post_submit` event sequencing (530-586); broker reject never creates position.
- Fill sim, then brackets off `round(fill_price*(1±pct),4)` (781-782); position created `PARENT_FILLED` (realism/parity) or `PROTECTED` (smoke) (800-839).

## Knobs

- `exits.stop_pct`/`stop_loss_pct` (0.02), `target_pct`/`take_profit_pct` (0.06), `max_hold_days` (5) — consumer 492-494.
- `exits.time_stop.enabled` (True if block present), `.exit_time` (15:45) — 682-683.
- `exits.signal_fade.enabled` (False), `.eval_time` (15:45), `.score_thresholds` ({soft .34/hard .50/critical .67}), `.exit_on` (hard,critical), `.initial_mode`/`signal_fade_mode` (telemetry_only), `.activation_state`, `.activation_artifact_dir` — 685-697, 276-319.
- `exits.same_minute_tie` (overrides `simulation.same_minute_resolution`) — 705-714.
- `exits.cross_spread` (False, PB.1), `participation_cap` (None, PB.2), `impact_coef_bps` (10), `impact_model` (sqrt), `require_fresh_quote` (False, PB.3), `max_quote_age_seconds` (15), `fill_model` (legacy, PB.4), `tape_window_seconds` (300), `tape_participation` (1.0) — 717-729.
- `simulation.same_minute_resolution` (conservative), `.quote_fallback_policy` (zero_spread), `.accepted_event_sequencing`, `.mode` — sim cfg.
- `backtest.cost_stress` (conservative; `severe`→halt model), `slippage_bps_offset`, `spread_multiplier`, `use_adv_bucket_caps`, `no_fill_bar_range_active`, `adverse_selection_active`, `late_day_active` — 264-271.
- `sizing.sizing_mode` (equal_slice), `bankroll_fixed_dollars` (90000), `max_concurrent_positions` (18), `equal_slice_bankroll_fraction` (0.80), `min_order_notional`, `max_per_trade_dollars`, `dollars_per_position`, `max_position_dollars`, `compounding.{enabled,base_dollars,cap_multiple=4,floor_fraction=0.50}` — 64-134.
- `scanner.same_symbol_entries_per_day` (1), `min_signal_strength` (0) — 274-276, 388-393.
- `risk.max_lots_per_symbol` (1) — 417.
- `execution.{order_type,max_quote_age_seconds=5,max_spread_bps=50,price_chase_gate,halt_gate,liquidity_proxy_adv_frac=0.05,commission_per_share,regulatory_fee_bps,market_impact_*,minute_volume_participation_frac=0.10,marketable_limit_*,fill_model,tape_*}` — throughout consume.

## Invariants & guards

- Numpy/pandas exit paths pinned byte-identical by `test_walk_lot_exit_numpy_parity.py`; `_FAST_EXIT_WALK` kill switch + `_FAST_EXIT_WALK_MIN_BARS=3` threshold (958-994).
- `_COST_STRESS_SLIPPAGE_MULT` mirror of fills constant; comment says a test asserts equality (407-409).
- Broker reject never creates a position (both sequencing modes).
- **Silent fallbacks (flagged):**
  - `_next_bid` silently falls back to minute **close** when no quote (367) — masks missing-quote in time-stop/max-hold/fade/halt exits.
  - `on_parent_ack` halt gate **silently fails open** in non-realism modes when supplier returns `None` (224-225).
  - All supplier calls (`quote_supplier`, `trades_supplier`, `status_supplier`, `signal_score_fn`) wrapped in bare `except Exception` → treated as "no data" (358, 395, 493, 805, 883, 1176, 1251) — a supplier bug is silently swallowed.
  - `_activation_artifact_present` returns `False` on any OSError/ValueError (271-273) — a corrupt artifact silently de-activates fade.
  - `trading_days_since` / `max_hold_exit_session` silently fall back to `pd.bdate_range` (ignores holidays) if `xcals` import failed (138-140, 159-162).
  - Tape replay supplier exception → `None` → silent fall-through to legacy fill (493-494, 669-670).

## Leads

- exits.py:682,1051 — `time_stop_enabled = bool(...enabled, True) if time_stop_cfg else False`: an **absent** `time_stop` block disables the time stop, but a *present empty* block defaults it ON. Asymmetric/surprising default; smoke vs realism configs may diverge.
- exits.py:816-832,1185-1201 — gap-through fills at the raw `open`, bypassing `_bracket_fill` entirely, so PB.1 spread / PB.2 impact / PB.3 freshness / **PB.4 tape** are NOT applied to gap exits while non-gap stop/target exits ARE. Realism asymmetry; gap stops are optimistic (no give-up).
- exits.py:919,1287 — max-hold uses `clock>=15:59`. If the minute supplier lacks a 15:59-16:00 bar (early close days, gaps), the inline max-hold never fires and only the end-of-walk fallback (last bar close) saves it — but on an early-close session at 13:00 the `15:59` gate is unreachable, so the lot rides to the fallback at a wrong/late price.
- exits.py:866-869 / 854-857 — same-minute target uses `kind="target"` which (PB.4) clamps the fill to exactly `target_price`, but a same-minute *stop* winner under severe gap could realize worse than stop; gap-stop path (no `_bracket_fill`) and stop-bracket path price the SAME event differently. Inconsistent stop pricing across branches.
- exits.py:891,912,1259,1280 — fade/time-stop exit at `_next_bid`, which silently uses minute close when no bid. In `intended_realism` this manufactures a fill at close even when the lake has no quote — contradicts the missing-quote-rejects intent on the entry side.
- exits.py:1409-1412 — `_mk_exit` MFE/MAE guards `state.peak>0` / `state.trough<1e30`; a lot that exits on the FIRST eligible bar via gap (peak/trough only updated AFTER... actually updated before gap at 781-782/1154-1157, OK) — but for the numpy path the excursion update is skipped on the halt-resume/status `continue` branches inconsistently; verify peak/trough parity on halted bars.
- exits.py:789-796 — halt-resume force-exit fires on the FIRST bar at/after `halt_until` regardless of whether that bar still trips the bracket; under severe stress a 60s halt always converts a bracket touch into a `_next_bid` exit (could be far from stop/target). Models halt as a guaranteed adverse exit — may be too punitive or too lenient depending on direction.
- exits.py:1287-1293 — numpy max-hold takes `px=c` unconditionally (comment says close never None for eligible frame) but `c` can be **NaN** (present-NaN); `float(NaN)` exit price would propagate a NaN PnL silently.
- strategy_consumer.py:594-599 — `entry_date` falls back to `_dt.date.today()` when `ts_pts` isn't a string — non-deterministic wall-clock date leaks into a backtest position.
- strategy_consumer.py:822,836-838 — `entry_timestamp`/`parent_fill_ts` set to `scan_timestamp`, NOT the marketable-limit fill minute. Comment admits it's a "conservative anchor", but the exit walk then skips bars up to scan-minute — a fill that lands minutes later has its early adverse path ignored. Realism gap.
- strategy_consumer.py:288-294 — `last_price`/`adv`/`volatility_pct` use `... or 5_000_000.0` / `or 0.02` defaults: a legitimately-zero ADV or ATR is silently replaced by a fabricated value feeding `resolve_quote`. Masks bad data.
- strategy_consumer.py:417 — `max_lots_per_symbol` read from `risk.` only, while `same_symbol_entries_per_day` accepts scanner-or-risk; inconsistent config location handling for two sibling caps.
- strategy_consumer.py:703 — comment "limit treated as marketable_limit": a plain `limit` order_type silently routes to the marketable-limit fill (crosses spread), overstating fill probability for true passive limits.
- strategy_consumer.py:660-665 — tape-replay limit ceiling uses `marketable_limit_slippage_pct` OR `limit_offset_bps/10000`; the same dual-key default appears at 707-708 — duplicated default logic, drift risk.
- strategy_consumer.py:400-405 — for caps>1, `lots_today` counts `positions_for_symbol` with `entry_session==session_date`, but `positions_for_symbol` returns only **open** lots; a same-symbol lot already closed this session is NOT counted, so the daily cap can be exceeded across intraday round-trips. Realism/correctness gap.
- exits.py:166 — `max_hold_exit_session` window heuristic `steps*4+10` days could under-cover very large `max_hold_days` (long holiday clusters), silently returning `sessions[-1]` short of the intended horizon.
- exits.py:1308-1313 — numpy end-of-walk fallback uses `c_arr[last_i]` but `c` from the loop may be stale; uses `c_arr[last_i]` correctly — but `float(px)` again NaN-unsafe.

## Test coverage hooks

Exercised: numpy/pandas parity (`test_walk_lot_exit_numpy_parity.py`), stop/target first (`test_exit_stop_first`, `test_exit_target_first`, `test_exit_same_minute_stop_wins`, `test_sim_ambiguity_resolution`), gaps (`test_exit_gap_below_stop`, `test_exit_gap_above_target`, `test_gap_through_stop_fills_at_open`), time-stop (`test_exit_time_stop`), max-hold (`test_exit_max_hold_trading_days`, `_skips_holiday`, `test_max_hold_exit_at_session_open`), fade (`test_exit_signal_fade_active`, `_telemetry`, `_default_initial_mode_is_telemetry`, `test_signal_fade_active_after_activation_artifact`), halt (`test_halt_then_exit_deferred`, `test_halt_gate_rejects_halted_symbol`, `test_intended_realism_fails_when_halt_data_absent`), window boundary (`test_close_lots_until_window_boundary`), sizing/compounding (`test_compounding_sizing`, `test_config_parity_sizing`), tape routing (`test_tape_replay_routing`), brackets (`test_bracket_pricing_actual_fill`), multi-lot (`test_portfolio_max_lots_per_symbol`, `test_portfolio_same_symbol_entries_per_day`, `test_same_symbol_entries_per_day_propagation`), sequencing/RNG/price-chase/broker (`test_decision_sequencing_*`, `test_strategy_consumer_rng_deterministic_across_processes`, `test_price_chase_gate_rejects_*`, `test_sim_broker_reject_emits_canonical`).

**No direct test found for:** PB.1 cross_spread give-up, PB.2 participation_cap sqrt-impact, PB.3 stale-quote widening, severe-stress `halt_resume_exit` (vs venue-status defer), the `_next_bid` close-fallback in fade/time-stop, the `entry_date=date.today()` fallback, the caps>1 intraday-roundtrip same-symbol counting, NaN-close max-hold, gap-exit bypass of `_bracket_fill`, and `evaluate_exits` daily-bar path beyond ambiguity.