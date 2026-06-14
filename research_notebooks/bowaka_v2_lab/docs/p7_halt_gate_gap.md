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

**§5.2 — Nasdaq halt ingester (code + tests; OPERATOR-run, see gate below):**
- `data/halt_ingest.py` — `parse_nasdaq_halt_rss` (documented Nasdaq RSS shape →
  `statuses/` rows) + `write_halt_statuses` (→ the partition `halt_feed.read_halt_events`
  + the DQ halt gate consume).
- `scripts/backfill_halts.py` — `--url` (live) / `--file` / `--dir` (historical archive).

## The Nasdaq halt-data GATE (§5.2) — why IR is not fully unblocked here

- The IR DQ gate `halt_data_unavailable_when_required` (data_quality.py) **already
  correctly requires** the lake's `statuses/` partition for `intended_realism`. Its
  logic is unchanged — **IR unblocks the moment a `statuses/` partition exists.** The
  only missing piece is the producer (the data).
- **Alpaca serves NO historical halt / LULD data** (confirmed — only current snapshots).
- **The build sandbox cannot resolve `nasdaqtrader.com`** (DNS `getaddrinfo` fails;
  only the Alpaca data host is reachable). So the Nasdaq ingester is **operator code**:
  run `scripts/backfill_halts.py` from a host/container where Nasdaq resolves.
- The live Nasdaq RSS (`rss.aspx?feed=tradehalts`) is **current halts only**.
  Historical halts for past folds need the operator's saved Nasdaq archive
  (`--dir` of saved RSS files) or a paid historical halt feed.
- `parse_nasdaq_halt_rss` is built to the **documented** Nasdaq RSS field shape —
  **validate it against one real pull** before production use.

### Best-effort fallback (per the chosen design: probe → fall back)
- **Halt RESUME from reopening auctions (P6):** a halt resumes with a reopening
  auction, so resume *could* be inferred from the auctions feed without Nasdaq.
  Caveat: the P6 auctions producer extracts the official **open/close** prints only;
  inferring resume needs the **intraday** halt-resume auction prints (other condition
  codes) — a bounded extension to the P6 auctions extraction. **Onset + LULD bands
  still require the Nasdaq feed.**
- Until the operator lands real Nasdaq halt data, `intended_realism` stays gated at the
  DQ halt check — **by design** (fail-closed). This is the documented IR halt-gate gap;
  the survivorship half of P7 (§3.4/§5.3) is fully shipped + tested and does not depend
  on it.

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

# §5.2 halts -> statuses/ partition (run where nasdaqtrader.com resolves)
MARKET_DATA_ROOT=/opt/market_data_cache PYTHONPATH=src:../bowaka_common/src \
  python scripts/backfill_halts.py --dir /path/to/nasdaq_halt_rss_archive   # historical
  #                                  --url                                   # current

# then: run the intended_realism walk-forward and CONFIRM coverage on INTERIOR folds
# (not just the first sessions — ties to P2 #7). The PIT master drives the universe;
# the statuses/ partition satisfies halt_data_unavailable_when_required.
```

## Exit status

- §3.4 / §5.3 survivorship: **shipped + tested** (corp-actions producer, PIT master,
  builder wiring, min-history, `_status_active("")` fix, CA-PIT hazard documented).
- §5.2 halts: **producer + tests shipped**; the live data ingest + the end-to-end IR
  walk-forward on interior folds are **operator/container steps** (Nasdaq DNS-gated in
  the build sandbox), documented here.
