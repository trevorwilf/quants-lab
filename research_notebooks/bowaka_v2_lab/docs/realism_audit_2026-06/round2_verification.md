# bowaka_v2_lab — Round 2 adversarial verification (2026-06-13)

> Finder (verify) -> Skeptic (refute) per lead from the roadmap section-9 shortlist.
> 17 leads, 34 read-only agents. Each finder reproduced against the real code/lake where
> possible; each skeptic independently re-read the current code and tried to refute.
> This is the evidence base for the roadmap verified-status updates.

## Verdict summary

| Lead | Finder verdict (sev) | Skeptic verdict | Final severity |
|------|----------------------|-----------------|----------------|
| **L1_pit_stamping** &mdash; Forming-bar inclusive <= scan_ts may leak the in-progress minute (lookahead) | real (critical) | CONFIRMED | **high** |
| **L2_t1_overfill** &mdash; T1 cent-walk + zero-size fill manufactures liquidity beyond displayed depth | real (high) | CONFIRMED (bounded) | **medium** |
| **L3_matrix_premarket** &mdash; Scan-matrix bakes 04:00 premarket bars vs the 09:45 policy window | real (high) | CONFIRMED | **high** |
| **L4_ir_coverage_bypass** &mdash; IR full-PIT-union coverage gate bypassed on a telemetry exception | real (high) | OVERSTATED (mechanism real, does not bite) | **low** |
| **L5_ema_slope** &mdash; Two ema_slope_prior definitions (ratio vs absolute/3) across builders | real (high) | CONFIRMED | **high** |
| **L6_lineage_synth_degrade** &mdash; Broken lake silently degraded to a synthetic dataset_hash | real (high) | OVERSTATED (mechanism real, does not bite) | **low** |
| **L7_same_symbol_cap** &mdash; caps>1 same-symbol daily count uses only OPEN lots (cap exceedable) | partially_real (low) | CONFIRMED (bounded) | **low** |
| **L8_nan_close_exit** &mdash; NaN minute close -> NaN exit price -> silent NaN PnL | real (high) | CONFIRMED (bounded) | **medium** |
| **L9_entry_date_today** &mdash; entry_date falls back to wall-clock date.today() in a backtest | not_real (low) | REFUTED (not real) | **none** |
| **L10_tape_manifest_flag** &mdash; derive_validation_config sets tape_replay but not the manifest flag suitability gates on | not_real (none) | REFUTED (not real) | **none** |
| **L11_default_exit_zero_slip** &mdash; Default exit _bracket_fill = exact bracket price, zero slippage | real (high) | CONFIRMED | **high** |
| **L12_t3_max_not_min** &mdash; T3 depth cap uses max(touch, cap_shares) so the cap cannot tighten below touch | real (high) | OVERSTATED (mechanism real, does not bite) | **low** |
| **L14_live_no_timestop_fade** &mdash; Live strategy has NO intraday time-stop and NO signal-fade (sim has both) | real (high) | CONFIRMED | **high** |
| **L15_live_ignores_riskcaps** &mdash; Live strategy ignores three risk caps the sim enforces | real (medium) | CONFIRMED | **medium** |
| **L16_wf_methodology** &mdash; No embargo/purge gap + step_months is dead (correlated folds) | real (high) | OVERSTATED (mechanism real, does not bite) | **low** |
| **L17_reconcile_vacuous** &mdash; Reconcile/parity comparators return vacuous PASS on empty sets | real (medium) | CONFIRMED | **low** |
| **L18_tape_condition_filter** &mdash; Tape-replay oracle/producer does not filter ineligible trade conditions | real (medium) | CONFIRMED | **low** |

---

## L1_pit_stamping &mdash; Forming-bar inclusive <= scan_ts may leak the in-progress minute (lookahead)

**Finder:** real (severity critical, confidence high) &middot; **Skeptic:** confirmed_real (final severity high)

**Evidence (finder):**

EMPIRICAL CONVENTION (real Alpaca lake parquet, same vendor=alpaca/feed=iex/timeframe=1m/adjustment=raw the v2 lake uses): read E:/.../bowaka_lab/db_tools/bowaka_data/parquet/bars/vendor=alpaca/feed=iex/timeframe=1m/adjustment=raw/session_date=2024-12-02/symbol=AAL.parquet → FIRST bar 09:30:00 ET, LAST bar 15:59:00 ET (297 rows; dtype datetime64[us,UTC]). Same for ACI/ACHR/ACMR (all first=09:30, last=15:59). This is START-of-interval (left-label) stamping: a bar stamped T covers [T, T+60s). Independently corroborated by round1_maps/alpaca_micro.md:94 ("Bars are right-/left-labeled by start of interval, UTC timestamps") and by the lab's OWN DQ code dq_levels.py:47-48 ("regular-session minute count (09:30-15:59 inclusive = 390 ...)").
INCLUSIVE CUTOFF (3 code paths, all <= scan_ts → the bar stamped AT scan_ts is consumed): scanner/session_minute_window_cache.py:194-196 (np.searchsorted(..., side="right")); scanner/scan_matrix.py:685 (full_bars[full_bars[ts_col] <= scan_ts_obj]); features/_numba_scan_features.py:284 (while bar_ts_ns[j] <= sc). The supplier path is also inclusive: data/suppliers.py:157 store.minute_bars(symbol, session_start, ts) and store.py:270 df[(timestamp>=start)&(timestamp<=end)].
CONSUMPTION: features/forming_bar.py:183 last_price = float(df[close_col].iloc[-1]) (close of the forming bar) feeds ema_distance (:355), current_return_pct (:359), close_location_so_far (:350), and is the per-scan decision price. numba sets last_close=b_close[j] for the bar at sc (:293).
GRID ALIGNMENT: sim/schedule.py:159-164 builds scan_times stepping scan_interval_seconds (default 60, config/models.py:194) from scanner_start (09:45 ET) — every scan_ts lands EXACTLY on a minute boundary, so a START-stamped bar is always stamped at scan_ts.
NO GUARD: round1_maps/scanner.md:20,76 already flagged "This is the PIT-critical assumption and it is nowhere asserted" / "No direct test of the PIT bar-stamping convention". grep confirms no convention assertion or partial-bar handling in src/.

**Reproduction (finder):**

(1) Read real lake parquet via C:/Python312 + pandas: AAL 2024-12-02 → "min ET: 2024-12-02 09:30:00-05:00  max ET: 2024-12-02 15:59:00-05:00" (297 rows, dtype datetime64[us, UTC]); ACI/ACHR/ACMR all first_ET=09:30 last_ET=15:59 → START-stamped CONFIRMED.
(2) Ran real bowaka_v2_lab.features.forming_bar.aggregate_forming_session_bar on a hand-built START-stamped frame (bars 09:58=100, 09:59=101, 10:00=150 ET; the 10:00 bar = a +49% move INSIDE [10:00,10:01)) with the EXACT scanner cutoff bars_through = full[full.timestamp <= scan_ts] at scan_ts=10:00:00. ACTUAL RESULT — inclusive (current code): bars included = ['09:58','09:59','10:00'], last_price = 150.0. Strictly-< (no-lookahead, only fully-closed bars): bars = ['09:58','09:59'], last_price = 101.0. LOOKAHEAD DELTA in last_price = 49.0 (+48.5%). The forming bar at scan_ts contributes a full future minute of price action to the decision.
(3) Ran real sim.schedule.scan_times_for_session('2024-12-02', default cfg) → 346 scans, first=09:45:00 ET, last=15:30:00 ET, all minute-aligned (sec==0)=True → confirms a START-stamped bar exists stamped at every scan_ts.
Could NOT inspect the container lake /opt/market_data_cache directly (Docker Desktop engine returned HTTP 500 on every API version 1.44–1.54), but the host-side legacy bowaka_lab Alpaca lake is the identical data source/convention and _coerce_bar_row (backfill.py:376-394) passes the Alpaca `t` field through unshifted for both IEX and SIP feeds, so the SIP v2 lake convention is identical.

**Blast radius (finder):** EVERY v2 backtest scan and therefore every objective/walk-forward/holdout/stress result, in all runtime modes. The forming-bar features (last_price, ema_distance, current_return_pct, close_location_so_far, session_high/low/range) carry up to one full minute of future price into each entry decision. Affects all three scan evaluators (legacy bars-supplier, scan_matrix compat, numba/vectorized) — they share the same inclusive cutoff and are byte-parity with each other, so the bias is uniform (no path escapes it). Magnitude per scan = the realized OHLC move of the [scan_ts, scan_ts+60s) minute on the candidate names (momentum/breakout screen → these are exactly the high-velocity minutes, so the leak is biased toward inflated entry signals). This is a genuine lookahead vs reality: in LIVE at wall-clock scan_ts the feed only has the PARTIAL in-progress minute (close = last trade so far), whereas the backtest reads the COMPLETED minute bar (close = price at scan_ts+60s). Optimistically inflates close_location/ema_distance/return-based gates and scores → over-optimistic backtested edge.

**Fix sketch (finder):** Use a strictly-exclusive upper bound so only fully-CLOSED bars are visible at scan_ts: change side="right"→"left" (cache:196), <=→< (scan_matrix:685, _numba:284), and pass end=scan_ts - 1ns / a strict bound in the supplier (suppliers.py:157 / store.minute_bars). Equivalently, since bars are START-stamped, only admit bars with timestamp <= scan_ts - 60s (the last bar that has fully closed). Then add a DQ/preflight assertion that pins the lake minute-bar convention (regular session first=09:30 / last=15:59) and a regression test on the cutoff. Note: changing the cutoff is a parity-breaking change to every golden/fixture — must be done as an explicit, versioned correctness fix with fixture regen, not a silent edit.

**Skeptic reasoning:**

Independently verified every load-bearing claim against current code and the real lake; tried hard to find a guard and found NONE. (1) Inclusive cutoffs confirmed verbatim: session_minute_window_cache.py:196 (np.searchsorted side="right"), scan_matrix.py:685 (full_bars[ts_col] <= scan_ts_obj), _numba_scan_features.py:284 (while bar_ts_ns[j] <= sc), and the supplier/store path store.py:270 (df[(timestamp>=start)&(timestamp<=end)] inclusive) via suppliers.py:157. (2) EMPIRICAL convention from the real Alpaca lake (same vendor=alpaca/feed=iex/timeframe=1m/adjustment=raw the v2 lake uses): read bowaka_lab/.../session_date=2024-12-02/symbol=AAL.parquet -> FIRST 09:30:00 ET, LAST 15:59:00 ET (297 rows, datetime64[us,UTC]); ABCL/ABEV/ACAD/ACDC all LAST=15:59 (never 16:00). This is START-of-interval (left-label) stamping: bar stamped T covers [T,T+60s). Corroborated by _coerce_bar_row (backfill.py:376-402) passing Alpaca `t` through unshifted, and round1 maps (scanner.md:"PIT-critical assumption nowhere asserted"; alpaca_micro.md:"Bars are right-/left-labeled by start of interval"). (3) REPRODUCED with real code: ran bowaka_v2_lab.features.forming_bar.aggregate_forming_session_bar on a START-stamped frame (10:00 bar = +49% inside [10:00,10:01)) with the exact scan_matrix cutoff at scan_ts=10:00 -> INCLUSIVE last_price=150.0, session_high=151.0 vs STRICT-< last_price=101.0 -> lookahead delta +48.5%. (4) GUARD-HUNT, the decisive part: ran the REAL SessionMinuteWindowCache.bars_until with the PRODUCTION default max_bar_age_seconds=90 -> the bar stamped exactly at scan_ts IS returned (close=150); max_bar_age only trims the LOWER bound (lo_ns, side="left", line 203) so it is NOT a guard. The staleness gate scan_loop.py:388 computes age=(scan_ts-last_bar_ts)=0 for that bar, 0>90 is False -> not stale -> consumed; test_stale_threshold_is_exclusive_boundary (test_stale_bar_rejected.py:92-110) asserts this age-at-boundary-is-fresh behavior is INTENDED, so it is the opposite of a guard. (5) Scan grid: sim.schedule.scan_times_for_session('2024-12-02') -> 346 scans, first 09:45:00, last 15:30:00, ALL minute-aligned (sec==0) -> a start-stamped bar exists at every scan_ts. (6) No convention assertion, no exclusive-cutoff, no no-lookahead test anywhere in src/ or tests/. CONSUMPTION confirmed end-to-end: scan_loop.py:357 bars=bars_supplier(symbol,scan_ts) -> :404 sess=aggregate_forming_session_bar(bars) -> :414 apply_v2_gates(...,price=sess.get("last_price")) and feats feed gates+score+candidate event. ONE TEMPERING NUANCE I verified and the finder slightly overweighted: the entry FILL price is NOT the forming-bar lookahead close — fills.py:214 uses fwd.iloc[0] (forward bar) and simulate_market_fill prices at quote.ask, so the leak is a SELECTION/GATE/SCORE bias (the scanner ranks/admits candidates using a close that already encodes the next 60s), not a direct free-lunch entry price. That refines the magnitude but does not refute: on a momentum/breakout screen this systematically over-selects exactly the high-velocity minutes -> inflated backtested edge across every objective/walk-forward/holdout/stress result in all three byte-parity scan evaluators. Could not inspect the container lake directly (Docker Desktop returned HTTP 500 on every API version, same as the finder), but the host legacy lake is the identical source/convention and the ingest applies no shift, so the SIP v2 lake convention is identical.

---

## L2_t1_overfill &mdash; T1 cent-walk + zero-size fill manufactures liquidity beyond displayed depth

**Finder:** real (severity high, confidence high) &middot; **Skeptic:** context_dependent (final severity medium)

**Evidence (finder):**

fills.py:_t1_fill (774-864). The cent-walk loop re-consumes the FULL displayed size at EVERY penny level:
  fills.py:818  `for _ in range(100):` (loop bound = 100 levels)
  fills.py:825  `take = min(remainder, int(size_at_touch * cap))`  <- uses size_at_touch (the ORIGINAL displayed size), NOT remaining displayed depth, so each penny level adds another full displayed quote.
  fills.py:814  initial level `[(usable_at_touch, touch)]` then walks `price = touch + cent` up to `limit_price` (fills.py:817,821,830).
Zero-displayed-size full fill:
  fills.py:804-808  `if usable_at_touch <= 0:` -> `filled = int(requested_qty); fill_price = limit_price; is_partial = False` (entire requested qty manufactured at limit).
Cap at base is 1.0 (no haircut): fills.py:283-293 `_resolve_fill_rate_cap`; stress_fill_rate_cap('base')==1.0 (verified in repro).
Callsite has NO size cap: strategy_consumer.py:477 `qty = size_quantity(target_notional, quote.ask)` (notional/price only), passed verbatim as strategy_consumer.py:705 `requested_qty=qty` into simulate_marketable_limit_fill. limit_price is set to ask*(1+offset) at fills.py:1008 with default offset 0.005 (0.5%), and the public dispatcher calls _t1_fill unguarded at fills.py:1097-1105. The T2 minute-volume cap (fills.py:1109-1134) only engages for T2/T4 tiers (needs minute_bars); plain T1 historical-quote runs have no post-walk size cap.

**Reproduction (finder):**

Ran the REAL functions via `PYTHONPATH=...src C:/Python312/python.exe -c` (no repo writes).
S1 (small displayed depth) _t1_fill side=buy req=5000, ask=100.00 ask_size=100, cost_stress=base (cap 1.0):
  limit=100.05 -> filled_qty=600  (6x displayed) part_frac=6.0 is_partial=True
  limit=100.50 -> filled_qty=5000 (50x displayed) part_frac=50.0 is_partial=False
  limit=101.00 -> filled_qty=5000 part_frac=50.0
S2 (zero displayed depth) _t1_fill side=buy req=5000, ask_size=0, limit=100.50 -> filled_qty=5000 avg_px=100.5 is_partial=False (ENTIRE qty manufactured at the limit price).
End-to-end PUBLIC dispatcher simulate_marketable_limit_fill(side=buy, req=5000, ask=100 ask_size=100, default 0.5% offset, minute_bars=None, mode=current_code_parity) -> tier=T1_TOP_OF_BOOK, filled_qty=5000, avg_px=100.245, part_frac=50.0, is_partial=False — i.e. 50x displayed depth filled with no caller-side cap.
Loop-bound demonstration: ask_size=1, req=1,000,000, limit=200 -> filled_qty=101 part_frac=101.0 (1 at touch + 100 penny levels, each re-consuming the full 1-share displayed size). The range(100) bound caps a single quote at displayed*(1+100) shares but lets each penny level fabricate another full displayed quote.

**Blast radius (finder):** Affects every T1_TOP_OF_BOOK marketable_limit (and limit-treated-as-marketable) entry fill — the default tier once historical quotes are ingested but no minute-volume/NBBO-depth cap is active (current_code_parity and any intended_realism run that lands on T1). Inflates entry sizing/fill rates far beyond real top-of-book liquidity (here 6x-50x, up to displayed*(1+100)), and zero-quote ticks fill the entire parent at the limit. This optimistically biases backtest PnL/Sharpe and the entire Optuna search/walk-forward/holdout chain that consumes these fills. T2/T4 (minute_bars present) partially clamps via the participation cap (fills.py:1109-1134); T3 depth-impact path (fills.py:1060-1084) is unaffected since it does not use the walk. Tape-replay (_tape_replay_fill) and market-order paths also bypass _t1_fill.

