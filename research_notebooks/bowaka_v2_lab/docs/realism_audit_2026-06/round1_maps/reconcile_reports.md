This confirms key findings: the OCO latency calibrator, the Phase-9 aggregate comparators (fill_latency, oco_attempt_count, exit_reason_timing, emission_jaccard), and `build_phase9_recon_report` are NOT wired into any CLI/orchestrator — they only exist within the reconcile package itself. The orchestrator's `_default_reconcile_one` raises `NotImplementedError`. Let me write the final report.

## Purpose & data flow (how this subsystem fits the backtest pipeline)

Two distinct, weakly-coupled subsystems live under "reconcile_reports":

**1. `parity/`** — production-vs-lab equivalence oracle. `run_parity` (runner.py:757) runs the mirrored prod backtester (`reference/source_strategy/scripts/bowaka_v2_backtest.py`) via subprocess and the lab backtester in-process over the same lake/window/per-session-PIT-universe, then normalizes both sides to `NormalizedTrade`/`NormalizedCandidate` (normalizers.py) and folds them into a `ParityReport` (metrics.py:`compute_parity_metrics`). It compares **trades and candidates only** — entry-price MAE (bps), trade-set Jaccard, exit-reason match, daily-PnL-sign match, candidate recall, gate match. It does NOT compare configs (that is a separate `config_diff` artifact surfaced in render_run_report), order-by-order fills, intrabar barrier ordering, or sizing math beyond the resulting trade rows. `golden.py` persists a diffable bundle as the fidelity gate for speedup phases (price tol 1e-12, pnl 1e-9). report.py renders paste-back Markdown.

**2. `reconcile/`** — paper-trading-vs-lab reconciliation. Three generations coexist: Phase-7 (`comparator.py` timestamp-window dict matcher + `importer.import_paper_logs` + `slippage_residuals.compute_slippage_residuals`), Phase-10 (`schemas.py` typed models → `replay.replay_paper_session` runs lab in `current_code_parity`, joins by `candidate_event_id` → `comparators` per-stage deltas → `report.build_reconcile_report`), and Phase-9 (`paper_log_schema` expanded event taxonomy + `importer.import_paper_event_logs` + 7 aggregate comparators in comparators.py + `report.build_phase9_recon_report` + `orchestrator.run_reconciliation` multi-session gate). **No real paper logs exist** — the entire path runs scaffolding-only against synthetic fixtures. The slippage and OCO-latency calibrators fit JSON artifacts the sim's T4/attach-latency paths can optionally consume.

`reports/` (render_run_report, exit_analysis, execution_quality) build the per-run `report.md`/`report.json` from on-disk artifacts; `schemas/events.py`+`decisions.py` define the candidate/decision record contract both sides emit.

## Behavioral spec

