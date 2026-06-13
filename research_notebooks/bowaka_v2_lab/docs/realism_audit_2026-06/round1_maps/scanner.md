I have what I need. The live reference `_et_minute_of_day` localizes naive to UTC (line 281), confirming the lab's documented divergence (lab rejects naive). Let me verify one remaining lead: the matrix builder window start (4:00 ET premarket) vs the live/legacy scan supplier window (09:45 ET default policy) — this is a potential parity gap between matrix path and scan_loop path. Let me confirm the matrix bakes 04:00-start bars while the runtime scan_loop uses the policy window.

The matrix `build_session_partition` (lines 604-611) fetches bars from 04:00 ET, and at lines 685 filters `full_bars[ts_col] <= scan_ts_obj` — no lower-bound policy filter. The live scan_loop path uses `intraday_window_start` (09:45 ET default). This is a real divergence I'll flag. Let me confirm there's no lower-bound applied in the numba build path either (lines 629-677): correct, the numba kernel accumulates from the first bar `j=0` with no policy lower bound.

I have read all target files end-to-end plus the supporting modules. Compiling the report.

## Purpose & data flow (how this subsystem fits the backtest pipeline)

The scanner screens the PIT universe at each intraday scan timestamp and emits ranked candidate events that the sim/event-loop converts into entries. Data flow per session:

1. `sim/schedule.scan_times_for_session` produces the UTC scan cadence `[scanner_start … min(scanner_end, early_close)]` (calendar-aware, DST-safe).
2. `scanner/scan_context.build_scan_session_context` precomputes `universe_meta_by_sym`, `cache_by_sym` (daily baselines), `config_hash_v`, and a `(scan_ts, adv_bucket)→volume_curve_fraction` map once per session.
3. For each scan_ts, `scan_loop.evaluate_one_scan` iterates symbols: dedup gates → baseline lookup → vcf lookup → `bars_supplier(symbol, scan_ts)` (forming minute bars up to cutoff) → stale-bar check → `aggregate_forming_session_bar` → `compute_forming_session_features` → `apply_v2_gates` → `compute_signal_strength` → rank/cap → `build_candidate_event`.
4. Bars come from `data.suppliers.make_lake_suppliers` (per-call parquet re-read) OR `SessionMinuteWindowCache` (preloaded session frame, searchsorted slice). 
5. Optional precomputed path: `scan_matrix.build_session_partition` bakes per-(scan,symbol) features into memmapped columns; `scan_matrix_runtime.evaluate_one_scan_compat` and `scan_matrix_vectorized.evaluate_one_scan_vectorized` reconstruct dicts/gates from the matrix instead of re-aggregating bars. Both claim field-by-field parity with the legacy scan; the bare `evaluate_one_scan_from_matrix` Phase-9 entry remains hard-refused scaffolding.

## Behavioral spec

**Forming-bar / PIT semantics**
- Forming-session bar is the cumulative aggregate of all minute bars with `timestamp <= scan_ts` — inclusive upper bound (`session_minute_window_cache.py:194-196` `side="right"`; matrix builder `scan_matrix.py:685` `full_bars[ts_col] <= scan_ts_obj`; numba `_numba_scan_features.py:284` `bar_ts_ns[j] <= sc`). The bar *stamped at* scan_ts IS consumed. If lake bars are interval-START stamped, the in-progress minute (open through scan_ts) is included — i.e. the scanner sees the full minute that begins at scan_ts. **This is the PIT-critical assumption and it is nowhere asserted in the scanner.**
- `aggregate_forming_session_bar` (`forming_bar.py:160-211`): open=first row, high=max, low=min, last_price=last close, volume=sum; rejects naive `last_bar_timestamp` (`:195-199`).
- Lower bound: scan_loop relies on the supplier's `intraday_window_start` (policy ET 09:45/09:30/04:00, `suppliers.py:47-71`); matrix builder fetches 04:00→16:00 ET and applies **no** policy lower bound before cumulating (see Leads).