**Fix sketch (finder):** Cap cumulative T1 fill at the displayed touch size (do not re-add full size_at_touch each penny level): change fills.py:825 so each walked level draws from remaining displayed depth (or fab a real per-level depth proxy), and at fills.py:804-808 reject/no-fill (or fill 0) instead of filling the full requested qty when displayed size is 0. Alternatively always route T1 through a participation/volume cap rather than fabricating per-cent depth.

**Skeptic reasoning:**

The code defect is REAL and reproduces exactly; the first analyst's mechanism is correct, but their severity ("high") and blast-radius ("default tier once quotes are ingested") OVERSTATE how broadly it bites, because the T1 walk is reachable only on one mode (current_code_parity) and is a documented, test-locked parity wart with an honest replacement (T3) wired for the realism-grade modes.

CODE CONFIRMED (independently read current code):
- fills.py:825 `take = min(remainder, int(size_at_touch * cap))` re-consumes the FULL original displayed size at every penny level; fills.py:818 `for _ in range(100)` caps the walk at displayed*(1+100). fills.py:804-808: zero displayed size fills the ENTIRE requested_qty at limit_price (is_partial=False). cap at base==1.0 (fills.py:110-114, 283-293).
- Reproduced via the REAL functions (PYTHONPATH set, python -c, no repo writes): _t1_fill side=buy ask=100.00 ask_size=100 req=5000 -> limit=100.05 filled 600 (6x); limit=100.50 filled 5000 (50x, not partial); ask_size=0 req=5000 -> filled 5000 @100.5 not partial; ask_size=1 req=1e6 -> filled 101 (1 touch + 100 levels). Public dispatcher simulate_marketable_limit_fill (current_code_parity, default 0.5% offset, minute_bars=None) -> tier=T1_TOP_OF_BOOK filled 5000 (50x). All match the first analyst's numbers.

WHERE THE FIRST ANALYST WAS RIGHT BUT INCOMPLETE — the T2 cap is NOT a guard: I reproduced that even on T2 (minute_bars WITH volume, the real lake path) the overfill survives when minute volume is ample: ask_size=100 req=5000 with 100k sh/min (mdv ~$10M, cap=$1M) -> filled 5000 (50x displayed, not partial). The participation cap (fills.py:1109-1139) caps on 10% of MINUTE DOLLAR VOLUME, not on displayed top-of-book depth, so it only bites for orders > ~10% mdv. liquidity_proxy_shares is computed (strategy_consumer.py:600-606) and passed in, but _t1_fill (fills.py:774-864) IGNORES it — it is used only by _t0_fill (903-905) and simulate_market_fill (487-518). So no caller-side size cap neutralizes T1.

THE GUARDS THAT NARROW IT (what the first analyst understated):
1) Mode gating — strategy_consumer.py:639-643 sets has_nbbo_depth=True for BOTH intended_realism (with a historical quote) AND fast_realism (always), routing those to _t3_depth_impact_fill (fills.py:1060-1084), which does NOT walk/fabricate depth. _t1_fill is reachable ONLY when has_nbbo_depth=False, i.e. mode in {current_code_parity, smoke_fixture}.
2) Quote-source gating — detect_execution_tier (fills.py:88-97) returns T0 unless quote.source==SOURCE_HISTORICAL. current_code_parity's fallback is zero_spread (config/models.py:34) -> synthetic quote source + ask_size=0 (quote_model.py:130-145) -> tier T0 -> _t0_fill (which DOES honor liquidity_proxy_shares). So _t1_fill bites only when a REAL historical quote is returned. (Quote producer exists — bowaka_common/data/quotes.py, quote_loader.py — and per project memory a SIP quote backfill was run, so historical quotes do reach current_code_parity runs.)
3) It is DELIBERATELY locked in: tests/integration/test_marketable_limit_t1_partial_fill_when_qty_exceeds_ask_size.py:29-47 asserts filled_qty==1000 for a 1000-share order vs ask_size=200 (the walk). config/models.py:70-71 documents current_code_parity as "live code as written (warts and all)", and the fast_realism comment (models.py:42-50) explicitly states the design routes ask_size=0 to the T3 minute-volume participation cap precisely BECAUSE T1 fabricates depth — i.e. maintainers already recognize this and built the honest path.

NET: confirmed_real defect, reproduces 6x-50x (up to displayed*101) and full-fill on zero displayed size; bites real runs only on the current_code_parity path with real historical quotes (a legitimate, used parity/timing path, and T2 does NOT save it). It does NOT bite intended_realism / fast_realism (T3) or the synthetic-fallback majority (T0). Severity medium not high: it is a known, test-pinned parity wart with an honest replacement already wired for the realism-grade modes, so it inflates only current_code_parity PnL/fill-rate, not the promotion-gated realism runs.

---

## L3_matrix_premarket &mdash; Scan-matrix bakes 04:00 premarket bars vs the 09:45 policy window

**Finder:** real (severity high, confidence high) &middot; **Skeptic:** confirmed_real (final severity high)

**Evidence (finder):**

scan_matrix.py:604-611 hardcodes the matrix bar window to 04:00 ET (`_dt.time(4, 0)`) through 16:00 ET, fetched from the RAW store (`store = MarketDataStore(lake_root)` at :527) with NO reference to intraday_window_policy. Per-scan pandas filter at :685 is `bars_through = full_bars[full_bars[ts_col] <= scan_ts_obj]` — upper bound only, no policy lower bound; aggregate_forming_session_bar (forming_bar.py:160-211) aggregates whatever frame it gets (open=iloc[0], high=max, low=min, vol=sum), so it bakes the 04:00 premarket bars. The numba build path _numba_scan_features.py:282-295 cumulates `while j < n_bars and bar_ts_ns[j] <= sc` starting from j=0 (the first/04:00 bar) into first_open/cum_high/cum_low/cum_vol with no policy floor. The NON-matrix path DOES apply the policy floor: session_minute_window_cache.py:198 `policy_lo_ns = intraday_window_start(ts_utc, self.intraday_policy).value` and suppliers.py:152-157 minute_bars_supplier starts at `intraday_window_start(ts, policy)` (default scanner_start_to_scan = 09:45 ET per suppliers.py:37-44). The matrix builder only RECORDS intraday_window_policy in the manifest (scan_matrix.py:359, :383) but never APPLIES it. Runtime consumption: backtester.py:1413 calls evaluate_one_scan_compat WITHOUT debug_bars_supplier (defaults None), and event_loop.py:464-465 sets `scan_result = scan_result_override` so the matrix result fully replaces the legacy 09:45-bounded scan. The debug-assert at scan_matrix_runtime.py:367 (`if _assert_on and debug_bars_supplier is not None`) can never fire in production (supplier is None there); the parity test test_scan_matrix_runtime_debug_assert.py:18-19 deliberately uses a fixture supplier that "returns the SAME window the matrix builder consumed" (04:00), validating the matrix against itself, not against the 09:45 policy window.

**Reproduction (finder):**

Ran two python -c REPLs with PYTHONPATH set to the lab+common src, on a hand-built 4-bar frame (04:00 premarket spike: O10.00/H12.50/L9.90/C11.00/V50000; 09:30 O10.20/H10.40/L10.10/C10.30/V2000; 09:45 O10.30/H10.50/L10.25/C10.45/V3000; 09:50 O10.45/H10.60/L10.40/C10.55/V4000), scan_ts=09:50 ET. (1) aggregate_forming_session_bar over the matrix window (`ts<=scan_ts`, no lower bound) vs the policy window (`ts>=intraday_window_start(09:45)`): intraday_window_start returned 14:45 UTC = 09:45 ET. MATRIX = session_open 10.0, high 12.5, low 9.9, volume 59000.0, range 2.60; POLICY = session_open 10.3, high 10.6, low 10.25, volume 7000.0, range 0.35 — ALL five fields DIVERGE=True. (2) Drove the numba kernel build_session_columns_nb with the exact matrix prep from scan_matrix.py:636-646 (numba available=True): session_open=10.0, session_high=12.5, session_low=9.9, session_vol=59000.0 — byte-identical to the matrix pandas path and equally premarket-contaminated, confirming both build paths cumulate from 04:00.

**Blast radius (finder):** Affects every backtest/study run with optuna.acceleration.scan_matrix.enabled=true AND runtime_mode in {compatibility, vectorized} — i.e. the matrix perf path that real studies rely on (per project memory the matrix is THE ~47x lever that makes controller_compat tractable; notebook-10 wires it for production studies). When active, all forming-session features that depend on session_open/high/low/volume/range (gap_pct, current_return_pct via last/open, range_expansion_so_far, close_location_so_far, rvol_so_far, projected_full_day_rvol, ema_distance, session_high/low/volume) are computed over a window that includes 04:00-09:45 premarket bars, whereas the live/legacy scanner excludes them. This shifts which symbols pass the v2 gates and their signal_strength scores, so emitted candidate events, fills, trades, and FoldResults diverge from the non-matrix (and live) path. Premarket bars are typically thin/wide-range, so session_high/low/range/volume are systematically inflated, biasing range_expansion, rvol, gap, and close-location features. The default config has enabled=False (backtester.py:940-941), so the bug bites only when the operator opts into the perf path — but that is precisely the path validated studies use. The disabled/legacy path is unaffected.

**Fix sketch (finder):** In build_session_partition, set session_start_et from intraday_window_start(scan-date, resolve_intraday_window_policy(cfg)) instead of hardcoded 04:00 ET (or apply a policy lower-bound filter `full_bars[ts >= policy_lo]` before both the pandas slice at :685 and the numba prep at :636), so the matrix cumulation window matches the supplier's policy window; alternatively wire the production backtester call (backtester.py:1413) to pass the policy-bounded bars_supplier as debug_bars_supplier and fix the parity fixture to use the policy window so the assert actually guards the divergence.

**Skeptic reasoning:**

Independently verified every load-bearing claim against current code; tried hard to find a guard and found none. (1) The matrix builder hardcodes the bar window to 04:00 ET (scan_matrix.py:604-611 `_dt.time(4, 0)` .. `_dt.time(16, 0)`) fetched from the RAW MarketDataStore (scan_matrix.py:527); the per-scan slice is upper-bound-only (scan_matrix.py:685 `full_bars[ts_col] <= scan_ts_obj`); aggregate_forming_session_bar bakes whatever frame it gets (forming_bar.py:180-189: open=iloc[0], high=max, low=min, vol=sum). The numba build path cumulates from j=0 with no floor (_numba_scan_features.py:273-295). intraday_window_policy is ONLY recorded in the manifest (scan_matrix.py:359) and hashed (scan_matrix.py:383) — never APPLIED as a window bound. (2) The non-matrix/live path DOES apply the 09:45 floor: suppliers.py:152-157 minute_bars_supplier starts at intraday_window_start(ts, policy), default scanner_start_to_scan=09:45 (suppliers.py:37-44); session_minute_window_cache.py:198 same. (3) Runtime fully consumes the contaminated cells: scan_matrix_runtime.py:360-403 feeds the matrix-reconstructed sess/feats straight into apply_v2_gates + compute_signal_strength; the vectorized path is identical (scan_matrix_vectorized.py:440-441, never re-fetches). backtester.py:1413/1402 calls evaluate_one_scan_compat/_vectorized WITHOUT debug_bars_supplier (→None), and event_loop.py:464-465 sets scan_result = scan_result_override, so the matrix replaces the 09:45-bounded legacy scan. The debug-assert (scan_matrix_runtime.py:367) needs `debug_bars_supplier is not None`, impossible in production. (4) NO parity gate catches it: verify_scan_matrix (scan_matrix.py:1280-1426) only checks dataset-hash drift, cell self-consistency, static-int8 sentinels, and a vectorized-vs-scalar score spot check (_vectorized_cell_spot_check :1233-1277 — both sides fed from the SAME matrix cells); it never re-fetches the 09:45 legacy supplier. The matrix-vs-legacy parity tests are rigged to 04:00 on BOTH sides: the fixture sets simulation.intraday_window_policy='extended_hours_to_scan' (scan_matrix_parity.py:119) and a matched 04:00 supplier (scan_matrix_parity.py:61-94); test_full_fold_backtest_parity drives the legacy side with resolve_intraday_window_policy(cfg) which reads that 04:00 policy (test:61-64). So passing tests cannot detect the production-default divergence. (5) The bug bites real runs: production matrix configs (_local_container_matrix.yml, *.workstation.matrix.yml) set scan_matrix.enabled=true + runtime_mode=vectorized + mode=current_code_parity, and config/models.py:30-31 resolves current_code_parity's unset intraday_window_policy to 'scanner_start_to_scan' (09:45) — exactly the divergent case. The default non-matrix config has enabled=false, so the bug bites only matrix-enabled studies, which per project memory ARE the production perf path. REPRODUCED with the production-default policy on a hand-built 4-bar frame (04:00 premarket spike + 09:30/09:45/09:50): intraday_window_start('scanner_start_to_scan')=14:45 UTC=09:45 ET; MATRIX(04:00)=open10.0/high12.5/low9.9/vol59000/range2.60 vs LEGACY(09:45)=open10.3/high10.6/low10.25/vol7000/range0.35 — all five session fields DIVERGE=True. The first analyst's verdict, evidence, repro, and blast-radius are accurate.

---

## L4_ir_coverage_bypass &mdash; IR full-PIT-union coverage gate bypassed on a telemetry exception

**Finder:** real (severity high, confidence high) &middot; **Skeptic:** overstated (final severity low)

**Evidence (finder):**

walkforward_runner.py:1961-1998 (function run_walkforward_study, def at :1848). Init: ":1962  preflight_coverage_fraction: Optional[float] = None". Telemetry block: ":1968 try:" -> ":1972 pit_union = plan_pit_symbol_union(lake_root, feed=feed, plan=plan, cfg=cfg, include_holdout=True,)" -> ":1976 if pit_union_symbol_count > 0:" -> ":1977 preflight_coverage_fraction = (len(set(symbols) & pit_union) / pit_union_symbol_count)". Broad handler: ":1980 except Exception as exc:  # noqa: BLE001 — coverage telemetry must never crash the study" / ":1981 log.warning(\"PIT-union coverage telemetry failed (%s); coverage unknown\", exc)" — handler does NOT re-raise and leaves preflight_coverage_fraction=None. The IR refusal gate: ":1983 if (" / ":1984 sim_cfg.mode == \"intended_realism\"" / ":1985 and not research_waiver_capped_symbols" / ":1986 and preflight_coverage_fraction is not None" / ":1987 and preflight_coverage_fraction < 1.0 - 1e-9" / ":1990 raise PreflightError(...)". The `is not None` clause at :1986 short-circuits the entire gate to a no-op when telemetry raised. plan_pit_symbol_union (pit_universe.py:96-124) has NO internal try/except and calls fold_pit_symbol_union (:44-93) which does `MarketDataStore(lake_root)` (:88) and `build_pit_universe_for_sessions(...)` (:90) — real lake I/O / PIT-baseline computation that can raise; the raise propagates to the :1980 handler. (Contrast eligible_per_session_map at pit_universe.py:155-169 which DOES fail-closed-to-None deliberately, confirming plan_pit_symbol_union has no such guard.) No compensating gate exists: grep shows preflight_coverage_fraction is referenced ONLY in walkforward_runner.py; downstream uses (:2140-2141, :2543-2544, :2674-2675, :2793-2794, :2840-2841, :2970) merely RECORD the value into artifacts/metadata. assert_intended_realism_data_prerequisites (:238-283) gates on require_adjusted_daily_bars + DQ required_failures + quote coverage only — NOT on symbol-union coverage, and its docstring (:258-262) states a None measurement does NOT fail the gate.

**Reproduction (finder):**

Ran the exact control-flow lines (1961-1998) in a python -c REPL with hand-built inputs (sim_cfg.mode='intended_realism', research_waiver_capped_symbols=False, symbols=100-element capped probe) and a plan_pit_symbol_union stub that raises RuntimeError('lake parquet read error / asset-master unavailable'). ACTUAL output: "WARNING:repro:PIT-union coverage telemetry failed (lake parquet read error / asset-master unavailable); coverage unknown" / "preflight_coverage_fraction = None" / "gate_fired (study refused?) = False" / "RESULT: study proceeds despite IR coverage being UNKNOWN". The raise is swallowed, preflight_coverage_fraction stays None, the `is not None` clause makes the gate evaluate False, no PreflightError is raised — the study proceeds. This is fail-OPEN, not fail-closed. (Did not exercise the real lake to force a natural raise — the container lake is read-only and a study launch is prohibited — but the propagation path from plan_pit_symbol_union/MarketDataStore is established by reading and the gate logic is reproduced byte-for-byte.)

**Blast radius (finder):** intended_realism Optuna studies only (gate guarded by sim_cfg.mode=="intended_realism"). current_code_parity / fast_realism / smoke / explicit research_waiver_capped_symbols runs are unaffected (they intentionally skip this gate). When triggered, the audit-2026-05-23 §6.6 full-PIT-union coverage invariant — the guarantee that an IR study probes the ENTIRE per-fold PIT eligible-symbol union rather than a capped sample — is silently waived. The study runs to completion (multi-hour) against a capped/unknown-coverage universe while metadata records preflight_coverage_fraction=null, and the resulting "intended_realism" finalists carry a selection-bias / coverage caveat that the gate was designed to prevent. Trigger requires the PIT-union telemetry to raise (lake read error, asset-master schema/access fault, PIT-baseline computation failure) — not the default happy path, so it is a latent escape hatch rather than an always-on bug.

