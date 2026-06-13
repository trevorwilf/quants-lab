I have everything needed. The strategy file is fully read end-to-end, config is read in full, schemas and the retighten one-shot are read. I have the test inventory. Producing the report.

## Purpose & data flow (how this subsystem fits the backtest pipeline)

`bowaka_v2_strategy.py` is the **LIVE production entry consumer** the simulator must replicate. It tails an append-only `candidate_events.jsonl` (produced by the scanner), applies execution + risk gates, sizes, submits market buys to OpenAlgo `/api/v2`, attaches OCO brackets to filled parents, polls fills, manages exits (target/stop/time-stop/protected-flatten/kill-switch), and writes closure records to a ledger + daily-summary that drive compounding. It is NOT a per-bar engine: it runs a wall-clock loop every `loop_interval_seconds` (5s), driven by an external event file and live broker REST polling. The lab's parity anchor is `bowaka_v2_config.yaml` (winner trial #3155 applied 2026-06-11). The sim mirror is `src/bowaka_v2_lab/sim/strategy_consumer.py`, `risk_gates.py`, `protection.py`.

## Behavioral spec

**Startup gate** (`validate_startup_config`, :96-120): refuses unless `strategy.mode=="forming_daily_bar_monitor"` (:103); if `environment=="live"` AND `feed!="sip"` AND `data.live_requires_sip` (default True) → ConfigError (:111). Non-SIP only logs a WARNING otherwise (:116). `main` returns 5 on ConfigError (:1828).

**Main loop** (`main`, :1798-2035): one-shot if `--dry-run/--once/--replay-from` (:1864-1869). Long loop (:1931): checks kill flags in order KILL_HARD→KILL_SOFT→KILL_NEW (:1933,1951,1970); L3 flattens best-effort, writes state, returns 99 (:1947); L2 flattens once, stays alive, releases mark when flag cleared (:1951-1966); L1 skips the entry-consume tick only (:1973-1984). Post-fill plumbing (poll_fills → submit_pending_oco → enforce_protected → run_time_stop) only runs when `live_client and oa_module` present (:1991-2021). Sleeps in 0.5s chunks honoring shutdown (:2028-2031).

**Entry pipeline** (`consume_candidate_events`, :748-1026): session rollover resets `entered_today/daily_entries_count/daily_realized_pnl_strategy/gross_exposure_dollars` on ET-date change (:776-784); migrates open_positions to link_id keys (:788). Per event: schema-validate (:805) → stale-session reject as `lost_signal_before_entry` (:812) → expiry reject as `lost_signal_before_entry` (:821) → same-symbol-today dedupe (:831) → max_lots_per_symbol cap (:844) → size → qty≤0 rejects as `adv_cap` (:863) → quote gate → price-chase gate → halt gate → risk gates (:877-887) → accept, emit shadow-risk, submit, record pending (:920-996). Order style from `execution.parent_order_style` ("market", :924).

**Sizing** (`size_position`, :654-673): `target_notional = equal_slice_bankroll_fraction * bankroll / max_concurrent_positions` (:666), floored at `min_order_notional` (:668), `qty = int(target_notional // current_price)` (:672). `_sizing_bankroll` (:606): base unless `compounding.enabled`, then `clamp(base+cumulative_realized, 0, cap_multiple*base)` (:616-618). NOTE: sizing uses `current_price=signal_price` (forming bar last_price), not the live quote (:861).

**Risk gates** (`_risk_gates`, :436-514) in order: bankroll-floor-halt FIRST (:449, dominates even at negative equity) → max_concurrent_positions (:467-469) → max_total_entries_per_day (:473) → gross_exposure_cap projected (:482-487) → daily_loss_pct→`kill_switch` (:490-494) → tiered ADV cap on aggregate symbol notional (:500-512). Risk gates anchor bankroll to base via fallback `bankroll_fixed_dollars` (:480), NOT compounded equity (deliberate, :889-894).

