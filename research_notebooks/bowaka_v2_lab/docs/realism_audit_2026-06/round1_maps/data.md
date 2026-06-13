I now have a complete picture. Let me write the report.

## Purpose & data flow (how this subsystem fits the backtest pipeline)

The `data` subsystem is the read/quality boundary between the shared Alpaca Parquet lake and the v2 backtester. Flow: `loaders.py`/`suppliers.py`/`cached_suppliers.py` wrap `bowaka_common.marketdata.MarketDataStore` (`store.py`, paths from `layout.py`) into the supplier callables `run_backtest`/`replay` consume — `minute_bars_supplier(symbol, cutoff)`, `daily_bars_supplier(symbol, session_date)`, `forward_minute_supplier`, `quote_supplier`, `trades_supplier`. `suppliers.build_daily_cache_from_lake` / `daily_cache_batch.build_daily_cache_for_sessions_from_lake` precompute the no-lookahead daily-feature cache. `lineage.py` derives the content-addressed `dataset_hash`. `data_quality.py` + `dq_levels.py` build the DQ report and gate `intended_realism` runs closed (`evaluate_startup_dq`). `verify_lake.py` is the operator CLI presence check. `backfill.py` (writer, `bowaka_common`) is the producer for bars/quotes/trades/quotes_fine/assets/audit/manifest.

## Behavioral spec (exact file:line refs)

**Lake schema** (`layout.py:7-31,56-65`): `bars/vendor/feed/timeframe={1d|1m}/adjustment/symbol[/year/month]`; `quotes/`, `quotes_fine/`, `trades/` per symbol/month; `statuses/` per symbol/date; `corporate_actions/`, `assets/snapshot_id`, `_ingestion/`. Daily=1 file/symbol; minute/quotes=per month.

**Minute bars (RAW always)** (`backfill.py:333,456-462`): minute bars always fetched+stored+read at `adjustment="raw"`; `cfg.adjustment` (e.g. split_adjusted) governs DAILY only. `store.minute_bars` (`store.py:242-276`): reads months overlapping `[start,end]`, inclusive both ends, sort+dedup on timestamp keep="last", returns tz-aware UTC OHLCV (`_BAR_COLUMNS` `store.py:19`).

**Daily bars** (`store.py:205-240`): filters on `session_date` column if present else timestamp `[start, end+1day)`; sorted ascending. `adjustment` defaults `"raw"`.

**Forming-window supplier** (`suppliers.py:152-157`, `intraday_window_start:47-71`): window `[policy-local-start, cutoff]` in UTC; policy start 09:45/09:30/04:00 ET (`_INTRADAY_WINDOW_START_ET:37-41`), default `scanner_start_to_scan` (09:45). ET session date from cutoff so window never spills to prior premarket.

**Forward minute supplier** (`suppliers.py:186-191`): `[ts, ts+window_minutes]` (default 5).

**Quote supplier** (`suppliers.py:218-238`): wraps `store.quotes_at_or_before`; returns dict with real row timestamp (`row_ts`, P1-002 fix line 224-227), `quote_age_seconds`, `source`. `store.quotes_at_or_before` (`store.py:350-418`): latest quote `<= ts` no older than `max_age_seconds` (default 60), else `None`; mid/spread synthesised from bid/ask if columns absent (396-400).

**Cached suppliers** (`cached_suppliers.py`): per-process LRU over normalised partitions; boundary semantics must match store exactly (8-12, `_range:203-225`). Negative minute partitions cached as empty frame (124); missing quote partitions memoised in `_missing_quote_partitions` (102,144,154). `quote_at_or_before` (227-276) reimplements store quote logic independently.

**Daily-feature cache row** (`suppliers.py:321-368`): TR/ATR(14)/EMA(10,adjust=False) over the truncated `prior` (<= lookback_days); `prior_atr_pct=atr/prior_close`; `ema_slope=(ema_prior-ema_lag3)/3`. No-lookahead: `prior["_sd"] < target` (410) / `< s` half-open (`daily_cache_batch.py:166`). Batch builder reads each symbol once over the full span and slices in-memory, sharing `_daily_cache_row_from_prior` for bit-parity (`daily_cache_batch.py:8-21,170`).