**Fix sketch (finder):** Fail closed on unknown coverage under intended_realism: when sim_cfg.mode=="intended_realism" and not research_waiver_capped_symbols, treat preflight_coverage_fraction is None (telemetry raised) as a refusal too — i.e., raise PreflightError unless coverage was successfully measured at >= 1.0 (or the waiver is set). Equivalently, change the :1986 clause from `preflight_coverage_fraction is not None and < 1.0` to "fraction is None OR fraction < 1.0", and/or remove the broad swallow at :1980 for the IR path so the telemetry exception propagates.

**Skeptic reasoning:**

The MECHANISM is real and reproduced: at walkforward_runner.py:1968-1981 the broad `except Exception` (:1980) swallows a telemetry raise from plan_pit_symbol_union and leaves preflight_coverage_fraction=None; the L4 gate at :1983-1998 only fires when `preflight_coverage_fraction is not None` (:1986), so a raise makes it a no-op. I reproduced this exactly with the real preflight.PreflightError: telemetry-raises -> preflight_coverage_fraction=None -> L4 gate fired=False (study not refused by L4). So the analyst's control-flow read is correct.

But the analyst's central claim — "No compensating gate exists ... the study runs to completion against a capped/unknown-coverage universe" — is REFUTED by the current code. plan_pit_symbol_union (pit_universe.py:96-124 -> fold_pit_symbol_union :69-93) can ONLY raise via `MarketDataStore(lake_root)` (:88) or `build_pit_universe_for_sessions(...)` (:90). TWO independent downstream gates re-exercise that exact surface and fail closed under intended_realism BEFORE study.create() (walkforward_runner.py:2294):

(1) The cheap study-start preflight: the probe block (:2007-2051) leaves dq_report/quote_cov_pct=None on its own broad except (:2051); run_preflight (:2071) then fails closed because _check_data_quality (preflight.py:165-176) and _check_quote_coverage (:269-287) both return status="fail" when the value is None AND sim_mode=="intended_realism". Reproduced with the real run_preflight: dq_report=None,quote=None,IR -> passed=False (data_quality:fail, quote_coverage:fail). This catches the common whole-lake-fault case where the fold-0 probe also fails.

(2) run_full_fold_preflight (walkforward_runner.py:2250-2273; preflight.py:865-989) runs UNCONDITIONALLY for intended_realism (no config opt-out; grep found none) over EVERY validation fold + holdout (:2253-2266) — the SAME scope L4 telemetry covers. _probe_fold (preflight.py:823-846) independently re-runs build_pit_universe_for_sessions over each fold's sessions and sets fold_passed=False with a `pit_universe_error` check (:839-846) on ANY PIT-build exception; run_full_fold_preflight then raises PreflightError (:982-988, raise_on_fail defaults True :877). I reproduced the L4-specific escape the analyst implied — a localized later-fold/holdout fault that lets the fold-0 cheap probe SUCCEED (forced clean dq_report + 99% quote) but breaks the PIT build: _probe_fold returned passed=False via fold:holdout_...:pit_universe_error -> study refused. The research_waiver_capped_symbols waiver (:1985) disables only the L4 coverage gate, NOT the full-fold preflight, so the non-empty PIT gate still runs.

Because any exception that trips L4 telemetry (MarketDataStore ctor or build_pit_universe_for_sessions) is the SAME call _probe_fold wraps in its own per-fold fail-closed try/except over the identical fold+holdout scope, the §6.6 full-PIT-union invariant is not actually escapable. The study still fails closed a few lines later; the only real residual is cosmetic: the L4 path logs "coverage unknown" and records preflight_coverage_fraction=null instead of emitting the L4-specific full-union refusal message. A one-line hardening (treat None as refusal under IR, or narrow the swallow) is reasonable defense-in-depth, but the analyst's "high" severity and "runs to completion" blast radius do not hold against the current code.

---

## L5_ema_slope &mdash; Two ema_slope_prior definitions (ratio vs absolute/3) across builders

**Finder:** real (severity high, confidence high) &middot; **Skeptic:** confirmed_real (final severity high)

**Evidence (finder):**

Three slope definitions confirmed in current code:
- suppliers.py:367 `_daily_cache_row_from_prior`: `"ema_slope_prior": (ema_prior - ema_lag3) / 3.0` (absolute/3).
- forming_bar.py:123-126 `compute_prior_daily_baselines`: `ema_slope_prior = ema_10_prior / ema_10_lag_3 - 1.0` (ratio).
- LIVE contract bowaka_v2_features.py:108-111: `ema_slope_prior = ema_10_prior / ema_10_lag_3 - 1.0` (ratio).

The scanner cache that feeds the gate/score is built by `_daily_cache_row_from_prior` (the absolute/3 path), NOT `compute_prior_daily_baselines`:
- suppliers.build_daily_cache_from_lake calls `_daily_cache_row_from_prior` (suppliers.py:413).
- daily_cache_batch.build_daily_cache_for_sessions_from_lake calls `_daily_cache_row_from_prior` (daily_cache_batch.py:170).
- cache_by_sym is built from that daily_cache DataFrame: scan_context.py:78-81, scan_loop.py:216-219, scan_matrix.py:556-557 (`cache_by_sym = {row["symbol"]: row.to_dict() ...}`).
- daily_cache comes from those builders in the real Optuna walkforward path: fold_context.py:302 (build_daily_cache_from_lake) and :309 (batch); walkforward_runner.py:537,659; scan_matrix.py:552.
- Scanner reads `baselines.get("ema_slope_prior")` (scan_loop.py:335, scan_matrix_runtime.py:314, scan_matrix.py:1251, scan_matrix_vectorized.py:276) and passes it to apply_v2_gates ema_slope_gate (`_ge(ema_slope_prior, s.get("ema_slope_min"))`, forming_bar.py:445-446) and to compute_signal_strength es term (`es = _to_float(ema_slope_prior) or 0.0`, forming_bar.py:522; capped es_cap=0.25 at :532,536).

`compute_prior_daily_baselines` (ratio) is used only by the numba parity kernel (_numba_scan_features.py:216, also ratio), unit tests, and benchmark/fixture scripts — NOT in the production cache_by_sym path.

**Reproduction (finder):**

Ran existing functions in a python -c REPL with a hand-built deterministic uptrend (price0=100, +0.2%/day, n=60), identical DataFrame to all three:
- ema_10_prior=111.50957518329484 and ema_10_lag_3=110.84319040903124 IDENTICAL across all three (same EMA), so the divergence is purely the final formula.
- suppliers (abs/3)     = 0.22212825808786837
- forming_bar (ratio)   = 0.006011959524121702
- live contract (ratio) = 0.006011959524121702  (EXACTLY matches forming_bar, NOT suppliers)
- ratio supplier/forming = 36.95x.

Price-scaling proof (same +0.2%/day drift, different price levels): supplier abs/3 = 0.0222 / 0.2221 / 1.1106 for price0 = 10 / 100 / 500, while forming/live ratio stays invariant at 0.006012 — confirming abs/3 carries price-point units and scales with absolute price.

Gate-outcome FLIP (downtrend -1%/day, live default ema_slope_min=-0.05 per search_space.py:74): supplier abs/3 = -0.5908 -> ema_slope_gate FAILS (val>=thr is False, symbol rejected); live/forming ratio = -0.029701 -> ema_slope_gate PASSES (True, symbol accepted). The lab rejects a candidate the live strategy accepts.

**Blast radius (finder):** Every real backtest/Optuna run via fold_context/walkforward_runner/scan_matrix uses the suppliers (abs/3) cache, so EVERY ema_slope_gate decision and the es score term diverge from the live contract. Direction-dependent and price-magnitude-scaled: for up-tilted stocks the slope is inflated (es term near-saturates the 0.25 cap for any moderately-priced trending name; gate too lenient at positive thresholds), for down-tilted stocks the slope is over-negative (gate too strict, rejects names live would accept). Because abs/3 scales with absolute price, the gate/score behavior also varies with stock price level — a systematic, non-uniform bias across the universe. Affects candidate selection (which symbols emit signals) and ranking (signal strength), i.e. the core scanner output that drives the whole backtest. The numba scan-feature build path (default-off) and unit/fixture paths use the correct ratio, so they are inconsistent with the live cache — also a build-vs-scan parity hazard.

**Fix sketch (finder):** Change suppliers.py:367 `_daily_cache_row_from_prior` to the dimensionless ratio used by the live contract and forming_bar: `"ema_slope_prior": (ema_prior / ema_lag3 - 1.0) if ema_lag3 != 0.0 else None` (guard div-by-zero like forming_bar.py:124-125). This is the single source for both build_daily_cache_from_lake and build_daily_cache_for_sessions_from_lake, so one edit fixes both production cache paths; then re-verify daily-cache parity fixtures/golden values.

**Skeptic reasoning:**

Independently verified all three definitions and the data-flow trace; reproduced the divergence and gate flip. No guard/caller/default/test prevents it from biting a real run.

THREE DEFINITIONS (current code):
- suppliers.py:367 `_daily_cache_row_from_prior`: `"ema_slope_prior": (ema_prior - ema_lag3) / 3.0` (abs/3).
- forming_bar.py:123-126 `compute_prior_daily_baselines`: `ema_10_prior / ema_10_lag_3 - 1.0` (ratio).
- LIVE contract bowaka_v2_features.py:108-111: `ema_10_prior / ema_10_lag_3 - 1.0` (ratio, identical to forming_bar).

PRODUCTION CACHE PATH = abs/3 (verified, not trusted):
- fold_context.py:302 calls build_daily_cache_from_lake; :309 calls batch build_daily_cache_for_sessions_from_lake — these are the real Optuna/walkforward daily_cache builders.
- build_daily_cache_from_lake calls _daily_cache_row_from_prior (suppliers.py:413); batch calls it at daily_cache_batch.py:170. Both = abs/3.
- cache_by_sym is built directly from that daily_cache DataFrame: scan_context.py:78-81 and scan_loop.py:216-219 (`cache_by_sym[row["symbol"]] = row.to_dict()`).
- Scanner reads baselines.get("ema_slope_prior") (scan_loop.py:335, scan_matrix_runtime.py:314, scan_matrix.py:1251, scan_matrix_vectorized.py:276) → apply_v2_gates ema_slope_gate `_ge(ema_slope_prior, ema_slope_min)` (forming_bar.py:445-446, _ge at :478-483) and compute_signal_strength es term (forming_bar.py:522, capped es_cap=0.25 weight 10x at :532/536/542).
- compute_prior_daily_baselines (ratio) is NEVER called in the production scan path: callers are only numba fixture scripts, the numba kernel _numba_scan_features.py:216 (also ratio, default-OFF build-only per repo memory), and unit tests. So even the lab's own default-on path uses abs/3.

NO GUARD REFUTES: The only adjacent test (tests/unit/data/test_daily_cache_row_helper_extracted.py) asserts legacy==batch (both abs/3) and ema_slope_prior==0.0 only in the degenerate short-prior fallback (line 58) where ema_lag3==ema_prior so both formulas coincide. It never compares against the ratio/live contract. No daily-cache parity test catches abs/3-vs-ratio.

REPRODUCED (python -c, existing functions, deterministic input):
- Identical EMA across all three: ema_10_prior=111.50957518329484, ema_10_lag_3=110.84319040903124 → divergence is purely the final formula.
- +0.2%/day uptrend n=60: supplier abs/3 = 0.22212825808786837 vs forming ratio = 0.006011959524121702 vs live ratio = 0.006011959524121702 (live EXACTLY matches forming, NOT supplier; 36.948x).
- Gate FLIP (downtrend -1%/day, live default ema_slope_min=-0.05): lab abs/3 slope=-0.5907682542630184 → ema_slope_gate=False (reject); live/forming ratio=-0.029700555863180766 → ema_slope_gate=True (accept). Confirmed via apply_v2_gates directly.
- Price-scaling (same +0.2%/day drift): abs/3 = 0.0222/0.2221/1.1106 for price0=10/100/500 while ratio invariant at 0.006012 → abs/3 carries price-point units.
- es score term (uptrend): lab abs/3 es=0.2221 → +2.22 to score (10x weight, just under 0.25 cap); live ratio es=0.006012 → +0.060. Lab inflates the slope-score contribution ~37x.

CROSS-BOUNDARY HARM CONFIRMED: ema_slope_min is an Optuna-searched param (search_space.py:74, uniform -0.10..0.10, live default -0.05). The exported config bowaka_v2_actual_iex_current_code.yml:139 carries ema_slope_min=-0.016531812911964736, selected by the lab against abs/3 slopes; the live contract applies that same threshold against the ratio slope (bowaka_v2_features.py:457-459). The threshold is semantically incompatible between lab-tuning and live-application — direction-dependent and price-magnitude-scaled bias across the universe.

MINOR ANALYST OVERSTATEMENTS (do not change verdict): (1) they wrote the es term "near-saturates / saturates 0.25 → +2.5" for moderate uptrends; my +0.2%/day repro gives es=0.2221 (below the 0.25 cap, +2.22 not +2.5) — saturation needs a steeper or higher-priced name. (2) "ratio supplier/forming = 36.95x" matches my 36.948x. Otherwise evidence is accurate. Severity high stands: every real backtest/Optuna run uses the abs/3 cache, so every ema_slope_gate decision and es score term diverges from the live contract, biasing candidate selection and ranking — the core scanner output.

---

## L6_lineage_synth_degrade &mdash; Broken lake silently degraded to a synthetic dataset_hash

**Finder:** real (severity high, confidence high) &middot; **Skeptic:** overstated (final severity low)

**Evidence (finder):**

research_notebooks/bowaka_v2_lab/src/bowaka_v2_lab/data/lineage.py:408-419 (build_dataset_lineage):
408  if lake_backed:
409      try:
410          lake_root = resolve_lake_root(cfg)
411          lake_manifest = load_lake_manifest(lake_root)
412      except Exception:  # noqa: BLE001 — lake resolution must never crash a run
413          lake_root = None
414          lake_manifest = None
417-419  # fall back to the synthetic regime so the hash is stable ...
        if lake_root is None or not lake_root.is_dir():
            lake_backed = False
Synthetic branch (lineage.py:443-454) sets components={feed,date_range,symbol_universe_hash,lab_config_hash,synthetic:True}, provider="fixture", regime="synthetic".

No upstream guard: resolve_lake_root (lineage.py:65-68) -> resolve_market_data_root (bowaka_common/.../store.py:81-101) is documented "Never raises", uses create=False, and does NO existence check — it returns a non-existent Path with is_dir()==False. The _coerce_lake_root guard (lineage.py:100-135) that raises on None/empty/Path("None") is NOT wired into build_dataset_lineage (only into resolve_lake_root_with_dataset_lineage_fallback); and even when called directly it does not reject a non-existent real-looking path.

No downstream guard: build_data_quality_report (data_quality.py:1280-1283) — `if regime != "lake": return synthetic_data_quality_report(...)` — so a degraded lake run is treated as a legitimate synthetic run. synthetic_data_quality_report (data_quality.py:1106-1128) emits a single status="warn" check named "synthetic_data" with empty required_failures. evaluate_startup_dq (data_quality.py:1184-1217) returns None for it in EVERY mode including intended_realism (gating_failures empty). Backtester consumes this verbatim (backtester.py:751-810): dataset_hash and dataset_regime come straight from the degraded lineage; the only gate is evaluate_startup_dq, which passes.

**Reproduction (finder):**

Ran the REAL build_dataset_lineage via: PYTHONPATH="research_notebooks/bowaka_v2_lab/src:research_notebooks/bowaka_common/src" C:/Python312/python.exe -c "..."

(1) Non-existent lake, lake-backed cfg (minute_bar_source='alpaca', shared_root='Z:/this/lake/does/not/exist/12345'): build_dataset_lineage did NOT raise. Returned regime='synthetic', provider='fixture', lake_root='Z:\\this\\lake\\does\\not\\exist\\12345', dataset_hash=0c8107ee05a9008a549f378bc3c5e3db7f7d2570a18ae2702e44cb895addde3a, components keys=[date_range,feed,lab_config_hash,symbol_universe_hash,synthetic]. resolve_lake_root(cfg) returned the bad path with is_dir()=False and did NOT raise.

(2) A genuine synthetic config (minute/daily_bar_source='fixture') over the SAME logical inputs produced the IDENTICAL hash 0c8107ee05a9008a549f378bc3c5e3db7f7d2570a18ae2702e44cb895addde3a — i.e. an unreadable real-lake run is indistinguishable by dataset_hash from a fixture run.

(3) Forced a genuine OSError inside the try-block (simulating an unreadable mount, the documented 9p/NFS-mount-gone scenario): the except at lineage.py:412 swallowed it; result regime='synthetic', lake_root=None, same hash 0c8107ee... — confirming the swallow path, not just the not-is_dir path.

(4) evaluate_startup_dq(synthetic_data_quality_report(...)) returned None for intended_realism, current_code_parity, AND fast_realism (required_failures=[], adjustment_gating_failures=[], checks=[('synthetic_data','warn')]) — no mode fails the run closed.

**Blast radius (finder):** Affects any lake-backed run (current_code_parity / fast_realism / intended_realism) whose lake becomes unreadable or whose shared_root is misconfigured/non-existent. Two failure consequences: (a) Correctness/lineage integrity — the run silently executes with synthetic suppliers and stamps a synthetic-regime dataset_hash that collides exactly with a fixture run over the same logical inputs, so forensics cannot tell a real-data run from a fixture run by hash; cached fold artifacts / scan-matrix entries keyed on dataset_hash could be reused across genuinely-different data states. (b) The intended_realism gate that is supposed to fail-closed on missing data does NOT trigger, because the run is reclassified as synthetic before the lake DQ checks (coverage/quote/audit) ever run — the operator believes they ran research-grade data while the engine ran fixtures. The only surfaced signal is a single warn-level "synthetic_data" check and dataset_regime='synthetic' in the manifest; nothing escalates a LAKE-INTENDED config that silently fell back to synthetic.