**Quote gate** (`_quote_gate`, :372-397): None quote→`quote_stale` (:378); require bid/ask>0 (:383); spread_pct computed from bid/ask if absent (:388); `>max_spread_pct`→`spread_too_wide` (:392); age>`max_quote_age_seconds`→`quote_stale` (:395). **Price-chase** (:400-418): mid/signal_price-1 outside [`min_pct_below`,`max_pct_above`]→`price_chase_band`. **Halt** (:421-430): status in {halted,pending_review,luld_pause}→`halt_or_pending_review`.

**Order submit** (:945-973): calls `submit_supplier`; validates `_http_status in (200,201)` before mutating state (:957); extracts parent_order_id from data.order_id/id/native_response.id (:965). Live buy is `submit_market_buy` TIF=DAY (:1908).

**OCO attach** (`submit_oco_children_v2`, :1146-1229): idempotent if both child ids set (:1159); target=`round(entry*(1+target_pct),2)`, stop=`round(entry*(1-stop_pct),2)` (:1175-1176); TIF from `exits.oco_time_in_force` default GTC (:1178); parses legs by order_type "limit"/"stop" with parent-id fallback for target (:1199-1208).

**Fill polling** (`poll_fills_v2`, :1262-1365): GET all orders, index active orders only (:1277); parent FILLED → status=filled, entry_price=filled_avg, qty=filled_qty, seeds peak/trough (:1313-1322); dead-status parent with filled_qty>0 treated as filled (:1332), else popped (:1346). Child target/stop/exit FILLED recorded (:1351-1364).

**Exits**: `process_fill_events_v2` (:1471-1511) maps target→`target_hit`, stop→`stop_hit`, exit→pos.exit_reason. `trigger_exit_v2` (:1514-1599): no-op unless status=="filled" (:1526); reserves status="exit_pending" before I/O (:1533); cancels OCO children; submits market sell; reverts to "filled" on any failure (:1560,1573,1584). `run_time_stop_pass_v2` (:1602-1626): exits when `_trading_days_since >= max_hold_days`. `_trading_days_since` (:1368-1382) uses `pd.bdate_range` Mon-Fri, NO holiday calendar.

**Closure** (`close_position_v2`, :1385-1468): `realized=(exit-entry)*qty` (:1402), no fees/slippage; appends closure to daily-summary + ledger; updates daily + cumulative realized PnL (:1448-1457); decrements gross exposure clamped≥0 (:1459).

**Protected-position** (`enforce_protected_position_invariant_v2`, :1715-1771): filled positions missing both OCO children for >`max_unprotected_seconds` (10) → market-flatten if `flatten_if_unprotected`.

**Retighten one-shot** (`_retighten_oco_at_market_open.py`): hardcoded RUM/BLMN lots, waits for cancels to clear, resubmits OCO, kills+patches state.json+relaunches watchdog. Refuses to patch if either leg id empty (:289-303, the 2026-05-27 incident guard). Roots at `E:\stocktradingsoftware\openalgo` (:30) and hardcodes target_pct=0.15 (:271,307).

**Time-of-day** behaviors (config, mostly NOT implemented in this module): session 09:30-15:55, scanner 09:45-15:30, `time_stop.exit_time=15:30`, `signal_fade.eval_time=15:45/telemetry_time=16:05`. The module has NO intraday time-stop-at-15:30 nor signal-fade code — those are config-declared but unwired here.

## Knobs (config field: default → effect → where)