**rvol / range-expansion / ema-slope / features** (`forming_bar.py:278-376`)
- `rvol_so_far = session_volume / (avg_volume_20d * vcf)`; `projected_full_day_rvol = (session_volume/vcf)/avg_volume_20d`; `range_expansion = session_range / prior_atr_14d`; `close_location = (last-low)/(high-low)`; `ema_distance = last/ema_10_prior - 1`; `current_return = last/prior_close - 1`; `gap = session_open/prior_close - 1`. Each guarded by `x and x>0` truthiness (so a 0.0 baseline → `None` feature).
- `ema_slope_prior` is a baseline (`compute_prior_daily_baselines:119-130`), NOT a forming feature; computed as `ema_10_prior/ema_10_lag_3 - 1` with `ewm(span,adjust=False)`. **Note divergence from `suppliers._daily_cache_row_from_prior:367` which computes `ema_slope_prior=(ema_prior-ema_lag3)/3.0` (absolute/3, not ratio).** Two different slope definitions feed the scanner depending on path.
- ATR is a **simple mean** of last `atr_n` TRs, not Wilder (`forming_bar.py:98-99`, kernel `:191`).

**Gates** (`forming_bar.py:400-466`): price/adv `_between`; rvol/proj/atr%/range/close_loc/ema_dist/ema_slope `_ge`; gap/max_rvol/max_range `_le`; instrument fail-closed. `_le` passes on `None` value (`:489-491`); `_ge` fails on `None` (`:481-482`); `_between` fails `None` when any bound set (`:495-496`).

**Score** (`forming_bar.py:509-554`): weighted sum, bounded caps default on; `cl_weight*cl + 10*ed + 10*es - max(gap-0.25,0)`. None→0.0.

**Dedup/cap** (`scan_loop.py`): already-entered → cooldown (390min default) → same-symbol-day-cap (1) → baselines → stale → gates. Emitted capped at `min(max_candidates_per_scan=25, max_entries_per_scan)`. Cooldown/day-cap keyed on EMIT counter `signal_emits_per_symbol_today`, separate from portfolio fills.

**Timezone** (`schedule.py`, `forming_bar.py:252-261`): all scan times built tz-aware local then UTC; `_et_minute_of_day` clamps [0,389]; naive rejected via `require_aware_timestamp`.

**Matrix equivalence**: three evaluators (legacy/compat/vectorized) share `apply_v2_gates`/`compute_signal_strength`/`build_candidate_event`; compat/vectorized reconstruct session_bar+feats from cells via `_nan_to_none`. Stable descending sort claimed equivalent to Python `sort(key=-score)`.

## Knobs
- `scanner.max_candidates_per_scan` (25), `scanner.max_entries_per_scan` (=max_candidates) — emit cap (`scan_loop.py:182-184`).
- `scanner.same_symbol_entries_per_day` (1) — per-day emit cap; `>0` to enable (`:190,305`).
- `scanner.symbol_cooldown_minutes` (390) — re-emit cooldown; `<=0` disables (`:191,317`).
- `market_data.max_bar_age_seconds` (90) — stale-bar threshold (`:187`).
- `simulation.intraday_window_policy` (`scanner_start_to_scan`/09:45) — supplier lower bound only (`suppliers.py:37-44`).
- `session.scanner_start/scanner_end/scan_interval_seconds/timezone/calendar` — scan cadence (`schedule.py:118-134`).
- `historical_features.volume_curve.bucket_edges` / `fallback_opening_15m_share` (0.08) — vcf (`scan_loop.py:164-171`).
- `signals.*` thresholds + `allow_unknown_instrument_class_for_research` (False, fail-closed) (`forming_bar.py:460`).
- `score.bounded`(True)/`close_location_weight`(0.75)/`gap_penalty_above`(0.25)/caps.
- `optuna.acceleration.numba.enabled` (False) — compiled kernels build+scan.
- `optuna.acceleration.scan_matrix.runtime_mode` (disabled) — disabled/compatibility/vectorized (`scan_matrix_runtime.py:70-89`).
- `BOWAKA_MATRIX_RUNTIME_ASSERT` env — debug parity assert (`:92-96`).