- `diff_candidate_sets` keys strictly on `event_id`; paper/lab share ids because both stamp `strategy:session:symbol:ts` (comparators.py:69-85).
- `compare_decision_reason` match=True only if `decision`==`decision` AND `reason`==`reason`; `None` if either side missing (comparators.py:108-130).
- `compare_fill` price delta bps relative to **paper** price, `None` when paper price is 0.0 (comparators.py:181-190).
- `emission_jaccard`: empty union → `jaccard=1.0` ("vacuous match", comparators.py:295-296); default threshold 0.85.
- `decision_reason_confusion`: `match=1.0` when no shared candidates (comparators.py:368); threshold 0.90.
- `fill_residuals` pairs by `candidate_event_id` else falls back to `parent_order_id` (comparators.py:441); `passes` iff `n_flagged==0`; default qty tolerance 0.0 shares.
- `fill_latency_residuals` requires all four maps (paper_acks, paper_fills_ts, lab_acks, lab_fills_ts) to share a cid (comparators.py:543) — any missing key drops the candidate silently.
- `oco_attempt_count_diff`: a candidate on one side counts as 0 on the other; `passes` iff every count matches exactly (comparators.py:608-631).
- `exit_reason_timing` pairs by cid, flags reason-mismatch OR abs-timing > tol (default 60s); `passes` requires all reasons match AND zero timing-flagged (comparators.py:726).
- `replay.run_lab_parity_session` forces `simulation.mode=current_code_parity` + `allow_research_relaxed=True` (replay.py:206-208); falls back to `smoke_fixture`+synthetic universe when no lake (replay.py:257-258).
- `_lab_orders_and_fills` reads `orders.parquet`/`fills.parquet`; only `filled==True` fills are comparable; **lab `fill_timestamp` is hardcoded `None`** (replay.py:360) — so lab fill latency can never be computed.
- `build_reconcile_rows` ensures every cid (incl. downstream-only) gets exactly one row (replay.py:454-464).
- importer `_read_jsonl` silently skips un-parseable JSON lines (importer.py:73-74) and un-parseable timestamps (replay.py:115).
- `import_paper_event_logs` non-strict mode drops malformed rows to `drift_issues` (importer.py:281-285); stamps `source_log_file` pre-validation (importer.py:269).
- metrics `_candidate_metrics` returns `(None,None)` when either side lacks candidates → metric excluded from verdict, never PASS (metrics.py:88-89). Same None-handling in `evaluate_thresholds` (metrics.py:63-65).
- `_fill_diff_bps` returns 0.0 when prod entry ≤ 0 (metrics.py:43-44) — masks divergence.
- normalizers: lab trade with unparseable entry ts **raises** (fail-loud, normalizers.py:203); prod malformed row silently dropped (normalizers.py:142).
- `NormalizedTrade.__post_init__` rejects side != "long" (schemas.py:34).
- `time_of_day_bin` maps unparseable ts → "midday" (oco_latency_calibrator.py:59-60).
- slippage calibrator residual sign: buy `(paper-sim)`, sell `(sim-paper)`; positive = paper worse (slippage_residuals.py:193-196).
- `validate_entry_decision`: accepted must carry `all_gates_passed`; rejected/broker_reject must be in canonical set (events.py:264-271).
- `build_broker_reject_record` sets `decision="rejected"`, `reason="broker_reject"` (decisions.py:206-217).
- render_run_report caps suitability at `backtesting_only`, emits IEX partial-tape banner when feed=="iex" (render_run_report.py:249-256), strips forbidden "stub" substrings via `_safe_text` (render_run_report.py:149-161).

## Knobs

- `DEFAULT_RECONCILE_TOLERANCES` (comparator.py:23-31): emission 0.85, decision 0.90, fill 5bps/0sh, latency p95 200ms, pnl $1, exit timing 60s. Loaded via `load_reconcile_tolerances`, override precedence default<shipped-yml<overrides (comparator.py:42-76).
- `DEFAULT_THRESHOLDS` parity (metrics.py:18-25): candidate_recall 0.99, gate 0.95, trade_intersection 0.90, fill_mae 5bps, exit 0.90, pnl-sign 0.95.
- orchestrator `DEFAULT_THRESHOLDS` (orchestrator.py:29-37) + `DEFAULT_MIN_SESSIONS=10`; `reconcile.paper_logs_root` default `data/paper_logs`.
- `chunk_per_session` (runner.py:771): False=carry-forward bankroll (sign-off numerics); True=per-session reset bankroll, progress visibility — **sizing-dependent qty can differ** (runner.py:797-800).
- `per_session_universe` (default True): per-session PIT symbols files vs legacy window-union (runner.py:806-811).
- `parallel_workers` (runner.py:774): contiguous-block parallel; cap 8/16 via `_parity_path_touches_postgres` (static source scan, runner.py:547-570).
- `cached_data_path` (default True): accelerated byte-identical supplier path (runner.py:352).
- `cost_stress` threaded both sides (runner.py:292-293).
- `execution.calibration_artifact` → opt-in T4 fill tier reads slippage artifact (slippage_residuals.py:10-12); T0-T3 ignore it.
- `BOWAKA_V2_PAPER_LOGS_ROOT` env fallback for `resolve_paper_logs_root` (importer.py:182).
- render_run_report `suitability` (required arg, raises if non-canonical).

## Invariants & guards

