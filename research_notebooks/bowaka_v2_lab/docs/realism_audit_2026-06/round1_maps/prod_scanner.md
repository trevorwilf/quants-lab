I have enough to identify the relevant test hooks. I have read all named files end to end plus the dependency modules and config. I'll now compose the report.

## Purpose & data flow (how this subsystem fits the backtest pipeline)

`prod_scanner` is the **live production candidate-generation layer** mirrored at `LAB\reference\source_strategy\scripts\`. Two daily/continuous jobs:

1. **`bowaka_universe_builder.py`** (nightly "garbage filter"): fetches the cached US-equity asset list + ~45 calendar days of daily bars per symbol via OpenAlgo `/api/v2/bars`, applies universe gates (tradable/status, exchange whitelist, OTC/instrument-class exclusions, ticker blocklist, price band, ADV band), computes prior-daily baselines (`bowaka_v2_features.compute_prior_daily_baselines`), ranks by ADV and caps to `cap_to_n_symbols` (600). Writes `universe_snapshot.json` + `daily_feature_cache.parquet` atomically (tmp + `os.replace`).
2. **`bowaka_intraday_scanner.py`** (long-running, 09:45→15:30 ET): every `scan_interval_seconds` (60) prefetches minute bars for every universe symbol, aggregates a FORMING session bar, computes forming features against the cached prior baselines and the time-of-day volume curve, applies v2 signal gates (`apply_v2_gates`), scores survivors (`compute_signal_strength`), ranks, caps to `max_candidates_per_scan` (25), and appends schema-v3 `candidate_signal` events to `candidate_events.jsonl`. The strategy process consumes those events. The scanner places **no orders**.
3. **`bowaka_v2_features.py`** is the **single source of truth** for all feature math; the scanner, universe builder, the LAB backtester, and the LAB `features/forming_bar.py` re-implementation must all agree (feature-parity contract). **`bowaka_v2_volume_curve.py`** builds the per-ADV-bucket cumulative-volume-fraction curve from prior sessions.

The scanner exposes `evaluate_one_scan()` as a pure injection point (`bars_supplier`) — the LAB backtester/replay drive it deterministically via `--replay-from` fixtures; this is the bridge into the backtest pipeline.

## Behavioral spec

**Universe builder** (`bowaka_universe_builder.py`):
- `classify_instrument` ordering: ticker_blocklist > name-keyword match > asset_class fallback; default `operating_equity` (`:91-135`). Only `operating_equity` is `eligible_for_bowaka_equity_bucket` (`:131-135`).
- Name match pads name with single spaces (`" "+name+" "`, `:86`) so whitespace-bracketed tokens like `" R "` hit word boundaries; tokens are NOT stripped (`:110-116`).
- `_universe_filter` (`:141-173`): drops not-tradable, status not in {active, active_tradable}, exchange not in whitelist (only if whitelist non-empty, `:163`), OTC exchanges, ticker blocklist.
- `_price_adv_drop_reason` (`:199-219`): drops `missing_prior_close`; price below/above band; ADV below min (or None) / above max.
- `compute_prior_daily_baselines` (`features:37-126`): ATR = mean of last `atr_n` true-range rows (needs `atr_n+1`); `prior_atr_pct = atr/prior_close`; `avg_volume_20d`/`avg_dollar_volume_20d` = mean of last `lookback` rows; EMA span=10 `adjust=False`; `ema_slope_prior = ema[-1]/ema[-(slope_lookback+1)] - 1` (`:107-109`).
- `_drop_today_forming_bar` (`:442-461`): drops bars whose ET date == today so live `end=now` daily fetch never folds today's bar into baselines (lookahead guard). Applied at the single serving point (`:601`).
- `build_and_write` cap (`:614-630`): ranks `cache_df` by `avg_dollar_volume_20d` DESC and keeps top N; if cache empty/missing column, falls back to taking the first N snapshot rows (alphabetical, `:628`).
- `write_outputs` (`:380-421`): parquet with jsonl.gz fallback on exception; empty cache writes a placeholder.
- Live suppliers (`:464-603`): `pre_fetch_sample_n` randomly samples eligible rows BEFORE daily fetch (seeded, `:543-550`); `_prefetch_all_daily` concurrent prefetch then dict lookups; `bars_supplier` falls back to single-symbol fetch on cache miss (`:596-597`).

**Volume curve** (`bowaka_v2_volume_curve.py`):
- `adv_bucket` (`:43-56`): None or `<edges[0]` → `<250k`; else `lo_hi` label; above last edge → `20M+`.
- `build_curve_from_minute_bars` (`:68-146`): ET minute-of-day = `(hour-9)*60+(minute-30)` clipped [0,389]; per-session cumulative volume / session total → fraction; then **mean** fraction by (adv_bucket, minute_of_day).
- `synthesize_default_curve` (`:149-182`): piecewise S-curve, identical across all buckets.

**Forming session + features** (`bowaka_v2_features.py`):
- `aggregate_forming_session_bar` (`:145-204`): open=first row open, high=max, low=min, last=last close, volume=**sum**, range=high-low. Does NOT filter by timestamp — caller must slice (`:154`).
- `compute_volume_curve_fraction` (`:210-270`): linear-interp at ET minute over the bucket's curve, clamp [0,1]; fallback to flat-rate curve when curve/bucket missing.
- `_fallback_curve_fraction` (`:287-300`): first 15 min carry `fallback_opening_15m_share` linearly; remainder distributed evenly over 375 min.
- `compute_forming_session_features` (`:306-383`): exact math —
  - `expected_volume_until_scan = avg_volume_20d * vcf`
  - `rvol_so_far = sess_vol / expected_volume_until_scan`
  - `projected_full_day_rvol = (sess_vol / vcf) / avg_volume_20d`
  - `range_expansion_so_far = sess_range / prior_atr_14d`
  - `close_location_so_far = (last - low)/(high - low)`
  - `ema_distance = last/ema_10_prior - 1`
  - `current_return_pct = last/prior_close - 1`; `gap_pct = sess_open/prior_close - 1`
- `apply_v2_gates` (`:389-480`): 13 gates; null threshold disables a gate; `_ge` fails closed on None, `_le` passes on None (`:502-509`), `_between` fails closed on None value (`:512-525`). `instrument_gate` passes when class is None or `operating_equity` (`:474-477`).
- `compute_signal_strength` (`:531-592`): bounded (default) = `1.0*min(rvol,cap) + 1.0*min(rng,cap) + 0.75*cl + 10*clip(ema_dist,0,cap) + 10*clip(ema_slope,0,cap) - 1.0*max(gap-gap_above,0)`. ema_distance/slope are clipped to **≥0** (negatives contribute 0).

**Scanner loop**:
- `evaluate_one_scan` (`:330-546`): skips `entered_symbols_today`; skips symbols with no baseline / no bars; computes vcf, forming bar, features, gates; on pass computes score; ranks DESC; caps to `max_candidates`; sets `candidate_rank` 1-based; updates `in_play_pool`; writes heartbeat.
- `_run_live` (`:637-860`): hot-reloads snapshot/cache/curve by mtime each tick (`:787-835`); `prefetch_scan_bars` fetches session_start→scan_ts; `bar_source` `alpaca_direct` with per-tick fallback to `openalgo`. Session window `scanner_start`(09:45)→`scanner_end`(15:30).
- `validate_startup_config` (`:55-73`): exit 5 if `feed != sip` and not `allow_non_sip_for_research_only`; else loud WARNING.
- `make_event_id` (`schemas:236-255`), schema v3 validation gating event append (`:301-316`).

## Knobs

| Field | Default | Effect / threaded |
|---|---|---|
| `data.feed` | `sip` | non-sip refused at startup unless research flag; sets `data_feed` on events (`scanner:251`) |
| `data.allow_non_sip_for_research_only` | false | bypasses SIP startup gate (`:61-67`) |
| `scanner.scan_interval_seconds` | 60 | loop cadence (`:659`) |
| `scanner.max_candidates_per_scan` | 25 | rank cap (`:367-369,520`) |
| `scanner.fetch_concurrency` | 40 | openalgo prefetch fan-out (`:663`) |
| `scanner.bar_source` | openalgo | `alpaca_direct` bypasses server; falls back to openalgo on cred/tick error (`:674-696,745-757`) |
| `scanner.debug_gate_dump` | true(cfg) | per-symbol gate JSONL dump (`:388-394`) |
| `scanner.signal_expiry_seconds` | 600 | event expiry (`:237`) |
| `session.scanner_start/end` | 09:45/15:30 | live window (`:711-717`) |
| `universe.cap_to_n_symbols` | 600 | ADV-ranked truncation (`:614`) |
| `universe.pre_fetch_sample_n` | null | random pre-sample before daily fetch (`:543`) |
| `universe.price_min/max`, `avg_dollar_volume_min/max` | 1/20, 250k/null | universe band (`:199-219`) |
| `signals.*_min/_max` | tuned (config §145-166) | per-gate thresholds; null disables gate |
| `score.bounded` + caps/weights | true / 5.0,2.5,0.40,0.25,0.75,0.25 | scoring (`features:565-580`) |
| `historical_features.{lookback,atr,ema,ema_slope_lookback}_days` | 20/14/10/3 | baseline windows (`:264-268`) |
| `volume_curve.bucket_edges` | [250k,500k,1M,5M,20M] | bucketing (`:354-359`) |
| `volume_curve.fallback_opening_15m_share` | 0.08 | flat-curve fallback (`:360-364`) |
| `live_fetch.daily_bars_lookback_calendar_days` | 45 | daily fetch span (`:482`) |

## Invariants & guards

- **Fail-loud**: missing universe_snapshot / daily_feature_cache → `ConfigError`, exit 5 (`scanner:79-105`); missing `OPENALGO_API_KEY` → `SystemExit(2)` (`builder:476-481`); SIP startup gate (`:55-67`); `build_universe` requires both suppliers or `RuntimeError` (`builder:257-261`).
- **Fail-closed**: `_ge`/`_between` treat None as fail; `compute_forming_session_features` returns None when inputs missing; gate eval fails the symbol.
- **Causality guards**: `_drop_today_forming_bar` (builder:442-461); curve/baseline causality is **documented but NOT enforced** (`features:218-224`, `:50-60`).
- **Silent fallbacks (flagged)**:
  - `load_daily_feature_cache` swallows parquet read exception and tries `.jsonl.gz`, else re-raises (`scanner:98-105`).
  - `load_volume_curve` returns None on missing file OR on any parquet exception (`:108-123`) → scanner silently runs on the flat fallback curve, distorting all RVOL.
  - `append_candidate_event` **silently drops** schema-invalid events (WARNING only) so a malformed candidate never emits (`:301-316`).
  - `_le` **passes on None value** (`features:502-509`) — a missing gap/rvol/range value silently bypasses the blow-off MAX caps.
  - `hydrate_entered_symbols_from_decisions` swallows OSError and skips malformed JSON lines (`:163-191`).
  - `load_or_init_scanner_state` returns empty state on any JSON parse error (`:140-151`).
  - `build_and_write` cap with empty cache silently falls back to alphabetical first-N instead of ADV-ranked (`builder:628`).
  - `bars_supplier` per-symbol fetch failure in builder → symbol dropped `bars_fetch_error` (not fatal, `:291-296`).
  - Volume-curve `write_curve` silently falls back to jsonl.gz on parquet failure (`vcurve:185-196`).
  - Scan-tick exceptions are caught + logged, loop continues (`scanner:854-855`).

## Leads

- **`scanner:846`** `bars_supplier=lambda sym, _ts: bars_by_sym.get(sym)` ignores `scan_ts` — prefetched bars span `session_start→scan_ts`, but `aggregate_forming_session_bar` does NOT timestamp-filter; if prefetch returns any bar > scan_ts (clock skew / provider over-return) it leaks into the forming bar (lookahead). No slicing in `evaluate_one_scan`.
- **`features:342-345`** `projected_full_day_rvol = (sess_vol/vcf)/avg_volume_20d` while `rvol_so_far = sess_vol/(avg_volume_20d*vcf)` — these are **algebraically identical**. Config comment (`config:147`) assumes they differ and sets `projected_full_day_rvol_min`(1.86) > `rvol_so_far_min`(0.50), making the projected floor the binding RVOL constraint; the two features are the same number → likely a spec/realism bug.
- **`features:107`** `ema_10_lag_3 = ema_series.iloc[-(ema_slope_lookback+1)]` → with default 3 this is offset −4 ("lag_3" but actually 3 bars back from the last = index −4). Name vs offset mismatch; verify against handoff.
- **`features:570-573`** `ema_distance`/`ema_slope` clipped to `[0, cap]` in the score, yet `ema_distance_min`/`ema_slope_min` gates accept **negative** thresholds (config `-0.095`, `-0.0165`). Negative-EMA candidates pass the gate but contribute 0 to score — silent scoring asymmetry.
- **`scanner:474-477` / config**: `projected_rvol_gate`, `max_rvol_gate`, `max_range_expansion_gate` exist in `apply_v2_gates` but `max_rvol_gate`/`max_range_expansion_gate`/`projected_rvol_gate` are **absent from `CANDIDATE_EVENT_REQUIRED_FIELDS`** (`schemas:78-87`) — schema validates only a subset of emitted gates; new gates aren't required so a producer dropping them passes validation.
- **`config:165` vs gates**: `current_return_pct_max` is configured but `apply_v2_gates` has **no `current_return` max gate** — dead config knob (never read).
- **`scanner:380-382`** `config_hash_v` hashes the full cfg incl. volatile/secret-adjacent fields and `default=str`; any cfg dict-order-independent change rotates the hash but the hash is truncated to 16 hex (collision surface, minor).
- **`features:265-268`** volume-curve interp clamps to endpoints: for `t_et_minute >= minutes[-1]` returns last fraction (often <1.0 if curve ends at minute 389 with fraction<1) — projected RVOL can be inflated near close if the prior-built curve never reaches 1.0.
- **`vcurve:135-139`** `df.apply(..., axis=1)` row-wise fraction is O(n) slow and uses `session_total>0` guard returning 0.0 — zero-volume sessions silently contribute 0-fraction rows that drag the **mean** curve down (`:142-144`).
- **`builder:165`** OTC check only fires when exchange string is literally in {OTC,OTCBB,OTCM}; OTC names with other exchange codes slip through if not on whitelist-only path.
- **`scanner:212`** `_session_date_et` contains a dead `if False else` ternary — confusing dead code; ET fallback branch (`timedelta(hours=-4)`) never executes.
- **`builder:124-129`** asset_class ETF fallback only catches `{etf, us_etf}`; ETN/leveraged via asset_class alone (no name keyword) are NOT caught here — relies entirely on name keywords.
- **Lake-dependency risk**: scanner needs live minute bars w/ correct ET timestamps + a prior-session volume curve + SIP-tape volume. LAB lake (Alpaca SIP, per MEMORY) may lack: halt/LULD data (no halt gate in scanner, but strategy needs it), accurate consolidated-tape minute **volume** (RVOL distortion on IEX explicitly warned, `config:13-20`), and `venue_code` per symbol (defaults `XNAS`, `scanner:257`, `builder:367-372`) — venue guessing can misroute non-NASDAQ.
- **`scanner:148-151`** new-session state reset keys on `session_date` only; if scanner restarts mid-session after a crash it reloads same-day state but `hydrate_entered_symbols_from_decisions` re-reads ALL decisions (no date-bounded file rotation) — O(file) each start.
- **`builder:543`** `pre_fetch_sample_n` random sample uses `random.Random(seed)` but samples AFTER in-memory universe+class filter only — does not re-apply price/ADV (those need bars), so the random subset's top-600 differs from the full set's top-600 (config comment at `:48-53` acknowledges; flagged as realism gap when set non-null).

## Test coverage hooks

LAB tests (the mirror itself ships no tests):
- `tests/integration/test_scanner_replay_fixture.py`, `test_scanner_parity_with_archive.py` — exercise `evaluate_one_scan` via `--replay-from`.
- `tests/integration/test_signal_appears_intraday.py`, `test_signal_appears_intraday.py` — forming-feature emission.
- `tests/integration/test_full_mode_gate_dump_unchanged.py` — `debug_gate_dump` output stability.
- `tests/parity/*` + `tests/integration/test_*parity*` + `tests/integration/test_feature_divergence_zero_on_identical_mock_partitions.py` — LAB `forming_bar.py`/`volume_curve.py` vs prod feature parity.
- `tests/integration/test_numba_scan_matrix_build_parity.py`, `test_scan_matrix_*_parity.py` — scan-matrix vs feature engine parity.
- `tests/integration/test_halt_gate_*`, `test_price_chase_gate_*`, `test_nbbo_coverage_gate.py` — strategy-side gates (NOT scanner gates).

**No direct test found for**: `apply_v2_gates` `_le`-passes-on-None blow-off-cap bypass; `compute_signal_strength` negative-EMA clip asymmetry; `projected_full_day_rvol` == `rvol_so_far` identity; `_drop_today_forming_bar` boundary; `build_and_write` empty-cache alphabetical fallback; `load_volume_curve` silent-None fallback; universe `classify_instrument` keyword/word-boundary edge cases; `ema_10_lag_3` offset. These are LAB-side gaps — verify before trusting.