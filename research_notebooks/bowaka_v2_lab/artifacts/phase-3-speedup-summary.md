# Phase 3 — Bowaka-local cached lake-supplier adapter

Speedup report §5.3 / §10.3 / §11.2.

## What landed

- **`data/cached_suppliers.py`** (new):
  `CachedSessionMarketData` wraps `MarketDataStore` with two LRUs
  (`_minute_cache` and `_quote_cache`, default cap 4096 entries) plus a
  per-`(symbol, end_date)` daily lookback cache. Each
  `(symbol, year, month, feed, adjustment)` Parquet partition is read once
  per process; subsequent calls slice the in-memory frame.
  - `forming_minutes(symbol, cutoff)` — minute-bar window from
    `intraday_window_start(cutoff, policy)` to `cutoff`, both ends
    **inclusive**, sort + dedupe-last identical to
    `MarketDataStore.minute_bars`.
  - `forward_minutes(symbol, ts, window_minutes=5)` — same inclusive
    boundary semantics; `window_minutes` override supported.
  - `quote_at_or_before(symbol, ts, max_age_seconds=None)` — returns the
    same dict shape as `make_quote_supplier`'s callable (`bid`, `ask`,
    `mid`, `spread_pct`, `quote_timestamp`, `quote_age_seconds`,
    `source="historical"`). Missing partitions are cached as negatives.
  - `daily_bars(symbol, session_date)` — trailing
    `daily_lookback_days` (default 400) keyed by `(symbol, end_date)`.
  - `make_cached_lake_suppliers(...)` factory +
    `make_cached_supplier_callables(adapter)` returns the four
    legacy-shape callables so the backtester accepts them unchanged.
- **`config.models.OptunaConfig.cached_suppliers: bool = False`** added.
  When true, `run_walkforward_study` builds each `FoldRuntimeContext`'s
  supplier bundle from a `CachedSessionMarketData` adapter. Default false
  preserves the legacy path; Phase 5 flips this on.
- **`optuna/fold_context.py`** — `_build_one_fold_context`,
  `build_fold_contexts`, and `build_holdout_context` now accept
  `cached_suppliers=False`. The flag is threaded from
  `run_walkforward_study` and `score_final_holdout`.
- **Config generator** — `reference/import_config.py` writes
  `optuna.cached_suppliers: false` to each generated optuna config
  (default off). Phase 5 flips to `true`.

## New tests

- `tests/parity/test_cached_minute_supplier_parity.py` (10).
- `tests/parity/test_cached_forward_minute_parity.py` (7).
- `tests/parity/test_cached_quote_supplier_parity.py` (3).
- `tests/parity/test_cached_supplier_lru_bound.py` (1).
- `tests/integration/test_cached_suppliers_walkforward_parity.py` (1).

## Result

`make test` (full unit + parity + integration + reconcile, excluding
slow/live): **1210 passed, 0 failed, 12 deselected** (16:14).

## Branch

`feature/phase-3-cached-suppliers` merged to `dev` with `--no-ff`.
Phase 4 takes off from `dev` next.