- Fail-loud: lab trade missing entry ts raises (normalizers.py:203); prod returncode != 0 raises (runner.py:840,612,959); prod timeout raises with log tail (runner.py:195-207); parity worker rc!=0 raises (runner.py:718); `resolve_paper_logs_root` raises `PaperLogsNotFoundError` (importer.py:184-189); `assert_strategy_isolation` (runner.py:306); MemoryBudget launch guard (runner.py:664).
- `orchestrator._default_reconcile_one` raises `NotImplementedError` — the production per-session reconcile body is **unimplemented**; only injected stubs run (orchestrator.py:103-111).
- **Silent fallbacks (flag each):**
  - importer drops bad JSON lines (importer.py:73-74), bad timestamps (importer.py:87, replay.py:115).
  - `_normalise_ts` swallows all parse exceptions, leaves raw value (importer.py:87-88).
  - `_latency_ms`/`time_of_day_bin`/`exit_reason_timing` timing catch-all → `None`/"midday" (comparators.py:523, oco:59, comparators.py:696).
  - prod malformed trade row dropped silently (normalizers.py:142,194).
  - prod `summary.json` malformed → empty dict (runner.py:213-214).
  - `compute_slippage_residuals` returns empty frame on no join keys (slippage_residuals.py:68-69) — divergence invisible.
  - `_fill_diff_bps` 0.0 on prod price ≤0 (metrics.py:43-44).
  - render_run_report every artifact reader swallows exceptions → "Not available" (render_run_report.py:83,95,104).
  - `load_reconcile_tolerances` malformed override file → silently returns defaults (comparator.py:69-70).
  - empty-union / no-shared-candidate comparators return `passes=True`/`jaccard=1.0` — a run that produced nothing **passes** vacuously (comparators.py:295,368; metrics.py:93,111).

## Leads