**Quote sampling (producer)** (`backfill.py:590-608`): `_sample_session_nbbo` = `merge_asof(direction="backward")` of the 390 regular-session minute boundaries against the NBBO tick stream → last quote at-or-before each minute (prevailing NBBO), preserving the tick's actual timestamp, dropping to 7 canonical columns. Boundaries 09:30…15:59 ET DST-aware (`_session_minute_boundaries_utc:582-587`). Fine path (`_sample_session_nbbo_fine:1073-1099`) keeps exchange/tape cols; trades stored RAW unsampled (`_coerce_trade_row:807-844`, `fetch_trades`).

**Dataset hashing/lineage** (`lineage.py`): `build_dataset_lineage:385` → lake regime hashes `{lake_manifest_hash, feed, adjustment, date_range, symbol_universe_hash, daily/minute/quote_partitions_hash (path,size lists), assets_snapshot_id, corp_actions_hash, lab_config_hash}`; `trades_partitions_hash` added only when config consumes tape (439). Synthetic regime hashes logical inputs only (446-452). `content_addressed_dataset_hash:567` hashes every parquet's pyarrow footer (schema+rowgroup+col stats, `_parquet_footer_hash:488`).

**DQ gating** (`data_quality.py`): `evaluate_startup_dq:1184` — `intended_realism` gates on all `required_failures`; `current_code_parity`/`fast_realism` gate ONLY on `_ADJUSTMENT_GATING_CHECK_NAMES` (adjustment_mismatch/split_adjustment_mismatch); `smoke_fixture` never gated; unknown mode → adjustment-only. Coverage fail fraction 1% (`COVERAGE_MISSING_FAIL_FRACTION:274`). Eligibility-scoped (Fix A/B/C) gates score only PIT-eligible (sym,session) pairs while keeping full-union telemetry.

## Knobs (config fields + defaults + threading)

- **`market_data.minute_bar_source`/`daily_bar_source`** (default `fixture`): `alpaca`/`shared` → lake regime (`lineage.uses_lake:55`). Else synthetic.
- **`market_data.feed`** (default `iex`): partition selector + SIP gate. `sip` against SIP-less lake → `sip_data_absent: fail` (data_quality.py:1404-1417). IEX capped research_only.
- **`market_data.shared_root`**: lake root; resolver chain explicit > `MARKET_DATA_ROOT` > in-repo default (`store.py:81-101`, `lineage.resolve_lake_root:65`).
- **`market_data.require_adjusted_daily_bars`** (default `False`): `adjustment_mismatch` against raw lake → fail (gates ALL non-smoke runs, `build_adjustment_check:825`).
- **`market_data.require_split_adjustment`** (default `False`): `split_adjustment_mismatch` (`:860`), adjustment-gating.
- **`market_data.max_quote_age_seconds`** (default 15): replay quote-age + quote coverage (`_build_multi_level_checks:1546`).
- **`daily_adjustment`** supplier arg (default `"raw"`): selects daily partition; must pass `split_adjusted` when config requires it (`suppliers.py:127,143-148`). **Default `raw` is a silent-correctness trap — see Leads.**
- **`simulation.mode`**: tiered gating; default `intended_realism` inside `_build_multi_level_checks` (1486).
- **`simulation.intraday_window_policy`** (default `scanner_start_to_scan`): window start (`suppliers.py:44,74-90`).
- **`simulation.quote_fallback_policy`** (`require_real` → `quotes_required_but_absent: fail`, `build_quote_check:935`).
- **`exits.max_hold_days`** (default 3): exit-path replay depth (`:1545`).
- **`execution.fill_model`/`exits.fill_model`** (`tape_replay` → wires trades supplier + trades hash component; `suppliers._config_uses_tape_replay:264`, `lineage._resolved_consumes_trades:273`).
- **`execution.halt_gate.enabled`** (default True): `halt_data_unavailable_when_required` (1592).
- **Env**: `MARKET_DATA_ROOT`, `QUOTE_FETCH_WORKERS`/`TRADE_FETCH_WORKERS`/`QUOTE_FINE_FETCH_WORKERS` (default 16), `TRADE_FLUSH_EVERY_SESSIONS` (default 0).
- **`daily_lookback_days`** (400), `default_max_age_seconds` (60), `window_minutes` (5), `max_partition_entries` (4096), `DQ_CHECK_INVARIANCE_VERSION` (2).