## Invariants & guards
- Naive-timestamp rejection: `_iso_utc` (`scan_loop.py:120`), `evaluate_one_scan` scan_ts (`:226`), `aggregate_forming_session_bar` (`:196`), `_et_minute_of_day`/`require_aware_timestamp`, volume_curve builder (`volume_curve.py:74-78`). Fail-loud.
- Volume-curve lookahead guard: `build_volume_curve_from_minute_bars` asserts no `current_session` rows (`volume_curve.py:83-90`). Fail-loud.
- Holdout isolation: `ScanMatrixStore.assert_can_read` refuses objective reads of holdout sessions (`scan_matrix.py:222-239`).
- Matrix opt-in refused: `evaluate_one_scan_from_matrix[_vectorized]` always raise; vectorized requires parity_proof_version≥2 (`scan_matrix_runtime.py:593,625,659-674`).
- Search-space guard: `assert_search_space_compatible_with_matrix` (`scan_matrix.py:393-413`).
- Matrix verify: dataset_hash drift + per-cell self-consistency (`verify_scan_matrix`).

**Silent fallbacks (flagged):**
- `SessionMinuteWindowCache.bars_until` returns **empty frame** on missing symbol (`session_minute_window_cache.py:188-190`) — no signal a symbol was absent vs genuinely no bars.
- `session_minute_window_supplier` returns empty frame on session-not-in-set or symbol-not-in-symbols_by_session (`:58-59,67` via cache) — silent.
- vcf `scan_context` miss silently falls back to per-call compute (`scan_loop.py:340-347`; compat `:317`; vectorized `:433`).
- `compute_volume_curve_fraction` silently returns fallback S-curve when curve is None/missing-columns/empty-bucket (`forming_bar.py:227-240`) — no fallback-rate surfaced per call (`fallback_rate` is a crude 0/1).
- Matrix builder swallows per-symbol bar-fetch exceptions → empty (`scan_matrix.py:616-617`), and `last_ts` parse exceptions (`:707-708`).
- `_eligible_pit_union_for_lineage`/`_prewarm_pit_daily_cache` swallow all exceptions (`:860,919`).
- `bars_supplier` exception in scan_loop → `BARS_FETCH_FAILED` skip, no counter mapped (`scan_loop.py:84` comment, not in `_SCAN_SKIP_COUNTER_FIELD`).
- `instrument_class is None` + `allow_unknown=False` → reject, but None is also the matrix static-int8 sentinel; instrument_class is never actually wired into the matrix (placeholder `:597-598`).