**Fix sketch (finder):** Distinguish "operator chose synthetic" from "operator chose a lake that is unreadable": when uses_lake(cfg) is True but the lake resolves to a non-directory or the resolution raised, do NOT degrade to the synthetic regime silently — either raise (or return a distinct regime like "lake_unreadable" / set a hard required_failure) so evaluate_startup_dq fails the run closed in intended_realism (and ideally all non-smoke modes). At minimum, route the lake branch through _coerce_lake_root and add an is_dir() existence assertion for lake-backed configs, reserving the silent synthetic fallback for configs that did not request a lake (direct run_backtest with synthetic suppliers).

**Skeptic reasoning:**

The code-level mechanism the analyst describes is REAL and I reproduced it in isolation: build_dataset_lineage (lineage.py:408-419) swallows the lake-resolution exception and the `if lake_root is None or not lake_root.is_dir(): lake_backed = False` (line 418) degrades a uses_lake() config to regime=synthetic; resolve_lake_root->resolve_market_data_root(...,create=False) (store.py:81-101) never raises/existence-checks; _coerce_lake_root does NOT reject a real non-existent path (only None/Path('None')/empty). Direct repro: cfg with shared_root='Z:/this/lake/does/not/exist' -> regime='synthetic', provider='fixture', and dataset_hash IDENTICAL to a genuine minute_bar_source='fixture' config (collision reproduced). synthetic_data is in neither _REQUIRED_CHECK_NAMES nor _ADJUSTMENT_GATING_CHECK_NAMES (data_quality.py:88-100,265-270) so evaluate_startup_dq returns None for it in every mode.\n\nBUT the analyst tested build_dataset_lineage IN ISOLATION and overstated the practical bite. In EVERY real lake-backed caller a MarketDataStore/supplier is constructed BEFORE build_dataset_lineage runs: walkforward_runner.py:533 (`MarketDataStore(lake_root)`) and :2014 (`make_lake_suppliers`) precede the lineage call at :565/:2019; cli_runners.py:240 (`make_lake_suppliers`) precedes run_backtest at :274. MarketDataStore.__init__ calls resolve_market_data_root(root) with the DEFAULT create=True (store.py:197-198,99-100), which mkdir's the lake root. Reproduced: with shared_root pointing at a missing-but-creatable dir, build_dataset_lineage returns regime='synthetic' if called first, but regime='lake' once make_lake_suppliers/MarketDataStore is constructed first (the real ordering). So the env-misconfig-creatable-path scenario does NOT silently degrade in a real run. The documented 'unreadable mount' / non-creatable path scenario: the store ctor's mkdir RAISES (reproduced FileExistsError [WinError 183]) -> a LOUD upstream crash at supplier construction, not a silent synthetic degrade -- contradicting the analyst's claim that the OSError is swallowed at lineage.py:412 on the real path. The surviving real scenario (empty/created lake) stays regime='lake' and evaluate_startup_dq FAILS CLOSED under intended_realism: reproduced required_failures=['coverage_missing','coverage_missing_exit_path','halt_data_unavailable_when_required'] -> 'intended_realism run aborted: 3 required data-quality check(s) failed'. This directly refutes the analyst's central consequence (b) that the intended_realism fail-closed gate never triggers because the run is reclassified as synthetic. No real call site was found that reaches build_dataset_lineage for a lake config without first constructing a store (the only place the synthetic-degrade hash-collision could materialize). Tests (test_dataset_hash_stable.py:117-131) only assert the synthetic fallback for genuine minute_bar_source='fixture' configs; none asserts unreadable-lake->synthetic as desired, so this is untested latent fragility, not validated behavior.\n\nNet: a genuine defense-in-depth weakness in lineage.py (the swallow+synthetic fallback for a lake-INTENDED config is incorrect in principle and produces a fixture-colliding hash), but the create=True side-effect of store construction in every caller defeats the is_dir()==False branch, non-creatable mounts crash upstream loudly, and the surviving path is caught fail-closed by the intended_realism coverage gate. It does not bite a real run as the high-severity correctness/gate-bypass bug claimed.

---

## L7_same_symbol_cap &mdash; caps>1 same-symbol daily count uses only OPEN lots (cap exceedable)

**Finder:** partially_real (severity low, confidence high) &middot; **Skeptic:** context_dependent (final severity low)

**Evidence (finder):**

The buggy counting is exactly as the lead describes. strategy_consumer.py:397-406:
```
if same_symbol_per_day <= 1:
    already_entered_today = symbol in entered_today
else:
    session_date = portfolio_state.session_date if portfolio_state else None
    lots_today = sum(
        1
        for p in self._portfolio.positions_for_symbol(symbol)
        if p.entry_session == session_date
    )
    already_entered_today = lots_today >= same_symbol_per_day
```
portfolio.py:285-287 confirms positions_for_symbol returns ONLY open lots:
```
def positions_for_symbol(self, symbol: str) -> list[Position]:
    return [p for p in self.open_positions.values() if p.symbol == symbol]
```
Closed lots are popped from open_positions (portfolio.py:552 close_position_by_id, :572 close_position), so an intraday round-trip removes the lot from the count. A CORRECT monotonic counter exists and is maintained (portfolio.py:413-415 entries_per_symbol_today increments on add_position, never decremented on close) but the cap>1 path does NOT use it.
cap=1 path is safe: it uses entered_symbols_today, which is add()-only (portfolio.py:406) and never discarded on close (grep shows no .discard/.remove anywhere). config/models.py:238 confirms same_symbol_entries_per_day default = 1.
BLAST-RADIUS MASK: the scanner caps emissions FIRST with a monotonic emit counter. scan_loop.py:305 `if signal_emits_per_symbol.get(symbol, 0) >= same_symbol_day_cap > 0: ...continue`; incremented only on emit at scan_loop.py:528 `signal_emits_per_symbol[ev["symbol"]] = ...+ 1`, never decremented; reset per-session (backtester.py:1015). The consumer only ever sees scan_result.emitted (event_loop.py:475 `for ev in scan_result.emitted:` -> :491 consumer.consume(...)), so at most `cap` candidates per symbol/session reach the buggy gate.

**Reproduction (finder):**

Ran the EXACT consumer cap>1 expression against a real Portfolio (PYTHONPATH set; C:/Python312/python.exe -c). Scenario: cap=2, symbol AAA, three intraday open+close round-trips in one session.
ACTUAL OUTPUT:
  after entry1: lots_today=1 open_lots=1 entries_per_symbol_today={'AAA': 1}
  after close1: lots_today=0 open_lots=0 entries_per_symbol_today={'AAA': 1} entered_today=['AAA']
  before entry2: lots_today=0 reject(cap=2)=False
  before entry3: lots_today=0 reject(cap=2)=False   <-- 3rd entry should be BLOCKED at cap=2
  before entry4: lots_today=0 reject(cap=2)=False
  TOTAL entries taken this session (entries_per_symbol_today): 3   (cap was 2)
So the open-lot gate (lots_today >= cap) NEVER fires because lots_today resets to 0 on each intraday close, while the correct counter reads 3 > cap=2. Unit-level defect reproduced. I did NOT run a full backtest (constraint); the pipeline-level mask was established by reading the call chain, not executed end-to-end.

**Blast radius (finder):** Bites ONLY a config that sets same_symbol_entries_per_day > 1 (default is 1, where the separate entered_symbols_today set correctly blocks re-entry). Even with cap>1, the consumer-side gate is upstream-masked: the scanner's monotonic per-session emit cap (scan_loop.py:305/+528, and the identical scan_matrix_runtime.py:287/+481 and scan_matrix_vectorized.py:373/+508 paths) emits at most `cap` candidates per symbol/session, and the consumer only consumes scan_result.emitted. So in the integrated backtester the per-day same-symbol entry cap is in practice enforced correctly by the scanner regardless of intraday closes. The consumer gate is redundant/defensive and its bug does not change emitted/filled counts in the normal pipeline. Impact would surface only if the consumer were driven with candidates bypassing the scanner emit cap (e.g. an isolated unit/integration harness, or a future caller). No effect on default-config runs or any run today.

**Fix sketch (finder):** In strategy_consumer.py cap>1 branch, count from the monotonic per-session counter instead of open lots: `lots_today = int(portfolio_state.entries_per_symbol_today.get(symbol, 0))` (already maintained in portfolio.add_position, never decremented on close), matching how the scanner uses signal_emits_per_symbol. Low priority given the scanner already enforces the cap upstream and default cap=1.

**Skeptic reasoning:**

UNIT-LEVEL BUG CONFIRMED & REPRODUCED. The consumer cap>1 branch counts only OPEN lots: strategy_consumer.py:399-406 does `lots_today = sum(1 for p in self._portfolio.positions_for_symbol(symbol) if p.entry_session == session_date)`, and positions_for_symbol returns open-only (portfolio.py:285-287: `[p for p in self.open_positions.values() if p.symbol == symbol]`). close_position_by_id pops from open_positions (portfolio.py:552) and _record_close (portfolio.py:422+) never touches the counter, so an intraday round-trip drops the lot from the count. My repro (Portfolio + the exact gate expr, cap=2, 3 intraday open+close round-trips): OPEN-LOT-GATE reject stayed False on entries 2/3/4 -> 4 entries taken under cap=2; the monotonic counter (entries_per_symbol_today) correctly rejected at entry3. So the bug is real and the proposed fix counter works.

BUT IT DOES NOT BITE ANY REAL RUN — two independent masks:
(1) Default + every shipped config sets cap=1. models.py:238 `same_symbol_entries_per_day: int = 1`. The cap=1 path (strategy_consumer.py:397-398) uses entered_symbols_today, which is add-only (portfolio.py:406) and never discarded — correct. ALL configs set 1, including the live contract sources reference/actual_bowaka_v2_contract.yaml:133 and reference/source_strategy/scripts/bowaka_v2_config.yaml:140, plus every optuna/matrix/smoke config. The Optuna search space does NOT tune this param (no match under optuna/). Reaching the buggy branch requires hand-editing a config to >1, which nothing in-repo does.
(2) Even at cap>1, the scanner upstream-masks it. The consumer only consumes scan_result.emitted (event_loop.py:475; the only two prod consume() sites both go through run_one_scan at backtester.py:1108 and :1429). The scanner caps EMITS with a monotonic per-session counter signal_emits_per_symbol (gate scan_loop.py:305 `>= same_symbol_day_cap > 0`, inc :528, never decremented, reset only by the fresh per-session state dict at backtester.py:1015). entered_symbols_today is read-only in the scanner (scan_loop.py:194, never written). Identical caps in scan_matrix_runtime.py:287 and scan_matrix_vectorized.py:373. Since entries <= emits <= cap, the consumer's open-lot gate is fully redundant; its bug cannot raise entry counts in the integrated pipeline.

CORRECTION to finder: they called entries_per_symbol_today a counter 'never decremented on close' — true within a session, but begin_session recomputes it from open lots each session (portfolio.py:325-330). Does not change the conclusion (it is per-session monotonic, valid for the fix). Net: confirmed real as a latent/defensive unit bug, overstated as run-affecting — dormant behind two gates, zero impact on any current/default run.

---

## L8_nan_close_exit &mdash; NaN minute close -> NaN exit price -> silent NaN PnL

**Finder:** real (severity high, confidence high) &middot; **Skeptic:** context_dependent (final severity medium)

**Evidence (finder):**

The code-level defect is unguarded end-to-end (all paths verified against current code):

- exits.py:1291 (in-loop max-hold): `px = c` taken unconditionally on the eligible frame; comment at 1288-1290 explicitly says "c ... possibly NaN ... always takes c". Then exits.py:1293 `return _mk_exit(pos, bar_date, float(px), "max_hold", ...)` — float(NaN) stays NaN.
- exits.py:1309 (end-of-walk fallback): `px = c_arr[last_i]`; exits.py:1311 `_mk_exit(..., float(px), "max_hold", ...)` — same NaN-unsafe.
- exits.py:1436 `_mk_exit`: `exit_price=float(exit_price)` — NO NaN guard.
- exits.py:992 `_exit_walk_fast_eligible`: only checks `pd.api.types.is_numeric_dtype(...)` on o/h/l/c; a column that is all/partly NaN is still numeric → routes to the numpy fast path. Comment 978-980 admits "Numeric columns never carry None (only NaN)".
- Pandas reference shares the bug: exits.py:184-186 `_bar_field` returns `float(bar[n])` when `bar[n] is not None` — NaN is not None and float(NaN) succeeds → present-NaN close becomes a NaN field in the reference path too.
- Earlier branches do NOT catch it: gap (1186/1194 `o<=stop`/`o>=target`) and stop/target (1204-1205 `l<=stop`/`h>=target`) all return False for NaN operands, so a NaN bar trips no earlier exit and rides to max-hold.
- Downstream PnL is NaN-unsafe: portfolio.py:437 `pnl = (exit_price - pos.entry_price) * pos.qty`; portfolio.py:469 `self.state.bankroll += pnl` — NaN exit_price → NaN pnl → NaN bankroll, silently.
- No upstream filter: store.py:135-153 `_normalise_bars` only normalises the timestamp column (no OHLC dropna/coerce); suppliers.py:152-157 returns store.minute_bars verbatim; cached_suppliers.py:203-225 `_range` slices on timestamp only; data_quality.py has zero isna/notna/dropna/NaN OHLC checks (grep: "No matches found"). Round-1 map sim_exits.md:77 and :86 pre-flagged this; sim_exits.md:92 confirms "No direct test found for ... NaN-close max-hold".

**Reproduction (finder):**

Ran the REAL functions in a throwaway python -c REPL (C:/Python312, PYTHONPATH=bowaka_v2_lab/src:bowaka_common/src) with a hand-built eligible minute frame (float64 OHLC) carrying a present-NaN close on the 15:59-ET max-hold bar, stop/target set 50% away so no earlier exit fires.

In-loop max-hold case — ACTUAL output:
  close dtype: float64 | eligible: True
  --- _walk_lot_exit_numpy result ---  exit_reason: max_hold  exit_price: nan | isnan: True
  --- walk_lot_exit (dispatcher) result ---  exit_reason: max_hold  exit_price: nan | isnan: True
  --- downstream PnL (portfolio._record_close formula) ---  pnl = (exit_price - entry_price) * qty = nan | isnan: True

End-of-walk fallback case (no bar at/after 15:59 ET; last eligible bar 15:00 ET has NaN close) — ACTUAL output:
  eligible: True | last close: nan
  exit_reason: max_hold  exit_price: nan | isnan: True   downstream pnl: nan | isnan: True

So BOTH cited paths (~1287-1293 and ~1308-1313) produce a NaN exit price and NaN PnL with the current code; no guard intervenes.

NOT verified: whether the REAL production lake actually carries a present-but-NaN close on an eligible minute bar. Docker Desktop's API returned HTTP 500 on every version probed (1.41-1.54) so `docker exec ql-jupyter` lake inspection at /opt/market_data_cache was impossible; the in-repo lake (research_notebooks/market_data/bars/vendor=alpaca) is empty of minute partitions. Note the minute writer (backfill.py:1470-1478 fetch_minute_bars) writes only minutes Alpaca returns and does NOT reindex onto a full session grid, so absent minutes are ROWS-MISSING (not present-NaN); a present-NaN close would require the vendor to emit a bar dict with a null OHLC field (or a corrupt/partial partition). This bounds the natural trigger frequency but does not eliminate it, and nothing in the pipeline rejects such a row if it exists.

**Blast radius (finder):** All exit-walk modes (current_code_parity, intended_realism, fast_realism) and both walk paths (numpy fast + pandas reference) on any backtest/Optuna fold whose data contains a present-NaN OHLC minute on a bar reaching max-hold. A single NaN-close max-hold exit poisons that trade's pnl → NaN, which propagates through portfolio.state.bankroll (portfolio.py:469) and daily_realized_pnl (portfolio.py:470) to NaN for the rest of the run, then into the Optuna objective — silently corrupting/NaN-ing the trial score with no error raised. Frequency is data-dependent (likely rare given the rows-missing writer semantics) but each occurrence is high-impact and undetected.

**Fix sketch (finder):** Guard the max-hold close before it becomes an exit price: if `np.isnan(c)` (in-loop, ~1291) or `c_arr[last_i]` (fallback, ~1309), fall back to the last numeric close / entry_price / a quote-derived price, OR drop NaN-OHLC rows at the supplier boundary (store.minute_bars / cached _range). Minimally, add a NaN guard in `_mk_exit` (exits.py:1436) and/or assert non-NaN pnl in portfolio._record_close (portfolio.py:437) so corruption fails loud instead of silent. Also make `_exit_walk_fast_eligible` reject frames with NaN OHLC (or treat NaN as a fallback-trigger) for path consistency.

**Skeptic reasoning:**

The CODE defect is confirmed and unguarded at the exit/portfolio layer (I independently read current code and reproduced it). exits.py:1291 `px = c` / :1293 `float(px)` (numpy in-loop max-hold) and :1309/:1311 (end-of-walk fallback) take the close unconditionally; the comments at 1288-1290 and 1307-1308 explicitly admit c is "possibly NaN" and "always" taken. The pandas reference shares it (920/924, 945-948 via _bar_field 184-186, since float(NaN) succeeds and the `h is None or l is None` skip at 778 returns False for present-NaN). _mk_exit (1436) has no NaN guard. Reproduced with real functions (PYTHONPATH set, C:/Python312): eligible=True, _walk_lot_exit_numpy AND walk_lot_exit both return exit_reason=max_hold, exit_price=nan; downstream pnl=(nan-100)*10=nan. portfolio.py:437/469/470/475 accumulate it with no guard (and is_loss at 476 miscounts NaN as non-loss).

