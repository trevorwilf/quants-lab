I now have a thorough understanding. Let me verify one detail about the cost-model entry fill base vs conservative (the `base` adds half_spread to mid which equals ask, then adds impact — possible double-count vs conservative which pays ask). I have enough to write the report. Let me also confirm the schemas version and stream `falled_back_to_polling` typo, both confirmed in what I read.

I have read all required files end-to-end and have sufficient context. Here is the report.

---

## Purpose & data flow (how this subsystem fits the backtest pipeline)

`prod_execution` is the **live production strategy mirror** (`LAB\reference\source_strategy\scripts\`) — the source of truth the lab simulator must match. Data/control flow:

1. **Market data in**: `bowaka_v2_alpaca_data.py` (direct multi-symbol Alpaca `/v2/stocks/bars`) and `bowaka_v2_openalgo_client.fetch_bars*` (single-symbol via local OpenAlgo server) feed the scanner/universe builder. `bowaka_v2_stream.py` is a *scaffold* for a future minute-bar websocket (disabled).
2. **Decision/order out**: `bowaka_v2_strategy.py` consumes candidate events (event stream, schema-versioned via `bowaka_v2_event_stream_versioning.py`), fetches a live quote (`fetch_quote`), submits a parent MARKET BUY (`submit_market_buy`), then polls fills (`fetch_all_orders` → `poll_fills_v2`), attaches an OCO bracket (`submit_oco_bracket`), and exits via `submit_market_sell` / `cancel_order`.
3. **Second simulator**: `bowaka_v2_backtest.py` + `bowaka_v2_cost_model.py` is a *separate* replay backtester (handoff §7.2.1) that reuses the SAME `bowaka_v2_features` as live, reads the shared lake, and applies a parametric cost model. This is the "prod backtester" distinct from the lab `pmm_lab`/v2 sim.
4. **Safety/observability**: `bowaka_v2_heartbeat.py` writes `KILL_NEW.flag` on scanner staleness; `bowaka_v2_replay.py`/`replay_data.py` reconstruct sessions; dashboard/analysis/counterfactuals/ablation/bucket read the JSONL streams.

## Behavioral spec

**OpenAlgo broker API (`bowaka_v2_openalgo_client.py`)**
- Auth: `X-API-KEY` header + `apikey` in body; host/key from env, raises if `OPENALGO_API_KEY` unset (`openalgo:29-36`).
- Parent BUY: `POST /api/v2/orders`, `order_type=MARKET`, `quantity_unit=WHOLE`, `session=REGULAR`, default `time_in_force="DAY"` (`openalgo:270-297`). Qty stringified.
- SELL exit: identical shape, default `DAY` (`openalgo:300-328`).
- OCO bracket: `POST /api/v2/orders/combo`, `combo_type=OCO`, two SELL legs — LIMIT @ `target_price`, STOP @ `trigger_price` — default `GTC` (`openalgo:331-383`). Prices rounded to 2 dp.
- All three order funcs annotate `_http_status` and return the parsed body; **no exception on non-2xx** — caller validates `_http_status in (200,201)` (`openalgo:294-297`, used at `strategy:957-959`,`1567`).
- `cancel_order`: `DELETE /api/v2/orders/<id>`; treats 200, 404, and error-message substrings ("already inactive/canceled/not found") as success; warns + returns `status:error` otherwise (`openalgo:386-420`).
- `fetch_bars`: POST, **swallows all HTTP failures/4xx → empty DataFrame** (`openalgo:114-129`). Parses `ts` or `timestamp`, coerces OHLCV, sorts ascending.
- `fetch_bars_concurrent`: bounded `ThreadPoolExecutor`, per-symbol failure → empty df (`openalgo:142-188`).
- `fetch_quote`: POST `/api/v2/quotes`; on failure/empty returns None (warns) (`openalgo:194-228`). `_normalize_quote` computes mid, `spread_pct=(ask-bid)/mid`, `quote_age_seconds` from `now-ts` (`openalgo:231-257`).
- `fetch_positions`/`fetch_open_orders`/`fetch_all_orders`: GET, **`raise_for_status()`** (do raise) (`openalgo:423-445`).

**Order lifecycle (`bowaka_v2_strategy.py`)** — *polling, not callbacks*:
- Submit: validates `_http_status`, extracts `order_id`/`id`/`native_response.id`; only mutates state if accepted (`strategy:947-973`).
- `poll_fills_v2`: GET `status=all`, indexes only pre-fill parents + child/exit ids; reconciles FILLED/dead statuses (`strategy:1262-1365`).
- Parent terminal (canceled/rejected/expired) WITH `filled_qty>0` is treated as a fill (`strategy:1330-1340`); else dropped.
- OCO attach is *post-fill, idempotent* — short-circuits when both child ids set (`strategy:1146-1229`). Leg ids parsed by `order_type` substring "limit"/"stop", with parent-id fallback for target (`strategy:1199-1208`).
- Exit (`trigger_exit_v2`): reserves `status="exit_pending"` before I/O, cancels children, submits MARKET sell `DAY`, reverts to `filled` on reject/missing-id so next pass retries (`strategy:1514-1599`).
- Time-stop: coarse `pd.bdate_range` (Mon–Fri, **no holiday calendar**) vs `max_hold_days` (`strategy:1368-1382`,`1602-1626`).
- Kill switches L1 (`KILL_NEW.flag`→skip entries), L2 (`KILL_SOFT.flag`→flatten all), L3 (`KILL_HARD.flag`→flatten+exit 99) checked each loop (`strategy:1931-1984`).
- Main loop cadence: full sequential pass then `time.sleep` in 0.5s chunks up to `interval` (`strategy:2027-2031`). **No explicit network latency model** — wall-clock polling only.

**Prod cost model (`bowaka_v2_cost_model.py`)** — pure, parametric, NO real tape:
- base: mid + half_spread + 5 bps impact (entry); mid − half_spread − 5 bps (exit) (`cost:52-54`,`106-108`).
- conservative: ask + `25·√(notional/adv)` bps impact (entry); bid − same (exit) (`cost:55-57`,`109-111`).
- severe: ask + `2·impact + 10` bps (entry); bid − same (exit) (`cost:58-61`,`112-115`).
- `halt_stress` → fill at caller-supplied `next_print_price` (`cost:91-96`).
- `gap_stress_overnight_stop` → stop fills 50 bps worse than trigger (`cost:97-104`).
- `_sqrt_impact_bps`: 5 bps floor when ADV missing/≤0 (`cost:125-133`).

**Prod backtester (`bowaka_v2_backtest.py`)** — *second simulator*:
- Scan times 09:45→15:30 ET every `scan_interval_seconds` (`backtest:240-253`). NOTE diverges from live scanner window.
- Per scan: aggregates forming session bar, applies v2 gates, scores; **takes only top-1 candidate** (`backtest:174-175`).
- Entry: bar at/after `effective_entry`; bid/ask default to bar **low/high** when no quote_supplier (`backtest:183-184`); qty=`per_trade//last_price`.
- Stop/target derived from `fill.fill_price` (`backtest:203-204`).
- `_manage_position`: first-touch low≤stop / high≥target / else time_stop at last bar (`backtest:291-333`). Exit fill uses synthetic bid/ask = `price*0.999/1.001`.
- Default suppliers are **lake-backed** via `bowaka_common.marketdata.MarketDataStore`; `--synth` uses built-in synthetic bars (`backtest:536-549`).

## Knobs (config fields read here)

- `execution.parent_order_style` (default `"market"`) — recorded only; submit always MARKET (`strategy:924`).
- `execution.default_venue_code` (default `"XNAS"`) (`strategy:977`,`1163`).
- `exits.oco_time_in_force` (default `"GTC"`) — threaded to `submit_oco_bracket` (`strategy:1178`).
- `exits.stop_pct`/`target_pct`/`max_hold_days` (0.08/0.15/3) — bracket pricing + time-stop (`strategy:927-929`,`1166-1167`,`1610`).
- `cost_stress` CLI/arg (base/conservative/severe) — backtester fill stress (`backtest:501`).
- `ablation` — strips one gate or delays entry 1/5/15/30m (`backtest:256-288`).
- `sizing.bankroll_fixed_dollars`/`max_concurrent_positions`/`equal_slice_bankroll_fraction` (90000/18/0.80) (`backtest:104-107`).
- `market_data.feed`/`vendor`/`shared_root`/`require_split_adjustment` — lake suppliers + adjustment (`backtest:472-486`,`441-452`).
- `scanner.bar_source` (openalgo|alpaca_direct) — swaps bar path (referenced in `alpaca_data` docstring).
- `StreamConfig.enabled` (default False) + reconnect backoff/lag thresholds (`stream:31-39`).
- Env: `ALPACA_DATA_FEED` (default `"iex"`), `ALPACA_LIVE_MODE`/`ALPACA_PAPER` (default paper) (`alpaca_data:96-122`); `HOST_SERVER` (default `127.0.0.1:5000`).
- Heartbeat `stale_threshold_seconds` (default 60) (`heartbeat:60`).

## Invariants & guards

- **Fail-loud**: missing `OPENALGO_API_KEY` (`openalgo:35`); missing Alpaca creds (`alpaca_data:114-119`); unresolved lake root (`backtest:432-437`); unsupported schema version (`event_stream_versioning:30-34`); `fetch_positions`/`fetch_open_orders`/`fetch_all_orders` `raise_for_status` (`openalgo:425,434,443`); `_validate_alpaca_parity` exits 1 on mismatch.
- **Reservation guard**: `trigger_exit_v2` sets `exit_pending` before I/O to prevent double-fire (`strategy:1532-1535`).
- **Idempotency**: OCO short-circuit (`strategy:1159`); parent `parent_fill_processed` flag (`strategy:1311`); `cancel_order` 404-as-success.
- **Atomic state writes** (`strategy:2024`); cumulative PnL reconciled from ledger on load.
- **SILENT FALLBACKS (flag each)**:
  - `fetch_bars` swallows ALL HTTP errors/4xx → empty df (`openalgo:114-129`); `fetch_bars_concurrent` swallows per-symbol (`openalgo:177-180`). A data outage looks like "no symbols," not an error.
  - `fetch_quote` failure → None → backtester/strategy fall back to bar low/high or signal price as bid/ask (`backtest:183-189`, `strategy` "synthesized-from-signal-price").
  - `_maybe_load_env_creds` swallows `.env` parse errors silently (`alpaca_data:82-83`).
  - `_normalize_quote` swallows timestamp parse → `quote_age_seconds=None` (no staleness signal) (`openalgo:243-250`).
  - `_last_heartbeat_age` falls back to file mtime if line parse fails (`heartbeat:50-53`) — mtime can look fresh even with stale content.
  - `cancel_order` returns `status:error` (not raise) on unexpected status; callers wrap in bare `except` and continue (`strategy:1543-1547`,`1647`).
  - `submit_oco_children_v2` returns None on missing entry_price/qty — "will retry next tick," no bound on retries except `oco_attach_attempts` counter that's never gated on (`strategy:1168-1174`).

## Leads

- `cost_model.py:52-54` — **base entry double-counts spread**: `mid + half_spread` already equals ask, then adds 5 bps; conservative pays `ask + impact`. Base ≈ conservative-with-fixed-5bps, suspiciously close; verify base isn't secretly harsher than intended.
- `cost_model.py:94` — `cost_bps=(mid - next_print_price)/mid` for halt; sign/labeling vs entry's `(fill-mid)/mid` is inconsistent and `notes` drops `spread` field (`cost:95`).
- `cost_model.py:130-131` — ADV-missing → 5 bps floor; for severe this gives only 10 bps total impact regardless of size — likely **understates illiquid-name impact**.
- `backtest.py:183-184` — entry bid/ask defaulted to bar **low/high** is wildly wide vs a real NBBO; with conservative stress this inflates spread cost or (with quote_supplier=None always) **manufactures unrealistic fills**. Lake suppliers wire `quote_supplier=None` (`backtest:489-490`) so EVERY lake run uses low/high as the quote.
- `backtest.py:303-305`,`312-314` — exit synthetic bid/ask `price*0.999/1.001` (≈20 bps spread) is a fixed fiction unrelated to symbol liquidity.
- `backtest.py:301` — stop/target use intrabar `low/high` first-touch with **no ordering guarantee** (if both stop and target touched same bar, stop wins by code order) — optimistic/pessimistic ambiguity not modeled.
- `backtest.py:174-175` — `candidates[:1]` enters only ONE symbol per scan, but live strategy enters up to N slots; **prod backtester ≠ live entry breadth** — major realism divergence.
- `backtest.py:240-245` — scan window 09:45–15:30 ET hardcoded; live scanner window may differ (config-driven elsewhere). Divergence.
- `backtest.py:214` — `max_hold_session_minutes = max_hold_days*390`, but `_manage_position` ignores it entirely (only stops at end of supplied bars) — **dead field / hold limit not enforced in single-session frames**.
- `stream.py:46`,`115` — `falled_back_to_polling` typo; whole module is an unwired scaffold (`stream:9-15`) — dead in prod but shipped.
- `strategy:1330-1340` — parent `rejected/expired` WITH `filled_qty>0` marked filled; for a MARKET order this is plausible (partial then expire) but **partial-fill (filled_qty < requested qty) silently overwrites `pos["qty"]`** without resizing the OCO — bracket qty may mismatch position. Verify partial handling.
- `strategy:1352-1357` — child target/stop fills recorded but **no OCO sibling cancel logic here**; relies on broker OCO. If broker doesn't auto-cancel the other leg, double-exit risk.
- `openalgo:237-239` — `spread_pct=(ask-bid)/mid` is a fraction, but field name implies percent; downstream gates comparing to a "_pct" threshold could be off by 100×. Verify consumer units.
- `_retighten_oco_at_market_open.py:30` — hardcoded `E:\stocktradingsoftware\openalgo` absolute path; one-shot dated script (2026-05-27) still in tree — dead/stale operator script.
- `replay.py:84-86` — `bars_supplier=lambda s,t: pd.DataFrame()` — replay never actually reads bars; `replay_session` only checks config_hash drift and reports `replay_complete:True` — **largely a stub** (no real reconstruction).
- `event_stream_versioning.py:17` — `SUPPORTED_SCHEMA_VERSIONS=(3,)`; reader rejects anything else but tuple comment says "future schema 4" — forward-compat path untested/absent.
- `heartbeat.py:73` — `age is None` (file missing) triggers kill; but a never-started scanner on first boot would write KILL_NEW immediately — possible false kill on cold start.
- `alpaca_data.py:121` — default feed `"iex"` (thin), not SIP; backtester realism depends on feed but defaults to the partial-tape feed.
- `strategy:982` — `link_id` uses `time.time_ns()`; `submit_oco_children_v2:1177` uses `int(time.time())` (second resolution) for OCO link_id — collision risk on rapid re-attach.

## Test coverage hooks

- The lab `tests/` import the **lab port**, not this prod mirror directly. The prod `bowaka_v2_backtest.py`/`cost_model.py` are exercised via `tests/integration/test_prod_backtester_*.py` and `tests/unit/reference/test_prod_backtester_default_uses_lake.py` (lake default, synth flag, megacap price gate, patch artifact) and `tests/unit/test_sim_cost_model_levels.py` (but that targets the **lab** cost model — confirm it asserts against prod `bowaka_v2_cost_model` values).
- **NO direct tests** for: `bowaka_v2_openalgo_client.py` (order submit/cancel/quote/`_normalize_quote`/`_http_status` semantics — entirely untested), `bowaka_v2_stream.py` (`StreamClient`, reconnect/backoff/`lag_seconds`), `bowaka_v2_heartbeat.py` (`check_and_kill`, mtime fallback), `bowaka_v2_strategy.py` live order plumbing (`poll_fills_v2`, `trigger_exit_v2`, OCO attach, kill switches L2/L3, partial-fill handling), `bowaka_v2_replay.py`, `bowaka_v2_alpaca_data.py` (`resolve_alpaca_data_auth` precedence, pagination), `_retighten_oco_at_market_open.py`, `_validate_alpaca_parity.py`. The cost-model `halt_stress`/`gap_stress` branches and `_sqrt_impact_bps` ADV-missing floor appear untested. The backtester's single-candidate-per-scan and low/high-as-quote behaviors have no realism assertion.