## Leads
- `scan_matrix.py:604-685` — **Matrix bakes 04:00 ET premarket bars with NO policy lower bound**, but the live/legacy `scan_loop` supplier starts the window at `intraday_window_start` (09:45 ET default). The matrix's cumulative session_open/high/low/volume therefore include premarket, diverging from the policy-windowed scan_loop. Potential matrix-vs-legacy parity break for any non-`extended_hours` policy.
- `_numba_scan_features.py:284` / `scan_matrix.py:685` — same: numba/build cumulate from bar `j=0` with no `intraday_window_start` filter; parity to scan_loop holds only if the supplier feeding scan_loop also returns from the same start.
- `forming_bar.py:123-126` vs `suppliers.py:367` — **two different `ema_slope_prior` definitions** (ratio `ema_prior/ema_lag3-1` vs absolute `(ema_prior-ema_lag3)/3`). Whichever populates `cache_by_sym` decides the `ema_slope_gate` and score `es` term; a silent semantic mismatch between baseline builders.
- `forming_bar.py:357` — `ema_slope_lookback` default 3 means `ema_10_lag_3 = ema_series.iloc[-4]`, but `suppliers._daily_cache_row_from_prior:357` uses `ema.iloc[-4]` AND divides by 3 hard-coded — lookback not honored consistently.
- PIT lookahead risk (whole subsystem): inclusive `<= scan_ts` consumes the bar stamped at scan_ts. If lake minute bars are interval-START stamped (Alpaca convention), the scanner sees a bar covering [scan_ts, scan_ts+60s) — i.e. **future price action within the forming minute**. No assertion anywhere pins the stamping convention. High-priority realism check.
- `scan_loop.py:373` ts-column detection only matches `timestamp`/`ts`; an empty/missing ts column silently skips the **entire** stale-bar check (`stale_skipped` stays False) — a bar with no recognizable ts column bypasses staleness.
- `scan_loop.py:506` `passing.sort(key=lambda x: -x[0])` — `x[0]` is `score`; if any passing score is `None` this raises (TypeError on `-None`). Passing branch always sets score (gates passed ⇒ `compute_signal_strength` ran), but no guard if a future gate path leaves it None.
- `scan_loop.py:305` `signal_emits_per_symbol.get(symbol,0) >= same_symbol_day_cap > 0` — chained comparison; when `same_symbol_day_cap==0` the cap is silently disabled (intended?) but undocumented at call site.
- `session_minute_window_cache.py:166-171` — `.view("int64")` on `datetime64[ns]` array; if any timestamp is NaT it becomes a large negative int and corrupts searchsorted bounds silently.
- `scan_matrix.py:1039,1067` — `sample_scan_count`/`n_scans_per_session` size estimate arithmetic (`390 // (scan_interval//60)`) is a coarse heuristic that breaks for sub-60s intervals; could under/over-reserve memory.
- `volume_curve.py:156-164` `fallback_rate` returns 0.0 for ANY non-empty curve and 1.0 for empty — does not actually count fallback cells; misleading data-quality metric.
- `scan_matrix_runtime.py:99-104` `_nan_to_none` does `float(v)` with no try/except — a non-float matrix cell raises; relies on builder dtype discipline.
- `scan_matrix.py:1135` `_dt.datetime.utcnow()` deprecated (naive UTC) — cosmetic.
- `scan_matrix_runtime.py:368` debug assert path re-fetches via `debug_bars_supplier` but does NOT compare against the policy-windowed bars (uses raw supplier), so the 04:00 vs 09:45 divergence above would NOT be caught by the debug assert.
- `scan_loop.py:142` docstring says "bars_supplier is the only data-side injection" but vcf/baselines also come from `scan_context` — stale-context risk if context built from a different cfg than the per-scan cfg (config_hash_v not re-checked per scan).
- `forming_bar.py:339-342` `projected_full_day_rvol` divides by `volume_curve_fraction` with only `>0` guard — a tiny vcf near session open massively inflates projected rvol (early-session false positives).

## Test coverage hooks
- Forming/gates/features: `tests/unit/test_features_gates.py`, `test_features_no_lookahead.py`, `test_features_timezone.py`, `test_instrument_gate_fail_closed.py`, `test_dq_feature_leakage_detected.py`.
- Volume curve: `test_volume_curve_builder.py` (builder lookahead assert). **No test found for `compute_volume_curve_fraction` interp/fallback edge cases or `_fallback_curve_fraction` numba-vs-python parity.**
- Scan loop: `test_scanner_max_entries_per_scan.py`, `test_scanner_stale_bar.py`, `test_scanner_state_paths.py`, `test_scanner_counter_emit_vs_filled_distinct.py`, `test_scanner_event_builder.py`, parity `test_scan_loop_context_parity_full_mode.py`, `test_scan_loop_objective_minimal_legacy_parity.py`, `test_scan_loop_objective_mode_emissions_match.py`.
- Matrix: extensive `tests/parity/test_scan_matrix_*` (one_scan/full_session/full_fold/tie_order/state_mutation/gate_dump/rejection_counts/event_id/runtime_debug_assert) + vectorized twins.
- Session-minute cache: `tests/scanner/test_session_minute_window_supplier_parity.py`, `tests/parity/test_session_minute_window_fold_supplier_parity.py`, `test_cached_minute_supplier_parity.py`.
- Schedule: `test_scan_count_per_session.py`.
- **No test exercises the matrix 04:00-ET-vs-policy-window divergence** (debug-assert uses raw supplier, not policy-windowed). **No test for the `ema_slope_prior` ratio-vs-absolute mismatch between `forming_bar` and `suppliers`.** **No direct test of the PIT bar-stamping convention** (inclusive `<= scan_ts`). **No test of stale-bar bypass when ts-column is absent.**