WHERE I DISAGREE with the finder's blast-radius/"silent, no error raised" claim — there IS a guard the finder missed, on the dominant (Optuna study) path: NaN pnl -> NaN final_bankroll -> net_return_pct NaN (sim/metrics.py:77) -> FoldResult.net_return NaN -> compute_objective always calls validate_metric_units (objective.py:691-693, validate_units defaults True, no production caller passes False) -> MetricUnits._validate_unit_ranges RAISES MetricUnitsError("net_return must be finite", objective.py:126-127). Reproduced: compute_objective([fold with NaN net_return]) raises MetricUnitsError. MetricUnitsError is ValueError/Exception (MRO verified), NOT in STRUCTURAL_EXCEPTIONS (errors.py:93-100), so at the trial body it falls past `except structural: raise` (walkforward_runner.py:1260) to `except Exception` (1262) -> log.error("trial ... failed entirely") (1272) -> return _FAILED_TRIAL_SCORE=-1.0e9 (1273/97). That trial is then filtered as sentinel_score (2701-2712) and excluded from best-trial selection. So the NaN does NOT silently NaN the objective nor silently corrupt bankroll "for the rest of the run" in a study — the offending trial dies loudly and is discarded.

The finder's cited DQ "guard" is irrelevant either way: ingestion_ohlc_violation runs on DAILY frames only (data_quality.py:1508 `bar_frames=daily_frames`), and I verified it does NOT even detect a NaN close (count=0 — NaN skipped by pandas max/min skipna; nonpositive `NaN<=0` is False); and current_code_parity/fast_realism aren't DQ-gated (data_quality.py:1204-1211). So no DQ check stops it; the real backstop is the objective finite-validator.

DATA-REACHABILITY is unverified and likely rare: store._normalise_bars (store.py:135-153) and minute_bars (242-276) do zero OHLC NaN filtering, so a present-NaN parquet row would flow through; but the writer _coerce_bar_row (backfill.py:395-398) uses `float(...or 0.0)` which I verified scrubs None->0.0 but does NOT scrub NaN (float(nan) or 0.0 -> nan). A natural trigger therefore needs the Alpaca SDK to emit a null OHLC field (abnormal) or a corrupt partition. Could not inspect the real lake (Docker API returned HTTP 500; in-repo bars/vendor=alpaca has no minute partitions), so frequency is UNKNOWN-but-bounded. No direct test exists for the NaN-close max-hold (only the MetricUnits validator is unit-tested, test_objective_units_consistent.py).

---

## L9_entry_date_today &mdash; entry_date falls back to wall-clock date.today() in a backtest

**Finder:** not_real (severity low, confidence high) &middot; **Skeptic:** refuted (final severity none)

**Evidence (finder):**

The defective branch exists exactly as described — sim/strategy_consumer.py:594-599:
  594  ts_pts = candidate_event.get("scan_timestamp", str(decision_ts))
  595  entry_date = (
  596      _dt.datetime.fromisoformat(ts_pts.replace("Z", "+00:00")).date()
  597      if isinstance(ts_pts, str)
  598      else _dt.date.today()
  599  )
But on every real path scan_timestamp is a STRING, so the else-branch is dead:
- All emitted candidate events are built by scanner/event_builder.py:build_candidate_event, which sets `"scan_timestamp": scan_iso` (event_builder.py:75) where scan_iso = _iso_utc(scan_ts). _iso_utc is typed `-> str` and its only return is `.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")` (event_builder.py:19-25). The two matrix paths likewise set scan_timestamp from an inline `.strftime(...)` (scan_matrix_runtime.py:248,261; scan_matrix_vectorized.py:229,342) and scan_loop.py from _iso_utc (scan_loop.py:117-121,227,238).
- The ONLY production caller of consume() is event_loop.py:491 (`cr = consumer.consume(ev, ...)`), where ev comes straight from scan_result.emitted (event_loop.py:475), i.e. the build_candidate_event dicts (scan_loop.py:485/514, scan_matrix_runtime.py:449/473, scan_matrix_vectorized.py:477/500). Both backtester dispatch paths (smoke batch backtester.py:1108 and event-driven backtester.py:1429, including the matrix override) route through run_one_scan → consume.
- grep for any reassignment of ev["scan_timestamp"] in sim/ and scanner/ post-build returned NOTHING, so the string survives to the consumer.
- Even the missing-key default is a string: `.get("scan_timestamp", str(decision_ts))`.
Other StrategyConsumer.consume callers are tests only (tests/integration/test_halt_gate_*, test_intended_realism_*), which hand-build events and are not a real backtest.

**Reproduction (finder):**

Ran existing code in a throwaway python -c REPL (PYTHONPATH=research_notebooks/bowaka_v2_lab/src:research_notebooks/bowaka_common/src, C:/Python312/python.exe). Built a REAL event via build_candidate_event and replayed the exact :594-599 expression:
  A. _iso_utc('2026-03-04 14:31 UTC') -> str '2026-03-04T14:31:00Z'
  B. build_candidate_event(...) ['scan_timestamp'] -> type=str, '2026-03-04T14:31:00Z'
  C. real-event path -> isinstance(ts_pts,str)=True, entry_date=2026-03-04 (deterministic scan date; today()-fallback NOT taken)
  D. FORCED non-string (ev['scan_timestamp']=pd.Timestamp) -> isinstance=False, entry_date=2026-06-12 == date.today() (fallback fires — confirms the latent bug, but requires an input that never occurs)
  E. missing scan_timestamp key -> ts_pts='2026-03-04 14:31:00+00:00' (str(decision_ts)), isinstance=True, entry_date=2026-03-04 (still a string; fallback NOT taken)
So the bug is only reachable with a non-string scan_timestamp, which no real producer or caller ever supplies.

**Blast radius (finder):** None on real runs. entry_date feeds Position.entry_date / entry_session (strategy_consumer.py:807,817), which drive max_hold_days / EOD / session accounting. IF the fallback ever fired it would stamp positions with wall-clock date.today() instead of the historical scan date, corrupting hold-period/session logic and making backtests non-deterministic across days — but no real path reaches it (build_candidate_event always emits a string, no post-build mutation, default is also a string). The exposure is purely latent: a future caller/refactor that puts a Timestamp/datetime into scan_timestamp before consume() would silently activate it. entry_timestamp/parent_fill_ts on the same path use str(ts_pts) and are unaffected.

**Fix sketch (finder):** Defensive hardening only (not a live defect): make the else-branch coerce ts_pts to its true timestamp (e.g. pd.Timestamp(ts_pts).date() / accept datetime/date directly) instead of date.today(), or assert/raise on a non-string so a future regression fails loud rather than leaking wall-clock time.

**Skeptic reasoning:**

Independently confirmed the first analyst's not_real verdict. The defective branch exists verbatim at sim/strategy_consumer.py:594-599 (ts_pts = candidate_event.get("scan_timestamp", str(decision_ts)); entry_date = ...date() if isinstance(ts_pts, str) else _dt.date.today()). But the else-branch is dead on every real path:\n\n1) scan_timestamp is ALWAYS a string at the source. build_candidate_event sets "scan_timestamp": scan_iso (event_builder.py:75), where scan_iso = _iso_utc(scan_ts) and _iso_utc is typed -> str with its sole return being .tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ") (event_builder.py:19-25).\n\n2) All THREE emit producers build the emitted event via build_candidate_event and mutate ONLY candidate_rank afterward, never scan_timestamp: scan_loop.py:485 (emit append :514), scan_matrix_runtime.py:449 (append :473, only ev["candidate_rank"]=rank :469), scan_matrix_vectorized.py:477 (append :500, only ev["candidate_rank"]=rank :496). The vectorized :342 scan_timestamp is a separate gate-dump _row, not the emitted event.\n\n3) The ONLY production consume() caller is event_loop.py:491, fed straight from scan_result.emitted (event_loop.py:475) with no intervening mutation of scan_timestamp. grep for consumer.consume/.consume( across non-test code returns only event_loop.py:491.\n\n4) Even the missing-key default is a string: .get("scan_timestamp", str(decision_ts)).\n\nReproduction (PYTHONPATH=research_notebooks/bowaka_v2_lab/src:research_notebooks/bowaka_common/src, C:/Python312/python.exe, existing code only):\n  A. _iso_utc(...) -> str '2026-03-04T14:31:00Z'\n  B. build_candidate_event(...)['scan_timestamp'] -> type=str, '2026-03-04T14:31:00Z'\n  C. real-event path -> isinstance str: True, entry_date=2026-03-04 (historical scan date), today()=2026-06-12 NOT taken\n  D. FORCED non-string (ev['scan_timestamp']=pd.Timestamp) -> entry_date=2026-06-12 == today() (fallback fires, but this input never occurs)\n  E. missing-key default -> str '2026-03-04 14:31:00+00:00', entry_date=2026-03-04, isinstance str: True (fallback NOT taken)\n\nThe date.today() fallback is reachable ONLY with a non-string scan_timestamp, which no real producer or caller ever supplies. It is purely latent: a future refactor inserting a Timestamp/datetime into scan_timestamp before consume() would silently leak wall-clock time into entry_date (which feeds Position.entry_date/entry_session for max_hold/EOD/session logic, strategy_consumer.py:807,817), but no current real backtest path reaches it. The finder's not_real / low verdict is correct; live-impact severity is none (latent-only).

---

## L10_tape_manifest_flag &mdash; derive_validation_config sets tape_replay but not the manifest flag suitability gates on

**Finder:** not_real (severity none, confidence high) &middot; **Skeptic:** refuted (final severity none)

**Evidence (finder):**

The lead assumes `consumes_trade_tape` is a manifest flag `derive_validation_config` must set independently, and forgets to. It is not. The backtester DERIVES the flag directly from the same `fill_model` config fields that `derive_validation_config` sets, at manifest-build time.

derive_validation_config (autoconfig.py:339-345) sets:
  for _blk in ("execution", "exits"):
      _sub = dict(cfg.get(_blk) or {}); _sub["fill_model"] = "tape_replay"; cfg[_blk] = _sub

The backtester builds the manifest fill_model block from cfg_dict (a shallow copy of the input cfg made at backtester.py:715 `cfg_dict = dict(cfg)`):
  backtester.py:1878-1885
    "fill_model": {
        "execution": str((cfg_dict.get("execution") or {}).get("fill_model", "legacy")),
        "exits": str((cfg_dict.get("exits") or {}).get("fill_model", "legacy")),
        "consumes_trade_tape": any(
            str((cfg_dict.get(_b) or {}).get("fill_model", "legacy")) == "tape_replay"
            for _b in ("execution", "exits")),
    }

suitability.decide_suitability reads that derived flag (suitability.py:236-237):
    if (manifest.get("fill_model") or {}).get("consumes_trade_tape"):
        return "research_only"

lineage._resolved_consumes_trades (lineage.py:273-283) uses the identical derivation from execution/exits fill_model — used to gate the trades_partitions_hash, not to populate the manifest flag the cap reads. No code mutates cfg_dict["execution"]/["exits"].fill_model between line 715 and 1878 (grep over backtester.py found zero assignments to those keys; only the two read sites). SimulationConfig.model_validate (line 719) validates only the `simulation` sub-dict, leaving execution/exits untouched.

**Reproduction (finder):**

Ran the REAL functions in a python -c REPL (PYTHONPATH=research_notebooks/bowaka_v2_lab/src:research_notebooks/bowaka_common/src, C:/Python312).

(1) derive_validation_config(search_cfg{execution:{foo:1}, exits:{bar:2}, mode:fast_realism, feed:sip}, validation_mode='intended_realism', enable_tape_replay=True) returned:
    execution.fill_model = tape_replay
    exits.fill_model     = tape_replay
    simulation.mode      = intended_realism
Replicating backtester.py:1878-1884 manifest derivation on that config gave:
    {'execution':'tape_replay','exits':'tape_replay','consumes_trade_tape': True}
And lineage._resolved_consumes_trades(cfg) = True.

(2) decide_suitability over a temp run_dir with summary.json{feed:sip} and run_manifest.json{simulation.mode:intended_realism, fill_model:{...consumes_trade_tape:True}}:
    VERDICT tier = research_only
Control (same but consumes_trade_tape:False/legacy fills):
    CONTROL tier = backtesting_only
_CONTRACT_TIER_CAP['intended_realism'] = backtesting_only — so the line-229 contract cap does NOT fire here; the line-236 consumes_trade_tape gate is provably the one that capped it to research_only. The cap fires exactly as designed; it does NOT evade.

**Blast radius (finder):** No runs affected. A config produced by derive_validation_config(enable_tape_replay=True) is correctly capped at research_only by decide_suitability regardless of simulation mode/feed, because the backtester re-derives consumes_trade_tape from the fill_model fields that derive_validation_config sets. Promotion safety holds.

**Fix sketch (finder):** No fix needed. If hardening is desired (defense-in-depth, since the flag is derived twice — once in lineage for the trades hash, once in backtester for the manifest), the two derivations could be unified to call lineage._resolved_consumes_trades, but they already agree.

**Skeptic reasoning:**

I independently read the CURRENT code (paths differ from the lead: optuna/autoconfig.py and promotion/suitability.py) and reproduced every leg. The lead's premise is false: `consumes_trade_tape` is NOT a manifest flag `derive_validation_config` must set independently — it is DERIVED by the backtester from the same `execution`/`exits` fill_model fields the function sets.

Chain, all verified against current code:
1. autoconfig.py:339-345 — `derive_validation_config(enable_tape_replay=True)` sets `cfg["execution"]["fill_model"]="tape_replay"` and `cfg["exits"]["fill_model"]="tape_replay"`. (No `consumes_trade_tape` key, as the lead notes — but that is by design.)
2. backtester.py:715 — `cfg_dict = dict(cfg)` (shallow). Grep over backtester.py for assignments to `cfg_dict["execution"]/["exits"]` or `["execution"]=/["exits"]=` returned ONLY line 715; nothing mutates those keys. `SimulationConfig.model_validate` (line 719) validates only the `simulation` sub-dict, leaving execution/exits untouched.
3. backtester.py:1878-1885 — the manifest fill_model block DERIVES `consumes_trade_tape = any(cfg_dict[b]["fill_model"]=="tape_replay" for b in (execution,exits))`. This is inside `build_run_manifest(...)` at line 1861.
4. The manifest is written to run_manifest.json (line 1992) and fed to `decide_suitability` (lines 2048-2051), both gated to `artifact_mode=="full"` — i.e. exactly the finalist-validation runs the derived config targets. The walk-forward objective uses `objective_minimal` (no manifest write / no suitability decision), so the cap is irrelevant there and cannot be "evaded" — there is no tier to evade.
5. suitability.py:236-237 — `if (manifest.get("fill_model") or {}).get("consumes_trade_tape"): return "research_only"`.
6. lineage.py:273-283 `_resolved_consumes_trades` uses the identical derivation (gates the trades hash); both agree.

REPRODUCTION (real functions, PYTHONPATH set, C:/Python312):
- derive_validation_config(search_cfg{execution:{...},exits:{...},mode:fast_realism,feed:sip}, validation_mode='intended_realism', enable_tape_replay=True): execution.fill_model=tape_replay, exits.fill_model=tape_replay, simulation.mode=intended_realism; lineage._resolved_consumes_trades=True; replicated manifest derivation -> {'execution':'tape_replay','exits':'tape_replay','consumes_trade_tape':True}.
- decide_suitability on a temp run_dir (summary feed=sip, manifest mode=intended_realism + consumes_trade_tape=True, FULL walk-forward+recon evidence) -> research_only. CONTROL (legacy fills) -> backtesting_only. This proves it is the line-236 consumes_trade_tape gate that caps (not the contract cap, since _CONTRACT_TIER_CAP['intended_realism']=backtesting_only). A manifest MISSING the fill_model block -> backtesting_only, but the backtester writes that block unconditionally, so that escape is unreachable.

Existing test test_tape_replay_pb6.py (tests/unit/sim/) locks both the derive output (lines 71-82) and the suitability cap on a tape-replay manifest (lines 46-55). Minor coverage gap: no e2e test asserts the backtester's line-1881 derivation from a real derive_validation_config output (the test hand-writes the manifest block) — but the derivation is unconditional and I reproduced it, so this is a test-thoroughness note, not a defect. The cap fires exactly as designed; it does NOT evade.

---

## L11_default_exit_zero_slip &mdash; Default exit _bracket_fill = exact bracket price, zero slippage

**Finder:** real (severity high, confidence high) &middot; **Skeptic:** confirmed_real (final severity high)

**Evidence (finder):**

