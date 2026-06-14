# P7 — Survivorship + `intended_realism` unblock (§3.4 / §5.2 / §5.3)

## What shipped (host — code + tests, real-data-grounded)

**§3.4 / §5.3 — corporate actions → PIT/survivorship master (DONE, tested):**
- `bowaka_common.marketdata.corporate_actions` — normaliser over the real Alpaca
  `/v1beta1/corporate-actions` shape (keyed on the affected symbol; canonical
  `effective_date`; `is_delisting` / `is_symbol_change` / `is_split` flags).
- `store.all_corporate_actions()` — the whole CA stream (incl. delisted/renamed
  symbols no longer in the universe).
- `scripts/backfill_corporate_actions.py` — multithreaded REST downloader (global
  stream by window; `symbols` is optional — required for survivorship).
- `universe/pit_master.py` — per-symbol listing/delisting/rename timeline +
  `status_as_of` + min-history eligibility + the loud `CA_PIT_HAZARD` flag.
- `universe/builder.py` — wired: the CA-derived PIT master drops a symbol delisted /
  renamed **as of the session**; `min_history_trading_days` (contract = 45) enforced;
  `_status_active("")` no longer treats blank status as active (fails closed).
  Graceful: a lake with **no** `corporate_actions/` partition leaves the asset-master
  status gate in charge (every fixture + any pre-backfill lake).

**§5.2 — Nasdaq halt ingester (code + tests; validated against real Nasdaq pulls):**
- `data/halt_ingest.py`:
  - `parse_nasdaq_halt_rss` — the live RSS shape (a current-open-halt snapshot).
  - `parse_nasdaq_halt_table` — the TradingHaltSearch JSON-RPC result table (GenTable
    HTML → `statuses/` rows; ET→UTC, LULD classification, ms-time + still-halted paths),
    pinned by real-data unit tests (GME LULD / SWAV deficiency / AMOD open halt).
  - `NasdaqHaltRpcClient` — the Jayrock JSON-RPC client (`RPCHandler.axd`, Referer-
    guarded): `GetHaltsByDate('YYYYMMDD')` (one historical day, reaches back years) +
    `SearchTradeHaltsNEW` (trailing ~1yr, ~13k halts, one call).
  - `write_halt_statuses` (→ the partition `halt_feed.read_halt_events` + the DQ halt
    gate consume).
- `scripts/backfill_halts.py` — `--start/--end` (per-day historical via JSON-RPC),
  `--recent` (trailing ~1yr), `--url` (live RSS), `--file`/`--dir` (local archive).

## §5.2 halt data — external-data gate RESOLVED (Nasdaq reachable; historical source wired)

- The IR DQ gate `halt_data_unavailable_when_required` (data_quality.py) requires the
  lake's `statuses/` partition for `intended_realism`. Its logic is unchanged — **IR
  unblocks the moment a `statuses/` partition exists.**
- **`nasdaqtrader.com` is reachable again** (the earlier sandbox DNS `getaddrinfo`
  block is gone). The full historical source is now reverse-engineered, wired, and
  verified against real pulls:
  - **Source:** the TradingHaltSearch JSON-RPC — Jayrock 1.1 at `RPCHandler.axd`
    (Referer-guarded; `var Server=new RPCClient("RPCHandler.axd",PROTOCOL_JSON)`).
    `BL_TradeHalt.GetHaltsByDate('YYYYMMDD')` returns one historical day with the full
    record (Halt Date/Time, Issue Symbol/Name, Market, Reason Code, Pause Threshold,
    Resumption Date/Quote/Trade Time) and **reaches back years** — verified on
    **2024-06-03** (92 halts incl. the GME market-wide LULD pause).
    `SearchTradeHaltsNEW` returns the trailing ~1yr (~13k halts: ~9.7k LUDP LULD pauses,
    plus M/T1/T3/T2/T12/D…) in a single call.
  - **Verified end-to-end:** a 2-day live backfill (2024-06-03/04 → 161 halts → 83
    `statuses/` files) reads back through `read_halt_events` (GME `M` 13:31:17 →
    13:36:21 UTC). The table parser is pinned by real-data unit tests.
- **Alpaca still serves NO halt / LULD data** — Nasdaq is the source.
- The live RSS (`rss.aspx?feed=tradehalts`) remains a **current-open-halt snapshot
  only**; use `--start/--end` (GetHaltsByDate) for historical folds.

### Remaining operator step (a data-volume step, NOT a reachability gate)
- Run `scripts/backfill_halts.py --start … --end …` **on the container** (where the
  real lake `/opt/market_data_cache` lives) to populate `statuses/` over the study
  window, then run the IR walk-forward and confirm coverage on interior folds.
- **Halt RESUME from reopening auctions (P6)** remains a documented best-effort fallback
  for any day the RPC is unavailable; the RPC already carries resume times directly.

## CA announcement-time PIT hazard (§5.3 — flagged loudly)

The PIT master is **effective-date** survivorship (ex / effective / process date), NOT
announcement-time PIT — Alpaca exposes no CA creation time. A delisting/rename takes
effect in the sim on its effective date (conservative for entry: a soon-to-delist name
stays tradable until then). `build_pit_master` logs `CA_PIT_HAZARD` once. For true PIT,
snapshot the CA table daily; until then this is ex/effective-date survivorship.

## Operator runbook (container — where the real lake lives; Nasdaq where it resolves)

```bash
# §3.4/§5.3 corporate actions -> corporate_actions/ partition (PIT master auto-builds)
MARKET_DATA_ROOT=/opt/market_data_cache PYTHONPATH=src:../bowaka_common/src \
  /opt/conda/envs/quants-lab/bin/python scripts/backfill_corporate_actions.py \
    --start 2020-01-01 --end 2026-06-30 --workers 6

# §5.2 halts -> statuses/ partition (Nasdaq reachable; JSON-RPC GetHaltsByDate)
MARKET_DATA_ROOT=/opt/market_data_cache PYTHONPATH=src:../bowaka_common/src \
  python scripts/backfill_halts.py --start 2024-01-01 --end 2026-06-30   # historical
  #                                  --recent                             # trailing ~1yr
  #                                  --url                                # current snapshot

# then: run the intended_realism walk-forward and CONFIRM coverage on INTERIOR folds
# (not just the first sessions — ties to P2 #7). The PIT master drives the universe;
# the statuses/ partition satisfies halt_data_unavailable_when_required.
```

## Exit status

- §3.4 / §5.3 survivorship: **shipped + tested** (corp-actions producer, PIT master,
  builder wiring, min-history, `_status_active("")` fix, CA-PIT hazard documented).
- §5.2 halts: **producer + historical JSON-RPC source + tests shipped, verified against
  real Nasdaq pulls** (incl. 2024 — the GME LULD pause). The Nasdaq DNS gate is
  **cleared**; the bulk backfill onto the container lake + the end-to-end IR walk-forward
  on interior folds remain operator/container steps (a data-volume step, not a gate).
