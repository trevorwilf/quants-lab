# SIP NBBO quote backfill → full intended_realism

The lake had a quote *consumer* (quote_supplier, quote-aware fills/exits, the
quote-coverage DQ gates) but no quote *producer* — the backfill fetched bars
only, so `historical_quote_coverage_pct` was always 0 and `feed='auto'` could
never reach intended_realism. This adds the producer + fixes the cutover.

## Producer = consumer contract (pinned)

Quote parquet schema (exactly what `MarketDataStore.quotes_at_or_before` reads):
`symbol, timestamp(datetime64[ns,UTC]), bid, ask, bid_size, ask_size, conditions`
at `quotes/vendor=alpaca/feed=sip/symbol=<S>/year=<Y>/month=<M>/part.parquet`.
Consumer lookup is `at-or-before(ts)` within `max_age_seconds` → returns the last
quote ≤ ts. The synthetic-SIP fixture stores ONE NBBO snapshot per minute; this
matches that cardinality + the bar-ts lookups.

## Implementation (`bowaka_common/marketdata/backfill.py` + `runner.py`)

- `make_alpaca_quotes_fetcher` — mirrors `make_alpaca_bars_fetcher` but
  `StockQuotesRequest`/`get_stock_quotes`, feed-aware (SIP), paginated. Returns
  the full NBBO tick stream per symbol.
- `_coerce_quote_row` — Alpaca quote (SDK obj OR raw dict: bid_price/bp, etc.) →
  canonical row, tz-aware UTC.
- `_sample_session_nbbo` — **the key**: tick stream → one prevailing NBBO per
  regular-session minute boundary (09:30–16:00 ET, DST-aware) via
  `merge_asof(direction="backward")`, keeping each quote's ACTUAL tick timestamp
  (so quote-age telemetry is real). ≤390 rows/symbol/session.
- `fetch_quotes` — mirrors `fetch_minute_bars`: per session batch symbols, fetch,
  sample per symbol, accumulate per (symbol, month), write at `quotes_path`.
  Resume-aware (skip sessions already in the symbol's month file). Quotes share
  the **minute-bar (symbol, session) universe** (so quotes exist where bars do).
- `runner.run_configured_backfill` — computes the target set once for minute +
  quote stages; runs `fetch_quotes` when `config.quotes.enabled` (warns if
  feed != sip — IEX quotes are partial-tape, unused by realism). New
  `quotes_fetcher` injection point for tests.

## Cutover fix (`bowaka_v2_lab/optuna/autoconfig.py`)

`lake_has_bars` checked ONLY the legacy `raw` daily partition. The backfill
writes `split_adjusted` (the bowaka_v2 default), so a fresh SIP backfill was
invisible → `feed='auto'` stayed on IEX even with SIP bars+quotes. Fixed to
check `raw` OR `split_adjusted` (mirrors `probe_lake_capability`). The IEX lake
(legacy raw present) is unaffected.

## Operator interface — cron-safe

- `config/marketdata_backfill.yml`: a `quotes:` block, **default disabled** (a
  nightly cron must not suddenly do a massive historical quote run).
- `scripts/backfill_market_data.py --quotes` (+ `backfill_market_data.ps1`
  passes it through): enable the quote stage per-invocation without editing the
  shared config. Run:
  `.\backfill_market_data.ps1 --feed sip --quotes --start 2025-01-01`.
  **Heavy on a first run** — the NBBO tick stream must be fetched before
  sampling (AAPL ≈ 11k ticks / 3 min). Scope `--start/--end` to the backtested
  windows (val + holdout); it is incremental (nightly adds the new day cheaply).

## Tested (real Alpaca SIP + synthetic)

- Real SIP fetch: 11,315 AAPL NBBO ticks / 3 min, exact schema, creds load from
  `/quants-lab/.env`, SIP feed entitled.
- Real e2e backfill (daily+minute+quotes, AAPL/1day → temp lake):
  `detect_best_feed → sip / intended_realism`; `quotes_at_or_before` returns a
  real sampled NBBO (0.6 bps spread, age 0.06 s).
- `tests/unit/test_marketdata_quotes_backfill.py` (round-trip + sampling +
  resume) + `tests/unit/test_autoconfig_split_adjusted_cutover.py` (the fix +
  cutover). bowaka_common marketdata 47 pass; autoconfig 12 pass.