exits.py:553-554 — the early-return default branch in `_bracket_fill`: `if not xf.cross_spread and not xf.participation_cap: return float(bracket_price), None`. The docstring (exits.py:530-532) states this is "BYTE-IDENTICAL to the legacy engine" filling "exactly at the bracket price with no slip override."
Default resolution at the call boundary (exits.py:717-728, duplicated verbatim at 1075-1086): `cross_spread = bool(cfg.get("cross_spread", False))` → False; `participation_cap = cfg.get("participation_cap")` → None; `require_fresh_quote = bool(cfg.get("require_fresh_quote", False))` → False; `fill_model = str(cfg.get("fill_model", "legacy"))` → "legacy". With fill_model="legacy" the tape branch at exits.py:548 is skipped, so control reaches the line 553 default branch.
Pydantic config defaults agree (config/models.py:319 fill_model="legacy", :421 cross_spread=False, :427 participation_cap=None, :433 require_fresh_quote=False).
Returned px flows straight into the exit price: exits.py:849/854/860/865 (and the 1218/1223/1229/1234 vectorized twin) call `px, slip = _bracket_fill(...)` then `_mk_exit(pos, bar_date, px, "stop"/"target", ..., slip_bps_override=slip)`. `_mk_exit` sets `exit_price=float(exit_price)` (exits.py:1436) and, with slip_bps_override=None and reason in {"stop","target"} (not in the discretionary-exit set), sets `slip_bps = 0.0` (exits.py:1420-1423) → zero slippage on BOTH the realized price and the forensic field.
exit_driver.py:81,110 passes the raw `cfg["exits"]` block straight through (`exit_cfg=exits_cfg`) with no mode-based override; backtester.py never references these levers (grep: no matches). Prod-parity config `configs/bowaka_v2_actual_iex_current_code.yml` runs `simulation.mode: current_code_parity` (line 151) and its `exits:` block (lines under `exits:`) sets NONE of the four levers → all default OFF.

**Reproduction (finder):**

Ran the REAL `_bracket_fill` in a throwaway REPL (PYTHONPATH set to the lab+common src; C:/Python312/python.exe). Built a real `_XFill` with the documented defaults (cross_spread=False, participation_cap=None, require_fresh_quote=False, fill_model="legacy") and a bar carrying a wide 99.00/101.00 spread + volume=1000. ACTUAL output:
  kind=stop   bracket_price= 99.5000  -> fill_px=99.5    slip_override=None  equal=True
  kind=target bracket_price=101.2500  -> fill_px=101.25  slip_override=None  equal=True
The exit fills land exactly on the stop/target price; the bar's spread, bid/ask and volume are entirely ignored at defaults, and the slip override is None (→ 0.0 bps in _mk_exit).