## Invariants & guards

- **Fail-loud**: `_coerce_lake_root` (`lineage.py:100-135`) rejects None/`Path('None')`/empty; `verify_lake_or_raise` raises `MissingLakePartitionError`; `StartupDataQualityError`/`DataQualityError` propagate past Optuna's broad except (`data_quality.py:44-70`); `make_trades_supplier_for_config` WARNs loudly when tape_replay requested but no trades partitions (`suppliers.py:299-317`); empty universe → `coverage_missing: fail` (`data_quality.py:651-660`); `write_ingestion_run` raises on missing required keys (`backfill.py:1580-1582`).
- **Silent fallbacks (flagged)**:
  1. `make_quote_supplier`/`store.quotes_at_or_before` return `None` on any missing/unreadable quote partition (`suppliers.py:213-214`, `store.py:376-381`) → lab falls to synthetic quote model; only `require_real`/realism gates catch it.
  2. `make_trades_supplier` returns EMPTY frame when no trades tree → tape_replay silently falls to legacy fill (`suppliers.py:253-255`).
  3. `build_dataset_lineage` swallows lake-resolution errors and **degrades a lake config to the synthetic regime** (`lineage.py:412-419`) — a real run with an unreadable lake gets a synthetic hash.
  4. `load_lake_manifest` returns `None` on corrupt manifest (`lineage.py:145-146`); `find_latest_audit`/`build_audit_checks` return `[]` on unreadable audit (`data_quality.py:293-294,377-379`).
  5. `_build_multi_level_checks` wraps every level in `except Exception` → `*_level_error: warn` (`data_quality.py:1509-1606`) — a crashing level never fails the run.
  6. `_quote_month` caches any read exception as "no quote" (`cached_suppliers.py:159-161`).
  7. `dq_check_invariance` unknown name → `trial_dependent` (conservative, documented, `data_quality.py:216`).
  8. `corporate_actions_for`/`store.corporate_actions` return empty on missing file silently (`loaders.py:178-179`, `store.py:424-425`).
- **Parity invariants**: cached suppliers must byte-match store boundaries (enforced by parity tests); batch daily cache must bit-match legacy (`daily_cache_batch.py:8-21`); minute-RAW invariant (`backfill.py:333`).

## Leads (suspected bugs / realism gaps / smells)

