# Phase 4 — Session minute-window cache (benchmark-only verdict)

Speedup report v2 §4 P3, §5.7, §10.4, §11.2 Phase 4.

## What landed

- **`SessionMinuteWindowCache`** in
  `scanner/session_minute_window_cache.py`. Preloads each eligible
  symbol's regular-session minute frame once per session (via the legacy
  supplier so timezone / normalisation / dedup logic is identical), then
  serves `bars_until(symbol, scan_ts)` via `np.searchsorted` slicing.
  * Inclusive upper bound: `searchsorted(timestamps, scan_ts_ns,
    side="right")` — a bar with ``ts == scan_ts`` IS returned.
  * Inclusive lower bound: :func:`intraday_window_start(scan_ts, policy)`
    by default (legacy parity); when the optional
    `max_bar_age_seconds` knob is set, the LATER of the policy bound
    and `scan_ts - max_bar_age_seconds`.
  * Missing-symbol returns the canonical empty minute frame with
    `["symbol", "timestamp", "open", "high", "low", "close", "volume"]`
    columns (same as legacy).
- **`make_session_minute_window_supplier`** in
  `scanner/session_minute_window_supplier.py` — closure with the
  legacy supplier's `(symbol, scan_ts) -> DataFrame` signature.
  Internally builds one `SessionMinuteWindowCache` per session lazily on
  first scan into that session; routes calls by
  `scan_ts.tz_convert("America/New_York").date()`.
- **Wired in `optuna/fold_context.py`** behind
  `optuna.acceleration.session_minute_window_cache.enabled` AND the
  existing `cached_suppliers` toggle. With both flags on the supplier
  bundle's `minute` callable is swapped for the cached one; the daily /
  quote / forward-minute suppliers keep the Phase 3 cached-suppliers
  semantics.
- **`ProfileCounters` Phase 4 fields**: `bars_supplier_calls`,
  `bars_df_slices`, `session_window_cache_hits`,
  `session_window_cache_misses`. Same default-off pattern.
- **`scripts/benchmark_session_minute_window_cache.py`** — operator-
  driven `--mode legacy|session_window` sweep that captures wall-clock,
  peak RSS, and the relevant counters. Not asserted by any test.

## New tests

- `tests/unit/scanner/test_session_minute_window_cache_supplier_parity.py`
  (6 parametrized + 1 empty case): legacy supplier vs cache return the
  same frame at mid-session / window-start / late-session / session-end
  / pre-window scan_ts values, columns / row count / content all match.
- `tests/unit/scanner/test_session_minute_window_cache_max_bar_age.py`
  (2): tight `max_bar_age_seconds=300` strictly shrinks the slice
  relative to legacy; `None` (default) returns every bar in the
  policy window.
- `tests/unit/scanner/test_session_minute_window_cache_missing_symbol.py`
  (1): cache + legacy agree on the empty frame for an absent symbol.
- `tests/parity/test_session_minute_window_fold_supplier_parity.py` (1):
  fold context's `suppliers.minute` callable with the flag off vs on
  returns identical per-(symbol, scan_ts) frames across every session.
- `tests/integration/test_session_minute_window_walkforward_objective_parity.py`
  (1, `@pytest.mark.slow`): walkforward `n_trials=2` parity — best_value
  within 1e-9 / best_params element-wise within 1e-9.

## Tests

| Gate | Result | Time |
|---|---|---|
| `make test-fast` | **1015 passed**, 0 failed | 46.4s |
| `make test-integration` (timeout=300) | **334 passed**, 2 skipped (PG-gated), 15 deselected (live + slow) | 13:50 |

## Default-off discipline

- `optuna.acceleration.session_minute_window_cache.enabled` is `false`
  everywhere — the prompt explicitly classifies this as
  "benchmark-only" until the parity tests prove the swap on the
  workstation.
- The flag is dual-gated: it has no effect unless `cached_suppliers` is
  also on (which is itself an opt-in). This keeps the legacy path the
  default-default.
- `max_bar_age_seconds` constructor knob defaults to `None` so the
  cache is byte-stable with the legacy supplier; the tightened-window
  semantics are opt-in only.

## Branch

`feature/phase-4-session-minute-window-cache` — merged to `dev` with
`--no-ff`.