**Blast radius (finder):** Affects every backtest/study run with the default exits block, which is the dominant operating mode. Specifically: all current_code_parity runs (the prod finalist #3155 path — commit 87a85ed "adopt prod winner #3155"; config bowaka_v2_actual_iex_current_code.yml mode=current_code_parity with no exit levers set) AND intended_realism runs that don't explicitly enable cross_spread/participation_cap/fill_model. Both walk implementations (pandas reference ~:730 and vectorized ~:1088) share the identical default chain, so the optimized path is equally affected. Impact direction: stop and target exits get zero adverse slippage / no spread give-up / no size-impact, making every bracket exit optimistic vs a real marketable sell — inflating backtested edge and PnL for the strategy actually selected for production. Realism levers exist (PB.1-4) but are OFF by default and no YAML in the lab enables them (grep over *.yml/*.yaml: no matches).

**Fix sketch (finder):** Either default the realism levers ON for current_code_parity/intended_realism (e.g. cross_spread=True with half_spread give-up, or fill_model="tape_replay" when a trades_supplier is wired), or have the sim-mode resolver inject a non-zero exit cost in the exits block for non-smoke modes — rather than leaving the optimistic exact-bracket fill as the silent default that the production finalist ran under. Note: targets are correctly clamped to the limit (resting limit, no improvement), so the realism gap is concentrated on stops/marketable exits paying no spread+impact.

**Skeptic reasoning:**

Independently verified against current code; the first analyst is correct and slightly understates the gap. DEFAULT BRANCH: exits.py:553-554 `if not xf.cross_spread and not xf.participation_cap: return float(bracket_price), None`; the tape branch (548-551) is bypassed when fill_model=="legacy". DEFAULT RESOLUTION (both walks, verbatim): exits.py:717-728 (pandas) and 1075-1086 (vectorized) resolve cross_spread=False, participation_cap=None, require_fresh_quote=False, fill_model="legacy". PYDANTIC: config/models.py:421,427,433,438 all default OFF. ZERO FORENSIC SLIP: exits.py:1420-1423 — slip_bps_override=None + reason in {stop,target} -> slip_bps=0.0. CALL SITES: exits.py:849/854/860/865 (pandas) and 1218/1223/1229/1234 (vectorized) feed px straight into _mk_exit -> exit_price=float(exit_price) (1436). DISPATCH: exit_driver.py:81,110 passes raw cfg["exits"] straight to walk_lot_exit with no mode override; backtester.py only READS fill_model for manifest stamping (1878-1882), never forces it on. current_code_parity/intended_realism drive exits through this minute-path walk (exits.py:1465-1466). REPRODUCED (my own REPL, real _bracket_fill at documented defaults, bar with 99/101 spread + vol=1000): kind=stop bracket=99.5000 -> fill=99.5 slip=None equal=True; kind=target bracket=101.25 -> fill=101.25 slip=None equal=True — spread/bid/ask/volume all ignored. NO CONFIG GATE: grep over every lab *.yml/*.yaml for the four levers returns zero matches; prod-parity bowaka_v2_actual_iex_current_code.yml (mode: current_code_parity at :151) sets only stop_pct/target_pct/etc in its exits: block (:33-53) — none of the levers; all three intended_realism configs likewise set none. I searched HARD for a refuting guard/caller/default/test and found NONE. ADVERSARIAL STRENGTHENING: the exit closure computes pnl=(exit_price-entry_price)*qty (portfolio.py:437) with NO sell-side commission/regulatory fee (those fields are entry-side only, portfolio.py:123-124) — so the default exit is not merely zero price-slip, it is entirely cost-free on the sell leg. The only nuance (correctly noted by the analyst) is that targets are clamped to the limit (a resting limit gets no improvement) so the realism gap concentrates on marketable stop exits paying no spread+impact. This bites the exact path used to select production finalist #3155 (commit 87a85ed).

---

## L12_t3_max_not_min &mdash; T3 depth cap uses max(touch, cap_shares) so the cap cannot tighten below touch

**Finder:** real (severity high, confidence high) &middot; **Skeptic:** overstated (final severity low)

**Evidence (finder):**

fills.py:621-622 — `cap_shares = float(participation_cap) * minute_vol_shares` then `fillable = min(int(requested_qty), int(max(touch_size, cap_shares)))`. Because of `max(touch_size, cap_shares)`, the participation cap can only RAISE the fillable size (when cap_shares > touch_size); it can never tighten the fill below the full displayed touch_size. Docstring fills.py:600-605 claims "The REAL displayed top-of-book size is always fillable; beyond it, the order may consume up to participation_cap of the scan minute's share volume" — i.e. the cap is meant to bound consumption BEYOND the touch, but the code lets cap_shares fully replace (not add to) the touch and treats it as a floor of touch_size, not a ceiling. Compare the T2/T4 cap at fills.py:1116-1119 which correctly tightens via `cap_qty = min(cap_qty, fill.filled_qty)`. The path is reachable in real runs: detect_execution_tier (fills.py:90-91) returns T3_NBBO_DEPTH whenever has_nbbo_depth=True, and strategy_consumer.py:640-643 sets `has_nbbo_depth = (_mode=="intended_realism" and quote.is_historical) or _mode=="fast_realism"`, passing `participation_cap=minute_volume_participation_frac` (default 0.10, config/models.py:314). exits.py:426 documents the buy side's `max(touch, cap*vol)` as the canonical fillable.

**Reproduction (finder):**

Ran the real `_t3_depth_impact_fill` via `C:/Python312/python.exe -c` with PYTHONPATH set to the lab+common src dirs. Inputs: real historical QuoteSnapshot ask=100.00, ask_size(touch)=1000; minute_bars with a 'timestamp' COLUMN (required by _forward_window — a DatetimeIndex silently yields minute_vol_shares=0) at scan_ts with volume=2000; requested_qty=5000; conservative stress; min_order_notional=0. Sanity: _minute_volume_shares returned 2000.0 and partic_frac was non-zero (0.5/1.0), confirming the full T3 path executed. Result table (cap_shares = pcap*2000):
  pcap=0.001  cap_shares=2     -> filled_qty=1000  (cap of 2 shares ignored; filled full touch)
  pcap=0.01   cap_shares=20    -> filled_qty=1000
  pcap=0.10   cap_shares=200   -> filled_qty=1000  (default cap of 200 shares ignored; filled 5x the cap)
  pcap=0.50   cap_shares=1000  -> filled_qty=1000
  pcap=1.00   cap_shares=2000  -> filled_qty=2000  (here cap_shares>touch, so max() lets the fill EXPAND beyond the touch)
filled_qty == touch_size (1000) regardless of the cap until cap_shares exceeds touch_size — exactly the claimed defect. Note: an earlier attempt used a DatetimeIndex (no 'timestamp' column) which made _forward_window return None and minute_vol_shares=0; rebuilding with a 'timestamp' column gave the valid repro above.

**Blast radius (finder):** Affects every T3_NBBO_DEPTH buy/entry fill, i.e. all runs in intended_realism (with a real historical quote) and ALL fast_realism runs (strategy_consumer.py:640-643). The minute-volume participation cap (default 0.10) is effectively inert for entry SIZE whenever the requested qty and minute-volume cap are below the displayed touch: the sim always grants the full displayed top-of-book size and never partial-fills down to the participation cap. This overstates entry fill size/fillability on illiquid names whose true displayed depth is small relative to requested orders, and—when cap_shares does exceed touch—jumps the fill to cap_shares rather than touch+cap_shares, both inconsistent with the docstring's "touch always fillable, plus up to cap beyond it." It does not corrupt prices (impact bps still scale with participation), only fill quantity / fillability. The sell/exit mirror (exits.py:_participation_impact_bps) caps only the impact bps via min(...), not quantity, so it is not affected by this specific quantity bug but documents the buy-side max as intentionally "symmetric."

**Fix sketch (finder):** If the cap is meant to bound total consumption: `fillable = min(requested_qty, max(touch_size, ...))` should likely be `min(requested_qty, max(touch_size, cap_shares))` only when cap is meant as a floor-of-touch; to make the cap actually tighten, change to `fillable = min(requested_qty, touch_size + int(cap_shares))` (touch always fillable + bounded depth beyond) OR `min(requested_qty, max(touch_size, cap_shares))` kept only for the fast_realism synthetic-quote (touch=0) degradation while real-quote intended_realism uses the additive/min form. Note the fast_realism zero-spread path (touch_size=0) deliberately relies on max(0, cap_shares)=cap_shares, so any fix must preserve that branch (strategy_consumer.py:633-636).

**Skeptic reasoning:**

The numeric behavior is fully confirmed: fills.py:622 is `fillable = min(int(requested_qty), int(max(touch_size, cap_shares)))` with `cap_shares = float(participation_cap)*minute_vol_shares` (:621). I reproduced the analyst's table exactly via `_t3_depth_impact_fill` (touch=1000, minvol=2000): pcap=0.001->filled=1000, 0.01->1000, 0.10->1000, 0.50->1000, 1.00->2000 — the cap is inert until cap_shares>touch_size. BUT the `max()` is the explicit, documented, unit-tested DESIGN CONTRACT, not a defect. The "guard" that refutes the bug framing is the design intent itself, enforced by two dedicated tests: (1) tests/unit/test_fills_t3_depth_impact.py:52-67 `test_touch_only_fill_when_cap_below_touch` asserts filled_qty==300 when cap_shares=100<touch=500 with the inline comment "max(touch, cap)=500, so a 300-share buy is fully filled at the touch model"; (2) tests/unit/sim/test_fast_realism_fill.py:74-83 `test_fast_realism_uses_real_touch_when_historical_quote_present` asserts filled==100 with comment "A real historical quote provides a touch floor: fillable = max(touch, cap)... touch 100 > participation cap 80 -> fills the displayed 100." Both docstrings state the contract: fills.py:601-605 and :984-987 — "The REAL displayed top-of-book size is always fillable; beyond it, the order may consume up to participation_cap of the minute share volume." This is economically correct: the displayed NBBO ask_size is real liquidity a marketable order can hit at the touch, so the cap is meant to bound consumption BEYOND the touch, not below it. The analyst's blast-radius claim is INVERTED: I ran a second repro for illiquid names — touch=100/minvol=500/req=5000 -> filled=100 (partial=True); touch=5/minvol=100/req=5000 -> filled=10 (partial=True). When real displayed depth is small the fill is bounded DOWN to that small touch; the model does NOT manufacture liquidity here. (The genuine over-fill bug is the SEPARATE zero-displayed-size T0/T1 path, roadmap lines 140-144, not this lead.) The audit roadmap itself (bowaka_v2_realism_roadmap.md:146-148) flags this only as "questionable as a 'depth' model" — a modeling-philosophy critique, not a confirmed correctness defect. Path reachability is confirmed (strategy_consumer.py:639-643 has_nbbo_depth = (intended_realism and quote.is_historical) or fast_realism; participation_cap=minute_volume_participation_frac default 0.10 at config/models.py:314; routed at fills.py:1060-1076), but reaching INTENDED, tested behavior is not a defect. Prices are unaffected (impact_bps scale correctly with participation, :626-636). git blame shows :622 landed in e73da67 "Fill model §10f Phase 1: T3_NBBO_DEPTH real-touch ... (default-off, byte-identical)" — deliberate, not accidental.

---

## L14_live_no_timestop_fade &mdash; Live strategy has NO intraday time-stop and NO signal-fade (sim has both)

**Finder:** real (severity high, confidence high) &middot; **Skeptic:** confirmed_real (final severity high)

**Evidence (finder):**

Prod config declares BOTH exits the sim honors but live ignores — research_notebooks/bowaka_v2_lab/reference/source_strategy/scripts/bowaka_v2_config.yaml:275-282: `time_stop:\n  enabled: true\n  exit_time: "15:30"` and `signal_fade:\n  enabled: true\n  initial_mode: "telemetry_then_active_after_validation"\n  eval_time: "15:45"` (max_hold_days: 10 at :273).

SIM honors them — research_notebooks/bowaka_v2_lab/src/bowaka_v2_lab/sim/exits.py: reads `time_stop.exit_time` at :683 (pandas) and :1052 (numpy); fires intraday time-stop at :911-915 (`if time_stop_enabled and clock >= time_stop_clock: ... "time_stop"`); reads signal_fade cfg at :685-697 and fires `signal_fade_*` at :874-908. walk_lot_exit dispatch at :1317-1367.

LIVE implements ONLY a max_hold-days exit — research_notebooks/bowaka_v2_lab/reference/source_strategy/scripts/bowaka_v2_strategy.py:1602-1626 `run_time_stop_pass_v2`: `max_hold = int((cfg.get("exits") or {}).get("max_hold_days", 3))` (:1610); `elapsed = _trading_days_since(entry_iso, today_et)` (:1617); `if elapsed >= max_hold:` then trigger_exit_v2 with `reason="time_stop"` (:1618-1622). The reason LABEL is "time_stop" but the trigger is purely the multi-day hold horizon. The main loop (:1991-2021) wires only poll_fills_v2/process_fill_events_v2 (OCO target/stop), submit_pending_oco_children_v2, enforce_protected_position_invariant_v2, and run_time_stop_pass_v2 — NO intraday-clock or signal-fade pass. grep over the whole live module: the only `exit_time` substring is `exit_timestamp` at :1428 (a closure-record field); zero occurrences of `signal_fade`, `eval_time`, `15:30`, `15:45`.

**Reproduction (finder):**

Ran the REAL functions in throwaway python -c REPLs (no repo writes).

(1) sim/exits.walk_lot_exit with the verbatim prod `exits` block on a hand-built single-day flat minute path (2024-06-10 09:31-16:00 ET, O/H/L/C ~99.5-100.5, entry fill 09:35, stop=89.6, target=140 — price never touches either; max_hold horizon is 10 trading days out so it can't fire on day 0). ACTUAL result: ExitEvent(exit_reason='time_stop', exit_timestamp='2024-06-10T19:30:00+00:00') == 2024-06-10 15:30:00-04:00 ET. The sim closed the lot at the 15:30 time-stop on the entry day.

(2) Live bowaka_v2_strategy._trading_days_since for the SAME lot/day. ACTUAL: entry-day elapsed=0 -> `0 >= 10` False (no exit); 2024-06-11 elapsed=1 False; 2024-06-14 elapsed=4 False; 2024-06-21 elapsed=9 False. Live never time-stops within the hold window — and has no other intraday/fade pass — so the lot the sim closed at 15:30 day-0 stays open live until a real OCO stop/target hits or max_hold_days(10) elapses.

(3) inspect.getsource(live module) substring scan: exit_time->only 'exit_timestamp':1428; signal_fade->False; eval_time->False; 15:30->False; 15:45->False.

**Blast radius (finder):** Affects current_code_parity and intended_realism sim modes (both drive exits through walk_lot_exit per exits.py:30-32; only the smoke_fixture daily path via evaluate_exits is unaffected, and it too has no fade). Every backtested lot is force-closed at 15:30 ET each session by the sim's always-on time_stop (enabled:true, no activation gate) — a divergence present on EVERY trial, since the live consumer holds to bracket/max_hold instead. This systematically shortens sim holding periods and changes the exit-price distribution vs live: sim exits at the 15:30 minute price; live rides to the OCO stop/target or the day-N close. Optimizer PnL/objective is computed against an exit policy live does not execute, so selected winners (e.g. config #3155 with target_pct=0.4, max_hold_days=10) are over-fit to a phantom intraday flatten. Signal_fade divergence is conditional: initial_mode=telemetry_then_active_after_validation means fade is telemetry-only by default in the sim too (records would-have-exited, does not close) — so it diverges from live only IF activated via config activation_state:active or an on-disk activation artifact. The time_stop divergence is the always-on, first-order one.

**Fix sketch (finder):** Achieve parity by either (a) adding an intraday time-stop pass + signal-fade pass to the live strategy that read exits.time_stop.exit_time / exits.signal_fade.eval_time and submit market exits (true parity), or (b) disabling/removing the sim's intraday time_stop (and gating fade off) so the sim's exit set matches live's bracket+max_hold-only behavior. Until reconciled, mark the sim's time_stop/signal_fade as live-unimplemented in the parity contract and exclude their effect from optimizer objectives.

**Skeptic reasoning:**

Independently verified against current code AND reproduced with the real functions. SIM honors an intraday time-stop: sim/exits.py:668 (cfg = exit_cfg or {}), :681-683 (time_stop_enabled defaults True; time_stop_clock=15:30), fires at :911-915. Callers pass exit_cfg = cfg.get('exits') (backtester.py:465-476; exit_driver.py:81-110), so exits.time_stop reaches the function. LIVE has NO intraday/fade path: bowaka_v2_strategy.py:1602-1626 run_time_stop_pass_v2 exits only when _trading_days_since >= max_hold_days(10); _trading_days_since (:1368-1382) returns 0 on the entry day. Main loop (:1991-2021) wires only poll_fills/submit_oco/enforce_protected/run_time_stop. inspect.getsource scan: signal_fade/eval_time/15:30/15:45/intraday = 0 occurrences; exit_time = 1 (only 'exit_timestamp' :1428).

REPRO (real walk_lot_exit, verbatim prod exits block, flat path entry 2024-06-10 09:35 ET, stop 89.6 / target 140 untouched): exit_reason='time_stop', exit_timestamp=2024-06-10 15:30:00-04:00 ET (entry day). Counterfactual time_stop.enabled:false -> 'max_hold' at 16:00. Multi-day path (3 sessions, max_hold_days=10) still closes 'time_stop' at 15:30 day-0. Live for same lot: _trading_days_since=0/1/4/9 for days 0/1/4/9, only >=10 at day 10 -> never exits in the window. (My first repro returned None only because I built the df with a DatetimeIndex; _bar_ts at exits.py:204-221 reads a 'timestamp' column/attr, not the index — the real backtester supplies that column, so this is NOT a guard; adding it reproduced the finder's result exactly.)

NO GUARD prevents it: ALL real run configs — bowaka_v2_actual_iex_current_code.yml:51-53, ..._optuna.yml:66-68, bowaka_v2_actual_iex_intended_realism.yml:51-53, bowaka_v2_actual_sip_intended_realism.yml:51-53, bowaka_v2_intended_realism.yml:51-53 — set time_stop.enabled:true, exit_time:'15:30'; no overlay disables it; both current_code_parity and intended_realism drive exits via walk_lot_exit. So the time_stop divergence bites EVERY trial.

SCOPED DOWN: the signal_fade half of the claim does NOT bite by default. All run configs use initial_mode: telemetry_then_active_after_validation with no activation_state:active, and resolve_signal_fade_active (exits.py:308-316) keeps that mode telemetry-only (records FadeTelemetry, does NOT close the lot) absent a config/artifact activation — matching live, which never fades. The finder correctly flagged this as conditional. The first-order, always-on divergence is the intraday 15:30 time_stop.

Corroborated by the repo's own round1 map prod_strategy.md:35,53,79 ('Major behavioral gap vs config intent'). The finder's real/high verdict is well-founded.

---

## L15_live_ignores_riskcaps &mdash; Live strategy ignores three risk caps the sim enforces

**Finder:** real (severity medium, confidence high) &middot; **Skeptic:** confirmed_real (final severity medium)

**Evidence (finder):**

SIM enforces all three (research_notebooks/bowaka_v2_lab/src/bowaka_v2_lab/sim/risk_gates.py):
- L129-131 max_stopouts_per_day: `max_stopouts = int(risk_cfg.get("max_stopouts_per_day", 4)); if state.stopouts_today >= max_stopouts: return RiskGateResult(False, "kill_switch", ...)`
- L133-136 stop_trading_after_consecutive_stopouts: `consec_stopout_limit = int(risk_cfg.get("stop_trading_after_consecutive_stopouts", 3)); if state.consecutive_stopouts >= consec_stopout_limit: state.kill_switch_state="consecutive_stopouts"; return ...kill_switch`
- L157-161 strategy_slice_loss_pct: `if "strategy_slice_loss_pct" in risk_cfg: slice_loss_pct=float(...); if ...>=slice_loss_pct: state.kill_switch_state="strategy_loss"; return ...kill_switch`
The first two fire UNCONDITIONALLY via defaults (4, 3); slice_loss fires when the key is present.

Sim state tracks the counters: portfolio.py L206-207 `stopouts_today:int=0; consecutive_stopouts:int=0`, incremented at L482-490 on stopout closes.

Gate is wired into the run: strategy_consumer.py L258 `risk_cfg = cfg.get("risk") or {}`, L450-456 `evaluate_risk_gates(..., risk_cfg=risk_cfg, ...)`.

LIVE enforces NONE of the three (research_notebooks/bowaka_v2_lab/reference/source_strategy/scripts/bowaka_v2_strategy.py):
- `_risk_gates` (L436-514) enforces only: bankroll_floor_halt (L449), max_concurrent_positions (L467, from sizing), max_total_entries_per_day (L473), max_gross_exposure_pct (L482), daily_loss_pct (L490), adv_cap (L500). Returns None otherwise (L514).
- `_shadow_risk_check` (L517-545) only handles shadow.{max_total_entries_per_day, max_gross_exposure_pct, daily_loss_pct}.
- Exhaustive grep for the three keys across ALL .py reference scripts (incl. imported bowaka_v2_features/paths/schemas): ZERO hits. They appear only in YAML (actual_bowaka_v2_contract.yaml L101/118/119; scripts/bowaka_v2_config.yaml L224/234/235).
- No stopout tracking exists in the live state machine at all; the only `consecutive` matches in live code are unrelated stream-reconnect failure counters (bowaka_v2_stream.py).

Both study configs carry all three keys: bowaka_v2_actual_iex_current_code.yml L84/101/102 and bowaka_v2_actual_sip_intended_realism.yml L84/101/102 (`max_stopouts_per_day:4`, `stop_trading_after_consecutive_stopouts:8`, `strategy_slice_loss_pct:0.025`).

NOTE the divergence is partially self-documented: risk_gates.py docstring L24-26/L151-161 and docs/current_code_vs_intended_realism.md §6 (L195-229) describe the slice-loss gate as an "intended-realism extension... additive (off unless configured)" claiming "a current_code_parity config that simply omits the key reproduces live behavior exactly" — but the actual current_code config does NOT omit the key (it sets 0.025), and the doc does NOT cover the stopout caps, which fire via hard-coded defaults regardless.

**Reproduction (finder):**

Ran the real sim function in a throwaway REPL (no repo writes):
PYTHONPATH=...src C:/Python312/python.exe -c "import datetime; build Portfolio(90000)+PortfolioState; risk_cfg with the 3 contract values + generous other caps; call evaluate_risk_gates"
ACTUAL output:
  BASELINE accepted= True reason= None
  STOPOUTS_TODAY=4 accepted= False reason= kill_switch
  CONSEC_STOPOUTS=8 accepted= False reason= kill_switch kill_state= consecutive_stopouts
  SLICE_LOSS -2300 (<-2250) accepted= False reason= kill_switch kill_state= strategy_loss
Each of the three caps observably rejects an entry the live _risk_gates would accept (live has no code path reading any of these keys, and no stopout state to evaluate them against).

**Blast radius (finder):** Affects every backtest/Optuna study/walkforward run using the actual contract or either study config (current_code_parity AND intended_realism) — all carry the three keys. The sim is strictly MORE risk-constrained than live: it can kill-switch a strategy-day on consecutive/total stopouts or a 2.5% slice drawdown that live would trade through. Direction of bias: the sim refuses entries (and trips kill switches) the live strategy would take, so backtested PnL/exposure understates what live actually risks/earns on adverse days — an optimistic-for-safety but pessimistic-for-return parity error that also distorts any objective sensitive to entry count, stopout-driven kill switches, or tail-day drawdown. max_stopouts_per_day and stop_trading_after_consecutive_stopouts fire even if a config omits them (hard-coded defaults 4/3), so the divergence is not fully escapable via config; strategy_slice_loss_pct is escapable only by deleting the key, which neither shipped config does.

**Fix sketch (finder):** Resolve the asymmetry per direction: either (a) implement the three caps in live _risk_gates (add stopout counters to live state + the slice-loss kill switch) to match the intended contract, or (b) for current_code_parity make the sim mirror live exactly — gate the two stopout caps behind key presence (drop the hard-coded 4/3 defaults so an absent key = no gate) and confirm current_code configs omit all three. Whichever way, add a parity test asserting sim and live accept/reject identically for these caps under the shipped configs.

**Skeptic reasoning:**

Independently verified the divergence is real and bites real runs; tried hard to find a guard/gate/test that neutralizes it and found none.

SIM enforces all three (research_notebooks/bowaka_v2_lab/src/bowaka_v2_lab/sim/risk_gates.py): max_stopouts_per_day L129-131 (default 4), stop_trading_after_consecutive_stopouts L133-136 (default 3, sets kill_switch_state="consecutive_stopouts"), strategy_slice_loss_pct L157-161 (fires only when key present, sets "strategy_loss"). The gate is wired into the sim entry path: strategy_consumer.py L450 evaluate_risk_gates(...). Counters are tracked/incremented in portfolio.py L482-490.

LIVE enforces NONE — confirmed two ways: (1) exhaustive grep across reference/source_strategy returned ZERO hits for all three keys / "stopout" / "consecutive"; (2) executed the live source — inspect.getsource(bowaka_v2_strategy._risk_gates) contains no "stopout"/"consecutive"/"slice_loss" substring. Live _risk_gates (L436-514) enforces only bankroll_floor_halt, max_concurrent_positions, max_total_entries_per_day, max_gross_exposure_pct, daily_loss_pct, adv_cap; live state has no stopout counters at all.

REPRODUCED the load-bearing claim (hand-built Portfolio/PortfolioState, real evaluate_risk_gates, no repo writes):
  KEYS ABSENT (empty risk_cfg, only defaults): stopouts_today=4 -> rejected kill_switch; consecutive_stopouts=3 -> rejected kill_switch. So the two stopout caps are NOT escapable by omitting keys.
  KEYS PRESENT (current_code values): stopouts_today=4 -> kill_switch; consecutive_stopouts=8 -> kill_switch (kill_state=consecutive_stopouts); slice_loss dpnl=-2300 (<-2.5%*90000) -> kill_switch (kill_state=strategy_loss).

Searched for a neutralizer and found none: (a) NO simulation.mode / current_code gate in risk_gates.py — the gates fire identically in current_code and intended_realism modes; (b) both shipped study configs set all three (bowaka_v2_actual_iex_current_code.yml L84/101/102: max_stopouts_per_day:4, stop_trading_after_consecutive_stopouts:8, strategy_slice_loss_pct:0.025; same in the actual contract L101/118/119), so even the "parity" config triggers them; (c) the doc rationale (docs/current_code_vs_intended_realism.md §6 L224-228) claims the slice gate is escapable by omitting the key — but the shipped current_code config does NOT omit it, and §6 says nothing about the two stopout caps, which fire via hard-coded 4/3 defaults regardless; (d) NO parity test asserts sim≡live for these caps — tests/parity/test_strategy_slice_loss_enforced.py only proves the slice gate is off when the key is absent (L78-90), and the integration tests (test_event_driven_simulator.py test_consecutive_stopouts_kill_switch / max_stopouts) assert the sim DOES reject, treating the divergence as intended sim behavior, not flagging it.

Refining nuances (do not refute): stopouts_today resets each begin_session (portfolio.py L349) so max_stopouts_per_day bites only when one session-day yields 4 intraday stops — less frequent for a once-per-day daily-bar strategy; consecutive_stopouts CARRIES OVER across sessions (portfolio.py L350) and kill_switch_state resets daily (L355), making the consecutive-stopout gate (cfg 8 / default 3) and the slice-loss gate (2.5% session drawdown) the reachable ones over a multi-month run. Direction of bias: sim is strictly MORE risk-constrained than live — it refuses entries / trips kill switches live would trade through, so backtests are pessimistic-for-return, not optimistic.

---

## L16_wf_methodology &mdash; No embargo/purge gap + step_months is dead (correlated folds)

**Finder:** real (severity high, confidence high) &middot; **Skeptic:** overstated (final severity low)

**Evidence (finder):**

Both sub-claims confirmed in current code.

(a) No embargo/purge gap — val_start == train_end:
walkforward.py:74-76 `train_end = _add_months(cur_train_start, train_months); val_start = train_end; val_end = _add_months(val_start, val_months)` — validation begins the exact instant training ends. tests/unit/test_walkforward_splits.py:22 even asserts `s.train_end == s.val_start` ("back-to-back is standard"). No 'embargo|purge|gap|warmup|carry-forward' token exists anywhere in src/bowaka_v2_lab/optuna (grep: No matches).
Leakage mechanism is concrete: suppliers.py:381-410 `build_daily_cache_from_lake(..., lookback_days: int = 400 ...)` builds the ATR/EMA/vol daily baseline for a session from `prior[prior["_sd"] < target]` — i.e. ~400 prior daily bars strictly before the session. For validation day 1 (session_date == val_start == train_end) every baseline value is computed from days that lie inside the immediately-preceding TRAIN window. fold_context.py:302-305 calls this per validation session with no gap.

(b) step_months is dead (never wired from config):
walkforward.py:54 `step_months: int | None = None`; :65 `step_months = step_months or val_months`; :80 `cur_train_start = _add_months(cur_train_start, step_months)`. All FIVE call sites pass only train/val/final_holdout_months and omit step_months: walkforward_runner.py:901-907, :973-979, :1930-1936; holdout.py:89-95; scan_matrix.py:1009-1015. grep for `step_months` across the whole lab returns only the function def, the docs/round1 maps, and one unit test (test_walkforward_splits.py:29) — never a config read or `wf.get("step_months")`. config/models.py:534 declares `walkforward: dict[str, Any]` (untyped), so no schema even surfaces the key. Downstream consumer of the correlated folds: objective.py:8 / :673-697 objective = median_fold_score - weights.fold_variance * statistics.stdev(per_fold_scores) — overlapping folds shrink that stdev.

**Reproduction (finder):**

Ran the real build_walkforward_splits in a throwaway REPL (PYTHONPATH set to the two src dirs, C:/Python312/python.exe), mirroring the runner's default call site (train/val/final only, no step_months).

Demo params (train=6,val=1,holdout=1, span 2023-01-01..2024-12-01): 16 splits; ALL 16 have val_start==train_end (True); consecutive TRAIN windows overlap ~83% (5/6 of a 6-month window), train_start steps ~1 month (=val_months).

Production params (train=21,val=1,holdout=5 from configs/bowaka_v2_actual_*_optuna*.yml:166-169/193-196/129-132, span 2022-01-01..2025-01-01): 10 splits; ALL val_start==train_end == True; MEAN consecutive-train overlap = 95.2% (= 20/21).

Proved step_months IS functional but unreachable: passing step_months=6 with train=6 yields 0d train overlap (3 disjoint splits) vs 83% overlap when omitted — so the only thing missing is the config wiring.

**Blast radius (finder):** Affects every walk-forward Optuna study (validation folds) and the final-holdout/scan-matrix windows built from build_walkforward_splits — i.e. all current_code_parity and intended_realism runs. Two compounding effects: (1) optimistic feature leakage at every fold's day-1 (prior-train ATR/EMA/vol baselines bleed into validation with zero embargo); (2) with the shipping 21m/1m config the 10 folds share 95.2% of their training data, so per-fold scores are strongly correlated -> statistics.stdev(fold_scores) is deflated -> the weights.fold_variance stability penalty (objective.py:697) is understated and 'apparent stability'/robustness gates are inflated. Net: the study's fold-variance penalty and any robustness verdict overstate out-of-sample stability; selected finalists are biased toward configs that merely fit the heavily-overlapping shared training prefix.

**Fix sketch (finder):** (b) Thread `step_months=int(wf.get("step_months", val_months))` through all five build_walkforward_splits call sites (and add it to the walkforward config schema). (a) Add an embargo/purge gap: insert `val_start = _add_months(train_end, embargo_months)` (configurable, >0) between train_end and val_start, or skip the first N validation sessions' feature warmup so day-1 baselines do not derive from data inside the train window.

**Skeptic reasoning:**

Both raw CODE FACTS are true and I confirmed them independently: (a) walkforward.py:75 `val_start = train_end` with no gap (and test_walkforward_splits.py:22 deliberately asserts `train_end == val_start`, "back-to-back is standard"); (b) walkforward.py:54,65 `step_months` defaults to `val_months` and is never threaded — all five call sites (walkforward_runner.py:901,973,1930; holdout.py:89; scan_matrix.py:1009) pass only train/val/final_holdout_months, and no config key exists. But the analyst's stated HARMS do not follow, because of the architecture they missed: THERE IS NO PER-FOLD TRAINING. _run_validation_folds (walkforward_runner.py:805-831) and _run_fold_backtest (488-540) take ONLY val_start/val_end and build sessions via _xnys_sessions(val_start,val_end); the train window is never used to fit/calibrate anything. The same global Optuna trial params are applied identically to every fold (apply_trial_params, line 868). Grepping the whole lab, train_start/train_end are used ONLY as a cache-key span anchor (walkforward_runner.py:2220-2231; scan_matrix.py:1026) and for plan serialization (2310-2311) — never for model fitting.

Sub-claim (b) REFUTED: the objective variance penalty statistics.stdev (objective.py:696, fold_variance weight 0.5 active) is computed over per-fold VALIDATION scores, and the validation windows are DISJOINT + ADJACENT, not overlapping. Reproduced with the shipping 21m/1m config (configs/...optuna.yml:129-132, span 2022-01..2025-01): 10 splits, every consecutive val window overlap=False / adjacent=True (they tile time with full, non-overlapping coverage). Train-window overlap is 95.2% but that data is unused, so it cannot correlate fold scores. I also reproduced that wiring step_months=6 makes things WORSE (only 2 val folds with 5-month GAPS), so dead step_months does not inflate stability or deflate the variance penalty — there is no mechanism.

Sub-claim (a) OVERSTATED: the day-1 daily ATR/EMA/vol baseline (suppliers.py:409-410, `prior[prior['_sd'] < target]`) is strictly CAUSAL — only sessions strictly before the trading day, never the day itself or any future data. That is exactly what a live deployment computes on that calendar date (correct no-look-ahead). With no model trained on the train window, the classic purge/embargo failure (train-feature ↔ val-label horizon bleed) has no mechanism here; reusing prior calendar days is not optimistic feature leakage and does not inflate fold returns. The legitimate residual point (no embargo between contiguous validation months relative to the hyperparameter search) is soft research hygiene, not the high-severity leakage + correlated-fold inflation claimed.

---

## L17_reconcile_vacuous &mdash; Reconcile/parity comparators return vacuous PASS on empty sets

**Finder:** real (severity medium, confidence high) &middot; **Skeptic:** confirmed_real (final severity low)

**Evidence (finder):**

RECONCILE comparators.py: emission_jaccard L295-296 `if not union: jac = 1.0` then L306 `passes=jac >= threshold` -> empty union PASSes. decision_reason_confusion L368 `match = matched/len(shared) if shared else 1.0` then L376 `passes=match >= threshold` -> no-shared-candidate PASSes (fires even when BOTH sides are non-empty but key-disjoint). report.py build_phase9_recon_report L400-401 `passes_by_stage[stage]=bool(payload['passes'])`, L404-405 `overall = all(v for v in passes_by_stage.values() if v is not None)`, L477 `overall_passed: bool(overall and not mismatch_flags)` -> NO guard on union_size==0 or comparable==0.
PARITY metrics.py: _trade_intersection_rate L111-112 `if not union: return 1.0,...`; _candidate_metrics L94-95 `if not matched_keys: return float(recall), 1.0` (gate vacuous on zero overlap); exit_reason_match_rate L189 `... if matched_diffs else 1.0`; daily_pnl_sign L132/149 `if not sessions: return 1.0,[]`. evaluate_thresholds L62-63 ONLY skips None (`if raw is None: continue`) so vacuous 1.0 counts as PASS. compute_parity_metrics L266 returns passes_audit_thresholds with NO check of prod_n_trades/lab_n_trades. NOTE the Phase-0 fix (L88-89 `if not prod_cands or not lab_cands: return None,None`) already neutralizes candidate_recall/gate_match_rate for the empty case, but trade_intersection_rate / exit_reason_match_rate / daily_pnl_sign_match_rate were NOT fixed.

**Reproduction (finder):**

Ran existing funcs in python -c (PYTHONPATH=.../bowaka_v2_lab/src:.../bowaka_common/src, C:/Python312). ACTUAL: emission_jaccard([],[]) -> jaccard=1.0 union_size=0 passes=True. decision_reason_confusion([],[]) -> comparable=0 match=1.0 passes=True. decision_reason_confusion with two NON-empty but cid-disjoint decision lists -> comparable=0 match=1.0 passes=True. build_phase9_recon_report(emission=ej_empty, decision_reason=dr_empty) -> passes_by_stage={emission_jaccard:True, decision_reason_confusion:True, ...None}, overall_passed=True, mismatch_flags=[]. compute_parity_metrics(all empty) -> candidate_recall=None gate_match_rate=None (Phase-0 fix OK) BUT trade_intersection_rate=1.0 exit_reason_match_rate=1.0 daily_pnl_sign_match_rate=1.0 fill_price_mae_bps=0.0 -> passes_audit_thresholds=True failing_metrics=[]. _candidate_metrics(non-empty zero-overlap) -> recall=0.0 gate_match_rate=1.0. Counter-case confirming partial scope: prod has 1 trade, lab empty -> trade_intersection_rate=0.0 passes=False (union non-empty catches one-sided emptiness; vacuous parity PASS needs BOTH sides empty). disjoint non-empty emission sets -> jaccard=0.0 passes=False (emission only vacuous on empty union, not zero-overlap).

**Blast radius (finder):** PARITY half is the LIVE wired gate: compute_parity_metrics <- parity/runner.py:1024 run_parity <- CLI subcommand + notebook-13. A parity window where BOTH prod and lab emit zero trades reports passes_audit_thresholds=True (trade_intersection/exit_reason/daily_pnl_sign all vacuous-1.0); a degenerate lab that emits nothing is masked only if prod also emitted nothing in that window (otherwise intersection=0.0 fails). exit_reason_match_rate and daily_pnl_sign_match_rate additionally go vacuous-1.0 whenever there are zero matched trades / zero sessions on a side. RECONCILE half (emission_jaccard / decision_reason_confusion / build_phase9_recon_report overall_passed) is real at function+report-builder level but confined to the synthetic-fixture / test path: orchestrator.py:106 _default_reconcile_one raises NotImplementedError and run_reconciliation returns status=REAL_LOGS_DEFERRED passes_all_thresholds=False on empty session sets, so the promotion-gating orchestrator does NOT vacuously pass today and no real paper logs exist. Severity medium: the parity gate can stamp PASS on a no-trade run, but only when both sides are simultaneously empty (preflight elsewhere blocks empty PIT universe); reconcile half not yet wired to real data.

**Fix sketch (finder):** In evaluate_thresholds, gate on observable coverage: fail (or mark NOT-MEASURED/None) when prod_n_trades==0 AND lab_n_trades==0 (and per-metric when matched/sessions==0) instead of letting the empty-set 1.0 fallbacks count as PASS; mirror the Phase-0 None-exclusion already used for candidate metrics. For the reconcile side, have emission_jaccard/decision_reason_confusion expose passes=None (or a comparable==0 sentinel) on empty union / empty shared set, and make build_phase9_recon_report treat union_size==0/comparable==0 as not-comparable rather than PASS.

**Skeptic reasoning:**

The function-level behavior reproduces EXACTLY as the finder claimed. Independently read current code + ran existing functions (PYTHONPATH=bowaka_v2_lab/src:bowaka_common/src, C:/Python312):

PARITY (parity/metrics.py): _trade_intersection_rate L111-112 `if not union: return 1.0,...`; exit_reason_match_rate L186-189 `... if matched_diffs else 1.0`; _per_session_pnl_signs L131-132 `if not sessions: return 1.0,[]`; fill_price_mae_bps L184 `... if abs_diffs else 0.0`. evaluate_thresholds L60-65 skips ONLY None. The Phase-0 fix (L88-89) neutralizes only candidate_recall/gate_match_rate to None — the other three were NOT fixed. REPRO: compute_parity_metrics(both sides empty, requested_sessions threaded) -> passes_audit_thresholds=True failing=[] (trade_isect=1.0 exit_match=1.0 pnl_sign=1.0 mae=0.0 cand_recall=None gate_match=None). RECONCILE (reconcile/comparators.py): emission_jaccard L295-306 -> jaccard=1.0 union=0 passes=True; decision_reason_confusion L368-376 -> comparable=0 match=1.0 passes=True (REPRO also confirmed this fires on TWO NON-EMPTY but cid-disjoint decision lists -> comparable=0 match=1.0 passes=True). build_phase9_recon_report report.py:404-477 has no union_size==0/comparable==0 guard -> overall_passed=True. Counter-case verified: one-sided (prod=1 lab=0) IS caught -> passes=False failing=['trade_intersection_rate','daily_pnl_sign_match_rate'] isect=0.0; vacuous parity PASS requires BOTH sides empty.

WHY IT DOES NOT BITE A REAL PROMOTION DECISION (skeptic refinement, down-grades severity): (1) The wired Optuna promotion gate promotion_gates.py:367-385 consumes the ReconcileReport object, NOT the comparators. run_reconciliation (orchestrator.py:128-134) returns status=REAL_LOGS_DEFERRED, passes_all_thresholds=False on empty sessions, and _default_reconcile_one (orchestrator.py:103-111) raises NotImplementedError — so the vacuous-PASS comparators / build_phase9_recon_report live ONLY in the synthetic-fixture/test path (tests/integration/test_synthetic_recon_*.py), not promotion. (2) parity passes_audit_thresholds is consumed ONLY in cli.py:1105/1108 (JSON + exit code) and notebook-13 — grep over the package shows zero references in promotion/ or optuna/promotion_gates.py; checklist.py qr.08 (_config_parity_check L227-254) is a config-FIELD diff, returns 'unknown' on zero rows, not the trade-parity metrics. (3) An independent gate qr.09_min_trade_count (checklist.py:260-289, DEFAULT_MIN_TRADE_COUNT=30) hard-fails any zero/low-trade run on the run's own summary.json['n_trades'], so a degenerate no-trade run cannot be promoted regardless of any vacuous parity PASS. (4) CLI _cmd_parity blocks an empty universe upfront (cli.py:1062-1068). Net: the defect is genuine and reproduces, but its only live consequence is a misleading parity DIAGNOSTIC report + CLI exit-code-0 on a both-sides-empty window, not a vacuous PASS through any automated promotion gate. Finder's 'medium' is slightly overstated; realistic impact is low (misleading human/CI signal, gated promotion is protected).

---

## L18_tape_condition_filter &mdash; Tape-replay oracle/producer does not filter ineligible trade conditions

**Finder:** real (severity medium, confidence high) &middot; **Skeptic:** confirmed_real (final severity low)

**Evidence (finder):**

PRODUCER keeps but never filters conditions. backfill.py:829-831,841 `_coerce_trade_row` captures Alpaca `c`/`conditions` into a "conditions" column ("" if None) and writes the full coerced dict — backfill.py:1032 `_t = pd.DataFrame(_raw)` then `_flush_accumulated_trade_months` (backfill.py:914-921) only `drop_duplicates()` + stable-sort, no condition filter. So odd-lot(I)/avg-price(B,W)/derivatively-priced(4)/out-of-seq(Z,L)/auction(O,M,Q) prints are stored RAW. Schema docstring backfill.py:809-810 lists "conditions" as a canonical column.
READER passes everything through. store.py trades_between (store.py:301-323) reads all parquet columns, filters only on timestamp window, no condition filter. suppliers.py:258-259 `trades_supplier` just returns `store.trades_between(...)` unfiltered.
ORACLE ignores conditions entirely. tape_fill.py:92 selects only `["timestamp","price","size"]`; eligibility mask (tape_fill.py:86-90) is time-window + optional min_price/max_price (the order's trigger) ONLY. Size summed at tape_fill.py:103 and consumed in the loop tape_fill.py:109-119 with no condition check. The required-columns guard (tape_fill.py:79 _EMPTY_COLS) does not include conditions, so a conditions column being present or absent is irrelevant to the oracle.
CALLERS don't filter either: _tape_replay_fill fills.py:690-698 and _tape_replay_bracket exits.py:497-505 pass the raw tape straight to replay_tape_fill with only price/time args.
Round1 maps independently flag the exact exclusion list: alpaca_micro.md:32 "Trade condition codes — what to exclude from a tape-replay fill model"; alpaca_micro.md:40-41 (@ include / I odd-lot exclude-from-price-volume-only); alpaca_catalog.md:19 confirms Alpaca trade payload carries `c` (condition codes array).

**Reproduction (finder):**

Ran the REAL oracle via python -c (PYTHONPATH set to lab+common src). Hand-built a 5-print tape at 2026-01-02 14:30:00Z: regular(@,100sh@100.00), odd-lot(I,10sh@99.50), avg-price(B,500sh@100.20), derivatively-priced(4,300sh@99.00), auction(O,200sh@101.00). ACTUAL output for replay_tape_fill(qty=600, window=5s, participation=1.0): filled=True, filled_qty=600, window_qty=1110 (= sum of ALL print sizes including the 1010 ineligible shares), n_prints=3, avg_fill_price=100.155. Eligible-only counterfactual (regular @ print only, 100sh): filled=False, filled_qty=100, window_qty=100. So the unfiltered oracle turns what should be a 100-share NO-FILL into a full 600/600 FILL — direct over-fill from counting ineligible prints. Could NOT inspect the real lake: Docker daemon returns 500 Internal Server Error on every API version (1.43/1.44/1.54) — `docker exec ql-jupyter` and `docker ps` both fail; no local trades parquet exists (Glob of **/trades/**/*.parquet = none, MARKET_DATA_ROOT unset). So the in-production FRACTION of ineligible prints is unquantified, but the conditions-column existence is proven by the producer schema and the over-count behavior is proven by executing the actual function.

