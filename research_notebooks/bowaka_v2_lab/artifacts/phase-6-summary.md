# Phase 6 summary — Execution, fill, and quote realism

**Branch:** `phase-6-realism-fills-and-quotes` (off `dev`)
**Audit refs:** P0-008, P0-012, §11 Phase 6, Tickets 7 & 8.
**Status:** complete, merged to `dev`.

## What shipped

- **Quote reader (`bowaka_common`)** — `MarketDataStore.quotes_at_or_before(
  symbol, ts, *, max_age_seconds, feed)` returning a `QuoteRow`
  (`bid, ask, bid_size, ask_size, mid, spread_pct, quote_age_seconds, source`).
  Quotes-lake layout `quotes/vendor=…/feed=…/symbol=…/year=…/month=…/part.parquet`;
  returns `None` when the partition is absent (the current lake has no `quotes/`).
- **`quote_supplier` wired** through `cli_runners`, `sim/backtester`,
  `StrategyConsumer.consume`, `optuna/walkforward_runner`.
- **Quote fallback per `simulation.quote_fallback_policy`** — `zero_spread`
  (parity: synthetic zero-spread at signal price), `synthetic_calibrated` (smoke:
  ADV/price/vol-calibrated spread + non-zero age + conservative slippage),
  `require_real` (realism: no historical quote → reject `missing_quote`).
- **Fill model integrated** — positions are created from a `FillResult`, not raw
  `quote.ask`. `market` → `quote.ask + slippage`; `marketable_limit` → limit with
  timeout (no fill on chase-past); partial fill below `min_order_notional` →
  no-fill `partial_below_min`; commissions/fees recorded.
- **Brackets from actual fill** — `stop_price`/`target_price` priced off
  `fill_price` (live `bracket_pricing_mode: actual_fill`).
- **Cost stress** — `base`/`conservative`/`severe` multiply slippage by
  `{1.0, 2.0, 3.5}`.
- **Quote coverage gate** — `SimulationConfig.min_quote_coverage_pct` (default
  95); an `intended_realism` run fails at finalize when historical quote
  coverage is below threshold.
- **Execution-quality report** — `reports/execution_quality.py`: spread
  (p50/p90/p99), quote-age, slippage-bps, fill-rate, partial-fill-rate,
  missing-quote, liquidity participation, fees, source-mix distributions.

## Files

`bowaka_common`: `marketdata/store.py`, `marketdata/__init__.py` (+1 test).
v2 lab: `sim/{quote_model,fills,strategy_consumer,portfolio,event_loop,backtester,__init__}.py`,
`scanner/scan_loop.py`, `data/{suppliers,data_quality}.py`, `config/models.py`,
`schemas/events.py`, `cli_runners.py`, `optuna/walkforward_runner.py`,
`reports/{__init__,execution_quality}.py`. Tests: 11 added; one
(`test_decision_sequencing_post_submit.py`) updated — realism now requires a
real quote, so the post_submit tests supply a `historical_quote`.

**Result:** v2 lab 522 passed / 1 skipped / 12 deselected; bowaka_common 84
passed; repo 20 passed. 0 failures.

## Acceptance criteria

| Criterion | Status |
|---|---|
| Positions created from fill results, not raw quote.ask | PASS |
| Quote supplier wired through every path | PASS |
| Synthetic fallback distinguished from real, capped by mode | PASS |
| Realism runs fail without sufficient quote coverage | PASS |
| env-check passes on all shipping configs | PASS (5/5) |

## Notes

- The lake has no `quotes/` partitions (operator constraint — no quote ingestion
  job, prompt §14). So `intended_realism` runs fail the finalize quote-coverage
  gate — correct/expected. Running realism end-to-end needs an operator quote
  backfill.
- Backward compatibility preserved: legacy `simulate_fill` / `synthesize_quote`
  / `get_quote` retained; `run_one_scan` tolerates 2- and 3-arg quote suppliers.