- comparators.py:295 / 368 / metrics.py:93,111 — **vacuous PASS**: empty/zero-overlap candidate sets yield jaccard=1.0, match=1.0, recall fallback 1.0, intersection 1.0 → a degenerate run that emits nothing reports full agreement.
- replay.py:360 — lab `LabFill.fill_timestamp=None` hardcoded; `fill_latency_residuals` for lab is structurally impossible, so latency reconciliation silently has zero lab data → vacuous pass.
- orchestrator.py:103-111 — production reconcile path is `NotImplementedError`; the entire Phase-9 multi-session gate only ever runs against injected test stubs. No real reconcile is wired.
- oco_latency_calibrator.py — **entirely unreferenced** outside its own module/`__init__`; dead code (no caller fits or consumes it). Sim attach-latency still uses the hardcoded 0.5s the docstring says it replaces.
- comparators.py:597-631 `oco_attempt_count_diff` & `fill_latency_residuals` & `emission_jaccard` & `exit_reason_timing` — only callers are report.py/tests; not wired into orchestrator's `_default_reconcile_one`, so they never run on real data.
- oco_latency_calibrator.py:64-75 — `time_of_day_bin` has no "close" boundary before 15:30: 15:00-15:29 → "afternoon", but the 16:00 close edge and `hour>=16` (after-hours) fall through to "close" — after-hours events mislabeled, and the documented "last 30 min before close" (15:30-16:00) is the only "close" path; bins are asymmetric vs docstring.
- comparators.py:441 — `fill_residuals` falls back to `parent_order_id` as the pairing key when `candidate_event_id` missing, but paper and lab parent_order_ids are independently generated → cross-pairing risk producing spurious residuals.
- metrics.py:43-44 — `_fill_diff_bps` returns 0.0 (a perfect match) when prod entry_price ≤ 0; a zero/negative prod price hides a real fill divergence as agreement.
- normalizers.py:148-149,216 — exit_ts/exit_price `_to_utc_minute_or_none` floors to minute; sub-minute exit-timing divergences between prod and lab are invisible by construction (only entry minute is the join key, exit timing not in match metric).
- metrics.py:180 / golden.py:150 — exit_reason equality after `_canonical_exit_reason` lowercasing/snake-casing (normalizers.py:87-113); if prod and lab use different vocab (e.g. "target" vs "take_profit"), canonicalizer does NOT map synonyms → false exit mismatches. `EXIT_REASONS` (exit_analysis.py:24) uses "target"/"time_stop"/"max_hold" but parity schema docstring lists "signal_fade_*"/"eod"/"manual" — vocab drift.
- runner.py:547-570 `_parity_path_touches_postgres` — static regex source-scan to pick worker cap; brittle (a comment or string literal matching the pattern flips the cap; also won't catch transitive PG imports).
- runner.py:797-800 — `chunk_per_session=True` changes lab bankroll carry → trade qty differs from full-window run; the parity verdict can differ between modes for the same window (sizing-sensitive). Not flagged in the report output.
- report.py:153 `compare_order_size` "matched" defined as delta `== 0.0` exact float compare (report.py:152) — any sub-share rounding diff counts as mismatch with no tolerance.
- build_reconcile_report fill "matched" uses `< 1e-9` bps and pnl `< 1e-6` (report.py:157,167) — Phase-10 report has hardcoded near-exact tolerances inconsistent with Phase-9's 5bps/$1 tolerances; two report generations disagree on what "match" means.
- importer.py:181-185 — order→candidate backfill only maps fills/exits when paper order row carries BOTH parent_order_id and candidate_event_id; orders lacking the link leave downstream records unjoined (presence becomes paper_only spuriously).
- slippage_residuals.py:91-98 `_bucket` — loop assigns largest edge index ≤ v but the top "implicit cap" comment implies values above the rightmost edge bucket into top bin; for v between edges it picks the lower edge — verify off-by-one binning vs intent.
- comparator.py:121-143 `compare_candidates` greedy nearest-ts within 120s window is order-dependent (first paper record claims nearest sim); not globally optimal matching — can inflate miss/extra counts.
- decisions.py:206-217 — `build_broker_reject_record` sets decision="rejected" not "broker_reject"; reconciliation keys on `reason` not `decision`, but `compare_decision_reason` compares `decision` too → a broker_reject vs rejected-for-other-reason still matches on decision, only differing on reason (intended per comment but subtle).
- render_run_report.py:149-161 `_safe_text` rewrites any "stub"/"phase N fills" substring in checklist evidence to "placeholder"/"[redacted]" — can mask legitimate diagnostic text that happens to contain those words.
- normalizers.py:172-176 — prod `.json` trades path silently redirected to `trades.parquet`; if both absent returns `[]` → prod side reads as zero trades, parity then compares lab-vs-empty (could show all lab_only, or vacuous pass if both empty).

## Test coverage hooks

- **parity**: covered by `tests/integration/test_parity_runner_against_real_lake.py`, `test_parity_runner_cached_path_parity.py`, `test_parity_parallel_matches_serial.py`, `test_parity_cli_subcommand.py`, `test_parity_notebook_papermill_runs_headless.py`; config-parity unit tests in `tests/parity/test_config_parity_*.py`. golden.py exercised by cached-path/parallel parity tests.
- **reconcile Phase-10**: `tests/reconcile/test_comparators_*.py`, `test_replay_paper_session_synthetic.py`, `test_reconciliation_report_realism.py`, `test_paper_logs_synthetic_fixture.py`, `test_reconcile_cli_synthetic.py`, `test_reconcile_fails_on_missing_paper_logs_when_no_fixture.py`.
- **reconcile Phase-9 orchestrator**: `tests/integration/test_reconcile_*` (below_min_sessions, with_no_logs_returns_deferred, cli_exit_codes, against_synthetic_fixture, cli_writes_report) — all exercise aggregation/status with **injected** `reconcile_one`; the production `_default_reconcile_one` body is never tested (it just raises).
- **slippage**: `tests/integration/test_slippage_calibrator_roundtrip.py`, `tests/unit/test_paper_slippage_residuals.py`.
- **reports**: `test_report_renderer_required_sections.py`, `test_report_json_completeness.py`, `test_report_no_stub_strings.py`, `test_iex_run_report_has_partial_tape_banner.py`, execution-quality + exit-lifecycle integration tests.
- **NO TEST FOUND for:** `oco_latency_calibrator.py` (entire module — no test references it; `time_of_day_bin` boundaries untested), `build_phase9_recon_report`/`render_phase9_recon_report` (report.py:361-621 — no dedicated test located), `fill_latency_residuals`/`oco_attempt_count_diff`/`exit_reason_timing`/`emission_jaccard` aggregate comparators (only `test_comparators_*` for candidate-set/decision/fill found — latency/oco/exit-timing/emission appear uncovered), `bucket_fill_errors`/`write_bucketed_fill_error` (slippage_residuals.py:284-346), Phase-7 `comparator.compare_candidates` greedy matcher (no `test_comparator*` for the window matcher located).