**Blast radius (finder):** Affects ONLY runs with fill_model="tape_replay" on entry (execution) or exit (exits) blocks — config default is "legacy" (models.py:319,438), where trades_supplier is not consulted, so legacy/default backtests are unaffected. For tape-replay runs (the "most-honest depth fill", tier-tagged T3_NBBO_DEPTH) the achievable VWAP, fill_fraction, filled flag, window_qty and resulting fill/no-fill decisions are all inflated by ineligible volume — making the intended highest-realism mode systematically OPTIMISTIC on fillability (over-fills marketable entries and sell brackets). Compounds the already-mapped tape over-fill notes (sim_fills.md:72 participation=1.0 lets one print be fully consumed). Note: odd-lot bias skews small/cheap-share names hardest.

**Fix sketch (finder):** Data permits the fix — the "conditions" column already exists in the lake schema. Add an eligibility filter to replay_tape_fill (e.g. include only @/space; drop I,B,W,4,Z,L,O,M,Q per alpaca_micro.md:32 table) reading the conditions column when present, with a safe fallback when absent; add "conditions" to the column projection (tape_fill.py:92) and keep _EMPTY_COLS optional so legacy fixtures without the column still work. Optionally also filter the `u` cancel/correct update flag.

**Skeptic reasoning:**

Independently confirmed the mechanism end-to-end and reproduced the over-fill. PRODUCER captures but never filters conditions: backfill.py:829-831,841 (_coerce_trade_row writes a "conditions" column, "" if None), backfill.py:914-919 (_flush_accumulated_trade_months only drop_duplicates().sort_values(), no condition filter). READER passes everything through: store.py:301-323 (trades_between filters only the timestamp window); _normalise_bars store.py:135-153 only normalises the timestamp dtype and does NOT drop conditions; suppliers.py:258-259 returns it unfiltered. ORACLE ignores conditions entirely: tape_fill.py:79 _EMPTY_COLS=("timestamp","price","size"); eligibility mask tape_fill.py:86-90 is time-window + optional min/max price only; projection tape_fill.py:92 selects only [timestamp,price,size]; grep for condition/odd-lot across sim/ returns only an unrelated "precondition" comment (backtester.py:773). CALLERS don't filter: strategy_consumer.py:667-680 (entry) and exits.py:492-505 (exit bracket) pass the raw supplier frame straight to replay_tape_fill with only price/time args. REPRODUCED (PYTHONPATH=lab+common src, real replay_tape_fill, hand-built 5-print tape at 2026-01-02 14:30:00Z): UNFILTERED qty=600/window=5s/part=1.0 -> filled=True, filled_qty=600, window_qty=1110, n_prints=3, vwap=100.155 (consumed the 1010 ineligible odd-lot/avg-price/deriv-priced shares); ELIGIBLE-ONLY (@ print, 100sh) -> filled=False, filled_qty=100, window_qty=100. So ineligible prints flip a 100-share no-fill into a full 600/600 fill — direct over-fill, matching the finder's numbers exactly. Conditions-column EXISTENCE in the lake is established by the producer source (backfill.py:807-844) which writes it on every row; I could NOT directly sample the real lake (docker exec ql-jupyter returns 500 Internal Server Error on v1.54; no local trades parquet — Glob of **/trades/**/*.parquet = none), so the in-production fraction of ineligible prints is unquantified, but the data permits the fix because the column is in the schema. WHERE I DIVERGE FROM FINDER (severity): the blast radius is narrower than "medium". Both blocks default fill_model="legacy" (models.py:319,438); no YAML/overlay in the repo sets tape_replay. The ONLY enabling path is derive_validation_config(enable_tape_replay=True), which defaults False (autoconfig.py:293) with a test asserting default-off (test_tape_replay_pb6.py:58). Critically, ANY tape-consuming run is HARD-CAPPED at research_only (suitability.py:236-237) precisely because the tape-replay fill model is "NOT yet validated against the tape (PB.5)". So it can never reach a deployable/promoted tier today; it only biases opt-in, research-capped finalist-validation experiments optimistic on fillability. Defect is real and reproducible but cannot bite a promotable run in current practice -> low severity, valid roadmap item for the PB.5 validation work.