1. **`suppliers.minute_bars_supplier`/`store.minute_bars` reads minute bars RAW even when the run needs split adjustment** — minute prices are never split-adjusted (`backfill.py:333`, by design for live parity) but the $1–$20 price gate + intrabar stops run on RAW minute prices while daily features may be split_adjusted; mixed-adjustment within one decision (`suppliers.py:152-157`). Realism gap on in-window splits.
2. **`daily_adjustment="raw"` default across suppliers** (`suppliers.py:127`, `cached_suppliers.py:88`, `daily_cache_batch.py:114`, `build_daily_cache_from_lake:382`) — a caller that forgets to thread `daily_adjustment_for_config(cfg)` silently computes ATR/EMA/RVOL on raw daily bars; only the DQ adjustment gate (separately) catches it. Easy to bypass.
3. **`loaders.minute_bars_for` lake path window starts at UTC midnight of session date** (`loaders.py:107-109`) — `pd.Timestamp(session_date, tz="UTC")` not the policy start; inconsistent with `suppliers.intraday_window_start` (09:45 ET). Two minute-window conventions coexist.
4. **`loaders.quotes_for` lake path uses `store.quotes` with a 3-day lookback and no max_age** (`loaders.py:133-136,153-155`) — diverges from `quotes_at_or_before`'s 60 s freshness gate; could return a stale 3-day-old quote with no age rejection. Two quote conventions.
5. **`build_dataset_lineage` synthetic-regime fallback for a lake config that fails to resolve** (`lineage.py:415-419`) — produces a stable hash that does NOT reflect lake content; a corrupt/missing lake yields a "valid-looking" synthetic dataset_hash. Realism/forensics gap.
6. **Quote sampling = single prevailing-NBBO per minute** (`backfill.py:590-608`) — `merge_asof` backward keeps one quote/minute; intrabar spread widening / size at the actual fill instant is lost. Known per memory (FOK depth artifact); flag the 1/min resolution as an execution-realism cap.
7. **`store.minute_bars` dedups on timestamp `keep="last"`** (`store.py:273`) — if two partitions overlap a month boundary with differing values, silently keeps the later-concatenated row; no warning. Same in `cached_suppliers._range:223`.
8. **`build_coverage_check` gated minute leg probes only `scan_times[-1]`** (`data_quality.py:614-617`) — a symbol with bars early but none at session close is treated as flat-session-dropped; conversely the supplier window `[09:45, last]` returning non-empty marks the whole session "simulable" even if the actual entry scan minute had no bar. Coverage criterion is coarse.
9. **`_eligible_missing_sessions` (Fix C) and ingestion-level checks iterate every (sym,session) calling `daily_bars_supplier`** (`data_quality.py:329-339`, `:1491-1499`) — O(symbols×sessions) supplier calls inside DQ; on a large universe this is slow and re-reads parquet unless cached. Performance smell (acknowledged for late-session cap but not here).
10. **`audit_daily_bars` OHLC check ignores low-vs-high and high-vs-low boundaries** (`backfill.py:1525-1527`) — only checks `high < max(open,close)` / `low > min(open,close)`, not `high>=low` or vs the other extreme; weaker than `dq_levels.build_ingestion_checks` (`dq_levels.py:127-129`). Inconsistent OHLC validity definitions.
11. **`large_gap_flags` threshold 0.40 on RAW daily bars** (`backfill.py:1530-1531`) — flags suspected splits via overnight gap but daily bars may be split_adjusted (gaps removed) → misses splits when adjusted, over-flags when raw. Adjustment-dependent heuristic.
12. **`split_adjustment_applied` inferred from adjustment string when manifest omits flag** (`data_quality.py:879-882`) — `raw`→not-applied is correct, but `write_manifest_json` never writes `split_adjustment_applied` (`backfill.py:1589-1604`), so the flag is ALWAYS inferred; the manifest-flag path is dead until the writer adds it.
13. **`content_addressed_dataset_hash` footer uses pyarrow stats `min/max/distinct`** (`lineage.py:528-540`) which may be unpopulated/`None` for some writers → silently `stats_fp=""`, weakening content-addressing for those columns. Not validated.
14. **`_parquet_footer_hash` cache keyed by mtime+size only** (`lineage.py:501-503`) — a payload edit preserving mtime+size (e.g. in-place rewrite) reuses the stale footer hash. Theoretical hash collision/staleness.
15. **`quotes_at_or_before` re-reads + re-normalises the whole month parquet per call** (`store.py:373-388`) — no cache in the store path (only `cached_suppliers` caches); the uncached DQ/quote-coverage path is O(reads). Perf.
16. **`verify_lake._check_bars` hardcodes `vendor=alpaca`** in f-strings (`verify_lake.py:80-82,104,126,148,170`) — ignores any non-alpaca vendor; also uses raw path strings instead of `layout` builders (drift risk vs `layout.py`).
17. **`build_quote_check` reads `quote_fallback_policy` from `simulation` but SimulationConfig may store it elsewhere** (`data_quality.py:1390`) — falls back to `""` if absent → `require_real` gate silently never fires when the resolved key differs.
18. **`make_lake_suppliers` daily supplier ignores `with_microstructure`** and the microstructure vwap/trade_count columns are never surfaced to suppliers (`suppliers.py:159-164`) — the size-cap impact model (PB.2) can't see per-minute volume via the standard supplier path. Possible dead capability.
19. **`_normalise_bars` localises naive datetime64 as UTC unconditionally** (`store.py:149-150`) — if any writer ever stored ET-naive timestamps this silently mislabels tz. Relies on writer always UTC.
20. **`fetch_quotes`/`fetch_trades` resume scan reads `timestamp` column of every existing part to build covered-dates** (`backfill.py:687-695`) — O(files) reads each run; and a partial month already partly covered will skip the whole session if the date appears, possibly leaving gaps within the session. Resume granularity is session-date, not (session,symbol)-complete.
21. **`dq_levels.build_session_checks` stale-segment loop is a Python row loop** (`dq_levels.py:265-267`) — O(minutes) per session in pure Python; slow on full universe.
22. **`_session_minute_boundaries_utc` uses `inclusive="left"`** giving 09:30–15:59 (390) (`backfill.py:587`) — excludes the 16:00 close bar; if the consumer expects a 16:00 quote at session close it has none. Edge boundary.

