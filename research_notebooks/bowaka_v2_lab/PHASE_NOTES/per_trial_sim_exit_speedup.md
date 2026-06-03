# Per-trial sim exit-walk speedup (deeper sim pass)

Goal: cut the post-matrix per-trial wall-clock further so the 5000-trial
walk-forward study fits the 24–48 h budget. The prior pass
(`per_trial_scan_speedup.md`, opt #1) attacked the matrix scan runtime; this
pass attacks the **sim exit path**, which the numba Phase-2 notes flagged as the
post-matrix residual (`bars_supplier_calls≈5.07M`, `bars_df_slices≈4.13M`,
`event_count_processed≈3.79M`). **Accuracy is the hard constraint** — every
change here is proven byte-identical, not "close".

## Where the time actually goes (corrected target)

Reading the code + cadence beat the `iterrows` hypothesis:

* The walk-forward objective drives exits through the **minute event loop**
  (`backtester._close_lots_until`), NOT `drive_session_exits_minute` (imported
  but never called). So the full-session batch walk is dead in the per-trial.
* Cadence defaults (`event_loop.CadenceConfig`) are **5 s** fill + protection
  polls → ~10k events/session. `_close_lots_until` runs per event, and per event
  per open lot it did `pd.to_datetime(bars.iloc[cursor:][ts]) <= walk_until`
  then `mask.sum()` — an **O(remaining-tail) re-parse of the timestamp column on
  every one of those ~10k events**, even when zero new bars appeared. THAT is the
  `bars_df_slices` cost, not `walk_lot_exit`'s `iterrows`.
* Because the cadence (5 s) is finer than the bar cadence (60 s),
  `walk_lot_exit` is actually called with **1-bar slices** most of the time.

## Optimization A — `_close_lots_until` window boundary (the dominant win)

`backtester.py`: cache each lot's sorted minute timestamps ONCE as an int64
ns-since-epoch (UTC) array (`ts_ns_by_lot`), and resolve the per-event new-bar
boundary with a single `np.searchsorted(ts_ns, walk_until_ns, side="right")`
instead of re-parsing the tail every event. `side="right"` includes a bar whose
ts == `walk_until`, exactly as the legacy `<= walk_until` mask did. The bars are
pre-sorted by `_bars_for_lot`, so the searchsorted boundary equals the legacy
`mask.sum()` boundary byte-for-byte; the identical `sub` frame reaches
`walk_lot_exit` and the cursor advances identically.

**Measured (1 held lot, 1 full regular session, 5 s cadence, 390 bars):**
per-event windowing **1213.6 ms → 9.1 ms = 132.9×**, with the new boundary
asserted equal to the legacy boundary for all 4669 events (µs and ns source
resolution). This recurs per (lot × session × fold) in every trial.

## Optimization B — `walk_lot_exit` numpy fast path (secondary, non-regressive)

`exits.py`: the reference walk (`_walk_lot_exit_pandas`, kept verbatim as the
frozen oracle + fallback) iterates `df.iterrows()` and reads each minute via
`_bar_ts`/`_bar_field` (fresh `Series` + per-bar `tz_convert`). The new
`_walk_lot_exit_numpy` pre-extracts the sorted path ONCE into numpy arrays
(`ts_ns` int64, vectorized ET `date`/`time` object arrays, `float64` OHLC) and
iterates by integer index with int/float compares, materialising a
`pd.Timestamp` only on the rare bar that exits / halts / re-scores. Same IEEE-754
double arithmetic → identical `ExitEvent` + `FadeTelemetry`.

Key parity facts baked into the port:
* `state.peak`/`trough` use `if h > peak` / `if l < trough` — identical to
  `max`/`min` AND inherits Python's NaN semantics (`NaN > peak` is `False`), so a
  present-NaN bar leaves excursions unchanged exactly as `max(peak, NaN)` would.
* `_bar_field` returns `None` only for an ABSENT column (numeric columns yield
  `NaN`, never `None`); the fast path is gated to numeric-OHLC frames
  (`_exit_walk_fast_eligible`) so the None-vs-NaN distinction never matters —
  object / missing-column frames fall back to the pandas reference.
* `idx[i].isoformat()` (original resolution) == `_bar_ts(bar).isoformat()`, so
  `exit_timestamp`, the same-minute seed key, and fade telemetry match.
* ns forced via `to_numpy("datetime64[ns]").view("int64")` (the µs astype gotcha).

**Measured (single `walk_lot_exit` call):** 1 bar 0.85× (slight regression),
3 bars 1.3×, 30 bars 5.5×, 388-bar full session **25–36×**. Because the event
loop usually passes 1-bar slices, a `_FAST_EXIT_WALK_MIN_BARS = 3` guard in the
`walk_lot_exit` dispatcher keeps tiny slices on the pandas path (no regression)
and routes only larger catch-up / full-session walks through numpy.
`_FAST_EXIT_WALK = True` is a module kill switch (flip → pandas everywhere).

## Accuracy gates (results provably unchanged)

* `tests/parity/test_walk_lot_exit_numpy_parity.py` — differential lock: drives
  BOTH production impls over hand-built cases for every exit branch (stop,
  target, gap, same-minute tie ×3, time-stop ±quote, max-hold inline+fallback,
  signal-fade active+telemetry, severe halt, until_ts window, status-defer, NaN
  cells, duplicate/unsorted ts) PLUS a seeded 400-case fuzzer, asserting every
  `ExitEvent` field + `FadeTelemetry` row exactly equal (NaN-aware).
* `tests/parity/test_close_lots_until_window_boundary.py` — pins the searchsorted
  boundary == legacy `to_datetime+mask.sum` boundary across a full-session 5 s
  cadence (µs+ns), bar-exactly-on-event, duplicate ts, single-bar/empty-tail.
* Existing suite: all 11 `test_exit_*` unit tests + the exit integration tests
  pass through the new dispatcher; the full-backtester event-loop integration
  tests (`test_event_driven_simulator`, `test_backtester_multi_day_hold`,
  `test_backtester_determinism`, `test_iex_subset_replay_deterministic`,
  `test_backtester_with_synthetic_quotes`, `test_exit_lifecycle_metrics_in_report`)
  and the scan-matrix full-fold/session parity tests (vectorized/compat/legacy)
  all green — these run `_close_lots_until` + `walk_lot_exit` end-to-end and
  assert deterministic golden outcomes.
* Host suite: `tests/unit` + `tests/parity` = **1495 passed, 1 skipped**, modulo
  the 4 documented pre-existing failures (gitignored prod-mirror
  `test_prod_backtester_*` ×2; operator's dirty notebooks 10 & 13 bootstrap-cell
  tests ×2). Run: `C:/Python312` + `PYTHONPATH=src;../bowaka_common/src`.

## Per-trial impact + how to confirm

Isolated speedups are large (132× on the windowing hot spot; 25–36× on the
full-session walk), but the real per-trial multiplier depends on how many
(lot × session × fold) windows a trial evaluates — which only a live measurement
settles. The current 5000-trial study (`d79e4c42_20260603`) was paced at ~110 h.
The study name hash is config-derived (unchanged), so **restarting the study
resumes the completed trials and runs the rest on the faster code** — the parity
gate guarantees the resumed trials are bit-identical to what the old code would
have produced, so mixing is safe. Measure the new trials/hour off the Optuna DB
and re-project the 5000-trial finish.