- `strategy.mode` (forming_daily_bar_monitor): startup gate :103.
- `data.feed` (sip) / `live_requires_sip` (true) / `allow_non_sip_for_research_only` (false): startup gate :108-119.
- `session.loop_interval_seconds` (5): loop cadence :1876.
- `execution.parent_order_style` (market): order_plan + exec-quality :924,1020.
- `execution.quote_gate.{enabled true, max_spread_pct 0.0094, max_quote_age_seconds 104, require_bid_ask_positive true}`: :375-396.
- `execution.price_chase_gate.{enabled true, max_pct_above_signal_price 0.10, min_pct_below -0.03}`: :403-417.
- `execution.halt_gate.enabled` (true): :423.
- `execution.default_venue_code` (XNAS): :977,1163.
- `data.max_quote_age_seconds` (15) — UNUSED here (gate uses execution.quote_gate's 104).
- `sizing.equal_slice_bankroll_fraction` (0.7016): :665. `sizing.max_concurrent_positions` (**1**): slots AND concurrency cap :467,664. `min_order_notional` (500): :667. `bankroll_fixed_dollars` (90000): base+risk fallback :480,564.
- `sizing.compounding.{enabled true, base_dollars null, floor_fraction 0.50, cap_multiple 4.0}`: :614-632.
- `risk.daily_loss_pct` (0.0918)→kill_switch :490. `max_gross_exposure_pct` (0.8514) :482. `max_total_entries_per_day` (14) :473. `max_lots_per_symbol` (4) :844. `adv_tier_caps` (5 tiers, reject <250k) :237-247,68-83. `risk.shadow.*`: telemetry-only blockers :517-545.
- `risk.strategy_slice_loss_pct` (0.025), `max_stopouts_per_day` (4), `stop_trading_after_consecutive_stopouts` (8): **read NOWHERE in this module** (dead in prod strategy; only in scanner/sim).
- `exits.{stop_pct 0.1038, target_pct 0.4, max_hold_days 10}`: :927-929,1166-1167,1610. `exits.oco_time_in_force` (default GTC, absent in yaml) :1178.
- `exits.time_stop.*`, `exits.signal_fade.*`: declared, NOT consumed in this module.
- `protected_position.{enabled true, max_unprotected_seconds 10, flatten_if_unprotected true, max_oco_attach_attempts 2}`: :1725-1728 (max_oco_attach_attempts NOT enforced — see Leads).
- `logging.emit_*` / `persist_config_snapshot`: emit toggles :136-180.
- `liquidity_monitor.enabled` (false): scaffold only :173.
- `paths.kill_switch_dir` (.): kill-flag dir :1877.

## Invariants & guards

- Order accepted only if broker `_http_status in (200,201)` before state mutation (:957-973) — fail-loud.
- `link_id` nanosecond-keyed open_positions (:982,1119) prevents lot overwrite/orphan.
- `_ledger_realized_sum` excludes bool from realized (:599), returns **0.0 on any read/parse failure** — SILENT FALLBACK (:601).
- `_reconcile_cumulative_from_ledger` OVERWRITES in-state cumulative from ledger on load (:641) — heals torn state but masks ledger loss silently.
- Atomic writes via tmp+os.replace for state + config snapshot (:644-651,196-198).
- `trigger_exit_v2` reserves status before I/O (:1533) and reverts on every failure path (:1560,1573,1584) — fail-safe.
- SILENT FALLBACKS to flag: quote_supplier None → synthesizes quote from signal_price with spread 0, age 0 (:872-876) — fabricated perfect quote bypasses spread/age gates offline. `_is_expired`/`_is_stale_session` swallow parse errors returning False (:280,285). ADV-cap gate wrapped in bare `except: pass` (:511) — any error silently allows entry. `poll_fills_v2` fetch failure returns [] (:1275). `_trading_days_since` returns 0 on parse error (:1378) — could suppress time-stop. malformed candidate line dropped with warn (:262). state load exception → empty dict, loses all positions silently (:1837).

## Leads

- :872-876 — offline quote fallback fabricates bid==ask==signal_price, spread_pct 0.0, age 0 → quote/price-chase gates ALWAYS pass when `quote_supplier=None` (every backtest/replay path). Realism gap: sim must NOT inherit this.
- :861 — sizing uses `signal_price` (forming-bar last_price), not the executable quote; live fills at market may differ, biasing qty/notional.
- :1402 — closure realized PnL has NO fees/commissions/slippage; pure (exit-entry)*qty. Backtest parity must match (or both are unrealistic).
- :1368-1382 — `_trading_days_since` uses `pd.bdate_range` with NO holiday calendar (acknowledged TODO at :1370); max_hold_days overcounts across holidays → premature time-stops.
- :467,664 — `max_concurrent_positions=1` is read as BOTH risk cap and sizing denominator; with frac 0.70 → target_notional ≈ $63k of $90k base into a single $1-20 microcap. Combined with ADV tier 0.015 cap this likely clamps hard; interaction worth checking.
- :490-494 — `daily_loss_pct` kill is checked per-candidate inside entry gating only; there is no portfolio-level mid-day flatten when the loss threshold trips (only refuses NEW entries). Config implies a kill_switch but exits aren't forced.
- `max_oco_attach_attempts` (config 2) is incremented (:1174) but NEVER compared/enforced — protected-position can retry forever; only the time-based flatten bounds it. Dead knob.
- `risk.strategy_slice_loss_pct`, `max_stopouts_per_day`, `stop_trading_after_consecutive_stopouts` — declared in yaml, consumed NOWHERE in prod strategy (sim has them via `risk_gates.py`). Parity divergence: sim enforces caps the live strategy does not.
- `exits.time_stop.exit_time=15:30` and entire `signal_fade` block — config-declared, NO code path in this module. Live strategy never does intraday 15:30 time-exit nor signal-fade exit; only max_hold_days. Major behavioral gap vs config intent.
- :1175-1176 — OCO target/stop rounded to 2 decimals; for $1-3 microcaps 1¢ rounding materially shifts effective stop/target_pct.
- :1864 — `--replay-from` forces one-shot (single tick) AND points consumer at alt file; multi-tick replay impossible via this flag.
- :476,533 — daily entry cap uses `>=`; with `max_total_entries_per_day` vs scanner `max_entries_per_scan=3` and `max_concurrent_positions=1`, only 1 position can ever be open — entries past 1 always hit max_concurrent.
- :1332-1340 — dead-status parent with partial fill is force-marked filled with NO OCO/peak seeding (skips :1320 peak init) → that lot enters protected-position flatten path.
- :199 (schemas) parity: `validate_candidate_event` requires schema_version==3; any sim producing v≠3 events is silently dropped as invalid (:807).
- :911 — rejection record for `qty<=0` mislabels reason as `adv_cap` even when cause is min_order_notional/price (:863).
- `_retighten` :30 — hardcoded `E:\stocktradingsoftware\openalgo` root and target_pct=0.15 (:271,307) diverge from config target_pct=0.4; one-shot is stale/incident-specific, effectively dead code in the mirror.
- :109,372 — `_quote_gate` default `qg.get("enabled", True)`: if quote_gate block absent gate runs with all-None thresholds (only require_bid_ask_positive default True fires). Threshold-less pass-through.

## Test coverage hooks

In-mirror tests are sim-side, not the prod module directly. Parity tests touching this contract: `tests/parity/test_config_parity_adv_tiers.py`, `test_config_parity_signals.py`, `test_risk_gates_adv_tier_aggregate.py`, `test_risk_max_concurrent_from_sizing.py`, `test_strategy_slice_loss_enforced.py`, `test_actual_contract_loaded.py`. Sim equivalents: `tests/unit/sim/test_compounding_sizing.py`, `test_sim_risk_stopout_caps.py`, `test_sim_portfolio_session_rollover.py`, `test_sim_quote_model_synthetic.py`, `test_sim_strategy_consumer_no_synth_default.py`, `test_broker_reject_decision_builder.py`, `test_event_schema_required.py`. Integration: `test_backtester_risk_kills.py`, `test_backtester_multi_day_hold.py`, `test_backtester_with_synthetic_quotes.py`.

**NO test coverage observed for (prod-module behaviors):** OCO leg-id parsing/fallback (`submit_oco_children_v2`), `poll_fills_v2` reconciliation incl. dead-status-partial-fill, `trigger_exit_v2` revert-on-failure paths, `enforce_protected_position_invariant_v2`, L2/L3/L1 kill-switch execution, `_trading_days_since` holiday gap, `_reconcile_cumulative_from_ledger` heal-on-load, `_ledger_realized_sum` silent-0 fallback, `max_oco_attach_attempts` (unenforced), and the `_retighten_oco_at_market_open` one-shot. These broker-state/race-condition paths (websocket-free REST polling, partial fills, cancel-queue races) are inherently HARD to simulate from bar/tape data and have no parity test.