## Test coverage hooks

- **suppliers/cached_suppliers**: `tests/parity/test_cached_minute_supplier_parity.py`, `test_cached_quote_supplier_parity.py`, `test_cached_supplier_lru_bound.py`, `test_session_minute_window_*_parity.py`, `tests/unit/test_real_supplier_helper.py`, `test_loaders_alpaca_source.py`.
- **daily_cache_batch**: `tests/parity/test_batch_daily_cache_matches_legacy_exact.py`, `_no_lookahead.py`, `_preserves_row_order.py`, `_truncated_ema_parity.py`, `_handles_missing_symbol_partition.py`; helper `tests/unit/data/test_daily_cache_row_helper_extracted.py`.
- **lineage**: `tests/unit/test_dataset_hash_content_addressed.py`, `integration/test_dataset_hash_changes_on_bar_payload_edit.py`, `_stable_across_runs.py`, `unit/data/test_coerce_lake_root.py`, `test_resolve_lake_root_chain.py`, `bowaka_common .../test_dataset_hash.py`, `test_dataset_manifest_schema.py`.
- **data_quality/dq_levels**: `tests/unit/test_dq_ingestion_level_checks.py`, `test_dq_feature_leakage_detected.py`, `test_dq_session_minute_count.py`, `unit/data/test_dq_coverage_eligibility_scoping_10c.py`, `test_dq_cache_invalidation.py`, `test_dq_check_invariance_classification.py`, `test_merge_dq_reports.py`, `unit/test_data_quality_checks_populated.py`; integration `test_dq_replay_level_missing_{exit_path,late_minute}.py`, `test_dq_halt_gate_unavailable_warning.py`, `test_intended_realism_fails_*`, `test_current_code_parity_fails_on_raw_lake*`, `test_nbbo_coverage_gate.py`, `test_quote_coverage_threshold.py`.
- **verify_lake**: `integration/test_verify_lake_cli.py`. **store/layout/backfill**: `bowaka_common/tests/unit/test_marketdata_*` (store_quotes, store_roundtrip, layout, backfill_unit/adjustment_kwarg/incremental_flush/quotes_backfill, runner, sip_path_layout_constants).
- **NO test (gaps)**: `loaders.minute_bars_for`/`quotes_for` lake-window conventions (Leads 3,4) — no test asserts the UTC-midnight vs policy-start or the 3-day-lookback quote behavior; `make_forward_minute_supplier` (no dedicated forward-window test found); `make_trades_supplier_for_config` loud-warning path (Lead in suppliers.py:299-317, no test grep hit); `build_dataset_lineage` synthetic fallback on unresolvable lake (Lead 5); `_sample_session_nbbo` 1/min prevailing-NBBO bias and the 16:00 exclusion (Lead 22) — `test_marketdata_quotes_backfill.py` exists but bias/boundary not asserted; `audit_daily_bars` OHLC/large_gap heuristics (Leads 10,11); `_parquet_footer_hash` mtime+size cache staleness (Lead 14); `with_microstructure` supplier surfacing (Lead 18).