# bowaka_v2_lab — Market-Data Lake & Scan-Matrix Reference

Complete reference for the shared market-data lake and the scan-matrix cache that power
bowaka_v2_lab's backtesting, walk-forward Bayesian optimization, and realism gates. Written
for engineers who do **not** have access to the running container.

- **Live-inventory figures captured 2026-06-24** (after the deep minute backfill). Sizes/counts/
  date-ranges drift as the lake is refreshed; the *structure, schema, sources, and mechanics* are stable.
- The lake itself is **gitignored** (a rebuildable cache). This document and the lake's own
  `README.md` are the only checked-in artifacts that describe it.
- Authoritative code: `bowaka_common.marketdata` (layout/store/fetch) under
  `research_notebooks/bowaka_common/src/`, and `bowaka_v2_lab.scanner.scan_matrix` +
  `bowaka_v2_lab.data` under `research_notebooks/bowaka_v2_lab/src/`.

---

## Table of contents
1. [TL;DR](#1-tldr)
2. [Where it physically lives & how to access it](#2-where-it-physically-lives--how-to-access-it)
3. [Data sources](#3-data-sources)
4. [Partition layout & schema (the 8 datasets)](#4-partition-layout--schema-the-8-datasets)
5. [What the lake HAS today (live inventory)](#5-what-the-lake-has-today-live-inventory)
6. [What it does NOT have yet / known limitations](#6-what-it-does-not-have-yet--known-limitations)
7. [Reader API (`MarketDataStore`)](#7-reader-api-marketdatastore)
8. [Scan matrices](#8-scan-matrices)
9. [Keeping it current (backfill scripts & weekly cadence)](#9-keeping-it-current-backfill-scripts--weekly-cadence)
10. [Gotchas & caveats every engineer should know](#10-gotchas--caveats-every-engineer-should-know)

---

## 1. TL;DR

- The lake is a **partitioned-Parquet store** of **Alpaca SIP** market data + **Nasdaq Trader**
  trade-halts. It is consumed **read-only** by `bowaka_v2_lab` (v2) and `bowaka_lab` (v1) via
  `bowaka_common.marketdata.MarketDataStore`.
- It physically lives **inside the `ql-jupyter` Docker container** at `/opt/market_data_cache`,
  on a **persistent Docker named volume** (`ql_market_data`). Vendor = `alpaca`, feed = `sip`
  throughout.
- ~**110 GB** across **8 datasets**: daily bars, minute bars (~25 GB after the 2026-06-23 deep
  backfill to 2023-09), NBBO quotes (1/min), fine NBBO (sub-minute), the **raw trade tape**
  (~74 GB, the bulk), official open/close auctions, trade-halt statuses, corporate actions, plus
  an asset-master snapshot.
- The **scan matrices** (`/opt/scan_matrix_cache`, volume `ql_scan_matrix`) are a precomputed,
  memory-mapped, per-`(session, scan_time, symbol)` feature cache. They are the single biggest
  performance lever — a walk-forward Optuna trial reads features from the matrix instead of
  re-aggregating minute bars per symbol.

---

## 2. Where it physically lives & how to access it

| Aspect | Value |
|---|---|
| Lake root (in-container) | `/opt/market_data_cache` (env `MARKET_DATA_ROOT`) |
| Matrix cache (in-container) | `/opt/scan_matrix_cache` |
| Storage backend | Docker **named volumes** `ql_market_data` + `ql_scan_matrix` (declared `external: true` in `quantslab_desktop_compose.yaml`) |
| Host disk file | `E:\dockers\docker-desktop\DockerDesktopWSL\disk\docker_data.vhdx` (the WSL2 ext4 vhdx that backs the volumes + Docker images) |
| Container | `ql-jupyter` (image `hummingbot/quants-lab:desktop`, conda env python `/opt/conda/envs/quants-lab/bin/python`) |

**Root resolution** (`store.py`): explicit `MarketDataStore(root=...)` arg → `MARKET_DATA_ROOT`
env → in-repo default `<repo>/research_notebooks/market_data`. The in-container workflow always
sets `MARKET_DATA_ROOT=/opt/market_data_cache` (the fast native-FS lake); the in-repo path is a
slow 9p-mounted fallback and is **not** the production lake.

**Why a volume, not the container overlay:** the data formerly lived on the container's writable
overlay and would have been wiped on any container recreate. It is now on external volumes that
survive `docker compose down/up`, image rebuilds, and even `docker compose down -v`. The vhdx was
also relocated off C: onto E: (a 3× NVMe Storage Space) for space + bandwidth.

**How engineers access it** (no host-level access — it's inside Docker):
- Via the container: `docker exec ql-jupyter ...`, or the JupyterLab server the container runs.
- In Python: `from bowaka_common.marketdata import MarketDataStore` +
  `from bowaka_common.marketdata.store import resolve_market_data_root`, then
  `store = MarketDataStore(resolve_market_data_root(None))` with `PYTHONPATH=src:../bowaka_common/src`
  from the lab dir.
- To replicate elsewhere: re-run the backfill scripts (§9) against your own `MARKET_DATA_ROOT`
  (requires Alpaca SIP credentials).

---

## 3. Data sources

Two upstreams. **Everything is labelled `vendor=alpaca`** in the partition path — including the
halts, whose true upstream is Nasdaq (see the caveat at the end of this section).

### Alpaca (the SIP consolidated tape) — bars, quotes, quotes_fine, trades, auctions, corporate_actions
- **API:** Alpaca Market Data (`data.alpaca.markets`). Bars/quotes/trades go through the
  `alpaca-py` SDK (`StockHistoricalDataClient`); auctions and corporate-actions use **raw REST**
  (`GET /v2/stocks/auctions`, `GET /v1beta1/corporate-actions`) because the SDK lacks those
  request classes.
- **Feed:** `sip` (full consolidated tape). The config default is `iex`, but every realism
  dataset is SIP-only and warns if `feed != "sip"`; the weekly refresh hard-pins `--feed sip`.
- **SIP entitlement is required.** The consolidated SIP tape needs an Alpaca SIP subscription
  (Algo-Trader-Plus tier). A missing/lapsed entitlement surfaces as HTTP **403**; the scheduler's
  pre-flight `alpaca_health_check.py` probes the SIP feed and aborts (exit 2, no retry) on 401/403.
- **Auth:** `ALPACA_API_KEY_ID` / `ALPACA_API_SECRET_KEY` from env or `.env` (auto-discovered by
  walking up from CWD; the raw-REST scripts also fall back to `/quants-lab/.env` and strip
  quotes/CRLF). `ALPACA_PAPER` defaults true.
- **Rate limits:** sliding-window limiter. Config default 180 rpm; SIP/Algo-Trader-Plus real
  limit is 10000 rpm; weekly refresh uses 8000, scheduler 9000. Batch sizes: bars 200 symbols/call,
  quotes/trades/quotes_fine 25.

### Nasdaq Trader — trade halts (the `statuses/` partition)
- **Alpaca serves no historical halt/LULD data**, so halts come from **Nasdaq Trader's
  TradingHaltSearch JSON-RPC** (Jayrock 1.1 at `https://nasdaqtrader.com/RPCHandler.axd`,
  Referer-guarded via a session cookie from `Trader.aspx?id=TradingHaltSearch`).
  - `BL_TradeHalt.GetHaltsByDate('YYYYMMDD')` — per-day historical (reaches back years); the
    backfill source for the deep halt history (full-history re-fetch floor `2023-09-01`; the lake now
    holds halts back to 2022-02-28).
  - `BL_TradeHalt.SearchTradeHaltsNEW` — trailing ~1 year (~13k halts) in one call.
  - Live RSS (`rss.aspx?feed=tradehalts`) — a snapshot of **currently-open** halts only.
- Requires outbound access to `nasdaqtrader.com`. No API auth.

> **Caveat — the `vendor=alpaca` label is a namespace, not the literal source.** The
> `statuses/` (halts) partition is also written under `vendor=alpaca` even though its upstream
> is Nasdaq Trader. Treat `vendor=alpaca` as "the lake's primary vendor namespace," not "fetched
> from Alpaca," for halts.

---

## 4. Partition layout & schema (the 8 datasets)

All paths are rooted at `<MARKET_DATA_ROOT>/` (= `/opt/market_data_cache/`). Path scheme is the
single source of truth in `bowaka_common.marketdata.layout`. Every leaf file is literally
`part.parquet` (except assets → `assets.parquet`). Partition keys: `vendor=`, `feed=`,
`adjustment=`, `timeframe=`, `symbol=`, `year=` (4-digit), `month=` (2-digit), `date=` (`YYYY-MM-DD`).
All `timestamp` columns come back tz-aware **UTC**.

### Quick index

| Dataset | Path template (under `<root>/`) | Partitioned by | Reader |
|---|---|---|---|
| daily bars | `bars/vendor=<v>/feed=<f>/timeframe=1d/adjustment=split_adjusted/symbol=<S>/part.parquet` | symbol (full history per file) | `daily_bars` / `sip_daily_bars` |
| minute bars | `bars/vendor=<v>/feed=<f>/timeframe=1m/adjustment=raw/symbol=<S>/year=<Y>/month=<M>/part.parquet` | symbol × month | `minute_bars` / `sip_minute_bars` |
| quotes (1/min NBBO) | `quotes/vendor=<v>/feed=<f>/symbol=<S>/year=<Y>/month=<M>/part.parquet` | symbol × month | `quotes`, `quotes_at_or_before` |
| quotes_fine (sub-min NBBO) | `quotes_fine/vendor=<v>/feed=<f>/symbol=<S>/year=<Y>/month=<M>/part.parquet` | symbol × month | `quotes_fine_between` |
| trades (raw tape) | `trades/vendor=<v>/feed=<f>/symbol=<S>/year=<Y>/month=<M>/part.parquet` | symbol × month | `trades_between` |
| auctions | `auctions/vendor=<v>/feed=<f>/symbol=<S>/year=<Y>/month=<M>/part.parquet` | symbol × month | `auctions_between` |
| statuses (halts) | `statuses/vendor=<v>/symbol=<S>/date=<YYYY-MM-DD>/part.parquet` | symbol × halt-date (**no feed**) | `halt_feed.read_halt_events` |
| corporate_actions | `corporate_actions/vendor=<v>/symbol=<S>/part.parquet` | symbol (**no feed/date**) | `corporate_actions`, `all_corporate_actions` |
| assets (master) | `assets/vendor=<v>/snapshot_id=<id>/assets.parquet` | snapshot | `assets`, `latest_snapshot_id` |

### 4.1 Daily bars — `timeframe=1d`, `adjustment=split_adjusted`
One file per symbol (no year/month; full history). **Split-adjusted** so a split doesn't create a
fake ADV/price discontinuity in the continuous history.

| column | type | meaning |
|---|---|---|
| `symbol` | str | ticker |
| `timestamp` | datetime64[us,UTC] | session timestamp (midnight UTC for daily) |
| `open`,`high`,`low`,`close` | float64 | continuous-session OHLC (first/last *continuous* trade — **not** the official auction; auctions are a separate dataset) |
| `volume` | int64 | session share volume |
| `vwap` | float64 | VWAP (nullable) |
| `trade_count` | int64 | number of trades (nullable) |
| `session_date` | str | ET calendar date (`timestamp`→America/New_York→date); **daily only** |

> A separate **`adjustment=all`** daily variant (split **+** dividend adjusted) also exists,
> written by `backfill_daily_all.py` for the dividend-adjustment cutover. Same columns minus
> `session_date`.

### 4.2 Minute bars — `timeframe=1m`, `adjustment=raw`
One file per symbol/month. **RAW (unadjusted)** — these are the actual live-traded intraday prices,
required for backtest-to-live parity (split-adjusting would skew the $1–20 price gate for any symbol
that splits in-window). Columns = daily **minus** `session_date`:
`symbol, timestamp(per-minute UTC bar open), open, high, low, close, volume, vwap, trade_count`.

### 4.3 Quotes — 1/min sampled NBBO (canonical)
Down-sampled to **one prevailing NBBO snapshot per regular-session minute** (≤390 rows/symbol/day):
the last quote at-or-before each 09:30–15:59 ET minute boundary, keeping the **real tick timestamp**
for honest quote-age telemetry. 7 columns:

| column | type | meaning |
|---|---|---|
| `symbol` | str | ticker |
| `timestamp` | datetime64[us,UTC] | actual tick time of the prevailing quote (not the boundary) |
| `bid`,`ask` | float64 | NBBO bid/ask price |
| `bid_size`,`ask_size` | float64 | NBBO sizes |
| `conditions` | str | quote condition codes (comma-joined) |

### 4.4 Quotes_fine — sub-minute NBBO (+ exchange/tape)
A **sibling** of `quotes/` (never nested under it, so it never perturbs the canonical
`quote_partitions_hash`). Same 7 columns **plus** `bid_exchange`, `ask_exchange`, `tape`. Sampled at
N evenly-spaced sub-minute boundaries (production: **4/min**) or raw ticks if N≤0. Not minute-deduped.

### 4.5 Trades — raw tape
A sibling of `quotes/`. **Every print, no sampling** (so the tape-replay fill oracle can reconstruct
VWAP / fill fraction). Many prints share a timestamp; stored stable-sorted, not deduped.

| column | type | meaning |
|---|---|---|
| `symbol` | str | ticker |
| `timestamp` | datetime64[us,UTC] | print time |
| `price` | float64 | trade price |
| `size` | float64 | shares |
| `exchange` | str | venue code |
| `conditions` | str | sale-condition codes |
| `tape` | str | tape A/B/C |
| `trade_id` | int64 | venue trade id (nullable) |

### 4.6 Auctions — official open/close prints
A sibling of trades/quotes; one row per session. Open = CTS opening print (`"O"`, else Nasdaq `"Q"`);
close = CTS official close (`"M"`, else UTP `"6"`); picks the largest-size print of the
highest-priority condition.

| column | type | meaning |
|---|---|---|
| `symbol`,`session_date` | str | ticker, `YYYY-MM-DD` |
| `timestamp` | datetime64[ns,UTC] | range anchor: close-auction time, else open, else `{date}T20:00:00Z` |
| `official_open`,`official_close` | float64 | official auction prices (nullable) |
| `open_size`,`close_size` | float64 | auction sizes |
| `open_condition`,`close_condition` | str | print sale-conditions |

### 4.7 Statuses — trade halts / LULD
Partitioned per symbol/halt-date (**no feed key**). One file per `(symbol, halt-start-date)`.

| column | type | meaning |
|---|---|---|
| `symbol` | str | ticker |
| `ts_start` | datetime64[us,UTC] | halt onset (Nasdaq ET → UTC) |
| `ts_end` | datetime64[us,UTC] | resumption time; NaT = still halted at pull time |
| `reason` | str | reason code (e.g. `LUDP`, `T1`, `T2`, `T5`, `M`) |
| `market` | str | listing market |
| `is_luld` | bool | reason ∈ {LUDP, LUDS, M} |
| `pause_threshold_price` | float64 | LULD pause threshold (nullable) |

> The reader `halt_feed.read_halt_events(...)` returns `HaltEvent(symbol, ts_start, ts_end, reason)`
> objects — it intentionally exposes only those 4 fields (drops market/is_luld/pause_threshold_price).
> It is **not** a `MarketDataStore` method.

### 4.8 Corporate actions — survivorship + adjustment source
The **whole CA stream** is fetched by date window (the `symbols` API param is deliberately omitted)
because renamed/merged/removed symbols are no longer in the current universe — and those are exactly
the events that prove a delisting/rename happened. One file per affected symbol (no feed/date keys).

| column | type | meaning |
|---|---|---|
| `ca_type` | str | raw Alpaca type: `forward_splits`,`reverse_splits`,`unit_splits`,`cash_dividends`,`name_changes`,`cash_mergers`,`stock_mergers`,`stock_and_cash_mergers`,`spin_offs`,`worthless_removals`,`redemptions`,`rights_distributions` |
| `symbol` | str | **primary** keyed symbol (mergers→acquiree, renames→old, spin-offs→source) |
| `old_symbol`,`new_symbol` | str | rename/spin-off symbols (nullable) |
| `effective_date` | str | **canonical PIT ordering key** = ex_date → effective_date → process_date → payable_date → record_date |
| `ex_date`,`process_date`,`record_date`,`payable_date` | str | event sub-dates (nullable) |
| `old_rate`,`new_rate` | obj | split ratio = new_rate/old_rate (nullable) |
| `rate` | float64 | cash dividend / cash-merger rate (nullable) |
| `cusip`,`id` | str | CUSIP, Alpaca event id (nullable) |
| `is_delisting` | bool | type ∈ {cash/stock/stock_and_cash mergers, worthless_removals, redemptions} |
| `is_symbol_change` | bool | type ∈ {name_changes} |
| `is_split` | bool | type ∈ {forward/reverse/unit splits} |

Unknown/future Alpaca CA types are **preserved** (never dropped; just unflagged).
`corporate_actions(symbol, ...)` filters one symbol by **`ex_date`**; `all_corporate_actions()`
returns the entire stream and callers filter on **`effective_date`** (renames/mergers/removals carry
no `ex_date`).

### Ingestion metadata (not a data partition)
`_ingestion/manifest.json`, `_ingestion/runs/<run_id>.json`, `_ingestion/audits/<id>.parquet` —
backfill bookkeeping.

---

## 5. What the lake HAS today (live inventory)

*Captured 2026-06-24 inside `ql-jupyter` (post deep minute backfill). Feed = `sip`, vendor = `alpaca` everywhere.*

### Sizes — `/opt/market_data_cache` (~110 GB)
| Partition | Size |
|---|---|
| trades | **74 GB** (~67% of the lake) |
| bars | ~25 GB (1m = 25 GB, 1d = 0.45 GB) |
| quotes_fine | 4.7 GB |
| quotes | 2.0 GB |
| auctions | 870 MB |
| corporate_actions | 254 MB |
| statuses | 199 MB |
| assets | 556 KB |

### Coverage — date range & symbol count
| Dataset | Symbols | Date range |
|---|---|---|
| bars 1m (raw) | 6,580 | **2023-09-01 → 2026-06-23** (deep backfill 2026-06-23) |
| bars 1d (split_adjusted) | 6,581 | **2023-09-25 → 2026-06-23** |
| bars 1d (all = split+div) | 6,524 | 2024-06-03 → 2026-06-12 (not deepened; deep backfill used adjustment=split_adjusted) |
| quotes | 3,729 | 2025-08-01 → 2026-06-18 (IR-only; not deepened) |
| quotes_fine | 3,725 | 2025-08-01 → 2026-06-18 (not deepened) |
| trades | 3,735 | 2025-08-01 → 2026-06-18 (not deepened) |
| auctions | 6,579 | 2025-08-01 → 2026-06-18 |
| statuses (halts) | 4,859 symdirs | halt dates **2022-02-28 → 2026-06-23** (763 halt-days) |
| corporate_actions | (event-driven) | full per-symbol CA history, ex_dates 2023-08-02 → 2026-06-23 (superset, includes delisted/inactive) |
| assets (master) | 6,527 (latest snapshot) | snapshots 2026-05-17, 2026-05-26, 2026-06-05 |

### Asset-master universe (latest snapshot)
6,527 symbols, 100% `active`/tradable. Exchanges: NASDAQ 4,097 / NYSE 2,142 / AMEX 264 / ARCA 22 /
BATS 2. Shortable 3,679 / not 2,848; fractionable 3,972 / not 2,555. Columns: `snapshot_id, symbol,
name, exchange, asset_class, tradable, marginable, shortable, fractionable, status`.

---

## 6. What it does NOT have yet / known limitations

- **Tick streams are shallower than bars.** Tick-resolution streams (quotes, quotes_fine, trades)
  start **2025-08** only (~10 months); minute *bars* now go back to **2023-09** (~2.75 yr, matching
  daily, after the 2026-06-23 deep backfill across all ~6,529 daily symbols). So minute-bar
  walk-forward tracks the full ~2.75 yr; anything needing quotes/trades is still bounded by 2025-08+.
- **Minute bars are RAW only** — no split/dividend-adjusted minute partition. Any intraday
  adjustment must be applied at read time using `corporate_actions`.
- **Symbol-count asymmetry.** Daily bars + 1m bars + auctions cover ~6,580 symbols, but
  quotes/quotes_fine/trades cover only ~3,730. ~2,850 symbols have daily + minute + auctions but
  **no tick-resolution (quote/trade) data** (the low-liquidity tail, deliberately not backfilled at
  tick resolution).
- **Halts (`statuses/`) now reach back to 2022-02-28** (full-history re-fetch floor pushed to
  2023-09-01 on 2026-06-23) and are event-driven (only halted symbols on halted days), not one row
  per symbol/day. Halts are maintained going forward by the weekly refresh.
- **Asset master has only 3 recent snapshots** (mid-May → early-June 2026), not a long PIT history of
  universe membership. Point-in-time survivorship therefore leans on `corporate_actions`, not on
  historical asset snapshots.
- **No options/futures/crypto** — US equities only.

---

## 7. Reader API (`MarketDataStore`)

`bowaka_common.marketdata.MarketDataStore` (read-only). Key methods (all `timestamp`→UTC, range-filtered,
sorted):

| Method | Returns |
|---|---|
| `daily_bars(sym, start, end, *, feed="iex", adjustment="raw", with_microstructure=False)` | daily-bar frame (filters on `session_date` if present) |
| `minute_bars(sym, start, end, *, feed="iex", adjustment="raw", with_microstructure=False)` | minute-bar frame (reads only overlapping symbol/month partitions; dedups on `timestamp`) |
| `quotes(sym, start, end, *, feed="iex")` | 1/min NBBO frame |
| `quotes_at_or_before(sym, ts, *, max_age_seconds=60.0, feed="iex")` | single `QuoteRow` (bid/ask/sizes/mid/spread_pct/quote_age_seconds) or `None` |
| `quotes_fine_between(sym, start, end, *, feed="iex")` | sub-minute NBBO frame (not deduped) |
| `trades_between(sym, start, end, *, feed="iex")` | raw trades frame (stable-sorted, not deduped) |
| `auctions_between(sym, start, end, *, feed="iex")` | auctions frame |
| `corporate_actions(sym, start, end)` | one symbol's CAs filtered by `ex_date` |
| `all_corporate_actions()` | the entire CA stream across all symbols |
| `assets(snapshot_id=None)` / `latest_snapshot_id()` | asset-master snapshot |

**SIP wrappers** pin `feed="sip"` (and split-adjusted daily): `sip_daily_bars`, `sip_minute_bars`,
`sip_quotes`, `sip_quotes_at_or_before`, `sip_quotes_fine_between`, `sip_trades_between`. Note the
**default `feed` arg is `iex`** — pass `feed="sip"` (or use the `sip_*` wrappers) to read the
production lake. Halts use `bowaka_v2_lab.data.halt_feed.read_halt_events(...)`, not the store.

---

## 8. Scan matrices

### 8.1 What & why
A scan matrix is a **read-only, memory-mapped, per-session columnar feature store** of precomputed
scanner features at `/opt/scan_matrix_cache` (volume `ql_scan_matrix`). A walk-forward Optuna trial
opens the matrix once per worker and reads the features the scanner needs from numpy memmaps — the
per-trial cost becomes a small slice + a few gates instead of a per-symbol feature recompute. It
excludes every trial-tuned knob (`signals.*`/`sizing.*`/`risk.*`/`execution.*`/`exits.*`), so one
matrix serves every trial in a study. `MATRIX_SCHEMA_VERSION = 1`.

### 8.2 What's in it (per `session=<date>` partition)
Arrays are shaped `(n_scans, n_symbols)` (dynamic) or `(n_symbols,)` (static). The universe is
**dynamic per day** (~1,200–1,900 symbols; ~196–346 intraday scan timestamps per session).

- **Dynamic float64 (16)** — the forming-session bar + scanner features per `(scan_ts, symbol)`:
  `session_open, session_high, session_low, last_price, session_volume, session_range,
  volume_curve_fraction, expected_volume_until_scan, rvol_so_far, projected_full_day_rvol,
  range_expansion_so_far, close_location_so_far, ema_distance, current_return_pct, gap_pct,
  bar_age_seconds`.
- **Dynamic int64 (1):** `last_bar_ts_ns` (ns-UTC of the last closed bar).
- **Dynamic uint8 (4)** — validity/eligibility flags: `has_bar, has_baseline, has_valid_timestamp,
  bar_timestamp_was_naive`.
- **Static float64 (8)** — per-symbol prior-day baselines: `prior_close, avg_volume_20d,
  avg_dollar_volume_20d` (ADV), `prior_atr_14d, prior_atr_pct, ema_10_prior, ema_10_lag_3,
  ema_slope_prior`.
- **Static int8 (4)** — metadata: `instrument_class_code, eligible_for_bowaka_equity_bucket,
  exchange_code, venue_code` (the last three are **placeholders pending asset-master wiring**).
- **Sidecars per session:** `universe_meta.parquet` (`symbol, symbol_id`),
  `daily_baselines.parquet`, `scan_timestamps_ns.int64.npy`, `symbol_ids.int32.npy`,
  `session_manifest.json` (per-file SHA-256 checksums).

### 8.3 Storage layout
`storage_format = numpy_memmap` (uncompressed `.npy`, read via `open_memmap(mode="r")`).
```
<store_root>/                         # e.g. /opt/scan_matrix_cache/validation
  manifest.json                       # see fields below
  parity_proof.json                   # written by `scan-matrix verify --vectorized-check`
  session=YYYY-MM-DD/                 # one partition per trading day
    dyn_f64__<col>.npy (x16) , dyn_i64__<col>.npy (x1) , dyn_u8__<col>.npy (x4)
    stat_f64__<col>.npy (x8) , stat_i8__<col>.npy (x4)
    scan_timestamps_ns.int64.npy , symbol_ids.int32.npy
    universe_meta.parquet , daily_baselines.parquet , session_manifest.json
```
`manifest.json` fields: `matrix_id, matrix_version, config_input_hash, dataset_hash, feed, scope,
created_at_utc, reserved_system_gib, max_optuna_workers, sessions[], columns{}, bowaka_lab_version,
code_hashes{}`.

### 8.4 How it's built
`bowaka-v2-lab scan-matrix build --config <cfg> --scope {validation|holdout|full_history} --workers N
[--store-root R]`:
1. Resolve walk-forward plan from `backtest.{start,end}_date` (default **`auto`** — anchors `end_date`
   to the latest lake session and back-derives `start_date` for `optuna.walkforward.n_folds`
   non-overlapping folds; set explicit `YYYY-MM-DD` to freeze) + `optuna.walkforward`
   (train/val/holdout/step months); resolve the session list for the scope.
2. Memory-budget guard (refuses to launch if estimated footprint breaches a 32 GiB reserve; it probes
   the *actual* PIT-eligible symbol count over the first ≤5 sessions).
3. Per session (parallel, fork-based `ProcessPoolExecutor`, byte-identical regardless of worker count):
   build the **PIT-eligible universe snapshot**, compute the forming-session bar + features at each
   scan time (excluding the still-forming minute to avoid look-ahead), write the memmaps atomically
   (`.tmp/` → rename).
4. Write `manifest.json` with the hashes.

`weekly_data_refresh.ps1`/`rebuild_scan_matrices.ps1` orchestrate this in-container (see §9). An
optional **numba** path (`optuna.acceleration.numba.enabled`, default OFF) speeds the build via njit
kernels with a build-parity guard.

### 8.5 Hashing, config-matching & mode-independence
`config_input_hash = sha256(...)` over: matrix schema version, feed/vendor/adjustment, lake root,
**dataset_hash**, backtest range, **walkforward** months, scanner cadence (start/end/interval/tz/
calendar), `simulation.intraday_window_policy`, the full `universe` + `historical_features` blocks,
the resolved session lists, and the SHA-256 of 5 build-affecting source files (`forming_bar.py`,
`suppliers.py`, `schedule.py`, `universe/builder.py`, `event_builder.py`).

**It deliberately excludes `simulation.mode` and `n_jobs`/`n_trials`.** Consequences:
- The matrix is **mode-independent** — `current_code_parity`, `intended_realism`, and `fast_realism`
  share one matrix **if** their window + walkforward + universe + cadence + feed match.
- A matrix is matched to a config by **store-root path** (`resolve_scan_matrix_store_root`), **not** by
  a runtime hash gate. The `config_input_hash` is written to the manifest and re-checked only by the
  CLI `scan-matrix verify` (dataset-hash drift + sampled cell self-consistency). **There is no runtime
  hash comparison** — the runtime correctness gate is an *exact ns-aligned scan-cadence match* (it
  raises on any cadence mismatch), plus fail-loud-if-the-store-can't-open.

### 8.6 The fast_realism matrix (IR family retired)
The IR (`_local_container_matrix`) family is **retired** — notebook 10 runs `fast_realism` for both
search and finalist re-score, and `rebuild_scan_matrices.ps1` now defaults to FR only. Only the
fast_realism matrix is maintained:

| | fast_realism (and CCP — mode is not hashed) |
|---|---|
| walk-forward | train 6 / val 1 / **holdout 5** / **step 7** mo, **n_folds 3** (auto-anchored to the latest lake session) |
| store root | `/opt/scan_matrix_cache/fast_realism/validation` (+ `…/holdout`) |
| `separate_holdout_matrix` | `false` (build both scopes — the FR sweep requires this) |

`current_code_parity` and `fast_realism` share the same matrix (identical window; mode is not hashed).
Build it with `_build_fr_matrices.py` or `rebuild_scan_matrices.ps1` (now FR-only by default; pass
`-Configs` to rebuild the retired IR family).

### 8.7 Live matrix inventory (2026-06-24, FR auto-anchored)
Only the fast_realism family is maintained (IR retired). The window **auto-anchors to the latest lake
session**, so session ranges + hashes are **recomputed on every rebuild** (each weekly cron run):

| Leaf | Window | Notes |
|---|---|---|
| `fast_realism/validation` | 3 non-overlapping folds, tests ~Oct2024 / May2025 / Dec2025 (relative to the latest session) | recomputed each rebuild |
| `fast_realism/validation/holdout` | ~5 months ending at the latest lake session | recomputed each rebuild |

Both leaves: `feed=sip`, `matrix_version=1`, `reserved_system_gib=32`, `verifier_version=2`
(parity-proven), identical column schema + `code_hashes`. The `dataset_hash`es reflect the
**post-corporate-actions + deep-minute-backfill** lake (survivorship baked in).

---

## 9. Keeping it current (backfill scripts & weekly cadence)

### Backfill scripts
| Dataset | Script | Notes |
|---|---|---|
| daily+minute bars, quotes, trades, quotes_fine | `scripts/backfill_market_data.py` (repo root) | flags `--quotes --trades --quotes-fine [--quotes-fine-samples-per-minute N] --start --rpm`; resume-aware (only new `(symbol, session)` fetched); per-month flush bounds RAM |
| daily "all" (split+div) | `research_notebooks/bowaka_v2_lab/scripts/backfill_daily_all.py` | one-off, `adjustment=all` |
| auctions | `…/scripts/backfill_auctions.py` | raw REST; resume skips symbols whose end-month exists (use `--force` for same-month increments); merge-dedupe by `session_date` |
| halts | `…/scripts/backfill_halts.py` | Nasdaq JSON-RPC; `--start/--end` per-day historical, `--recent`, `--url`/`--file`/`--dir`; per-`(symbol,day)` complete overwrite |
| corporate_actions | `…/scripts/backfill_corporate_actions.py` | whole CA stream by year-chunked window; merge-dedupe on event `id` |

> **Bars are fetched SERIALLY per process.** Only the quotes/trades/quotes_fine fetchers use a
> `ThreadPoolExecutor` (`QUOTE_FETCH_WORKERS` etc.); the minute/daily **bars** stage in
> `backfill_market_data.py` is serial per process (its per-month flush assumes serial date order). To
> deepen bars fast, fan out **N processes over disjoint symbol subsets** — the 2026-06-23 deep
> backfill (2025-08 → 2023-09, all symbols) used **8 processes**, ~6–8× faster than serial. Reusable
> config: `config/_minute_backfill_full_history.yml` (minute `policy: all_daily`, `start: 2023-09-01`).
The **only** scheduled thing that touches the lake is `scheduled_weekly_refresh.ps1` (a Friday
18:30 MT Windows task). Flow: Alpaca SIP health check (hourly retry up to 6h; 401/403 aborts) →
**study guard** (defers the *entire* run if a notebook-10 study/sweep is active, because a mid-study
lake change corrupts it) → `weekly_data_refresh.ps1` → re-check guard → `rebuild_scan_matrices.ps1`.

`weekly_data_refresh.ps1` runs **one in-container pass** that updates **every** dataset:
- **Critical (abort + stale-flag on failure):** bars/quotes/trades/quotes_fine over a short rolling
  lookback window (`-LookbackDays`, resume-aware/incremental).
- **Supplementary (best-effort; a failure WARNs but never blocks bars/quotes or the rebuild):**
  - auctions — short lookback `--force` (merge-dedupe);
  - halts — **full-history re-fetch** every run (`-HaltsStart` default `2023-09-01`; idempotent per-`(symbol,day)` overwrite; self-bootstraps);
  - corporate_actions — **full-history re-fetch** every run (`-CorpActionsStart` default `2023-09-01`; idempotent dedupe by event `id`). Both floors were pushed 2025-08-01 → 2023-09-01 on 2026-06-23 to match the deeper minute/daily backfill.

`rebuild_scan_matrices.ps1` then rebuilds the **fast_realism** matrix family (validation + holdout)
from the refreshed lake — **auto-anchored to the latest session**, so each weekly rebuild re-targets
the freshest data and corporate-actions/survivorship + the latest bars are baked in. (The IR family is
retired; pass `-Configs` to rebuild it.) Because the window auto-anchors, every weekly lake refresh
implies a new matrix by design.

> Do **not** register standalone tasks for `weekly_data_refresh.ps1` / `rebuild_scan_matrices.ps1`;
> only the guarded wrapper. An unguarded refresh/rebuild on its own clock can corrupt a live study.

---

## 10. Gotchas & caveats every engineer should know

1. **`vendor=alpaca` is a namespace, not always the source.** Halts (`statuses/`) come from Nasdaq
   Trader but are stored under `vendor=alpaca`.
2. **Default `feed` arg is `iex`, but the production lake is `sip`.** Pass `feed="sip"` or use the
   `sip_*` reader wrappers. SIP requires an Alpaca SIP entitlement (else HTTP 403).
3. **Adjustment split-brain:** daily = `split_adjusted`, minute = `raw`. A config that resolves to
   raw-daily silently empties the PIT universe (every symbol gets `no_prior_bar`) — keep
   `require_split_adjustment: true`.
4. **Tick data (quotes/quotes_fine/trades) only goes back to 2025-08; minute bars + daily reach
   ~2023-09.** Minute bars were deep-backfilled to 2023-09 for all ~6,529 daily symbols (2026-06-23);
   don't assume *tick* data exists for the full minute/daily span.
5. **Survivorship comes from `corporate_actions`, not asset snapshots.** With CA absent, the universe
   builder has no PIT delisting/rename info → survivorship bias. (CA is now backfilled; the live
   matrices' `dataset_hash` reflects it.)
6. **No runtime matrix hash gate.** A docstring in `scan_matrix_runtime.py` claims the fold-context
   builder verifies the manifest `config_input_hash`/`dataset_hash` — **the code does not**. The only
   runtime protections are (a) fail-loud if the store can't open and (b) an exact ns-cadence match.
   Stale-matrix detection (dataset-hash drift) requires manually running `scan-matrix verify`. Always
   rebuild the matrix after any lake change before relying on it.
7. **The matrix is mode-independent** — `current_code_parity`/`fast_realism` share a matrix when
   window+universe+cadence match (mode is not hashed); matrices differ by *window*, not *mode*. (The
   IR matrix family is retired; only fast_realism is maintained.)
8. **The lake + matrices are gitignored** and live only in the Docker volumes — they are not in the
   repo. They are rebuildable from the backfill scripts (intraday is expensive: the trade tape is ~70 GB).
9. **`quotes_fine`/`trades` are siblings of `quotes/`** by design, so they never perturb the canonical
   `quote_partitions_hash` that the dataset lineage uses.
